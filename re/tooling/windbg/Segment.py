# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations
from dataclasses import dataclass as DataClass, asdict as Asdict
import json as JsonData
from pathlib import Path as PathInfo
import struct as Struct
import sys as System

# needed to keep reverse engineering responsibilities isolated and maintainable
KHereInfo = PathInfo(__file__).resolve().parent

# needed to keep reverse engineering responsibilities isolated and maintainable
KScratch = KHereInfo.parents[2] / ".rescratch"

# needed to keep reverse engineering responsibilities isolated and maintainable
KGrammar = KHereInfo.parent / "harness"
for CandInfo in (KHereInfo, KGrammar):
    if str(CandInfo) not in System.path:
        System.path.insert(0, str(CandInfo))
import Tracelog as Tracelog
import Streamlib as Streamlib
from convert.Security.PathBoundary import ResolveInput, ValidateLabel


# needed to keep reverse engineering responsibilities isolated and maintainable
def GetLegacyAttr(SelfRef, NameText):
    AliasName = SelfRef.KAliasNames.get(NameText)
    if AliasName is None:
        raise AttributeError(NameText)
    return getattr(SelfRef, AliasName)


# needed to keep reverse engineering responsibilities isolated and maintainable
def SetLegacyMut(SelfRef, NameText, ValueData):
    TargetName = SelfRef.KAliasNames.get(NameText, NameText)
    object.__setattr__(SelfRef, TargetName, ValueData)


# needed to keep reverse engineering responsibilities isolated and maintainable
KOutInfo = KScratch / "trace" / "out"

# needed to keep reverse engineering responsibilities isolated and maintainable
KNewClassTag = 65535

# needed to keep reverse engineering responsibilities isolated and maintainable
KClassTagBit = 32768

# needed to keep reverse engineering responsibilities isolated and maintainable
KBigObjectTag = 32767

# needed to keep reverse engineering responsibilities isolated and maintainable
KNullTag = 0


# needed to keep reverse engineering responsibilities isolated and maintainable
class SegmentError(RuntimeError):
    __slots__ = ()


# needed to keep reverse engineering responsibilities isolated and maintainable
@DataClass(frozen=True, slots=True)
class Segment:
    IndexData: int
    Offset: int
    EndIndex: int
    Length: int
    ScopeEnd: int
    Depth: int
    Parent: int
    RspInfo: int
    TagInfoInfo: int
    KindNameInfo: str
    Header: int
    ClassIndex: int
    ClassNameData: str
    MapIndex: int
    ModelledIndex: int
    ObjectIndex: int
    KAliasNames = {
        "index": "IndexData",
        "offset": "Offset",
        "end": "EndIndex",
        "length": "Length",
        "scope_end": "ScopeEnd",
        "depth": "Depth",
        "parent": "Parent",
        "rsp": "RspInfo",
        "tag": "TagInfoInfo",
        "kind": "KindNameInfo",
        "header": "Header",
        "class_index": "ClassIndex",
        "class_name": "ClassNameData",
        "map_index": "MapIndex",
        "modelled_index": "ModelledIndex",
        "object_index": "ObjectIndex",
    }


# needed to keep reverse engineering responsibilities isolated and maintainable
Segment.__getattr__ = GetLegacyAttr


# needed to keep reverse engineering responsibilities isolated and maintainable
def TagAt(ByteBlob: bytes, Offset: int) -> tuple[int, str, int]:
    Token = Struct.unpack_from("<H", ByteBlob, Offset)[0]
    if Token == KNewClassTag:
        Length = Struct.unpack_from("<H", ByteBlob, Offset + 4)[0]
        return (Token, "definition", 6 + Length)
    if Token == KNullTag:
        return (Token, "null", 2)
    if Token == KBigObjectTag:
        return (Token, "big", 6)
    if Token & KClassTagBit:
        return (Token, "classref", 2)
    return (Token, "objectref", 2)


# needed to keep reverse engineering responsibilities isolated and maintainable
def Ordered(
    Events: tuple[Tracelog.Event, ...], Buffer: int, SpanInfo: int | None = None
) -> list[Tracelog.Event]:
    SeenInfo: set[int] = set()
    Result: list[Tracelog.Event] = []
    for EventInfo in Events:
        if (
            EventInfo.kind != "RO"
            or EventInfo.buffer != Buffer
            or EventInfo.offset in SeenInfo
        ):
            continue
        if SpanInfo is not None and EventInfo.span != SpanInfo:
            continue
        SeenInfo.add(EventInfo.offset)
        Result.append(EventInfo)

    # needed to keep reverse engineering responsibilities isolated and maintainable
    Result.sort(key=lambda EventInfo: EventInfo.offset)
    return Result


# needed to keep reverse engineering responsibilities isolated and maintainable
def Nesting(Events: list[Tracelog.Event]) -> tuple[list[int], list[int], list[int]]:
    Stack: list[tuple[int, int]] = []
    Depths: list[int] = []
    Parents: list[int] = []
    for PosInfoInfo, EventInfo in enumerate(Events):
        while Stack and Stack[-1][0] <= EventInfo.rsp:
            Stack.pop()
        Parents.append(Stack[-1][1] if Stack else -1)
        Depths.append(len(Stack))
        Stack.append((EventInfo.rsp, PosInfoInfo))
    Scope: list[int] = []
    for PosInfoInfo, EventInfo in enumerate(Events):
        EndIndex = -1
        for Later in range(PosInfoInfo + 1, len(Events)):
            if Events[Later].rsp >= EventInfo.rsp:
                EndIndex = Events[Later].offset
                break
        Scope.append(EndIndex)
    return (Depths, Parents, Scope)


# needed to keep reverse engineering responsibilities isolated and maintainable
def FinishBuildMut(
    ByteBlob, Depths, EventInfo, Names, OrderedInfo, Parents, Scope
) -> tuple[Segment, ...]:
    CounterInfo = OrderedInfo[0].counter
    Result: list[Segment] = []
    for PosInfoInfo, EventInfo in enumerate(OrderedInfo):
        Offset = EventInfo.offset
        EndIndex = (
            OrderedInfo[PosInfoInfo + 1].offset
            if PosInfoInfo + 1 < len(OrderedInfo)
            else len(ByteBlob)
        )
        Token, KindNameInfo, Header = TagAt(ByteBlob, Offset)
        Modelled = CounterInfo
        if KindNameInfo == "definition":
            Length = Struct.unpack_from("<H", ByteBlob, Offset + 4)[0]
            NameTextInfo = ByteBlob[Offset + 6 : Offset + 6 + Length].decode(
                "ascii", "replace"
            )
            ClassIndex = CounterInfo
            Names[ClassIndex] = NameTextInfo
            ObjectIndex = CounterInfo + 1
            CounterInfo += 2
        elif KindNameInfo == "classref":
            ClassIndex = Token & ~KClassTagBit
            NameTextInfo = Names.get(ClassIndex, f"external#{ClassIndex}")
            ObjectIndex = CounterInfo
            CounterInfo += 1
        elif KindNameInfo == "objectref":
            ClassIndex = 0
            NameTextInfo = f"backref->{Token}"
            ObjectIndex = Token
        else:
            ClassIndex = 0
            NameTextInfo = KindNameInfo
            ObjectIndex = 0
        Result.append(
            Segment(
                IndexData=PosInfoInfo,
                Offset=Offset,
                EndIndex=EndIndex,
                Length=EndIndex - Offset,
                ScopeEnd=(
                    Scope[PosInfoInfo] if Scope[PosInfoInfo] >= 0 else len(ByteBlob)
                ),
                Depth=Depths[PosInfoInfo],
                Parent=Parents[PosInfoInfo],
                RspInfo=EventInfo.rsp,
                TagInfoInfo=Token,
                KindNameInfo=KindNameInfo,
                Header=Header,
                ClassIndex=ClassIndex,
                ClassNameData=NameTextInfo,
                MapIndex=EventInfo.counter,
                ModelledIndex=Modelled,
                ObjectIndex=ObjectIndex,
            )
        )
    return tuple(Result)


# needed to keep reverse engineering responsibilities isolated and maintainable
def Build(
    ByteBlob: bytes,
    Events: tuple[Tracelog.Event, ...],
    *,
    Buffer: int | None = None,
    SpanInfo: int | None = None,
) -> tuple[Segment, ...]:
    Objects = tuple((EventInfo for EventInfo in Events if EventInfo.kind == "RO"))
    if not Objects:
        raise SegmentError("trace contains no ReadObject events")
    if Buffer is not None:
        Target = Buffer
    elif SpanInfo is not None:
        Target = Tracelog.BusiestBuffer(Events, SpanInfo)
    else:
        Target = Tracelog.DominantBuffer(Objects)
    OrderedInfo = Ordered(Events, Target, SpanInfo)
    Depths, Parents, Scope = Nesting(OrderedInfo)
    Names: dict[int, str] = {}
    return FinishBuildMut(
        ByteBlob, Depths, EventInfo, Names, OrderedInfo, Parents, Scope
    )


# needed to keep reverse engineering responsibilities isolated and maintainable
def Tiling(ByteBlob: bytes, SegmentsInfo: tuple[Segment, ...]) -> dict[str, object]:
    FindGaps: list[tuple[int, int]] = []
    Overlaps: list[tuple[int, int]] = []
    Cursor = SegmentsInfo[0].offset
    for ItemData in SegmentsInfo:
        if ItemData.offset > Cursor:
            FindGaps.append((Cursor, ItemData.offset))
        if ItemData.offset < Cursor:
            Overlaps.append((ItemData.offset, Cursor))
        Cursor = ItemData.end
    Trailing = len(ByteBlob) - Cursor
    return {
        "header_bytes": SegmentsInfo[0].offset,
        "gaps": FindGaps,
        "overlaps": Overlaps,
        "trailing_bytes": Trailing,
        "covered": Cursor - SegmentsInfo[0].offset,
        "tiles": not FindGaps and (not Overlaps) and (Trailing == 0),
    }


# needed to keep reverse engineering responsibilities isolated and maintainable
def CounterData(SegmentsInfo: tuple[Segment, ...]) -> tuple[Segment, ...]:
    return tuple(
        (
            ItemData
            for ItemData in SegmentsInfo
            if ItemData.map_index != ItemData.modelled_index
        )
    )


# needed to keep reverse engineering responsibilities isolated and maintainable
def ClassTable(SegmentsInfo: tuple[Segment, ...]) -> dict[str, int]:
    return {
        ItemData.class_name: ItemData.class_index
        for ItemData in SegmentsInfo
        if ItemData.kind == "definition"
    }


# needed to keep reverse engineering responsibilities isolated and maintainable
def IncrementRule(SegmentsInfo: tuple[Segment, ...]) -> dict[str, list[int]]:
    Table: dict[str, set[int]] = {}
    for LeftInfo, Right in zip(SegmentsInfo, SegmentsInfo[1:]):
        Table.setdefault(LeftInfo.kind, set()).add(Right.map_index - LeftInfo.map_index)
    return {
        KindNameInfo: sorted(Values) for KindNameInfo, Values in sorted(Table.items())
    }


# needed to keep reverse engineering responsibilities isolated and maintainable
def LoadData(
    PartInfoInfo: PathInfo, LogInfo: PathInfo, *, Stream: str = Streamlib.KResolved
) -> tuple[bytes, tuple[Segment, ...]]:
    ByteBlob = Streamlib.LoadDonor(PartInfoInfo).streams[Stream]
    Events = Tracelog.ReadEvents(LogInfo)
    Spans = {EventInfo.span for EventInfo in Events if EventInfo.kind == "RO"}
    SpanInfo = len(ByteBlob) if Spans - {0} else None
    return (ByteBlob, Build(ByteBlob, Events, SpanInfo=SpanInfo))


# needed to keep reverse engineering responsibilities isolated and maintainable
def Report(
    LabelInfo: str,
    PartInfoInfo: PathInfo,
    LogInfo: PathInfo,
    *,
    Stream: str = Streamlib.KResolved,
) -> dict[str, object]:
    ByteBlob, SegmentsInfo = LoadData(PartInfoInfo, LogInfo, Stream=Stream)
    Shape = Tiling(ByteBlob, SegmentsInfo)
    Mismatch = CounterData(SegmentsInfo)
    Defns = tuple(
        (ItemData for ItemData in SegmentsInfo if ItemData.kind == "definition")
    )
    PayloadInfo = {
        "label": LabelInfo,
        "part": str(PartInfoInfo),
        "log": str(LogInfo),
        "stream": Stream,
        "stream_length": len(ByteBlob),
        "base_map_index": SegmentsInfo[0].map_index,
        "object_count": len(SegmentsInfo),
        "definition_count": len(Defns),
        "counter_mismatches": len(Mismatch),
        "tiling": Shape,
        "increment_rule": IncrementRule(SegmentsInfo),
        "class_index": ClassTable(SegmentsInfo),
        "segments": [Asdict(ItemData) for ItemData in SegmentsInfo],
    }
    KOutInfo.mkdir(parents=True, exist_ok=True)
    (KOutInfo / f"segments_{LabelInfo}.json").write_text(
        JsonData.dumps(PayloadInfo, indent=2), encoding="utf-8"
    )
    print(
        f"{LabelInfo:14s} stream={len(ByteBlob):6d} objects={len(SegmentsInfo):4d} defs={len(Defns):3d} base={SegmentsInfo[0].map_index} tiles={Shape['tiles']} mismatches={len(Mismatch)}"
    )
    return PayloadInfo


# needed to keep reverse engineering responsibilities isolated and maintainable
def MainRun() -> int:
    ArgsInfo = System.argv[1:]
    if len(ArgsInfo) % 3:
        raise SystemExit("usage: Segment.py <label> <part> <log> [...]")
    for PosInfoInfo in range(0, len(ArgsInfo), 3):
        LabelInfo = ValidateLabel(ArgsInfo[PosInfoInfo])
        PartInfoInfo = ResolveInput(ArgsInfo[PosInfoInfo + 1])
        LogInfo = ResolveInput(ArgsInfo[PosInfoInfo + 2])
        Report(LabelInfo, PartInfoInfo, LogInfo)
    return 0


if __name__ == "__main__":
    raise SystemExit(MainRun())
