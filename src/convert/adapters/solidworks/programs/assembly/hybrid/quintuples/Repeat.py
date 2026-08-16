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

from convert.adapters.solidworks.programs.assembly.distinct.default.Repeat import (
    KConfigShiftFive as ConfigShiftMap,
    KConfigShiftOne as ConfigShiftUnique,
    KResolvedShiftFive as ResolvedShiftMap,
    KResolvedShiftNine as ResolvedShiftLink,
    KResolvedShiftOne as ResolvedShiftUnique,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Program import (
    EncodeField,
    StreamPrograms,
)
from convert.adapters.solidworks.programs.assembly.default.Repeat import (
    IsIdentityBasis,
    OccurHash,
    RepeatItem,
)
from convert.adapters.solidworks.container.Container import SldprtFormatError


# recovered boundaries separate stable fields from hybrid occurrence records
KInsertSpecs = MappingProxyType(
    {
        "Contents/CMgr": (1720, 378),
        "Contents/Config-0": (668, 502),
        "Contents/Config-0-ResolvedFeatures": (755, 56),
        "Contents/Config-0-ModelHeader": (1728, 58),
    }
)

# five traced occurrences isolate occurrence growth from file class growth
KTracedCount = 5

# three traced component files anchor the independent unique file dimension
KTracedUnique = 3

# header external start separates occurrences from the first component file
KHeaderExtStart = 1960

# the first file record includes the external object list framing
KHeaderExtWidth = 300

# subsequent file records share one fixed typed field sequence
KHeaderFileStart = 2260

# equal width oracle paths expose the physical repeated file record boundary
KHeaderFileWidth = 229

# the stable header tail follows the two traced subsequent file records
KHeaderTailStart = 2718


# operation emission preserves typed ownership while applying semantic values
def EncodeOps(
    Operations: Sequence[FieldOp],
    Overrides: FieldOverrides,
    BasePos: int = 0,
    BasisValues: Mapping[int, tuple[float, ...]] | None = None,
) -> bytes:
    OutputData = bytearray()
    BasisMap = BasisValues or {}
    for Operation in Operations:
        StartPos, KindName, DefaultValue = Operation[0], Operation[3], Operation[4]
        FieldValue = Overrides.get(StartPos - BasePos, DefaultValue)
        OutputData.extend(EncodeField(KindName, FieldValue))
        BasisValue = BasisMap.get(StartPos - BasePos)
        if BasisValue is not None:
            if KindName != "primitive:uchar" or FieldValue != 1:
                raise SldprtFormatError("assembly transform basis marker is invalid")
            OutputData.extend(EncodeField("direct:9d", BasisValue))
    return bytes(OutputData)


# logical slicing remains stable when semantic strings change physical width
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


# windows path keys identify repeated component documents case insensitively
def PathKey(PathValue: str) -> str:
    return str(PureWindowsPath(PathValue)).casefold()


# first occurrences define unique component file ordering independently
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


# path ordinals reconnect every occurrence to its unique external file
def PathIndex(UniqueItems: tuple[RepeatItem, ...]) -> Mapping[str, int]:
    return MappingProxyType(
        {
            PathKey(ItemValue.CompPath): ItemIndex
            for ItemIndex, ItemValue in enumerate(UniqueItems, 1)
        }
    )


# hybrid configuration manager records enumerate every component occurrence
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
        {82: 61 + (8 * (ItemCount - KTracedCount))},
        SuffixStart,
    )
    return PrefixData + bytes(UnitData) + SuffixData


# hybrid configuration records bind occurrence maps to unique file classes
def EncodeConfig(
    ModelName: str,
    ConfigName: str,
    CoreItems: tuple[RepeatItem, ...],
    UniqueItems: tuple[RepeatItem, ...],
) -> bytes:
    ItemCount = len(CoreItems)
    BasisCount = sum(
        not IsIdentityBasis(ItemValue.BasisVals) for ItemValue in CoreItems
    )
    UniqueCount = len(UniqueItems)
    OccurShift = ItemCount - KTracedCount
    UniqueShift = UniqueCount - KTracedUnique
    MapShift = (4 * OccurShift) + UniqueShift
    PathMap = PathIndex(UniqueItems)
    InsertPos, UnitWidth = KInsertSpecs["Contents/Config-0"]
    PrefixData = EncodeOps(
        SliceOps("Contents/Config-0", 0, InsertPos),
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
            **({275: 1} if not IsIdentityBasis(CoreItems[0].BasisVals) else {}),
        },
        BasisValues=(
            {275: CoreItems[0].BasisVals}
            if not IsIdentityBasis(CoreItems[0].BasisVals)
            else None
        ),
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
                    **({168: 1} if not IsIdentityBasis(ItemValue.BasisVals) else {}),
                },
                UnitStart,
                (
                    {168: ItemValue.BasisVals}
                    if not IsIdentityBasis(ItemValue.BasisVals)
                    else None
                ),
            )
        )
    SuffixStart = InsertPos + ((KTracedCount - 1) * UnitWidth)
    SuffixOps = SliceOps("Contents/Config-0", SuffixStart)
    SuffixOverrides = BuildShiftMap(
        SuffixOps,
        SuffixStart,
        (
            (ConfigShiftMap, MapShift),
            (ConfigShiftUnique, UniqueShift),
        ),
        "configuration suffix reference",
    )
    SuffixOverrides[23442] = ItemCount
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
    MapShift = (4 * OccurShift) + UniqueShift
    LinkShift = (8 * OccurShift) + UniqueShift
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
            739: 20 + (13 * ItemCount),
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
            + MapShift
            for Operation in UnitOps
            if Operation[3] == "classref"
        }
        UnitData.extend(
            EncodeOps(
                UnitOps,
                {
                    **RefValues,
                    38: 9 + (4 * ItemIndex) + UniqueCount,
                    40: 32 + (13 * (ItemCount - ItemIndex)) + (ItemIndex % 2),
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
            (ResolvedShiftLink, LinkShift),
            (ResolvedShiftMap, MapShift),
            (ResolvedShiftUnique, UniqueShift),
        ),
        "resolved suffix reference",
    )
    SuffixData = EncodeOps(SuffixOps, SuffixOverrides, SuffixStart)
    return PrefixData + bytes(UnitData) + SuffixData


# model header records separate occurrence stamps from unique component files
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
            225: 64 + (2 * ItemCount),
            227: FirstStem,
            268: PathCounts[PathKey(FirstItem.CompPath)],
        }
    )
    if FirstItem.FileStamp > 0:
        ExtOverrides[246] = FirstItem.FileStamp
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
                154: 64 + (2 * ItemCount),
                156: FileStem,
                197: PathCounts[PathKey(ItemValue.CompPath)],
                205: FileIndex - 1,
            }
        )
        if ItemValue.FileStamp > 0:
            FileOverrides[175] = ItemValue.FileStamp
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


# legacy aliases preserve recovered hybrid helpers and existing external callers
InsertSpecs = KInsertSpecs
TracedCount = KTracedCount
TracedUnique = KTracedUnique
HeaderExtStart = KHeaderExtStart
HeaderExtWidth = KHeaderExtWidth
HeaderFileStart = KHeaderFileStart
HeaderFileWidth = KHeaderFileWidth
HeaderTailStart = KHeaderTailStart
_EmitOps = EncodeOps  # lgtm[py/unused-global-variable]
_SliceOps = SliceOps  # lgtm[py/unused-global-variable]
_PathKey = PathKey  # lgtm[py/unused-global-variable]
_UniqueItems = UniqueItems  # lgtm[py/unused-global-variable]
_PathIndex = PathIndex  # lgtm[py/unused-global-variable]
_EncodeCMgr = EncodeCmgr  # lgtm[py/unused-global-variable]
_EncodeConfig = EncodeConfig  # lgtm[py/unused-global-variable]
_EncodeResolved = EncodeResolved  # lgtm[py/unused-global-variable]
_EncodeHeader = EncodeHeader  # lgtm[py/unused-global-variable]


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
    UniqueValues = UniqueItems(CoreItems)
    if len(UniqueValues) < 2 or len(UniqueValues) == len(CoreItems):
        raise SldprtFormatError(
            "hybrid assembly history requires shared and distinct component files"
        )
    StreamsMap = {
        "Contents/CMgr": EncodeCmgr(ModelName, ConfigName, CoreItems),
        "Contents/Config-0": EncodeConfig(
            ModelName, ConfigName, CoreItems, UniqueValues
        ),
        "Contents/Config-0-ResolvedFeatures": EncodeResolved(CoreItems, UniqueValues),
        "Contents/Definition": EncodeOps(
            StreamPrograms["Contents/Definition"], {3479: len(CoreItems)}
        ),
        "Contents/Config-0-ModelHeader": EncodeHeader(
            ModelName, ConfigName, CoreItems, UniqueValues
        ),
    }
    return MappingProxyType(StreamsMap)
