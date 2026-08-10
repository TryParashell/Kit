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
# resolved feature streams end with one fixed footer dword
KStreamTailSize = 4
MO_VERSION_PREFIX = "_MO_VERSION_"
DEFINITION_KIND = "definition"
CLASS_REFERENCE_KIND = "classref"
OBJECT_REFERENCE_KIND = "objectref"
NULL_KIND = "null"
LEAD_RUN = "lead"
LEAF_RUN = "leaf"
TAIL_RUN = "tail"
REPEATED_SLOT = "..."
POLYMORPHIC_SLOT = "*"
OPAQUE_RULE = "opaque"
STRING_RULE = "string"
COUNT_RULE = "count"
CONDITIONAL_RULE = "conditional"
# guard rules reject unsupported record variants before advancing
KGuardRule = "guard"
EXTERNAL_PREFIX = "external#"
BASE_RESOLUTION_LIMIT = 64


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
        unresolved_index: int = -1,
        unresolved_kind: str = "",
    ) -> None:
        self.class_name = class_name
        self.slot = slot
        self.offset = offset
        self.reason = reason
        self.base = base
        self.progress = progress
        self.depth = depth
        self.unresolved_index = unresolved_index
        self.unresolved_kind = unresolved_kind
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


def container_mo_version(stream_names: Iterable[str]) -> int | None:
    found: set[int] = set()
    for name in stream_names:
        head = str(name).replace("\\", "/").split("/", 1)[0]
        if not head.startswith(MO_VERSION_PREFIX):
            continue
        digits = head[len(MO_VERSION_PREFIX) :]
        if digits.isdigit():
            found.add(int(digits))
    if not found:
        return None
    return max(found)


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
        if units == 0:
            raise ArchiveError(f"class definition at offset {offset} has an empty name")
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


# The native CString operators share this variable-width MFC length decoder.
def ParseArchiveStringLength(blob: bytes, offset: int) -> tuple[int, bool, int]:
    if offset < 0 or offset >= len(blob):
        raise ArchiveError(f"string length at offset {offset} is missing")
    First = blob[offset]
    if First != SHORT_STRING_LIMIT:
        return First, False, 1
    if offset + 3 > len(blob):
        raise ArchiveError(f"string length at offset {offset} has no 16 bit value")
    Second = struct.unpack_from("<H", blob, offset + 1)[0]
    if Second == LONG_STRING_LIMIT:
        return 0, True, 3
    if Second != 0xFFFF:
        return Second, False, 3
    if offset + 7 > len(blob):
        raise ArchiveError(f"string length at offset {offset} has no 32 bit value")
    return struct.unpack_from("<I", blob, offset + 3)[0], False, 7


def read_string(blob: bytes, offset: int) -> tuple[str, int]:
    Units, IsUnicode, Head = ParseArchiveStringLength(blob, offset)
    if IsUnicode:
        Units, IsSecondMarker, SecondHead = ParseArchiveStringLength(
            blob, offset + Head
        )
        if IsSecondMarker:
            raise ArchiveError(f"string at offset {offset} repeats its Unicode marker")
        Head += SecondHead
    Width = 2 if IsUnicode else 1
    End = offset + Head + Width * Units
    if End > len(blob):
        raise ArchiveError(
            f"string at offset {offset} claims {Units} units past the end"
        )
    Encoding = "utf-16-le" if IsUnicode else "latin-1"
    return blob[offset + Head : End].decode(Encoding), End - offset


def encode_string(text: str) -> bytes:
    encoded = text.encode("utf-16-le")
    units = len(encoded) // 2
    if units < SHORT_STRING_LIMIT:
        return STRING_MARKER + bytes((units,)) + encoded
    if units < LONG_STRING_LIMIT:
        return STRING_MARKER + b"\xff" + struct.pack("<H", units) + encoded
    if units <= 0xFFFFFFFF:
        return STRING_MARKER + b"\xff\xff\xff" + struct.pack("<I", units) + encoded
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


# archive models preserve framing around mutable object nodes
@dataclass(slots=True)
class Model:
    header: bytes
    base: int
    nodes: list[Node] = field(default_factory=list)
    Trailer: bytes = b""

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
            Trailer=self.Trailer,
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
        out += self.Trailer
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


# version gated tails keep variable records aligned across document generations
@dataclass(frozen=True, slots=True)
class VariableRun:
    slot: str
    rule: str
    at: int
    tail: int
    TailByVersion: Mapping[int, int]
    stride: int
    count_width: int
    width: int
    predicate: str
    predicate_at: int
    predicate_width: int
    values: tuple[int, ...]
    note: str


# repeat fields locate dynamic child counts within a preceding scalar run
@dataclass(frozen=True, slots=True)
class RepeatField:
    run: str
    at: int
    Back: int
    width: int


# child count branches keep conditional serializer paths inside their owning object
@dataclass(frozen=True, slots=True)
class ChildCountByClass:
    Slot: int
    Counts: Mapping[str, int]


# group count branches preserve serializer paths whose next array header moves with the
# runtime class of the preceding tagged child
@dataclass(frozen=True, slots=True)
class RunGroupCount:
    At: int
    Back: int
    Width: int
    Lead: int


# group count variants preserve fixed serializer branches selected by inline state
@dataclass(frozen=True, slots=True)
class RunGroupCountVariant:
    Versions: tuple[int, ...]
    PredicateAt: int
    PredicateWidth: int
    Values: tuple[int, ...]
    Count: int
    Lead: int


# group run variants preserve inline discriminator branches without fitting whole records
@dataclass(frozen=True, slots=True)
class RunGroupVariant:
    Slot: int
    Last: bool
    StopGroups: bool
    Versions: tuple[int, ...]
    PredicateAt: int
    PredicateWidth: int
    Values: tuple[int, ...]
    ChildClasses: tuple[str, ...]
    Run: int
    RunsByVersion: Mapping[int, int]
    Trailer: int


# group trailer variants keep empty-loop gates and post-loop branches in the group grammar
@dataclass(frozen=True, slots=True)
class RunGroupTrailerVariant:
    Versions: tuple[int, ...]
    PredicateAt: int
    PredicateWidth: int
    Values: tuple[int, ...]
    Trailer: int


# run groups describe ordered counted serializer loops inside otherwise inline records
@dataclass(frozen=True, slots=True)
class RunGroup:
    name: str
    repeat: int
    count_back: int
    count_width: int
    CountByChildClass: Mapping[str, RunGroupCount]
    CountVariants: tuple[RunGroupCountVariant, ...]
    slots: tuple[str, ...]
    element: tuple[int, ...]
    element_by_version: Mapping[int, tuple[int, ...]]
    ElementRunVariants: tuple[RunGroupVariant, ...]
    trailer: int
    TrailerVariants: tuple[RunGroupTrailerVariant, ...]
    note: str

    def element_runs(self, mo_version: int | None) -> tuple[int, ...]:
        if mo_version is not None:
            gated = self.element_by_version.get(mo_version)
            if gated is not None:
                return gated
        return self.element


# class records need one immutable shape shared by parsing verification and emission
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
    repeat_prefix: int = 0
    RepeatTrailer: int = 0
    ChildCounts: ChildCountByClass | None = None
    runs_by_version: Mapping[str, Mapping[int, int]] = field(default_factory=dict)
    RunsByChildClass: Mapping[str, Mapping[str, int]] = field(default_factory=dict)
    groups: tuple[RunGroup, ...] = ()

    @property
    def walks_groups(self) -> bool:
        return bool(self.groups)

    @property
    def repeats(self) -> bool:
        return self.repeat_unresolved and self.repeat_prefix <= 0

    @property
    def walks_a_prefix(self) -> bool:
        return self.repeat_unresolved and self.repeat_prefix > 0

    @property
    def constant_run_keys(self) -> frozenset[str]:
        return frozenset(
            set(self.runs) | set(self.runs_by_version) | set(self.RunsByChildClass)
        )

    def constant_run(self, key: str, mo_version: int | None) -> int | None:
        gated = self.runs_by_version.get(key)
        if gated is not None and mo_version is not None:
            length = gated.get(mo_version)
            if length is not None:
                return length
        return self.runs.get(key)

    @property
    def template_slot(self) -> int:
        return len(self.child_slots) - 2

    def run_key(self, slot: int) -> str:
        if self.walks_a_prefix and slot >= self.repeat_prefix - 1:
            return TAIL_RUN
        if self.repeat_count is not None and slot >= self.template_slot:
            return str(self.template_slot)
        return str(slot)

    def run_keys(self) -> tuple[str, ...]:
        if self.groups:
            if TAIL_RUN in self.constant_run_keys or TAIL_RUN in self.variable_runs:
                return (LEAD_RUN, TAIL_RUN)
            return (LEAD_RUN,)
        if not self.child_slots:
            return (LEAF_RUN,)
        if self.walks_a_prefix:
            return (
                (LEAD_RUN,)
                + tuple(str(slot) for slot in range(self.repeat_prefix - 1))
                + (TAIL_RUN,)
            )
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


# group count parsing enforces an unambiguous forward or backward scalar locator
def ParseRunGroupCount(
    OwnerName: str,
    GroupName: str,
    Entry: Mapping[str, object],
    HasLead: bool,
) -> RunGroupCount:
    RawAt = Entry.get("at")
    RawBack = Entry.get("back")
    HasAt = RawAt is not None
    HasBack = RawBack is not None
    At = int(RawAt) if HasAt else 0
    Back = int(RawBack) if HasBack else 0
    Width = int(Entry.get("width", 0) or 0)
    Lead = int(Entry.get("lead", 0) or 0)
    if (
        HasAt == HasBack
        or Width not in (1, 2, 4)
        or At < 0
        or Back < 0
        or Lead < 0
        or (HasBack and Back < Width)
        or (HasAt and HasLead and At + Width > Lead)
    ):
        raise ArchiveError(
            f"run group {OwnerName}@{GroupName} has a malformed count locator"
        )
    if not HasLead and Lead:
        raise ArchiveError(
            f"run group {OwnerName}@{GroupName} has a count lead outside a class branch"
        )
    return RunGroupCount(At=At, Back=Back, Width=Width, Lead=Lead)


# run group parsing converts the reverse engineered JSON contract into immutable rules
def _run_group(name: str, entry: Mapping[str, object]) -> RunGroup:
    label = str(entry.get("name", ""))
    if not label:
        raise ArchiveError(f"a run group of {name!r} has no name")
    raw_element = entry.get("element", ())
    if isinstance(raw_element, str) or not isinstance(raw_element, Sequence):
        raise ArchiveError(f"run group {name}@{label} has a malformed element")
    element = tuple(int(value) for value in raw_element)
    if not element or any(value < 0 for value in element):
        raise ArchiveError(
            f"run group {name}@{label} needs one non negative run per element child"
        )
    raw_slots = entry.get("slots", ())
    if isinstance(raw_slots, str) or not isinstance(raw_slots, Sequence):
        raise ArchiveError(f"run group {name}@{label} has a malformed slots list")
    slots = tuple(str(value) for value in raw_slots)
    if len(slots) != len(element):
        raise ArchiveError(
            f"run group {name}@{label} names {len(slots)} slots for "
            f"{len(element)} element runs"
        )
    trailer = int(entry.get("trailer", 0) or 0)
    if trailer < 0:
        raise ArchiveError(f"run group {name}@{label} has a negative trailer")
    raw_gated = entry.get("element_by_version", {})
    if not isinstance(raw_gated, Mapping):
        raise ArchiveError(
            f"run group {name}@{label} has a malformed element_by_version"
        )
    gated: dict[int, tuple[int, ...]] = {}
    for version, values in raw_gated.items():
        text = str(version)
        if not text.isdigit():
            raise ArchiveError(
                f"run group {name}@{label} names a non numeric document "
                f"version {text!r}"
            )
        if isinstance(values, str) or not isinstance(values, Sequence):
            raise ArchiveError(
                f"run group {name}@{label} at document version {text} has no element"
            )
        widths = tuple(int(value) for value in values)
        if len(widths) != len(element) or any(value < 0 for value in widths):
            raise ArchiveError(
                f"run group {name}@{label} at document version {text} does not hold "
                f"{len(element)} non negative runs"
            )
        gated[int(text)] = widths
    RawVariants = entry.get("element_run_variants", ())
    if isinstance(RawVariants, (str, Mapping)) or not isinstance(RawVariants, Sequence):
        raise ArchiveError(
            f"run group {name}@{label} has malformed element_run_variants"
        )
    Variants: list[RunGroupVariant] = []
    for RawVariant in RawVariants:
        if not isinstance(RawVariant, Mapping):
            raise ArchiveError(
                f"run group {name}@{label} has a malformed element run variant"
            )
        Slot = int(RawVariant.get("slot", -1))
        PredicateAt = int(RawVariant.get("predicate_at", 0))
        PredicateWidth = int(RawVariant.get("predicate_width", 0))
        RawValues = RawVariant.get("values", ())
        RawChildClasses = RawVariant.get("child_classes", ())
        RawLast = RawVariant.get("last", False)
        RawStopGroups = RawVariant.get("stop_groups", False)
        RawVersions = RawVariant.get("versions", ())
        Run = int(RawVariant.get("run", -1))
        RawVersionRuns = RawVariant.get("runs_by_version", {})
        RawTrailer = RawVariant.get("trailer")
        Trailer = int(RawTrailer) if RawTrailer is not None else -1
        if (
            Slot < 0
            or Slot >= len(element)
            or PredicateAt < 0
            or isinstance(RawValues, str)
            or not isinstance(RawValues, Sequence)
            or any(
                not isinstance(Value, int) or isinstance(Value, bool) or Value < 0
                for Value in RawValues
            )
            or isinstance(RawChildClasses, str)
            or not isinstance(RawChildClasses, Sequence)
            or any(
                not isinstance(ChildClass, str) or not ChildClass
                for ChildClass in RawChildClasses
            )
            or not isinstance(RawLast, bool)
            or not isinstance(RawStopGroups, bool)
            or isinstance(RawVersions, (str, Mapping))
            or not isinstance(RawVersions, Sequence)
            or any(
                not isinstance(Version, int) or isinstance(Version, bool) or Version < 0
                for Version in RawVersions
            )
            or Run < 0
            or not isinstance(RawVersionRuns, Mapping)
            or Trailer < -1
            or (not RawValues and not RawChildClasses)
            or (RawValues and PredicateWidth not in (1, 2, 4, 8))
            or (not RawValues and PredicateWidth != 0)
        ):
            raise ArchiveError(
                f"run group {name}@{label} has a malformed element run variant"
            )
        VersionRuns: dict[int, int] = {}
        for Version, Width in RawVersionRuns.items():
            VersionText = str(Version)
            if (
                not VersionText.isdigit()
                or not isinstance(Width, int)
                or isinstance(Width, bool)
                or Width < 0
            ):
                raise ArchiveError(
                    f"run group {name}@{label} has a malformed versioned "
                    "element run variant"
                )
            VersionRuns[int(VersionText)] = int(Width)
        Variants.append(
            RunGroupVariant(
                Slot=Slot,
                Last=RawLast,
                StopGroups=RawStopGroups,
                Versions=tuple(int(Version) for Version in RawVersions),
                PredicateAt=PredicateAt,
                PredicateWidth=PredicateWidth,
                Values=tuple(int(Value) for Value in RawValues),
                ChildClasses=tuple(str(ChildClass) for ChildClass in RawChildClasses),
                Run=Run,
                RunsByVersion=VersionRuns,
                Trailer=Trailer,
            )
        )
    RawTrailerVariants = entry.get("trailer_variants", ())
    if isinstance(RawTrailerVariants, (str, Mapping)) or not isinstance(
        RawTrailerVariants, Sequence
    ):
        raise ArchiveError(f"run group {name}@{label} has malformed trailer_variants")
    TrailerVariants: list[RunGroupTrailerVariant] = []
    for RawVariant in RawTrailerVariants:
        if not isinstance(RawVariant, Mapping):
            raise ArchiveError(
                f"run group {name}@{label} has a malformed trailer variant"
            )
        RawVersions = RawVariant.get("versions", ())
        PredicateAt = RawVariant.get("predicate_at", 0)
        PredicateWidth = RawVariant.get("predicate_width", 0)
        RawValues = RawVariant.get("values", ())
        RawTrailer = RawVariant.get("trailer", -1)
        if (
            isinstance(RawVersions, (str, Mapping))
            or not isinstance(RawVersions, Sequence)
            or any(
                not isinstance(Version, int) or isinstance(Version, bool) or Version < 0
                for Version in RawVersions
            )
            or not isinstance(PredicateAt, int)
            or isinstance(PredicateAt, bool)
            or PredicateAt < 0
            or PredicateWidth not in (1, 2, 4, 8)
            or isinstance(RawValues, (str, Mapping))
            or not isinstance(RawValues, Sequence)
            or not RawValues
            or any(
                not isinstance(Value, int) or isinstance(Value, bool) or Value < 0
                for Value in RawValues
            )
            or not isinstance(RawTrailer, int)
            or isinstance(RawTrailer, bool)
            or RawTrailer < 0
        ):
            raise ArchiveError(
                f"run group {name}@{label} has a malformed trailer variant"
            )
        TrailerVariants.append(
            RunGroupTrailerVariant(
                Versions=tuple(int(Version) for Version in RawVersions),
                PredicateAt=PredicateAt,
                PredicateWidth=PredicateWidth,
                Values=tuple(int(Value) for Value in RawValues),
                Trailer=RawTrailer,
            )
        )
    RawCountVariants = entry.get("count_variants", ())
    if isinstance(RawCountVariants, (str, Mapping)) or not isinstance(
        RawCountVariants, Sequence
    ):
        raise ArchiveError(f"run group {name}@{label} has malformed count_variants")
    CountVariants: list[RunGroupCountVariant] = []
    for RawVariant in RawCountVariants:
        if not isinstance(RawVariant, Mapping):
            raise ArchiveError(
                f"run group {name}@{label} has a malformed count variant"
            )
        RawVersions = RawVariant.get("versions", ())
        PredicateAt = RawVariant.get("predicate_at", 0)
        PredicateWidth = RawVariant.get("predicate_width", 0)
        RawValues = RawVariant.get("values", ())
        RawCount = RawVariant.get("count", -1)
        RawLead = RawVariant.get("lead", 0)
        if (
            isinstance(RawVersions, (str, Mapping))
            or not isinstance(RawVersions, Sequence)
            or any(
                not isinstance(Version, int) or isinstance(Version, bool) or Version < 0
                for Version in RawVersions
            )
            or not isinstance(PredicateAt, int)
            or isinstance(PredicateAt, bool)
            or PredicateAt < 0
            or PredicateWidth not in (1, 2, 4, 8)
            or isinstance(RawValues, (str, Mapping))
            or not isinstance(RawValues, Sequence)
            or not RawValues
            or any(
                not isinstance(Value, int) or isinstance(Value, bool) or Value < 0
                for Value in RawValues
            )
            or not isinstance(RawCount, int)
            or isinstance(RawCount, bool)
            or RawCount < 0
            or not isinstance(RawLead, int)
            or isinstance(RawLead, bool)
            or RawLead < 0
        ):
            raise ArchiveError(
                f"run group {name}@{label} has a malformed count variant"
            )
        CountVariants.append(
            RunGroupCountVariant(
                Versions=tuple(int(Version) for Version in RawVersions),
                PredicateAt=PredicateAt,
                PredicateWidth=PredicateWidth,
                Values=tuple(int(Value) for Value in RawValues),
                Count=RawCount,
                Lead=RawLead,
            )
        )
    raw_count = entry.get("count")
    raw_repeat = entry.get("repeat")
    RawCountBranches = entry.get("count_by_child_class", {})
    if not isinstance(RawCountBranches, Mapping):
        raise ArchiveError(
            f"run group {name}@{label} has malformed count_by_child_class"
        )
    CountBranches: dict[str, RunGroupCount] = {}
    for ChildClass, RawBranch in RawCountBranches.items():
        if not str(ChildClass) or not isinstance(RawBranch, Mapping):
            raise ArchiveError(f"run group {name}@{label} has a malformed count branch")
        CountBranches[str(ChildClass)] = ParseRunGroupCount(
            name,
            label,
            RawBranch,
            True,
        )
    if raw_count is None and raw_repeat is None:
        raise ArchiveError(f"run group {name}@{label} has neither a count nor a repeat")
    if raw_count is not None and raw_repeat is not None:
        raise ArchiveError(f"run group {name}@{label} has both a count and a repeat")
    note = str(entry.get("note", ""))
    if raw_repeat is not None:
        if CountBranches or CountVariants:
            raise ArchiveError(
                f"run group {name}@{label} repeats a constant and cannot branch its count"
            )
        if (
            not isinstance(raw_repeat, int)
            or isinstance(raw_repeat, bool)
            or raw_repeat < 1
        ):
            raise ArchiveError(
                f"run group {name}@{label} has a repeat that is not a positive integer"
            )
        return RunGroup(
            name=label,
            repeat=int(raw_repeat),
            count_back=0,
            count_width=0,
            CountByChildClass={},
            CountVariants=(),
            slots=slots,
            element=element,
            element_by_version=gated,
            ElementRunVariants=tuple(Variants),
            trailer=trailer,
            TrailerVariants=tuple(TrailerVariants),
            note=note,
        )
    if not isinstance(raw_count, Mapping):
        raise ArchiveError(f"run group {name}@{label} has a malformed count")
    Count = ParseRunGroupCount(name, label, raw_count, False)
    if not Count.Back:
        raise ArchiveError(
            f"run group {name}@{label} has a forward default count without a lead"
        )
    return RunGroup(
        name=label,
        repeat=-1,
        count_back=Count.Back,
        count_width=Count.Width,
        CountByChildClass=CountBranches,
        CountVariants=tuple(CountVariants),
        slots=slots,
        element=element,
        element_by_version=gated,
        ElementRunVariants=tuple(Variants),
        trailer=trailer,
        TrailerVariants=tuple(TrailerVariants),
        note=note,
    )


# layout validation prevents malformed reverse engineered rules from corrupting later records
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
    raw_gated = entry.get("runs_by_version", {})
    if not isinstance(raw_gated, Mapping):
        raise ArchiveError(f"layout entry for {name!r} has a malformed runs_by_version")
    gated: dict[str, Mapping[int, int]] = {}
    for key, mapping in raw_gated.items():
        if not isinstance(mapping, Mapping):
            raise ArchiveError(
                f"runs_by_version {name}@{key} does not hold a version mapping"
            )
        by_version: dict[int, int] = {}
        for version, value in mapping.items():
            text = str(version)
            if not text.isdigit():
                raise ArchiveError(
                    f"runs_by_version {name}@{key} names a "
                    f"non numeric document version {text!r}"
                )
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise ArchiveError(
                    f"run {name}@{key} at document version {text} is not a "
                    "non negative integer"
                )
            by_version[int(text)] = int(value)
        if not by_version:
            raise ArchiveError(f"runs_by_version {name}@{key} names no version")
        gated[str(key)] = by_version
    RawChildRuns = entry.get("runs_by_child_class", {})
    if not isinstance(RawChildRuns, Mapping):
        raise ArchiveError(
            f"layout entry for {name!r} has malformed runs_by_child_class"
        )
    ChildRuns: dict[str, Mapping[str, int]] = {}
    for RunKey, RawClassRuns in RawChildRuns.items():
        if not isinstance(RawClassRuns, Mapping) or not RawClassRuns:
            raise ArchiveError(
                f"runs_by_child_class {name}@{RunKey} has no class mapping"
            )
        ClassRuns: dict[str, int] = {}
        for ChildClass, RunValue in RawClassRuns.items():
            if (
                not str(ChildClass)
                or not isinstance(RunValue, int)
                or isinstance(RunValue, bool)
                or RunValue < 0
            ):
                raise ArchiveError(
                    f"run {name}@{RunKey} for child {ChildClass!r} is malformed"
                )
            ClassRuns[str(ChildClass)] = int(RunValue)
        ChildRuns[str(RunKey)] = ClassRuns
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
        RawTailGate = item.get("tail_by_version", {})
        if not isinstance(RawTailGate, Mapping):
            raise ArchiveError(
                f"variable run {name}@{slot} has malformed tail_by_version"
            )
        TailGate: dict[int, int] = {}
        for VersionText, TailValue in RawTailGate.items():
            VersionName = str(VersionText)
            if not VersionName.isdigit():
                raise ArchiveError(
                    f"variable run {name}@{slot} names a non numeric "
                    f"tail version {VersionName!r}"
                )
            if (
                not isinstance(TailValue, int)
                or isinstance(TailValue, bool)
                or TailValue < 0
            ):
                raise ArchiveError(
                    f"variable run {name}@{slot} has an invalid tail for "
                    f"document version {VersionName}"
                )
            TailGate[int(VersionName)] = int(TailValue)
        variable.setdefault(slot, []).append(
            VariableRun(
                slot=slot,
                rule=str(item.get("rule", OPAQUE_RULE)),
                at=int(item.get("at", 0) or 0),
                tail=int(item.get("tail", 0) or 0),
                TailByVersion=TailGate,
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
        RawAt = raw_repeat.get("at")
        RawBack = raw_repeat.get("back")
        HasAt = RawAt is not None
        HasBack = RawBack is not None
        at = int(RawAt) if HasAt else 0
        Back = int(RawBack) if HasBack else 0
        width = int(raw_repeat.get("width", 0))
        if (
            not run
            or HasAt == HasBack
            or at < 0
            or Back < 0
            or width not in (1, 2, 4)
            or (HasBack and Back < width)
        ):
            raise ArchiveError(f"repeat_count of {name!r} is malformed")
        if len(slots) < 2:
            raise ArchiveError(f"repeat_count of {name!r} has no template slot")
        repeat = RepeatField(run=run, at=at, Back=Back, width=width)
    unresolved = (REPEATED_SLOT in slots or raw_repeat is not None) and repeat is None
    raw_prefix = entry.get("repeat_prefix", 0)
    if (
        not isinstance(raw_prefix, int)
        or isinstance(raw_prefix, bool)
        or raw_prefix < 0
    ):
        raise ArchiveError(f"repeat_prefix of {name!r} is not a non negative integer")
    prefix = int(raw_prefix)
    if prefix and not unresolved:
        raise ArchiveError(
            f"repeat_prefix of {name!r} names a prefix for a class whose child "
            "count is already resolved"
        )
    if prefix > len(slots):
        raise ArchiveError(
            f"repeat_prefix {prefix} of {name!r} exceeds its {len(slots)} child slots"
        )
    RepeatTrailer = entry.get("repeat_trailer", 0)
    if (
        not isinstance(RepeatTrailer, int)
        or isinstance(RepeatTrailer, bool)
        or RepeatTrailer < 0
    ):
        raise ArchiveError(f"repeat_trailer of {name!r} is not a non negative integer")
    if RepeatTrailer and repeat is None:
        raise ArchiveError(f"repeat_trailer of {name!r} has no resolved repeat_count")
    RawChildCounts = entry.get("child_count_by_class")
    ChildCounts: ChildCountByClass | None = None
    if RawChildCounts is not None:
        if not isinstance(RawChildCounts, Mapping):
            raise ArchiveError(f"child_count_by_class of {name!r} is malformed")
        RawCountSlot = RawChildCounts.get("slot")
        RawCounts = RawChildCounts.get("counts")
        if (
            not isinstance(RawCountSlot, int)
            or isinstance(RawCountSlot, bool)
            or not isinstance(RawCounts, Mapping)
        ):
            raise ArchiveError(f"child_count_by_class of {name!r} is malformed")
        CountSlot = int(RawCountSlot)
        Counts: dict[str, int] = {}
        for ClassName, CountValue in RawCounts.items():
            if (
                not str(ClassName)
                or not isinstance(CountValue, int)
                or isinstance(CountValue, bool)
                or CountValue <= CountSlot
                or CountValue > len(slots)
            ):
                raise ArchiveError(
                    f"child count branch {name}@{ClassName} is malformed"
                )
            Counts[str(ClassName)] = int(CountValue)
        if CountSlot < 0 or CountSlot >= len(slots) or not Counts:
            raise ArchiveError(f"child_count_by_class of {name!r} is malformed")
        if repeat is not None or unresolved or prefix:
            raise ArchiveError(
                f"child_count_by_class of {name!r} conflicts with a repeat rule"
            )
        ChildCounts = ChildCountByClass(Slot=CountSlot, Counts=Counts)
    raw_groups = entry.get("groups", ())
    if isinstance(raw_groups, str) or not isinstance(raw_groups, Sequence):
        raise ArchiveError(f"layout entry for {name!r} has a malformed groups list")
    parsed: list[RunGroup] = []
    for item in raw_groups:
        if not isinstance(item, Mapping):
            raise ArchiveError(f"a run group of {name!r} is not a mapping")
        parsed.append(_run_group(name, item))
    groups = tuple(parsed)
    if groups and (slots or repeat is not None or unresolved or prefix):
        raise ArchiveError(
            f"layout entry for {name!r} drives its children from run groups and "
            "must not also declare child slots"
        )
    if groups and LEAD_RUN not in runs and LEAD_RUN not in gated:
        raise ArchiveError(f"layout entry for {name!r} has run groups but no lead run")
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
        repeat_prefix=prefix,
        RepeatTrailer=RepeatTrailer,
        ChildCounts=ChildCounts,
        runs_by_version=gated,
        RunsByChildClass=ChildRuns,
        groups=groups,
    )


@dataclass(slots=True)
class _Frame:
    node: int
    class_name: str
    layout: ClassLayout
    slot: int
    total: int
    group: int = 0
    step: int = 0
    plan: tuple[int, ...] = ()
    key: str = LEAD_RUN
    ChildClass: str = ""


def _scalar(blob: bytes, offset: int, width: int) -> int:
    if width not in (1, 2, 4, 8):
        raise ArchiveError(f"unsupported scalar width {width}")
    if offset < 0 or offset + width > len(blob):
        raise ArchiveError(
            f"{width} byte field at offset {offset} runs past the end of the stream"
        )
    return int.from_bytes(blob[offset : offset + width], "little")


# variable element sizing lets the static walk cross strings arrays and gated tails safely
def _element_length(
    blob: bytes,
    cursor: int,
    layout: ClassLayout,
    key: str,
    offset: int,
    base: int,
    element: VariableRun,
    mo_version: int | None,
) -> int:
    TailValue = element.tail
    if mo_version is not None:
        TailValue = element.TailByVersion.get(mo_version, TailValue)
    if element.rule == STRING_RULE:
        try:
            _, consumed = read_string(blob, cursor + element.at)
        except ArchiveError as error:
            raise SegmentationError(
                layout.name, key, offset, str(error), base=base
            ) from error
        return element.at + consumed + TailValue
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
        return element.at + element.count_width + element.stride * count + TailValue
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
        return element.at + present + TailValue
    if element.rule == KGuardRule:
        if element.predicate_width <= 0 or not element.values:
            raise SegmentationError(
                layout.name,
                key,
                offset,
                "guard rule is missing a predicate width or value set",
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
        if value not in element.values:
            raise SegmentationError(
                layout.name,
                key,
                offset,
                f"guard predicate {element.predicate!r} rejected value {value}",
                base=base,
            )
        return element.at + TailValue
    raise SegmentationError(
        layout.name,
        key,
        offset,
        f"run rule {element.rule!r} cannot be resolved statically"
        + (f" ({element.note})" if element.note else ""),
        base=base,
    )


# one run resolver centralizes refusal semantics before the parser advances its cursor
def _run_length(
    blob: bytes,
    cursor: int,
    layout: ClassLayout,
    key: str,
    offset: int,
    base: int,
    mo_version: int | None,
    ChildClass: str = "",
) -> int:
    ClassRuns = layout.RunsByChildClass.get(key)
    if ClassRuns is not None:
        ClassLength = ClassRuns.get(ChildClass)
        if ClassLength is None:
            raise SegmentationError(
                layout.name,
                key,
                offset,
                f"run branch has no case for child class {ChildClass!r}",
                base=base,
            )
        return ClassLength
    constant = layout.constant_run(key, mo_version)
    if constant is not None:
        return constant
    elements = layout.variable_runs.get(key)
    if not elements:
        reason = "no constant run length and no rule recorded in the layout table"
        if key in layout.runs_by_version:
            reason += (
                f" for document version {mo_version}"
                if mo_version is not None
                else " and no document version was supplied"
            )
        raise SegmentationError(
            layout.name,
            key,
            offset,
            reason,
            base=base,
        )
    length = 0
    for element in elements:
        length += _element_length(
            blob,
            cursor + length,
            layout,
            key,
            offset,
            base,
            element,
            mo_version,
        )
    return length


# repeat totals make variable child collections statically walkable
def _repeat_total(
    blob: bytes,
    run_start: int,
    run_end: int,
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
        CountAt = run_end - repeat.Back if repeat.Back else run_start + repeat.at
        count = _scalar(blob, CountAt, repeat.width)
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


# grouped element sizing selects the decompiled discriminator branch before advancing
def _group_element_length(
    blob: bytes,
    cursor: int,
    frame: _Frame,
    offset: int,
    base: int,
    mo_version: int | None,
) -> tuple[int, int | None, bool]:
    Group = frame.layout.groups[frame.group - 1]
    Slot = frame.step % len(Group.element)
    for Variant in Group.ElementRunVariants:
        if Variant.Slot != Slot:
            continue
        if Variant.Last and frame.step + 1 != len(frame.plan):
            continue
        if Variant.Versions and mo_version not in Variant.Versions:
            continue
        if Variant.ChildClasses and frame.ChildClass not in Variant.ChildClasses:
            continue
        MatchesPredicate = not Variant.Values
        if Variant.Values:
            try:
                Value = _scalar(
                    blob,
                    cursor + Variant.PredicateAt,
                    Variant.PredicateWidth,
                )
            except ArchiveError as error:
                raise SegmentationError(
                    frame.layout.name,
                    Group.name,
                    offset,
                    str(error),
                    base=base,
                ) from error
            MatchesPredicate = Value in Variant.Values
        if MatchesPredicate:
            Length = Variant.Run
            if mo_version is not None:
                Length = Variant.RunsByVersion.get(mo_version, Length)
            Trailer = Variant.Trailer if Variant.Trailer >= 0 else None
            return Length, Trailer, Variant.StopGroups
    return frame.plan[frame.step], None, False


# grouped trailer sizing selects empty-loop and post-loop discriminator branches
def _group_trailer_length(
    blob: bytes,
    cursor: int,
    layout: ClassLayout,
    Group: RunGroup,
    offset: int,
    base: int,
    mo_version: int | None,
) -> int:
    for Variant in Group.TrailerVariants:
        if Variant.Versions and mo_version not in Variant.Versions:
            continue
        try:
            Value = _scalar(
                blob,
                cursor + Variant.PredicateAt,
                Variant.PredicateWidth,
            )
        except ArchiveError as error:
            raise SegmentationError(
                layout.name,
                Group.name,
                offset,
                str(error),
                base=base,
            ) from error
        if Value in Variant.Values:
            return Variant.Trailer
    return Group.trailer


# resolved stream framing is identified before excluding its footer
def GetTailSize(blob: bytes, base: int, header_size: int) -> int:
    if header_size != STREAM_HEADER_SIZE or len(blob) < header_size + KStreamTailSize:
        return 0
    if int.from_bytes(blob[:4], "little") != base:
        return 0
    if blob[-KStreamTailSize:] != bytes(KStreamTailSize):
        return 0
    return KStreamTailSize


def _group_open(
    blob: bytes,
    cursor: int,
    frame: _Frame,
    offset: int,
    base: int,
    mo_version: int | None,
) -> tuple[int, bool]:
    layout = frame.layout
    while frame.group < len(layout.groups):
        group = layout.groups[frame.group]
        frame.group += 1
        frame.key = group.name
        if group.repeat >= 0:
            count = group.repeat
            GroupLead = 0
        else:
            count = -1
            GroupLead = 0
            for CountVariant in group.CountVariants:
                if CountVariant.Versions and mo_version not in CountVariant.Versions:
                    continue
                try:
                    Predicate = _scalar(
                        blob,
                        cursor + CountVariant.PredicateAt,
                        CountVariant.PredicateWidth,
                    )
                except ArchiveError as error:
                    raise SegmentationError(
                        layout.name, group.name, offset, str(error), base=base
                    ) from error
                if Predicate in CountVariant.Values:
                    count = CountVariant.Count
                    GroupLead = CountVariant.Lead
                    break
            if count < 0:
                CountBranch = group.CountByChildClass.get(frame.ChildClass)
                CountAt = cursor - group.count_back
                CountWidth = group.count_width
                if CountBranch is not None:
                    CountAt = (
                        cursor - CountBranch.Back
                        if CountBranch.Back
                        else cursor + CountBranch.At
                    )
                    CountWidth = CountBranch.Width
                    GroupLead = CountBranch.Lead
                try:
                    count = _scalar(blob, CountAt, CountWidth)
                except ArchiveError as error:
                    raise SegmentationError(
                        layout.name, group.name, offset, str(error), base=base
                    ) from error
        if count:
            cursor = _advance(
                blob,
                cursor,
                GroupLead,
                layout,
                group.name,
                offset,
                base,
            )
            frame.plan = tuple(group.element_runs(mo_version) * count)
            frame.step = 0
            return cursor, True
        Trailer = _group_trailer_length(
            blob,
            cursor,
            layout,
            group,
            offset,
            base,
            mo_version,
        )
        cursor = _advance(blob, cursor, Trailer, layout, group.name, offset, base)
    if TAIL_RUN in layout.constant_run_keys or TAIL_RUN in layout.variable_runs:
        amount = _run_length(
            blob,
            cursor,
            layout,
            TAIL_RUN,
            offset,
            base,
            mo_version,
        )
        cursor = _advance(blob, cursor, amount, layout, TAIL_RUN, offset, base)
    return cursor, False


def _declared_slot_class(layouts: LayoutTable, frames: Sequence[_Frame]) -> str:
    if not frames:
        return ""
    frame = frames[-1]
    layout = frame.layout
    if layout.groups:
        group = layout.groups[frame.group - 1]
        declared = group.slots[frame.step % len(group.slots)]
        if declared in (POLYMORPHIC_SLOT, REPEATED_SLOT) or declared not in layouts:
            return ""
        return declared
    slots = layout.child_slots
    slot = frame.slot
    if layout.repeat_count is not None and slot >= layout.template_slot:
        slot = layout.template_slot
    if slot < 0 or slot >= len(slots):
        return ""
    declared = slots[slot]
    if declared in (POLYMORPHIC_SLOT, REPEATED_SLOT):
        return ""
    if declared not in layouts:
        return ""
    return declared


def _external_name(
    class_index: int, layouts: LayoutTable, frames: Sequence[_Frame]
) -> str:
    alias = f"{EXTERNAL_PREFIX}{class_index}"
    if alias in layouts:
        return alias
    return _declared_slot_class(layouts, frames) or alias


# the stack walk preserves exact ownership while refusing every unresolved byte boundary
def _segment_walk(
    blob: bytes,
    base: int,
    layouts: LayoutTable,
    header_size: int,
    segments: list[StaticSegment],
    progress: list[int],
    mo_version: int | None,
) -> tuple[StaticSegment, ...]:
    if base < 1:
        raise ArchiveError(f"archive map base {base} must be positive")
    if header_size < 0 or header_size > len(blob):
        raise ArchiveError(
            f"stream header of {header_size} bytes does not fit a "
            f"{len(blob)} byte stream"
        )
    TrailerSize = GetTailSize(blob, base, header_size)
    ContentEnd = len(blob) - TrailerSize
    frames: list[_Frame] = []
    class_names: dict[int, str] = {}
    object_owner: dict[int, str] = {}
    counter = base
    cursor = header_size
    while True:
        if not frames and cursor == ContentEnd:
            break
        progress[0] = len(segments)
        progress[1] = len(frames)
        offset = cursor
        parent = frames[-1].node if frames else -1
        parent_name = frames[-1].class_name if frames else "<stream>"
        if frames and frames[-1].layout.groups:
            parent_slot = f"{frames[-1].key}[{frames[-1].step}]"
        else:
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
            DeclaredClass = _declared_slot_class(layouts, frames)
            if (
                class_index >= base
                and class_index not in class_names
                and not DeclaredClass
            ):
                raise SegmentationError(
                    parent_name,
                    parent_slot,
                    offset,
                    f"class reference {class_index} is at or above the base {base} "
                    "but no definition has been seen",
                    base=base,
                    unresolved_index=class_index,
                    unresolved_kind=CLASS_REFERENCE_KIND,
                )
            name = class_names.get(class_index, "")
            if not name and class_index >= base:
                name = DeclaredClass
            if not name:
                name = _external_name(class_index, layouts, frames)
            object_index = counter
            object_owner[object_index] = name
            counter += 1
        elif tag.kind == OBJECT_REFERENCE_KIND:
            class_index = 0
            object_index = tag.index
            DeclaredClass = _declared_slot_class(layouts, frames)
            if (
                object_index >= base
                and object_index not in object_owner
                and not DeclaredClass
            ):
                raise SegmentationError(
                    parent_name,
                    parent_slot,
                    offset,
                    f"object reference {object_index} is at or above the base {base} "
                    "but no such object has been seen",
                    base=base,
                    unresolved_index=object_index,
                    unresolved_kind=OBJECT_REFERENCE_KIND,
                )
            name = object_owner.get(
                object_index,
                DeclaredClass or f"{EXTERNAL_PREFIX}{object_index}",
            )
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
        if frames:
            frames[-1].ChildClass = name
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
            if layout.groups:
                amount = _run_length(
                    blob, cursor, layout, LEAD_RUN, offset, base, mo_version
                )
                cursor = _advance(blob, cursor, amount, layout, LEAD_RUN, offset, base)
                frame = _Frame(
                    node=node,
                    class_name=name,
                    layout=layout,
                    slot=0,
                    total=-1,
                )
                cursor, opened = _group_open(
                    blob, cursor, frame, offset, base, mo_version
                )
                if opened:
                    frames.append(frame)
                    pushed = True
            elif layout.child_slots:
                amount = _run_length(
                    blob, cursor, layout, LEAD_RUN, offset, base, mo_version
                )
                cursor = _advance(blob, cursor, amount, layout, LEAD_RUN, offset, base)
                total = -1
                if layout.walks_a_prefix:
                    total = layout.repeat_prefix
                elif layout.ChildCounts is not None:
                    total = -1
                elif layout.repeat_count is None:
                    total = len(layout.child_slots)
                elif layout.repeat_count.run == LEAD_RUN:
                    total = _repeat_total(
                        blob,
                        cursor - amount,
                        cursor,
                        layout,
                        offset,
                        base,
                    )
                if total != 0:
                    frames.append(
                        _Frame(
                            node=node,
                            class_name=name,
                            layout=layout,
                            slot=0,
                            total=total,
                        )
                    )
                    pushed = True
            else:
                amount = _run_length(
                    blob, cursor, layout, LEAF_RUN, offset, base, mo_version
                )
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
            origin = segments[frame.node].offset
            if frame.layout.groups:
                Group = frame.layout.groups[frame.group - 1]
                Amount, TrailerOverride, StopGroups = _group_element_length(
                    blob,
                    cursor,
                    frame,
                    origin,
                    base,
                    mo_version,
                )
                if frame.step + 1 == len(frame.plan):
                    Amount += (
                        _group_trailer_length(
                            blob,
                            cursor + Amount,
                            frame.layout,
                            Group,
                            origin,
                            base,
                            mo_version,
                        )
                        if TrailerOverride is None
                        else TrailerOverride
                    )
                cursor = _advance(
                    blob,
                    cursor,
                    Amount,
                    frame.layout,
                    frame.key,
                    origin,
                    base,
                )
                frame.step += 1
                if frame.step < len(frame.plan):
                    break
                if StopGroups:
                    frames.pop()
                    continue
                cursor, opened = _group_open(
                    blob, cursor, frame, origin, base, mo_version
                )
                if opened:
                    break
                frames.pop()
                continue
            key = frame.layout.run_key(frame.slot)
            run_start = cursor
            amount = _run_length(
                blob,
                cursor,
                frame.layout,
                key,
                origin,
                base,
                mo_version,
                frame.ChildClass,
            )
            cursor = _advance(blob, cursor, amount, frame.layout, key, origin, base)
            repeat = frame.layout.repeat_count
            if repeat is not None and frame.total < 0 and repeat.run == key:
                frame.total = _repeat_total(
                    blob,
                    run_start,
                    cursor,
                    frame.layout,
                    origin,
                    base,
                )
            ChildCounts = frame.layout.ChildCounts
            if (
                ChildCounts is not None
                and frame.total < 0
                and frame.slot == ChildCounts.Slot
            ):
                ResolvedCount = ChildCounts.Counts.get(frame.ChildClass)
                if ResolvedCount is None:
                    raise SegmentationError(
                        frame.class_name,
                        key,
                        origin,
                        f"child count branch has no case for {frame.ChildClass!r}",
                        base=base,
                    )
                frame.total = ResolvedCount
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
            if repeat is not None and frame.layout.RepeatTrailer:
                cursor = _advance(
                    blob,
                    cursor,
                    frame.layout.RepeatTrailer,
                    frame.layout,
                    TAIL_RUN,
                    origin,
                    base,
                )
            frames.pop()
        segments[node].end = cursor
        if not frames and cursor > ContentEnd:
            raise SegmentationError(
                "<stream>",
                LEAD_RUN,
                offset,
                f"segmentation overran the {ContentEnd} byte object region",
                base=base,
            )
    if frames:
        frame = frames[-1]
        raise SegmentationError(
            frame.class_name,
            frame.key if frame.layout.groups else str(frame.slot),
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
    mo_version: int | None = None,
) -> tuple[StaticSegment, ...]:
    if mo_version is not None and mo_version < 0:
        raise ArchiveError(f"document version {mo_version} must not be negative")
    progress = [0, 0]
    reached: list[StaticSegment] = []
    try:
        return _segment_walk(
            blob, base, layouts, header_size, reached, progress, mo_version
        )
    except SegmentationError as error:
        if error.progress < 0:
            error.progress = progress[0]
            error.depth = progress[1]
        if not error.reached:
            error.reached = tuple(reached)
        raise


@dataclass(frozen=True, slots=True)
class BaseResolution:
    base: int
    seed: int
    segmented: bool
    progress: int
    offset: int
    tried: tuple[int, ...]
    implied: tuple[int, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "base": self.base,
            "seed": self.seed,
            "segmented": self.segmented,
            "progress": self.progress,
            "offset": self.offset,
            "tried": list(self.tried),
            "implied": list(self.implied),
        }


def implied_bases(error: SegmentationError, base: int) -> tuple[int, ...]:
    if error.unresolved_index < 0:
        return ()
    if error.unresolved_kind != CLASS_REFERENCE_KIND:
        return ()
    offsets = {
        item.class_index - base
        for item in error.reached
        if item.kind == DEFINITION_KIND
    }
    found = {
        error.unresolved_index - value
        for value in offsets
        if error.unresolved_index - value >= 1
    }
    return tuple(sorted(found, reverse=True))


def resolve_base(
    blob: bytes,
    seed: int,
    layouts: LayoutTable,
    *,
    header_size: int = STREAM_HEADER_SIZE,
    mo_version: int | None = None,
    limit: int = BASE_RESOLUTION_LIMIT,
) -> BaseResolution:
    if seed < 1:
        raise ArchiveError(f"base seed {seed} must be positive")
    if limit < 1:
        raise ArchiveError(f"base resolution limit {limit} must be positive")
    queue: list[int] = [seed]
    tried: list[int] = []
    implied: list[int] = []
    chosen = seed
    best = (0, -1, -1)
    while queue and len(tried) < limit:
        candidate = queue.pop(0)
        if candidate < 1 or candidate in tried:
            continue
        tried.append(candidate)
        try:
            produced = segment(
                blob,
                candidate,
                layouts,
                header_size=header_size,
                mo_version=mo_version,
            )
        except SegmentationError as error:
            score = (0, error.progress, error.offset)
            if score > best:
                best = score
                chosen = candidate
            for value in implied_bases(error, candidate):
                if value not in tried and value not in queue:
                    queue.append(value)
                    implied.append(value)
            continue
        except ArchiveError:
            continue
        chosen = candidate
        best = (1, len(produced), len(blob))
        break
    return BaseResolution(
        base=chosen,
        seed=seed,
        segmented=bool(best[0]),
        progress=best[1],
        offset=best[2],
        tried=tuple(tried),
        implied=tuple(implied),
    )


# models retain references and stream framing for exact reemission
def build_model(
    blob: bytes,
    segments: Sequence[StaticSegment],
    base: int,
    header_size: int,
    TrailerSize: int = 0,
) -> Model:
    if not segments:
        raise ArchiveError("cannot build a model from an empty segmentation")
    if not TrailerSize:
        TrailerSize = GetTailSize(blob, base, header_size)
    ContentEnd = len(blob) - TrailerSize
    Trailer = blob[len(blob) - TrailerSize :] if TrailerSize else b""
    model = Model(header=blob[:header_size], base=base, Trailer=Trailer)
    class_position: dict[int, int] = {}
    object_position: dict[int, int] = {}
    for position, item in enumerate(segments):
        BodyEnd = min(item.end, ContentEnd)
        body = blob[item.offset + item.header : BodyEnd]
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
            and item.class_name.startswith(EXTERNAL_PREFIX)
        ):
            raise ArchiveError(
                f"object reference {item.object_index} at offset {item.offset} "
                "is unresolved"
            )
        if (
            node.kind == CLASS_REFERENCE_KIND
            and node.target < 0
            and item.class_index >= base
            and item.class_name.startswith(EXTERNAL_PREFIX)
        ):
            raise ArchiveError(
                f"class reference {item.class_index} at offset {item.offset} "
                "is unresolved"
            )
    model.assign()
    return model


# tiling checks object coverage independently from known stream framing
def tiling(
    blob: bytes,
    segments: Sequence[StaticSegment],
    header_size: int,
    TrailerSize: int = 0,
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
    trailing = len(blob) - TrailerSize - cursor
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
    mo_version: int | None = None,
) -> VerifyReport:
    try:
        segments = segment(
            blob, base, layouts, header_size=header_size, mo_version=mo_version
        )
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
    TrailerSize = GetTailSize(blob, base, header_size)
    shape = tiling(blob, segments, header_size, TrailerSize)
    definitions = sum(1 for item in segments if item.kind == DEFINITION_KIND)
    try:
        model = build_model(blob, segments, base, header_size, TrailerSize)
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
