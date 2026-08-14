# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import PureWindowsPath
from types import MappingProxyType
from typing import Any as AnyValue

from convert.adapters.solidworks.programs.assembly.distinct.quintuples.Program import EncodeField, StreamPrograms
from convert.adapters.solidworks.programs.assembly.default.Repeat import (
    IsIdentityBasis,
    OccurHash,
    RepeatItem,
)
from convert.adapters.solidworks.container.Container import SldprtFormatError


# recovered boundaries separate stable fields from unique component records
KInsertSpecs = MappingProxyType(
    {
        "Contents/CMgr": (1720, 378),
        "Contents/Config-0": (668, 502),
        "Contents/Config-0-ResolvedFeatures": (755, 56),
        "Contents/Config-0-ModelHeader": (1728, 58),
    }
)

# five traced component files provide four canonical record templates
KTracedCount = 5

# config suffix targets advance five map entries per unique component file
KConfigShiftFive = frozenset(
    {
        297,
        3337,
        4283,
        4781,
        5287,
        5789,
        6303,
        6841,
        7799,
        20327,
        20648,
        21270,
        21410,
        21620,
        21830,
        22042,
        22250,
        22464,
        22684,
        22904,
        23336,
        23346,
        23418,
    }
)

# config class targets advance once for each new external component class
KConfigShiftOne = frozenset({19623, 19715, 20008, 20329, 20650})

# resolved suffix links span both five entry base and four entry occurrence maps
KResolvedShiftNine = frozenset({1115, 1310, 1344, 2424, 2747, 2990, 3317})

# resolved suffix links into the configuration base advance five entries
KResolvedShiftFive = frozenset({1493, 4069, 4243, 4330})

# resolved component class links advance once per unique external file
KResolvedShiftOne = frozenset(
    {
        28,
        241,
        439,
        658,
        864,
        948,
        1117,
        1520,
        1710,
        1903,
        2426,
        2992,
        3590,
        4512,
    }
)

# header external start separates occurrence stamps from component records
KHeaderExtStart = 1960

# header external width preserves each recovered component reference record
KHeaderExtWidth = 286

# header file start anchors the first recovered external document record
KHeaderFileStart = 2246

# header file width preserves each recovered external document record
KHeaderFileWidth = 215

# header tail start separates component files from stable trailing fields
KHeaderTailStart = 3106


# operation emission preserves typed ownership while applying semantic values
def EncodeOps(
    Operations: Sequence[tuple[int, int, int, str, AnyValue]],
    Overrides: Mapping[int, AnyValue],
    BasePos: int = 0,
    BasisValues: Mapping[int, tuple[float, ...]] | None = None,
) -> bytes:
    OutputData = bytearray()
    BasisMap = BasisValues or {}
    for StartPos, FieldWidth, OwnerIndex, KindName, DefaultValue in Operations:
        FieldValue = Overrides.get(StartPos - BasePos, DefaultValue)
        OutputData.extend(EncodeField(KindName, FieldValue))
        BasisValue = BasisMap.get(StartPos - BasePos)
        if BasisValue is not None:
            if KindName != "primitive:uchar" or FieldValue != 1:
                raise SldprtFormatError("assembly transform basis marker is invalid")
            OutputData.extend(EncodeField("direct:9d", BasisValue))
    return bytes(OutputData)


# logical slicing remains stable when semantic strings change byte width
def SliceOps(
    StreamName: str,
    StartPos: int,
    EndPos: int | None = None,
) -> tuple[tuple[int, int, int, str, AnyValue], ...]:
    return tuple(
        Operation
        for Operation in StreamPrograms[StreamName]
        if Operation[0] >= StartPos and (EndPos is None or Operation[0] < EndPos)
    )


# windows path keys identify repeated component documents case insensitively
def PathKey(PathValue: str) -> str:
    return str(PureWindowsPath(PathValue)).casefold()


# first occurrences define the external file record order independently
def UniqueItems(CoreItems: tuple[RepeatItem, ...]) -> tuple[RepeatItem, ...]:
    SeenPaths: set[str] = set()
    UniqueItems: list[RepeatItem] = []
    for ItemValue in CoreItems:
        PathValue = _PathKey(ItemValue.CompPath)
        if PathValue in SeenPaths:
            continue
        SeenPaths.add(PathValue)
        UniqueItems.append(ItemValue)
    return tuple(UniqueItems)


# distinct configuration manager records enumerate every component occurrence
def EncodeCmgr(
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
            1617: ConfigName,
            1655: ConfigName,
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


# distinct configuration records bind paths identities and placements
def EncodeConfig(
    ModelName: str,
    ConfigName: str,
    CoreItems: tuple[RepeatItem, ...],
) -> bytes:
    ItemCount = len(CoreItems)
    BasisCount = sum(
        not _IsIdentityBasis(ItemValue.BasisVals) for ItemValue in CoreItems
    )
    BaseShift = ItemCount - TracedCount
    InsertPos, UnitWidth = InsertSpecs["Contents/Config-0"]
    PrefixData = _EmitOps(
        _SliceOps("Contents/Config-0", 0, InsertPos),
        {
            18: 2218 + (UnitWidth * ItemCount) + (72 * BasisCount),
            48: ModelName,
            88: ItemCount,
            109: 9 + BaseShift,
            111: CoreItems[0].OccurName,
            400: ConfigName,
            533: 16 + BaseShift,
            535: ModelName,
            584: 16 + BaseShift,
            586: CoreItems[0].OccurName,
            606: 12 + BaseShift,
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
        UnitData.extend(
            _EmitOps(
                UnitOps,
                {
                    0: 11 + BaseShift,
                    2: 9 + BaseShift,
                    4: ItemValue.OccurName,
                    32: 23 + ItemIndex,
                    153: HashValue,
                    169: ItemValue.TransX,
                    177: ItemValue.TransY,
                    185: ItemValue.TransZ,
                    283: 3 + ItemIndex,
                    293: ItemValue.ConfigName,
                    341: 14 + ItemIndex,
                    379: 14 + BaseShift,
                    381: 17 + BaseShift,
                    383: 18 + BaseShift,
                    414: 23 + ItemIndex,
                    418: 16 + BaseShift,
                    420: ItemValue.OccurName,
                    440: 12 + (4 * ItemIndex) + BaseShift,
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
        if RelativePos in ConfigShift5:
            SuffixOverrides[RelativePos] = DefaultValue + (5 * BaseShift)
        elif RelativePos in ConfigShift1:
            SuffixOverrides[RelativePos] = DefaultValue + BaseShift
    SuffixOverrides[23442] = ItemCount
    SuffixData = _EmitOps(SuffixOps, SuffixOverrides, SuffixStart)
    return PrefixData + bytes(UnitData) + SuffixData


# resolved records reconnect every inserted occurrence to shifted feature maps
def EncodeResolved(CoreItems: tuple[RepeatItem, ...]) -> bytes:
    ItemCount = len(CoreItems)
    BaseShift = ItemCount - TracedCount
    InsertPos, UnitWidth = InsertSpecs["Contents/Config-0-ResolvedFeatures"]
    PrefixData = _EmitOps(
        _SliceOps("Contents/Config-0-ResolvedFeatures", 0, InsertPos),
        {
            0: 96 + (5 * ItemCount),
            30: 9 + BaseShift,
            227: 9 + BaseShift,
            433: 9 + BaseShift,
            604: ItemCount,
            737: 15 + BaseShift,
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
            StartPos - UnitStart: DefaultValue + (5 * BaseShift)
            for StartPos, _Width, _Owner, KindName, DefaultValue in UnitOps
            if KindName == "classref"
        }
        UnitData.extend(
            _EmitOps(
                UnitOps,
                {
                    **RefValues,
                    38: 14 + (4 * ItemIndex) + BaseShift,
                    40: 33 + (13 * (ItemCount - ItemIndex)),
                },
                UnitStart,
            )
        )
    SuffixStart = InsertPos + ((TracedCount - 1) * UnitWidth)
    SuffixOps = _SliceOps("Contents/Config-0-ResolvedFeatures", SuffixStart)
    SuffixOverrides: dict[int, Any] = {}
    for StartPos, _Width, _Owner, _Kind, DefaultValue in SuffixOps:
        RelativePos = StartPos - SuffixStart
        if RelativePos in ResolvedShift9:
            SuffixOverrides[RelativePos] = DefaultValue + (9 * BaseShift)
        elif RelativePos in ResolvedShift5:
            SuffixOverrides[RelativePos] = DefaultValue + (5 * BaseShift)
        elif RelativePos in ResolvedShift1:
            SuffixOverrides[RelativePos] = DefaultValue + BaseShift
    SuffixData = _EmitOps(SuffixOps, SuffixOverrides, SuffixStart)
    return PrefixData + bytes(UnitData) + SuffixData


# model header records enumerate occurrences and their independent part files
def EncodeHeader(
    ModelName: str,
    ConfigName: str,
    CoreItems: tuple[RepeatItem, ...],
) -> bytes:
    ItemCount = len(CoreItems)
    UniqueItems = _UniqueItems(CoreItems)
    UniqueCount = len(UniqueItems)
    BaseShift = ItemCount - TracedCount
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
        211: 74 + (2 * BaseShift),
        213: FirstStem,
    }
    if FirstItem.FileStamp > 0:
        ExtOverrides[232] = FirstItem.FileStamp
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
        TemplateIndex = min(FileIndex, TracedCount)
        FileStart = HeaderFileStart + ((TemplateIndex - 2) * HeaderFileWidth)
        FileStem = PureWindowsPath(ItemValue.CompPath).stem
        FileOverrides = {
            0: 72 + (2 * BaseShift),
            2: 74 + (2 * BaseShift),
            4: ItemValue.CompPath,
            140: 74 + (2 * BaseShift),
            142: FileStem,
            191: FileIndex - 1,
        }
        if ItemValue.FileStamp > 0:
            FileOverrides[161] = ItemValue.FileStamp
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
            4: 72 + (2 * BaseShift),
            6: 74 + (2 * BaseShift),
            12: 74 + (2 * BaseShift),
            14: ModelName,
            67: ConfigName,
            131: ItemCount,
        },
        HeaderTailStart,
    )
    return PrefixData + bytes(OccurData) + ExtPrefix + bytes(FileData) + TailData


# canonical distinct path programs scale independent component files without donors
def EncodePathCore(
    ModelName: str,
    ConfigName: str,
    CoreItems: tuple[RepeatItem, ...],
) -> Mapping[str, bytes]:
    if len(CoreItems) < 3:
        raise SldprtFormatError("distinct assembly history requires three components")
    CompPaths = tuple(ItemValue.CompPath for ItemValue in CoreItems)
    if any(not PureWindowsPath(ItemPath).stem for ItemPath in CompPaths):
        raise SldprtFormatError("distinct assembly component path has no stem")
    StreamsMap = {
        "Contents/CMgr": _EncodeCMgr(ModelName, ConfigName, CoreItems),
        "Contents/Config-0": _EncodeConfig(ModelName, ConfigName, CoreItems),
        "Contents/Config-0-ResolvedFeatures": _EncodeResolved(CoreItems),
        "Contents/Definition": _EmitOps(
            StreamPrograms["Contents/Definition"], {3479: len(CoreItems)}
        ),
        "Contents/Config-0-ModelHeader": _EncodeHeader(
            ModelName, ConfigName, CoreItems
        ),
    }
    return MappingProxyType(StreamsMap)
