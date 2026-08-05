from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import re
import struct
import sys

HERE = Path(__file__).resolve().parent
GRAMMAR = HERE.parent / "grammar"
for candidate in (HERE, GRAMMAR):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

import streamlib

EVENT = re.compile(r"^(RO|RC) ([0-9a-fA-F]+) ([0-9a-fA-F]+) (\d+)\s*$")

NEW_CLASS_TAG = 0xFFFF
CLASS_TAG_BIT = 0x8000
BIG_OBJECT_TAG = 0x7FFF
NULL_TAG = 0x0000


@dataclass(frozen=True, slots=True)
class Event:
    kind: str
    buffer: int
    offset: int
    counter: int


@dataclass(frozen=True, slots=True)
class Tag:
    offset: int
    token: int
    kind: str
    header: int
    schema: int
    name: str
    index: int


def read_events(path: Path) -> tuple[Event, ...]:
    out: list[Event] = []
    for raw in path.read_text(errors="replace").splitlines():
        match = EVENT.match(raw.strip())
        if match is None:
            continue
        out.append(
            Event(
                kind=match.group(1),
                buffer=int(match.group(2), 16),
                offset=int(match.group(3), 16),
                counter=int(match.group(4)),
            )
        )
    return tuple(out)


def decode_tag(blob: bytes, offset: int) -> Tag:
    token = struct.unpack_from("<H", blob, offset)[0]
    if token == NEW_CLASS_TAG:
        schema, length = struct.unpack_from("<HH", blob, offset + 2)
        name = blob[offset + 6 : offset + 6 + length].decode("ascii", "replace")
        return Tag(offset, token, "definition", 6 + length, schema, name, -1)
    if token == NULL_TAG:
        return Tag(offset, token, "null", 2, 0, "", -1)
    if token == BIG_OBJECT_TAG:
        index = struct.unpack_from("<I", blob, offset + 2)[0]
        return Tag(offset, token, "big", 6, 0, "", index)
    if token & CLASS_TAG_BIT:
        return Tag(offset, token, "classref", 2, 0, "", token & ~CLASS_TAG_BIT)
    return Tag(offset, token, "objectref", 2, 0, "", token)


def objects(events: tuple[Event, ...]) -> tuple[Event, ...]:
    return tuple(event for event in events if event.kind == "RO")


def dominant_buffer(events: tuple[Event, ...]) -> int:
    counts: dict[int, int] = {}
    for event in events:
        counts[event.buffer] = counts.get(event.buffer, 0) + 1
    return max(counts, key=lambda key: counts[key])


def delta_for(kind: str) -> int:
    if kind == "definition":
        return 2
    if kind in {"classref", "big"}:
        return 1
    return 0


def analyse(blob: bytes, log: Path) -> dict[str, object]:
    events = objects(read_events(log))
    buffer = dominant_buffer(events)
    events = tuple(event for event in events if event.buffer == buffer)
    tags = [decode_tag(blob, event.offset) for event in events]
    mismatch: list[str] = []
    for position in range(len(events) - 1):
        expected = events[position].counter + delta_for(tags[position].kind)
        actual = events[position + 1].counter
        if expected != actual:
            mismatch.append(
                f"{events[position].offset:#x} {tags[position].kind} "
                f"counter {events[position].counter} -> {actual} expected {expected}"
            )
    monotonic = all(
        events[position].offset < events[position + 1].offset
        for position in range(len(events) - 1)
    )
    return {
        "log": log.name,
        "buffer": f"{buffer:#x}",
        "stream_length": len(blob),
        "events": len(events),
        "base_counter": events[0].counter if events else 0,
        "monotonic_offsets": monotonic,
        "counter_rule_mismatches": mismatch,
        "kinds": {
            kind: sum(1 for tag in tags if tag.kind == kind)
            for kind in ("definition", "classref", "objectref", "null", "big")
        },
        "items": [
            {
                "offset": event.offset,
                "counter": event.counter,
                "kind": tag.kind,
                "token": tag.token,
                "index": tag.index,
                "name": tag.name,
                "schema": tag.schema,
                "header": tag.header,
            }
            for event, tag in zip(events, tags)
        ],
    }


def main() -> None:
    part = Path(sys.argv[1]).resolve()
    log = Path(sys.argv[2]).resolve()
    destination = Path(sys.argv[3]).resolve()
    blob = streamlib.load_donor(part).resolved
    report = analyse(blob, log)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"stream={report['stream_length']} events={report['events']}")
    print(f"base_counter={report['base_counter']}")
    print(f"monotonic_offsets={report['monotonic_offsets']}")
    print(f"kinds={report['kinds']}")
    print(f"counter_rule_mismatches={len(report['counter_rule_mismatches'])}")
    for text in report["counter_rule_mismatches"][:20]:
        print(f"  {text}")


if __name__ == "__main__":
    main()
