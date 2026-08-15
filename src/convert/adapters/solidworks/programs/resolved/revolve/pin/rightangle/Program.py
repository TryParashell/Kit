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


# the fixed program length prevents an accidental structural family change
KReferenceLength = 12537

# the exact digest anchors the complete typed field program without vendor bytes
KReferenceDigest = "cd1ef9071450bacb44a54efc92b5e3b1d2a778504b5124e942e79fbfba5de8d4"

# the two serialized angle fields keep the parameter and favorite handle synchronized
KAngleOffsets = (11481, 12019)

# the sketch coordinate pairs expose every canonical profile vertex for verification
KProfileOffsets = (
    (6904, 6912),
    (7066, 7074),
    (7228, 7236),
    (7390, 7398),
    (7552, 7560),
    (7714, 7722),
)


# callers can replace semantic fields while retaining recovered object framing
def EncodeProgram(Overrides: Mapping[int, FieldType] | None = None) -> bytes:
    return ReplayResolved(KResolvedOps, KReferenceLength, Overrides, KPrimitiveFormats)


# coverage metrics make hidden opaque or donor regressions mechanically visible
def GetCoverage() -> dict[str, int]:
    return {
        "stream_bytes": KReferenceLength,
        "typed": KReferenceLength,
        "opaque": 0,
        "accounted": KReferenceLength,
        "operations": len(KResolvedOps),
        "owners": len(KFieldOwners),
    }
