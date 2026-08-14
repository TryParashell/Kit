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
import json
import pathlib
import re
import sys
from typing import Dict, List, Optional, Tuple

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(HERE))

from convert.adapters.solidworks.container.Container import SldprtArchive

from solve_runs import Solver, load_traces

STREAM = "Contents/Config-0-ResolvedFeatures"
NO_BODY_KINDS = ("null", "objectref")
BACKREF = re.compile(r"backref->(\d+)$")


def part_path(doc: dict) -> pathlib.Path:
    part = pathlib.Path(doc["part"])
    if part.exists():
        return part
    for base in (
        ROOT / ".rescratch/corpus/parts",
        ROOT / ".rescratch/corpus2",
        ROOT / ".rescratch/trace/parts",
        ROOT / "examples",
        ROOT / ".rescratch",
    ):
        hits = list(base.rglob(part.name))
        if hits:
            return hits[0]
    raise SystemExit("cannot locate part " + str(part))


def class_of(segments: List[dict], index: int) -> str:
    name = segments[index]["class_name"]
    match = BACKREF.match(name)
    if match:
        return segments[int(match.group(1))]["class_name"]
    return name


def fallback_runs(traces: List[dict]) -> Dict[str, Dict[str, int]]:
    solver = Solver(traces)
    solver.solve()
    table: Dict[str, Dict[str, int]] = collections.defaultdict(dict)
    for key, value in solver.runs.items():
        name, slot = key.rsplit("@", 1)
        table[name][slot] = value
    return table


def string_length(blob: bytes, at: int) -> Optional[int]:
    if blob[at : at + 3] != b"\xff\xfe\xff":
        return None
    marker = blob[at + 3]
    if marker == 0xFF:
        units = int.from_bytes(blob[at + 4 : at + 6], "little")
        return 6 + 2 * units
    return 4 + 2 * marker


def run_length(
    layout: dict, key: str, blob: bytes, start: int
) -> Tuple[Optional[int], str]:
    constant = layout.get("runs", {}).get(key)
    if constant is not None:
        return constant, "constant"
    entries = [e for e in layout.get("variable_runs", []) if e["slot"] == key]
    if not entries:
        return None, "undeclared"
    total = 0
    for entry in entries:
        rule = entry["rule"]
        if rule == "opaque":
            return None, "opaque"
        total += entry.get("at", 0)
        cursor = start + total
        if rule == "string":
            size = string_length(blob, cursor)
            if size is None:
                return None, "string marker absent at %d" % cursor
            total += size
        elif rule == "count":
            width = entry["count_width"]
            count = int.from_bytes(blob[cursor : cursor + width], "little")
            total += width + entry["stride"] * count
        elif rule == "conditional":
            width = entry["predicate_width"]
            offset = cursor + entry.get("predicate_at", 0)
            value = int.from_bytes(blob[offset : offset + width], "little")
            total += width
            if value in entry["values"]:
                total += entry["width"]
        else:
            return None, "unknown rule " + rule
        total += entry.get("tail", 0)
    return total, "rule"


class Walker:
    def __init__(
        self,
        segments: List[dict],
        blob: bytes,
        declared: Dict[str, dict],
        fallback: Dict[str, Dict[str, int]],
    ) -> None:
        self.segments = segments
        self.blob = blob
        self.declared = declared
        self.fallback = fallback
        self.kids: Dict[int, List[int]] = collections.defaultdict(list)
        for index, seg in enumerate(segments):
            if seg["parent"] >= 0:
                self.kids[seg["parent"]].append(index)
        self.order = sorted(
            range(len(segments)), key=lambda i: (segments[i]["offset"], i)
        )
        self.next_offset: Dict[int, Optional[int]] = {}
        for position, index in enumerate(self.order):
            head = segments[index]["offset"] + segments[index]["header"]
            found = None
            for other in self.order[position + 1 :]:
                if segments[other]["offset"] >= head:
                    found = segments[other]["offset"]
                    break
            self.next_offset[index] = found
        self.memo: Dict[int, Optional[int]] = {}
        self.active: set = set()

    def layout_for(self, index: int) -> Optional[dict]:
        name = class_of(self.segments, index)
        if name in self.declared:
            return self.declared[name]
        runs = self.fallback.get(name)
        if runs is None:
            return None
        return {"runs": runs, "variable_runs": [], "child_slots": None}

    def body_end(self, index: int) -> Optional[int]:
        if index in self.memo:
            return self.memo[index]
        if index in self.active:
            return None
        seg = self.segments[index]
        if seg["kind"] in NO_BODY_KINDS:
            self.memo[index] = seg["offset"] + seg["header"]
            return self.memo[index]
        self.active.add(index)
        result = self.compute(index)
        self.active.discard(index)
        self.memo[index] = result
        return result

    def compute(self, index: int) -> Optional[int]:
        seg = self.segments[index]
        head = seg["offset"] + seg["header"]
        layout = self.layout_for(index)
        if layout is None:
            return None
        slots = layout.get("child_slots")
        kids = self.kids[index]
        if slots == [] or not kids:
            size, _ = run_length(layout, "leaf", self.blob, head)
            return None if size is None else head + size
        cursor = head
        size, _ = run_length(layout, "lead", self.blob, cursor)
        if size is None:
            return None
        cursor += size
        for slot, kid in enumerate(kids):
            end = self.body_end(kid)
            if end is None:
                return None
            cursor = end
            size, _ = run_length(layout, str(slot), self.blob, cursor)
            if size is None:
                return None
            cursor += size
        return cursor

    def predicted_child_offsets(self, index: int) -> List[Tuple[int, int, int]]:
        seg = self.segments[index]
        head = seg["offset"] + seg["header"]
        layout = self.layout_for(index)
        out: List[Tuple[int, int, int]] = []
        if layout is None or layout.get("child_slots") == []:
            return out
        kids = self.kids[index]
        if not kids:
            return out
        size, _ = run_length(layout, "lead", self.blob, head)
        if size is not None:
            out.append((-1, head + size, self.segments[kids[0]]["offset"]))
        for slot, kid in enumerate(kids):
            end = self.body_end(kid)
            if end is None:
                continue
            size, _ = run_length(layout, str(slot), self.blob, end)
            if size is None:
                continue
            if slot + 1 < len(kids):
                out.append((slot, end + size, self.segments[kids[slot + 1]]["offset"]))
            elif seg["depth"] == 0:
                out.append((slot, end + size, seg["scope_end"]))
        return out

    def bound(self, index: int) -> int:
        seg = self.segments[index]
        head = seg["offset"] + seg["header"]
        layout = self.layout_for(index)
        kids = self.kids[index]
        leaf = layout is not None and layout.get("child_slots") == []
        start = head
        if kids and not leaf:
            start = max(head, self.segments[kids[-1]]["scope_end"])
        limit = seg["scope_end"]
        for other in self.order:
            offset = self.segments[other]["offset"]
            if offset >= start:
                limit = min(limit, offset)
                break
        return limit - head


def verify(layouts: dict, segments_dir: pathlib.Path) -> dict:
    traces = load_traces(str(segments_dir), "")
    fallback = fallback_runs(traces)
    declared = layouts["classes"]
    blobs = {}
    for trace in traces:
        blobs[trace["label"]] = SldprtArchive.open(part_path(trace)).require(STREAM)
    report: Dict[str, dict] = {
        name: {
            "confidence": spec.get("confidence", "not found"),
            "instances": 0,
            "computed": 0,
            "exact_span": 0,
            "overruns": [],
            "run_checks": 0,
            "run_mismatches": [],
            "unresolved": 0,
            "traced_children_ignored": 0,
            "declared_leaf": spec.get("child_slots") == [],
        }
        for name, spec in declared.items()
    }
    for trace in traces:
        label = trace["label"]
        segments = trace["segments"]
        walker = Walker(segments, blobs[label], declared, fallback)
        for index, seg in enumerate(segments):
            if seg["kind"] in NO_BODY_KINDS:
                continue
            name = class_of(segments, index)
            if name not in declared:
                continue
            row = report[name]
            row["instances"] += 1
            head = seg["offset"] + seg["header"]
            gap = walker.bound(index)
            if row["declared_leaf"] and walker.kids[index]:
                row["traced_children_ignored"] += 1
            end = walker.body_end(index)
            if end is None:
                row["unresolved"] += 1
            else:
                row["computed"] += 1
                length = end - head
                if length > gap:
                    row["overruns"].append(
                        {
                            "label": label,
                            "node": index,
                            "computed": length,
                            "gap": gap,
                        }
                    )
                elif length == gap:
                    row["exact_span"] += 1
                if seg["depth"] == 0 and end != seg["scope_end"]:
                    row["overruns"].append(
                        {
                            "label": label,
                            "node": index,
                            "computed": length,
                            "gap": seg["scope_end"] - head,
                            "reason": "top level object must tile exactly",
                        }
                    )
            for slot, predicted, observed in walker.predicted_child_offsets(index):
                row["run_checks"] += 1
                if predicted != observed:
                    row["run_mismatches"].append(
                        {
                            "label": label,
                            "node": index,
                            "run": "lead" if slot < 0 else str(slot),
                            "expected": observed,
                            "computed": predicted,
                        }
                    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--layouts", default=str(ROOT / "re/data/Layouts/ClassLayoutsDecompiled.json")
    )
    parser.add_argument("--segments", default=str(ROOT / "re/data/segments"))
    parser.add_argument("--out", default="")
    args = parser.parse_args()
    layouts = json.loads(pathlib.Path(args.layouts).read_text(encoding="utf-8"))
    report = verify(layouts, pathlib.Path(args.segments))
    failures = 0
    print(
        "%-24s %-9s %5s %5s %5s %5s %6s %5s %5s"
        % (
            "class",
            "claim",
            "inst",
            "comp",
            "exact",
            "unres",
            "runchk",
            "runX",
            "over",
        )
    )
    for name in sorted(report):
        row = report[name]
        bad = len(row["run_mismatches"]) + len(row["overruns"])
        if row["confidence"] == "confirmed" and bad:
            failures += bad
        print(
            "%-24s %-9s %5d %5d %5d %5d %6d %5d %5d"
            % (
                name,
                row["confidence"],
                row["instances"],
                row["computed"],
                row["exact_span"],
                row["unresolved"],
                row["run_checks"],
                len(row["run_mismatches"]),
                len(row["overruns"]),
            )
        )
    for name in sorted(report):
        row = report[name]
        for item in row["overruns"]:
            print(
                "OVERRUN  %-22s %-16s node=%-4d computed=%-6d gap=%-6d %s"
                % (
                    name,
                    item["label"],
                    item["node"],
                    item["computed"],
                    item["gap"],
                    item.get("reason", ""),
                )
            )
        for item in row["run_mismatches"]:
            print(
                "MISMATCH %-22s %-16s node=%-4d run=%-4s expected=%-6d computed=%-6d"
                % (
                    name,
                    item["label"],
                    item["node"],
                    item["run"],
                    item["expected"],
                    item["computed"],
                )
            )
    for name in sorted(report):
        row = report[name]
        if row["traced_children_ignored"]:
            print(
                "NOTE     %-22s %d instances carry traced children that its Serialize does not read"
                % (name, row["traced_children_ignored"])
            )
    print(
        "classes=%d confirmed=%d failures=%d"
        % (
            len(report),
            sum(1 for r in report.values() if r["confidence"] == "confirmed"),
            failures,
        )
    )
    if args.out:
        pathlib.Path(args.out).write_text(
            json.dumps(report, indent=1), encoding="utf-8"
        )
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
