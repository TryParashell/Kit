# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from collections.abc import Mapping
import struct as StructLib
from convert.adapters.solidworks.programs.Common.ProgramContract import (
    FieldValue as FieldType,
)

from convert.adapters.solidworks.container.Archive import (
    encode_class_reference as EncodeClassReference,
    encode_string as EncodeString,
)
from convert.adapters.solidworks.container.Container import SldprtFormatError
from convert.adapters.solidworks.programs.Common.FieldEncoder import (
    EncodeValue,
    KPrimitiveFormats,
    RequireInt,
)

from .Registry import (
    KFieldOwners,
    ConfigOps,
)


# compatibility binding preserves the generated owner catalog facade
FieldOwners = KFieldOwners

# recovered stream length detects accidental configuration grammar drift
KReferenceLength = 25214

# record length location supports variable part name serialization
KPartRecordLengthOffset = 0xE

# part name location supports semantic configuration identity replacement
KPartNameOffset = 0x2C

# recovered part name establishes the reference encoded string width
KReferencePartName = "Part70"

# secondary unit start supports optional duplicate length unit removal
KSecondUnitStart = 0x34A

# secondary unit end bounds optional duplicate length unit removal
KSecondUnitEnd = 0x38C

# atom header locations carry maximum identifiers and atom counts
KAtomHeadOffsets = (0xB24, 0xB28)

# atom region start anchors semantic atom replacement within the stream
KAtomStart = 0xB3A

# atom region end anchors archive map shifting after atom replacement
KAtomEnd = 0xB9C

# high water locations preserve configuration allocation counters
KHighWaterOffsets = (0x6085, 0x6089)

# atom class index identifies the recovered native configuration class
KAtomClassIndex = 57

# atom link stamp preserves recovered feature tree association framing
KAtomLinkStamp = 42358


# each field operation serializes one recovered value through its typed contract
def EncodeField(KindName: str, FieldValue: FieldType) -> bytes:
    return EncodeValue(KindName, FieldValue, "Config-0")


# one semantic atom links a native configuration item to a feature tree object
def EncodeAtom(
    AtomId: int,
    TreeId: int,
    SessionStamp: int,
    Position: int,
    IsLast: bool,
    Generation: int,
) -> bytes:
    if not 0 <= AtomId <= 0xFFFFFFFF or not 0 <= TreeId <= 0xFFFFFFFF:
        raise SldprtFormatError("Config-0 atom identifiers must fit in 32 bits")
    OutputData = bytearray()
    if Position:
        OutputData.extend(EncodeClassReference(KAtomClassIndex))
    OutputData.extend(StructLib.pack("<H4i", 0, 1, 0x40000000, -1, 0))
    OutputData.extend(EncodeString(""))
    OutputData.extend(StructLib.pack("<iH", 0, 0))
    RecordValues = (
        0,
        AtomId,
        0 if Position == 0 else 1,
        TreeId,
        TreeId,
        0,
        0,
        0,
        SessionStamp,
        -1,
        KAtomLinkStamp,
        SessionStamp,
        KAtomLinkStamp,
        6,
    )
    OutputData.extend(StructLib.pack("<H14i", 0, *RecordValues))
    if IsLast:
        OutputData.extend(StructLib.pack("<III", Generation, 10000, 0x10000000))
    return bytes(OutputData)


# inserted atom references shift every later archive map target
def ShiftMapRef(KindName: str, FieldValue: FieldType, MapShift: int) -> FieldType:
    if MapShift <= 0:
        return FieldValue
    if KindName == "classref":
        RefValue = RequireInt(FieldValue, "configuration class reference")
        return RefValue + MapShift if RefValue > KAtomClassIndex else RefValue
    if KindName == "objectref":
        RefValue = RequireInt(FieldValue, "configuration object reference")
        return RefValue + MapShift if RefValue > KAtomClassIndex + 1 else RefValue
    return FieldValue


# legacy aliases preserve external configuration callers and recovered diagnostic access
PrimitiveFormats = KPrimitiveFormats
ReferenceLength = KReferenceLength
PartRecordLengthOffset = KPartRecordLengthOffset
PartNameOffset = KPartNameOffset
ReferencePartName = KReferencePartName
SecondUnitStart = KSecondUnitStart
SecondUnitEnd = KSecondUnitEnd
AtomHeadOffsets = KAtomHeadOffsets
AtomStart = KAtomStart
AtomEnd = KAtomEnd
HighWaterOffsets = KHighWaterOffsets
AtomClassIndex = KAtomClassIndex
AtomLinkStamp = KAtomLinkStamp
ShiftMapReference = ShiftMapRef


# atom validation protects native identifiers and the recovered generation contract
def ValidateAtoms(Atoms: tuple[tuple[int, int], ...], Generation: int) -> None:
    if not Atoms:
        raise SldprtFormatError("Contents/Config-0 needs at least one atom record")
    if any(
        not 0 <= AtomId <= 0xFFFFFFFF or not 0 <= TreeId <= 0xFFFFFFFF
        for AtomId, TreeId in Atoms
    ):
        raise SldprtFormatError("Config-0 atom identifiers must fit in 32 bits")
    if Generation != 18000:
        raise SldprtFormatError(
            f"Contents/Config-0 fields are recovered at generation 18000, {Generation} was requested"
        )


# semantic override construction isolates all variable configuration header fields
def MakeOverrides(
    PartName: str,
    Atoms: tuple[tuple[int, int], ...],
    HighWater: tuple[int, int],
    Overrides: Mapping[int, FieldType] | None,
) -> tuple[dict[int, FieldType], int]:
    FieldOverrides = dict(Overrides or {})
    FieldOverrides[KPartRecordLengthOffset] = (
        RequireInt(ConfigOps[1][4], "configuration record length")
        + len(EncodeString(PartName))
        - len(EncodeString(KReferencePartName))
    )
    FieldOverrides[KPartNameOffset] = PartName
    FieldOverrides[KAtomHeadOffsets[0]] = max(AtomData[0] for AtomData in Atoms)
    FieldOverrides[KAtomHeadOffsets[1]] = len(Atoms)
    FieldOverrides[KHighWaterOffsets[0]] = HighWater[0]
    FieldOverrides[KHighWaterOffsets[1]] = HighWater[1]
    return FieldOverrides, len(Atoms) - 1


# atom sequence encoding preserves ordering links and terminal generation framing
def EncodeAtoms(
    Atoms: tuple[tuple[int, int], ...], SessionStamp: int, Generation: int
) -> bytes:
    OutputData = bytearray()
    for Position, (AtomId, TreeId) in enumerate(Atoms):
        OutputData.extend(
            EncodeAtom(
                AtomId,
                TreeId,
                SessionStamp,
                Position,
                Position == len(Atoms) - 1,
                Generation,
            )
        )
    return bytes(OutputData)


# configuration replay replaces semantic regions while preserving recovered field order
def ReplayConfig(
    FieldOverrides: Mapping[int, FieldType],
    AtomData: bytes,
    DualLengthUnits: bool,
    MapShift: int,
) -> bytes:
    OutputData = bytearray()
    SourceCursor = 0
    AtomsWritten = False
    for StartPos, FieldWidth, _OwnerIndex, KindName, DefaultValue in ConfigOps:
        if StartPos != SourceCursor:
            raise SldprtFormatError(f"Config-0 field program drifted at {StartPos}")
        SourceCursor += FieldWidth
        if not DualLengthUnits and KSecondUnitStart <= StartPos < KSecondUnitEnd:
            continue
        if KAtomStart <= StartPos < KAtomEnd:
            if not AtomsWritten:
                OutputData.extend(AtomData)
                AtomsWritten = True
            continue
        FieldValue = FieldOverrides.get(StartPos, DefaultValue)
        if StartPos >= KAtomEnd:
            FieldValue = ShiftMapRef(KindName, FieldValue, MapShift)
        FieldData = EncodeField(KindName, FieldValue)
        if StartPos != KPartNameOffset and len(FieldData) != FieldWidth:
            raise SldprtFormatError(f"Config-0 field width changed at {StartPos}")
        OutputData.extend(FieldData)
    if SourceCursor != KReferenceLength or not AtomsWritten:
        raise SldprtFormatError("Config-0 field program did not close its source")
    return bytes(OutputData)


# dynamic configuration generation replays every typed field in original order
def EncodeProgram(
    PartName: str = "Part70",
    Atoms: tuple[tuple[int, int], ...] = ((101, 32),),
    SessionStamp: int = 1,
    Generation: int = 18000,
    DualLengthUnits: bool = True,
    HighWater: tuple[int, int] = (101, 103),
    Overrides: Mapping[int, FieldType] | None = None,
) -> bytes:
    ValidateAtoms(Atoms, Generation)
    FieldOverrides, MapShift = MakeOverrides(PartName, Atoms, HighWater, Overrides)
    AtomData = EncodeAtoms(Atoms, SessionStamp, Generation)
    return ReplayConfig(FieldOverrides, AtomData, DualLengthUnits, MapShift)
