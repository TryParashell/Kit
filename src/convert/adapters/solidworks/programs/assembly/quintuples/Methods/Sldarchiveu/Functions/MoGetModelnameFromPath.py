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
            (2494, 1, 3156, "primitive:uchar", 0),
            (2499, 4, 3701, "primitive:long", 0),
            (2503, 4, 3762, "primitive:long", 1),
            (2507, 4, 3826, "primitive:long", -1),
            (2529, 4, 3839, "primitive:long", 0),
            (2533, 4, 3934, "primitive:long", 0),
            (2541, 4, 4388, "primitive:long", 0),
            (2918, 1, 3156, "primitive:uchar", 0),
            (2923, 4, 3701, "primitive:long", 0),
            (2927, 4, 3762, "primitive:long", 1),
            (2931, 4, 3826, "primitive:long", -1),
            (2953, 4, 3839, "primitive:long", 0),
            (2957, 4, 3934, "primitive:long", 0),
            (2965, 4, 4388, "primitive:long", 0),
            (3342, 1, 3156, "primitive:uchar", 0),
            (3347, 4, 3701, "primitive:long", 0),
            (3351, 4, 3762, "primitive:long", 1),
            (3355, 4, 3826, "primitive:long", -1),
            (3377, 4, 3839, "primitive:long", 0),
            (3381, 4, 3934, "primitive:long", 0),
            (3389, 4, 4388, "primitive:long", 0),
        ),
        "Contents/Config-0-ModelHeader": (
            (2531, 1, 3156, "primitive:uchar", 0),
            (2536, 4, 3701, "primitive:long", 5),
            (2540, 4, 3762, "primitive:long", 0),
            (2544, 4, 3826, "primitive:long", 0),
            (2552, 4, 3839, "primitive:long", -1),
            (2556, 4, 3934, "primitive:long", 0),
            (2564, 4, 4388, "primitive:long", 0),
            (2618, 1, 3156, "primitive:uchar", 8),
            (2623, 4, 3701, "primitive:long", 1),
            (2627, 4, 3762, "primitive:long", 0),
            (2631, 4, 3826, "primitive:long", -1),
            (2653, 4, 3839, "primitive:long", 0),
            (2657, 4, 3934, "primitive:long", 0),
            (2665, 4, 4388, "primitive:long", 0),
        ),
    },
)
