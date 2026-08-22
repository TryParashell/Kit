# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoWeldFavoriteC.GetRuntimeClass import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (9437, 4, 1928, "primitive:long", 0),
            (9441, 4, 1948, "primitive:long", -1),
            (9445, 4, 2000, "primitive:ulong", 0),
            (10880, 4, 1928, "primitive:long", 0),
            (10884, 4, 1948, "primitive:long", -1),
            (10888, 4, 2000, "primitive:ulong", 0),
            (14282, 4, 1928, "primitive:long", 0),
            (14286, 4, 1948, "primitive:long", -1),
            (14290, 4, 2000, "primitive:ulong", 0),
        ),
    },
)
