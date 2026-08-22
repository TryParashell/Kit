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
            (1794, 1, 3156, "primitive:uchar", 8),
            (1799, 4, 3701, "primitive:long", 0),
            (1803, 4, 3762, "primitive:long", 1),
            (1807, 4, 3826, "primitive:long", -1),
            (1829, 4, 3839, "primitive:long", 0),
            (1833, 4, 3934, "primitive:long", 0),
            (1841, 4, 4388, "primitive:long", 0),
            (2218, 1, 3156, "primitive:uchar", 8),
            (2223, 4, 3701, "primitive:long", 0),
            (2227, 4, 3762, "primitive:long", 1),
            (2231, 4, 3826, "primitive:long", -1),
            (2253, 4, 3839, "primitive:long", 0),
            (2257, 4, 3934, "primitive:long", 0),
            (2265, 4, 4388, "primitive:long", 0),
            (2642, 1, 3156, "primitive:uchar", 0),
            (2647, 4, 3701, "primitive:long", 0),
            (2651, 4, 3762, "primitive:long", 1),
            (2655, 4, 3826, "primitive:long", -1),
            (2677, 4, 3839, "primitive:long", 0),
            (2681, 4, 3934, "primitive:long", 0),
            (2689, 4, 4388, "primitive:long", 0),
        ),
        "Contents/Config-0-ModelHeader": (
            (2323, 1, 3156, "primitive:uchar", 0),
            (2328, 4, 3701, "primitive:long", 3),
            (2332, 4, 3762, "primitive:long", 0),
            (2336, 4, 3826, "primitive:long", 0),
            (2344, 4, 3839, "primitive:long", -1),
            (2348, 4, 3934, "primitive:long", 0),
            (2356, 4, 4388, "primitive:long", 0),
            (2538, 1, 3156, "primitive:uchar", 8),
            (2543, 4, 3701, "primitive:long", 1),
            (2547, 4, 3762, "primitive:long", 0),
            (2551, 4, 3826, "primitive:long", -1),
            (2573, 4, 3839, "primitive:long", 0),
            (2577, 4, 3934, "primitive:long", 0),
            (2585, 4, 4388, "primitive:long", 0),
        ),
    },
)
