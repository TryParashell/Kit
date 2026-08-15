# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence
import struct as StructLib

from convert.adapters.solidworks.container.Archive import (
    encode_class_definition as EncodeClassDefinition,
    encode_class_reference as EncodeClassReference,
    encode_object_reference as EncodeObjectReference,
    encode_string as EncodeString,
)
from convert.adapters.solidworks.container.Container import SldprtFormatError
from convert.adapters.solidworks.programs.Common.ProgramContract import (
    BuildOverrides,
    FieldOp,
    FieldOverrides,
    FieldValue,
)


# primitive format mapping preserves signed and floating field widths
KPrimitiveFormats = {
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


# reference arithmetic needs validated integers instead of unchecked recursive field values
def RequireInt(FieldData: FieldValue, ErrorScope: str) -> int:
    if not isinstance(FieldData, int):
        raise SldprtFormatError(f"{ErrorScope} requires an integer field value")
    return FieldData


# selected suffix references need shared filtering before recursive values are narrowed to integers
def BuildShiftMap(
    Operations: Sequence[FieldOp],
    BasePos: int,
    ShiftRules: Sequence[tuple[Collection[int], int]],
    ErrorScope: str,
) -> dict[int, FieldValue]:
    ShiftValues = BuildOverrides()
    for Operation in Operations:
        RelativePos = Operation[0] - BasePos
        for TargetOffsets, ShiftValue in ShiftRules:
            if RelativePos in TargetOffsets:
                ShiftValues[RelativePos] = (
                    RequireInt(Operation[4], ErrorScope) + ShiftValue
                )
                break
    return ShiftValues


# archive field encoding centralizes the recovered structural value grammar
def EncodeArchive(KindName: str, FieldData: FieldValue) -> bytes | None:
    if KindName == "definition":
        if not isinstance(FieldData, tuple) or len(FieldData) != 2:
            raise SldprtFormatError("archive class definition value is invalid")
        ClassName, SchemaCode = FieldData
        if not isinstance(ClassName, str) or not isinstance(SchemaCode, int):
            raise SldprtFormatError("archive class definition types are invalid")
        return EncodeClassDefinition(ClassName, SchemaCode)
    if KindName == "classref":
        if not isinstance(FieldData, int):
            raise SldprtFormatError("archive class reference value is invalid")
        return EncodeClassReference(FieldData)
    if KindName == "objectref":
        if not isinstance(FieldData, int):
            raise SldprtFormatError("archive object reference value is invalid")
        return EncodeObjectReference(FieldData)
    if KindName == "null":
        return StructLib.pack("<H", 0)
    if KindName == "string":
        if not isinstance(FieldData, str):
            raise SldprtFormatError("archive string value is invalid")
        return EncodeString(FieldData)
    if KindName == "stringlist":
        if not isinstance(FieldData, tuple):
            raise SldprtFormatError("archive string list value is invalid")
        EncodedItems: list[bytes] = []
        for ItemText in FieldData:
            if not isinstance(ItemText, str):
                raise SldprtFormatError("archive string list item is invalid")
            EncodedItems.append(EncodeString(ItemText))
        return StructLib.pack("<H", len(FieldData)) + b"".join(EncodedItems)
    return None


# typed field encoding preserves every recovered primitive and archive contract
def EncodeValue(
    KindName: str,
    FieldData: FieldValue,
    ErrorScope: str,
    FormatMap: Mapping[str, str] = KPrimitiveFormats,
) -> bytes:
    ArchiveData = EncodeArchive(KindName, FieldData)
    if ArchiveData is not None:
        return ArchiveData
    if KindName.startswith("primitive:"):
        if not isinstance(FieldData, int | float):
            raise SldprtFormatError(f"invalid {ErrorScope} primitive value")
        TypeName = KindName.split(":", 1)[1]
        return StructLib.pack("<" + FormatMap[TypeName], FieldData)
    if KindName.startswith("direct:"):
        if isinstance(FieldData, str):
            raise SldprtFormatError(f"invalid {ErrorScope} direct value")
        FormatText = KindName.split(":", 1)[1]
        ValuesData: tuple[FieldValue, ...] = (
            FieldData if isinstance(FieldData, tuple) else (FieldData,)
        )
        if any(not isinstance(ItemValue, int | float) for ItemValue in ValuesData):
            raise SldprtFormatError(f"invalid {ErrorScope} direct values")
        return StructLib.pack("<" + FormatText, *ValuesData)
    raise SldprtFormatError(f"unknown {ErrorScope} operation {KindName!r}")


# resolved replay validates contiguous offsets field widths and final closure
def ReplayResolved(
    Operations: tuple[FieldOp, ...],
    ExpectedLength: int,
    Overrides: FieldOverrides | None = None,
    FormatMap: Mapping[str, str] = KPrimitiveFormats,
) -> bytes:
    FieldOverrides = Overrides or {}
    OutputData = bytearray()
    for StartPos, FieldWidth, _OwnerIndex, KindName, DefaultValue in Operations:
        if len(OutputData) != StartPos:
            raise SldprtFormatError(f"resolved field program drifted at {StartPos}")
        FieldValue = FieldOverrides.get(StartPos, DefaultValue)
        FieldData = EncodeValue(KindName, FieldValue, "resolved", FormatMap)
        if len(FieldData) != FieldWidth:
            raise SldprtFormatError(f"resolved field width changed at {StartPos}")
        OutputData.extend(FieldData)
    if len(OutputData) != ExpectedLength:
        raise SldprtFormatError("resolved field program length changed")
    return bytes(OutputData)


# fixed replay validates source ordering encoded widths and exact source closure
def ReplayFixed(
    Operations: tuple[FieldOp, ...],
    ExpectedLength: int,
    ScopeName: str,
    Overrides: FieldOverrides | None = None,
) -> bytes:
    FieldOverrides = Overrides or {}
    OutputData = bytearray()
    SourceCursor = 0
    for StartPos, FieldWidth, _OwnerIndex, KindName, DefaultValue in Operations:
        if StartPos != SourceCursor:
            raise SldprtFormatError(f"{ScopeName} field program drifted at {StartPos}")
        FieldData = EncodeValue(
            KindName, FieldOverrides.get(StartPos, DefaultValue), ScopeName
        )
        if len(FieldData) != FieldWidth:
            raise SldprtFormatError(f"{ScopeName} field width changed at {StartPos}")
        OutputData.extend(FieldData)
        SourceCursor += FieldWidth
    if SourceCursor != ExpectedLength or len(OutputData) != ExpectedLength:
        raise SldprtFormatError(f"{ScopeName} field program did not close its source")
    return bytes(OutputData)


# assembly replay permits only the recovered variable width string operations
def ReplayAssembly(
    Operations: tuple[FieldOp, ...],
    Overrides: FieldOverrides | None = None,
) -> bytes:
    FieldOverrides = Overrides or {}
    OutputData = bytearray()
    SourceCursor = 0
    for StartPos, FieldWidth, _OwnerIndex, KindName, DefaultValue in Operations:
        if StartPos != SourceCursor:
            raise SldprtFormatError(f"assembly field program drifted at {StartPos}")
        SourceCursor += FieldWidth
        FieldValue = FieldOverrides.get(StartPos, DefaultValue)
        FieldData = EncodeValue(KindName, FieldValue, "assembly")
        if KindName not in {"string", "stringlist"} and len(FieldData) != FieldWidth:
            raise SldprtFormatError(f"assembly field width changed at {StartPos}")
        OutputData.extend(FieldData)
    return bytes(OutputData)
