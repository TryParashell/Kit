from __future__ import annotations

import argparse
from fractions import Fraction
import glob
import json
import os
from typing import Dict, List, Sequence, Tuple

NO_BODY_KINDS = ("null", "objectref")


def load_traces(segments_dir: str) -> List[dict]:
    traces = []
    for path in sorted(glob.glob(os.path.join(segments_dir, "segments_*.json"))):
        traces.append(json.load(open(path, encoding="utf-8")))
    return traces


def build_tree(segments: Sequence[dict]) -> Tuple[List[List[int]], List[int]]:
    children: List[List[int]] = [[] for _ in segments]
    for i, seg in enumerate(segments):
        parent = seg["parent"]
        if parent >= 0:
            children[parent].append(i)
    subtree_order: List[int] = []
    for i in range(len(segments) - 1, -1, -1):
        subtree_order.append(i)
    return children, subtree_order


def subtree_stats(
    segments: Sequence[dict], children: Sequence[Sequence[int]]
) -> Tuple[List[Dict[str, int]], List[int]]:
    counts: List[Dict[str, int]] = [dict() for _ in segments]
    headers: List[int] = [0] * len(segments)
    for i in range(len(segments) - 1, -1, -1):
        seg = segments[i]
        acc: Dict[str, int] = {}
        hdr = 0
        if seg["kind"] not in NO_BODY_KINDS:
            acc[seg["class_name"]] = 1
        for c in children[i]:
            hdr += segments[c]["header"] + headers[c]
            for key, value in counts[c].items():
                acc[key] = acc.get(key, 0) + value
        counts[i] = acc
        headers[i] = hdr
    return counts, headers


def tail_chain(
    segments: Sequence[dict], children: Sequence[Sequence[int]], index: int
) -> Tuple[Dict[str, int], bool]:
    chain: Dict[str, int] = {}
    cursor = index
    while True:
        seg = segments[cursor]
        parent = seg["parent"]
        if parent < 0:
            return chain, True
        siblings = children[parent]
        if siblings[-1] != cursor:
            return chain, False
        name = segments[parent]["class_name"]
        if segments[parent]["kind"] in NO_BODY_KINDS:
            return chain, False
        chain[name] = chain.get(name, 0) + 1
        cursor = parent


def build_equations(traces: Sequence[dict]) -> Tuple[List[dict], List[str]]:
    equations: List[dict] = []
    variables: Dict[str, None] = {}
    for trace in traces:
        segments = trace["segments"]
        children, _ = build_tree(segments)
        counts, headers = subtree_stats(segments, children)
        for i, seg in enumerate(segments):
            if seg["kind"] in NO_BODY_KINDS:
                continue
            chain, usable = tail_chain(segments, children, i)
            if not usable:
                continue
            row: Dict[str, int] = {}
            for key, value in counts[i].items():
                row["S:" + key] = row.get("S:" + key, 0) + value
            for key, value in chain.items():
                row["T:" + key] = row.get("T:" + key, 0) + value
            span = seg["scope_end"] - seg["offset"] - seg["header"]
            rhs = span - headers[i]
            for key in row:
                variables[key] = None
            equations.append(
                {
                    "label": trace["label"],
                    "node": i,
                    "class_name": seg["class_name"],
                    "row": row,
                    "rhs": rhs,
                    "span": span,
                    "depth": seg["depth"],
                }
            )
    return equations, sorted(variables)


def rref(
    rows: List[List[Fraction]], width: int
) -> Tuple[List[List[Fraction]], List[int], bool]:
    pivots: List[int] = []
    r = 0
    for c in range(width):
        pick = -1
        for k in range(r, len(rows)):
            if rows[k][c] != 0:
                pick = k
                break
        if pick < 0:
            continue
        rows[r], rows[pick] = rows[pick], rows[r]
        lead = rows[r][c]
        rows[r] = [value / lead for value in rows[r]]
        for k in range(len(rows)):
            if k != r and rows[k][c] != 0:
                factor = rows[k][c]
                rows[k] = [a - factor * b for a, b in zip(rows[k], rows[r])]
        pivots.append(c)
        r += 1
        if r == len(rows):
            break
    consistent = True
    for k in range(r, len(rows)):
        if all(value == 0 for value in rows[k][:width]) and rows[k][width] != 0:
            consistent = False
    return rows, pivots, consistent


def solve(equations: Sequence[dict], variables: Sequence[str]) -> dict:
    index = {name: i for i, name in enumerate(variables)}
    width = len(variables)
    rows: List[List[Fraction]] = []
    for eq in equations:
        row = [Fraction(0)] * (width + 1)
        for key, value in eq["row"].items():
            row[index[key]] = Fraction(value)
        row[width] = Fraction(eq["rhs"])
        rows.append(row)
    reduced, pivots, consistent = rref(rows, width)
    free = [c for c in range(width) if c not in set(pivots)]
    freeset = set(free)
    determined: Dict[str, int] = {}
    for r, c in enumerate(pivots):
        if all(reduced[r][f] == 0 for f in freeset):
            value = reduced[r][width]
            determined[variables[c]] = value
    return {
        "consistent": consistent,
        "rank": len(pivots),
        "variables": len(variables),
        "determined": determined,
        "free": [variables[f] for f in free],
    }


def residual_check(
    equations: Sequence[dict], determined: Dict[str, Fraction]
) -> List[dict]:
    failures: List[dict] = []
    for eq in equations:
        total = Fraction(0)
        complete = True
        for key, value in eq["row"].items():
            if key in determined:
                total += determined[key] * value
            else:
                complete = False
                break
        if not complete:
            continue
        if total != Fraction(eq["rhs"]):
            failures.append(
                {
                    "label": eq["label"],
                    "node": eq["node"],
                    "class_name": eq["class_name"],
                    "predicted": str(total),
                    "observed": eq["rhs"],
                }
            )
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--segments", default="re/data/segments")
    parser.add_argument("--out", default="re/data/body_scalars.json")
    parser.add_argument("--labels", default="")
    args = parser.parse_args()
    traces = load_traces(args.segments)
    if args.labels:
        wanted = set(args.labels.split(","))
        traces = [t for t in traces if t["label"] in wanted]
    equations, variables = build_equations(traces)
    result = solve(equations, variables)
    determined = result["determined"]
    failures = residual_check(equations, determined)
    payload = {
        "traces": [t["label"] for t in traces],
        "equations": len(equations),
        "variables": result["variables"],
        "rank": result["rank"],
        "consistent": result["consistent"],
        "determined": {
            key: (int(value) if value.denominator == 1 else str(value))
            for key, value in sorted(determined.items())
        },
        "free": result["free"],
        "residual_failures": failures,
    }
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=1)
        handle.write("\n")
    print(
        f"equations={len(equations)} variables={result['variables']} "
        f"rank={result['rank']} consistent={result['consistent']} "
        f"determined={len(determined)} residual_failures={len(failures)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
