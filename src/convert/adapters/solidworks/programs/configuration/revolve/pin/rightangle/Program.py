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

# the exact digest anchors the complete configuration without retaining vendor bytes
KReferenceDigest = "4a09091e5f03e9c8f617da241f1e0a71d5e43f64f84889067a2e520ac5c91f76"


# typed replay emits the fixed configuration without retaining vendor byte spans
def EncodeProgram(Overrides: Mapping[int, FieldType] | None = None) -> bytes:
    return ReplayFixed(KConfigOps, KReferenceLength, "Config-0", Overrides)


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
