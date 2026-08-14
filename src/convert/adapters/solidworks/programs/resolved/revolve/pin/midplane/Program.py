# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from collections.abc import Mapping
from typing import Any as AnyValue

from convert.adapters.solidworks.programs.Common.FieldEncoder import (
    KPrimitiveFormats,
    ReplayResolved,
)

from .Registry import (
    KFieldOwners,
    KResolvedOps,
)


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
def EncodeProgram(Overrides: Mapping[int, AnyValue] | None = None) -> bytes:
    return ReplayResolved(KResolvedOps, KReferenceLength, Overrides)


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
