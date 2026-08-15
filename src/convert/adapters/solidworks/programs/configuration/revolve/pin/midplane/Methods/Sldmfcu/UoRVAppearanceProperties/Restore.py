# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Sldmfcu.UoRVAppearanceProperties.Restore import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "Configuration": (
            (222, 4, 46, "primitive:int", 5),
            (226, 4, 59, "primitive:int", 0),
            (262, 1, 85, "primitive:uchar", 3),
            (263, 4, 98, "primitive:ulong", 15651274),
            (267, 4, 111, "primitive:float", float.fromhex("0x1.0000000000000p+0")),
            (271, 4, 124, "primitive:float", float.fromhex("0x0.0p+0")),
            (275, 4, 137, "primitive:float", float.fromhex("0x0.0p+0")),
            (279, 4, 150, "primitive:float", float.fromhex("0x0.0p+0")),
            (283, 4, 163, "primitive:float", float.fromhex("0x1.0000000000000p+0")),
            (287, 4, 176, "primitive:float", float.fromhex("0x0.0p+0")),
            (291, 4, 189, "primitive:float", float.fromhex("0x0.0p+0")),
            (295, 4, 202, "primitive:float", float.fromhex("0x0.0p+0")),
            (299, 4, 215, "primitive:float", float.fromhex("0x0.0p+0")),
            (303, 4, 228, "primitive:float", float.fromhex("0x1.0000000000000p+0")),
            (307, 4, 257, "primitive:int", 1),
            (311, 4, 270, "primitive:float", float.fromhex("0x1.3333340000000p-3")),
            (315, 4, 334, "primitive:float", float.fromhex("0x0.0p+0")),
            (319, 4, 363, "primitive:float", float.fromhex("-0x1.0000000000000p+0")),
            (323, 4, 376, "primitive:float", float.fromhex("-0x1.0000000000000p+0")),
            (327, 4, 389, "primitive:float", float.fromhex("-0x1.0000000000000p+0")),
            (331, 4, 402, "primitive:int", 0),
            (335, 4, 435, "primitive:float", float.fromhex("0x0.0p+0")),
            (339, 4, 448, "primitive:float", float.fromhex("0x0.0p+0")),
            (473, 4, 604, "primitive:ulong", 16777215),
            (477, 4, 617, "primitive:float", float.fromhex("0x1.3333340000000p-1")),
            (481, 4, 630, "primitive:float", float.fromhex("0x1.0000000000000p+0")),
            (489, 4, 795, "primitive:float", float.fromhex("0x1.0624de0000000p-10")),
            (493, 4, 811, "primitive:float", float.fromhex("0x1.0624de0000000p-10")),
            (497, 4, 827, "primitive:float", float.fromhex("0x0.0p+0")),
            (501, 4, 843, "primitive:int", 320),
            (505, 4, 902, "primitive:float", float.fromhex("0x0.0p+0")),
            (509, 4, 915, "primitive:int", 0),
            (513, 4, 940, "primitive:float", float.fromhex("0x1.0000000000000p+0")),
            (517, 4, 956, "primitive:float", float.fromhex("0x0.0p+0")),
            (521, 4, 972, "primitive:float", float.fromhex("0x0.0p+0")),
            (525, 4, 988, "primitive:float", float.fromhex("0x0.0p+0")),
            (529, 4, 1004, "primitive:float", float.fromhex("0x1.0000000000000p+0")),
            (533, 4, 1020, "primitive:float", float.fromhex("0x0.0p+0")),
            (537, 4, 1036, "primitive:float", float.fromhex("0x0.0p+0")),
            (541, 4, 1052, "primitive:float", float.fromhex("0x0.0p+0")),
            (545, 4, 1084, "primitive:float", float.fromhex("0x1.0000000000000p+0")),
            (549, 4, 1100, "primitive:float", float.fromhex("0x1.6800000000000p+6")),
            (553, 4, 1132, "primitive:float", float.fromhex("0x1.0000000000000p+0")),
            (557, 4, 1164, "primitive:float", float.fromhex("-0x1.0000000000000p+0")),
            (561, 4, 1180, "primitive:float", float.fromhex("-0x1.0000000000000p+0")),
            (569, 4, 1244, "primitive:float", float.fromhex("0x0.0p+0")),
            (585, 4, 1328, "primitive:float", float.fromhex("0x0.0p+0")),
            (589, 4, 1344, "primitive:float", float.fromhex("0x0.0p+0")),
            (593, 4, 1360, "primitive:float", float.fromhex("0x0.0p+0")),
            (597, 4, 1376, "primitive:float", float.fromhex("0x0.0p+0")),
            (601, 4, 1392, "primitive:float", float.fromhex("0x0.0p+0")),
            (605, 4, 1408, "primitive:float", float.fromhex("0x0.0p+0")),
            (609, 4, 1424, "primitive:float", float.fromhex("0x0.0p+0")),
            (613, 4, 1440, "primitive:float", float.fromhex("0x0.0p+0")),
            (617, 4, 1456, "primitive:float", float.fromhex("0x0.0p+0")),
            (621, 4, 1472, "primitive:float", float.fromhex("0x0.0p+0")),
            (625, 4, 1488, "primitive:float", float.fromhex("0x0.0p+0")),
            (629, 4, 1504, "primitive:float", float.fromhex("0x0.0p+0")),
            (633, 4, 1520, "primitive:float", float.fromhex("0x0.0p+0")),
            (637, 4, 1536, "primitive:float", float.fromhex("0x0.0p+0")),
            (641, 4, 1552, "primitive:float", float.fromhex("0x0.0p+0")),
            (645, 4, 1568, "primitive:float", float.fromhex("0x0.0p+0")),
            (649, 4, 1584, "primitive:float", float.fromhex("0x0.0p+0")),
            (653, 4, 1600, "primitive:int", 0),
            (657, 4, 1616, "primitive:int", 0),
            (661, 4, 1632, "primitive:int", 0),
            (665, 4, 1648, "primitive:int", 0),
            (669, 4, 1664, "primitive:int", 0),
            (673, 4, 1680, "primitive:int", 0),
        ),
    },
)
