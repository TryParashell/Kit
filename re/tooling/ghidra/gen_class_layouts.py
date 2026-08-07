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
DEFAULT_EXTERNAL = ROOT / "re" / "data" / "external_classes.json"
DEFAULT_VERSIONED = ROOT / "re" / "data" / "class_layouts_versioned.json"
DEFAULT_OUT = ROOT / "re" / "data" / "class_layouts.json"
EXTERNAL_SOURCE = "re/data/external_classes.json"
EXTERNAL_PREFIX = "external#"
PINNED_EXTERNAL_SLOTS = ("component", "object_list", "pmark_record")
NO_BODY_KINDS = solve_runs.NO_BODY_KINDS
LEAD_RUN = "lead"
LEAF_RUN = "leaf"
REPEATED_SLOT = "..."
POLYMORPHIC_SLOT = "*"
SOLVED_SOURCE = "re/data/segments"
DECOMPILED_SOURCE = "re/data/class_layouts_decompiled.json"
VERSIONED_SOURCE = "re/data/class_layouts_versioned.json"


def reparented(
    segments: Sequence[Mapping[str, object]],
) -> Tuple[List[List[int]], List[int]]:
    kids = solve_runs.children_of(segments)
    parents = [int(item["parent"]) for item in segments]
    for node in range(len(segments) - 1, -1, -1):
        if segments[node]["kind"] not in NO_BODY_KINDS or not kids[node]:
            continue
        owner = parents[node]
        moved = kids[node]
        kids[node] = []
        for child in moved:
            parents[child] = owner
        if owner >= 0:
            kids[owner] = sorted(kids[owner] + moved)
    return kids, parents


def record_ends(trace: Mapping[str, object]) -> List[int]:
    segments = list(trace["segments"])
    total = int(trace["stream_length"])
    count = len(segments)
    children = reparented(segments)[0]
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
    children = reparented(segments)[0]
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
        self.parents: Dict[str, List[int]] = {}
        for trace in traces:
            label = str(trace["label"])
            if not contiguous(trace):
                raise ValueError(f"trace {label} has interleaved object subtrees")
            kids, parents = reparented(list(trace["segments"]))
            self.kids[label] = kids
            self.parents[label] = parents
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
    table: Dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    for label, segments in solver.segments.items():
        kids = solver.kids[label]
        for node, item in enumerate(segments):
            if item["kind"] in NO_BODY_KINDS:
                continue
            table[item["class_name"]][len(kids[node])] += 1
    return table


def observed_lengths(solver: solve_runs.Solver) -> Dict[str, collections.Counter]:
    table: Dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
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


def leaf_instances(
    solver: TilingSolver,
) -> Dict[str, List[dict]]:
    table: Dict[str, List[dict]] = collections.defaultdict(list)
    for label, segments in solver.segments.items():
        kids = solver.kids[label]
        for node, item in enumerate(segments):
            if item["kind"] in NO_BODY_KINDS or kids[node]:
                continue
            end = solver.end[(label, node)]
            if end is None:
                continue
            parent = solver.parents[label][node]
            if parent < 0:
                context = ("<root>", -1)
            else:
                context = (
                    segments[parent]["class_name"],
                    kids[parent].index(node),
                )
            table[item["class_name"]].append(
                {
                    "label": label,
                    "node": node,
                    "head": item["offset"] + item["header"],
                    "span": end - item["offset"] - item["header"],
                    "context": context,
                }
            )
    return table


def string_length(blob: bytes, offset: int) -> int:
    if blob[offset : offset + 3] != b"\xff\xfe\xff":
        return -1
    units = blob[offset + 3]
    head = 4
    if units == 0xFF:
        units = int.from_bytes(blob[offset + 4 : offset + 6], "little")
        head = 6
    end = offset + head + 2 * units
    if end > len(blob):
        return -1
    return head + 2 * units


def rebalance_string_leaves(
    solver: solve_runs.Solver, streams: Mapping[str, bytes]
) -> Tuple[Dict[str, int], Dict[Tuple[str, int], int]]:
    tails: Dict[str, int] = {}
    shifts: Dict[Tuple[str, int], int] = {}
    for name, rows in sorted(leaf_instances(solver).items()):
        if any(row["label"] not in streams for row in rows):
            continue
        spans = {row["span"] for row in rows}
        if len(spans) < 2:
            continue
        measured: List[Tuple[dict, int]] = []
        for row in rows:
            length = string_length(streams[row["label"]], row["head"])
            if length < 0 or length > row["span"]:
                measured = []
                break
            measured.append((row, row["span"] - length))
        if not measured:
            continue
        floor = min(tail for _, tail in measured)
        deltas: Dict[Tuple[str, int], set] = collections.defaultdict(set)
        for row, tail in measured:
            deltas[row["context"]].add(tail - floor)
        if any(len(values) != 1 for values in deltas.values()):
            continue
        owners = slot_owners(solver)
        conflict = False
        for context, values in deltas.items():
            delta = next(iter(values))
            if delta and (context == ("<root>", -1) or owners.get(context) != {name}):
                conflict = True
        if conflict:
            continue
        tails[name] = floor
        for context, values in deltas.items():
            delta = next(iter(values))
            if delta:
                shifts[context] = shifts.get(context, 0) + delta
    return tails, shifts


def slot_owners(solver: solve_runs.Solver) -> Dict[Tuple[str, int], set]:
    table: Dict[Tuple[str, int], set] = collections.defaultdict(set)
    for label, segments in solver.segments.items():
        kids = solver.kids[label]
        for node, item in enumerate(segments):
            if item["kind"] in NO_BODY_KINDS:
                continue
            for slot, child in enumerate(kids[node]):
                entry = segments[child]
                table[(item["class_name"], slot)].add(
                    POLYMORPHIC_SLOT
                    if entry["kind"] in NO_BODY_KINDS
                    else entry["class_name"]
                )
    return table


def parent_instances(solver: solve_runs.Solver) -> Dict[str, List[dict]]:
    table: Dict[str, List[dict]] = collections.defaultdict(list)
    for label, segments in solver.segments.items():
        kids = solver.kids[label]
        for node, item in enumerate(segments):
            if item["kind"] in NO_BODY_KINDS or not kids[node]:
                continue
            own_end = solver.end[(label, node)]
            if own_end is None:
                continue
            slots = kids[node]
            child_ends = [solver.end[(label, child)] for child in slots]
            if any(value is None for value in child_ends):
                continue
            table[item["class_name"]].append(
                {
                    "label": label,
                    "head": item["offset"] + item["header"],
                    "offsets": [segments[child]["offset"] for child in slots],
                    "ends": child_ends,
                    "names": [
                        (
                            POLYMORPHIC_SLOT
                            if segments[child]["kind"] in NO_BODY_KINDS
                            else segments[child]["class_name"]
                        )
                        for child in slots
                    ],
                    "own_end": own_end,
                }
            )
    return table


def repeat_shape(
    solver: solve_runs.Solver, streams: Mapping[str, bytes], name: str
) -> dict | None:
    rows = parent_instances(solver).get(name, [])
    if not rows or any(row["label"] not in streams for row in rows):
        return None
    if len({len(row["names"]) for row in rows}) < 2:
        return None
    smallest = min(len(row["names"]) for row in rows)
    for template in range(smallest + 1):
        templates = {
            row["names"][slot]
            for row in rows
            for slot in range(template, len(row["names"]))
        }
        if len(templates) != 1 or POLYMORPHIC_SLOT in templates:
            continue
        values = set()
        for row in rows:
            for slot in range(template, len(row["names"])):
                bound = (
                    row["offsets"][slot + 1]
                    if slot + 1 < len(row["names"])
                    else row["own_end"]
                )
                values.add(bound - row["ends"][slot])
        if len(values) != 1:
            continue
        run = LEAD_RUN if template == 0 else str(template - 1)
        if template == 0:
            starts = [row["head"] for row in rows]
        else:
            starts = [row["ends"][template - 1] for row in rows]
        bounds = [
            (
                row["offsets"][template]
                if template < len(row["offsets"])
                else row["own_end"]
            )
            for row in rows
        ]
        span = min(bound - start for bound, start in zip(bounds, starts))
        if span <= 0:
            continue
        for width in (2, 4):
            for at in range(0, max(span - width + 1, 0)):
                if all(
                    int.from_bytes(
                        streams[row["label"]][start + at : start + at + width],
                        "little",
                    )
                    == len(row["names"]) - template
                    for row, start in zip(rows, starts)
                ):
                    return {
                        "template": template,
                        "name": next(iter(templates)),
                        "run": run,
                        "at": at,
                        "width": width,
                        "template_run": next(iter(values)),
                    }
    return None


def build_classes(
    solver: solve_runs.Solver,
    streams: Mapping[str, bytes],
) -> Tuple[Dict[str, dict], Dict[str, int]]:
    names = slot_names(solver)
    counts = child_counts(solver)
    lengths = observed_lengths(solver)
    string_tails, slot_shifts = rebalance_string_leaves(solver, streams)
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
        shape = repeat_shape(solver, streams, name) if varying else None
        if shape is not None:
            slots = slots[: shape["template"]] + [shape["name"], REPEATED_SLOT]
        elif varying:
            slots.append(REPEATED_SLOT)
        if shape is not None:
            needed = [LEAD_RUN] + [str(slot) for slot in range(shape["template"] + 1)]
        elif widest == 0:
            needed = [LEAF_RUN]
        else:
            needed = [LEAD_RUN] + [str(slot) for slot in range(widest)]
        runs: Dict[str, int] = {}
        variable: List[dict] = []
        opaque = 0
        for key in needed:
            full = f"{name}@{key}"
            if shape is not None and key == str(shape["template"]):
                runs[key] = shape["template_run"]
                continue
            if full in solver.runs:
                value = solver.runs[full]
                if key not in (LEAD_RUN, LEAF_RUN):
                    value += slot_shifts.get((name, int(key)), 0)
                runs[key] = value
                continue
            if key == LEAF_RUN and name in string_tails:
                variable.append(
                    {
                        "slot": LEAF_RUN,
                        "rule": "string",
                        "at": 0,
                        "tail": string_tails[name],
                        "note": (
                            "every traced instance opens with an ff fe ff string and "
                            f"closes with {string_tails[name]} constant bytes"
                        ),
                    }
                )
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
            opaque += 1
        repeat_note = ""
        if varying:
            tally = ", ".join(
                f"{count}x{times}" for count, times in sorted(observed.items())
            )
            repeat_note = f"child count varies across instances: {tally}"
            if shape is not None:
                repeat_note += (
                    f"; the count sits in run {shape['run']} at offset "
                    f"{shape['at']} as a {shape['width']} byte value and the "
                    f"repeated slot holds {shape['name']}"
                )
        confidence = (
            "confirmed"
            if not opaque and (not varying or shape is not None)
            else "partial"
        )
        statistics[confidence] += 1
        entry: Dict[str, object] = {
            "confidence": confidence,
            "source": SOLVED_SOURCE,
            "child_slots": slots,
            "instances": sum(observed.values()),
            "child_counts": [
                [count, times] for count, times in sorted(observed.items())
            ],
            "runs": {key: runs[key] for key in needed if key in runs},
        }
        if varying:
            entry["repeat_count"] = (
                None
                if shape is None
                else {
                    "run": shape["run"],
                    "at": shape["at"],
                    "width": shape["width"],
                }
            )
            entry["repeat_note"] = repeat_note
        if variable:
            entry["variable_runs"] = variable
        classes[name] = entry
    return classes, statistics


def merge_authored(
    classes: Dict[str, dict], path: Path, source: str
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
        combined["source"] = source
        merged[name] = combined
    return merged, len(incoming)


def merge_decompiled(
    classes: Dict[str, dict], path: Path
) -> Tuple[Dict[str, dict], int]:
    return merge_authored(classes, path, DECOMPILED_SOURCE)


def merge_versioned(
    classes: Dict[str, dict], path: Path
) -> Tuple[Dict[str, dict], int]:
    return merge_authored(classes, path, VERSIONED_SOURCE)


def _external_layout(slot: str, record: Mapping[str, object]) -> dict:
    name = str(record["class_name"])
    bodies = [int(value) for value in record["own_body_lengths"]]
    if len(bodies) != 1:
        raise ValueError(
            f"external slot {slot} has {len(bodies)} own body lengths; "
            "a pinned slot must have exactly one"
        )
    body = bodies[0]
    entry: Dict[str, object] = {
        "confidence": str(record["confidence"]),
        "source": EXTERNAL_SOURCE,
        "external_class": name,
        "instances": sum(
            int(value) for value in record["occurrences_per_trace"].values()
        ),
        "note": (
            f"resolved to {name}; own body is {body} bytes by "
            f"{record['decompiled_serialize']}. The traced spans "
            f"{record['traced_span_lengths']} are longer because bytes an ancestor "
            "reads after this object returns are absorbed into its row, so they "
            "belong to the ancestor run and not to this class."
        ),
    }
    if slot == "component":
        entry["child_slots"] = [POLYMORPHIC_SLOT]
        entry["runs"] = {LEAD_RUN: body, "0": 0}
        return entry
    if slot == "pmark_record":
        entry["child_slots"] = []
        entry["runs"] = {LEAF_RUN: body}
        return entry
    if slot == "object_list":
        entry["child_slots"] = [POLYMORPHIC_SLOT, REPEATED_SLOT]
        entry["runs"] = {LEAD_RUN: body, "0": 0}
        entry["repeat_count"] = {"run": LEAD_RUN, "at": 0, "width": 2}
        entry["repeat_note"] = (
            "u16 element count in the lead run followed by that many nested objects"
        )
        return entry
    raise ValueError(f"external slot {slot} has no pinned layout rule")


def merge_external(
    classes: Dict[str, dict], path: Path
) -> Tuple[Dict[str, dict], int, Dict[str, List[str]]]:
    if not path.is_file():
        return classes, 0, {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    slots = payload.get("slots")
    if not isinstance(slots, dict):
        raise ValueError(f"{path} has no slots mapping")
    merged = dict(classes)
    bindings: Dict[str, List[str]] = {}
    pinned = 0
    for slot in PINNED_EXTERNAL_SLOTS:
        record = slots.get(slot)
        if not isinstance(record, dict):
            raise ValueError(f"{path} has no {slot} slot")
        entry = _external_layout(slot, record)
        indices = sorted(
            {int(value) for value in record["class_index_per_trace"].values()}
        )
        aliases = [f"{EXTERNAL_PREFIX}{index}" for index in indices]
        bindings[str(record["class_name"])] = aliases
        for alias in aliases:
            merged[alias] = dict(entry)
            pinned += 1
        merged[str(record["class_name"])] = dict(entry)
    return merged, pinned, bindings


def external_slot_classes(
    solver: solve_runs.Solver, aliases: Mapping[str, str]
) -> Dict[Tuple[str, int], str]:
    table: Dict[Tuple[str, int], set] = collections.defaultdict(set)
    for label, segments in solver.segments.items():
        kids = solver.kids[label]
        for node, item in enumerate(segments):
            if item["kind"] in NO_BODY_KINDS:
                continue
            for slot, child in enumerate(kids[node]):
                entry = segments[child]
                if entry["kind"] in NO_BODY_KINDS:
                    continue
                resolved = aliases.get(str(entry["class_name"]))
                if resolved is not None:
                    table[(str(item["class_name"]), slot)].add(resolved)
    return {key: next(iter(value)) for key, value in table.items() if len(value) == 1}


def bind_external_slots(
    classes: Dict[str, dict],
    table: Mapping[Tuple[str, int], str],
    aliases: Mapping[str, str],
) -> Tuple[Dict[str, dict], List[dict]]:
    merged = dict(classes)
    bound: List[dict] = []
    for (parent, slot), resolved in sorted(table.items()):
        entry = merged.get(parent)
        if entry is None or resolved not in merged:
            continue
        slots = list(entry.get("child_slots", ()))
        if slot >= len(slots):
            continue
        if REPEATED_SLOT in slots and slot >= len(slots) - 2:
            continue
        current = str(slots[slot])
        if current == resolved:
            continue
        if current != POLYMORPHIC_SLOT and current not in aliases:
            continue
        slots[slot] = resolved
        updated = dict(entry)
        updated["child_slots"] = slots
        merged[parent] = updated
        bound.append({"class": parent, "slot": slot, "was": current, "now": resolved})
    return merged, bound


def traced_streams(traces: Sequence[Mapping[str, object]]) -> Dict[str, bytes]:
    sys.path.insert(0, str(ROOT / "src"))
    from convert.adapters.solidworks.container import SldprtArchive
    from convert.adapters.solidworks.format import RESOLVED_FEATURES_STREAM

    streams: Dict[str, bytes] = {}
    for trace in traces:
        part = Path(str(trace["part"]))
        if not part.is_file():
            continue
        blob = SldprtArchive.from_bytes(part.read_bytes()).streams[
            RESOLVED_FEATURES_STREAM
        ]
        if len(blob) != int(trace["stream_length"]):
            continue
        streams[str(trace["label"])] = blob
    return streams


def generate(
    segments_dir: Path,
    decompiled: Path,
    external: Path,
    versioned: Path,
    labels: str,
) -> dict:
    traces = solve_runs.load_traces(str(segments_dir), labels)
    if not traces:
        raise ValueError(f"no segmentations found under {segments_dir}")
    solver = TilingSolver(traces)
    solver.solve()
    streams = traced_streams(traces)
    classes, statistics = build_classes(solver, streams)
    classes, decompiled_count = merge_decompiled(classes, decompiled)
    classes, versioned_count = merge_versioned(classes, versioned)
    classes, external_count, external_bindings = merge_external(classes, external)
    aliases = {
        alias: name for name, group in external_bindings.items() for alias in group
    }
    classes, bound_slots = bind_external_slots(
        classes, external_slot_classes(solver, aliases), aliases
    )
    gated = sorted(
        name for name, entry in classes.items() if "runs_by_version" in entry
    )
    return {
        "external_classes": external_count,
        "external_bindings": external_bindings,
        "external_slot_bindings": bound_slots,
        "external_slot_binding_contract": (
            "a child slot whose traced occupant is one of the resolved external "
            "classes carries that class name rather than the document specific "
            "external#<index> alias, so the segmenter binds an unknown below base "
            "class index from the class the parent Serialize is recorded to read at "
            "that position instead of from the index; a slot is only bound when every "
            "traced occupant of it resolves to the same class, and a slot at or past a "
            "repeated template is left alone because rewriting it would move the "
            "template"
        ),
        "streams_read_for_string_rules": sorted(streams),
        "version": 1,
        "source": " + ".join(
            [SOLVED_SOURCE]
            + ([DECOMPILED_SOURCE] if decompiled_count else [])
            + ([VERSIONED_SOURCE] if versioned_count else [])
            + ([EXTERNAL_SOURCE] if external_count else [])
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
        "versioned_classes": versioned_count,
        "version_gated_classes": gated,
        "version_gate_contract": (
            "runs_by_version maps a run key to a mapping from document version to run "
            "length; the segmenter consults it before runs, falls back to runs when "
            "the version is unknown or absent from the mapping, and refuses the class "
            "when neither names the run"
        ),
        "classes": dict(sorted(classes.items())),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--segments", default=str(DEFAULT_SEGMENTS))
    parser.add_argument("--decompiled", default=str(DEFAULT_DECOMPILED))
    parser.add_argument("--external", default=str(DEFAULT_EXTERNAL))
    parser.add_argument("--versioned", default=str(DEFAULT_VERSIONED))
    parser.add_argument("--labels", default="")
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    arguments = parser.parse_args()
    payload = generate(
        Path(arguments.segments),
        Path(arguments.decompiled),
        Path(arguments.external),
        Path(arguments.versioned),
        arguments.labels,
    )
    destination = Path(arguments.out)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=1)
        handle.write("\n")
    print(
        "classes=%d confirmed=%d partial=%d opaque_runs=%d decompiled=%d "
        "versioned=%d version_gated=%d external=%d"
        % (
            payload["class_count"],
            payload["confirmed_classes"],
            payload["partial_classes"],
            payload["opaque_runs"],
            payload["decompiled_classes"],
            payload["versioned_classes"],
            len(payload["version_gated_classes"]),
            payload["external_classes"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
