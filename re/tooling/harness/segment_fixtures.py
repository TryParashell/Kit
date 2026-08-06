from __future__ import annotations

import argparse
import collections
import json
from pathlib import Path
import struct
import sys
from typing import Dict, List, Tuple

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
for candidate in (str(ROOT / "src"),):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from convert.adapters.solidworks.archive import (
    LayoutTable,
    STREAM_HEADER_SIZE,
    VerifyReport,
    verify,
)

DEFAULT_FIXTURES = ROOT / "tests" / "fixtures" / "solidworks" / "donors"
DEFAULT_LAYOUTS = ROOT / "re" / "data" / "class_layouts.json"
DEFAULT_SEGMENTS = ROOT / "re" / "data" / "segments"
FEATURE_COUNT_OFFSET = 604
FIRST_FEATURE_BASE = 109
BASE_SEARCH_SPAN = 12


CLASS_DEFINITION_MARKER = b"\xff\xff\x01\x00"


def scanned_class_names(blob: bytes) -> List[str]:
    found: List[str] = []
    cursor = blob.find(CLASS_DEFINITION_MARKER)
    while cursor >= 0:
        units = struct.unpack_from("<H", blob, cursor + 4)[0]
        end = cursor + 6 + units
        if 0 < units < 64 and end <= len(blob):
            raw = blob[cursor + 6 : end]
            if all(32 <= byte < 127 for byte in raw):
                name = raw.decode("ascii")
                if name not in found:
                    found.append(name)
        cursor = blob.find(CLASS_DEFINITION_MARKER, cursor + 1)
    return found


def fixture_feature_count(donor: Path) -> int:
    meta = donor / "meta.json"
    if not meta.is_file():
        return -1
    payload = json.loads(meta.read_text(encoding="utf-8"))
    features = payload.get("features")
    return len(features) if isinstance(features, list) else -1


def recorded_bases(segments_dir: Path) -> Dict[str, int]:
    table: Dict[str, int] = {}
    for path in sorted(segments_dir.glob("segments_*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        table[str(payload["label"])] = int(payload["base_map_index"])
    return table


def derived_base(blob: bytes) -> Tuple[int, str]:
    if len(blob) < FEATURE_COUNT_OFFSET + 2:
        return FIRST_FEATURE_BASE, "stream too short for the history array length"
    doubled = struct.unpack_from("<H", blob, FEATURE_COUNT_OFFSET)[0]
    if doubled < 2 or doubled % 2:
        return (
            FIRST_FEATURE_BASE,
            f"history array length {doubled} at byte {FEATURE_COUNT_OFFSET} "
            "is not twice a positive feature count",
        )
    features = doubled // 2
    return (
        FIRST_FEATURE_BASE + features - 1,
        f"history array length {doubled} at byte {FEATURE_COUNT_OFFSET} "
        f"gives {features} features",
    )


def best_base(
    blob: bytes, layouts: LayoutTable, start: int
) -> Tuple[int, str, VerifyReport]:
    first = verify(blob, start, layouts, header_size=STREAM_HEADER_SIZE)
    if first.identical:
        return start, "derived", first
    candidates = [
        candidate
        for candidate in range(
            max(1, start - BASE_SEARCH_SPAN), start + BASE_SEARCH_SPAN + 1
        )
        if candidate != start
    ]
    best = first
    for candidate in candidates:
        report = verify(blob, candidate, layouts, header_size=STREAM_HEADER_SIZE)
        if report.identical:
            return candidate, "searched", report
        if report.segmented and not best.segmented:
            best = report
    return start, "derived", best


def run(fixtures: Path, layouts_path: Path, segments_dir: Path) -> dict:
    layouts = LayoutTable.load(layouts_path)
    donors = sorted(
        path for path in fixtures.iterdir() if (path / "resolved.bin").is_file()
    )
    if not donors:
        raise ValueError(f"no donor fixtures with resolved.bin under {fixtures}")
    partial = {
        name
        for name, entry in layouts.classes.items()
        if entry.confidence != "confirmed"
    }
    rows: List[dict] = []
    blockers: collections.Counter = collections.Counter()
    required: collections.Counter = collections.Counter()
    for donor in donors:
        blob = (donor / "resolved.bin").read_bytes()
        start, rule = derived_base(blob)
        base, method, report = best_base(blob, layouts, start)
        meta_features = fixture_feature_count(donor)
        scanned = scanned_class_names(blob)
        outstanding = sorted(name for name in scanned if name in partial)
        unknown = sorted(name for name in scanned if name not in layouts.classes)
        for name in outstanding:
            required[name] += 1
        row = {"donor": donor.name, "base_rule": rule, "base_method": method}
        row.update(report.as_dict())
        row["base"] = base
        row["meta_feature_count"] = meta_features
        row["meta_base"] = (
            FIRST_FEATURE_BASE + meta_features - 1 if meta_features > 0 else -1
        )
        row["base_agrees_with_meta"] = row["meta_base"] == base
        row["scanned_class_count"] = len(scanned)
        row["outstanding_partial_classes"] = outstanding
        row["classes_absent_from_layout_table"] = unknown
        rows.append(row)
        if not report.identical:
            label = (
                f"{report.blocking_class}@{report.blocking_slot}"
                if report.blocking_class
                else "<none>"
            )
            blockers[label] += 1
    verified = [row for row in rows if row["identical"]]
    return {
        "fixtures": str(fixtures),
        "layouts": str(layouts_path),
        "layout_source": layouts.source,
        "class_count": len(layouts.classes),
        "confirmed_classes": sum(
            1
            for entry in layouts.classes.values()
            if entry.confidence == "confirmed"
        ),
        "donor_count": len(rows),
        "segmented_count": sum(1 for row in rows if row["segmented"]),
        "tiled_count": sum(1 for row in rows if row["tiled"]),
        "identical_count": len(verified),
        "identical_donors": [row["donor"] for row in verified],
        "blocking_runs": dict(sorted(blockers.items(), key=lambda pair: -pair[1])),
        "partial_classes": sorted(partial),
        "outstanding_classes_by_donor_count": dict(
            sorted(required.items(), key=lambda pair: (-pair[1], pair[0]))
        ),
        "class_scan_caveat": (
            "the per donor class name list comes from a static ff ff 01 00 scan, "
            "which over approximates because the marker also occurs inside object "
            "bodies; it is a lower bound on the layout work each donor needs, not a "
            "segmentation"
        ),
        "recorded_trace_bases": recorded_bases(segments_dir),
        "bases_agreeing_with_fixture_metadata": sum(
            1 for row in rows if row["base_agrees_with_meta"]
        ),
        "bases_disagreeing_with_fixture_metadata": [
            {
                "donor": row["donor"],
                "derived": row["base"],
                "from_metadata": row["meta_base"],
            }
            for row in rows
            if not row["base_agrees_with_meta"]
        ],
        "base_derivation": (
            "base = 109 + feature_count - 1 where 2 * feature_count is the u16 at "
            f"stream byte {FEATURE_COUNT_OFFSET}; when the derived base does not "
            f"produce a byte identical re-emit, bases within {BASE_SEARCH_SPAN} of "
            "it are searched and the method column records which one was used; the "
            "derived value is cross checked against 109 + feature_count - 1 taken "
            "from each fixture meta.json, and the disagreements are listed because "
            "segmentation stops too early to settle them independently"
        ),
        "donors": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixtures", default=str(DEFAULT_FIXTURES))
    parser.add_argument("--layouts", default=str(DEFAULT_LAYOUTS))
    parser.add_argument("--segments", default=str(DEFAULT_SEGMENTS))
    parser.add_argument("--out", required=True)
    arguments = parser.parse_args()
    payload = run(
        Path(arguments.fixtures), Path(arguments.layouts), Path(arguments.segments)
    )
    destination = Path(arguments.out)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=1)
        handle.write("\n")
    print(
        "donors=%d segmented=%d tiled=%d identical=%d"
        % (
            payload["donor_count"],
            payload["segmented_count"],
            payload["tiled_count"],
            payload["identical_count"],
        )
    )
    for name, tally in payload["blocking_runs"].items():
        print("  blocked by %-38s %d" % (name, tally))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
