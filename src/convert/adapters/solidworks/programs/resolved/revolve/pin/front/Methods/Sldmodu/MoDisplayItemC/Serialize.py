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
            (10444, 2, 7349, "primitive:ushort", 0),
            (10452, 4, 7550, "primitive:long", 0),
            (10456, 4, 7718, "primitive:long", 0),
            (10481, 4, 7917, "primitive:long", 0),
            (10487, 4, 8109, "primitive:long", 0),
            (10491, 4, 8386, "primitive:long", 18000),
            (10495, 4, 1016, "primitive:long", 0),
            (10499, 4, 1055, "primitive:long", 524416),
            (10531, 4, 1275, "primitive:long", 0),
            (10553, 8, 1602, "primitive:double", float.fromhex("0x0.0p+0")),
            (10595, 4, 1650, "primitive:long", 1),
            (10599, 4, 1685, "primitive:long", 200),
            (10603, 1, 1897, "primitive:uchar", 0),
            (10604, 8, 1990, "primitive:double", float.fromhex("0x0.0p+0")),
            (10612, 4, 2003, "primitive:long", 0),
            (10616, 4, 2121, "primitive:long", 0),
            (
                10622,
                8,
                2319,
                "primitive:double",
                float.fromhex("-0x1.0000000000000p+0"),
            ),
            (10630, 4, 2666, "primitive:long", 0),
            (10634, 4, 3709, "primitive:long", 1),
            (10644, 4, 3748, "primitive:long", 0),
            (10648, 4, 3764, "primitive:long", 1),
            (10658, 4, 3803, "primitive:long", 0),
            (10662, 4, 3943, "primitive:long", 0),
            (10666, 4, 3959, "primitive:long", 0),
            (10670, 4, 3976, "primitive:long", -1),
            (10674, 4, 4005, "primitive:long", -1),
            (10682, 4, 4272, "primitive:long", 1),
            (10686, 4, 4288, "primitive:long", 0),
            (10696, 4, 4326, "primitive:long", 0),
            (10700, 4, 4410, "primitive:long", 0),
            (10704, 4, 4891, "primitive:long", 0),
            (10708, 4, 5194, "primitive:long", 0),
            (10712, 4, 5593, "primitive:long", 4),
            (10812, 4, 5761, "primitive:long", 2),
            (10832, 8, 5816, "primitive:double", float.fromhex("0x0.0p+0")),
            (10856, 8, 5816, "primitive:double", float.fromhex("0x0.0p+0")),
        ),
    },
)
