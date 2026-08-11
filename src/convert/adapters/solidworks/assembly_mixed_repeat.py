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

from .assembly_mixed6_programs import EncodeField, StreamPrograms
from .assembly_repeat import RepeatItem, _OccurHash
from .container import SldprtFormatError


# recovered boundaries separate stable fields from mixed occurrence records
InsertSpecs = MappingProxyType(
    {
        "Contents/CMgr": (1720, 378),
        "Contents/Config-0": (588, 422),
        "Contents/Config-0-ResolvedFeatures": (755, 56),
        "Contents/Config-0-ModelHeader": (1728, 58),
    }
)

# six traced occurrences provide five canonical mixed record templates
TracedCount = 6

# three traced component files anchor independent unique-file map growth
TracedUnique = 3

# configuration targets beyond inserted records follow the combined map size
ConfigShiftMap = frozenset(
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
ConfigShiftUniq = frozenset({19463, 19555, 19848, 20169, 20490})

# resolved suffix links span the occurrence and unique-file maps together
ResolvedShiftMap = frozenset({1115, 1310, 1344, 2424, 2747, 2990, 3317})

# resolved configuration links follow the complete preceding map growth
ResolvedShiftBase = frozenset({1493, 4069, 4243, 4330})

# resolved component-class links advance once for each unique file
ResolvedShiftUniq = frozenset(
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

# header boundaries isolate occurrence stamps and unique external-file records
HeaderExtStart = 2018
HeaderExtWidth = 286
HeaderFileStart = 2304
HeaderFileWidth = 215
HeaderTailStart = 2734


# operation emission preserves typed ownership while replacing semantic fields
def _EmitOps(
    Operations: Sequence[tuple[int, int, int, str, Any]],
    Overrides: Mapping[int, Any],
    BasePos: int = 0,
) -> bytes:
    OutputData = bytearray()
    for StartPos, _FieldWidth, _OwnerIndex, KindName, DefaultValue in Operations:
        FieldValue = Overrides.get(StartPos - BasePos, DefaultValue)
        OutputData.extend(EncodeField(KindName, FieldValue))
    return bytes(OutputData)


# logical slicing remains stable when variable strings alter physical widths
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


# windows path keys identify shared component documents case-insensitively
def _PathKey(PathValue: str) -> str:
    return str(PureWindowsPath(PathValue)).casefold()


# first occurrences define the native external-file record order
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


# path ordinals reconnect each occurrence to its external-file definition
def _PathIndex(UniqueItems: tuple[RepeatItem, ...]) -> Mapping[str, int]:
    return MappingProxyType(
        {
            _PathKey(ItemValue.CompPath): ItemIndex
            for ItemIndex, ItemValue in enumerate(UniqueItems, 1)
        }
    )


# mixed configuration-manager records enumerate every component occurrence
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
        {82: 69 + (8 * (ItemCount - TracedCount))},
        SuffixStart,
    )
    return PrefixData + bytes(UnitData) + SuffixData


# mixed configuration records bind occurrences to shared component paths
def _EncodeConfig(
    ModelName: str,
    CoreItems: tuple[RepeatItem, ...],
    UniqueItems: tuple[RepeatItem, ...],
) -> bytes:
    ItemCount = len(CoreItems)
    UniqueCount = len(UniqueItems)
    OccurShift = ItemCount - TracedCount
    UniqueShift = UniqueCount - TracedUnique
    MapShift = (4 * OccurShift) + UniqueShift
    PathIndex = _PathIndex(UniqueItems)
    InsertPos, UnitWidth = InsertSpecs["Contents/Config-0"]
    PrefixData = _EmitOps(
        _SliceOps("Contents/Config-0", 0, InsertPos),
        {
            18: 2058 + (UnitWidth * ItemCount),
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
                    185: ItemValue.TransZ - 0.005,
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
            )
        )
    SuffixStart = InsertPos + ((TracedCount - 1) * UnitWidth)
    SuffixOps = _SliceOps("Contents/Config-0", SuffixStart)
    SuffixOverrides: dict[int, Any] = {}
    for StartPos, _Width, _Owner, _Kind, DefaultValue in SuffixOps:
        RelativePos = StartPos - SuffixStart
        if RelativePos in ConfigShiftMap:
            SuffixOverrides[RelativePos] = DefaultValue + MapShift
        elif RelativePos in ConfigShiftUniq:
            SuffixOverrides[RelativePos] = DefaultValue + UniqueShift
    SuffixOverrides[23282] = ItemCount
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
    BaseShift = (4 * OccurShift) + UniqueShift
    LinkShift = (8 * OccurShift) + UniqueShift
    ChainShift = (18 * OccurShift) - (10 * UniqueShift)
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
            739: 105 + ChainShift,
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
            StartPos - UnitStart: DefaultValue + BaseShift
            for StartPos, _Width, _Owner, KindName, DefaultValue in UnitOps
            if KindName == "classref"
        }
        UnitData.extend(
            _EmitOps(
                UnitOps,
                {
                    **RefValues,
                    38: 9 + (4 * ItemIndex) + UniqueCount,
                    40: (40 + (18 * ItemCount) - (10 * UniqueCount) - (13 * ItemIndex)),
                },
                UnitStart,
            )
        )
    SuffixStart = InsertPos + ((TracedCount - 1) * UnitWidth)
    SuffixOps = _SliceOps("Contents/Config-0-ResolvedFeatures", SuffixStart)
    SuffixOverrides: dict[int, Any] = {}
    for StartPos, _Width, _Owner, _Kind, DefaultValue in SuffixOps:
        RelativePos = StartPos - SuffixStart
        if RelativePos in ResolvedShiftMap:
            SuffixOverrides[RelativePos] = DefaultValue + LinkShift
        elif RelativePos in ResolvedShiftBase:
            SuffixOverrides[RelativePos] = DefaultValue + BaseShift
        elif RelativePos in ResolvedShiftUniq:
            SuffixOverrides[RelativePos] = DefaultValue + UniqueShift
    SuffixData = _EmitOps(SuffixOps, SuffixOverrides, SuffixStart)
    return PrefixData + bytes(UnitData) + SuffixData


# model-header records separate occurrence stamps from shared component files
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
        211: 64 + (2 * ItemCount),
        213: FirstStem,
        254: PathCounts[_PathKey(FirstItem.CompPath)],
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
        TemplateIndex = min(FileIndex, TracedUnique)
        FileStart = HeaderFileStart + ((TemplateIndex - 2) * HeaderFileWidth)
        FileStem = PureWindowsPath(ItemValue.CompPath).stem
        FileOverrides = {
            0: 62 + (2 * ItemCount),
            2: 64 + (2 * ItemCount),
            4: ItemValue.CompPath,
            140: 64 + (2 * ItemCount),
            142: FileStem,
            183: PathCounts[_PathKey(ItemValue.CompPath)],
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
    UniqueItems = _UniqueItems(CoreItems)
    if len(UniqueItems) < 2 or len(UniqueItems) == len(CoreItems):
        raise SldprtFormatError(
            "mixed assembly history requires shared and distinct component files"
        )
    StreamsMap = {
        "Contents/CMgr": _EncodeCMgr(ModelName, ConfigName, CoreItems),
        "Contents/Config-0": _EncodeConfig(ModelName, CoreItems, UniqueItems),
        "Contents/Config-0-ResolvedFeatures": _EncodeResolved(CoreItems, UniqueItems),
        "Contents/Definition": _EmitOps(
            StreamPrograms["Contents/Definition"], {3479: len(CoreItems)}
        ),
        "Contents/Config-0-ModelHeader": _EncodeHeader(
            ModelName, ConfigName, CoreItems, UniqueItems
        ),
    }
    return MappingProxyType(StreamsMap)
