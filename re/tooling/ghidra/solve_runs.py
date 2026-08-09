# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

import argparse
import collections
import glob
import json
import os
from typing import Dict, List, Optional, Sequence, Tuple

NO_BODY_KINDS = ("null", "objectref")


def load_traces(segments_dir: str, labels: str) -> List[dict]:
    traces = []
    for path in sorted(glob.glob(os.path.join(segments_dir, "segments_*.json"))):
        traces.append(json.load(open(path, encoding="utf-8")))
    if labels:
        wanted = set(labels.split(","))
        traces = [t for t in traces if t["label"] in wanted]
    return traces


def children_of(segments: Sequence[dict]) -> List[List[int]]:
    children: List[List[int]] = [[] for _ in segments]
    for i, seg in enumerate(segments):
        if seg["parent"] >= 0:
            children[seg["parent"]].append(i)
    return children


class Solver:
    def __init__(self, traces: Sequence[dict]) -> None:
        self.traces = list(traces)
        self.segments: Dict[str, List[dict]] = {}
        self.kids: Dict[str, List[List[int]]] = {}
        for trace in self.traces:
            label = trace["label"]
            self.segments[label] = trace["segments"]
            self.kids[label] = children_of(trace["segments"])
        self.variable: set = set()
        self.conflicts: List[dict] = []
        self.runs: Dict[str, int] = {}
        self.end: Dict[Tuple[str, int], Optional[int]] = {}
        self.witness: Dict[str, List[str]] = collections.defaultdict(list)

    def key(self, label: str, node: int, slot: int) -> str:
        name = self.segments[label][node]["class_name"]
        if slot == -2:
            return name + "@leaf"
        if slot == -1:
            return name + "@lead"
        return "%s@%d" % (name, slot)

    def seed(self) -> None:
        self.runs = {}
        self.witness = collections.defaultdict(list)
        self.end = {}
        for label, segments in self.segments.items():
            for i, seg in enumerate(segments):
                if seg["kind"] in NO_BODY_KINDS:
                    self.end[(label, i)] = seg["offset"] + seg["header"]
                elif seg["depth"] == 0:
                    self.end[(label, i)] = seg["scope_end"]
                else:
                    self.end[(label, i)] = None

    def set_run(self, key: str, value: int, label: str, node: int) -> bool:
        if key in self.variable:
            return False
        if value < 0:
            self.conflicts.append(
                {
                    "key": key,
                    "reason": "negative",
                    "observed": value,
                    "label": label,
                    "node": node,
                }
            )
            self.variable.add(key)
            self.runs.pop(key, None)
            return False
        previous = self.runs.get(key)
        if previous is None:
            self.runs[key] = value
            self.witness[key].append("%s:%d" % (label, node))
            return True
        if previous != value:
            self.conflicts.append(
                {
                    "key": key,
                    "reason": "mismatch",
                    "existing": previous,
                    "observed": value,
                    "label": label,
                    "node": node,
                }
            )
            self.variable.add(key)
            self.runs.pop(key, None)
            return False
        self.witness[key].append("%s:%d" % (label, node))
        return False

    def set_end(self, label: str, node: int, value: int) -> bool:
        seg = self.segments[label][node]
        low = seg["offset"] + seg["header"]
        high = seg["scope_end"]
        if value < low or value > high:
            self.conflicts.append(
                {
                    "key": seg["class_name"] + "@end",
                    "reason": "out_of_range",
                    "observed": value,
                    "low": low,
                    "high": high,
                    "label": label,
                    "node": node,
                }
            )
            return False
        current = self.end[(label, node)]
        if current is None:
            self.end[(label, node)] = value
            return True
        return False

    def pass_once(self) -> int:
        progress = 0
        for label, segments in self.segments.items():
            kids_all = self.kids[label]
            for node, seg in enumerate(segments):
                if seg["kind"] in NO_BODY_KINDS:
                    continue
                kids = kids_all[node]
                head = seg["offset"] + seg["header"]
                if not kids:
                    key = self.key(label, node, -2)
                    known = self.end[(label, node)]
                    if known is not None:
                        if self.set_run(key, known - head, label, node):
                            progress += 1
                    elif key in self.runs:
                        if self.set_end(label, node, head + self.runs[key]):
                            progress += 1
                    continue
                if self.set_run(
                    self.key(label, node, -1),
                    segments[kids[0]]["offset"] - head,
                    label,
                    node,
                ):
                    progress += 1
                for slot, child in enumerate(kids):
                    key = self.key(label, node, slot)
                    if slot + 1 < len(kids):
                        bound = segments[kids[slot + 1]]["offset"]
                    else:
                        bound = self.end[(label, node)]
                    child_end = self.end[(label, child)]
                    if bound is None and child_end is None:
                        continue
                    if bound is not None and child_end is not None:
                        if self.set_run(key, bound - child_end, label, node):
                            progress += 1
                    elif bound is not None and key in self.runs:
                        if self.set_end(label, child, bound - self.runs[key]):
                            progress += 1
                    elif child_end is not None and key in self.runs:
                        if self.set_end(label, node, child_end + self.runs[key]):
                            progress += 1
        return progress

    def solve(self, rounds: int = 400) -> None:
        attempts = 0
        while attempts < 40:
            attempts += 1
            before = len(self.variable)
            self.seed()
            for _ in range(rounds):
                if self.pass_once() == 0:
                    break
            if len(self.variable) == before:
                break

    def bodies(self) -> Dict[str, List[dict]]:
        result: Dict[str, List[dict]] = collections.defaultdict(list)
        for label, segments in self.segments.items():
            for i, seg in enumerate(segments):
                if seg["kind"] in NO_BODY_KINDS:
                    continue
                end = self.end[(label, i)]
                result[seg["class_name"]].append(
                    {
                        "label": label,
                        "node": i,
                        "kind": seg["kind"],
                        "depth": seg["depth"],
                        "children": len(self.kids[label][i]),
                        "span": seg["scope_end"] - seg["offset"] - seg["header"],
                        "body": None if end is None else end - seg["offset"] - seg["header"],
                    }
                )
        return result


def summarise(bodies: Dict[str, List[dict]], solver: Solver) -> dict:
    summary: Dict[str, dict] = {}
    for name, rows in sorted(bodies.items()):
        resolved = [r["body"] for r in rows if r["body"] is not None]
        counter = collections.Counter(resolved)
        own = {
            key: value
            for key, value in solver.runs.items()
            if key.rsplit("@", 1)[0] == name
        }
        variable = sorted(k for k in solver.variable if k.rsplit("@", 1)[0] == name)
        child_counts = sorted(collections.Counter(r["children"] for r in rows).items())
        scalar_total = None
        if len(child_counts) == 1 and not variable:
            slots = child_counts[0][0]
            if slots == 0:
                if name + "@leaf" in own:
                    scalar_total = own[name + "@leaf"]
            else:
                needed = [name + "@lead"] + ["%s@%d" % (name, j) for j in range(slots)]
                if all(k in own for k in needed):
                    scalar_total = sum(own[k] for k in needed)
        summary[name] = {
            "instances": len(rows),
            "resolved": len(resolved),
            "body_lengths": sorted(counter.items()),
            "child_counts": child_counts,
            "runs": dict(sorted(own.items())),
            "variable_runs": variable,
            "own_scalar_total": scalar_total,
        }
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--segments", default="re/data/segments")
    parser.add_argument("--labels", default="")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    traces = load_traces(args.segments, args.labels)
    solver = Solver(traces)
    solver.solve()
    bodies = solver.bodies()
    payload = {
        "traces": [t["label"] for t in traces],
        "run_keys": dict(sorted(solver.runs.items())),
        "variable_runs": sorted(solver.variable),
        "conflicts": solver.conflicts,
        "witnesses": {k: len(v) for k, v in sorted(solver.witness.items())},
        "classes": summarise(bodies, solver),
    }
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=1)
        handle.write("\n")
    total = sum(len(v) for v in bodies.values())
    resolved = sum(1 for v in bodies.values() for r in v if r["body"] is not None)
    print(
        "objects=%d resolved=%d runkeys=%d variable=%d conflicts=%d"
        % (total, resolved, len(solver.runs), len(solver.variable), len(solver.conflicts))
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
