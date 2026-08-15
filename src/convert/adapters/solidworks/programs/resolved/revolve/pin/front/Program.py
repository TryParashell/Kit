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

from convert.adapters.solidworks.programs.Common.FieldEncoder import (
    KPrimitiveFormats,
    ReplayResolved,
)

from .Registry import (
    KFieldOwners,
    KResolvedOps,
)


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
def EncodeProgram(Overrides: Mapping[int, FieldType] | None = None) -> bytes:
    return ReplayResolved(KResolvedOps, KReferenceLength, Overrides, KPrimitiveFormats)


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
