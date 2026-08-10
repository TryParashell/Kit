# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

import binascii
from collections.abc import Mapping, Sequence
from pathlib import PureWindowsPath
from types import MappingProxyType
from typing import Any

from .assembly5_programs import EncodeField, StreamPrograms
from .container import SldprtFormatError


# recovered insertion boundaries split stable fields from occurrence records
InsertSpecs = MappingProxyType(
    {
        "Contents/CMgr": (1766, 424),
        "Contents/Config-0": (760, 594),
        "Contents/Config-0-ResolvedFeatures": (755, 56),
        "Contents/Config-0-ModelHeader": (1774, 104),
    }
)

# five traced occurrences provide four complete canonical repeat templates
TracedCount = 5

# config suffix references advance four map entries for every occurrence
ConfigShiftRefs = frozenset(
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

# resolved suffix targets after insertion advance eight combined map entries
ResolvedShift8 = frozenset({1115, 1310, 1344, 2424, 2747, 2990, 3317})

# resolved suffix targets before insertion advance by the four-entry base map
ResolvedShift4 = frozenset({1493, 4069, 4243, 4330})

# header suffix references advance two map entries for every occurrence stamp
HeaderShiftRefs = frozenset({257, 382, 384, 390})


# one repeated item supplies semantic identity and display translation fields
class RepeatItem:
    __slots__ = (
        "OccurName",
        "CompPath",
        "TransX",
        "TransY",
        "TransZ",
        "ConfigName",
    )

    # immutable initialization keeps one occurrence coherent across all streams
    def __init__(
        self,
        OccurName: str,
        CompPath: str,
        TransX: float = 0.0,
        TransY: float = 0.0,
        TransZ: float = 0.0,
        ConfigName: str = "Default",
    ) -> None:
        self.OccurName = OccurName
        self.CompPath = CompPath
        self.TransX = TransX
        self.TransY = TransY
        self.TransZ = TransZ
        self.ConfigName = ConfigName


# one operation tuple retains its typed serializer owner and native field value
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


# logical slicing ignores variable string widths while preserving field order
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


# stable occurrence hashes give later records unique recovered identifier fields
def _OccurHash(OccurName: str) -> int:
    CheckValue = binascii.crc32(OccurName.encode("utf-16le")) & 0x0FFFFFFF
    return 0x50000000 | CheckValue


# repeated configuration-manager objects advance eight archive map entries
def _EncodeCMgr(
    ModelName: str,
    ConfigName: str,
    CoreItems: tuple[RepeatItem, ...],
) -> bytes:
    ItemCount = len(CoreItems)
    DisplayName = f"<{ConfigName}>_Display State 1"
    PrefixOps = _SliceOps("Contents/CMgr", 0, InsertSpecs["Contents/CMgr"][0])
    PrefixData = _EmitOps(
        PrefixOps,
        {
            0x00CE: ConfigName,
            0x04D9: DisplayName,
            0x05B8: ModelName,
            0x05EB: CoreItems[0].OccurName,
            0x067F: ConfigName,
            0x06A5: ConfigName,
            365: ItemCount,
            377: 23 + ItemCount,
            381: 103 + (2 * ItemCount),
            1031: ItemCount + 1,
        },
    )
    InsertPos, UnitWidth = InsertSpecs["Contents/CMgr"]
    UnitData = bytearray()
    for ItemIndex, ItemValue in enumerate(CoreItems[1:], 2):
        TemplateIndex = min(ItemIndex, TracedCount)
        UnitStart = InsertPos + ((TemplateIndex - 2) * UnitWidth)
        UnitOps = _SliceOps("Contents/CMgr", UnitStart, UnitStart + UnitWidth)
        UnitData.extend(
            _EmitOps(
                UnitOps,
                {
                    48: DisplayName,
                    184: 23 + ItemIndex,
                    190: ItemValue.OccurName,
                    321: ItemValue.ConfigName,
                    359: ItemValue.ConfigName,
                },
                UnitStart,
            )
        )
    SuffixStart = InsertPos + ((TracedCount - 1) * UnitWidth)
    RefShift = 8 * (ItemCount - TracedCount)
    SuffixData = _EmitOps(
        _SliceOps("Contents/CMgr", SuffixStart),
        {82: 61 + RefShift},
        SuffixStart,
    )
    return PrefixData + bytes(UnitData) + SuffixData


# repeated configuration objects carry occurrence identity and display placement
def _EncodeConfig(
    ModelName: str,
    ConfigName: str,
    CoreItems: tuple[RepeatItem, ...],
) -> bytes:
    ItemCount = len(CoreItems)
    InsertPos, UnitWidth = InsertSpecs["Contents/Config-0"]
    PrefixData = _EmitOps(
        _SliceOps("Contents/Config-0", 0, InsertPos),
        {
            0x0030: ModelName,
            0x006F: CoreItems[0].OccurName,
            0x01BE: ConfigName,
            0x0245: ModelName,
            0x0278: CoreItems[0].OccurName,
            18: 2218 + (UnitWidth * ItemCount),
            88: ItemCount,
        },
    )
    UnitData = bytearray()
    for ItemIndex, ItemValue in enumerate(CoreItems[1:], 2):
        TemplateIndex = min(ItemIndex, TracedCount)
        UnitStart = InsertPos + ((TemplateIndex - 2) * UnitWidth)
        UnitOps = _SliceOps("Contents/Config-0", UnitStart, UnitStart + UnitWidth)
        HashValue = (
            next(
                Operation[4] for Operation in UnitOps if Operation[0] - UnitStart == 199
            )
            if ItemIndex <= TracedCount
            else _OccurHash(ItemValue.OccurName)
        )
        UnitData.extend(
            _EmitOps(
                UnitOps,
                {
                    4: ItemValue.OccurName,
                    78: 23 + ItemIndex,
                    199: HashValue,
                    215: ItemValue.TransX,
                    223: ItemValue.TransY,
                    231: ItemValue.TransZ - 0.005,
                    387: 14 + ItemIndex,
                    460: 23 + ItemIndex,
                    466: ItemValue.OccurName,
                    532: 8 + (4 * ItemIndex),
                    339: ItemValue.ConfigName,
                },
                UnitStart,
            )
        )
    SuffixStart = InsertPos + ((TracedCount - 1) * UnitWidth)
    RefShift = 4 * (ItemCount - TracedCount)
    SuffixOverrides = {
        OffsetValue: DefaultValue + RefShift
        for OffsetValue in ConfigShiftRefs
        for StartPos, _Width, _Owner, _Kind, DefaultValue in _SliceOps(
            "Contents/Config-0", SuffixStart
        )
        if StartPos - SuffixStart == OffsetValue
    }
    SuffixOverrides[23442] = ItemCount
    SuffixData = _EmitOps(
        _SliceOps("Contents/Config-0", SuffixStart),
        SuffixOverrides,
        SuffixStart,
    )
    return PrefixData + bytes(UnitData) + SuffixData


# resolved occurrence links advance from the final occurrence back to the first
def _EncodeResolved(CoreItems: tuple[RepeatItem, ...]) -> bytes:
    ItemCount = len(CoreItems)
    BaseShift = 4 * (ItemCount - TracedCount)
    InsertPos, UnitWidth = InsertSpecs["Contents/Config-0-ResolvedFeatures"]
    PrefixData = _EmitOps(
        _SliceOps("Contents/Config-0-ResolvedFeatures", 0, InsertPos),
        {0: 97 + (4 * ItemCount), 604: ItemCount, 739: 23 + (14 * ItemCount)},
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
                    38: 10 + (4 * ItemIndex),
                    40: 32 + (13 * (ItemCount - ItemIndex)),
                },
                UnitStart,
            )
        )
    SuffixStart = InsertPos + ((TracedCount - 1) * UnitWidth)
    ShiftCount = ItemCount - TracedCount
    SuffixOps = _SliceOps("Contents/Config-0-ResolvedFeatures", SuffixStart)
    SuffixOverrides: dict[int, Any] = {}
    for StartPos, _Width, _Owner, _Kind, DefaultValue in SuffixOps:
        RelativePos = StartPos - SuffixStart
        if RelativePos in ResolvedShift8:
            SuffixOverrides[RelativePos] = DefaultValue + (8 * ShiftCount)
        elif RelativePos in ResolvedShift4:
            SuffixOverrides[RelativePos] = DefaultValue + (4 * ShiftCount)
    SuffixData = _EmitOps(SuffixOps, SuffixOverrides, SuffixStart)
    return PrefixData + bytes(UnitData) + SuffixData


# model-header stamps enumerate every occurrence and one shared component file
def _EncodeHeader(
    ModelName: str,
    ConfigName: str,
    CoreItems: tuple[RepeatItem, ...],
) -> bytes:
    ItemCount = len(CoreItems)
    CompPath = CoreItems[0].CompPath
    CompStem = PureWindowsPath(CompPath).stem
    InsertPos, UnitWidth = InsertSpecs["Contents/Config-0-ModelHeader"]
    PrefixData = _EmitOps(
        _SliceOps("Contents/Config-0-ModelHeader", 0, InsertPos),
        {0x008E: ModelName, 0x06AC: CoreItems[0].OccurName, 77: 23 + ItemCount},
    )
    UnitData = bytearray()
    for ItemIndex, ItemValue in enumerate(CoreItems[1:], 2):
        TemplateIndex = min(ItemIndex, TracedCount)
        UnitStart = InsertPos + ((TemplateIndex - 2) * UnitWidth)
        UnitData.extend(
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
    SuffixStart = InsertPos + ((TracedCount - 1) * UnitWidth)
    RefShift = 2 * (ItemCount - TracedCount)
    SuffixOps = _SliceOps("Contents/Config-0-ModelHeader", SuffixStart)
    SuffixOverrides = {
        OffsetValue: DefaultValue + RefShift
        for OffsetValue in HeaderShiftRefs
        for StartPos, _Width, _Owner, _Kind, DefaultValue in SuffixOps
        if StartPos - SuffixStart == OffsetValue
    }
    SuffixOverrides.update(
        {
            4: 24 + ItemCount,
            75: CompPath,
            259: CompStem,
            346: ItemCount,
            378: 103 + (2 * ItemCount),
            392: ModelName,
            445: ConfigName,
            509: ItemCount,
        }
    )
    SuffixData = _EmitOps(SuffixOps, SuffixOverrides, SuffixStart)
    return PrefixData + bytes(UnitData) + SuffixData


# canonical repeat assembly programs scale one shared component file to map limit
def EncodeRepCore(
    ModelName: str,
    ConfigName: str,
    CoreItems: tuple[RepeatItem, ...],
) -> Mapping[str, bytes]:
    if len(CoreItems) < 2:
        raise SldprtFormatError("repeat assembly history requires two occurrences")
    if any(ItemValue.CompPath != CoreItems[0].CompPath for ItemValue in CoreItems):
        raise SldprtFormatError("repeat assembly history requires one component file")
    StreamsMap = {
        "Contents/CMgr": _EncodeCMgr(ModelName, ConfigName, CoreItems),
        "Contents/Config-0": _EncodeConfig(ModelName, ConfigName, CoreItems),
        "Contents/Config-0-ResolvedFeatures": _EncodeResolved(CoreItems),
        "Contents/Definition": _EmitOps(StreamPrograms["Contents/Definition"], {}),
        "Contents/Config-0-ModelHeader": _EncodeHeader(
            ModelName, ConfigName, CoreItems
        ),
    }
    return MappingProxyType(StreamsMap)
