# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoDisplayItemC.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (10716, 2, 7349, "primitive:ushort", 0),
            (10724, 4, 7550, "primitive:long", 0),
            (10728, 4, 7718, "primitive:long", 0),
            (10753, 4, 7917, "primitive:long", 0),
            (10759, 4, 8109, "primitive:long", 0),
            (10763, 4, 8386, "primitive:long", 18000),
            (10767, 4, 1016, "primitive:long", 0),
            (10771, 4, 1055, "primitive:long", 524416),
            (10803, 4, 1275, "primitive:long", 0),
            (10825, 8, 1602, "primitive:double", float.fromhex("0x0.0p+0")),
            (10867, 4, 1650, "primitive:long", 1),
            (10871, 4, 1685, "primitive:long", 200),
            (10875, 1, 1897, "primitive:uchar", 0),
            (10876, 8, 1990, "primitive:double", float.fromhex("0x0.0p+0")),
            (10884, 4, 2003, "primitive:long", 0),
            (10888, 4, 2121, "primitive:long", 0),
            (
                10894,
                8,
                2319,
                "primitive:double",
                float.fromhex("-0x1.0000000000000p+0"),
            ),
            (10902, 4, 2666, "primitive:long", 0),
            (10906, 4, 3709, "primitive:long", 1),
            (10916, 4, 3748, "primitive:long", 0),
            (10920, 4, 3764, "primitive:long", 1),
            (10930, 4, 3803, "primitive:long", 0),
            (10934, 4, 3943, "primitive:long", 0),
            (10938, 4, 3959, "primitive:long", 0),
            (10942, 4, 3976, "primitive:long", -1),
            (10946, 4, 4005, "primitive:long", -1),
            (10954, 4, 4272, "primitive:long", 1),
            (10958, 4, 4288, "primitive:long", 0),
            (10968, 4, 4326, "primitive:long", 0),
            (10972, 4, 4410, "primitive:long", 0),
            (10976, 4, 4891, "primitive:long", 0),
            (10980, 4, 5194, "primitive:long", 0),
            (10984, 4, 5593, "primitive:long", 4),
            (11084, 4, 5761, "primitive:long", 2),
            (11104, 8, 5816, "primitive:double", float.fromhex("0x0.0p+0")),
            (11128, 8, 5816, "primitive:double", float.fromhex("0x0.0p+0")),
        ),
    },
)
