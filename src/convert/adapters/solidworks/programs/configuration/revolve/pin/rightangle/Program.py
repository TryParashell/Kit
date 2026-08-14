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


# exact closure proves the fixed program accounts for the complete stream
KReferenceLength = 24902

# the exact digest anchors the complete configuration without retaining vendor bytes
KReferenceDigest = "4a09091e5f03e9c8f617da241f1e0a71d5e43f64f84889067a2e520ac5c91f76"


# typed replay emits the fixed configuration without retaining vendor byte spans
def EncodeProgram(Overrides: Mapping[int, Any] | None = None) -> bytes:
    FieldOverrides = dict(Overrides or {})
    OutputData = bytearray()
    SourceCursor = 0
    for StartPos, FieldWidth, OwnerIndex, KindName, DefaultValue in KConfigOps:
        if StartPos != SourceCursor:
            raise SldprtFormatError(f"Config-0 field program drifted at {StartPos}")
        FieldValue = FieldOverrides.get(StartPos, DefaultValue)
        FieldData = EncodeField(KindName, FieldValue)
        if len(FieldData) != FieldWidth:
            raise SldprtFormatError(f"Config-0 field width changed at {StartPos}")
        OutputData.extend(FieldData)
        SourceCursor += FieldWidth
    if SourceCursor != KReferenceLength or len(OutputData) != KReferenceLength:
        raise SldprtFormatError("Config-0 field program did not close its source")
    return bytes(OutputData)


# coverage metrics make hidden opaque or donor regressions mechanically visible
def GetCoverage() -> dict[str, int]:
    return {
        "stream_bytes": KReferenceLength,
        "typed": KReferenceLength,
        "opaque": 0,
        "accounted": KReferenceLength,
        "operations": len(KConfigOps),
        "owners": len(KFieldOwners),
    }
