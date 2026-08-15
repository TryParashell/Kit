# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Sldmodu.SgSketch.OffsetEdgesInThreeD import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (5689, 4, 37887, "primitive:long", 0),
            (5693, 4, 37887, "primitive:long", 0),
            (5697, 4, 37887, "primitive:long", 0),
            (5701, 4, 37887, "primitive:long", 0),
            (7736, 4, 37887, "primitive:long", 0),
            (7740, 4, 37887, "primitive:long", 0),
            (7744, 4, 37887, "primitive:long", 0),
            (7748, 4, 37887, "primitive:long", 0),
        ),
    },
)
