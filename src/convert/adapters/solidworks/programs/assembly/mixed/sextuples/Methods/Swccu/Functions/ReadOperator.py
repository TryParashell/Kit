# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Swccu.Functions.ReadOperator import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "Contents/CMgr": (
            (643, 4, 19, "primitive:ulong", 631152000),
            (1483, 4, 19, "primitive:ulong", 1786398596),
            (1583, 4, 19, "primitive:ulong", 1786398596),
            (1601, 4, 19, "primitive:ulong", 0),
            (1643, 4, 19, "primitive:ulong", 0),
            (1878, 4, 19, "primitive:ulong", 1786398596),
            (1961, 4, 19, "primitive:ulong", 1786398596),
            (1979, 4, 19, "primitive:ulong", 0),
            (2021, 4, 19, "primitive:ulong", 0),
            (2256, 4, 19, "primitive:ulong", 1786398596),
            (2339, 4, 19, "primitive:ulong", 1786398596),
            (2357, 4, 19, "primitive:ulong", 0),
            (2399, 4, 19, "primitive:ulong", 0),
            (2634, 4, 19, "primitive:ulong", 1786398596),
            (2717, 4, 19, "primitive:ulong", 1786398596),
            (2735, 4, 19, "primitive:ulong", 0),
            (2777, 4, 19, "primitive:ulong", 0),
            (3012, 4, 19, "primitive:ulong", 1786398596),
            (3095, 4, 19, "primitive:ulong", 1786398596),
            (3113, 4, 19, "primitive:ulong", 0),
            (3155, 4, 19, "primitive:ulong", 0),
            (3390, 4, 19, "primitive:ulong", 1786398596),
            (3473, 4, 19, "primitive:ulong", 1786398596),
            (3491, 4, 19, "primitive:ulong", 0),
            (3533, 4, 19, "primitive:ulong", 0),
            (3746, 4, 19, "primitive:ulong", 4294967295),
        ),
        "Contents/Config-0": (
            (398, 4, 19, "primitive:ulong", 1786398610),
            (474, 4, 19, "primitive:ulong", 1786398596),
            (879, 4, 19, "primitive:ulong", 1786398610),
            (896, 4, 19, "primitive:ulong", 1786398596),
            (1301, 4, 19, "primitive:ulong", 1786398610),
            (1318, 4, 19, "primitive:ulong", 1786398596),
            (1723, 4, 19, "primitive:ulong", 1786398610),
            (1740, 4, 19, "primitive:ulong", 1786398596),
            (2145, 4, 19, "primitive:ulong", 1786398610),
            (2162, 4, 19, "primitive:ulong", 1786398596),
            (2567, 4, 19, "primitive:ulong", 1786398610),
            (2584, 4, 19, "primitive:ulong", 1786398596),
            (4670, 4, 19, "primitive:ulong", 0),
        ),
        "Contents/Config-0-ModelHeader": (
            (116, 4, 19, "primitive:ulong", 1763334902),
            (170, 4, 19, "primitive:ulong", 1763334902),
            (234, 4, 19, "primitive:ulong", 1763334902),
            (264, 4, 19, "primitive:ulong", 1763334902),
            (330, 4, 19, "primitive:ulong", 1763334902),
            (360, 4, 19, "primitive:ulong", 1763334902),
            (422, 4, 19, "primitive:ulong", 1763334902),
            (452, 4, 19, "primitive:ulong", 1763334902),
            (518, 4, 19, "primitive:ulong", 1763334902),
            (548, 4, 19, "primitive:ulong", 1763334902),
            (604, 4, 19, "primitive:ulong", 1763334902),
            (682, 4, 19, "primitive:ulong", 1763334902),
            (750, 4, 19, "primitive:ulong", 1763334902),
            (808, 4, 19, "primitive:ulong", 1763334902),
            (888, 4, 19, "primitive:ulong", 1763334902),
            (940, 4, 19, "primitive:ulong", 1763334902),
            (996, 4, 19, "primitive:ulong", 1763334902),
            (1062, 4, 19, "primitive:ulong", 1763334902),
            (1128, 4, 19, "primitive:ulong", 1763334902),
            (1194, 4, 19, "primitive:ulong", 1763334902),
            (1254, 4, 19, "primitive:ulong", 1786398596),
            (1306, 4, 19, "primitive:ulong", 1786398596),
            (1384, 4, 19, "primitive:ulong", 1786398596),
            (1440, 4, 19, "primitive:ulong", 1786398596),
            (1496, 4, 19, "primitive:ulong", 1786398596),
            (1556, 4, 19, "primitive:ulong", 1786398596),
            (1612, 4, 19, "primitive:ulong", 1786398596),
            (1682, 4, 19, "primitive:ulong", 1786398609),
            (1740, 4, 19, "primitive:ulong", 1786398609),
            (1798, 4, 19, "primitive:ulong", 1786398609),
            (1856, 4, 19, "primitive:ulong", 1786398609),
            (1914, 4, 19, "primitive:ulong", 1786398609),
            (1972, 4, 19, "primitive:ulong", 1786398610),
            (2018, 4, 19, "primitive:ulong", 1763334902),
            (2250, 4, 19, "primitive:ulong", 1862940586),
            (2268, 4, 19, "primitive:ulong", 1786398610),
            (2296, 4, 19, "primitive:ulong", 1786398610),
            (2465, 4, 19, "primitive:ulong", 1862940586),
            (2483, 4, 19, "primitive:ulong", 1786398610),
            (2511, 4, 19, "primitive:ulong", 1786398610),
            (2680, 4, 19, "primitive:ulong", 1862940586),
            (2698, 4, 19, "primitive:ulong", 1786398610),
            (2726, 4, 19, "primitive:ulong", 1786398610),
            (2767, 4, 19, "primitive:ulong", 1786398596),
            (2785, 4, 19, "primitive:ulong", 1786398610),
            (2827, 4, 19, "primitive:ulong", 0),
            (2847, 4, 19, "primitive:ulong", 1786398596),
            (2873, 4, 19, "primitive:ulong", 1786398610),
        ),
        "Contents/Config-0-ResolvedFeatures": (
            (5454, 4, 19, "primitive:ulong", 1763334902),
        ),
        "Contents/Definition": ((3591, 4, 19, "primitive:ulong", 0),),
    },
)
