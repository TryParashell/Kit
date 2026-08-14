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
from typing import Any as AnyValue

from convert.adapters.solidworks.container.Archive import (
    encode_class_definition as EncodeClassDefinition,
    encode_class_reference as EncodeClassReference,
    encode_object_reference as EncodeObjectReference,
    encode_string as EncodeString,
)
from convert.adapters.solidworks.container.Container import SldprtFormatError


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


# archive field encoding centralizes the recovered structural value grammar
def EncodeArchive(KindName: str, FieldValue: AnyValue) -> bytes | None:
    if KindName == "definition":
        ClassName, SchemaCode = FieldValue
        return EncodeClassDefinition(ClassName, SchemaCode)
    if KindName == "classref":
        return EncodeClassReference(FieldValue)
    if KindName == "objectref":
        return EncodeObjectReference(FieldValue)
    if KindName == "null":
        return StructLib.pack("<H", 0)
    if KindName == "string":
        return EncodeString(FieldValue)
    if KindName == "stringlist":
        return StructLib.pack("<H", len(FieldValue)) + b"".join(
            EncodeString(ItemText) for ItemText in FieldValue
        )
    return None


# typed field encoding preserves every recovered primitive and archive contract
def EncodeValue(
    KindName: str,
    FieldValue: AnyValue,
    ErrorScope: str,
    FormatMap: Mapping[str, str] = KPrimitiveFormats,
) -> bytes:
    ArchiveData = EncodeArchive(KindName, FieldValue)
    if ArchiveData is not None:
        return ArchiveData
    if KindName.startswith("primitive:"):
        TypeName = KindName.split(":", 1)[1]
        return StructLib.pack("<" + FormatMap[TypeName], FieldValue)
    if KindName.startswith("direct:"):
        FormatText = KindName.split(":", 1)[1]
        ValuesData = FieldValue if isinstance(FieldValue, tuple) else (FieldValue,)
        return StructLib.pack("<" + FormatText, *ValuesData)
    raise SldprtFormatError(f"unknown {ErrorScope} operation {KindName!r}")


# resolved replay validates contiguous offsets field widths and final closure
def ReplayResolved(
    Operations: tuple[AnyValue, ...],
    ExpectedLength: int,
    Overrides: Mapping[int, AnyValue] | None = None,
    FormatMap: Mapping[str, str] = KPrimitiveFormats,
) -> bytes:
    FieldOverrides = Overrides or {}
    OutputData = bytearray()
    for StartPos, FieldWidth, OwnerIndex, KindName, DefaultValue in Operations:
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
    Operations: tuple[AnyValue, ...],
    ExpectedLength: int,
    ScopeName: str,
    Overrides: Mapping[int, AnyValue] | None = None,
) -> bytes:
    FieldOverrides = Overrides or {}
    OutputData = bytearray()
    SourceCursor = 0
    for StartPos, FieldWidth, OwnerIndex, KindName, DefaultValue in Operations:
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
    Operations: tuple[AnyValue, ...],
    Overrides: Mapping[int, AnyValue] | None = None,
) -> bytes:
    FieldOverrides = Overrides or {}
    OutputData = bytearray()
    SourceCursor = 0
    for StartPos, FieldWidth, OwnerIndex, KindName, DefaultValue in Operations:
        if StartPos != SourceCursor:
            raise SldprtFormatError(f"assembly field program drifted at {StartPos}")
        SourceCursor += FieldWidth
        FieldValue = FieldOverrides.get(StartPos, DefaultValue)
        FieldData = EncodeValue(KindName, FieldValue, "assembly")
        if KindName not in {"string", "stringlist"} and len(FieldData) != FieldWidth:
            raise SldprtFormatError(f"assembly field width changed at {StartPos}")
        OutputData.extend(FieldData)
    return bytes(OutputData)
