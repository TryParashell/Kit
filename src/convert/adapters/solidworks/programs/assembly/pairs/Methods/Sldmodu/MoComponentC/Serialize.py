# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoComponentC.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "Contents/CMgr": (
            (1146, 4, 7212, "primitive:long", -1),
            (1154, 4, 27187, "primitive:ulong", 101),
            (1158, 4, 7511, "primitive:long", 0),
            (1164, 4, 7826, "primitive:long", 273),
            (1168, 4, 7930, "primitive:long", 0),
            (1172, 4, 7994, "primitive:long", 0),
            (1176, 4, 8189, "primitive:long", 0),
            (1188, 1, 8938, "primitive:uchar", 0),
            (1697, 4, 23934, "primitive:long", 0),
            (1719, 4, 7212, "primitive:long", 0),
            (1727, 4, 27187, "primitive:ulong", 101),
            (1731, 4, 7511, "primitive:long", 0),
            (1737, 4, 7826, "primitive:long", 1048849),
            (1741, 4, 7930, "primitive:long", 0),
            (1745, 4, 7994, "primitive:long", 0),
            (1749, 4, 8189, "primitive:long", 0),
            (1761, 1, 8938, "primitive:uchar", 0),
            (2121, 4, 23934, "primitive:long", 0),
            (2143, 4, 7212, "primitive:long", 0),
            (2151, 4, 27187, "primitive:ulong", 101),
            (2155, 4, 7511, "primitive:long", 0),
            (2161, 4, 7826, "primitive:long", 1048849),
            (2165, 4, 7930, "primitive:long", 0),
            (2169, 4, 7994, "primitive:long", 0),
            (2173, 4, 8189, "primitive:long", 0),
            (2185, 1, 8938, "primitive:uchar", 0),
            (2194, 4, 22256, "primitive:long", 0),
            (2198, 4, 22283, "primitive:long", 1),
            (2208, 4, 13031, "primitive:int", 1),
            (2216, 4, 13087, "primitive:int", 0),
            (2220, 4, 13366, "primitive:int", 0),
            (2228, 4, 13440, "primitive:int", 0),
            (2248, 4, 13676, "primitive:int", 0),
            (2252, 4, 13857, "primitive:int", 0),
            (2256, 4, 14309, "primitive:int", 0),
            (2260, 4, 15292, "primitive:int", 0),
            (2264, 4, 15313, "primitive:int", 0),
            (2292, 4, 17006, "primitive:int", 0),
            (2298, 4, 17234, "primitive:int", 0),
            (2302, 4, 17301, "primitive:int", 2),
            (2306, 4, 17367, "primitive:int", 0),
            (2330, 4, 17995, "primitive:long", 0),
            (2334, 4, 18764, "primitive:long", 0),
        ),
    },
)
