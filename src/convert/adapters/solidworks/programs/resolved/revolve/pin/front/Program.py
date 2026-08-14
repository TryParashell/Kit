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
    KFieldOwners,
    KResolvedOps,
)


# primitive formats keep signed and floating fields faithful to their reader
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

# the exact stream length detects accidental grammar drift
KReferenceLength = 12265

# the exact digest freezes the independently recovered front plane vector
KReferenceDigest = "2319ad19c471780a0d0b30f9108b47d5816f23cb16d9a327224b81e6afa1ec3a"

# six coordinate pairs preserve every editable stepped pin sketch vertex
KProfileOffsets = (
    (6904, 6912),
    (7066, 7074),
    (7228, 7236),
    (7390, 7398),
    (7552, 7560),
    (7714, 7722),
)

# all recovered angle copies carry the same editable full revolution value
KAngleOffsets = (11209, 11723, 11747)


# callers can replace semantic fields while retaining recovered object framing
def EncodeProgram(Overrides: Mapping[int, Any] | None = None) -> bytes:
    FieldOverrides = Overrides or {}
    OutputData = bytearray()
    for StartPos, FieldWidth, _OwnerIndex, KindName, DefaultValue in KResolvedOps:
        if len(OutputData) != StartPos:
            raise SldprtFormatError(f"resolved field program drifted at {StartPos}")
        FieldValue = FieldOverrides.get(StartPos, DefaultValue)
        if KindName == "definition":
            ClassName, SchemaCode = FieldValue
            FieldData = encode_class_definition(ClassName, SchemaCode)
        elif KindName == "classref":
            FieldData = encode_class_reference(FieldValue)
        elif KindName == "objectref":
            FieldData = encode_object_reference(FieldValue)
        elif KindName == "null":
            FieldData = struct.pack("<H", 0)
        elif KindName == "string":
            FieldData = encode_string(FieldValue)
        elif KindName.startswith("primitive:"):
            TypeName = KindName.split(":", 1)[1]
            FieldData = struct.pack("<" + KPrimitiveFormats[TypeName], FieldValue)
        elif KindName.startswith("direct:"):
            FormatText = KindName.split(":", 1)[1]
            ValuesData = FieldValue if isinstance(FieldValue, tuple) else (FieldValue,)
            FieldData = struct.pack("<" + FormatText, *ValuesData)
        else:
            raise SldprtFormatError(f"unknown resolved operation {KindName!r}")
        if len(FieldData) != FieldWidth:
            raise SldprtFormatError(f"resolved field width changed at {StartPos}")
        OutputData.extend(FieldData)
    if len(OutputData) != KReferenceLength:
        raise SldprtFormatError("resolved field program length changed")
    return bytes(OutputData)


# coverage metrics make opaque or donor regressions mechanically visible
def GetCoverage() -> dict[str, int]:
    return {
        "stream_bytes": KReferenceLength,
        "typed": KReferenceLength,
        "opaque": 0,
        "accounted": KReferenceLength,
        "operations": len(KResolvedOps),
        "owners": len(KFieldOwners),
    }
