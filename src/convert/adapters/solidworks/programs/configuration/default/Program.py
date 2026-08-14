# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from collections.abc import Mapping
import struct
from typing import Any

from convert.adapters.solidworks.container.Archive import (
    encode_class_definition,
    encode_class_reference,
    encode_object_reference,
    encode_string,
)
from convert.adapters.solidworks.container.Container import SldprtFormatError

from .Registry import (
    FieldOwners,
    ConfigOps,
)


# primitive formats keep signed and floating fields faithful to their reader
PrimitiveFormats = {
    "char": "b",
    "uchar": "B",
    "short": "h",
    "ushort": "H",
    "int": "i",
    "long": "i",
    "ulong": "I",
    "float": "f",
    "double": "d",
    "int64": "q",
    "uint64": "Q",
}

# recovered boundaries isolate the only two variable-sized record regions
ReferenceLength = 25214
PartRecordLengthOffset = 0xE
PartNameOffset = 0x2C
ReferencePartName = "Part70"
SecondUnitStart = 0x34A
SecondUnitEnd = 0x38C
AtomHeadOffsets = (0xB24, 0xB28)
AtomStart = 0xB3A
AtomEnd = 0xB9C
HighWaterOffsets = (0x6085, 0x6089)
AtomClassIndex = 57
AtomLinkStamp = 42358


# each field operation serializes one recovered value through its typed contract
def EncodeField(KindName: str, FieldValue: Any) -> bytes:
    if KindName == "definition":
        ClassName, SchemaCode = FieldValue
        return encode_class_definition(ClassName, SchemaCode)
    if KindName == "classref":
        return encode_class_reference(FieldValue)
    if KindName == "objectref":
        return encode_object_reference(FieldValue)
    if KindName == "null":
        return struct.pack("<H", 0)
    if KindName == "string":
        return encode_string(FieldValue)
    if KindName == "stringlist":
        return struct.pack("<H", len(FieldValue)) + b"".join(
            encode_string(ItemText) for ItemText in FieldValue
        )
    if KindName.startswith("primitive:"):
        TypeName = KindName.split(":", 1)[1]
        return struct.pack("<" + PrimitiveFormats[TypeName], FieldValue)
    if KindName.startswith("direct:"):
        FormatText = KindName.split(":", 1)[1]
        ValuesList = FieldValue if isinstance(FieldValue, tuple) else (FieldValue,)
        return struct.pack("<" + FormatText, *ValuesList)
    raise SldprtFormatError(f"unknown Config-0 operation {KindName!r}")


# one semantic atom links a native configuration item to a feature-tree object
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
        OutputData.extend(encode_class_reference(AtomClassIndex))
    OutputData.extend(struct.pack("<H4i", 0, 1, 0x40000000, -1, 0))
    OutputData.extend(encode_string(""))
    OutputData.extend(struct.pack("<iH", 0, 0))
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
        AtomLinkStamp,
        SessionStamp,
        AtomLinkStamp,
        6,
    )
    OutputData.extend(struct.pack("<H14i", 0, *RecordValues))
    if IsLast:
        OutputData.extend(struct.pack("<III", Generation, 10000, 0x10000000))
    return bytes(OutputData)


# inserted atom class references shift every archive-map target defined after moAtom_c
def ShiftMapReference(KindName: str, FieldValue: Any, MapShift: int) -> Any:
    if MapShift <= 0:
        return FieldValue
    if KindName == "classref" and int(FieldValue) > AtomClassIndex:
        return int(FieldValue) + MapShift
    if KindName == "objectref" and int(FieldValue) > AtomClassIndex + 1:
        return int(FieldValue) + MapShift
    return FieldValue


# dynamic configuration generation replays every typed field in original order
def EncodeProgram(
    PartName: str = "Part70",
    Atoms: tuple[tuple[int, int], ...] = ((101, 32),),
    SessionStamp: int = 1,
    Generation: int = 18000,
    DualLengthUnits: bool = True,
    HighWater: tuple[int, int] = (101, 103),
    Overrides: Mapping[int, Any] | None = None,
) -> bytes:
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
    FieldOverrides = dict(Overrides or {})
    FieldOverrides[PartRecordLengthOffset] = (
        ConfigOps[1][4]
        + len(encode_string(PartName))
        - len(encode_string(ReferencePartName))
    )
    FieldOverrides[PartNameOffset] = PartName
    FieldOverrides[AtomHeadOffsets[0]] = max(AtomId for AtomId, _TreeId in Atoms)
    FieldOverrides[AtomHeadOffsets[1]] = len(Atoms)
    FieldOverrides[HighWaterOffsets[0]] = HighWater[0]
    FieldOverrides[HighWaterOffsets[1]] = HighWater[1]
    MapShift = len(Atoms) - 1
    OutputData = bytearray()
    SourceCursor = 0
    AtomsWritten = False
    for StartPos, FieldWidth, OwnerIndex, KindName, DefaultValue in ConfigOps:
        if StartPos != SourceCursor:
            raise SldprtFormatError(f"Config-0 field program drifted at {StartPos}")
        SourceCursor += FieldWidth
        if not DualLengthUnits and SecondUnitStart <= StartPos < SecondUnitEnd:
            continue
        if AtomStart <= StartPos < AtomEnd:
            if not AtomsWritten:
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
                AtomsWritten = True
            continue
        FieldValue = FieldOverrides.get(StartPos, DefaultValue)
        if StartPos >= AtomEnd:
            FieldValue = ShiftMapReference(KindName, FieldValue, MapShift)
        FieldData = EncodeField(KindName, FieldValue)
        if StartPos != PartNameOffset and len(FieldData) != FieldWidth:
            raise SldprtFormatError(f"Config-0 field width changed at {StartPos}")
        OutputData.extend(FieldData)
    if SourceCursor != ReferenceLength or not AtomsWritten:
        raise SldprtFormatError("Config-0 field program did not close its source")
    return bytes(OutputData)
