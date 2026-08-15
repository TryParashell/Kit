# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Sldarchiveu.Functions.MoGetModelnameFromPath import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "Contents/CMgr": (
            (1646, 1, 3156, "primitive:uchar", 0),
            (1651, 4, 3701, "primitive:long", 0),
            (1655, 4, 3762, "primitive:long", 1),
            (1659, 4, 3826, "primitive:long", -1),
            (1681, 4, 3839, "primitive:long", 0),
            (1685, 4, 3934, "primitive:long", 0),
            (1693, 4, 4388, "primitive:long", 0),
            (2070, 1, 3156, "primitive:uchar", 0),
            (2075, 4, 3701, "primitive:long", 0),
            (2079, 4, 3762, "primitive:long", 1),
            (2083, 4, 3826, "primitive:long", -1),
            (2105, 4, 3839, "primitive:long", 0),
            (2109, 4, 3934, "primitive:long", 0),
            (2117, 4, 4388, "primitive:long", 0),
        ),
        "Contents/Config-0-ModelHeader": (
            (2219, 1, 3156, "primitive:uchar", 0),
            (2224, 4, 3701, "primitive:long", 2),
            (2228, 4, 3762, "primitive:long", 0),
            (2232, 4, 3826, "primitive:long", 0),
            (2240, 4, 3839, "primitive:long", -1),
            (2244, 4, 3934, "primitive:long", 0),
            (2252, 4, 4388, "primitive:long", 0),
            (2306, 1, 3156, "primitive:uchar", 8),
            (2311, 4, 3701, "primitive:long", 1),
            (2315, 4, 3762, "primitive:long", 0),
            (2319, 4, 3826, "primitive:long", -1),
            (2341, 4, 3839, "primitive:long", 0),
            (2345, 4, 3934, "primitive:long", 0),
            (2353, 4, 4388, "primitive:long", 0),
        ),
    },
)
