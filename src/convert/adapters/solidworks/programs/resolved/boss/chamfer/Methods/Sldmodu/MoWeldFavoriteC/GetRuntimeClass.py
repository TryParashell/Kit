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
            (10619, 4, 1928, "primitive:long", 0),
            (10623, 4, 1948, "primitive:long", -1),
            (10627, 4, 2000, "primitive:ulong", 0),
            (13227, 4, 1928, "primitive:long", 0),
            (13231, 4, 1948, "primitive:long", -1),
            (13235, 4, 2000, "primitive:ulong", 0),
            (14983, 4, 1928, "primitive:long", 0),
            (14987, 4, 1948, "primitive:long", -1),
            (14991, 4, 2000, "primitive:ulong", 0),
        ),
    },
)
