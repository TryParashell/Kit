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
    def __init__(self, traces: Sequence[dict], key_mode: str) -> None:
        self.traces = list(traces)
        self.key_mode = key_mode
        self.end: Dict[Tuple[str, int], Optional[int]] = {}
        self.runs: Dict[str, int] = {}
        self.run_evidence: Dict[str, List[dict]] = collections.defaultdict(list)
        self.conflicts: List[dict] = []
        self.trees: Dict[str, List[List[int]]] = {}
        for trace in self.traces:
            label = trace["label"]
            segments = trace["segments"]
            self.trees[label] = children_of(segments)
            for i, seg in enumerate(segments):
                if seg["kind"] in NO_BODY_KINDS:
                    self.end[(label, i)] = seg["offset"] + seg["header"]
                elif seg["depth"] == 0:
                    self.end[(label, i)] = seg["scope_end"]
                else:
                    self.end[(label, i)] = None

    def run_key(self, label: str, parent: int, slot: int) -> str:
        segments = self.trace(label)["segments"]
        name = segments[parent]["class_name"]
        if self.key_mode == "count":
            total = len(self.trees[label][parent])
            return "%s#%d@%d" % (name, total, slot)
        return "%s@%d" % (name, slot)

    def trace(self, label: str) -> dict:
        for trace in self.traces:
            if trace["label"] == label:
                return trace
        raise KeyError(label)

    def record_run(self, key: str, value: int, evidence: dict) -> bool:
        previous = self.runs.get(key)
        if previous is None:
            self.runs[key] = value
            self.run_evidence[key].append(evidence)
            return True
        if previous != value:
            self.conflicts.append(
                {"key": key, "existing": previous, "observed": value, **evidence}
            )
            return False
        self.run_evidence[key].append(evidence)
        return False

    def slot_limit(self, label: str, parent: int, slot: int) -> int:
        segments = self.trace(label)["segments"]
        kids = self.trees[label][parent]
        if slot + 1 < len(kids):
            return segments[kids[slot + 1]]["offset"]
        return segments[parent]["scope_end"]

    def pass_once(self) -> int:
        progress = 0
        for trace in self.traces:
            label = trace["label"]
            segments = trace["segments"]
            kids_all = self.trees[label]
            for parent, kids in enumerate(kids_all):
                if not kids:
                    continue
                if segments[parent]["kind"] in NO_BODY_KINDS:
                    continue
                head = segments[parent]["offset"] + segments[parent]["header"]
                key0 = self.run_key(label, parent, -1)
                if self.record_run(
                    key0,
                    segments[kids[0]]["offset"] - head,
                    {"label": label, "node": parent, "slot": "lead"},
                ):
                    progress += 1
                for slot, child in enumerate(kids):
                    limit = self.slot_limit(label, parent, slot)
                    key = self.run_key(label, parent, slot)
                    child_end = self.end[(label, child)]
                    is_last = slot + 1 == len(kids)
                    if child_end is not None:
                        if is_last and self.end[(label, parent)] is None:
                            continue
                        bound = (
                            self.end[(label, parent)]
                            if is_last
                            else limit
                        )
                        if bound is None:
                            continue
                        if self.record_run(
                            key,
                            bound - child_end,
                            {"label": label, "node": parent, "slot": slot},
                        ):
                            progress += 1
                    elif key in self.runs:
                        if is_last:
                            parent_end = self.end[(label, parent)]
                            if parent_end is None:
                                continue
                            value = parent_end - self.runs[key]
                        else:
                            value = limit - self.runs[key]
                        self.end[(label, child)] = value
                        progress += 1
                last = kids[-1]
                if (
                    self.end[(label, parent)] is None
                    and self.end[(label, last)] is not None
                ):
                    key = self.run_key(label, parent, len(kids) - 1)
                    if key in self.runs:
                        self.end[(label, parent)] = (
                            self.end[(label, last)] + self.runs[key]
                        )
                        progress += 1
        return progress

    def solve(self, rounds: int = 60) -> None:
        for _ in range(rounds):
            if self.pass_once() == 0:
                break

    def bodies(self) -> Dict[str, List[dict]]:
        result: Dict[str, List[dict]] = collections.defaultdict(list)
        for trace in self.traces:
            label = trace["label"]
            segments = trace["segments"]
            for i, seg in enumerate(segments):
                if seg["kind"] in NO_BODY_KINDS:
                    continue
                end = self.end[(label, i)]
                body = None
                if end is not None:
                    body = end - seg["offset"] - seg["header"]
                result[seg["class_name"]].append(
                    {
                        "label": label,
                        "node": i,
                        "kind": seg["kind"],
                        "depth": seg["depth"],
                        "children": len(self.trees[label][i]),
                        "span": seg["scope_end"] - seg["offset"] - seg["header"],
                        "body": body,
                    }
                )
        return result


def summarise(bodies: Dict[str, List[dict]], runs: Dict[str, int]) -> dict:
    summary: Dict[str, dict] = {}
    for name, rows in sorted(bodies.items()):
        resolved = [r["body"] for r in rows if r["body"] is not None]
        counter = collections.Counter(resolved)
        scalars = collections.Counter()
        for row in rows:
            if row["body"] is None:
                continue
        own = {}
        for key, value in runs.items():
            head = key.rsplit("@", 1)[0]
            if head.split("#")[0] == name:
                own[key] = value
        summary[name] = {
            "instances": len(rows),
            "resolved": len(resolved),
            "distinct_body_lengths": len(counter),
            "body_lengths": sorted(counter.items()),
            "child_counts": sorted(collections.Counter(r["children"] for r in rows).items()),
            "runs": dict(sorted(own.items())),
            "own_scalar_total": sum(own.values()) if own else None,
        }
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--segments", default="re/data/segments")
    parser.add_argument("--labels", default="")
    parser.add_argument("--key-mode", default="slot", choices=("slot", "count"))
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    traces = load_traces(args.segments, args.labels)
    solver = Solver(traces, args.key_mode)
    solver.solve()
    bodies = solver.bodies()
    payload = {
        "traces": [t["label"] for t in traces],
        "key_mode": args.key_mode,
        "run_keys": len(solver.runs),
        "conflicts": solver.conflicts,
        "runs": dict(sorted(solver.runs.items())),
        "classes": summarise(bodies, solver.runs),
    }
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=1)
        handle.write("\n")
    total = sum(len(v) for v in bodies.values())
    resolved = sum(1 for v in bodies.values() for r in v if r["body"] is not None)
    print(
        "objects=%d resolved=%d runkeys=%d conflicts=%d"
        % (total, resolved, len(solver.runs), len(solver.conflicts))
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
