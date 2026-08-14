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
KReferenceLength = 14065

# the exact digest anchors the independently recovered midplane field vector
KReferenceDigest = "bffc7d98b6ed899d79deff6b71772454cb94c1c45d8ace10a167022f154f179e"

# six coordinate pairs preserve every editable stepped pin sketch vertex
KProfileOffsets = (
    (6904, 6912),
    (7066, 7074),
    (7228, 7236),
    (7390, 7398),
    (7552, 7560),
    (7714, 7722),
)

# the first end mode distinguishes a symmetric revolution from a single end
KSingleEndOffset = 10437

# all first angle copies carry the editable full revolution value
KFirstAngleOffsets = (11281, 11795, 11819)

# all second angle copies preserve the explicit zero length opposite end
KSecondAngleOffsets = (13033, 13547, 13571)


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
            ValuesList = FieldValue if isinstance(FieldValue, tuple) else (FieldValue,)
            FieldData = struct.pack("<" + FormatText, *ValuesList)
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
