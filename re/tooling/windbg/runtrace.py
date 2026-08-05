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

import cdbdrive
import segment as segmentlib
import tracelog

import carchive
import streamlib

OUT = SCRATCH / "trace" / "out"

SCRIPT = """.symopt+0x4000
.symopt-0x20000
.exepath+ {solidworks}
.reload /f swccu.dll
bp swccu!su_CArchive::ReadObject ".if ((poi(@rcx+{max:#x})-poi(@rcx+{start:#x}))=={span:#x}) {{ .printf \\"RO %p %x %d %p\\\\n\\", poi(@rcx+{start:#x}), poi(@rcx+{cur:#x})-poi(@rcx+{start:#x}), dwo(@rcx+{map:#x}), @rsp }}; gc"
bp swccu!su_CArchive::ReadClass ".if ((poi(@rcx+{max:#x})-poi(@rcx+{start:#x}))=={span:#x}) {{ .printf \\"RC %p %x %d %p\\\\n\\", poi(@rcx+{start:#x}), poi(@rcx+{cur:#x})-poi(@rcx+{start:#x}), dwo(@rcx+{map:#x}), @rsp }}; gc"
bl
g
"""


def layout() -> dict[str, int]:
    path = OUT / "calibrate.json"
    if not path.is_file():
        raise SystemExit(f"run calibrate.py first: {path} is missing")
    return json.loads(path.read_text(encoding="utf-8"))["layout"]


def write_script(path: Path, span: int, fields: dict[str, int]) -> None:
    path.write_text(
        SCRIPT.format(
            solidworks=cdbdrive.SOLIDWORKS_DIR,
            span=span,
            cur=fields["cur"],
            max=fields["max"],
            start=fields["start"],
            map=fields["map"],
        ),
        encoding="ascii",
    )


def cross_check(
    blob: bytes, segments: tuple[segmentlib.Segment, ...]
) -> dict[str, object]:
    definitions = carchive.class_definitions(blob)
    static = [item.tag_offset for item in definitions]
    traced = {item.offset for item in segments if item.kind == "definition"}
    missing = [offset for offset in static if offset not in traced]
    extra = sorted(traced - set(static))
    return {
        "static_definitions": len(static),
        "traced_definitions": len(traced),
        "static_offsets_head": static[:8],
        "missing_from_trace": missing,
        "traced_not_scanned": extra,
        "agree": not missing and not extra,
    }


def trace_one(
    label: str, part: Path, fields: dict[str, int], mode: str
) -> dict[str, object]:
    blob = streamlib.load_donor(part).resolved
    span = len(blob)
    script = HERE / f"cdb_trace_{label}.txt"
    log = OUT / f"cdb_trace_{label}.log"
    write_script(script, span, fields)
    record: dict[str, object] = {
        "label": label,
        "part": str(part),
        "stream_length": span,
        "script": str(script),
        "log": str(log),
    }
    if mode == "run":
        result = cdbdrive.run(
            script,
            log,
            part,
            marker=r"^RO ",
            hard_deadline=600.0,
            quiet_seconds=45.0,
        )
        record["cdb_reason"] = result.reason
        record["cdb_seconds"] = round(result.seconds, 1)
        record["read_object_events"] = result.markers
    if not log.is_file():
        record["status"] = "no-log"
        return record
    events = tracelog.read_events(log)
    if not any(event.kind == "RO" for event in events):
        record["status"] = "no-events"
        return record
    segments = segmentlib.build(blob, events)
    shape = segmentlib.tiling(blob, segments)
    mismatch = segmentlib.counter_mismatches(segments)
    record.update(
        {
            "status": "traced",
            "objects": len(segments),
            "definitions": sum(1 for item in segments if item.kind == "definition"),
            "base_map_index": segments[0].map_index,
            "tiles": shape["tiles"],
            "header_bytes": shape["header_bytes"],
            "trailing_bytes": shape["trailing_bytes"],
            "counter_mismatches": len(mismatch),
            "increment_rule": segmentlib.increment_rule(segments),
            "cross_check": cross_check(blob, segments),
        }
    )
    segmentlib.report(label, part, log)
    return record


def main() -> int:
    arguments = sys.argv[1:]
    if not arguments:
        raise SystemExit(
            "usage: runtrace.py <mode> <label> <part> [<label> <part> ...]"
        )
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
        record = trace_one(label, part, fields, mode)
        records.append(record)
        print(
            f"{label:22s} {record.get('status')} objects={record.get('objects')} "
            f"tiles={record.get('tiles')} mismatches={record.get('counter_mismatches')} "
            f"agree={(record.get('cross_check') or {}).get('agree')}",
            flush=True,
        )
        (OUT / "runtrace.json").write_text(
            json.dumps(records, indent=2), encoding="utf-8"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
