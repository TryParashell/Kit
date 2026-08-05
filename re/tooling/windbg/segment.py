from __future__ import annotations

from dataclasses import dataclass, asdict
import json
from pathlib import Path
import struct
import sys

HERE = Path(__file__).resolve().parent
SCRATCH = HERE.parents[2] / ".rescratch"
GRAMMAR = HERE.parent / "harness"
for candidate in (HERE, GRAMMAR):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

import tracelog

import streamlib

OUT = SCRATCH / "trace" / "out"

NEW_CLASS_TAG = 0xFFFF
CLASS_TAG_BIT = 0x8000
BIG_OBJECT_TAG = 0x7FFF
NULL_TAG = 0x0000


class SegmentError(RuntimeError):
    __slots__ = ()


@dataclass(frozen=True, slots=True)
class Segment:
    index: int
    offset: int
    end: int
    length: int
    scope_end: int
    depth: int
    parent: int
    rsp: int
    tag: int
    kind: str
    header: int
    class_index: int
    class_name: str
    map_index: int
    modelled_index: int
    object_index: int


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


def _ordered(
    events: tuple[tracelog.Event, ...], buffer: int, span: int | None = None
) -> list[tracelog.Event]:
    seen: set[int] = set()
    result: list[tracelog.Event] = []
    for event in events:
        if event.kind != "RO" or event.buffer != buffer or event.offset in seen:
            continue
        if span is not None and event.span != span:
            continue
        seen.add(event.offset)
        result.append(event)
    result.sort(key=lambda event: event.offset)
    return result


def _nesting(events: list[tracelog.Event]) -> tuple[list[int], list[int], list[int]]:
    stack: list[tuple[int, int]] = []
    depths: list[int] = []
    parents: list[int] = []
    for position, event in enumerate(events):
        while stack and stack[-1][0] <= event.rsp:
            stack.pop()
        parents.append(stack[-1][1] if stack else -1)
        depths.append(len(stack))
        stack.append((event.rsp, position))
    scope: list[int] = []
    for position, event in enumerate(events):
        end = -1
        for later in range(position + 1, len(events)):
            if events[later].rsp >= event.rsp:
                end = events[later].offset
                break
        scope.append(end)
    return depths, parents, scope


def build(
    blob: bytes,
    events: tuple[tracelog.Event, ...],
    *,
    buffer: int | None = None,
    span: int | None = None,
) -> tuple[Segment, ...]:
    objects = tuple(event for event in events if event.kind == "RO")
    if not objects:
        raise SegmentError("trace contains no ReadObject events")
    if buffer is not None:
        target = buffer
    elif span is not None:
        target = tracelog.busiest_buffer(events, span)
    else:
        target = tracelog.dominant_buffer(objects)
    ordered = _ordered(events, target, span)
    depths, parents, scope = _nesting(ordered)
    names: dict[int, str] = {}
    counter = ordered[0].counter
    result: list[Segment] = []
    for position, event in enumerate(ordered):
        offset = event.offset
        end = ordered[position + 1].offset if position + 1 < len(ordered) else len(blob)
        token, kind, header = tag_at(blob, offset)
        modelled = counter
        if kind == "definition":
            length = struct.unpack_from("<H", blob, offset + 4)[0]
            name = blob[offset + 6 : offset + 6 + length].decode("ascii", "replace")
            class_index = counter
            names[class_index] = name
            object_index = counter + 1
            counter += 2
        elif kind == "classref":
            class_index = token & ~CLASS_TAG_BIT
            name = names.get(class_index, f"external#{class_index}")
            object_index = counter
            counter += 1
        elif kind == "objectref":
            class_index = 0
            name = f"backref->{token}"
            object_index = token
        else:
            class_index = 0
            name = kind
            object_index = 0
        result.append(
            Segment(
                index=position,
                offset=offset,
                end=end,
                length=end - offset,
                scope_end=scope[position] if scope[position] >= 0 else len(blob),
                depth=depths[position],
                parent=parents[position],
                rsp=event.rsp,
                tag=token,
                kind=kind,
                header=header,
                class_index=class_index,
                class_name=name,
                map_index=event.counter,
                modelled_index=modelled,
                object_index=object_index,
            )
        )
    return tuple(result)


def tiling(blob: bytes, segments: tuple[Segment, ...]) -> dict[str, object]:
    gaps: list[tuple[int, int]] = []
    overlaps: list[tuple[int, int]] = []
    cursor = segments[0].offset
    for item in segments:
        if item.offset > cursor:
            gaps.append((cursor, item.offset))
        if item.offset < cursor:
            overlaps.append((item.offset, cursor))
        cursor = item.end
    trailing = len(blob) - cursor
    return {
        "header_bytes": segments[0].offset,
        "gaps": gaps,
        "overlaps": overlaps,
        "trailing_bytes": trailing,
        "covered": cursor - segments[0].offset,
        "tiles": not gaps and not overlaps and trailing == 0,
    }


def counter_mismatches(segments: tuple[Segment, ...]) -> tuple[Segment, ...]:
    return tuple(item for item in segments if item.map_index != item.modelled_index)


def class_table(segments: tuple[Segment, ...]) -> dict[str, int]:
    return {
        item.class_name: item.class_index
        for item in segments
        if item.kind == "definition"
    }


def increment_rule(segments: tuple[Segment, ...]) -> dict[str, list[int]]:
    table: dict[str, set[int]] = {}
    for left, right in zip(segments, segments[1:]):
        table.setdefault(left.kind, set()).add(right.map_index - left.map_index)
    return {kind: sorted(values) for kind, values in sorted(table.items())}


def load(
    part: Path, log: Path, *, stream: str = streamlib.RESOLVED
) -> tuple[bytes, tuple[Segment, ...]]:
    blob = streamlib.load_donor(part).streams[stream]
    events = tracelog.read_events(log)
    spans = {event.span for event in events if event.kind == "RO"}
    span = len(blob) if spans - {0} else None
    return blob, build(blob, events, span=span)


def report(
    label: str, part: Path, log: Path, *, stream: str = streamlib.RESOLVED
) -> dict[str, object]:
    blob, segments = load(part, log, stream=stream)
    shape = tiling(blob, segments)
    mismatch = counter_mismatches(segments)
    definitions = tuple(item for item in segments if item.kind == "definition")
    payload = {
        "label": label,
        "part": str(part),
        "log": str(log),
        "stream": stream,
        "stream_length": len(blob),
        "base_map_index": segments[0].map_index,
        "object_count": len(segments),
        "definition_count": len(definitions),
        "counter_mismatches": len(mismatch),
        "tiling": shape,
        "increment_rule": increment_rule(segments),
        "class_index": class_table(segments),
        "segments": [asdict(item) for item in segments],
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"segments_{label}.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )
    print(
        f"{label:14s} stream={len(blob):6d} objects={len(segments):4d} "
        f"defs={len(definitions):3d} base={segments[0].map_index} "
        f"tiles={shape['tiles']} mismatches={len(mismatch)}"
    )
    return payload


def main() -> int:
    arguments = sys.argv[1:]
    if len(arguments) % 3:
        raise SystemExit("usage: segment.py <label> <part> <log> [...]")
    for position in range(0, len(arguments), 3):
        label = arguments[position]
        part = Path(arguments[position + 1]).resolve()
        log = Path(arguments[position + 2]).resolve()
        report(label, part, log)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
