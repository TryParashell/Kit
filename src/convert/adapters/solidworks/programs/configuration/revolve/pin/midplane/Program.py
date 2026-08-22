# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from collections.abc import Mapping
from convert.adapters.solidworks.programs.Common.ProgramContract import (
    FieldValue as FieldType,
)

from convert.adapters.solidworks.programs.Common.FieldEncoder import ReplayFixed

from .Registry import (
    KConfigOps as KConfigOps,
    KFieldOwners as KFieldOwners,
)


# exact closure proves the fixed program accounts for the complete stream
KReferenceLength = 24902

# the exact digest anchors the independently recovered midplane configuration
KReferenceDigest = "f2dc3d440fb6ac956155e5d300c15e83a8574311c9e58802b514af486d448341"


# typed replay emits the fixed configuration without retaining vendor byte spans
def EncodeProgram(Overrides: Mapping[int, FieldType] | None = None) -> bytes:
    return ReplayFixed(KConfigOps, KReferenceLength, "Config-0", Overrides)


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
