from __future__ import annotations

import argparse
import collections
import json
from pathlib import Path
import sys
from typing import Dict, List, Mapping, Sequence, Tuple

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import solve_runs

ROOT = HERE.parents[2]
DEFAULT_SEGMENTS = ROOT / "re" / "data" / "segments"
DEFAULT_DECOMPILED = ROOT / "re" / "data" / "class_layouts_decompiled.json"
DEFAULT_OUT = ROOT / "re" / "data" / "class_layouts.json"
NO_BODY_KINDS = solve_runs.NO_BODY_KINDS
LEAD_RUN = "lead"
LEAF_RUN = "leaf"
REPEATED_SLOT = "..."
POLYMORPHIC_SLOT = "*"
SOLVED_SOURCE = "re/data/segments"
DECOMPILED_SOURCE = "re/data/class_layouts_decompiled.json"


def record_ends(trace: Mapping[str, object]) -> List[int]:
    segments = list(trace["segments"])
    total = int(trace["stream_length"])
    count = len(segments)
    children = solve_runs.children_of(segments)
    last = list(range(count))
    for node in range(count - 1, -1, -1):
        bound = node
        for child in children[node]:
            bound = max(bound, last[child])
        last[node] = bound
    ends: List[int] = []
    for node, item in enumerate(segments):
        if item["kind"] in NO_BODY_KINDS:
            ends.append(item["offset"] + item["header"])
            continue
        follower = last[node] + 1
        ends.append(segments[follower]["offset"] if follower < count else total)
    return ends


def contiguous(trace: Mapping[str, object]) -> bool:
    segments = list(trace["segments"])
    children = solve_runs.children_of(segments)
    reach: List[set] = [set() for _ in segments]
    for node in range(len(segments) - 1, -1, -1):
        acc: set = set()
        for child in children[node]:
            acc.add(child)
            acc |= reach[child]
        reach[node] = acc
    for node, descendants in enumerate(reach):
        if not descendants:
            continue
        if descendants != set(range(node + 1, max(descendants) + 1)):
            return False
    return True


class TilingSolver(solve_runs.Solver):
    def __init__(self, traces: Sequence[Mapping[str, object]]) -> None:
        super().__init__(traces)
        self.exact: Dict[str, List[int]] = {}
        for trace in traces:
            label = str(trace["label"])
            if not contiguous(trace):
                raise ValueError(f"trace {label} has interleaved object subtrees")
            self.exact[label] = record_ends(trace)

    def seed(self) -> None:
        super().seed()
        for label, ends in self.exact.items():
            for node, value in enumerate(ends):
                self.end[(label, node)] = value


def slot_names(
    solver: solve_runs.Solver,
) -> Dict[str, Dict[int, set]]:
    table: Dict[str, Dict[int, set]] = collections.defaultdict(
        lambda: collections.defaultdict(set)
    )
    for label, segments in solver.segments.items():
        kids = solver.kids[label]
        for node, item in enumerate(segments):
            if item["kind"] in NO_BODY_KINDS:
                continue
            for slot, child in enumerate(kids[node]):
                entry = segments[child]
                if entry["kind"] in NO_BODY_KINDS:
                    table[item["class_name"]][slot].add(POLYMORPHIC_SLOT)
                else:
                    table[item["class_name"]][slot].add(entry["class_name"])
    return table


def child_counts(solver: solve_runs.Solver) -> Dict[str, collections.Counter]:
    table: Dict[str, collections.Counter] = collections.defaultdict(
        collections.Counter
    )
    for label, segments in solver.segments.items():
        kids = solver.kids[label]
        for node, item in enumerate(segments):
            if item["kind"] in NO_BODY_KINDS:
                continue
            table[item["class_name"]][len(kids[node])] += 1
    return table


def observed_lengths(solver: solve_runs.Solver) -> Dict[str, collections.Counter]:
    table: Dict[str, collections.Counter] = collections.defaultdict(
        collections.Counter
    )
    for label, segments in solver.segments.items():
        kids = solver.kids[label]
        ends = solver.end
        for node, item in enumerate(segments):
            if item["kind"] in NO_BODY_KINDS:
                continue
            name = item["class_name"]
            head = item["offset"] + item["header"]
            slots = kids[node]
            own_end = ends[(label, node)]
            if not slots:
                if own_end is not None:
                    table[f"{name}@{LEAF_RUN}"][own_end - head] += 1
                continue
            table[f"{name}@{LEAD_RUN}"][segments[slots[0]]["offset"] - head] += 1
            for slot, child in enumerate(slots):
                bound = (
                    segments[slots[slot + 1]]["offset"]
                    if slot + 1 < len(slots)
                    else own_end
                )
                child_end = ends[(label, child)]
                if bound is None or child_end is None:
                    continue
                table[f"{name}@{slot}"][bound - child_end] += 1
    return table


def build_classes(
    solver: solve_runs.Solver,
) -> Tuple[Dict[str, dict], Dict[str, int]]:
    names = slot_names(solver)
    counts = child_counts(solver)
    lengths = observed_lengths(solver)
    classes: Dict[str, dict] = {}
    statistics = {"confirmed": 0, "partial": 0, "opaque_runs": 0}
    for name in sorted(counts):
        observed = counts[name]
        seen = sorted(observed)
        widest = seen[-1]
        slots: List[str] = []
        for slot in range(widest):
            candidates = names[name].get(slot, {POLYMORPHIC_SLOT})
            concrete = {item for item in candidates if item != POLYMORPHIC_SLOT}
            slots.append(concrete.pop() if len(concrete) == 1 else POLYMORPHIC_SLOT)
        varying = len(seen) > 1
        if varying:
            slots.append(REPEATED_SLOT)
        needed = (
            [LEAF_RUN]
            if widest == 0
            else [LEAD_RUN] + [str(slot) for slot in range(widest)]
        )
        runs: Dict[str, int] = {}
        variable: List[dict] = []
        for key in needed:
            full = f"{name}@{key}"
            if full in solver.runs:
                runs[key] = solver.runs[full]
                continue
            note = ", ".join(
                f"{length}x{tally}"
                for length, tally in sorted(lengths.get(full, {}).items())
            )
            variable.append(
                {
                    "slot": key,
                    "rule": "opaque",
                    "note": (
                        f"observed run lengths {note}"
                        if note
                        else "no traced instance resolves this run"
                    ),
                }
            )
            statistics["opaque_runs"] += 1
        repeat_note = ""
        if varying:
            tally = ", ".join(
                f"{count}x{times}" for count, times in sorted(observed.items())
            )
            repeat_note = f"child count varies across instances: {tally}"
        confidence = "confirmed" if not variable and not varying else "partial"
        statistics[confidence] += 1
        entry: Dict[str, object] = {
            "confidence": confidence,
            "source": SOLVED_SOURCE,
            "child_slots": slots,
            "instances": sum(observed.values()),
            "child_counts": [[count, times] for count, times in sorted(observed.items())],
            "runs": {key: runs[key] for key in needed if key in runs},
        }
        if varying:
            entry["repeat_count"] = None
            entry["repeat_note"] = repeat_note
        if variable:
            entry["variable_runs"] = variable
        classes[name] = entry
    return classes, statistics


def merge_decompiled(
    classes: Dict[str, dict], path: Path
) -> Tuple[Dict[str, dict], int]:
    if not path.is_file():
        return classes, 0
    payload = json.loads(path.read_text(encoding="utf-8"))
    incoming = payload.get("classes")
    if not isinstance(incoming, dict):
        raise ValueError(f"{path} has no classes mapping")
    merged = dict(classes)
    for name, entry in incoming.items():
        if not isinstance(entry, dict):
            raise ValueError(f"{path} entry for {name} is not an object")
        combined = dict(entry)
        combined["source"] = DECOMPILED_SOURCE
        merged[name] = combined
    return merged, len(incoming)


def generate(segments_dir: Path, decompiled: Path, labels: str) -> dict:
    traces = solve_runs.load_traces(str(segments_dir), labels)
    if not traces:
        raise ValueError(f"no segmentations found under {segments_dir}")
    solver = TilingSolver(traces)
    solver.solve()
    classes, statistics = build_classes(solver)
    classes, decompiled_count = merge_decompiled(classes, decompiled)
    return {
        "version": 1,
        "source": (
            f"{SOLVED_SOURCE} + {DECOMPILED_SOURCE}"
            if decompiled_count
            else SOLVED_SOURCE
        ),
        "traces": [str(trace["label"]) for trace in traces],
        "run_keys": len(solver.runs),
        "conflicting_run_keys": sorted(solver.variable),
        "run_derivation": (
            "solve_runs.Solver seeded with the exact record end of every traced "
            "object, taken from the contiguous preorder subtree of the recorded "
            "segmentation; a run is constant only when every traced instance agrees"
        ),
        "repeat_count_contract": (
            "a trailing ... entry in child_slots means the child count is not "
            "constant across the traced instances; repeat_count is null because no "
            "field holding the count has been recovered, and the static segmenter "
            "refuses such a class rather than guessing"
        ),
        "class_count": len(classes),
        "confirmed_classes": statistics["confirmed"],
        "partial_classes": statistics["partial"],
        "opaque_runs": statistics["opaque_runs"],
        "decompiled_classes": decompiled_count,
        "classes": dict(sorted(classes.items())),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--segments", default=str(DEFAULT_SEGMENTS))
    parser.add_argument("--decompiled", default=str(DEFAULT_DECOMPILED))
    parser.add_argument("--labels", default="")
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    arguments = parser.parse_args()
    payload = generate(
        Path(arguments.segments), Path(arguments.decompiled), arguments.labels
    )
    destination = Path(arguments.out)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=1)
        handle.write("\n")
    print(
        "classes=%d confirmed=%d partial=%d opaque_runs=%d decompiled=%d"
        % (
            payload["class_count"],
            payload["confirmed_classes"],
            payload["partial_classes"],
            payload["opaque_runs"],
            payload["decompiled_classes"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
