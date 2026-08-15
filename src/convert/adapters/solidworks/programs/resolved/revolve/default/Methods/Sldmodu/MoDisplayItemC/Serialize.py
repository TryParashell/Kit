# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Owners.Sldmodu.MoDisplayItemC.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (10314, 2, 7349, "primitive:ushort", 0),
            (10322, 4, 7550, "primitive:long", 0),
            (10326, 4, 7718, "primitive:long", 0),
            (10351, 4, 7917, "primitive:long", 0),
            (10357, 4, 8109, "primitive:long", 0),
            (10361, 4, 8386, "primitive:long", 18000),
            (10365, 4, 1016, "primitive:long", 0),
            (10369, 4, 1055, "primitive:long", 524416),
            (10401, 4, 1275, "primitive:long", 0),
            (10423, 8, 1602, "primitive:double", float.fromhex("0x0.0p+0")),
            (10465, 4, 1650, "primitive:long", 1),
            (10469, 4, 1685, "primitive:long", 200),
            (10473, 1, 1897, "primitive:uchar", 0),
            (10474, 8, 1990, "primitive:double", float.fromhex("0x0.0p+0")),
            (10482, 4, 2003, "primitive:long", 0),
            (10486, 4, 2121, "primitive:long", 0),
            (
                10492,
                8,
                2319,
                "primitive:double",
                float.fromhex("-0x1.0000000000000p+0"),
            ),
            (10500, 4, 2666, "primitive:long", 0),
            (10504, 4, 3709, "primitive:long", 1),
            (10514, 4, 3748, "primitive:long", 0),
            (10518, 4, 3764, "primitive:long", 1),
            (10528, 4, 3803, "primitive:long", 0),
            (10532, 4, 3943, "primitive:long", 0),
            (10536, 4, 3959, "primitive:long", 0),
            (10540, 4, 3976, "primitive:long", -1),
            (10544, 4, 4005, "primitive:long", -1),
            (10552, 4, 4272, "primitive:long", 1),
            (10556, 4, 4288, "primitive:long", 0),
            (10566, 4, 4326, "primitive:long", 0),
            (10570, 4, 4410, "primitive:long", 0),
            (10574, 4, 4891, "primitive:long", 0),
            (10578, 4, 5194, "primitive:long", 0),
            (10582, 4, 5593, "primitive:long", 4),
            (10682, 4, 5761, "primitive:long", 2),
            (10702, 8, 5816, "primitive:double", float.fromhex("0x0.0p+0")),
            (10726, 8, 5816, "primitive:double", float.fromhex("0x0.0p+0")),
        ),
    },
)
