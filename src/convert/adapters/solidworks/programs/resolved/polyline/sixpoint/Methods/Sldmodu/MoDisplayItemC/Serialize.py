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
            (10308, 2, 7349, "primitive:ushort", 0),
            (10316, 4, 7550, "primitive:long", 0),
            (10320, 4, 7718, "primitive:long", 0),
            (10345, 4, 7917, "primitive:long", 0),
            (10351, 4, 8109, "primitive:long", 0),
            (10355, 4, 8386, "primitive:long", 18000),
            (10359, 4, 1016, "primitive:long", 0),
            (10363, 4, 1055, "primitive:long", 524416),
            (10395, 4, 1275, "primitive:long", 0),
            (10417, 8, 1602, "primitive:double", float.fromhex("0x0.0p+0")),
            (10459, 4, 1650, "primitive:long", 1),
            (10463, 4, 1685, "primitive:long", 200),
            (10467, 1, 1897, "primitive:uchar", 0),
            (10468, 8, 1990, "primitive:double", float.fromhex("0x0.0p+0")),
            (10476, 4, 2003, "primitive:long", 0),
            (10480, 4, 2121, "primitive:long", 0),
            (
                10486,
                8,
                2319,
                "primitive:double",
                float.fromhex("-0x1.0000000000000p+0"),
            ),
            (10494, 4, 2666, "primitive:long", 0),
            (10498, 4, 3709, "primitive:long", 1),
            (10508, 4, 3748, "primitive:long", 0),
            (10512, 4, 3764, "primitive:long", 1),
            (10522, 4, 3803, "primitive:long", 0),
            (10526, 4, 3943, "primitive:long", 0),
            (10530, 4, 3959, "primitive:long", 0),
            (10534, 4, 3976, "primitive:long", -1),
            (10538, 4, 4005, "primitive:long", -1),
            (10546, 4, 4272, "primitive:long", 1),
            (10550, 4, 4288, "primitive:long", 0),
            (10560, 4, 4326, "primitive:long", 0),
            (10564, 4, 4410, "primitive:long", 0),
            (10568, 4, 4891, "primitive:long", 0),
            (10572, 4, 5194, "primitive:long", 0),
            (10576, 4, 5593, "primitive:long", 4),
            (10676, 4, 5761, "primitive:long", 2),
            (10696, 8, 5816, "primitive:double", float.fromhex("0x0.0p+0")),
            (10720, 8, 5816, "primitive:double", float.fromhex("0x0.0p+0")),
        ),
    },
)
