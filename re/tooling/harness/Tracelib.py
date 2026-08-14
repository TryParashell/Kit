from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import struct

import carchive

EVENT = re.compile(r"^(RO|RC) ([0-9a-fA-F]+) ([0-9a-fA-F]+) (\d+)\s*$")

NEW_CLASS_TAG = 0xFFFF
CLASS_TAG_BIT = 0x8000
NULL_TAG = 0x0000
BIG_OBJECT_TAG = 0x7FFF


@dataclass(frozen=True, slots=True)
class Event:
    kind: str
    buffer: int
    offset: int
    counter: int


@dataclass(frozen=True, slots=True)
class Segment:
    index: int
    offset: int
    end: int
    tag: int
    tag_kind: str
    class_index: int
    class_name: str
    counter: int
    header: int

    @property
    def length(self) -> int:
        return self.end - self.offset

    @property
    def body_offset(self) -> int:
        return self.offset + self.header

    @property
    def body_length(self) -> int:
        return self.end - self.offset - self.header


def read_events(path: Path) -> tuple[Event, ...]:
    result: list[Event] = []
    for raw in path.read_text(errors="replace").splitlines():
        match = EVENT.match(raw.strip())
        if not match:
            continue
        result.append(
            Event(
                kind=match.group(1),
                buffer=int(match.group(2), 16),
                offset=int(match.group(3), 16),
                counter=int(match.group(4)),
            )
        )
    return tuple(result)


def object_events(events: tuple[Event, ...]) -> tuple[Event, ...]:
    return tuple(event for event in events if event.kind == "RO")


def dominant_buffer(events: tuple[Event, ...]) -> int:
    counts: dict[int, int] = {}
    for event in events:
        counts[event.buffer] = counts.get(event.buffer, 0) + 1
    return max(counts, key=lambda key: counts[key])


def tag_at(blob: bytes, offset: int) -> tuple[int, str, int]:
    token = struct.unpack_from("<H", blob, offset)[0]
    if token == NEW_CLASS_TAG:
        length = struct.unpack_from("<H", blob, offset + 4)[0]
        return token, "definition", 6 + length
    if token == NULL_TAG:
        return token, "null", 2
    if token == BIG_OBJECT_TAG:
        return token, "big", 6
    if token & CLASS_TAG_BIT:
        return token, "classref", 2
    return token, "objectref", 2


def segment(
    blob: bytes, events: tuple[Event, ...], *, buffer: int | None = None
) -> tuple[Segment, ...]:
    objects = object_events(events)
    if not objects:
        return ()
    target = dominant_buffer(objects) if buffer is None else buffer
    offsets = sorted({event.offset for event in objects if event.buffer == target})
    counters = {}
    for event in objects:
        if event.buffer == target:
            counters.setdefault(event.offset, event.counter)
    result: list[Segment] = []
    names: dict[int, str] = {}
    counter = 0
    for position, offset in enumerate(offsets):
        end = offsets[position + 1] if position + 1 < len(offsets) else len(blob)
        token, kind, header = tag_at(blob, offset)
        if kind == "definition":
            length = struct.unpack_from("<H", blob, offset + 4)[0]
            name = blob[offset + 6 : offset + 6 + length].decode("ascii", "replace")
            counter += 1
            names[counter] = name
            class_index = counter
            counter += 1
        elif kind == "classref":
            class_index = token & ~CLASS_TAG_BIT
            name = names.get(class_index, f"#{class_index}")
            counter += 1
        else:
            class_index = 0
            name = kind
        result.append(
            Segment(
                index=position,
                offset=offset,
                end=end,
                tag=token,
                tag_kind=kind,
                class_index=class_index,
                class_name=name,
                counter=counters[offset],
                header=header,
            )
        )
    return tuple(result)


def definition_names(blob: bytes) -> dict[int, str]:
    return {
        definition.tag_offset: definition.name
        for definition in carchive.class_definitions(blob)
    }
