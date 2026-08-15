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
from convert.adapters.solidworks.programs.Common.ProgramContract import (
    BuildOverrides,
    FieldOp,
    FieldOverrides,
)
from convert.adapters.solidworks.programs.Common.FieldEncoder import (
    BuildShiftMap,
    RequireInt,
)

from convert.adapters.solidworks.programs.assembly.mixed.sextuples.Program import (
    EncodeField,
    StreamPrograms,
)
from convert.adapters.solidworks.programs.assembly.default.Repeat import (
    OccurHash,
    RepeatItem,
)
from convert.adapters.solidworks.container.Container import SldprtFormatError


# recovered boundaries separate stable fields from mixed occurrence records
KInsertSpecs = MappingProxyType(
    {
        "Contents/CMgr": (1720, 378),
        "Contents/Config-0": (588, 422),
        "Contents/Config-0-ResolvedFeatures": (755, 56),
        "Contents/Config-0-ModelHeader": (1728, 58),
    }
)

# six traced occurrences provide five canonical mixed record templates
KTracedCount = 6

# three traced component files anchor independent unique file map growth
KTracedUnique = 3

# configuration targets beyond inserted records follow the combined map size
KConfigShiftMap = frozenset(
    {
        297,
        3177,
        4123,
        4621,
        5127,
        5629,
        6143,
        6681,
        7639,
        20167,
        20488,
        21110,
        21250,
        21460,
        21670,
        21882,
        22090,
        22304,
        22524,
        22744,
        23176,
        23186,
        23258,
    }
)

# configuration class targets advance only for new component files
KConfigShiftUniq = frozenset({19463, 19555, 19848, 20169, 20490})

# resolved suffix links span the occurrence and unique file maps together
KResolvedShiftMap = frozenset({1115, 1310, 1344, 2424, 2747, 2990, 3317})

# resolved configuration links follow the complete preceding map growth
KResolvedShiftBase = frozenset({1493, 4069, 4243, 4330})

# resolved component class links advance once for each unique file
KResolvedShiftUniq = frozenset(
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
KHeaderExtStart = 2018

# header external width preserves the first recovered component record
KHeaderExtWidth = 286

# header file start anchors subsequent recovered component records
KHeaderFileStart = 2304

# header file width preserves every subsequent component record
KHeaderFileWidth = 215

# header tail start separates component records from stable fields
KHeaderTailStart = 2734


# operation emission preserves typed ownership while replacing semantic fields
def EncodeOps(
    Operations: Sequence[FieldOp],
    Overrides: FieldOverrides,
    BasePos: int = 0,
    XformPos: int | None = None,
    XformItem: RepeatItem | None = None,
) -> bytes:
    OutputData = bytearray()
    for Operation in Operations:
        StartPos, KindName, DefaultValue = Operation[0], Operation[3], Operation[4]
        RelativePos = StartPos - BasePos
        if XformPos is not None and XformItem is not None:
            if RelativePos == XformPos:
                OutputData.extend(EncodeXform(XformItem))
                continue
            if XformPos < RelativePos <= XformPos + 33:
                continue
        FieldValue = Overrides.get(StartPos - BasePos, DefaultValue)
        OutputData.extend(EncodeField(KindName, FieldValue))
    return bytes(OutputData)


# native transform records need an explicit basis only for rotated occurrences
def EncodeXform(ItemValue: RepeatItem) -> bytes:
    BasisVals = tuple(ItemValue.BasisVals)
    if len(BasisVals) != 9:
        raise SldprtFormatError("native assembly basis requires nine values")
    HasBasis = BasisVals != (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)
    OutputData = bytearray(EncodeField("primitive:uchar", int(HasBasis)))
    if HasBasis:
        for BasisValue in BasisVals:
            OutputData.extend(EncodeField("primitive:double", BasisValue))
    for TransValue in (ItemValue.TransX, ItemValue.TransY, ItemValue.TransZ, 1.0):
        OutputData.extend(EncodeField("primitive:double", TransValue))
    OutputData.extend(EncodeField("primitive:uchar", 0))
    return bytes(OutputData)


# rotated occurrence count drives the enclosing serialized byte length
def CountBasis(CoreItems: tuple[RepeatItem, ...]) -> int:
    IdentityVals = (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)
    return sum(tuple(ItemValue.BasisVals) != IdentityVals for ItemValue in CoreItems)


# logical slicing remains stable when variable strings alter physical widths
def SliceOps(
    StreamName: str,
    StartPos: int,
    EndPos: int | None = None,
) -> tuple[FieldOp, ...]:
    return tuple(
        Operation
        for Operation in StreamPrograms[StreamName]
        if Operation[0] >= StartPos and (EndPos is None or Operation[0] < EndPos)
    )


# windows path keys identify shared component documents case insensitively
def PathKey(PathValue: str) -> str:
    return str(PureWindowsPath(PathValue)).casefold()


# first occurrences define the native external file record order
def UniqueItems(CoreItems: tuple[RepeatItem, ...]) -> tuple[RepeatItem, ...]:
    SeenPaths: set[str] = set()
    DistinctItems: list[RepeatItem] = []
    for ItemValue in CoreItems:
        PathValue = PathKey(ItemValue.CompPath)
        if PathValue in SeenPaths:
            continue
        SeenPaths.add(PathValue)
        DistinctItems.append(ItemValue)
    return tuple(DistinctItems)


# path ordinals reconnect each occurrence to its external file definition
def PathIndex(UniqueItems: tuple[RepeatItem, ...]) -> Mapping[str, int]:
    return MappingProxyType(
        {
            PathKey(ItemValue.CompPath): ItemIndex
            for ItemIndex, ItemValue in enumerate(UniqueItems, 1)
        }
    )


# mixed configuration manager records enumerate every component occurrence
def EncodeCmgr(
    ModelName: str,
    ConfigName: str,
    CoreItems: tuple[RepeatItem, ...],
) -> bytes:
    ItemCount = len(CoreItems)
    DisplayName = f"<{ConfigName}>_Display State 1"
    InsertPos, UnitWidth = KInsertSpecs["Contents/CMgr"]
    PrefixData = EncodeOps(
        SliceOps("Contents/CMgr", 0, InsertPos),
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
        TemplateIndex = min(ItemIndex, KTracedCount)
        UnitStart = InsertPos + ((TemplateIndex - 2) * UnitWidth)
        UnitData.extend(
            EncodeOps(
                SliceOps("Contents/CMgr", UnitStart, UnitStart + UnitWidth),
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
    SuffixStart = InsertPos + ((KTracedCount - 1) * UnitWidth)
    SuffixData = EncodeOps(
        SliceOps("Contents/CMgr", SuffixStart),
        {82: 69 + (8 * (ItemCount - KTracedCount))},
        SuffixStart,
    )
    return PrefixData + bytes(UnitData) + SuffixData


# mixed configuration records bind occurrences to shared component paths
def EncodeConfig(
    ModelName: str,
    CoreItems: tuple[RepeatItem, ...],
    UniqueItems: tuple[RepeatItem, ...],
) -> bytes:
    ItemCount = len(CoreItems)
    UniqueCount = len(UniqueItems)
    OccurShift = ItemCount - KTracedCount
    UniqueShift = UniqueCount - KTracedUnique
    MapShift = (4 * OccurShift) + UniqueShift
    PathMap = PathIndex(UniqueItems)
    InsertPos, UnitWidth = KInsertSpecs["Contents/Config-0"]
    PrefixData = EncodeOps(
        SliceOps("Contents/Config-0", 0, InsertPos),
        {
            18: 2058 + (UnitWidth * ItemCount) + (72 * CountBasis(CoreItems)),
            48: ModelName,
            88: ItemCount,
            109: 4 + UniqueCount,
            111: CoreItems[0].OccurName,
            320: CoreItems[0].ConfigName,
            453: 11 + UniqueCount,
            455: ModelName,
            504: 11 + UniqueCount,
            506: CoreItems[0].OccurName,
            526: 7 + UniqueCount,
        },
        XformPos=275,
        XformItem=CoreItems[0],
    )
    UnitData = bytearray()
    for ItemIndex, ItemValue in enumerate(CoreItems[1:], 2):
        TemplateIndex = min(ItemIndex, KTracedCount)
        UnitStart = InsertPos + ((TemplateIndex - 2) * UnitWidth)
        UnitOps = SliceOps("Contents/Config-0", UnitStart, UnitStart + UnitWidth)
        HashValue = (
            next(
                Operation[4] for Operation in UnitOps if Operation[0] - UnitStart == 153
            )
            if ItemIndex <= KTracedCount
            else OccurHash(ItemValue.OccurName)
        )
        FileIndex = PathMap[PathKey(ItemValue.CompPath)]
        UnitData.extend(
            EncodeOps(
                UnitOps,
                {
                    0: 6 + UniqueCount,
                    2: 4 + UniqueCount,
                    4: ItemValue.OccurName,
                    32: 23 + ItemIndex,
                    153: HashValue,
                    203: 3 + FileIndex,
                    213: ItemValue.ConfigName,
                    261: 14 + ItemIndex,
                    299: 9 + UniqueCount,
                    301: 12 + UniqueCount,
                    303: 13 + UniqueCount,
                    334: 23 + ItemIndex,
                    338: 11 + UniqueCount,
                    340: ItemValue.OccurName,
                    360: 7 + (4 * ItemIndex) + UniqueCount,
                },
                UnitStart,
                168,
                ItemValue,
            )
        )
    SuffixStart = InsertPos + ((KTracedCount - 1) * UnitWidth)
    SuffixOps = SliceOps("Contents/Config-0", SuffixStart)
    SuffixOverrides = BuildShiftMap(
        SuffixOps,
        SuffixStart,
        (
            (KConfigShiftMap, MapShift),
            (KConfigShiftUniq, UniqueShift),
        ),
        "configuration suffix reference",
    )
    SuffixOverrides[23282] = ItemCount
    SuffixData = EncodeOps(SuffixOps, SuffixOverrides, SuffixStart)
    return PrefixData + bytes(UnitData) + SuffixData


# resolved records reconnect occurrence maps and unique component classes
def EncodeResolved(
    CoreItems: tuple[RepeatItem, ...],
    UniqueItems: tuple[RepeatItem, ...],
) -> bytes:
    ItemCount = len(CoreItems)
    UniqueCount = len(UniqueItems)
    OccurShift = ItemCount - KTracedCount
    UniqueShift = UniqueCount - KTracedUnique
    BaseShift = (4 * OccurShift) + UniqueShift
    LinkShift = (8 * OccurShift) + UniqueShift
    ChainShift = (18 * OccurShift) - (10 * UniqueShift)
    InsertPos, UnitWidth = KInsertSpecs["Contents/Config-0-ResolvedFeatures"]
    PrefixData = EncodeOps(
        SliceOps("Contents/Config-0-ResolvedFeatures", 0, InsertPos),
        {
            0: 96 + (4 * ItemCount) + UniqueCount,
            30: 4 + UniqueCount,
            227: 4 + UniqueCount,
            433: 4 + UniqueCount,
            604: ItemCount,
            737: 10 + UniqueCount,
            739: 105 + ChainShift,
        },
    )
    UnitData = bytearray()
    for ItemIndex in range(2, ItemCount + 1):
        TemplateIndex = min(ItemIndex, KTracedCount)
        UnitStart = InsertPos + ((TemplateIndex - 2) * UnitWidth)
        UnitOps = SliceOps(
            "Contents/Config-0-ResolvedFeatures",
            UnitStart,
            UnitStart + UnitWidth,
        )
        RefValues = {
            Operation[0]
            - UnitStart: RequireInt(Operation[4], "resolved unit reference")
            + BaseShift
            for Operation in UnitOps
            if Operation[3] == "classref"
        }
        UnitData.extend(
            EncodeOps(
                UnitOps,
                {
                    **RefValues,
                    38: 9 + (4 * ItemIndex) + UniqueCount,
                    40: (40 + (18 * ItemCount) - (10 * UniqueCount) - (13 * ItemIndex)),
                },
                UnitStart,
            )
        )
    SuffixStart = InsertPos + ((KTracedCount - 1) * UnitWidth)
    SuffixOps = SliceOps("Contents/Config-0-ResolvedFeatures", SuffixStart)
    SuffixOverrides = BuildShiftMap(
        SuffixOps,
        SuffixStart,
        (
            (KResolvedShiftMap, LinkShift),
            (KResolvedShiftBase, BaseShift),
            (KResolvedShiftUniq, UniqueShift),
        ),
        "resolved suffix reference",
    )
    SuffixData = EncodeOps(SuffixOps, SuffixOverrides, SuffixStart)
    return PrefixData + bytes(UnitData) + SuffixData


# model header records separate occurrence stamps from shared component files
def EncodeHeader(
    ModelName: str,
    ConfigName: str,
    CoreItems: tuple[RepeatItem, ...],
    UniqueItems: tuple[RepeatItem, ...],
) -> bytes:
    ItemCount = len(CoreItems)
    UniqueCount = len(UniqueItems)
    PathCounts = Counter(PathKey(ItemValue.CompPath) for ItemValue in CoreItems)
    InsertPos, UnitWidth = KInsertSpecs["Contents/Config-0-ModelHeader"]
    PrefixData = EncodeOps(
        SliceOps("Contents/Config-0-ModelHeader", 0, InsertPos),
        {
            77: 23 + ItemCount,
            142: ModelName,
            1708: CoreItems[0].OccurName,
        },
    )
    OccurData = bytearray()
    for ItemIndex, ItemValue in enumerate(CoreItems[1:], 2):
        TemplateIndex = min(ItemIndex, KTracedCount)
        UnitStart = InsertPos + ((TemplateIndex - 2) * UnitWidth)
        OccurData.extend(
            EncodeOps(
                SliceOps(
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
    ExtOverrides = BuildOverrides(
        {
            4: 24 + ItemCount,
            31: UniqueCount,
            75: FirstItem.CompPath,
            211: 64 + (2 * ItemCount),
            213: FirstStem,
            254: PathCounts[PathKey(FirstItem.CompPath)],
        }
    )
    if FirstItem.FileStamp > 0:
        ExtOverrides[232] = FirstItem.FileStamp
    ExtPrefix = EncodeOps(
        SliceOps(
            "Contents/Config-0-ModelHeader",
            KHeaderExtStart,
            KHeaderExtStart + KHeaderExtWidth,
        ),
        ExtOverrides,
        KHeaderExtStart,
    )
    FileData = bytearray()
    for FileIndex, ItemValue in enumerate(UniqueItems[1:], 2):
        TemplateIndex = min(FileIndex, KTracedUnique)
        FileStart = KHeaderFileStart + ((TemplateIndex - 2) * KHeaderFileWidth)
        FileStem = PureWindowsPath(ItemValue.CompPath).stem
        FileOverrides = BuildOverrides(
            {
                0: 62 + (2 * ItemCount),
                2: 64 + (2 * ItemCount),
                4: ItemValue.CompPath,
                140: 64 + (2 * ItemCount),
                142: FileStem,
                183: PathCounts[PathKey(ItemValue.CompPath)],
                191: FileIndex - 1,
            }
        )
        if ItemValue.FileStamp > 0:
            FileOverrides[161] = ItemValue.FileStamp
        FileData.extend(
            EncodeOps(
                SliceOps(
                    "Contents/Config-0-ModelHeader",
                    FileStart,
                    FileStart + KHeaderFileWidth,
                ),
                FileOverrides,
                FileStart,
            )
        )
    TailData = EncodeOps(
        SliceOps("Contents/Config-0-ModelHeader", KHeaderTailStart),
        {
            0: 103 + (2 * ItemCount),
            4: 62 + (2 * ItemCount),
            6: 64 + (2 * ItemCount),
            12: 64 + (2 * ItemCount),
            14: ModelName,
            67: ConfigName,
            131: ItemCount,
        },
        KHeaderTailStart,
    )
    return PrefixData + bytes(OccurData) + ExtPrefix + bytes(FileData) + TailData


# legacy aliases preserve recovered mixed helpers and existing external callers
InsertSpecs = KInsertSpecs
TracedCount = KTracedCount
TracedUnique = KTracedUnique
ConfigShiftMap = KConfigShiftMap
ConfigShiftUniq = KConfigShiftUniq
ResolvedShiftMap = KResolvedShiftMap
ResolvedShiftBase = KResolvedShiftBase
ResolvedShiftUniq = KResolvedShiftUniq
HeaderExtStart = KHeaderExtStart
HeaderExtWidth = KHeaderExtWidth
HeaderFileStart = KHeaderFileStart
HeaderFileWidth = KHeaderFileWidth
HeaderTailStart = KHeaderTailStart
_EmitOps = EncodeOps
_SliceOps = SliceOps
_PathKey = PathKey
_UniqueItems = UniqueItems
_PathIndex = PathIndex
_EncodeCMgr = EncodeCmgr
_EncodeConfig = EncodeConfig
_EncodeResolved = EncodeResolved
_EncodeHeader = EncodeHeader


# canonical mixed programs scale repeated paths without opaque vendor payloads
def EncodeMixCore(
    ModelName: str,
    ConfigName: str,
    CoreItems: tuple[RepeatItem, ...],
) -> Mapping[str, bytes]:
    if len(CoreItems) < 3:
        raise SldprtFormatError("mixed assembly history requires three occurrences")
    if any(
        not ItemValue.OccurName
        or not ItemValue.ConfigName
        or not PureWindowsPath(ItemValue.CompPath).stem
        for ItemValue in CoreItems
    ):
        raise SldprtFormatError("mixed assembly fields cannot be empty")
    UniqueValues = UniqueItems(CoreItems)
    if len(UniqueValues) < 2 or len(UniqueValues) == len(CoreItems):
        raise SldprtFormatError(
            "mixed assembly history requires shared and distinct component files"
        )
    StreamsMap = {
        "Contents/CMgr": EncodeCmgr(ModelName, ConfigName, CoreItems),
        "Contents/Config-0": EncodeConfig(ModelName, CoreItems, UniqueValues),
        "Contents/Config-0-ResolvedFeatures": EncodeResolved(CoreItems, UniqueValues),
        "Contents/Definition": EncodeOps(
            StreamPrograms["Contents/Definition"], {3479: len(CoreItems)}
        ),
        "Contents/Config-0-ModelHeader": EncodeHeader(
            ModelName, ConfigName, CoreItems, UniqueValues
        ),
    }
    return MappingProxyType(StreamsMap)
