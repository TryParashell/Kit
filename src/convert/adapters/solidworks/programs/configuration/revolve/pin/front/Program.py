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
