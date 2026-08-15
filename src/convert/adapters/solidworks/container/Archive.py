# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations as Annotations
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass as Dataclass, field as Field
import json as JsonModule
from pathlib import Path as PathValue
import struct as Struct
from typing import TypeAlias, TypeGuard, TypedDict, TypeVar
from convert.adapters.solidworks.container.Container import SldprtFormatError

# this contract exists because decoded layouts need recursively concrete json values
LayoutValue: TypeAlias = (
    str | int | float | bool | None | list["LayoutValue"] | dict[str, "LayoutValue"]
)

# this contract exists because layout parsers only accept keyed json objects
LayoutObject: TypeAlias = Mapping[str, LayoutValue]

# this binding exists because layout constructors preserve concrete table subclasses
LayoutTableType = TypeVar("LayoutTableType", bound="LayoutTable")


# this guard exists because runtime json objects need a typed parsing boundary
def IsLayoutObject(Value: object) -> TypeGuard[LayoutObject]:
    return isinstance(Value, Mapping)


# this guard exists because layout lists must exclude textual scalar values
def IsLayoutSequence(Value: object) -> TypeGuard[Sequence[LayoutValue]]:
    return not isinstance(Value, str) and isinstance(Value, Sequence)


# this conversion exists because json scalar fields retain their existing numeric coercion
def LayoutInteger(Value: LayoutValue) -> int:
    if isinstance(Value, (str, int, float)):
        return int(Value)
    raise TypeError(f"layout value {Value!r} is not an integer")


# this contract exists because tiling results need fixed concrete report fields
class TilingReport(TypedDict):
    header_bytes: int
    gaps: list[tuple[int, int]]
    overlaps: list[tuple[int, int]]
    trailing_bytes: int
    covered: int
    tiles: bool


# this binding exists because shared behavior needs one stable value
KNullTag = 0

# this binding exists because shared behavior needs one stable value
KNewClassTag = 65535

# this binding exists because shared behavior needs one stable value
KBigObjectTag = 32767

# this binding exists because shared behavior needs one stable value
KClassTagBit = 32768

# this binding exists because shared behavior needs one stable value
KBigClassTagBit = 2147483648

# this binding exists because shared behavior needs one stable value
KMaxMapIndex = 1073741822

# this binding exists because shared behavior needs one stable value
KStringMarker = b"\xff\xfe\xff"

# this binding exists because shared behavior needs one stable value
KShortStringLimit = 255

# this binding exists because shared behavior needs one stable value
KLongStringLimit = 65534

# this binding exists because shared behavior needs one stable value
KStreamHeaderSize = 6

# this binding exists because shared behavior needs one stable value
KStreamTailSize = 4

# this binding exists because shared behavior needs one stable value
KMoVersionPrefix = "_MO_VERSION_"

# this binding exists because shared behavior needs one stable value
KDefinitionKind = "definition"

# this binding exists because shared behavior needs one stable value
KClassRefKind = "classref"

# this binding exists because shared behavior needs one stable value
KObjectRefKind = "objectref"

# this binding exists because shared behavior needs one stable value
KNullKind = "null"

# this binding exists because shared behavior needs one stable value
KLeadRun = "lead"

# this binding exists because shared behavior needs one stable value
KLeafRun = "leaf"

# this binding exists because shared behavior needs one stable value
KTailRun = "tail"

# this binding exists because shared behavior needs one stable value
KRepeatedSlot = "..."

# this binding exists because shared behavior needs one stable value
KPolymorphicSlot = "*"

# this binding exists because shared behavior needs one stable value
KOpaqueRule = "opaque"

# this binding exists because shared behavior needs one stable value
KStringRule = "string"

# this binding exists because shared behavior needs one stable value
KCountRule = "count"

# this binding exists because shared behavior needs one stable value
KConditionalRule = "conditional"

# this binding exists because shared behavior needs one stable value
KGuardRule = "guard"

# this binding exists because shared behavior needs one stable value
KOuterPrefix = "external#"

# this binding exists because shared behavior needs one stable value
KBaseResolutionLimit = 64


# this definition exists because focused behavior needs one stable owner
class ArchiveError(SldprtFormatError):
    KSlots = ()


# this definition exists because focused behavior needs one stable owner
class Segmentation(ArchiveError):
    KSlots = ()
    class_name: str
    slot: str
    offset: int
    reason: str
    base: int
    progress: int
    depth: int
    unresolved_index: int
    unresolved_kind: str
    reached: tuple[StaticSegment, ...]

    # this definition exists because focused behavior needs one stable owner
    def __init__(
        self,
        ClassName: str,
        SlotValue: str,
        Offset: int,
        Reason: str,
        *,
        BaseValue: int = -1,
        Progress: int = -1,
        Depth: int = -1,
        UnresolvedIndex: int = -1,
        UnresolvedKind: str = "",
    ) -> None:
        self.class_name = ClassName
        self.slot = SlotValue
        self.offset = Offset
        self.reason = Reason
        self.base = BaseValue
        self.progress = Progress
        self.depth = Depth
        self.unresolved_index = UnresolvedIndex
        self.unresolved_kind = UnresolvedKind
        self.reached = ()
        super().__init__(
            f"class {ClassName!r} slot {SlotValue!r} at byte offset {Offset}: {Reason}"
        )


# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class TagAction:
    kind: str
    size: int
    token: int
    index: int
    schema: int
    class_name: str
    wide: bool


# this definition exists because focused behavior needs one stable owner
def ContainerMo(StreamNames: Iterable[str]) -> int | None:
    Found: set[int] = set()
    for NameValue in StreamNames:
        HeadValue = str(NameValue).replace("\\", "/").split("/", 1)[0]
        if not HeadValue.startswith(KMoVersionPrefix):
            continue
        Digits = HeadValue[len(KMoVersionPrefix) :]
        if Digits.isdigit():
            Found.add(int(Digits))
    if not Found:
        return None
    return max(Found)


# this definition exists because focused behavior needs one stable owner
def ReadTag(BlobValue: bytes, Offset: int) -> TagAction:
    if Offset < 0:
        raise ArchiveError(f"negative tag offset {Offset}")
    if Offset + 2 > len(BlobValue):
        raise ArchiveError(
            f"tag at offset {Offset} runs past the end of a {len(BlobValue)} byte stream"
        )
    Token = Struct.unpack_from("<H", BlobValue, Offset)[0]
    if Token == KNewClassTag:
        return ReadClassTag(BlobValue, Offset, Token)
    if Token == KBigObjectTag:
        return ReadWideTag(BlobValue, Offset, Token)
    if Token == KNullTag:
        return TagAction(
            kind=KNullKind,
            size=2,
            token=Token,
            index=0,
            schema=0,
            class_name="",
            wide=False,
        )
    if Token & KClassTagBit:
        return TagAction(
            kind=KClassRefKind,
            size=2,
            token=Token,
            index=Token & ~KClassTagBit,
            schema=0,
            class_name="",
            wide=False,
        )
    return TagAction(
        kind=KObjectRefKind,
        size=2,
        token=Token,
        index=Token,
        schema=0,
        class_name="",
        wide=False,
    )


# this definition exists because class definition tags require dedicated name validation
def ReadClassTag(BlobValue: bytes, Offset: int, Token: int) -> TagAction:
    if Offset + 6 > len(BlobValue):
        raise ArchiveError(
            f"class definition at offset {Offset} has no schema and name length"
        )
    Schema, Units = Struct.unpack_from("<HH", BlobValue, Offset + 2)
    if Units == 0:
        raise ArchiveError(f"class definition at offset {Offset} has an empty name")
    if Offset + 6 + Units > len(BlobValue):
        raise ArchiveError(
            f"class definition at offset {Offset} names {Units} bytes past the end"
        )
    RawValue = BlobValue[Offset + 6 : Offset + 6 + Units]
    try:
        NameValue = RawValue.decode("ascii")
    except UnicodeDecodeError as ErrorInfo:
        raise ArchiveError(
            f"class definition at offset {Offset} has a non ascii name"
        ) from ErrorInfo
    return TagAction(
        kind=KDefinitionKind,
        size=6 + Units,
        token=Token,
        index=-1,
        schema=Schema,
        class_name=NameValue,
        wide=False,
    )


# this definition exists because wide reference tags require dedicated index validation
def ReadWideTag(BlobValue: bytes, Offset: int, Token: int) -> TagAction:
    if Offset + 6 > len(BlobValue):
        raise ArchiveError(f"big object tag at offset {Offset} has no 32 bit index")
    WideToken = Struct.unpack_from("<I", BlobValue, Offset + 2)[0]
    Index = WideToken & ~KBigClassTagBit
    if Index > KMaxMapIndex:
        raise ArchiveError(
            f"big object tag at offset {Offset} holds unrepresentable index {Index}"
        )
    KindValue = KClassRefKind if WideToken & KBigClassTagBit else KObjectRefKind
    return TagAction(
        kind=KindValue,
        size=6,
        token=Token,
        index=Index,
        schema=0,
        class_name="",
        wide=True,
    )


# this definition exists because focused behavior needs one stable owner
def EncodeClass(NameValue: str, Schema: int) -> bytes:
    try:
        Encoded = NameValue.encode("ascii")
    except UnicodeEncodeError as ErrorInfo:
        raise ArchiveError(f"class name {NameValue!r} is not ascii") from ErrorInfo
    if not Encoded:
        raise ArchiveError("class name must not be empty")
    if len(Encoded) > 65535:
        raise ArchiveError(f"class name {NameValue!r} is longer than 65535 bytes")
    if not 0 <= Schema <= 65535:
        raise ArchiveError(f"class schema {Schema} does not fit in 16 bits")
    return Struct.pack("<HHH", KNewClassTag, Schema, len(Encoded)) + Encoded


# this definition exists because focused behavior needs one stable owner
def EncodeClassRef(Index: int, *, WideValue: bool = False, **Options: object) -> bytes:
    WideValue = CompatOption(Options, "wide", WideValue, "EncodeClassRef")
    if Index < 0:
        raise ArchiveError(f"negative class index {Index}")
    if Index > KMaxMapIndex:
        raise ArchiveError(f"class index {Index} exceeds the archive map limit")
    if WideValue or Index >= KBigObjectTag:
        return Struct.pack("<HI", KBigObjectTag, Index | KBigClassTagBit)
    return Struct.pack("<H", KClassTagBit | Index)


# this definition exists because focused behavior needs one stable owner
def EncodeObjectRef(Index: int, *, WideValue: bool = False, **Options: object) -> bytes:
    WideValue = CompatOption(Options, "wide", WideValue, "EncodeObjectRef")
    if Index < 0:
        raise ArchiveError(f"negative object index {Index}")
    if Index > KMaxMapIndex:
        raise ArchiveError(f"object index {Index} exceeds the archive map limit")
    if Index == KNullTag and (not WideValue):
        return Struct.pack("<H", KNullTag)
    if WideValue or Index >= KBigObjectTag:
        return Struct.pack("<HI", KBigObjectTag, Index)
    return Struct.pack("<H", Index)


# this definition exists because one legacy keyword alias needs consistent unknown option errors
def CompatOption(
    Options: Mapping[str, object], KeyValue: str, Current: bool, Caller: str
) -> bool:
    Unknown = set(Options) - {KeyValue}
    if Unknown:
        NameValue = next(iter(Unknown))
        raise TypeError(f"{Caller}() got an unexpected keyword argument '{NameValue}'")
    Value = Options.get(KeyValue, Current)
    if not isinstance(Value, bool):
        raise TypeError(f"{Caller}() {KeyValue} must be a boolean")
    return Value


# this definition exists because focused behavior needs one stable owner
def EncodeNull() -> bytes:
    return Struct.pack("<H", KNullTag)


# this definition exists because focused behavior needs one stable owner
def ParseArchive(BlobValue: bytes, Offset: int) -> tuple[int, bool, int]:
    if Offset < 0 or Offset >= len(BlobValue):
        raise ArchiveError(f"string length at offset {Offset} is missing")
    First = BlobValue[Offset]
    if First != KShortStringLimit:
        return (First, False, 1)
    if Offset + 3 > len(BlobValue):
        raise ArchiveError(f"string length at offset {Offset} has no 16 bit value")
    Second = Struct.unpack_from("<H", BlobValue, Offset + 1)[0]
    if Second == KLongStringLimit:
        return (0, True, 3)
    if Second != 65535:
        return (Second, False, 3)
    if Offset + 7 > len(BlobValue):
        raise ArchiveError(f"string length at offset {Offset} has no 32 bit value")
    return (Struct.unpack_from("<I", BlobValue, Offset + 3)[0], False, 7)


# this definition exists because focused behavior needs one stable owner
def ReadString(BlobValue: bytes, Offset: int) -> tuple[str, int]:
    Units, IsUnicode, HeadValue = ParseArchive(BlobValue, Offset)
    if IsUnicode:
        Units, IsSecondMarker, SecondHead = ParseArchive(BlobValue, Offset + HeadValue)
        if IsSecondMarker:
            raise ArchiveError(f"string at offset {Offset} repeats its Unicode marker")
        HeadValue += SecondHead
    Width = 2 if IsUnicode else 1
    EndValue = Offset + HeadValue + Width * Units
    if EndValue > len(BlobValue):
        raise ArchiveError(
            f"string at offset {Offset} claims {Units} units past the end"
        )
    Encoding = "utf-16-le" if IsUnicode else "latin-1"
    return (
        BlobValue[Offset + HeadValue : EndValue].decode(Encoding),
        EndValue - Offset,
    )


# this definition exists because focused behavior needs one stable owner
def EncodeString(TextValue: str) -> bytes:
    Encoded = TextValue.encode("utf-16-le")
    Units = len(Encoded) // 2
    if Units < KShortStringLimit:
        return KStringMarker + bytes((Units,)) + Encoded
    if Units < KLongStringLimit:
        return KStringMarker + b"\xff" + Struct.pack("<H", Units) + Encoded
    if Units <= 4294967295:
        return KStringMarker + b"\xff\xff\xff" + Struct.pack("<I", Units) + Encoded
    raise ArchiveError(f"string of {Units} code units is not representable")


# this definition exists because focused behavior needs one stable owner
@Dataclass(slots=True)
class NodeAction:
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


# this definition exists because focused behavior needs one stable owner
@Dataclass(slots=True)
class Model:
    header: bytes
    base: int
    nodes: list[NodeAction] = Field(default_factory=list[NodeAction])
    Trailer: bytes = b""

    # this definition exists because focused behavior needs one stable owner
    def Clone(self) -> Model:
        return Model(
            header=self.header,
            base=self.base,
            nodes=[
                NodeAction(
                    kind=NodeValue.kind,
                    body=NodeValue.body,
                    schema=NodeValue.schema,
                    class_name=NodeValue.class_name,
                    target=NodeValue.target,
                    literal=NodeValue.literal,
                    wide=NodeValue.wide,
                    origin=NodeValue.origin,
                )
                for NodeValue in self.nodes
            ],
            Trailer=self.Trailer,
        )

    # this definition exists because focused behavior needs one stable owner
    def DefinitionIndex(self, NameValue: str) -> int:
        for Position, NodeValue in enumerate(self.nodes):
            if NodeValue.kind == KDefinitionKind and NodeValue.class_name == NameValue:
                return Position
        raise KeyError(NameValue)

    # this definition exists because focused behavior needs one stable owner
    def Assign(self) -> None:
        AssignModel(self)

    # this definition exists because focused behavior needs one stable owner
    def EmitAction(self) -> bytes:
        return EmitModelMut(self)

    assign = Assign
    clone = Clone
    definition_index = DefinitionIndex
    emit = EmitAction


# this definition exists because archive index assignment is independent from model storage
def AssignModel(ModelData: Model) -> None:
    Counter = ModelData.base
    for NodeValue in ModelData.nodes:
        if NodeValue.kind == KDefinitionKind:
            setattr(NodeValue, "class_index", Counter)
            setattr(NodeValue, "object_index", Counter + 1)
            Counter += 2
        elif NodeValue.kind == KClassRefKind:
            setattr(NodeValue, "class_index", 0)
            setattr(NodeValue, "object_index", Counter)
            Counter += 1
        else:
            setattr(NodeValue, "class_index", 0)
            setattr(NodeValue, "object_index", 0)


# this definition exists because model emission owns tag encoding order and trailer placement
def EmitModelMut(ModelData: Model) -> bytes:
    ModelData.assign()
    OutValue = bytearray(ModelData.header)
    for NodeValue in ModelData.nodes:
        if NodeValue.kind == KDefinitionKind:
            OutValue += EncodeClass(NodeValue.class_name, NodeValue.schema)
        elif NodeValue.kind == KClassRefKind:
            Index = (
                NodeValue.literal
                if NodeValue.target < 0
                else ModelData.nodes[NodeValue.target].class_index
            )
            OutValue += EncodeClassRef(Index, WideValue=NodeValue.wide)
        elif NodeValue.kind == KObjectRefKind:
            Index = (
                NodeValue.literal
                if NodeValue.target < 0
                else ModelData.nodes[NodeValue.target].object_index
            )
            OutValue += EncodeObjectRef(Index, WideValue=NodeValue.wide)
        elif NodeValue.kind == KNullKind:
            OutValue += EncodeNull()
        else:
            raise ArchiveError(f"cannot emit node kind {NodeValue.kind!r}")
        OutValue += NodeValue.body
    OutValue += ModelData.Trailer
    return bytes(OutValue)


# this definition exists because focused behavior needs one stable owner
@Dataclass(slots=True)
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


# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
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


# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class RepeatField:
    run: str
    at: int
    Back: int
    width: int


# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class ChildCountBy:
    Slot: int
    Counts: Mapping[str, int]


# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class RunGroupCount:
    At: int
    Back: int
    Width: int
    Lead: int


# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class RunGroupCountA:
    Versions: tuple[int, ...]
    PredicateAt: int
    PredicateWidth: int
    Values: tuple[int, ...]
    Count: int
    Lead: int


# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
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


# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class RunGroupTrailer:
    Versions: tuple[int, ...]
    PredicateAt: int
    PredicateWidth: int
    Values: tuple[int, ...]
    Trailer: int


# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class RunGroup:
    name: str
    repeat: int
    count_back: int
    count_width: int
    CountByChildClass: Mapping[str, RunGroupCount]
    CountVariants: tuple[RunGroupCountA, ...]
    slots: tuple[str, ...]
    element: tuple[int, ...]
    element_by_version: Mapping[int, tuple[int, ...]]
    ElementRunVariants: tuple[RunGroupVariant, ...]
    trailer: int
    TrailerVariants: tuple[RunGroupTrailer, ...]
    note: str

    # this definition exists because focused behavior needs one stable owner
    def ElemRuns(self, MoVersion: int | None) -> tuple[int, ...]:
        if MoVersion is not None:
            Gated = self.element_by_version.get(MoVersion)
            if Gated is not None:
                return Gated
        return self.element

    element_runs = ElemRuns


# this definition exists because layout state predicates form one focused property interface
class LayoutFlags:
    groups: tuple[RunGroup, ...]
    repeat_unresolved: bool
    repeat_prefix: int
    runs: Mapping[str, int]
    runs_by_version: Mapping[str, Mapping[int, int]]
    RunsByChildClass: Mapping[str, Mapping[str, int]]
    child_slots: tuple[str, ...]
    variable_runs: Mapping[str, tuple[VariableRun, ...]]

    # this definition exists because focused behavior needs one stable owner
    @property
    def IsWalksGroups(self) -> bool:
        return bool(self.groups)

    # this definition exists because focused behavior needs one stable owner
    @property
    def IsRepeats(self) -> bool:
        return self.repeat_unresolved and self.repeat_prefix <= 0

    # this definition exists because focused behavior needs one stable owner
    @property
    def IsWalksAPrefix(self) -> bool:
        return self.repeat_unresolved and self.repeat_prefix > 0

    # this definition exists because focused behavior needs one stable owner
    @property
    def ConstantRunKeys(self) -> frozenset[str]:
        return frozenset(
            set(self.runs) | set(self.runs_by_version) | set(self.RunsByChildClass)
        )

    # this definition exists because focused behavior needs one stable owner
    @property
    def TemplateSlot(self) -> int:
        return len(self.child_slots) - 2

    constant_run_keys = ConstantRunKeys
    repeats = IsRepeats
    template_slot = TemplateSlot
    walks_a_prefix = IsWalksAPrefix
    walks_groups = IsWalksGroups
    Repeats = IsRepeats
    WalksAPrefix = IsWalksAPrefix
    WalksGroups = IsWalksGroups


# this definition exists because layout run selection forms one focused lookup interface
class LayoutRuns:
    child_slots: tuple[str, ...]
    groups: tuple[RunGroup, ...]
    repeat_count: RepeatField | None
    repeat_prefix: int
    template_slot: int
    runs: Mapping[str, int]
    runs_by_version: Mapping[str, Mapping[int, int]]
    variable_runs: Mapping[str, tuple[VariableRun, ...]]
    walks_a_prefix: bool
    constant_run_keys: frozenset[str]

    # this definition exists because focused behavior needs one stable owner
    def ConstantRun(self, KeyValue: str, MoVersion: int | None) -> int | None:
        Gated = self.runs_by_version.get(KeyValue)
        if Gated is not None and MoVersion is not None:
            Length = Gated.get(MoVersion)
            if Length is not None:
                return Length
        return self.runs.get(KeyValue)

    # this definition exists because focused behavior needs one stable owner
    def RunKey(self, SlotValue: int) -> str:
        if self.walks_a_prefix and SlotValue >= self.repeat_prefix - 1:
            return KTailRun
        if self.repeat_count is not None and SlotValue >= self.template_slot:
            return str(self.template_slot)
        return str(SlotValue)

    # this definition exists because focused behavior needs one stable owner
    def RunKeys(self) -> tuple[str, ...]:
        if self.groups:
            if KTailRun in self.constant_run_keys or KTailRun in self.variable_runs:
                return (KLeadRun, KTailRun)
            return (KLeadRun,)
        if not self.child_slots:
            return (KLeafRun,)
        if self.walks_a_prefix:
            return (
                (KLeadRun,)
                + tuple((str(SlotValue) for SlotValue in range(self.repeat_prefix - 1)))
                + (KTailRun,)
            )
        SpanValue = (
            self.template_slot + 1
            if self.repeat_count is not None
            else len(self.child_slots)
        )
        return (KLeadRun,) + tuple((str(SlotValue) for SlotValue in range(SpanValue)))

    constant_run = ConstantRun
    run_key = RunKey
    run_keys = RunKeys


# this definition exists because class layout storage composes state and run selection behavior
@Dataclass(frozen=True, slots=True)
class ClassLayout(LayoutFlags, LayoutRuns):
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
    ChildCounts: ChildCountBy | None = None
    runs_by_version: Mapping[str, Mapping[int, int]] = Field(
        default_factory=dict[str, Mapping[int, int]]
    )
    RunsByChildClass: Mapping[str, Mapping[str, int]] = Field(
        default_factory=dict[str, Mapping[str, int]]
    )
    groups: tuple[RunGroup, ...] = ()


# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class LayoutTable:
    version: int
    source: str
    classes: Mapping[str, ClassLayout]

    # this definition exists because focused behavior needs one stable owner
    def IsContains(self, NameValue: object) -> bool:
        return NameValue in self.classes

    # this definition exists because focused behavior needs one stable owner
    def Getitem(self, NameValue: str) -> ClassLayout:
        return self.classes[NameValue]

    # this definition exists because focused behavior needs one stable owner
    def GetAction(self, NameValue: str) -> ClassLayout | None:
        return self.classes.get(NameValue)

    # this definition exists because focused behavior needs one stable owner
    @classmethod
    def FromMapping(
        cls: type[LayoutTableType], Payload: LayoutObject
    ) -> LayoutTableType:
        return ParseLayouts(cls, Payload)

    # this definition exists because focused behavior needs one stable owner
    @classmethod
    def LoadAction(
        cls: type[LayoutTableType], SourcePath: str | Path
    ) -> LayoutTableType:
        return LoadLayouts(cls, SourcePath)

    __contains__ = IsContains
    __getitem__ = Getitem
    from_mapping = FromMapping
    get = GetAction
    load = LoadAction
    Contains = IsContains


# this definition exists because layout mapping validation is independent from table storage
def ParseLayouts(
    ClassType: type[LayoutTableType], Payload: LayoutObject
) -> LayoutTableType:
    RawClasses = Payload.get("classes")
    if not IsLayoutObject(RawClasses):
        raise ArchiveError("layout table has no classes mapping")
    Classes: dict[str, ClassLayout] = {}
    for NameValue, Entry in RawClasses.items():
        if not IsLayoutObject(Entry):
            raise ArchiveError(f"layout entry for {NameValue!r} is not a mapping")
        Classes[NameValue] = ClassLayoutA(str(NameValue), Entry)
    Version = Payload.get("version", 1)
    Source = Payload.get("source", "")
    return ClassType(
        version=int(Version) if isinstance(Version, int) else 1,
        source=str(Source),
        classes=Classes,
    )


# this definition exists because layout file loading owns filesystem and json failures
def LoadLayouts(
    ClassType: type[LayoutTableType], SourcePath: str | Path
) -> LayoutTableType:
    Location = PathValue(SourcePath)
    try:
        Payload: object = JsonModule.loads(Location.read_text(encoding="utf-8"))
    except OSError as ErrorInfo:
        raise ArchiveError(f"cannot read layout table {Location}") from ErrorInfo
    except JsonModule.JSONDecodeError as ErrorInfo:
        raise ArchiveError(f"layout table {Location} is not valid json") from ErrorInfo
    if not IsLayoutObject(Payload):
        raise ArchiveError(f"layout table {Location} is not a json object")
    return ClassType.from_mapping(Payload)


# this definition exists because focused behavior needs one stable owner
def ParseRunGroup(
    OwnerName: str, GroupName: str, Entry: LayoutObject, HasLead: bool
) -> RunGroupCount:
    RawAt = Entry.get("at")
    RawBack = Entry.get("back")
    HasAt = RawAt is not None
    HasBack = RawBack is not None
    AtValue = LayoutInteger(RawAt) if HasAt else 0
    BackValue = LayoutInteger(RawBack) if HasBack else 0
    Width = LayoutInteger(Entry.get("width", 0) or 0)
    LeadValue = LayoutInteger(Entry.get("lead", 0) or 0)
    if (
        HasAt == HasBack
        or Width not in (1, 2, 4)
        or AtValue < 0
        or (BackValue < 0)
        or (LeadValue < 0)
        or (HasBack and BackValue < Width)
        or (HasAt and HasLead and (AtValue + Width > LeadValue))
    ):
        raise ArchiveError(
            f"run group {OwnerName}@{GroupName} has a malformed count locator"
        )
    if not HasLead and LeadValue:
        raise ArchiveError(
            f"run group {OwnerName}@{GroupName} has a count lead outside a class branch"
        )
    return RunGroupCount(At=AtValue, Back=BackValue, Width=Width, Lead=LeadValue)


# this definition exists because focused behavior needs one stable owner
def RunGroupA(NameValue: str, Entry: LayoutObject) -> RunGroup:
    Label, ElemValue, Slots, TrailerA = GroupBase(NameValue, Entry)
    Gated = GroupGated(NameValue, Label, ElemValue, Entry)
    Variants = GroupVariants(NameValue, Label, ElemValue, Entry)
    TrailerVariants = GroupTrailers(NameValue, Label, Entry)
    CountVariants = CountVariantsA(NameValue, Label, Entry)
    CountBranches = CountBranchesA(NameValue, Label, Entry)
    return FinalRunGroup(
        NameValue,
        Label,
        ElemValue,
        Slots,
        TrailerA,
        Gated,
        Variants,
        TrailerVariants,
        CountVariants,
        CountBranches,
        Entry,
    )


# this definition exists because group element and slot validation forms one structural boundary
def GroupBase(
    NameValue: str, Entry: LayoutObject
) -> tuple[str, tuple[int, ...], tuple[str, ...], int]:
    Label = str(Entry.get("name", ""))
    if not Label:
        raise ArchiveError(f"a run group of {NameValue!r} has no name")
    RawElem = Entry.get("element", ())
    if not IsLayoutSequence(RawElem):
        raise ArchiveError(f"run group {NameValue}@{Label} has a malformed element")
    ElemValue = tuple((LayoutInteger(Value) for Value in RawElem))
    if not ElemValue or any((Value < 0 for Value in ElemValue)):
        raise ArchiveError(
            f"run group {NameValue}@{Label} needs one non negative run per element child"
        )
    RawSlots = Entry.get("slots", ())
    if not IsLayoutSequence(RawSlots):
        raise ArchiveError(f"run group {NameValue}@{Label} has a malformed slots list")
    Slots = tuple((str(Value) for Value in RawSlots))
    if len(Slots) != len(ElemValue):
        raise ArchiveError(
            f"run group {NameValue}@{Label} names {len(Slots)} slots for {len(ElemValue)} element runs"
        )
    TrailerA = LayoutInteger(Entry.get("trailer", 0) or 0)
    if TrailerA < 0:
        raise ArchiveError(f"run group {NameValue}@{Label} has a negative trailer")
    return (Label, ElemValue, Slots, TrailerA)


# this definition exists because version gated element widths share one validation boundary
def GroupGated(
    NameValue: str, Label: str, ElemValue: tuple[int, ...], Entry: LayoutObject
) -> dict[int, tuple[int, ...]]:
    RawGated = Entry.get("element_by_version", {})
    if not IsLayoutObject(RawGated):
        raise ArchiveError(
            f"run group {NameValue}@{Label} has a malformed element_by_version"
        )
    Gated: dict[int, tuple[int, ...]] = {}
    for VersionA, Values in RawGated.items():
        TextValue = str(VersionA)
        if not TextValue.isdigit():
            raise ArchiveError(
                f"run group {NameValue}@{Label} names a non numeric document version {TextValue!r}"
            )
        if not IsLayoutSequence(Values):
            raise ArchiveError(
                f"run group {NameValue}@{Label} at document version {TextValue} has no element"
            )
        Widths = tuple((LayoutInteger(Value) for Value in Values))
        if len(Widths) != len(ElemValue) or any((Value < 0 for Value in Widths)):
            raise ArchiveError(
                f"run group {NameValue}@{Label} at document version {TextValue} does not hold {len(ElemValue)} non negative runs"
            )
        Gated[int(TextValue)] = Widths
    return Gated


# this definition exists because element variant lists require mapping entries exclusively
def GroupVariants(
    NameValue: str, Label: str, ElemValue: tuple[int, ...], Entry: LayoutObject
) -> list[RunGroupVariant]:
    RawVariants = Entry.get("element_run_variants", ())
    if not IsLayoutSequence(RawVariants):
        raise ArchiveError(
            f"run group {NameValue}@{Label} has malformed element_run_variants"
        )
    Variants: list[RunGroupVariant] = []
    for RawVariant in RawVariants:
        if not IsLayoutObject(RawVariant):
            raise ArchiveError(
                f"run group {NameValue}@{Label} has a malformed element run variant"
            )
        Variants.append(GroupVariant(NameValue, Label, ElemValue, RawVariant))
    return Variants


# this definition exists because one element run variant owns predicate and version validation
def GroupVariant(
    NameValue: str,
    Label: str,
    ElemValue: tuple[int, ...],
    RawVariant: LayoutObject,
) -> RunGroupVariant:
    SlotValue = LayoutInteger(RawVariant.get("slot", -1))
    PredicateAt = LayoutInteger(RawVariant.get("predicate_at", 0))
    PredicateWidth = LayoutInteger(RawVariant.get("predicate_width", 0))
    RawValues = RawVariant.get("values", ())
    RawChildClasses = RawVariant.get("child_classes", ())
    RawLast = RawVariant.get("last", False)
    RawStopGroups = RawVariant.get("stop_groups", False)
    RawVersions = RawVariant.get("versions", ())
    RunValue = LayoutInteger(RawVariant.get("run", -1))
    RawVersionRuns = RawVariant.get("runs_by_version", {})
    RawTrailer = RawVariant.get("trailer")
    Trailer = LayoutInteger(RawTrailer) if RawTrailer is not None else -1
    if (
        SlotValue < 0
        or SlotValue >= len(ElemValue)
        or PredicateAt < 0
        or isinstance(RawValues, str)
        or (not IsLayoutSequence(RawValues))
        or any(
            (
                not isinstance(Value, int) or isinstance(Value, bool) or Value < 0
                for Value in RawValues
            )
        )
        or isinstance(RawChildClasses, str)
        or (not IsLayoutSequence(RawChildClasses))
        or any(
            (
                not isinstance(ChildClass, str) or not ChildClass
                for ChildClass in RawChildClasses
            )
        )
        or (not isinstance(RawLast, bool))
        or (not isinstance(RawStopGroups, bool))
        or (not IsLayoutSequence(RawVersions))
        or any(
            (
                not isinstance(Version, int) or isinstance(Version, bool) or Version < 0
                for Version in RawVersions
            )
        )
        or (RunValue < 0)
        or (not IsLayoutObject(RawVersionRuns))
        or (Trailer < -1)
        or (not RawValues and (not RawChildClasses))
        or (RawValues and PredicateWidth not in (1, 2, 4, 8))
        or (not RawValues and PredicateWidth != 0)
    ):
        raise ArchiveError(
            f"run group {NameValue}@{Label} has a malformed element run variant"
        )
    VersionRuns = VariantRuns(NameValue, Label, RawVersionRuns)
    return RunGroupVariant(
        Slot=SlotValue,
        Last=RawLast,
        StopGroups=RawStopGroups,
        Versions=tuple((LayoutInteger(Version) for Version in RawVersions)),
        PredicateAt=PredicateAt,
        PredicateWidth=PredicateWidth,
        Values=tuple((LayoutInteger(Value) for Value in RawValues)),
        ChildClasses=tuple((str(ChildClass) for ChildClass in RawChildClasses)),
        Run=RunValue,
        RunsByVersion=VersionRuns,
        Trailer=Trailer,
    )


# this definition exists because version run overrides require numeric keys and widths
def VariantRuns(NameValue: str, Label: str, RawRuns: LayoutObject) -> dict[int, int]:
    VersionRuns: dict[int, int] = {}
    for Version, Width in RawRuns.items():
        VersionText = str(Version)
        if (
            not VersionText.isdigit()
            or not isinstance(Width, int)
            or isinstance(Width, bool)
            or (Width < 0)
        ):
            raise ArchiveError(
                f"run group {NameValue}@{Label} has a malformed versioned element run variant"
            )
        VersionRuns[int(VersionText)] = int(Width)
    return VersionRuns


# this definition exists because trailer variants share predicate and version validation
def GroupTrailers(
    NameValue: str, Label: str, Entry: LayoutObject
) -> list[RunGroupTrailer]:
    RawTrailerVariants = Entry.get("trailer_variants", ())
    if not IsLayoutSequence(RawTrailerVariants):
        raise ArchiveError(
            f"run group {NameValue}@{Label} has malformed trailer_variants"
        )
    TrailerVariants: list[RunGroupTrailer] = []
    for RawVariant in RawTrailerVariants:
        if not IsLayoutObject(RawVariant):
            raise ArchiveError(
                f"run group {NameValue}@{Label} has a malformed trailer variant"
            )
        RawVersions = RawVariant.get("versions", ())
        PredicateAt = RawVariant.get("predicate_at", 0)
        PredicateWidth = RawVariant.get("predicate_width", 0)
        RawValues = RawVariant.get("values", ())
        RawTrailer = RawVariant.get("trailer", -1)
        if (
            not IsLayoutSequence(RawVersions)
            or any(
                (
                    not isinstance(Version, int)
                    or isinstance(Version, bool)
                    or Version < 0
                    for Version in RawVersions
                )
            )
            or (not isinstance(PredicateAt, int))
            or isinstance(PredicateAt, bool)
            or (PredicateAt < 0)
            or (PredicateWidth not in (1, 2, 4, 8))
            or (not IsLayoutSequence(RawValues))
            or (not RawValues)
            or any(
                (
                    not isinstance(Value, int) or isinstance(Value, bool) or Value < 0
                    for Value in RawValues
                )
            )
            or (not isinstance(RawTrailer, int))
            or isinstance(RawTrailer, bool)
            or (RawTrailer < 0)
        ):
            raise ArchiveError(
                f"run group {NameValue}@{Label} has a malformed trailer variant"
            )
        TrailerVariants.append(
            RunGroupTrailer(
                Versions=tuple((LayoutInteger(Version) for Version in RawVersions)),
                PredicateAt=PredicateAt,
                PredicateWidth=PredicateWidth,
                Values=tuple((LayoutInteger(Value) for Value in RawValues)),
                Trailer=RawTrailer,
            )
        )
    return TrailerVariants


# this definition exists because count variants share predicate and version validation
def CountVariantsA(
    NameValue: str, Label: str, Entry: LayoutObject
) -> list[RunGroupCountA]:
    RawCountVariants = Entry.get("count_variants", ())
    if not IsLayoutSequence(RawCountVariants):
        raise ArchiveError(
            f"run group {NameValue}@{Label} has malformed count_variants"
        )
    CountVariants: list[RunGroupCountA] = []
    for RawVariant in RawCountVariants:
        if not IsLayoutObject(RawVariant):
            raise ArchiveError(
                f"run group {NameValue}@{Label} has a malformed count variant"
            )
        RawVersions = RawVariant.get("versions", ())
        PredicateAt = RawVariant.get("predicate_at", 0)
        PredicateWidth = RawVariant.get("predicate_width", 0)
        RawValues = RawVariant.get("values", ())
        RawCount = RawVariant.get("count", -1)
        RawLead = RawVariant.get("lead", 0)
        if (
            not IsLayoutSequence(RawVersions)
            or any(
                (
                    not isinstance(Version, int)
                    or isinstance(Version, bool)
                    or Version < 0
                    for Version in RawVersions
                )
            )
            or (not isinstance(PredicateAt, int))
            or isinstance(PredicateAt, bool)
            or (PredicateAt < 0)
            or (PredicateWidth not in (1, 2, 4, 8))
            or (not IsLayoutSequence(RawValues))
            or (not RawValues)
            or any(
                (
                    not isinstance(Value, int) or isinstance(Value, bool) or Value < 0
                    for Value in RawValues
                )
            )
            or (not isinstance(RawCount, int))
            or isinstance(RawCount, bool)
            or (RawCount < 0)
            or (not isinstance(RawLead, int))
            or isinstance(RawLead, bool)
            or (RawLead < 0)
        ):
            raise ArchiveError(
                f"run group {NameValue}@{Label} has a malformed count variant"
            )
        CountVariants.append(
            RunGroupCountA(
                Versions=tuple((LayoutInteger(Version) for Version in RawVersions)),
                PredicateAt=PredicateAt,
                PredicateWidth=PredicateWidth,
                Values=tuple((LayoutInteger(Value) for Value in RawValues)),
                Count=RawCount,
                Lead=RawLead,
            )
        )
    return CountVariants


# this definition exists because child class count branches share locator parsing
def CountBranchesA(
    NameValue: str, Label: str, Entry: LayoutObject
) -> dict[str, RunGroupCount]:
    RawCountBranches = Entry.get("count_by_child_class", {})
    if not IsLayoutObject(RawCountBranches):
        raise ArchiveError(
            f"run group {NameValue}@{Label} has malformed count_by_child_class"
        )
    CountBranches: dict[str, RunGroupCount] = {}
    for ChildClass, RawBranch in RawCountBranches.items():
        if not str(ChildClass) or not IsLayoutObject(RawBranch):
            raise ArchiveError(
                f"run group {NameValue}@{Label} has a malformed count branch"
            )
        CountBranches[str(ChildClass)] = ParseRunGroup(
            NameValue, Label, RawBranch, True
        )
    return CountBranches


# this definition exists because repeat and counted groups require mutually exclusive construction
def FinalRunGroup(
    NameValue: str,
    Label: str,
    ElemValue: tuple[int, ...],
    Slots: tuple[str, ...],
    TrailerA: int,
    Gated: dict[int, tuple[int, ...]],
    Variants: list[RunGroupVariant],
    TrailerVariants: list[RunGroupTrailer],
    CountVariants: list[RunGroupCountA],
    CountBranches: dict[str, RunGroupCount],
    Entry: LayoutObject,
) -> RunGroup:
    RawCountA = Entry.get("count")
    RawRepeat = Entry.get("repeat")
    if RawCountA is None and RawRepeat is None:
        raise ArchiveError(
            f"run group {NameValue}@{Label} has neither a count nor a repeat"
        )
    if RawCountA is not None and RawRepeat is not None:
        raise ArchiveError(
            f"run group {NameValue}@{Label} has both a count and a repeat"
        )
    NoteValue = str(Entry.get("note", ""))
    if RawRepeat is not None:
        if CountBranches or CountVariants:
            raise ArchiveError(
                f"run group {NameValue}@{Label} repeats a constant and cannot branch its count"
            )
        if (
            not isinstance(RawRepeat, int)
            or isinstance(RawRepeat, bool)
            or RawRepeat < 1
        ):
            raise ArchiveError(
                f"run group {NameValue}@{Label} has a repeat that is not a positive integer"
            )
        return RunGroup(
            name=Label,
            repeat=int(RawRepeat),
            count_back=0,
            count_width=0,
            CountByChildClass={},
            CountVariants=(),
            slots=Slots,
            element=ElemValue,
            element_by_version=Gated,
            ElementRunVariants=tuple(Variants),
            trailer=TrailerA,
            TrailerVariants=tuple(TrailerVariants),
            note=NoteValue,
        )
    if not IsLayoutObject(RawCountA):
        raise ArchiveError(f"run group {NameValue}@{Label} has a malformed count")
    Count = ParseRunGroup(NameValue, Label, RawCountA, False)
    if not Count.Back:
        raise ArchiveError(
            f"run group {NameValue}@{Label} has a forward default count without a lead"
        )
    return RunGroup(
        name=Label,
        repeat=-1,
        count_back=Count.Back,
        count_width=Count.Width,
        CountByChildClass=CountBranches,
        CountVariants=tuple(CountVariants),
        slots=Slots,
        element=ElemValue,
        element_by_version=Gated,
        ElementRunVariants=tuple(Variants),
        trailer=TrailerA,
        TrailerVariants=tuple(TrailerVariants),
        note=NoteValue,
    )


# this definition exists because focused behavior needs one stable owner
def ClassLayoutA(NameValue: str, Entry: LayoutObject) -> ClassLayout:
    Slots = LayoutSlots(NameValue, Entry)
    RunsValue = LayoutRunsA(NameValue, Entry)
    Gated = VersionedRuns(NameValue, Entry)
    ChildRuns = ChildClassRuns(NameValue, Entry)
    Variable = VariableRunsA(NameValue, Entry)
    RawRepeat = Entry.get("repeat_count")
    Repeat = RepeatRule(NameValue, Slots, RawRepeat)
    Unresolved = (KRepeatedSlot in Slots or RawRepeat is not None) and Repeat is None
    Prefix, RepeatTrailer = RepeatSettings(NameValue, Slots, Entry, Repeat, Unresolved)
    ChildCounts = ChildCountRule(NameValue, Slots, Entry, Repeat, Unresolved, Prefix)
    Groups = GroupRules(
        NameValue, Slots, Entry, Repeat, Unresolved, Prefix, RunsValue, Gated
    )
    return ClassLayout(
        name=NameValue,
        child_slots=Slots,
        runs=RunsValue,
        variable_runs={KeyValue: tuple(Value) for KeyValue, Value in Variable.items()},
        confidence=str(Entry.get("confidence", "partial")),
        source=str(Entry.get("source", "")),
        repeat_note=str(Entry.get("repeat_note", "")),
        repeat_count=Repeat,
        repeat_unresolved=Unresolved,
        repeat_prefix=Prefix,
        RepeatTrailer=RepeatTrailer,
        ChildCounts=ChildCounts,
        runs_by_version=Gated,
        RunsByChildClass=ChildRuns,
        groups=Groups,
    )


# this definition exists because child slot parsing has one sequence validation boundary
def LayoutSlots(NameValue: str, Entry: LayoutObject) -> tuple[str, ...]:
    RawSlots = Entry.get("child_slots", ())
    if not IsLayoutSequence(RawSlots):
        raise ArchiveError(
            f"layout entry for {NameValue!r} has a malformed child_slots"
        )
    return tuple((str(SlotValue) for SlotValue in RawSlots))


# this definition exists because constant layout runs require non negative integer widths
def LayoutRunsA(NameValue: str, Entry: LayoutObject) -> dict[str, int]:
    RawRuns = Entry.get("runs", {})
    if not IsLayoutObject(RawRuns):
        raise ArchiveError(
            f"layout entry for {NameValue!r} has a malformed runs mapping"
        )
    RunsValue: dict[str, int] = {}
    for KeyValue, Value in RawRuns.items():
        if not isinstance(Value, int) or isinstance(Value, bool) or Value < 0:
            raise ArchiveError(
                f"run {NameValue}@{KeyValue} is not a non negative integer"
            )
        RunsValue[str(KeyValue)] = LayoutInteger(Value)
    return RunsValue


# this definition exists because versioned layout runs require numeric version mappings
def VersionedRuns(NameValue: str, Entry: LayoutObject) -> dict[str, Mapping[int, int]]:
    RawGated = Entry.get("runs_by_version", {})
    if not IsLayoutObject(RawGated):
        raise ArchiveError(
            f"layout entry for {NameValue!r} has a malformed runs_by_version"
        )
    Gated: dict[str, Mapping[int, int]] = {}
    for KeyValue, RawMapping in RawGated.items():
        if not IsLayoutObject(RawMapping):
            raise ArchiveError(
                f"runs_by_version {NameValue}@{KeyValue} does not hold a version mapping"
            )
        ByVersion: dict[int, int] = {}
        for Version, Value in RawMapping.items():
            TextValue = str(Version)
            if not TextValue.isdigit():
                raise ArchiveError(
                    f"runs_by_version {NameValue}@{KeyValue} names a non numeric document version {TextValue!r}"
                )
            if not isinstance(Value, int) or isinstance(Value, bool) or Value < 0:
                raise ArchiveError(
                    f"run {NameValue}@{KeyValue} at document version {TextValue} is not a non negative integer"
                )
            ByVersion[int(TextValue)] = LayoutInteger(Value)
        if not ByVersion:
            raise ArchiveError(
                f"runs_by_version {NameValue}@{KeyValue} names no version"
            )
        Gated[str(KeyValue)] = ByVersion
    return Gated


# this definition exists because child class run branches require complete class mappings
def ChildClassRuns(NameValue: str, Entry: LayoutObject) -> dict[str, Mapping[str, int]]:
    RawChildRuns = Entry.get("runs_by_child_class", {})
    if not IsLayoutObject(RawChildRuns):
        raise ArchiveError(
            f"layout entry for {NameValue!r} has malformed runs_by_child_class"
        )
    ChildRuns: dict[str, Mapping[str, int]] = {}
    for RunKey, RawClassRuns in RawChildRuns.items():
        if not IsLayoutObject(RawClassRuns) or not RawClassRuns:
            raise ArchiveError(
                f"runs_by_child_class {NameValue}@{RunKey} has no class mapping"
            )
        ClassRuns: dict[str, int] = {}
        for ChildClass, RunValue in RawClassRuns.items():
            if (
                not str(ChildClass)
                or not isinstance(RunValue, int)
                or isinstance(RunValue, bool)
                or (RunValue < 0)
            ):
                raise ArchiveError(
                    f"run {NameValue}@{RunKey} for child {ChildClass!r} is malformed"
                )
            ClassRuns[str(ChildClass)] = LayoutInteger(RunValue)
        ChildRuns[str(RunKey)] = ClassRuns
    return ChildRuns


# this definition exists because variable run lists group validated entries by slot
def VariableRunsA(NameValue: str, Entry: LayoutObject) -> dict[str, list[VariableRun]]:
    RawVariable = Entry.get("variable_runs", ())
    if not IsLayoutSequence(RawVariable):
        raise ArchiveError(
            f"layout entry for {NameValue!r} has a malformed variable_runs"
        )
    Variable: dict[str, list[VariableRun]] = {}
    for ItemValue in RawVariable:
        if not IsLayoutObject(ItemValue):
            raise ArchiveError(f"variable run of {NameValue!r} is not a mapping")
        SlotValue, Parsed = VariableEntry(NameValue, ItemValue)
        Variable.setdefault(SlotValue, []).append(Parsed)
    return Variable


# this definition exists because one variable run owns its value and version gates
def VariableEntry(NameValue: str, ItemValue: LayoutObject) -> tuple[str, VariableRun]:
    SlotValue = str(ItemValue.get("slot", ""))
    RawValues = ItemValue.get("values", ())
    if not IsLayoutSequence(RawValues):
        raise ArchiveError(f"variable run {NameValue}@{SlotValue} has malformed values")
    RawTailGate = ItemValue.get("tail_by_version", {})
    if not IsLayoutObject(RawTailGate):
        raise ArchiveError(
            f"variable run {NameValue}@{SlotValue} has malformed tail_by_version"
        )
    TailGate: dict[int, int] = {}
    for VersionText, TailValue in RawTailGate.items():
        VersionName = str(VersionText)
        if not VersionName.isdigit():
            raise ArchiveError(
                f"variable run {NameValue}@{SlotValue} names a non numeric tail version {VersionName!r}"
            )
        if (
            not isinstance(TailValue, int)
            or isinstance(TailValue, bool)
            or TailValue < 0
        ):
            raise ArchiveError(
                f"variable run {NameValue}@{SlotValue} has an invalid tail for document version {VersionName}"
            )
        TailGate[int(VersionName)] = LayoutInteger(TailValue)
    Parsed = VariableRun(
        slot=SlotValue,
        rule=str(ItemValue.get("rule", KOpaqueRule)),
        at=LayoutInteger(ItemValue.get("at", 0) or 0),
        tail=LayoutInteger(ItemValue.get("tail", 0) or 0),
        TailByVersion=TailGate,
        stride=LayoutInteger(ItemValue.get("stride", 0) or 0),
        count_width=LayoutInteger(ItemValue.get("count_width", 0) or 0),
        width=LayoutInteger(ItemValue.get("width", 0) or 0),
        predicate=str(ItemValue.get("predicate", "")),
        predicate_at=LayoutInteger(ItemValue.get("predicate_at", 0) or 0),
        predicate_width=LayoutInteger(ItemValue.get("predicate_width", 0) or 0),
        values=tuple((LayoutInteger(Value) for Value in RawValues)),
        note=str(ItemValue.get("note", "")),
    )
    return (SlotValue, Parsed)


# this definition exists because repeat count locators require mutually exclusive offsets
def RepeatRule(
    NameValue: str, Slots: tuple[str, ...], RawRepeat: object
) -> RepeatField | None:
    if not IsLayoutObject(RawRepeat) or KRepeatedSlot not in Slots:
        return None
    RunValueA = str(RawRepeat.get("run", ""))
    RawAt = RawRepeat.get("at")
    RawBack = RawRepeat.get("back")
    HasAt = RawAt is not None
    HasBack = RawBack is not None
    AtValue = LayoutInteger(RawAt) if HasAt else 0
    BackValue = LayoutInteger(RawBack) if HasBack else 0
    Width = LayoutInteger(RawRepeat.get("width", 0))
    if (
        not RunValueA
        or HasAt == HasBack
        or AtValue < 0
        or (BackValue < 0)
        or (Width not in (1, 2, 4))
        or (HasBack and BackValue < Width)
    ):
        raise ArchiveError(f"repeat_count of {NameValue!r} is malformed")
    if len(Slots) < 2:
        raise ArchiveError(f"repeat_count of {NameValue!r} has no template slot")
    return RepeatField(run=RunValueA, at=AtValue, Back=BackValue, width=Width)


# this definition exists because repeat prefix and trailer rules depend on resolution state
def RepeatSettings(
    NameValue: str,
    Slots: tuple[str, ...],
    Entry: LayoutObject,
    Repeat: RepeatField | None,
    Unresolved: bool,
) -> tuple[int, int]:
    RawPrefix = Entry.get("repeat_prefix", 0)
    if not isinstance(RawPrefix, int) or isinstance(RawPrefix, bool) or RawPrefix < 0:
        raise ArchiveError(
            f"repeat_prefix of {NameValue!r} is not a non negative integer"
        )
    Prefix = int(RawPrefix)
    if Prefix and (not Unresolved):
        raise ArchiveError(
            f"repeat_prefix of {NameValue!r} names a prefix for a class whose child count is already resolved"
        )
    if Prefix > len(Slots):
        raise ArchiveError(
            f"repeat_prefix {Prefix} of {NameValue!r} exceeds its {len(Slots)} child slots"
        )
    RepeatTrailer = Entry.get("repeat_trailer", 0)
    if (
        not isinstance(RepeatTrailer, int)
        or isinstance(RepeatTrailer, bool)
        or RepeatTrailer < 0
    ):
        raise ArchiveError(
            f"repeat_trailer of {NameValue!r} is not a non negative integer"
        )
    if RepeatTrailer and Repeat is None:
        raise ArchiveError(
            f"repeat_trailer of {NameValue!r} has no resolved repeat_count"
        )
    return (Prefix, RepeatTrailer)


# this definition exists because child count branches must not conflict with repeat rules
def ChildCountRule(
    NameValue: str,
    Slots: tuple[str, ...],
    Entry: LayoutObject,
    Repeat: RepeatField | None,
    Unresolved: bool,
    Prefix: int,
) -> ChildCountBy | None:
    RawChildCounts = Entry.get("child_count_by_class")
    if RawChildCounts is None:
        return None
    if not IsLayoutObject(RawChildCounts):
        raise ArchiveError(f"child_count_by_class of {NameValue!r} is malformed")
    RawCountSlot = RawChildCounts.get("slot")
    RawCounts = RawChildCounts.get("counts")
    if (
        not isinstance(RawCountSlot, int)
        or isinstance(RawCountSlot, bool)
        or (not IsLayoutObject(RawCounts))
    ):
        raise ArchiveError(f"child_count_by_class of {NameValue!r} is malformed")
    CountSlot = LayoutInteger(RawCountSlot)
    Counts: dict[str, int] = {}
    for ClassName, CountValue in RawCounts.items():
        if (
            not str(ClassName)
            or not isinstance(CountValue, int)
            or isinstance(CountValue, bool)
            or (CountValue <= CountSlot)
            or (CountValue > len(Slots))
        ):
            raise ArchiveError(
                f"child count branch {NameValue}@{ClassName} is malformed"
            )
        Counts[str(ClassName)] = LayoutInteger(CountValue)
    if CountSlot < 0 or CountSlot >= len(Slots) or (not Counts):
        raise ArchiveError(f"child_count_by_class of {NameValue!r} is malformed")
    if Repeat is not None or Unresolved or Prefix:
        raise ArchiveError(
            f"child_count_by_class of {NameValue!r} conflicts with a repeat rule"
        )
    return ChildCountBy(Slot=CountSlot, Counts=Counts)


# this definition exists because grouped child walks must remain exclusive from slot rules
def GroupRules(
    NameValue: str,
    Slots: tuple[str, ...],
    Entry: LayoutObject,
    Repeat: RepeatField | None,
    Unresolved: bool,
    Prefix: int,
    RunsValue: dict[str, int],
    Gated: dict[str, Mapping[int, int]],
) -> tuple[RunGroup, ...]:
    RawGroups = Entry.get("groups", ())
    if not IsLayoutSequence(RawGroups):
        raise ArchiveError(
            f"layout entry for {NameValue!r} has a malformed groups list"
        )
    Parsed: list[RunGroup] = []
    for ItemValue in RawGroups:
        if not IsLayoutObject(ItemValue):
            raise ArchiveError(f"a run group of {NameValue!r} is not a mapping")
        Parsed.append(RunGroupA(NameValue, ItemValue))
    Groups = tuple(Parsed)
    if Groups and (Slots or Repeat is not None or Unresolved or Prefix):
        raise ArchiveError(
            f"layout entry for {NameValue!r} drives its children from run groups and must not also declare child slots"
        )
    if Groups and KLeadRun not in RunsValue and (KLeadRun not in Gated):
        raise ArchiveError(
            f"layout entry for {NameValue!r} has run groups but no lead run"
        )
    return Groups


# this definition exists because focused behavior needs one stable owner
@Dataclass(slots=True)
class Frame:
    node: int
    class_name: str
    layout: ClassLayout
    slot: int
    total: int
    group: int = 0
    step: int = 0
    plan: tuple[int, ...] = ()
    key: str = KLeadRun
    ChildClass: str = ""


# this definition exists because focused behavior needs one stable owner
def Scalar(BlobValue: bytes, Offset: int, Width: int) -> int:
    if Width not in (1, 2, 4, 8):
        raise ArchiveError(f"unsupported scalar width {Width}")
    if Offset < 0 or Offset + Width > len(BlobValue):
        raise ArchiveError(
            f"{Width} byte field at offset {Offset} runs past the end of the stream"
        )
    return int.from_bytes(BlobValue[Offset : Offset + Width], "little")


# this definition exists because focused behavior needs one stable owner
def ElemLength(
    BlobValue: bytes,
    Cursor: int,
    Layout: ClassLayout,
    KeyValue: str,
    Offset: int,
    BaseValue: int,
    ElemValue: VariableRun,
    MoVersion: int | None,
) -> int:
    TailValue = ElemValue.tail
    if MoVersion is not None:
        TailValue = ElemValue.TailByVersion.get(MoVersion, TailValue)
    if ElemValue.rule == KStringRule:
        return StringElem(
            BlobValue, Cursor, Layout, KeyValue, Offset, BaseValue, ElemValue, TailValue
        )
    if ElemValue.rule == KCountRule:
        return CountElem(
            BlobValue, Cursor, Layout, KeyValue, Offset, BaseValue, ElemValue, TailValue
        )
    if ElemValue.rule == KConditionalRule:
        return ConditionalElem(
            BlobValue, Cursor, Layout, KeyValue, Offset, BaseValue, ElemValue, TailValue
        )
    if ElemValue.rule == KGuardRule:
        return GuardElem(
            BlobValue, Cursor, Layout, KeyValue, Offset, BaseValue, ElemValue, TailValue
        )
    raise Segmentation(
        Layout.name,
        KeyValue,
        Offset,
        f"run rule {ElemValue.rule!r} cannot be resolved statically"
        + (f" ({ElemValue.note})" if ElemValue.note else ""),
        BaseValue=BaseValue,
    )


# this definition exists because encoded string runs translate parser failures into segmentation context
def StringElem(
    BlobValue: bytes,
    Cursor: int,
    Layout: ClassLayout,
    KeyValue: str,
    Offset: int,
    BaseValue: int,
    ElemValue: VariableRun,
    TailValue: int,
) -> int:
    try:
        _, Consumed = ReadString(BlobValue, Cursor + ElemValue.at)
    except ArchiveError as ErrorInfo:
        raise Segmentation(
            Layout.name, KeyValue, Offset, str(ErrorInfo), BaseValue=BaseValue
        ) from ErrorInfo
    return ElemValue.at + Consumed + TailValue


# this definition exists because counted runs validate width before applying their stride
def CountElem(
    BlobValue: bytes,
    Cursor: int,
    Layout: ClassLayout,
    KeyValue: str,
    Offset: int,
    BaseValue: int,
    ElemValue: VariableRun,
    TailValue: int,
) -> int:
    if ElemValue.count_width <= 0 or ElemValue.stride < 0:
        raise Segmentation(
            Layout.name,
            KeyValue,
            Offset,
            "count rule is missing a count width or stride",
            BaseValue=BaseValue,
        )
    try:
        Count = Scalar(BlobValue, Cursor + ElemValue.at, ElemValue.count_width)
    except ArchiveError as ErrorInfo:
        raise Segmentation(
            Layout.name, KeyValue, Offset, str(ErrorInfo), BaseValue=BaseValue
        ) from ErrorInfo
    return ElemValue.at + ElemValue.count_width + ElemValue.stride * Count + TailValue


# this definition exists because conditional runs select their payload from one scalar predicate
def ConditionalElem(
    BlobValue: bytes,
    Cursor: int,
    Layout: ClassLayout,
    KeyValue: str,
    Offset: int,
    BaseValue: int,
    ElemValue: VariableRun,
    TailValue: int,
) -> int:
    if ElemValue.predicate_width <= 0 or not ElemValue.values:
        raise Segmentation(
            Layout.name,
            KeyValue,
            Offset,
            "conditional rule is missing a predicate width or value set",
            BaseValue=BaseValue,
        )
    try:
        Value = Scalar(
            BlobValue, Cursor + ElemValue.predicate_at, ElemValue.predicate_width
        )
    except ArchiveError as ErrorInfo:
        raise Segmentation(
            Layout.name, KeyValue, Offset, str(ErrorInfo), BaseValue=BaseValue
        ) from ErrorInfo
    Present = ElemValue.width if Value in ElemValue.values else 0
    return ElemValue.at + Present + TailValue


# this definition exists because guarded runs reject unexpected scalar predicate values explicitly
def GuardElem(
    BlobValue: bytes,
    Cursor: int,
    Layout: ClassLayout,
    KeyValue: str,
    Offset: int,
    BaseValue: int,
    ElemValue: VariableRun,
    TailValue: int,
) -> int:
    if ElemValue.predicate_width <= 0 or not ElemValue.values:
        raise Segmentation(
            Layout.name,
            KeyValue,
            Offset,
            "guard rule is missing a predicate width or value set",
            BaseValue=BaseValue,
        )
    try:
        Value = Scalar(
            BlobValue, Cursor + ElemValue.predicate_at, ElemValue.predicate_width
        )
    except ArchiveError as ErrorInfo:
        raise Segmentation(
            Layout.name, KeyValue, Offset, str(ErrorInfo), BaseValue=BaseValue
        ) from ErrorInfo
    if Value not in ElemValue.values:
        raise Segmentation(
            Layout.name,
            KeyValue,
            Offset,
            f"guard predicate {ElemValue.predicate!r} rejected value {Value}",
            BaseValue=BaseValue,
        )
    return ElemValue.at + TailValue


# this definition exists because focused behavior needs one stable owner
def RunLength(
    BlobValue: bytes,
    Cursor: int,
    Layout: ClassLayout,
    KeyValue: str,
    Offset: int,
    BaseValue: int,
    MoVersion: int | None,
    ChildClass: str = "",
) -> int:
    ClassRuns = Layout.RunsByChildClass.get(KeyValue)
    if ClassRuns is not None:
        ClassLength = ClassRuns.get(ChildClass)
        if ClassLength is None:
            raise Segmentation(
                Layout.name,
                KeyValue,
                Offset,
                f"run branch has no case for child class {ChildClass!r}",
                BaseValue=BaseValue,
            )
        return ClassLength
    Constant = Layout.constant_run(KeyValue, MoVersion)
    if Constant is not None:
        return Constant
    Elements = Layout.variable_runs.get(KeyValue)
    if not Elements:
        Reason = "no constant run length and no rule recorded in the layout table"
        if KeyValue in Layout.runs_by_version:
            Reason += (
                f" for document version {MoVersion}"
                if MoVersion is not None
                else " and no document version was supplied"
            )
        raise Segmentation(Layout.name, KeyValue, Offset, Reason, BaseValue=BaseValue)
    Length = 0
    for ElemValue in Elements:
        Length += ElemLength(
            BlobValue,
            Cursor + Length,
            Layout,
            KeyValue,
            Offset,
            BaseValue,
            ElemValue,
            MoVersion,
        )
    return Length


# this definition exists because focused behavior needs one stable owner
def RepeatTotal(
    BlobValue: bytes,
    RunStart: int,
    RunEnd: int,
    Layout: ClassLayout,
    Offset: int,
    BaseValue: int,
) -> int:
    Repeat = Layout.repeat_count
    if Repeat is None:
        raise Segmentation(
            Layout.name,
            KLeadRun,
            Offset,
            "a repeated child count was requested without a repeat_count rule",
            BaseValue=BaseValue,
        )
    try:
        CountAt = RunEnd - Repeat.Back if Repeat.Back else RunStart + Repeat.at
        Count = Scalar(BlobValue, CountAt, Repeat.width)
    except ArchiveError as ErrorInfo:
        raise Segmentation(
            Layout.name, Repeat.run, Offset, str(ErrorInfo), BaseValue=BaseValue
        ) from ErrorInfo
    Template = Layout.template_slot
    if Count < 0 or Template < 0:
        raise Segmentation(
            Layout.name,
            Repeat.run,
            Offset,
            f"repeated child count {Count} is not usable",
            BaseValue=BaseValue,
        )
    return Template + Count


# this definition exists because focused behavior needs one stable owner
def Advance(
    BlobValue: bytes,
    Cursor: int,
    Amount: int,
    Layout: ClassLayout,
    KeyValue: str,
    Offset: int,
    BaseValue: int,
) -> int:
    EndValue = Cursor + Amount
    if EndValue > len(BlobValue):
        raise Segmentation(
            Layout.name,
            KeyValue,
            Offset,
            f"run of {Amount} bytes at {Cursor} runs past the {len(BlobValue)} byte stream",
            BaseValue=BaseValue,
        )
    return EndValue


# this definition exists because focused behavior needs one stable owner
def GroupElemLength(
    BlobValue: bytes,
    Cursor: int,
    Frame: _Frame,
    Offset: int,
    BaseValue: int,
    MoVersion: int | None,
) -> tuple[int, int | None, bool]:
    Group = Frame.layout.groups[Frame.group - 1]
    SlotValue = Frame.step % len(Group.element)
    for Variant in Group.ElementRunVariants:
        if Variant.Slot != SlotValue:
            continue
        if Variant.Last and Frame.step + 1 != len(Frame.plan):
            continue
        if Variant.Versions and MoVersion not in Variant.Versions:
            continue
        if Variant.ChildClasses and Frame.ChildClass not in Variant.ChildClasses:
            continue
        MatchesPredicate = not Variant.Values
        if Variant.Values:
            try:
                Value = Scalar(
                    BlobValue, Cursor + Variant.PredicateAt, Variant.PredicateWidth
                )
            except ArchiveError as ErrorInfo:
                raise Segmentation(
                    Frame.layout.name,
                    Group.name,
                    Offset,
                    str(ErrorInfo),
                    BaseValue=BaseValue,
                ) from ErrorInfo
            MatchesPredicate = Value in Variant.Values
        if MatchesPredicate:
            Length = Variant.Run
            if MoVersion is not None:
                Length = Variant.RunsByVersion.get(MoVersion, Length)
            Trailer = Variant.Trailer if Variant.Trailer >= 0 else None
            return (Length, Trailer, Variant.StopGroups)
    return (Frame.plan[Frame.step], None, False)


# this definition exists because focused behavior needs one stable owner
def GroupTrailer(
    BlobValue: bytes,
    Cursor: int,
    Layout: ClassLayout,
    Group: RunGroup,
    Offset: int,
    BaseValue: int,
    MoVersion: int | None,
) -> int:
    for Variant in Group.TrailerVariants:
        if Variant.Versions and MoVersion not in Variant.Versions:
            continue
        try:
            Value = Scalar(
                BlobValue, Cursor + Variant.PredicateAt, Variant.PredicateWidth
            )
        except ArchiveError as ErrorInfo:
            raise Segmentation(
                Layout.name, Group.name, Offset, str(ErrorInfo), BaseValue=BaseValue
            ) from ErrorInfo
        if Value in Variant.Values:
            return Variant.Trailer
    return Group.trailer


# this definition exists because focused behavior needs one stable owner
def GetTailSize(BlobValue: bytes, BaseValue: int, HeaderSize: int) -> int:
    if HeaderSize != KStreamHeaderSize or len(BlobValue) < HeaderSize + KStreamTailSize:
        return 0
    if int.from_bytes(BlobValue[:4], "little") != BaseValue:
        return 0
    if BlobValue[-KStreamTailSize:] != bytes(KStreamTailSize):
        return 0
    return KStreamTailSize


# this definition exists because focused behavior needs one stable owner
def GroupOpenMut(
    BlobValue: bytes,
    Cursor: int,
    Frame: _Frame,
    Offset: int,
    BaseValue: int,
    MoVersion: int | None,
) -> tuple[int, bool]:
    Layout = Frame.layout
    while Frame.group < len(Layout.groups):
        Group = Layout.groups[Frame.group]
        setattr(Frame, "group", Frame.group + 1)
        setattr(Frame, "key", Group.name)
        Count, GroupLead = GroupCount(
            BlobValue, Cursor, Frame, Group, Offset, BaseValue, MoVersion
        )
        if Count:
            Cursor = Advance(
                BlobValue, Cursor, GroupLead, Layout, Group.name, Offset, BaseValue
            )
            setattr(Frame, "plan", tuple(Group.element_runs(MoVersion) * Count))
            setattr(Frame, "step", 0)
            return (Cursor, True)
        Trailer = GroupTrailer(
            BlobValue, Cursor, Layout, Group, Offset, BaseValue, MoVersion
        )
        Cursor = Advance(
            BlobValue, Cursor, Trailer, Layout, Group.name, Offset, BaseValue
        )
    if KTailRun in Layout.constant_run_keys or KTailRun in Layout.variable_runs:
        Amount = RunLength(
            BlobValue, Cursor, Layout, KTailRun, Offset, BaseValue, MoVersion
        )
        Cursor = Advance(BlobValue, Cursor, Amount, Layout, KTailRun, Offset, BaseValue)
    return (Cursor, False)


# this definition exists because group count resolution combines variants and child class branches
def GroupCount(
    BlobValue: bytes,
    Cursor: int,
    Frame: Frame,
    Group: RunGroup,
    Offset: int,
    BaseValue: int,
    MoVersion: int | None,
) -> tuple[int, int]:
    if Group.repeat >= 0:
        return (Group.repeat, 0)
    Count = -1
    GroupLead = 0
    for CountVariant in Group.CountVariants:
        if CountVariant.Versions and MoVersion not in CountVariant.Versions:
            continue
        try:
            Predicate = Scalar(
                BlobValue,
                Cursor + CountVariant.PredicateAt,
                CountVariant.PredicateWidth,
            )
        except ArchiveError as ErrorInfo:
            raise Segmentation(
                Frame.layout.name,
                Group.name,
                Offset,
                str(ErrorInfo),
                BaseValue=BaseValue,
            ) from ErrorInfo
        if Predicate in CountVariant.Values:
            Count = CountVariant.Count
            GroupLead = CountVariant.Lead
            break
    if Count >= 0:
        return (Count, GroupLead)
    CountBranch = Group.CountByChildClass.get(Frame.ChildClass)
    CountAt = Cursor - Group.count_back
    CountWidth = Group.count_width
    if CountBranch is not None:
        CountAt = (
            Cursor - CountBranch.Back if CountBranch.Back else Cursor + CountBranch.At
        )
        CountWidth = CountBranch.Width
        GroupLead = CountBranch.Lead
    try:
        return (Scalar(BlobValue, CountAt, CountWidth), GroupLead)
    except ArchiveError as ErrorInfo:
        raise Segmentation(
            Frame.layout.name, Group.name, Offset, str(ErrorInfo), BaseValue=BaseValue
        ) from ErrorInfo


# this definition exists because focused behavior needs one stable owner
def DeclaredSlot(Layouts: LayoutTable, Frames: Sequence[_Frame]) -> str:
    if not Frames:
        return ""
    Frame = Frames[-1]
    Layout = Frame.layout
    if Layout.groups:
        Group = Layout.groups[Frame.group - 1]
        Declared = Group.slots[Frame.step % len(Group.slots)]
        if Declared in (KPolymorphicSlot, KRepeatedSlot) or Declared not in Layouts:
            return ""
        return Declared
    Slots = Layout.child_slots
    SlotValue = Frame.slot
    if Layout.repeat_count is not None and SlotValue >= Layout.template_slot:
        SlotValue = Layout.template_slot
    if SlotValue < 0 or SlotValue >= len(Slots):
        return ""
    Declared = Slots[SlotValue]
    if Declared in (KPolymorphicSlot, KRepeatedSlot):
        return ""
    if Declared not in Layouts:
        return ""
    return Declared


# this definition exists because focused behavior needs one stable owner
def OuterName(ClassIndex: int, Layouts: LayoutTable, Frames: Sequence[_Frame]) -> str:
    Alias = f"{KOuterPrefix}{ClassIndex}"
    if Alias in Layouts:
        return Alias
    return DeclaredSlot(Layouts, Frames) or Alias


# this definition exists because focused behavior needs one stable owner
def SegmentWalkMut(
    BlobValue: bytes,
    BaseValue: int,
    Layouts: LayoutTable,
    HeaderSize: int,
    Segments: list[StaticSegment],
    Progress: list[int],
    MoVersion: int | None,
) -> tuple[StaticSegment, ...]:
    ContentEnd = WalkBounds(BlobValue, BaseValue, HeaderSize)
    Frames: list[Frame] = []
    ClassNames: dict[int, str] = {}
    ObjectOwner: dict[int, str] = {}
    Counter = BaseValue
    Cursor = HeaderSize
    while True:
        if not Frames and Cursor == ContentEnd:
            break
        Offset, Parent, ParentName, ParentSlot, TagValue = WalkHeaderMut(
            BlobValue, BaseValue, Cursor, Frames, Segments, Progress
        )
        ClassIndex, ObjectIndex, NameValue, Counter = ResolveTagMut(
            TagValue,
            Counter,
            BaseValue,
            Layouts,
            Frames,
            ClassNames,
            ObjectOwner,
            ParentName,
            ParentSlot,
            Offset,
        )
        Cursor = Offset + TagValue.size
        if Cursor > len(BlobValue):
            raise Segmentation(
                ParentName,
                ParentSlot,
                Offset,
                f"tag of {TagValue.size} bytes runs past the {len(BlobValue)} byte stream",
                BaseValue=BaseValue,
            )
        NodeValue = len(Segments)
        Depth = len(Frames)
        if Frames:
            Frames[-1].ChildClass = NameValue
        Cursor, Pushed = OpenNodeMut(
            BlobValue,
            BaseValue,
            Layouts,
            Frames,
            TagValue,
            NameValue,
            NodeValue,
            Offset,
            Cursor,
            MoVersion,
        )
        Segments.append(
            StaticSegment(
                index=NodeValue,
                offset=Offset,
                header=TagValue.size,
                end=Cursor,
                kind=TagValue.kind,
                token=TagValue.token,
                wide=TagValue.wide,
                schema=TagValue.schema,
                class_name=NameValue,
                class_index=ClassIndex,
                object_index=ObjectIndex,
                depth=Depth,
                parent=Parent,
            )
        )
        if Pushed:
            continue
        Cursor = CloseNodeMut(BlobValue, BaseValue, Frames, Segments, Cursor, MoVersion)
        setattr(Segments[NodeValue], "end", Cursor)
        if not Frames and Cursor > ContentEnd:
            raise Segmentation(
                "<stream>",
                KLeadRun,
                Offset,
                f"segmentation overran the {ContentEnd} byte object region",
                BaseValue=BaseValue,
            )
    return FinishWalkMut(BaseValue, Frames, Segments, Progress)


# this definition exists because walk bounds validate the header before traversal state begins
def WalkBounds(BlobValue: bytes, BaseValue: int, HeaderSize: int) -> int:
    if BaseValue < 1:
        raise ArchiveError(f"archive map base {BaseValue} must be positive")
    if HeaderSize < 0 or HeaderSize > len(BlobValue):
        raise ArchiveError(
            f"stream header of {HeaderSize} bytes does not fit a {len(BlobValue)} byte stream"
        )
    return len(BlobValue) - GetTailSize(BlobValue, BaseValue, HeaderSize)


# this definition exists because each walk step records progress before parsing its tag
def WalkHeaderMut(
    BlobValue: bytes,
    BaseValue: int,
    Cursor: int,
    Frames: list[Frame],
    Segments: list[StaticSegment],
    Progress: list[int],
) -> tuple[int, int, str, str, TagAction]:
    Progress[0] = len(Segments)
    Progress[1] = len(Frames)
    Offset = Cursor
    Parent = Frames[-1].node if Frames else -1
    ParentName = Frames[-1].class_name if Frames else "<stream>"
    if Frames and Frames[-1].layout.groups:
        ParentSlot = f"{Frames[-1].key}[{Frames[-1].step}]"
    else:
        ParentSlot = str(Frames[-1].slot) if Frames else KLeadRun
    try:
        TagValue = ReadTag(BlobValue, Offset)
    except ArchiveError as ErrorInfo:
        raise Segmentation(
            ParentName, ParentSlot, Offset, str(ErrorInfo), BaseValue=BaseValue
        ) from ErrorInfo
    return (Offset, Parent, ParentName, ParentSlot, TagValue)


# this definition exists because tag resolution owns archive map counters and object ownership
def ResolveTagMut(
    TagValue: TagAction,
    Counter: int,
    BaseValue: int,
    Layouts: LayoutTable,
    Frames: list[Frame],
    ClassNames: dict[int, str],
    ObjectOwner: dict[int, str],
    ParentName: str,
    ParentSlot: str,
    Offset: int,
) -> tuple[int, int, str, int]:
    if TagValue.kind == KDefinitionKind:
        ClassIndex = Counter
        ObjectIndex = Counter + 1
        ClassNames[ClassIndex] = TagValue.class_name
        ObjectOwner[ObjectIndex] = TagValue.class_name
        return (ClassIndex, ObjectIndex, TagValue.class_name, Counter + 2)
    if TagValue.kind == KClassRefKind:
        return ResolveClassMut(
            TagValue,
            Counter,
            BaseValue,
            Layouts,
            Frames,
            ClassNames,
            ObjectOwner,
            ParentName,
            ParentSlot,
            Offset,
        )
    if TagValue.kind == KObjectRefKind:
        ClassIndex, ObjectIndex, NameValue = ResolveObject(
            TagValue,
            BaseValue,
            Layouts,
            Frames,
            ObjectOwner,
            ParentName,
            ParentSlot,
            Offset,
        )
        return (ClassIndex, ObjectIndex, NameValue, Counter)
    return (0, 0, KNullKind, Counter)


# this definition exists because class references resolve declared and previously defined names
def ResolveClassMut(
    TagValue: TagAction,
    Counter: int,
    BaseValue: int,
    Layouts: LayoutTable,
    Frames: list[Frame],
    ClassNames: dict[int, str],
    ObjectOwner: dict[int, str],
    ParentName: str,
    ParentSlot: str,
    Offset: int,
) -> tuple[int, int, str, int]:
    ClassIndex = TagValue.index
    DeclaredClass = DeclaredSlot(Layouts, Frames)
    if ClassIndex >= BaseValue and ClassIndex not in ClassNames and (not DeclaredClass):
        raise Segmentation(
            ParentName,
            ParentSlot,
            Offset,
            f"class reference {ClassIndex} is at or above the base {BaseValue} but no definition has been seen",
            BaseValue=BaseValue,
            UnresolvedIndex=ClassIndex,
            UnresolvedKind=KClassRefKind,
        )
    NameValue = ClassNames.get(ClassIndex, "")
    if not NameValue and ClassIndex >= BaseValue:
        NameValue = DeclaredClass
    if not NameValue:
        NameValue = OuterName(ClassIndex, Layouts, Frames)
    ObjectIndex = Counter
    ObjectOwner[ObjectIndex] = NameValue
    return (ClassIndex, ObjectIndex, NameValue, Counter + 1)


# this definition exists because object references validate ownership without advancing the map
def ResolveObject(
    TagValue: TagAction,
    BaseValue: int,
    Layouts: LayoutTable,
    Frames: list[Frame],
    ObjectOwner: dict[int, str],
    ParentName: str,
    ParentSlot: str,
    Offset: int,
) -> tuple[int, int, str]:
    ObjectIndex = TagValue.index
    DeclaredClass = DeclaredSlot(Layouts, Frames)
    if (
        ObjectIndex >= BaseValue
        and ObjectIndex not in ObjectOwner
        and (not DeclaredClass)
    ):
        raise Segmentation(
            ParentName,
            ParentSlot,
            Offset,
            f"object reference {ObjectIndex} is at or above the base {BaseValue} but no such object has been seen",
            BaseValue=BaseValue,
            UnresolvedIndex=ObjectIndex,
            UnresolvedKind=KObjectRefKind,
        )
    return (
        0,
        ObjectIndex,
        ObjectOwner.get(ObjectIndex, DeclaredClass or f"{KOuterPrefix}{ObjectIndex}"),
    )


# this definition exists because class nodes dispatch grouped slotted and leaf layout traversal
def OpenNodeMut(
    BlobValue: bytes,
    BaseValue: int,
    Layouts: LayoutTable,
    Frames: list[Frame],
    TagValue: TagAction,
    NameValue: str,
    NodeValue: int,
    Offset: int,
    Cursor: int,
    MoVersion: int | None,
) -> tuple[int, bool]:
    if TagValue.kind not in (KDefinitionKind, KClassRefKind):
        return (Cursor, False)
    Layout = Layouts.get(NameValue)
    if Layout is None:
        raise Segmentation(
            NameValue,
            KLeadRun,
            Offset,
            "no layout entry recorded for this class",
            BaseValue=BaseValue,
        )
    if Layout.repeats:
        raise Segmentation(
            NameValue,
            KLeadRun,
            Offset,
            "child count is not constant and no repeat rule is recorded"
            + (f" ({Layout.repeat_note})" if Layout.repeat_note else ""),
            BaseValue=BaseValue,
        )
    if Layout.groups:
        return OpenGroupsMut(
            BlobValue,
            BaseValue,
            Frames,
            Layout,
            NameValue,
            NodeValue,
            Offset,
            Cursor,
            MoVersion,
        )
    if Layout.child_slots:
        return OpenSlotsMut(
            BlobValue,
            BaseValue,
            Frames,
            Layout,
            NameValue,
            NodeValue,
            Offset,
            Cursor,
            MoVersion,
        )
    AmountA = RunLength(
        BlobValue, Cursor, Layout, KLeafRun, Offset, BaseValue, MoVersion
    )
    return (
        Advance(BlobValue, Cursor, AmountA, Layout, KLeafRun, Offset, BaseValue),
        False,
    )


# this definition exists because grouped layouts initialize their first planned child run
def OpenGroupsMut(
    BlobValue: bytes,
    BaseValue: int,
    Frames: list[Frame],
    Layout: ClassLayout,
    NameValue: str,
    NodeValue: int,
    Offset: int,
    Cursor: int,
    MoVersion: int | None,
) -> tuple[int, bool]:
    AmountA = RunLength(
        BlobValue, Cursor, Layout, KLeadRun, Offset, BaseValue, MoVersion
    )
    Cursor = Advance(BlobValue, Cursor, AmountA, Layout, KLeadRun, Offset, BaseValue)
    FrameData = Frame(
        node=NodeValue, class_name=NameValue, layout=Layout, slot=0, total=-1
    )
    Cursor, Opened = GroupOpenMut(
        BlobValue, Cursor, FrameData, Offset, BaseValue, MoVersion
    )
    if Opened:
        Frames.append(FrameData)
    return (Cursor, Opened)


# this definition exists because slotted layouts resolve their initial child count consistently
def OpenSlotsMut(
    BlobValue: bytes,
    BaseValue: int,
    Frames: list[Frame],
    Layout: ClassLayout,
    NameValue: str,
    NodeValue: int,
    Offset: int,
    Cursor: int,
    MoVersion: int | None,
) -> tuple[int, bool]:
    AmountA = RunLength(
        BlobValue, Cursor, Layout, KLeadRun, Offset, BaseValue, MoVersion
    )
    Cursor = Advance(BlobValue, Cursor, AmountA, Layout, KLeadRun, Offset, BaseValue)
    Total = -1
    if Layout.walks_a_prefix:
        Total = Layout.repeat_prefix
    elif Layout.ChildCounts is not None:
        Total = -1
    elif Layout.repeat_count is None:
        Total = len(Layout.child_slots)
    elif Layout.repeat_count.run == KLeadRun:
        Total = RepeatTotal(
            BlobValue, Cursor - AmountA, Cursor, Layout, Offset, BaseValue
        )
    if Total == 0:
        return (Cursor, False)
    Frames.append(
        Frame(node=NodeValue, class_name=NameValue, layout=Layout, slot=0, total=Total)
    )
    return (Cursor, True)


# this definition exists because closing child frames advances parent group and slot plans
def CloseNodeMut(
    BlobValue: bytes,
    BaseValue: int,
    Frames: list[Frame],
    Segments: list[StaticSegment],
    Cursor: int,
    MoVersion: int | None,
) -> int:
    while Frames:
        FrameData = Frames[-1]
        Origin = Segments[FrameData.node].offset
        if FrameData.layout.groups:
            Cursor, IsContinue = CloseGroupMut(
                BlobValue, BaseValue, Frames, FrameData, Origin, Cursor, MoVersion
            )
        else:
            Cursor, IsContinue = CloseSlotsMut(
                BlobValue, BaseValue, Frames, FrameData, Origin, Cursor, MoVersion
            )
        if not IsContinue:
            break
    return Cursor


# this definition exists because grouped frame completion handles trailers and subsequent groups
def CloseGroupMut(
    BlobValue: bytes,
    BaseValue: int,
    Frames: list[Frame],
    FrameData: Frame,
    Origin: int,
    Cursor: int,
    MoVersion: int | None,
) -> tuple[int, bool]:
    Group = FrameData.layout.groups[FrameData.group - 1]
    Amount, TrailerOverride, StopGroups = GroupElemLength(
        BlobValue, Cursor, FrameData, Origin, BaseValue, MoVersion
    )
    if FrameData.step + 1 == len(FrameData.plan):
        Amount += (
            GroupTrailer(
                BlobValue,
                Cursor + Amount,
                FrameData.layout,
                Group,
                Origin,
                BaseValue,
                MoVersion,
            )
            if TrailerOverride is None
            else TrailerOverride
        )
    Cursor = Advance(
        BlobValue, Cursor, Amount, FrameData.layout, FrameData.key, Origin, BaseValue
    )
    setattr(FrameData, "step", FrameData.step + 1)
    if FrameData.step < len(FrameData.plan):
        return (Cursor, False)
    if StopGroups:
        Frames.pop()
        return (Cursor, True)
    Cursor, Opened = GroupOpenMut(
        BlobValue, Cursor, FrameData, Origin, BaseValue, MoVersion
    )
    if Opened:
        return (Cursor, False)
    Frames.pop()
    return (Cursor, True)


# this definition exists because slotted frame completion resolves repeats and child class counts
def CloseSlotsMut(
    BlobValue: bytes,
    BaseValue: int,
    Frames: list[Frame],
    FrameData: Frame,
    Origin: int,
    Cursor: int,
    MoVersion: int | None,
) -> tuple[int, bool]:
    KeyValue = FrameData.layout.run_key(FrameData.slot)
    RunStart = Cursor
    AmountA = RunLength(
        BlobValue,
        Cursor,
        FrameData.layout,
        KeyValue,
        Origin,
        BaseValue,
        MoVersion,
        FrameData.ChildClass,
    )
    Cursor = Advance(
        BlobValue, Cursor, AmountA, FrameData.layout, KeyValue, Origin, BaseValue
    )
    Repeat = FrameData.layout.repeat_count
    if Repeat is not None and FrameData.total < 0 and (Repeat.run == KeyValue):
        setattr(
            FrameData,
            "total",
            RepeatTotal(
                BlobValue, RunStart, Cursor, FrameData.layout, Origin, BaseValue
            ),
        )
    ChildCounts = FrameData.layout.ChildCounts
    if (
        ChildCounts is not None
        and FrameData.total < 0
        and (FrameData.slot == ChildCounts.Slot)
    ):
        ResolvedCount = ChildCounts.Counts.get(FrameData.ChildClass)
        if ResolvedCount is None:
            raise Segmentation(
                FrameData.class_name,
                KeyValue,
                Origin,
                f"child count branch has no case for {FrameData.ChildClass!r}",
                BaseValue=BaseValue,
            )
        setattr(FrameData, "total", ResolvedCount)
    Limit = FrameData.total if FrameData.total >= 0 else FrameData.layout.template_slot
    if FrameData.slot + 1 < Limit:
        setattr(FrameData, "slot", FrameData.slot + 1)
        return (Cursor, False)
    if FrameData.total < 0:
        raise Segmentation(
            FrameData.class_name,
            KeyValue,
            Origin,
            "the repeated child count was not read before the repeated slots began",
            BaseValue=BaseValue,
        )
    if Repeat is not None and FrameData.layout.RepeatTrailer:
        Cursor = Advance(
            BlobValue,
            Cursor,
            FrameData.layout.RepeatTrailer,
            FrameData.layout,
            KTailRun,
            Origin,
            BaseValue,
        )
    Frames.pop()
    return (Cursor, True)


# this definition exists because traversal completion validates open frames and records progress
def FinishWalkMut(
    BaseValue: int,
    Frames: list[Frame],
    Segments: list[StaticSegment],
    Progress: list[int],
) -> tuple[StaticSegment, ...]:
    if Frames:
        FrameData = Frames[-1]
        raise Segmentation(
            FrameData.class_name,
            FrameData.key if FrameData.layout.groups else str(FrameData.slot),
            Segments[FrameData.node].offset,
            f"stream ended with {len(Frames)} open objects",
            BaseValue=BaseValue,
        )
    if not Segments:
        raise ArchiveError("stream holds no archive objects")
    Progress[0] = len(Segments)
    Progress[1] = 0
    return tuple(Segments)


# this definition exists because focused behavior needs one stable owner
def Segment(
    BlobValue: bytes,
    BaseValue: int,
    Layouts: LayoutTable,
    *,
    HeaderSize: int = KStreamHeaderSize,
    MoVersion: int | None = None,
    **Options: object,
) -> tuple[StaticSegment, ...]:
    HeaderSize, MoVersion, _ = ArchiveOptions(
        Options, HeaderSize, MoVersion, None, "Segment"
    )
    if MoVersion is not None and MoVersion < 0:
        raise ArchiveError(f"document version {MoVersion} must not be negative")
    Progress = [0, 0]
    Reached: list[StaticSegment] = []
    try:
        return SegmentWalkMut(
            BlobValue, BaseValue, Layouts, HeaderSize, Reached, Progress, MoVersion
        )
    except Segmentation as ErrorInfo:
        if ErrorInfo.progress < 0:
            setattr(ErrorInfo, "progress", Progress[0])
            setattr(ErrorInfo, "depth", Progress[1])
        if not ErrorInfo.reached:
            setattr(ErrorInfo, "reached", tuple(Reached))
        raise


# this definition exists because archive interfaces preserve established snake case option names
def ArchiveOptions(
    Options: Mapping[str, object],
    HeaderSize: int,
    MoVersion: int | None,
    Limit: int | None,
    Caller: str,
) -> tuple[int, int | None, int | None]:
    Allowed = {"header_size", "mo_version"}
    if Caller == "ResolveBase":
        Allowed.add("limit")
    Unknown = set(Options) - Allowed
    if Unknown:
        NameValue = next(iter(Unknown))
        raise TypeError(f"{Caller}() got an unexpected keyword argument '{NameValue}'")
    RawHeaderSize = Options.get("header_size", HeaderSize)
    RawMoVersion = Options.get("mo_version", MoVersion)
    RawLimit = Options.get("limit", Limit)
    if not isinstance(RawHeaderSize, int) or isinstance(RawHeaderSize, bool):
        raise TypeError(f"{Caller}() header_size must be an integer")
    if RawMoVersion is not None and (
        not isinstance(RawMoVersion, int) or isinstance(RawMoVersion, bool)
    ):
        raise TypeError(f"{Caller}() mo_version must be an integer or none")
    if RawLimit is not None and (
        not isinstance(RawLimit, int) or isinstance(RawLimit, bool)
    ):
        raise TypeError(f"{Caller}() limit must be an integer or none")
    HeaderSize = RawHeaderSize
    MoVersion = RawMoVersion
    Limit = RawLimit
    return (HeaderSize, MoVersion, Limit)


# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class BaseResolution:
    base: int
    seed: int
    segmented: bool
    progress: int
    offset: int
    tried: tuple[int, ...]
    implied: tuple[int, ...]

    # this definition exists because focused behavior needs one stable owner
    def AsDict(self) -> dict[str, object]:
        return {
            "base": self.base,
            "seed": self.seed,
            "segmented": self.segmented,
            "progress": self.progress,
            "offset": self.offset,
            "tried": list(self.tried),
            "implied": list(self.implied),
        }

    as_dict = AsDict


# this definition exists because focused behavior needs one stable owner
def ImpliedBases(Error: SegmentationError, BaseValue: int) -> tuple[int, ...]:
    if Error.unresolved_index < 0:
        return ()
    if Error.unresolved_kind != KClassRefKind:
        return ()
    Offsets = {
        ItemValue.class_index - BaseValue
        for ItemValue in Error.reached
        if ItemValue.kind == KDefinitionKind
    }
    Found = {
        Error.unresolved_index - Value
        for Value in Offsets
        if Error.unresolved_index - Value >= 1
    }
    return tuple(sorted(Found, reverse=True))


# this definition exists because focused behavior needs one stable owner
def ResolveBase(
    BlobValue: bytes,
    SeedValue: int,
    Layouts: LayoutTable,
    *,
    HeaderSize: int = KStreamHeaderSize,
    MoVersion: int | None = None,
    Limit: int = KBaseResolutionLimit,
    **Options: object,
) -> BaseResolution:
    HeaderSize, MoVersion, ResolvedLimit = ArchiveOptions(
        Options, HeaderSize, MoVersion, Limit, "ResolveBase"
    )
    if ResolvedLimit is None:
        raise ArchiveError("base resolution limit must be provided")
    Limit = ResolvedLimit
    Queue, Tried, Implied, Chosen, BestValue = BaseState(SeedValue, Limit)
    while Queue and len(Tried) < Limit:
        Choice = Queue.pop(0)
        if Choice < 1 or Choice in Tried:
            continue
        Tried.append(Choice)
        try:
            Produced = Segment(
                BlobValue, Choice, Layouts, HeaderSize=HeaderSize, MoVersion=MoVersion
            )
        except Segmentation as ErrorInfo:
            Score = (0, ErrorInfo.progress, ErrorInfo.offset)
            if Score > BestValue:
                BestValue = Score
                Chosen = Choice
            for Value in ImpliedBases(ErrorInfo, Choice):
                if Value not in Tried and Value not in Queue:
                    Queue.append(Value)
                    Implied.append(Value)
            continue
        except ArchiveError:
            continue
        Chosen = Choice
        BestValue = (1, len(Produced), len(BlobValue))
        break
    return BaseResolution(
        base=Chosen,
        seed=SeedValue,
        segmented=bool(BestValue[0]),
        progress=BestValue[1],
        offset=BestValue[2],
        tried=tuple(Tried),
        implied=tuple(Implied),
    )


# this definition exists because base resolver bounds and queue state share one initializer
def BaseState(
    SeedValue: int, Limit: int
) -> tuple[list[int], list[int], list[int], int, tuple[int, int, int]]:
    if SeedValue < 1:
        raise ArchiveError(f"base seed {SeedValue} must be positive")
    if Limit < 1:
        raise ArchiveError(f"base resolution limit {Limit} must be positive")
    return ([SeedValue], [], [], SeedValue, (0, -1, -1))


# this definition exists because focused behavior needs one stable owner
def BuildModel(
    BlobValue: bytes,
    Segments: Sequence[StaticSegment],
    BaseValue: int,
    HeaderSize: int,
    TrailerSize: int = 0,
) -> Model:
    if not Segments:
        raise ArchiveError("cannot build a model from an empty segmentation")
    if not TrailerSize:
        TrailerSize = GetTailSize(BlobValue, BaseValue, HeaderSize)
    ContentEnd = len(BlobValue) - TrailerSize
    Trailer = BlobValue[len(BlobValue) - TrailerSize :] if TrailerSize else b""
    ModelData = Model(header=BlobValue[:HeaderSize], base=BaseValue, Trailer=Trailer)
    ClassPosition: dict[int, int] = {}
    ObjectPosition: dict[int, int] = {}
    for Position, ItemValue in enumerate(Segments):
        BodyEnd = min(ItemValue.end, ContentEnd)
        BodyValue = BlobValue[ItemValue.offset + ItemValue.header : BodyEnd]
        if ItemValue.kind == KDefinitionKind:
            ModelData.nodes.append(
                NodeAction(
                    kind=KDefinitionKind,
                    body=BodyValue,
                    schema=ItemValue.schema,
                    class_name=ItemValue.class_name,
                    origin=ItemValue.offset,
                )
            )
            ClassPosition[ItemValue.class_index] = Position
            ObjectPosition[ItemValue.object_index] = Position
        elif ItemValue.kind == KClassRefKind:
            ModelData.nodes.append(
                NodeAction(
                    kind=KClassRefKind,
                    body=BodyValue,
                    class_name=ItemValue.class_name,
                    literal=ItemValue.class_index,
                    wide=ItemValue.wide,
                    target=ClassPosition.get(ItemValue.class_index, -1),
                    origin=ItemValue.offset,
                )
            )
            ObjectPosition[ItemValue.object_index] = Position
        elif ItemValue.kind == KObjectRefKind:
            ModelData.nodes.append(
                NodeAction(
                    kind=KObjectRefKind,
                    body=BodyValue,
                    literal=ItemValue.object_index,
                    wide=ItemValue.wide,
                    target=ObjectPosition.get(ItemValue.object_index, -1),
                    origin=ItemValue.offset,
                )
            )
        elif ItemValue.kind == KNullKind:
            ModelData.nodes.append(
                NodeAction(kind=KNullKind, body=BodyValue, origin=ItemValue.offset)
            )
        else:
            raise ArchiveError(
                f"unsupported tag kind {ItemValue.kind!r} at offset {ItemValue.offset}"
            )
    ValidateModel(ModelData, Segments, BaseValue)
    ModelData.assign()
    return ModelData


# this definition exists because rebuilt model references must resolve before index assignment
def ValidateModel(
    ModelData: Model, Segments: Sequence[StaticSegment], BaseValue: int
) -> None:
    for Position, ItemValue in enumerate(Segments):
        NodeValue = ModelData.nodes[Position]
        if (
            NodeValue.kind == KObjectRefKind
            and NodeValue.target < 0
            and (ItemValue.object_index >= BaseValue)
            and ItemValue.class_name.startswith(KOuterPrefix)
        ):
            raise ArchiveError(
                f"object reference {ItemValue.object_index} at offset {ItemValue.offset} is unresolved"
            )
        if (
            NodeValue.kind == KClassRefKind
            and NodeValue.target < 0
            and (ItemValue.class_index >= BaseValue)
            and ItemValue.class_name.startswith(KOuterPrefix)
        ):
            raise ArchiveError(
                f"class reference {ItemValue.class_index} at offset {ItemValue.offset} is unresolved"
            )


# this definition exists because focused behavior needs one stable owner
def Tiling(
    BlobValue: bytes,
    Segments: Sequence[StaticSegment],
    HeaderSize: int,
    TrailerSize: int = 0,
) -> TilingReport:
    GapsValue: list[tuple[int, int]] = []
    Overlaps: list[tuple[int, int]] = []
    Cursor = HeaderSize
    for ItemValue in Segments:
        if ItemValue.offset > Cursor:
            GapsValue.append((Cursor, ItemValue.offset))
        elif ItemValue.offset < Cursor:
            Overlaps.append((ItemValue.offset, Cursor))
        Cursor = ItemValue.end
    Trailing = len(BlobValue) - TrailerSize - Cursor
    return {
        "header_bytes": HeaderSize,
        "gaps": GapsValue,
        "overlaps": Overlaps,
        "trailing_bytes": Trailing,
        "covered": Cursor - HeaderSize,
        "tiles": not GapsValue and (not Overlaps) and (Trailing == 0),
    }


# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
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

    # this definition exists because focused behavior needs one stable owner
    def AsDict(self) -> dict[str, object]:
        return {
            "length": self.length,
            "base": self.base,
            "header_bytes": self.header_bytes,
            "segmented": self.segmented,
            "tiled": self.tiled,
            "identical": self.identical,
            "object_count": self.object_count,
            "definition_count": self.definition_count,
            "gaps": [list(ItemValue) for ItemValue in self.gaps],
            "overlaps": [list(ItemValue) for ItemValue in self.overlaps],
            "trailing_bytes": self.trailing_bytes,
            "error": self.error,
            "blocking_class": self.blocking_class,
            "blocking_slot": self.blocking_slot,
            "blocking_offset": self.blocking_offset,
            "blocking_depth": self.blocking_depth,
        }

    as_dict = AsDict


# this definition exists because focused behavior needs one stable owner
def Verify(
    BlobValue: bytes,
    BaseValue: int,
    Layouts: LayoutTable,
    *,
    HeaderSize: int = KStreamHeaderSize,
    MoVersion: int | None = None,
    **Options: object,
) -> VerifyReport:
    HeaderSize, MoVersion, _ = ArchiveOptions(
        Options, HeaderSize, MoVersion, None, "Verify"
    )
    try:
        Segments = Segment(
            BlobValue, BaseValue, Layouts, HeaderSize=HeaderSize, MoVersion=MoVersion
        )
    except Segmentation as ErrorInfo:
        return VerifyReport(
            length=len(BlobValue),
            base=BaseValue,
            header_bytes=HeaderSize,
            segmented=False,
            tiled=False,
            identical=False,
            object_count=max(ErrorInfo.progress, 0),
            definition_count=0,
            gaps=(),
            overlaps=(),
            trailing_bytes=len(BlobValue) - HeaderSize,
            error=str(ErrorInfo),
            blocking_class=ErrorInfo.class_name,
            blocking_slot=ErrorInfo.slot,
            blocking_offset=ErrorInfo.offset,
            blocking_depth=ErrorInfo.depth,
        )
    except ArchiveError as ErrorInfo:
        return VerifyReport(
            length=len(BlobValue),
            base=BaseValue,
            header_bytes=HeaderSize,
            segmented=False,
            tiled=False,
            identical=False,
            object_count=0,
            definition_count=0,
            gaps=(),
            overlaps=(),
            trailing_bytes=len(BlobValue) - HeaderSize,
            error=str(ErrorInfo),
            blocking_class="",
            blocking_slot="",
            blocking_offset=-1,
            blocking_depth=-1,
        )
    TrailerSize = GetTailSize(BlobValue, BaseValue, HeaderSize)
    Shape = Tiling(BlobValue, Segments, HeaderSize, TrailerSize)
    Definitions = sum(
        (1 for ItemValue in Segments if ItemValue.kind == KDefinitionKind)
    )
    try:
        Model = BuildModel(BlobValue, Segments, BaseValue, HeaderSize, TrailerSize)
        Rebuilt = Model.emit()
        Identical = Rebuilt == BlobValue
        Message = "" if Identical else f"re-emit produced {len(Rebuilt)} bytes"
    except ArchiveError as ErrorInfo:
        Identical = False
        Message = str(ErrorInfo)
    return VerifyReport(
        length=len(BlobValue),
        base=BaseValue,
        header_bytes=HeaderSize,
        segmented=True,
        tiled=bool(Shape["tiles"]),
        identical=Identical,
        object_count=len(Segments),
        definition_count=Definitions,
        gaps=tuple(Shape["gaps"]),
        overlaps=tuple(Shape["overlaps"]),
        trailing_bytes=int(Shape["trailing_bytes"]),
        error=Message,
        blocking_class="",
        blocking_slot="",
        blocking_offset=-1,
        blocking_depth=-1,
    )


# this definition exists because focused behavior needs one stable owner
def ClassNames(Segments: Iterable[StaticSegment]) -> tuple[str, ...]:
    SeenValue: dict[str, None] = {}
    for ItemValue in Segments:
        if ItemValue.kind in (KDefinitionKind, KClassRefKind):
            SeenValue[ItemValue.class_name] = None
    return tuple(SeenValue)


# this binding exists because shared behavior needs one stable value
BASE_RESOLUTION_LIMIT = KBaseResolutionLimit

# this binding exists because shared behavior needs one stable value
BIG_CLASS_TAG_BIT = KBigClassTagBit

# this binding exists because shared behavior needs one stable value
BIG_OBJECT_TAG = KBigObjectTag

# this binding exists because shared behavior needs one stable value
CLASS_REFERENCE_KIND = KClassRefKind

# this binding exists because shared behavior needs one stable value
CLASS_TAG_BIT = KClassTagBit

# this binding exists because shared behavior needs one stable value
CONDITIONAL_RULE = KConditionalRule

# this binding exists because shared behavior needs one stable value
COUNT_RULE = KCountRule

# this binding exists because shared behavior needs one stable value
ChildCountByClass = ChildCountBy

# this binding exists because shared behavior needs one stable value
DEFINITION_KIND = KDefinitionKind

# this binding exists because shared behavior needs one stable value
EXTERNAL_PREFIX = KOuterPrefix

# this binding exists because shared behavior needs one stable value
LEAD_RUN = KLeadRun

# this binding exists because shared behavior needs one stable value
LEAF_RUN = KLeafRun

# this binding exists because shared behavior needs one stable value
LONG_STRING_LIMIT = KLongStringLimit

# this binding exists because shared behavior needs one stable value
MAX_MAP_INDEX = KMaxMapIndex

# this binding exists because shared behavior needs one stable value
MO_VERSION_PREFIX = KMoVersionPrefix

# this binding exists because shared behavior needs one stable value
NEW_CLASS_TAG = KNewClassTag

# this binding exists because shared behavior needs one stable value
NULL_KIND = KNullKind

# this binding exists because shared behavior needs one stable value
NULL_TAG = KNullTag

# this binding exists because shared behavior needs one stable value
Node = NodeAction

# this binding exists because shared behavior needs one stable value
OBJECT_REFERENCE_KIND = KObjectRefKind

# this binding exists because shared behavior needs one stable value
OPAQUE_RULE = KOpaqueRule

# this binding exists because shared behavior needs one stable value
POLYMORPHIC_SLOT = KPolymorphicSlot

# this binding exists because shared behavior needs one stable value
ParseArchiveStringLength = ParseArchive

# this binding exists because shared behavior needs one stable value
ParseRunGroupCount = ParseRunGroup

# this binding exists because shared behavior needs one stable value
Path = PathValue

# this binding exists because shared behavior needs one stable value
REPEATED_SLOT = KRepeatedSlot

# this binding exists because shared behavior needs one stable value
RunGroupCountVariant = RunGroupCountA

# this binding exists because shared behavior needs one stable value
RunGroupTrailerVariant = RunGroupTrailer

# this binding exists because shared behavior needs one stable value
SHORT_STRING_LIMIT = KShortStringLimit

# this binding exists because shared behavior needs one stable value
STREAM_HEADER_SIZE = KStreamHeaderSize

# this binding exists because shared behavior needs one stable value
STRING_MARKER = KStringMarker

# this binding exists because shared behavior needs one stable value
STRING_RULE = KStringRule

# this binding exists because shared behavior needs one stable value
SegmentationError = Segmentation

# this binding exists because shared behavior needs one stable value
TAIL_RUN = KTailRun

# this binding exists because shared behavior needs one stable value
Tag = TagAction

# this binding exists because shared behavior needs one stable value
_Frame = Frame

# this binding exists because shared behavior needs one stable value
_advance = Advance

# this binding exists because shared behavior needs one stable value
_class_layout = ClassLayoutA

# this binding exists because shared behavior needs one stable value
_declared_slot_class = DeclaredSlot

# this binding exists because shared behavior needs one stable value
_element_length = ElemLength

# this binding exists because shared behavior needs one stable value
_external_name = OuterName

# this binding exists because shared behavior needs one stable value
_group_element_length = GroupElemLength

# this binding exists because shared behavior needs one stable value
_group_open = GroupOpenMut

# this binding exists because shared behavior needs one stable value
_group_trailer_length = GroupTrailer

# this binding exists because shared behavior needs one stable value
_repeat_total = RepeatTotal

# this binding exists because shared behavior needs one stable value
_run_group = RunGroupA

# this binding exists because shared behavior needs one stable value
_run_length = RunLength

# this binding exists because shared behavior needs one stable value
_scalar = Scalar

# this binding exists because shared behavior needs one stable value
_segment_walk = SegmentWalkMut

# this binding exists because shared behavior needs one stable value
annotations = Annotations

# this binding exists because shared behavior needs one stable value
build_model = BuildModel

# this binding exists because shared behavior needs one stable value
class_names = ClassNames

# this binding exists because shared behavior needs one stable value
container_mo_version = ContainerMo

# this binding exists because shared behavior needs one stable value
dataclass = Dataclass

# this binding exists because shared behavior needs one stable value
encode_class_definition = EncodeClass

# this binding exists because shared behavior needs one stable value
encode_class_reference = EncodeClassRef

# this binding exists because shared behavior needs one stable value
encode_null = EncodeNull

# this binding exists because shared behavior needs one stable value
encode_object_reference = EncodeObjectRef

# this binding exists because shared behavior needs one stable value
encode_string = EncodeString

# this binding exists because shared behavior needs one stable value
field = Field

# this binding exists because shared behavior needs one stable value
implied_bases = ImpliedBases

# this binding exists because shared behavior needs one stable value
json = JsonModule

# this binding exists because shared behavior needs one stable value
read_string = ReadString

# this binding exists because shared behavior needs one stable value
read_tag = ReadTag

# this binding exists because shared behavior needs one stable value
resolve_base = ResolveBase

# this binding exists because shared behavior needs one stable value
segment = Segment

# this binding exists because shared behavior needs one stable value
struct = Struct

# this binding exists because shared behavior needs one stable value
tiling = Tiling

# this binding exists because shared behavior needs one stable value
verify = Verify

# this binding exists because shared behavior needs one stable value
GroupOpen = GroupOpenMut

# this binding exists because shared behavior needs one stable value
SegmentWalk = SegmentWalkMut
