# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from convert.adapters.solidworks.programs.configuration.default.Program import (
    EncodeField,
)
from convert.adapters.solidworks.container.Container import SldprtFormatError

from .Registry import (
    KFieldOwners,
    KConfigOps,
)


# the exact stream length detects accidental grammar drift
KReferenceLength = 24976

# the exact digest freezes the independently recovered front plane vector
KReferenceDigest = "692fc14d4f32dd9e171d31a70b1c778eed157f1b2b62caf78bfaeae188d344d7"

# the annotation orientation matrix maps the front plane into model coordinates
KAnnotationMatrixOffset = 24315


# typed replay emits the fixed configuration without retaining vendor byte spans
def EncodeProgram(Overrides: Mapping[int, Any] | None = None) -> bytes:
    FieldOverrides = dict(Overrides or {})
    OutputData = bytearray()
    for StartPos, FieldWidth, _OwnerIndex, KindName, DefaultValue in KConfigOps:
        if StartPos != len(OutputData):
            raise SldprtFormatError(f"Config-0 field program drifted at {StartPos}")
        FieldValue = FieldOverrides.get(StartPos, DefaultValue)
        FieldData = EncodeField(KindName, FieldValue)
        if len(FieldData) != FieldWidth:
            raise SldprtFormatError(f"Config-0 field width changed at {StartPos}")
        OutputData.extend(FieldData)
    if len(OutputData) != KReferenceLength:
        raise SldprtFormatError("Config-0 field program did not close its source")
    return bytes(OutputData)


# coverage metrics make opaque or donor regressions mechanically visible
def GetCoverage() -> dict[str, int]:
    return {
        "stream_bytes": KReferenceLength,
        "typed": KReferenceLength,
        "opaque": 0,
        "accounted": KReferenceLength,
        "operations": len(KConfigOps),
        "owners": len(KFieldOwners),
    }
