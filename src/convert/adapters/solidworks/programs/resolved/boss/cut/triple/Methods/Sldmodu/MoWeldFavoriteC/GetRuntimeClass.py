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
            (11214, 4, 1928, "primitive:long", 0),
            (11218, 4, 1948, "primitive:long", -1),
            (11222, 4, 2000, "primitive:ulong", 0),
            (16394, 4, 1928, "primitive:long", 0),
            (16398, 4, 1948, "primitive:long", -1),
            (16402, 4, 2000, "primitive:ulong", 0),
            (21464, 4, 1928, "primitive:long", 0),
            (21468, 4, 1948, "primitive:long", -1),
            (21472, 4, 2000, "primitive:ulong", 0),
            (26538, 4, 1928, "primitive:long", 0),
            (26542, 4, 1948, "primitive:long", -1),
            (26546, 4, 2000, "primitive:ulong", 0),
        ),
    },
)
