# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

import binascii as BinaryAscii
from collections.abc import Mapping, Sequence
from pathlib import PureWindowsPath
from types import MappingProxyType
from convert.adapters.solidworks.programs.Common.ProgramContract import (
    FieldOp,
    FieldValue as FieldType,
)
from convert.adapters.solidworks.programs.Common.FieldEncoder import RequireInt

from convert.adapters.solidworks.programs.assembly.quintuples.Program import (
    EncodeField,
    StreamPrograms,
)
from convert.adapters.solidworks.container.Container import SldprtFormatError


# recovered insertion boundaries split stable fields from occurrence records
KInsertSpecs = MappingProxyType(
    {
        "Contents/CMgr": (1766, 424),
        "Contents/Config-0": (760, 594),
        "Contents/Config-0-ResolvedFeatures": (755, 56),
        "Contents/Config-0-ModelHeader": (1774, 104),
    }
)

# five traced occurrences provide four complete canonical repeat templates
KTracedCount = 5

# config suffix references advance four map entries for every occurrence
KConfigShiftRefs = frozenset(
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
KResolvedShiftEight = frozenset({1115, 1310, 1344, 2424, 2747, 2990, 3317})

# resolved suffix targets before insertion advance by the four entry base map
KResolvedShiftFour = frozenset({1493, 4069, 4243, 4330})

# header suffix references advance two map entries for every occurrence stamp
KHeaderShiftRefs = frozenset({257, 382, 384, 390})


# one repeated item supplies semantic identity and display translation fields
class RepeatItem:
    OccurName: str
    CompPath: str
    TransX: float
    TransY: float
    TransZ: float
    ConfigName: str
    FileStamp: int
    BasisVals: tuple[float, ...]

    __slots__ = (
        "OccurName",
        "CompPath",
        "TransX",
        "TransY",
        "TransZ",
        "ConfigName",
        "FileStamp",
        "BasisVals",
    )

    # explicit initialization lets static consumers retain every recovered occurrence field
    def __init__(
        self,
        OccurName: str,
        CompPath: str,
        TransX: float = 0.0,
        TransY: float = 0.0,
        TransZ: float = 0.0,
        ConfigName: str = "Default",
        FileStamp: int = 0,
        BasisVals: tuple[float, ...] = (
            1.0,
            0.0,
            0.0,
            0.0,
            1.0,
            0.0,
            0.0,
            0.0,
            1.0,
        ),
    ) -> None:
        if len(BasisVals) != 9:
            raise SldprtFormatError("assembly transform basis requires nine values")
        self.OccurName = OccurName
        self.CompPath = CompPath
        self.TransX = TransX
        self.TransY = TransY
        self.TransZ = TransZ
        self.ConfigName = ConfigName
        self.FileStamp = FileStamp
        self.BasisVals = BasisVals


# identity transforms retain the compact native transform representation
def IsIdentityBasis(BasisVals: tuple[float, ...]) -> bool:
    return BasisVals == (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)


# one operation tuple retains its typed serializer owner and native field value
def EncodeOps(
    Operations: Sequence[FieldOp],
    Overrides: Mapping[int, FieldType],
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


# logical slicing ignores variable string widths while preserving field order
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


# stable occurrence hashes give later records unique recovered identifier fields
def OccurHash(OccurName: str) -> int:
    CheckValue = BinaryAscii.crc32(OccurName.encode("utf-16le")) & 0x0FFFFFFF
    return 0x50000000 | CheckValue


# repeated configuration manager objects advance eight archive map entries
def EncodeCmgr(
    ModelName: str,
    ConfigName: str,
    CoreItems: tuple[RepeatItem, ...],
) -> bytes:
    ItemCount = len(CoreItems)
    DisplayName = f"<{ConfigName}>_Display State 1"
    PrefixOps = SliceOps("Contents/CMgr", 0, KInsertSpecs["Contents/CMgr"][0])
    PrefixData = EncodeOps(
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
    InsertPos, UnitWidth = KInsertSpecs["Contents/CMgr"]
    UnitData = bytearray()
    for ItemIndex, ItemValue in enumerate(CoreItems[1:], 2):
        TemplateIndex = min(ItemIndex, KTracedCount)
        UnitStart = InsertPos + ((TemplateIndex - 2) * UnitWidth)
        UnitOps = SliceOps("Contents/CMgr", UnitStart, UnitStart + UnitWidth)
        UnitData.extend(
            EncodeOps(
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
    SuffixStart = InsertPos + ((KTracedCount - 1) * UnitWidth)
    RefShift = 8 * (ItemCount - KTracedCount)
    SuffixData = EncodeOps(
        SliceOps("Contents/CMgr", SuffixStart),
        {82: 61 + RefShift},
        SuffixStart,
    )
    return PrefixData + bytes(UnitData) + SuffixData


# repeated configuration objects carry occurrence identity and display placement
def EncodeConfig(
    ModelName: str,
    ConfigName: str,
    CoreItems: tuple[RepeatItem, ...],
) -> bytes:
    ItemCount = len(CoreItems)
    BasisCount = sum(
        not IsIdentityBasis(ItemValue.BasisVals) for ItemValue in CoreItems
    )
    InsertPos, UnitWidth = KInsertSpecs["Contents/Config-0"]
    PrefixData = EncodeOps(
        SliceOps("Contents/Config-0", 0, InsertPos),
        {
            0x0030: ModelName,
            0x006F: CoreItems[0].OccurName,
            0x01BE: ConfigName,
            0x0245: ModelName,
            0x0278: CoreItems[0].OccurName,
            322: CoreItems[0].TransX,
            330: CoreItems[0].TransY,
            338: CoreItems[0].TransZ,
            18: 2218 + (UnitWidth * ItemCount) + (72 * BasisCount),
            88: ItemCount,
            **({321: 1} if not IsIdentityBasis(CoreItems[0].BasisVals) else {}),
        },
        BasisValues=(
            {321: CoreItems[0].BasisVals}
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
                Operation[4] for Operation in UnitOps if Operation[0] - UnitStart == 199
            )
            if ItemIndex <= KTracedCount
            else OccurHash(ItemValue.OccurName)
        )
        UnitData.extend(
            EncodeOps(
                UnitOps,
                {
                    4: ItemValue.OccurName,
                    78: 23 + ItemIndex,
                    199: HashValue,
                    215: ItemValue.TransX,
                    223: ItemValue.TransY,
                    231: ItemValue.TransZ,
                    387: 14 + ItemIndex,
                    460: 23 + ItemIndex,
                    466: ItemValue.OccurName,
                    532: 8 + (4 * ItemIndex),
                    339: ItemValue.ConfigName,
                    **({214: 1} if not IsIdentityBasis(ItemValue.BasisVals) else {}),
                },
                UnitStart,
                (
                    {214: ItemValue.BasisVals}
                    if not IsIdentityBasis(ItemValue.BasisVals)
                    else None
                ),
            )
        )
    SuffixStart = InsertPos + ((KTracedCount - 1) * UnitWidth)
    RefShift = 4 * (ItemCount - KTracedCount)
    SuffixOverrides = {
        OffsetValue: RequireInt(Operation[4], "configuration suffix reference")
        + RefShift
        for OffsetValue in KConfigShiftRefs
        for Operation in SliceOps("Contents/Config-0", SuffixStart)
        if Operation[0] - SuffixStart == OffsetValue
    }
    SuffixOverrides[23442] = ItemCount
    SuffixData = EncodeOps(
        SliceOps("Contents/Config-0", SuffixStart),
        SuffixOverrides,
        SuffixStart,
    )
    return PrefixData + bytes(UnitData) + SuffixData


# resolved occurrence links advance from the final occurrence back to the first
def EncodeResolved(CoreItems: tuple[RepeatItem, ...]) -> bytes:
    ItemCount = len(CoreItems)
    BaseShift = 4 * (ItemCount - KTracedCount)
    InsertPos, UnitWidth = KInsertSpecs["Contents/Config-0-ResolvedFeatures"]
    PrefixData = EncodeOps(
        SliceOps("Contents/Config-0-ResolvedFeatures", 0, InsertPos),
        {0: 97 + (4 * ItemCount), 604: ItemCount, 739: 23 + (14 * ItemCount)},
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
            Operation[0] - UnitStart: RequireInt(
                Operation[4], "resolved unit reference"
            )
            + BaseShift
            for Operation in UnitOps
            if Operation[3] == "classref"
        }
        UnitData.extend(
            EncodeOps(
                UnitOps,
                {
                    **RefValues,
                    38: 10 + (4 * ItemIndex),
                    40: 32 + (13 * (ItemCount - ItemIndex)),
                },
                UnitStart,
            )
        )
    SuffixStart = InsertPos + ((KTracedCount - 1) * UnitWidth)
    ShiftCount = ItemCount - KTracedCount
    SuffixOps = SliceOps("Contents/Config-0-ResolvedFeatures", SuffixStart)
    SuffixOverrides: dict[int, FieldType] = {}
    for Operation in SuffixOps:
        RelativePos = Operation[0] - SuffixStart
        DefaultValue = RequireInt(Operation[4], "resolved suffix reference")
        if RelativePos in KResolvedShiftEight:
            SuffixOverrides[RelativePos] = DefaultValue + (8 * ShiftCount)
        elif RelativePos in KResolvedShiftFour:
            SuffixOverrides[RelativePos] = DefaultValue + (4 * ShiftCount)
    SuffixData = EncodeOps(SuffixOps, SuffixOverrides, SuffixStart)
    return PrefixData + bytes(UnitData) + SuffixData


# model header stamps enumerate every occurrence and one shared component file
def EncodeHeader(
    ModelName: str,
    ConfigName: str,
    CoreItems: tuple[RepeatItem, ...],
) -> bytes:
    ItemCount = len(CoreItems)
    CompPath = CoreItems[0].CompPath
    CompStem = PureWindowsPath(CompPath).stem
    InsertPos, UnitWidth = KInsertSpecs["Contents/Config-0-ModelHeader"]
    PrefixData = EncodeOps(
        SliceOps("Contents/Config-0-ModelHeader", 0, InsertPos),
        {0x008E: ModelName, 0x06AC: CoreItems[0].OccurName, 77: 23 + ItemCount},
    )
    UnitData = bytearray()
    for ItemIndex, ItemValue in enumerate(CoreItems[1:], 2):
        TemplateIndex = min(ItemIndex, KTracedCount)
        UnitStart = InsertPos + ((TemplateIndex - 2) * UnitWidth)
        UnitData.extend(
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
    SuffixStart = InsertPos + ((KTracedCount - 1) * UnitWidth)
    RefShift = 2 * (ItemCount - KTracedCount)
    SuffixOps = SliceOps("Contents/Config-0-ModelHeader", SuffixStart)
    SuffixOverrides = {
        OffsetValue: RequireInt(Operation[4], "header suffix reference") + RefShift
        for OffsetValue in KHeaderShiftRefs
        for Operation in SuffixOps
        if Operation[0] - SuffixStart == OffsetValue
    }
    SuffixOverrides.update(
        {
            4: 24 + ItemCount,
            75: CompPath,
            259: CompStem,
            **({324: CoreItems[0].FileStamp} if CoreItems[0].FileStamp > 0 else {}),
            346: ItemCount,
            378: 103 + (2 * ItemCount),
            392: ModelName,
            445: ConfigName,
            509: ItemCount,
        }
    )
    SuffixData = EncodeOps(SuffixOps, SuffixOverrides, SuffixStart)
    return PrefixData + bytes(UnitData) + SuffixData


# legacy aliases preserve recovered repeat helpers and existing external callers
InsertSpecs = KInsertSpecs
TracedCount = KTracedCount
ConfigShiftRefs = KConfigShiftRefs
ResolvedShift8 = KResolvedShiftEight
ResolvedShift4 = KResolvedShiftFour
HeaderShiftRefs = KHeaderShiftRefs
_IsIdentityBasis = IsIdentityBasis
_EmitOps = EncodeOps
_SliceOps = SliceOps
_OccurHash = OccurHash
_EncodeCMgr = EncodeCmgr
_EncodeConfig = EncodeConfig
_EncodeResolved = EncodeResolved
_EncodeHeader = EncodeHeader


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
        "Contents/CMgr": EncodeCmgr(ModelName, ConfigName, CoreItems),
        "Contents/Config-0": EncodeConfig(ModelName, ConfigName, CoreItems),
        "Contents/Config-0-ResolvedFeatures": EncodeResolved(CoreItems),
        "Contents/Definition": EncodeOps(
            StreamPrograms["Contents/Definition"], {3479: len(CoreItems)}
        ),
        "Contents/Config-0-ModelHeader": EncodeHeader(ModelName, ConfigName, CoreItems),
    }
    return MappingProxyType(StreamsMap)
