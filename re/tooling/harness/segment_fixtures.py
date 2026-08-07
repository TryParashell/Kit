from __future__ import annotations

import argparse
import collections
import json
from pathlib import Path
import struct
import sys
from typing import Dict, List, Mapping, Tuple

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
for candidate in (str(ROOT / "src"),):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from convert.adapters.solidworks.archive import (
    BaseResolution,
    LayoutTable,
    MO_VERSION_PREFIX,
    STREAM_HEADER_SIZE,
    container_mo_version,
    resolve_base,
    verify,
)
from convert.adapters.solidworks.container import SldprtArchive

DEFAULT_FIXTURES = ROOT / "tests" / "fixtures" / "solidworks" / "donors"
DEFAULT_LAYOUTS = ROOT / "re" / "data" / "class_layouts.json"
DEFAULT_SEGMENTS = ROOT / "re" / "data" / "segments"
FIRST_FEATURE_BASE = 109
VENDOR_LABEL_PREFIX = "vendor_"


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


def donor_stream_names(donor: Path) -> List[str]:
    names: List[str] = []
    meta = donor / "meta.json"
    if meta.is_file():
        payload = json.loads(meta.read_text(encoding="utf-8"))
        listed = payload.get("container_streams")
        if isinstance(listed, list):
            for item in listed:
                if isinstance(item, dict) and isinstance(item.get("name"), str):
                    names.append(str(item["name"]))
    return names


def donor_mo_version(donor: Path) -> Tuple[int | None, str]:
    meta = donor / "meta.json"
    if meta.is_file():
        payload = json.loads(meta.read_text(encoding="utf-8"))
        recorded = payload.get("mo_version")
        if isinstance(recorded, int) and not isinstance(recorded, bool):
            return int(recorded), "mo_version field in the fixture meta.json"
    names = donor_stream_names(donor)
    found = container_mo_version(names)
    if found is not None:
        return found, (
            f"{MO_VERSION_PREFIX}{found} among the {len(names)} container stream "
            "names in the fixture meta.json"
        )
    return None, (
        f"neither an mo_version field nor a {MO_VERSION_PREFIX}* storage among the "
        f"{len(names)} container stream names in the fixture meta.json"
    )


def traced_mo_versions(segments_dir: Path) -> Dict[str, int]:
    table: Dict[str, int] = {}
    for path in sorted(segments_dir.glob("segments_*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        part = Path(str(payload["part"]))
        if not part.is_file():
            continue
        archive = SldprtArchive.from_bytes(part.read_bytes())
        found = container_mo_version(archive.streams)
        if found is not None:
            table[str(payload["label"])] = found
    return table


def authored_mo_version(traced: Mapping[str, int]) -> Tuple[int | None, str]:
    authored = {
        label: version
        for label, version in traced.items()
        if not label.startswith(VENDOR_LABEL_PREFIX)
    }
    if not authored:
        return None, (
            "no authored traced part is present in this checkout, so no document "
            "version can be read for the donor corpus"
        )
    found = sorted(set(authored.values()))
    if len(found) != 1:
        return None, (
            f"the {len(authored)} authored traced parts disagree on the document "
            f"version {found}"
        )
    return found[0], (
        f"{MO_VERSION_PREFIX}{found[0]} read from the {len(authored)} authored traced "
        "parts, which the same writer produced as the donor corpus"
    )


def recorded_bases(segments_dir: Path) -> Dict[str, int]:
    table: Dict[str, int] = {}
    for path in sorted(segments_dir.glob("segments_*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        table[str(payload["label"])] = int(payload["base_map_index"])
    return table


def seed_base(donor: Path) -> Tuple[int, str]:
    features = fixture_feature_count(donor)
    if features > 0:
        return (
            FIRST_FEATURE_BASE + features - 1,
            f"{FIRST_FEATURE_BASE} + {features} - 1 from the features array of the "
            "fixture meta.json",
        )
    return (
        FIRST_FEATURE_BASE,
        f"{FIRST_FEATURE_BASE}, the base of the smallest traced document, because "
        "the fixture meta.json names no features array",
    )


def resolved_base(
    blob: bytes, layouts: LayoutTable, seed: int, mo_version: int | None
) -> BaseResolution:
    return resolve_base(
        blob,
        seed,
        layouts,
        header_size=STREAM_HEADER_SIZE,
        mo_version=mo_version,
    )


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
    versions: collections.Counter = collections.Counter()
    traced = traced_mo_versions(segments_dir)
    corpus_version, corpus_rule = authored_mo_version(traced)
    for donor in donors:
        blob = (donor / "resolved.bin").read_bytes()
        seed, rule = seed_base(donor)
        mo_version, version_rule = donor_mo_version(donor)
        if mo_version is None:
            mo_version, version_rule = corpus_version, corpus_rule
        versions[mo_version if mo_version is not None else -1] += 1
        resolution = resolved_base(blob, layouts, seed, mo_version)
        base = resolution.base
        method = "seed" if base == seed else "refined"
        report = verify(
            blob,
            base,
            layouts,
            header_size=STREAM_HEADER_SIZE,
            mo_version=mo_version,
        )
        meta_features = fixture_feature_count(donor)
        scanned = scanned_class_names(blob)
        outstanding = sorted(name for name in scanned if name in partial)
        unknown = sorted(name for name in scanned if name not in layouts.classes)
        for name in outstanding:
            required[name] += 1
        row = {
            "donor": donor.name,
            "base_rule": rule,
            "base_method": method,
            "mo_version": mo_version if mo_version is not None else -1,
            "mo_version_rule": version_rule,
        }
        row.update(report.as_dict())
        row["base"] = base
        row["base_resolution"] = resolution.as_dict()
        row["meta_feature_count"] = meta_features
        row["meta_base"] = seed
        row["base_agrees_with_meta"] = seed == base
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
        "mo_versions": dict(sorted(versions.items())),
        "mo_version_derivation": (
            "a run length recorded under runs_by_version is selected by the document "
            "generation, which is the _MO_VERSION_<n> storage name in the containing "
            "SLDPRT; a donor fixture records only its Contents and Header2 streams, so "
            "none carries that storage and no meta.json holds an mo_version field, and "
            "the generation is therefore taken from the authored traced parts, whose "
            "writer also produced the donor corpus; -1 marks a donor whose generation "
            "could not be established, and such a donor is segmented with no version "
            "so a version gated run is refused rather than guessed"
        ),
        "mo_version_of_traced_parts": dict(sorted(traced.items())),
        "class_count": len(layouts.classes),
        "confirmed_classes": sum(
            1 for entry in layouts.classes.values() if entry.confidence == "confirmed"
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
        "bases_taken_from_the_metadata_seed": sum(
            1 for row in rows if row["base_agrees_with_meta"]
        ),
        "bases_refined_away_from_the_metadata_seed": [
            {
                "donor": row["donor"],
                "resolved": row["base"],
                "seed": row["meta_base"],
                "objects_reached": row["base_resolution"]["progress"],
                "tried": row["base_resolution"]["tried"],
            }
            for row in rows
            if not row["base_agrees_with_meta"]
        ],
        "base_derivation": (
            "the base is seeded at 109 + feature_count - 1 from the features array of "
            "the fixture meta.json and then refined against the stream: when the walk "
            "stops on a class or object reference at or above the trial base that no "
            "definition has produced, the reference index minus the counter offset of "
            "every definition already reached names the bases that would resolve it, "
            "and each is walked in turn until one segments or the candidates run out; "
            "the base that reaches the most objects wins and the method column records "
            "whether that was the seed or a refinement; the seed is only a seed, "
            "because 109 + feature_count - 1 is refuted by the fixtures whose "
            "Contents/Config-0 node population differs from the traced boss family: a "
            "revolve feature adds one counter unit (boss_disjoint_revolve, boss_revcut "
            "and arcboss_cut_cut_cut_through_rev resolve one above the seed), a "
            "mid-plane end condition removes one (boss_midplane resolves one below), "
            "and the extra document metadata of arcboss_cut_cut_cut_through_rev_meta "
            "moves it to 337, far outside any fixed window"
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
