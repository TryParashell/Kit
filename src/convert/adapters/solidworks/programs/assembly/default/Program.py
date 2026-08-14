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
    StreamPrograms,
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


# each operation serializes one recovered value through its typed contract
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
    raise SldprtFormatError(f"unknown assembly operation {KindName!r}")


# callers may replace semantic fields while source offsets preserve field order
def EncodeProgram(StreamName: str, Overrides: Mapping[int, Any] | None = None) -> bytes:
    try:
        Operations = StreamPrograms[StreamName]
    except KeyError as ErrorData:
        raise SldprtFormatError(
            f"unknown assembly stream {StreamName!r}"
        ) from ErrorData
    FieldOverrides = Overrides or {}
    OutputData = bytearray()
    SourceCursor = 0
    for StartPos, FieldWidth, OwnerIndex, KindName, DefaultValue in Operations:
        if StartPos != SourceCursor:
            raise SldprtFormatError(f"assembly field program drifted at {StartPos}")
        SourceCursor += FieldWidth
        FieldValue = FieldOverrides.get(StartPos, DefaultValue)
        FieldData = EncodeField(KindName, FieldValue)
        if KindName not in {"string", "stringlist"} and len(FieldData) != FieldWidth:
            raise SldprtFormatError(f"assembly field width changed at {StartPos}")
        OutputData.extend(FieldData)
    return bytes(OutputData)
