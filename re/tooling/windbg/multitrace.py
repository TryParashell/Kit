# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
SCRATCH = HERE.parents[2] / ".rescratch"
GRAMMAR = HERE.parent / "harness"
for candidate in (HERE, GRAMMAR):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

import cdbdrive  # noqa: E402
import model as modellib  # noqa: E402
import segment as segmentlib  # noqa: E402
import tracelog  # noqa: E402

import streamlib  # noqa: E402

OUT = SCRATCH / "trace" / "out"

RESOLVED = streamlib.RESOLVED
CMGR = "Contents/CMgr"
MODEL_HEADER = "Contents/Config-0-ModelHeader"
HEADER2 = "Header2"
CONFIG0 = "Contents/Config-0"
VISUAL_STATES = "ThirdPtyStore/VisualStates"

STREAMS = (RESOLVED, CMGR, MODEL_HEADER, CONFIG0, VISUAL_STATES)

PREAMBLE = """$$ SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
$$ SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
$$
$$ This SPDX license identifier and copyright notice must not be
$$ removed, altered, or obscured. Doing so is a material breach of
$$ the PolyForm Strict License 1.0.0 and voids all licenses granted
$$ to you under it immediately and permanently.
.symopt+0x4000
.symopt-0x20000
.exepath+ {solidworks}
.reload /f swccu.dll
"""

BREAKPOINT = (
    'bp swccu!su_CArchive::{routine} ".if ({guard}) {{ .printf '
    '\\"{tag} %p %x %d %p %x\\\\n\\", poi(@rcx+{start:#x}), '
    "poi(@rcx+{cur:#x})-poi(@rcx+{start:#x}), dwo(@rcx+{map:#x}), @rsp, "
    'poi(@rcx+{max:#x})-poi(@rcx+{start:#x}) }}; gc"\n'
)


def layout() -> dict[str, int]:
    path = OUT / "Calibrate.json"
    if not path.is_file():
        raise SystemExit(f"run Calibrate.py first: {path} is missing")
    return json.loads(path.read_text(encoding="utf-8"))["layout"]


def guard(spans: tuple[int, ...], fields: dict[str, int]) -> str:
    span = f"(poi(@rcx+{fields['max']:#x})-poi(@rcx+{fields['start']:#x}))"
    return " | ".join(f"({span}=={value:#x})" for value in sorted(set(spans)))


def write_script(path: Path, spans: tuple[int, ...], fields: dict[str, int]) -> None:
    text = PREAMBLE.format(solidworks=cdbdrive.SOLIDWORKS_DIR)
    condition = guard(spans, fields)
    for routine, tag in (("ReadObject", "RO"), ("ReadClass", "RC")):
        text += BREAKPOINT.format(
            routine=routine,
            tag=tag,
            guard=condition,
            start=fields["start"],
            cur=fields["cur"],
            max=fields["max"],
            map=fields["map"],
        )
    text += "bl\ng\n"
    path.write_text(text, encoding="ascii")


def analyse(part: Path, log: Path, streams: tuple[str, ...]) -> list[dict[str, object]]:
    donor = streamlib.load_donor(part)
    events = tracelog.read_events(log)
    rows: list[dict[str, object]] = []
    for name in streams:
        blob = donor.streams.get(name)
        if blob is None:
            rows.append({"stream": name, "status": "absent"})
            continue
        counts = tracelog.buffers_for_span(events, len(blob))
        if not counts:
            rows.append(
                {"stream": name, "status": "no-events", "stream_length": len(blob)}
            )
            continue
        segments = segmentlib.build(blob, events, span=len(blob))
        shape = segmentlib.tiling(blob, segments)
        mismatch = segmentlib.counter_mismatches(segments)
        row: dict[str, object] = {
            "stream": name,
            "status": "traced",
            "stream_length": len(blob),
            "buffers": len(counts),
            "objects": len(segments),
            "definitions": sum(1 for item in segments if item.kind == "definition"),
            "base_map_index": segments[0].map_index,
            "tiles": shape["tiles"],
            "header_bytes": shape["header_bytes"],
            "trailing_bytes": shape["trailing_bytes"],
            "gaps": shape["gaps"],
            "overlaps": shape["overlaps"],
            "counter_mismatches": len(mismatch),
            "increment_rule": segmentlib.increment_rule(segments),
        }
        try:
            reparsed = modellib.parse(blob, segments)
            row["reemit_identical"] = reparsed.emit() == blob
            row["external_classrefs"] = sum(
                1
                for node in reparsed.nodes
                if node.kind == "classref" and node.target < 0
            )
            row["external_objectrefs"] = sum(
                1
                for node in reparsed.nodes
                if node.kind == "objectref" and node.target < 0
            )
        except modellib.ModelError as error:
            row["reemit_identical"] = False
            row["model_error"] = str(error)
        rows.append(row)
    return rows


def trace_one(
    label: str, part: Path, fields: dict[str, int], mode: str, streams: tuple[str, ...]
) -> dict[str, object]:
    donor = streamlib.load_donor(part)
    spans = tuple(len(donor.streams[name]) for name in streams if name in donor.streams)
    script = HERE / f"cdb_multi_{label}.txt"
    log = OUT / f"cdb_multi_{label}.log"
    write_script(script, spans, fields)
    record: dict[str, object] = {
        "label": label,
        "part": str(part),
        "spans": list(spans),
        "script": str(script),
        "log": str(log),
    }
    if mode == "run":
        result = cdbdrive.run(
            script,
            log,
            part,
            marker=r"^RO ",
            hard_deadline=900.0,
            quiet_seconds=60.0,
        )
        record["cdb_reason"] = result.reason
        record["cdb_seconds"] = round(result.seconds, 1)
        record["read_object_events"] = result.markers
    if not log.is_file():
        record["status"] = "no-log"
        return record
    record["status"] = "traced"
    record["streams"] = analyse(part, log, streams)
    return record


def main() -> int:
    arguments = sys.argv[1:]
    if len(arguments) < 3:
        raise SystemExit("usage: Multitrace.py <mode> <label> <part> [<label> <part>]")
    mode = arguments[0]
    pairs = arguments[1:]
    if len(pairs) % 2:
        raise SystemExit("labels and parts must come in pairs")
    fields = layout()
    OUT.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, object]] = []
    for position in range(0, len(pairs), 2):
        label = pairs[position]
        part = Path(pairs[position + 1]).resolve()
        record = trace_one(label, part, fields, mode, STREAMS)
        records.append(record)
        print(f"== {label} {record.get('status')} {record.get('cdb_reason')}")
        for row in record.get("streams") or []:
            print(
                f"   {str(row['stream']):38s} {str(row['status']):10s} "
                f"len={row.get('stream_length')} objects={row.get('objects')} "
                f"tiles={row.get('tiles')} mism={row.get('counter_mismatches')} "
                f"reemit={row.get('reemit_identical')}",
                flush=True,
            )
        (OUT / "Multitrace.json").write_text(
            json.dumps(records, indent=2), encoding="utf-8"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
