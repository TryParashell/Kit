# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
import json
from pathlib import Path
import struct

from .container import SldprtFormatError

NULL_TAG = 0x0000
NEW_CLASS_TAG = 0xFFFF
BIG_OBJECT_TAG = 0x7FFF
CLASS_TAG_BIT = 0x8000
BIG_CLASS_TAG_BIT = 0x80000000
MAX_MAP_INDEX = 0x3FFFFFFE
STRING_MARKER = b"\xff\xfe\xff"
SHORT_STRING_LIMIT = 0xFF
LONG_STRING_LIMIT = 0xFFFE
STREAM_HEADER_SIZE = 6
DEFINITION_KIND = "definition"
CLASS_REFERENCE_KIND = "classref"
OBJECT_REFERENCE_KIND = "objectref"
NULL_KIND = "null"
LEAD_RUN = "lead"
LEAF_RUN = "leaf"
REPEATED_SLOT = "..."
POLYMORPHIC_SLOT = "*"
OPAQUE_RULE = "opaque"
STRING_RULE = "string"
COUNT_RULE = "count"
CONDITIONAL_RULE = "conditional"


class ArchiveError(SldprtFormatError):
    __slots__ = ()


class SegmentationError(ArchiveError):
    __slots__ = ()

    def __init__(
        self,
        class_name: str,
        slot: str,
        offset: int,
        reason: str,
        *,
        base: int = -1,
        progress: int = -1,
        depth: int = -1,
    ) -> None:
        self.class_name = class_name
        self.slot = slot
        self.offset = offset
        self.reason = reason
        self.base = base
        self.progress = progress
        self.depth = depth
        self.reached: tuple[StaticSegment, ...] = ()
        super().__init__(
            f"class {class_name!r} slot {slot!r} at byte offset {offset}: {reason}"
        )


@dataclass(frozen=True, slots=True)
class Tag:
    kind: str
    size: int
    token: int
    index: int
    schema: int
    class_name: str
    wide: bool


def read_tag(blob: bytes, offset: int) -> Tag:
    if offset < 0:
        raise ArchiveError(f"negative tag offset {offset}")
    if offset + 2 > len(blob):
        raise ArchiveError(
            f"tag at offset {offset} runs past the end of a {len(blob)} byte stream"
        )
    token = struct.unpack_from("<H", blob, offset)[0]
    if token == NEW_CLASS_TAG:
        if offset + 6 > len(blob):
            raise ArchiveError(
                f"class definition at offset {offset} has no schema and name length"
            )
        schema, units = struct.unpack_from("<HH", blob, offset + 2)
        if offset + 6 + units > len(blob):
            raise ArchiveError(
                f"class definition at offset {offset} names {units} bytes past the end"
            )
        raw = blob[offset + 6 : offset + 6 + units]
        try:
            name = raw.decode("ascii")
        except UnicodeDecodeError as error:
            raise ArchiveError(
                f"class definition at offset {offset} has a non ascii name"
            ) from error
        return Tag(
            kind=DEFINITION_KIND,
            size=6 + units,
            token=token,
            index=-1,
            schema=schema,
            class_name=name,
            wide=False,
        )
    if token == BIG_OBJECT_TAG:
        if offset + 6 > len(blob):
            raise ArchiveError(f"big object tag at offset {offset} has no 32 bit index")
        wide_token = struct.unpack_from("<I", blob, offset + 2)[0]
        index = wide_token & ~BIG_CLASS_TAG_BIT
        if index > MAX_MAP_INDEX:
            raise ArchiveError(
                f"big object tag at offset {offset} holds unrepresentable index {index}"
            )
        kind = (
            CLASS_REFERENCE_KIND
            if wide_token & BIG_CLASS_TAG_BIT
            else OBJECT_REFERENCE_KIND
        )
        return Tag(
            kind=kind,
            size=6,
            token=token,
            index=index,
            schema=0,
            class_name="",
            wide=True,
        )
    if token == NULL_TAG:
        return Tag(
            kind=NULL_KIND,
            size=2,
            token=token,
            index=0,
            schema=0,
            class_name="",
            wide=False,
        )
    if token & CLASS_TAG_BIT:
        return Tag(
            kind=CLASS_REFERENCE_KIND,
            size=2,
            token=token,
            index=token & ~CLASS_TAG_BIT,
            schema=0,
            class_name="",
            wide=False,
        )
    return Tag(
        kind=OBJECT_REFERENCE_KIND,
        size=2,
        token=token,
        index=token,
        schema=0,
        class_name="",
        wide=False,
    )


def encode_class_definition(name: str, schema: int) -> bytes:
    try:
        encoded = name.encode("ascii")
    except UnicodeEncodeError as error:
        raise ArchiveError(f"class name {name!r} is not ascii") from error
    if not encoded:
        raise ArchiveError("class name must not be empty")
    if len(encoded) > 0xFFFF:
        raise ArchiveError(f"class name {name!r} is longer than 65535 bytes")
    if not 0 <= schema <= 0xFFFF:
        raise ArchiveError(f"class schema {schema} does not fit in 16 bits")
    return struct.pack("<HHH", NEW_CLASS_TAG, schema, len(encoded)) + encoded


def encode_class_reference(index: int, *, wide: bool = False) -> bytes:
    if index < 0:
        raise ArchiveError(f"negative class index {index}")
    if index > MAX_MAP_INDEX:
        raise ArchiveError(f"class index {index} exceeds the archive map limit")
    if wide or index >= BIG_OBJECT_TAG:
        return struct.pack("<HI", BIG_OBJECT_TAG, index | BIG_CLASS_TAG_BIT)
    return struct.pack("<H", CLASS_TAG_BIT | index)


def encode_object_reference(index: int, *, wide: bool = False) -> bytes:
    if index < 0:
        raise ArchiveError(f"negative object index {index}")
    if index > MAX_MAP_INDEX:
        raise ArchiveError(f"object index {index} exceeds the archive map limit")
    if index == NULL_TAG and not wide:
        return struct.pack("<H", NULL_TAG)
    if wide or index >= BIG_OBJECT_TAG:
        return struct.pack("<HI", BIG_OBJECT_TAG, index)
    return struct.pack("<H", index)


def encode_null() -> bytes:
    return struct.pack("<H", NULL_TAG)


def read_string(blob: bytes, offset: int) -> tuple[str, int]:
    if offset + 4 > len(blob):
        raise ArchiveError(f"string at offset {offset} has no length prefix")
    if blob[offset : offset + 3] != STRING_MARKER:
        raise ArchiveError(
            f"string at offset {offset} does not carry the ff fe ff marker"
        )
    units = blob[offset + 3]
    head = 4
    if units == SHORT_STRING_LIMIT:
        if offset + 6 > len(blob):
            raise ArchiveError(f"string at offset {offset} has no 16 bit length")
        units = struct.unpack_from("<H", blob, offset + 4)[0]
        head = 6
        if units < SHORT_STRING_LIMIT:
            raise ArchiveError(
                f"string at offset {offset} uses the wide form for {units} units"
            )
    end = offset + head + 2 * units
    if end > len(blob):
        raise ArchiveError(
            f"string at offset {offset} claims {units} units past the end"
        )
    return blob[offset + head : end].decode("utf-16-le"), end - offset


def encode_string(text: str) -> bytes:
    encoded = text.encode("utf-16-le")
    units = len(encoded) // 2
    if units < SHORT_STRING_LIMIT:
        return STRING_MARKER + bytes((units,)) + encoded
    if units < LONG_STRING_LIMIT:
        return STRING_MARKER + b"\xff" + struct.pack("<H", units) + encoded
    raise ArchiveError(f"string of {units} code units is not representable")


@dataclass(slots=True)
class Node:
    kind: str
    body: bytes
    schema: int = 0
    class_name: str = ""
    target: int = -1
    literal: int = 0
    wide: bool = False
    origin: int = -1
    class_index: int = 0
    object_index: int = 0


@dataclass(slots=True)
class Model:
    header: bytes
    base: int
    nodes: list[Node] = field(default_factory=list)

    def clone(self) -> Model:
        return Model(
            header=self.header,
            base=self.base,
            nodes=[
                Node(
                    kind=node.kind,
                    body=node.body,
                    schema=node.schema,
                    class_name=node.class_name,
                    target=node.target,
                    literal=node.literal,
                    wide=node.wide,
                    origin=node.origin,
                )
                for node in self.nodes
            ],
        )

    def definition_index(self, name: str) -> int:
        for position, node in enumerate(self.nodes):
            if node.kind == DEFINITION_KIND and node.class_name == name:
                return position
        raise KeyError(name)

    def assign(self) -> None:
        counter = self.base
        for node in self.nodes:
            if node.kind == DEFINITION_KIND:
                node.class_index = counter
                node.object_index = counter + 1
                counter += 2
            elif node.kind == CLASS_REFERENCE_KIND:
                node.class_index = 0
                node.object_index = counter
                counter += 1
            else:
                node.class_index = 0
                node.object_index = 0

    def emit(self) -> bytes:
        self.assign()
        out = bytearray(self.header)
        for node in self.nodes:
            if node.kind == DEFINITION_KIND:
                out += encode_class_definition(node.class_name, node.schema)
            elif node.kind == CLASS_REFERENCE_KIND:
                index = (
                    node.literal
                    if node.target < 0
                    else self.nodes[node.target].class_index
                )
                out += encode_class_reference(index, wide=node.wide)
            elif node.kind == OBJECT_REFERENCE_KIND:
                index = (
                    node.literal
                    if node.target < 0
                    else self.nodes[node.target].object_index
                )
                out += encode_object_reference(index, wide=node.wide)
            elif node.kind == NULL_KIND:
                out += encode_null()
            else:
                raise ArchiveError(f"cannot emit node kind {node.kind!r}")
            out += node.body
        return bytes(out)


@dataclass(slots=True)
class StaticSegment:
    index: int
    offset: int
    header: int
    end: int
    kind: str
    token: int
    wide: bool
    schema: int
    class_name: str
    class_index: int
    object_index: int
    depth: int
    parent: int


@dataclass(frozen=True, slots=True)
class VariableRun:
    slot: str
    rule: str
    at: int
    tail: int
    stride: int
    count_width: int
    width: int
    predicate: str
    predicate_at: int
    predicate_width: int
    values: tuple[int, ...]
    note: str


@dataclass(frozen=True, slots=True)
class RepeatField:
    run: str
    at: int
    width: int


@dataclass(frozen=True, slots=True)
class ClassLayout:
    name: str
    child_slots: tuple[str, ...]
    runs: Mapping[str, int]
    variable_runs: Mapping[str, tuple[VariableRun, ...]]
    confidence: str
    source: str
    repeat_note: str = ""
    repeat_count: RepeatField | None = None
    repeat_unresolved: bool = False

    @property
    def repeats(self) -> bool:
        return self.repeat_unresolved

    @property
    def template_slot(self) -> int:
        return len(self.child_slots) - 2

    def run_key(self, slot: int) -> str:
        if self.repeat_count is not None and slot >= self.template_slot:
            return str(self.template_slot)
        return str(slot)

    def run_keys(self) -> tuple[str, ...]:
        if not self.child_slots:
            return (LEAF_RUN,)
        span = (
            self.template_slot + 1
            if self.repeat_count is not None
            else len(self.child_slots)
        )
        return (LEAD_RUN,) + tuple(str(slot) for slot in range(span))


@dataclass(frozen=True, slots=True)
class LayoutTable:
    version: int
    source: str
    classes: Mapping[str, ClassLayout]

    def __contains__(self, name: object) -> bool:
        return name in self.classes

    def __getitem__(self, name: str) -> ClassLayout:
        return self.classes[name]

    def get(self, name: str) -> ClassLayout | None:
        return self.classes.get(name)

    @classmethod
    def from_mapping(cls, payload: Mapping[str, object]) -> LayoutTable:
        raw_classes = payload.get("classes")
        if not isinstance(raw_classes, Mapping):
            raise ArchiveError("layout table has no classes mapping")
        classes: dict[str, ClassLayout] = {}
        for name, entry in raw_classes.items():
            if not isinstance(entry, Mapping):
                raise ArchiveError(f"layout entry for {name!r} is not a mapping")
            classes[name] = _class_layout(str(name), entry)
        version = payload.get("version", 1)
        source = payload.get("source", "")
        return cls(
            version=int(version) if isinstance(version, int) else 1,
            source=str(source),
            classes=classes,
        )

    @classmethod
    def load(cls, path: str | Path) -> LayoutTable:
        location = Path(path)
        try:
            payload = json.loads(location.read_text(encoding="utf-8"))
        except OSError as error:
            raise ArchiveError(f"cannot read layout table {location}") from error
        except json.JSONDecodeError as error:
            raise ArchiveError(f"layout table {location} is not valid json") from error
        if not isinstance(payload, Mapping):
            raise ArchiveError(f"layout table {location} is not a json object")
        return cls.from_mapping(payload)


def _class_layout(name: str, entry: Mapping[str, object]) -> ClassLayout:
    raw_slots = entry.get("child_slots", ())
    if isinstance(raw_slots, str) or not isinstance(raw_slots, Sequence):
        raise ArchiveError(f"layout entry for {name!r} has a malformed child_slots")
    slots = tuple(str(slot) for slot in raw_slots)
    raw_runs = entry.get("runs", {})
    if not isinstance(raw_runs, Mapping):
        raise ArchiveError(f"layout entry for {name!r} has a malformed runs mapping")
    runs: dict[str, int] = {}
    for key, value in raw_runs.items():
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise ArchiveError(f"run {name}@{key} is not a non negative integer")
        runs[str(key)] = int(value)
    raw_variable = entry.get("variable_runs", ())
    if isinstance(raw_variable, str) or not isinstance(raw_variable, Sequence):
        raise ArchiveError(f"layout entry for {name!r} has a malformed variable_runs")
    variable: dict[str, list[VariableRun]] = {}
    for item in raw_variable:
        if not isinstance(item, Mapping):
            raise ArchiveError(f"variable run of {name!r} is not a mapping")
        slot = str(item.get("slot", ""))
        raw_values = item.get("values", ())
        if isinstance(raw_values, str) or not isinstance(raw_values, Sequence):
            raise ArchiveError(f"variable run {name}@{slot} has malformed values")
        variable.setdefault(slot, []).append(
            VariableRun(
                slot=slot,
                rule=str(item.get("rule", OPAQUE_RULE)),
                at=int(item.get("at", 0) or 0),
                tail=int(item.get("tail", 0) or 0),
                stride=int(item.get("stride", 0) or 0),
                count_width=int(item.get("count_width", 0) or 0),
                width=int(item.get("width", 0) or 0),
                predicate=str(item.get("predicate", "")),
                predicate_at=int(item.get("predicate_at", 0) or 0),
                predicate_width=int(item.get("predicate_width", 0) or 0),
                values=tuple(int(value) for value in raw_values),
                note=str(item.get("note", "")),
            )
        )
    raw_repeat = entry.get("repeat_count")
    repeat: RepeatField | None = None
    if isinstance(raw_repeat, Mapping) and REPEATED_SLOT in slots:
        run = str(raw_repeat.get("run", ""))
        at = int(raw_repeat.get("at", -1))
        width = int(raw_repeat.get("width", 0))
        if not run or at < 0 or width not in (1, 2, 4):
            raise ArchiveError(f"repeat_count of {name!r} is malformed")
        if len(slots) < 2:
            raise ArchiveError(f"repeat_count of {name!r} has no template slot")
        repeat = RepeatField(run=run, at=at, width=width)
    unresolved = (REPEATED_SLOT in slots or raw_repeat is not None) and repeat is None
    return ClassLayout(
        name=name,
        child_slots=slots,
        runs=runs,
        variable_runs={key: tuple(value) for key, value in variable.items()},
        confidence=str(entry.get("confidence", "partial")),
        source=str(entry.get("source", "")),
        repeat_note=str(entry.get("repeat_note", "")),
        repeat_count=repeat,
        repeat_unresolved=unresolved,
    )


@dataclass(slots=True)
class _Frame:
    node: int
    class_name: str
    layout: ClassLayout
    slot: int
    total: int


def _scalar(blob: bytes, offset: int, width: int) -> int:
    if width not in (1, 2, 4, 8):
        raise ArchiveError(f"unsupported scalar width {width}")
    if offset < 0 or offset + width > len(blob):
        raise ArchiveError(
            f"{width} byte field at offset {offset} runs past the end of the stream"
        )
    return int.from_bytes(blob[offset : offset + width], "little")


def _element_length(
    blob: bytes,
    cursor: int,
    layout: ClassLayout,
    key: str,
    offset: int,
    base: int,
    element: VariableRun,
) -> int:
    if element.rule == STRING_RULE:
        try:
            _, consumed = read_string(blob, cursor + element.at)
        except ArchiveError as error:
            raise SegmentationError(
                layout.name, key, offset, str(error), base=base
            ) from error
        return element.at + consumed + element.tail
    if element.rule == COUNT_RULE:
        if element.count_width <= 0 or element.stride < 0:
            raise SegmentationError(
                layout.name,
                key,
                offset,
                "count rule is missing a count width or stride",
                base=base,
            )
        try:
            count = _scalar(blob, cursor + element.at, element.count_width)
        except ArchiveError as error:
            raise SegmentationError(
                layout.name, key, offset, str(error), base=base
            ) from error
        return element.at + element.count_width + element.stride * count + element.tail
    if element.rule == CONDITIONAL_RULE:
        if element.predicate_width <= 0 or not element.values:
            raise SegmentationError(
                layout.name,
                key,
                offset,
                "conditional rule is missing a predicate width or value set",
                base=base,
            )
        try:
            value = _scalar(
                blob,
                cursor + element.predicate_at,
                element.predicate_width,
            )
        except ArchiveError as error:
            raise SegmentationError(
                layout.name, key, offset, str(error), base=base
            ) from error
        present = element.width if value in element.values else 0
        return element.at + present + element.tail
    raise SegmentationError(
        layout.name,
        key,
        offset,
        f"run rule {element.rule!r} cannot be resolved statically"
        + (f" ({element.note})" if element.note else ""),
        base=base,
    )


def _run_length(
    blob: bytes,
    cursor: int,
    layout: ClassLayout,
    key: str,
    offset: int,
    base: int,
) -> int:
    if key in layout.runs:
        return layout.runs[key]
    elements = layout.variable_runs.get(key)
    if not elements:
        raise SegmentationError(
            layout.name,
            key,
            offset,
            "no constant run length and no rule recorded in the layout table",
            base=base,
        )
    length = 0
    for element in elements:
        length += _element_length(
            blob, cursor + length, layout, key, offset, base, element
        )
    return length


def _repeat_total(
    blob: bytes,
    run_start: int,
    layout: ClassLayout,
    offset: int,
    base: int,
) -> int:
    repeat = layout.repeat_count
    if repeat is None:
        raise SegmentationError(
            layout.name,
            LEAD_RUN,
            offset,
            "a repeated child count was requested without a repeat_count rule",
            base=base,
        )
    try:
        count = _scalar(blob, run_start + repeat.at, repeat.width)
    except ArchiveError as error:
        raise SegmentationError(
            layout.name, repeat.run, offset, str(error), base=base
        ) from error
    template = layout.template_slot
    if count < 0 or template < 0:
        raise SegmentationError(
            layout.name,
            repeat.run,
            offset,
            f"repeated child count {count} is not usable",
            base=base,
        )
    return template + count


def _advance(
    blob: bytes,
    cursor: int,
    amount: int,
    layout: ClassLayout,
    key: str,
    offset: int,
    base: int,
) -> int:
    end = cursor + amount
    if end > len(blob):
        raise SegmentationError(
            layout.name,
            key,
            offset,
            f"run of {amount} bytes at {cursor} runs past the {len(blob)} byte stream",
            base=base,
        )
    return end


def _segment_walk(
    blob: bytes,
    base: int,
    layouts: LayoutTable,
    header_size: int,
    segments: list[StaticSegment],
    progress: list[int],
) -> tuple[StaticSegment, ...]:
    if base < 1:
        raise ArchiveError(f"archive map base {base} must be positive")
    if header_size < 0 or header_size > len(blob):
        raise ArchiveError(
            f"stream header of {header_size} bytes does not fit a "
            f"{len(blob)} byte stream"
        )
    frames: list[_Frame] = []
    class_names: dict[int, str] = {}
    object_owner: dict[int, str] = {}
    counter = base
    cursor = header_size
    while True:
        if not frames and cursor == len(blob):
            break
        progress[0] = len(segments)
        progress[1] = len(frames)
        offset = cursor
        parent = frames[-1].node if frames else -1
        parent_name = frames[-1].class_name if frames else "<stream>"
        parent_slot = str(frames[-1].slot) if frames else LEAD_RUN
        try:
            tag = read_tag(blob, offset)
        except ArchiveError as error:
            raise SegmentationError(
                parent_name, parent_slot, offset, str(error), base=base
            ) from error
        if tag.kind == DEFINITION_KIND:
            class_index = counter
            object_index = counter + 1
            class_names[class_index] = tag.class_name
            object_owner[object_index] = tag.class_name
            counter += 2
            name = tag.class_name
        elif tag.kind == CLASS_REFERENCE_KIND:
            class_index = tag.index
            if class_index >= base and class_index not in class_names:
                raise SegmentationError(
                    parent_name,
                    parent_slot,
                    offset,
                    f"class reference {class_index} is at or above the base {base} "
                    "but no definition has been seen",
                    base=base,
                )
            name = class_names.get(class_index, f"external#{class_index}")
            object_index = counter
            object_owner[object_index] = name
            counter += 1
        elif tag.kind == OBJECT_REFERENCE_KIND:
            class_index = 0
            object_index = tag.index
            if object_index >= base and object_index not in object_owner:
                raise SegmentationError(
                    parent_name,
                    parent_slot,
                    offset,
                    f"object reference {object_index} is at or above the base {base} "
                    "but no such object has been seen",
                    base=base,
                )
            name = object_owner.get(object_index, f"external#{object_index}")
        else:
            class_index = 0
            object_index = 0
            name = NULL_KIND
        cursor = offset + tag.size
        if cursor > len(blob):
            raise SegmentationError(
                parent_name,
                parent_slot,
                offset,
                f"tag of {tag.size} bytes runs past the {len(blob)} byte stream",
                base=base,
            )
        node = len(segments)
        depth = len(frames)
        pushed = False
        if tag.kind in (DEFINITION_KIND, CLASS_REFERENCE_KIND):
            layout = layouts.get(name)
            if layout is None:
                raise SegmentationError(
                    name,
                    LEAD_RUN,
                    offset,
                    "no layout entry recorded for this class",
                    base=base,
                )
            if layout.repeats:
                raise SegmentationError(
                    name,
                    LEAD_RUN,
                    offset,
                    "child count is not constant and no repeat rule is recorded"
                    + (f" ({layout.repeat_note})" if layout.repeat_note else ""),
                    base=base,
                )
            if layout.child_slots:
                amount = _run_length(blob, cursor, layout, LEAD_RUN, offset, base)
                cursor = _advance(blob, cursor, amount, layout, LEAD_RUN, offset, base)
                frame = _Frame(
                    node=node,
                    class_name=name,
                    layout=layout,
                    slot=0,
                    total=(
                        -1
                        if layout.repeat_count is not None
                        else len(layout.child_slots)
                    ),
                )
                if (
                    layout.repeat_count is not None
                    and layout.repeat_count.run == LEAD_RUN
                ):
                    frame.total = _repeat_total(
                        blob, cursor - amount, layout, offset, base
                    )
                frames.append(frame)
                pushed = True
            else:
                amount = _run_length(blob, cursor, layout, LEAF_RUN, offset, base)
                cursor = _advance(blob, cursor, amount, layout, LEAF_RUN, offset, base)
        segments.append(
            StaticSegment(
                index=node,
                offset=offset,
                header=tag.size,
                end=cursor,
                kind=tag.kind,
                token=tag.token,
                wide=tag.wide,
                schema=tag.schema,
                class_name=name,
                class_index=class_index,
                object_index=object_index,
                depth=depth,
                parent=parent,
            )
        )
        if pushed:
            continue
        while frames:
            frame = frames[-1]
            key = frame.layout.run_key(frame.slot)
            origin = segments[frame.node].offset
            run_start = cursor
            amount = _run_length(blob, cursor, frame.layout, key, origin, base)
            cursor = _advance(blob, cursor, amount, frame.layout, key, origin, base)
            repeat = frame.layout.repeat_count
            if repeat is not None and frame.total < 0 and repeat.run == key:
                frame.total = _repeat_total(blob, run_start, frame.layout, origin, base)
            limit = frame.total if frame.total >= 0 else frame.layout.template_slot
            if frame.slot + 1 < limit:
                frame.slot += 1
                break
            if frame.total < 0:
                raise SegmentationError(
                    frame.class_name,
                    key,
                    origin,
                    "the repeated child count was not read before the repeated "
                    "slots began",
                    base=base,
                )
            frames.pop()
        segments[node].end = cursor
        if not frames and cursor > len(blob):
            raise SegmentationError(
                "<stream>",
                LEAD_RUN,
                offset,
                f"segmentation overran the {len(blob)} byte stream",
                base=base,
            )
    if frames:
        frame = frames[-1]
        raise SegmentationError(
            frame.class_name,
            str(frame.slot),
            segments[frame.node].offset,
            f"stream ended with {len(frames)} open objects",
            base=base,
        )
    if not segments:
        raise ArchiveError("stream holds no archive objects")
    progress[0] = len(segments)
    progress[1] = 0
    return tuple(segments)


def segment(
    blob: bytes,
    base: int,
    layouts: LayoutTable,
    *,
    header_size: int = STREAM_HEADER_SIZE,
) -> tuple[StaticSegment, ...]:
    progress = [0, 0]
    reached: list[StaticSegment] = []
    try:
        return _segment_walk(blob, base, layouts, header_size, reached, progress)
    except SegmentationError as error:
        if error.progress < 0:
            error.progress = progress[0]
            error.depth = progress[1]
        if not error.reached:
            error.reached = tuple(reached)
        raise


def build_model(
    blob: bytes, segments: Sequence[StaticSegment], base: int, header_size: int
) -> Model:
    if not segments:
        raise ArchiveError("cannot build a model from an empty segmentation")
    model = Model(header=blob[:header_size], base=base)
    class_position: dict[int, int] = {}
    object_position: dict[int, int] = {}
    for position, item in enumerate(segments):
        body = blob[item.offset + item.header : item.end]
        if item.kind == DEFINITION_KIND:
            model.nodes.append(
                Node(
                    kind=DEFINITION_KIND,
                    body=body,
                    schema=item.schema,
                    class_name=item.class_name,
                    origin=item.offset,
                )
            )
            class_position[item.class_index] = position
            object_position[item.object_index] = position
        elif item.kind == CLASS_REFERENCE_KIND:
            model.nodes.append(
                Node(
                    kind=CLASS_REFERENCE_KIND,
                    body=body,
                    class_name=item.class_name,
                    literal=item.class_index,
                    wide=item.wide,
                    target=class_position.get(item.class_index, -1),
                    origin=item.offset,
                )
            )
            object_position[item.object_index] = position
        elif item.kind == OBJECT_REFERENCE_KIND:
            model.nodes.append(
                Node(
                    kind=OBJECT_REFERENCE_KIND,
                    body=body,
                    literal=item.object_index,
                    wide=item.wide,
                    target=object_position.get(item.object_index, -1),
                    origin=item.offset,
                )
            )
        elif item.kind == NULL_KIND:
            model.nodes.append(Node(kind=NULL_KIND, body=body, origin=item.offset))
        else:
            raise ArchiveError(
                f"unsupported tag kind {item.kind!r} at offset {item.offset}"
            )
    for position, item in enumerate(segments):
        node = model.nodes[position]
        if (
            node.kind == OBJECT_REFERENCE_KIND
            and node.target < 0
            and item.object_index >= base
        ):
            raise ArchiveError(
                f"object reference {item.object_index} at offset {item.offset} "
                "is unresolved"
            )
        if (
            node.kind == CLASS_REFERENCE_KIND
            and node.target < 0
            and item.class_index >= base
        ):
            raise ArchiveError(
                f"class reference {item.class_index} at offset {item.offset} "
                "is unresolved"
            )
    model.assign()
    return model


def tiling(
    blob: bytes, segments: Sequence[StaticSegment], header_size: int
) -> dict[str, object]:
    gaps: list[tuple[int, int]] = []
    overlaps: list[tuple[int, int]] = []
    cursor = header_size
    for item in segments:
        if item.offset > cursor:
            gaps.append((cursor, item.offset))
        elif item.offset < cursor:
            overlaps.append((item.offset, cursor))
        cursor = item.end
    trailing = len(blob) - cursor
    return {
        "header_bytes": header_size,
        "gaps": gaps,
        "overlaps": overlaps,
        "trailing_bytes": trailing,
        "covered": cursor - header_size,
        "tiles": not gaps and not overlaps and trailing == 0,
    }


@dataclass(frozen=True, slots=True)
class VerifyReport:
    length: int
    base: int
    header_bytes: int
    segmented: bool
    tiled: bool
    identical: bool
    object_count: int
    definition_count: int
    gaps: tuple[tuple[int, int], ...]
    overlaps: tuple[tuple[int, int], ...]
    trailing_bytes: int
    error: str
    blocking_class: str
    blocking_slot: str
    blocking_offset: int
    blocking_depth: int

    def as_dict(self) -> dict[str, object]:
        return {
            "length": self.length,
            "base": self.base,
            "header_bytes": self.header_bytes,
            "segmented": self.segmented,
            "tiled": self.tiled,
            "identical": self.identical,
            "object_count": self.object_count,
            "definition_count": self.definition_count,
            "gaps": [list(item) for item in self.gaps],
            "overlaps": [list(item) for item in self.overlaps],
            "trailing_bytes": self.trailing_bytes,
            "error": self.error,
            "blocking_class": self.blocking_class,
            "blocking_slot": self.blocking_slot,
            "blocking_offset": self.blocking_offset,
            "blocking_depth": self.blocking_depth,
        }


def verify(
    blob: bytes,
    base: int,
    layouts: LayoutTable,
    *,
    header_size: int = STREAM_HEADER_SIZE,
) -> VerifyReport:
    try:
        segments = segment(blob, base, layouts, header_size=header_size)
    except SegmentationError as error:
        return VerifyReport(
            length=len(blob),
            base=base,
            header_bytes=header_size,
            segmented=False,
            tiled=False,
            identical=False,
            object_count=max(error.progress, 0),
            definition_count=0,
            gaps=(),
            overlaps=(),
            trailing_bytes=len(blob) - header_size,
            error=str(error),
            blocking_class=error.class_name,
            blocking_slot=error.slot,
            blocking_offset=error.offset,
            blocking_depth=error.depth,
        )
    except ArchiveError as error:
        return VerifyReport(
            length=len(blob),
            base=base,
            header_bytes=header_size,
            segmented=False,
            tiled=False,
            identical=False,
            object_count=0,
            definition_count=0,
            gaps=(),
            overlaps=(),
            trailing_bytes=len(blob) - header_size,
            error=str(error),
            blocking_class="",
            blocking_slot="",
            blocking_offset=-1,
            blocking_depth=-1,
        )
    shape = tiling(blob, segments, header_size)
    definitions = sum(1 for item in segments if item.kind == DEFINITION_KIND)
    try:
        model = build_model(blob, segments, base, header_size)
        rebuilt = model.emit()
        identical = rebuilt == blob
        message = "" if identical else f"re-emit produced {len(rebuilt)} bytes"
    except ArchiveError as error:
        identical = False
        message = str(error)
    return VerifyReport(
        length=len(blob),
        base=base,
        header_bytes=header_size,
        segmented=True,
        tiled=bool(shape["tiles"]),
        identical=identical,
        object_count=len(segments),
        definition_count=definitions,
        gaps=tuple(tuple(item) for item in shape["gaps"]),
        overlaps=tuple(tuple(item) for item in shape["overlaps"]),
        trailing_bytes=int(shape["trailing_bytes"]),
        error=message,
        blocking_class="",
        blocking_slot="",
        blocking_offset=-1,
        blocking_depth=-1,
    )


def class_names(segments: Iterable[StaticSegment]) -> tuple[str, ...]:
    seen: dict[str, None] = {}
    for item in segments:
        if item.kind in (DEFINITION_KIND, CLASS_REFERENCE_KIND):
            seen[item.class_name] = None
    return tuple(seen)
