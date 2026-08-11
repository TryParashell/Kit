# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import PureWindowsPath
from types import MappingProxyType
from typing import Any

from .assembly_distinct_repeat import (
    ConfigShift1 as ConfigShiftUnique,
    ConfigShift5 as ConfigShiftMap,
    ResolvedShift1 as ResolvedShiftUnique,
    ResolvedShift5 as ResolvedShiftMap,
    ResolvedShift9 as ResolvedShiftLink,
)
from .assembly_hybrid5_programs import EncodeField, StreamPrograms
from .assembly_repeat import RepeatItem, _IsIdentityBasis, _OccurHash
from .container import SldprtFormatError


# recovered boundaries separate stable fields from hybrid occurrence records
InsertSpecs = MappingProxyType(
    {
        "Contents/CMgr": (1720, 378),
        "Contents/Config-0": (668, 502),
        "Contents/Config-0-ResolvedFeatures": (755, 56),
        "Contents/Config-0-ModelHeader": (1728, 58),
    }
)

# five traced occurrences isolate occurrence growth from file-class growth
TracedCount = 5

# three traced component files anchor the independent unique-file dimension
TracedUnique = 3

# header boundaries isolate occurrences, the first file, repeated files, and tail
HeaderExtStart = 1960

# the first file record includes the external-object list framing
HeaderExtWidth = 300

# subsequent file records share one fixed typed field sequence
HeaderFileStart = 2260

# equal-width oracle paths expose the physical repeated-file record boundary
HeaderFileWidth = 229

# the stable header tail follows the two traced subsequent file records
HeaderTailStart = 2718


# operation emission preserves typed ownership while applying semantic values
def _EmitOps(
    Operations: Sequence[tuple[int, int, int, str, Any]],
    Overrides: Mapping[int, Any],
    BasePos: int = 0,
    BasisValues: Mapping[int, tuple[float, ...]] | None = None,
) -> bytes:
    OutputData = bytearray()
    BasisMap = BasisValues or {}
    for StartPos, _FieldWidth, _OwnerIndex, KindName, DefaultValue in Operations:
        FieldValue = Overrides.get(StartPos - BasePos, DefaultValue)
        OutputData.extend(EncodeField(KindName, FieldValue))
        BasisValue = BasisMap.get(StartPos - BasePos)
        if BasisValue is not None:
            if KindName != "primitive:uchar" or FieldValue != 1:
                raise SldprtFormatError("assembly transform basis marker is invalid")
            OutputData.extend(EncodeField("direct:9d", BasisValue))
    return bytes(OutputData)


# logical slicing remains stable when semantic strings change physical width
def _SliceOps(
    StreamName: str,
    StartPos: int,
    EndPos: int | None = None,
) -> tuple[tuple[int, int, int, str, Any], ...]:
    return tuple(
        Operation
        for Operation in StreamPrograms[StreamName]
        if Operation[0] >= StartPos and (EndPos is None or Operation[0] < EndPos)
    )


# windows path keys identify repeated component documents case-insensitively
def _PathKey(PathValue: str) -> str:
    return str(PureWindowsPath(PathValue)).casefold()


# first occurrences define unique component-file ordering independently
def _UniqueItems(CoreItems: tuple[RepeatItem, ...]) -> tuple[RepeatItem, ...]:
    SeenPaths: set[str] = set()
    UniqueItems: list[RepeatItem] = []
    for ItemValue in CoreItems:
        PathValue = _PathKey(ItemValue.CompPath)
        if PathValue in SeenPaths:
            continue
        SeenPaths.add(PathValue)
        UniqueItems.append(ItemValue)
    return tuple(UniqueItems)


# path ordinals reconnect every occurrence to its unique external file
def _PathIndex(UniqueItems: tuple[RepeatItem, ...]) -> Mapping[str, int]:
    return MappingProxyType(
        {
            _PathKey(ItemValue.CompPath): ItemIndex
            for ItemIndex, ItemValue in enumerate(UniqueItems, 1)
        }
    )


# hybrid configuration-manager records enumerate every component occurrence
def _EncodeCMgr(
    ModelName: str,
    ConfigName: str,
    CoreItems: tuple[RepeatItem, ...],
) -> bytes:
    ItemCount = len(CoreItems)
    DisplayName = f"<{ConfigName}>_Display State 1"
    InsertPos, UnitWidth = InsertSpecs["Contents/CMgr"]
    PrefixData = _EmitOps(
        _SliceOps("Contents/CMgr", 0, InsertPos),
        {
            206: ConfigName,
            365: ItemCount,
            377: 23 + ItemCount,
            381: 103 + (2 * ItemCount),
            1031: ItemCount + 1,
            1241: DisplayName,
            1464: ModelName,
            1515: CoreItems[0].OccurName,
            1617: CoreItems[0].ConfigName,
            1655: CoreItems[0].ConfigName,
        },
    )
    UnitData = bytearray()
    for ItemIndex, ItemValue in enumerate(CoreItems[1:], 2):
        TemplateIndex = min(ItemIndex, TracedCount)
        UnitStart = InsertPos + ((TemplateIndex - 2) * UnitWidth)
        UnitData.extend(
            _EmitOps(
                _SliceOps("Contents/CMgr", UnitStart, UnitStart + UnitWidth),
                {
                    48: DisplayName,
                    184: 23 + ItemIndex,
                    190: ItemValue.OccurName,
                    275: ItemValue.ConfigName,
                    313: ItemValue.ConfigName,
                },
                UnitStart,
            )
        )
    SuffixStart = InsertPos + ((TracedCount - 1) * UnitWidth)
    SuffixData = _EmitOps(
        _SliceOps("Contents/CMgr", SuffixStart),
        {82: 61 + (8 * (ItemCount - TracedCount))},
        SuffixStart,
    )
    return PrefixData + bytes(UnitData) + SuffixData


# hybrid configuration records bind occurrence maps to unique file classes
def _EncodeConfig(
    ModelName: str,
    ConfigName: str,
    CoreItems: tuple[RepeatItem, ...],
    UniqueItems: tuple[RepeatItem, ...],
) -> bytes:
    ItemCount = len(CoreItems)
    BasisCount = sum(
        not _IsIdentityBasis(ItemValue.BasisVals) for ItemValue in CoreItems
    )
    UniqueCount = len(UniqueItems)
    OccurShift = ItemCount - TracedCount
    UniqueShift = UniqueCount - TracedUnique
    MapShift = (4 * OccurShift) + UniqueShift
    PathIndex = _PathIndex(UniqueItems)
    InsertPos, UnitWidth = InsertSpecs["Contents/Config-0"]
    PrefixData = _EmitOps(
        _SliceOps("Contents/Config-0", 0, InsertPos),
        {
            18: 2218 + (UnitWidth * ItemCount) + (72 * BasisCount),
            48: ModelName,
            88: ItemCount,
            109: 4 + UniqueCount,
            111: CoreItems[0].OccurName,
            400: ConfigName,
            533: 11 + UniqueCount,
            535: ModelName,
            584: 11 + UniqueCount,
            586: CoreItems[0].OccurName,
            606: 7 + UniqueCount,
            276: CoreItems[0].TransX,
            284: CoreItems[0].TransY,
            292: CoreItems[0].TransZ,
            **({275: 1} if not _IsIdentityBasis(CoreItems[0].BasisVals) else {}),
        },
        BasisValues=(
            {275: CoreItems[0].BasisVals}
            if not _IsIdentityBasis(CoreItems[0].BasisVals)
            else None
        ),
    )
    UnitData = bytearray()
    for ItemIndex, ItemValue in enumerate(CoreItems[1:], 2):
        TemplateIndex = min(ItemIndex, TracedCount)
        UnitStart = InsertPos + ((TemplateIndex - 2) * UnitWidth)
        UnitOps = _SliceOps("Contents/Config-0", UnitStart, UnitStart + UnitWidth)
        HashValue = (
            next(
                Operation[4] for Operation in UnitOps if Operation[0] - UnitStart == 153
            )
            if ItemIndex <= TracedCount
            else _OccurHash(ItemValue.OccurName)
        )
        FileIndex = PathIndex[_PathKey(ItemValue.CompPath)]
        UnitData.extend(
            _EmitOps(
                UnitOps,
                {
                    0: 6 + UniqueCount,
                    2: 4 + UniqueCount,
                    4: ItemValue.OccurName,
                    32: 23 + ItemIndex,
                    153: HashValue,
                    169: ItemValue.TransX,
                    177: ItemValue.TransY,
                    185: ItemValue.TransZ,
                    283: 3 + FileIndex,
                    293: ItemValue.ConfigName,
                    341: 14 + ItemIndex,
                    379: 9 + UniqueCount,
                    381: 12 + UniqueCount,
                    383: 13 + UniqueCount,
                    414: 23 + ItemIndex,
                    418: 11 + UniqueCount,
                    420: ItemValue.OccurName,
                    440: 7 + (4 * ItemIndex) + UniqueCount,
                    **({168: 1} if not _IsIdentityBasis(ItemValue.BasisVals) else {}),
                },
                UnitStart,
                (
                    {168: ItemValue.BasisVals}
                    if not _IsIdentityBasis(ItemValue.BasisVals)
                    else None
                ),
            )
        )
    SuffixStart = InsertPos + ((TracedCount - 1) * UnitWidth)
    SuffixOps = _SliceOps("Contents/Config-0", SuffixStart)
    SuffixOverrides: dict[int, Any] = {}
    for StartPos, _Width, _Owner, _Kind, DefaultValue in SuffixOps:
        RelativePos = StartPos - SuffixStart
        if RelativePos in ConfigShiftMap:
            SuffixOverrides[RelativePos] = DefaultValue + MapShift
        elif RelativePos in ConfigShiftUnique:
            SuffixOverrides[RelativePos] = DefaultValue + UniqueShift
    SuffixOverrides[23442] = ItemCount
    SuffixData = _EmitOps(SuffixOps, SuffixOverrides, SuffixStart)
    return PrefixData + bytes(UnitData) + SuffixData


# resolved records reconnect occurrence maps and unique component classes
def _EncodeResolved(
    CoreItems: tuple[RepeatItem, ...],
    UniqueItems: tuple[RepeatItem, ...],
) -> bytes:
    ItemCount = len(CoreItems)
    UniqueCount = len(UniqueItems)
    OccurShift = ItemCount - TracedCount
    UniqueShift = UniqueCount - TracedUnique
    MapShift = (4 * OccurShift) + UniqueShift
    LinkShift = (8 * OccurShift) + UniqueShift
    InsertPos, UnitWidth = InsertSpecs["Contents/Config-0-ResolvedFeatures"]
    PrefixData = _EmitOps(
        _SliceOps("Contents/Config-0-ResolvedFeatures", 0, InsertPos),
        {
            0: 96 + (4 * ItemCount) + UniqueCount,
            30: 4 + UniqueCount,
            227: 4 + UniqueCount,
            433: 4 + UniqueCount,
            604: ItemCount,
            737: 10 + UniqueCount,
            739: 20 + (13 * ItemCount),
        },
    )
    UnitData = bytearray()
    for ItemIndex in range(2, ItemCount + 1):
        TemplateIndex = min(ItemIndex, TracedCount)
        UnitStart = InsertPos + ((TemplateIndex - 2) * UnitWidth)
        UnitOps = _SliceOps(
            "Contents/Config-0-ResolvedFeatures",
            UnitStart,
            UnitStart + UnitWidth,
        )
        RefValues = {
            StartPos - UnitStart: DefaultValue + MapShift
            for StartPos, _Width, _Owner, KindName, DefaultValue in UnitOps
            if KindName == "classref"
        }
        UnitData.extend(
            _EmitOps(
                UnitOps,
                {
                    **RefValues,
                    38: 9 + (4 * ItemIndex) + UniqueCount,
                    40: 32 + (13 * (ItemCount - ItemIndex)) + (ItemIndex % 2),
                },
                UnitStart,
            )
        )
    SuffixStart = InsertPos + ((TracedCount - 1) * UnitWidth)
    SuffixOps = _SliceOps("Contents/Config-0-ResolvedFeatures", SuffixStart)
    SuffixOverrides: dict[int, Any] = {}
    for StartPos, _Width, _Owner, _Kind, DefaultValue in SuffixOps:
        RelativePos = StartPos - SuffixStart
        if RelativePos in ResolvedShiftLink:
            SuffixOverrides[RelativePos] = DefaultValue + LinkShift
        elif RelativePos in ResolvedShiftMap:
            SuffixOverrides[RelativePos] = DefaultValue + MapShift
        elif RelativePos in ResolvedShiftUnique:
            SuffixOverrides[RelativePos] = DefaultValue + UniqueShift
    SuffixData = _EmitOps(SuffixOps, SuffixOverrides, SuffixStart)
    return PrefixData + bytes(UnitData) + SuffixData


# model-header records separate occurrence stamps from unique component files
def _EncodeHeader(
    ModelName: str,
    ConfigName: str,
    CoreItems: tuple[RepeatItem, ...],
    UniqueItems: tuple[RepeatItem, ...],
) -> bytes:
    ItemCount = len(CoreItems)
    UniqueCount = len(UniqueItems)
    PathCounts = Counter(_PathKey(ItemValue.CompPath) for ItemValue in CoreItems)
    InsertPos, UnitWidth = InsertSpecs["Contents/Config-0-ModelHeader"]
    PrefixData = _EmitOps(
        _SliceOps("Contents/Config-0-ModelHeader", 0, InsertPos),
        {
            77: 23 + ItemCount,
            142: ModelName,
            1708: CoreItems[0].OccurName,
        },
    )
    OccurData = bytearray()
    for ItemIndex, ItemValue in enumerate(CoreItems[1:], 2):
        TemplateIndex = min(ItemIndex, TracedCount)
        UnitStart = InsertPos + ((TemplateIndex - 2) * UnitWidth)
        OccurData.extend(
            _EmitOps(
                _SliceOps(
                    "Contents/Config-0-ModelHeader",
                    UnitStart,
                    UnitStart + UnitWidth,
                ),
                {34: 23 + ItemIndex, 38: ItemValue.OccurName},
                UnitStart,
            )
        )
    FirstItem = UniqueItems[0]
    FirstStem = PureWindowsPath(FirstItem.CompPath).stem
    ExtOverrides = {
        4: 24 + ItemCount,
        31: UniqueCount,
        75: FirstItem.CompPath,
        225: 64 + (2 * ItemCount),
        227: FirstStem,
        268: PathCounts[_PathKey(FirstItem.CompPath)],
    }
    if FirstItem.FileStamp > 0:
        ExtOverrides[246] = FirstItem.FileStamp
    ExtPrefix = _EmitOps(
        _SliceOps(
            "Contents/Config-0-ModelHeader",
            HeaderExtStart,
            HeaderExtStart + HeaderExtWidth,
        ),
        ExtOverrides,
        HeaderExtStart,
    )
    FileData = bytearray()
    for FileIndex, ItemValue in enumerate(UniqueItems[1:], 2):
        TemplateIndex = min(FileIndex, TracedUnique)
        FileStart = HeaderFileStart + ((TemplateIndex - 2) * HeaderFileWidth)
        FileStem = PureWindowsPath(ItemValue.CompPath).stem
        FileOverrides = {
            0: 62 + (2 * ItemCount),
            2: 64 + (2 * ItemCount),
            4: ItemValue.CompPath,
            154: 64 + (2 * ItemCount),
            156: FileStem,
            197: PathCounts[_PathKey(ItemValue.CompPath)],
            205: FileIndex - 1,
        }
        if ItemValue.FileStamp > 0:
            FileOverrides[175] = ItemValue.FileStamp
        FileData.extend(
            _EmitOps(
                _SliceOps(
                    "Contents/Config-0-ModelHeader",
                    FileStart,
                    FileStart + HeaderFileWidth,
                ),
                FileOverrides,
                FileStart,
            )
        )
    TailData = _EmitOps(
        _SliceOps("Contents/Config-0-ModelHeader", HeaderTailStart),
        {
            0: 103 + (2 * ItemCount),
            4: 62 + (2 * ItemCount),
            6: 64 + (2 * ItemCount),
            12: 64 + (2 * ItemCount),
            14: ModelName,
            67: ConfigName,
            131: ItemCount,
        },
        HeaderTailStart,
    )
    return PrefixData + bytes(OccurData) + ExtPrefix + bytes(FileData) + TailData


# canonical hybrid programs scale repeated paths with distinct internal identities
def EncodeHybCore(
    ModelName: str,
    ConfigName: str,
    CoreItems: tuple[RepeatItem, ...],
) -> Mapping[str, bytes]:
    if len(CoreItems) < 3:
        raise SldprtFormatError("hybrid assembly history requires three occurrences")
    if any(
        not ItemValue.OccurName
        or not ItemValue.ConfigName
        or not PureWindowsPath(ItemValue.CompPath).stem
        for ItemValue in CoreItems
    ):
        raise SldprtFormatError("hybrid assembly fields cannot be empty")
    UniqueItems = _UniqueItems(CoreItems)
    if len(UniqueItems) < 2 or len(UniqueItems) == len(CoreItems):
        raise SldprtFormatError(
            "hybrid assembly history requires shared and distinct component files"
        )
    StreamsMap = {
        "Contents/CMgr": _EncodeCMgr(ModelName, ConfigName, CoreItems),
        "Contents/Config-0": _EncodeConfig(
            ModelName, ConfigName, CoreItems, UniqueItems
        ),
        "Contents/Config-0-ResolvedFeatures": _EncodeResolved(CoreItems, UniqueItems),
        "Contents/Definition": _EmitOps(
            StreamPrograms["Contents/Definition"], {3479: len(CoreItems)}
        ),
        "Contents/Config-0-ModelHeader": _EncodeHeader(
            ModelName, ConfigName, CoreItems, UniqueItems
        ),
    }
    return MappingProxyType(StreamsMap)
