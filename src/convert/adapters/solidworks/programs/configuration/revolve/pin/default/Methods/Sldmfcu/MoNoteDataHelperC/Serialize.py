# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Sldmfcu.MoNoteDataHelperC.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "Configuration": (
            (16319, 1, 953, "primitive:uchar", 1),
            (16320, 1, 973, "primitive:uchar", 1),
            (16321, 1, 993, "primitive:uchar", 0),
            (16322, 1, 1013, "primitive:uchar", 0),
            (16323, 1, 1033, "primitive:uchar", 0),
            (16324, 1, 1053, "primitive:uchar", 0),
            (16325, 4, 1073, "primitive:long", 0),
            (16329, 8, 1092, "primitive:double", float.fromhex("0x0.0p+0")),
            (16337, 1, 1105, "primitive:uchar", 1),
            (16338, 4, 1125, "primitive:long", 0),
            (16342, 4, 1144, "primitive:long", 2),
            (16346, 4, 1163, "primitive:long", 0),
            (16350, 4, 1182, "primitive:long", 0),
            (16354, 4, 1201, "primitive:long", 0),
            (16358, 4, 1223, "primitive:long", 3),
            (16362, 4, 1245, "primitive:long", 10),
            (16366, 4, 1267, "primitive:long", 0),
            (
                16370,
                8,
                1292,
                "primitive:double",
                float.fromhex("0x1.0c6f7a0b5ed8dp-20"),
            ),
            (
                16378,
                8,
                1308,
                "primitive:double",
                float.fromhex("0x1.0c6f7a0b5ed8dp-20"),
            ),
            (16386, 1, 1321, "primitive:uchar", 1),
            (16387, 1, 1344, "primitive:uchar", 1),
            (16388, 1, 1367, "primitive:uchar", 0),
            (16389, 1, 1390, "primitive:uchar", 1),
            (16390, 1, 1413, "primitive:uchar", 1),
            (16391, 1, 1436, "primitive:uchar", 1),
            (16392, 1, 1459, "primitive:uchar", 1),
            (16393, 1, 1482, "primitive:uchar", 1),
            (16394, 1, 1505, "primitive:uchar", 1),
            (16395, 1, 1528, "primitive:uchar", 0),
            (16396, 1, 1551, "primitive:uchar", 0),
            (16397, 1, 1574, "primitive:uchar", 1),
            (16486, 4, 1636, "primitive:int", 0),
            (16490, 4, 1668, "primitive:int", 0),
            (16494, 8, 1720, "primitive:uint64", 0),
            (16502, 1, 2043, "primitive:uchar", 0),
            (16503, 1, 2066, "primitive:uchar", 0),
            (16504, 1, 2089, "primitive:uchar", 0),
            (16644, 1, 2208, "primitive:uchar", 0),
            (16645, 1, 2278, "primitive:uchar", 0),
            (16646, 4, 2344, "primitive:long", 0),
            (16650, 8, 2408, "primitive:double", float.fromhex("0x1.4cec41dd1a21fp-7")),
            (16658, 4, 2498, "primitive:int", 0),
            (16662, 4, 2514, "primitive:int", 1),
            (16672, 4, 2638, "primitive:int", 1),
            (16676, 4, 2654, "primitive:int", 1),
            (16680, 4, 2670, "primitive:int", 0),
            (16684, 4, 2686, "primitive:int", 0),
            (16688, 8, 2741, "primitive:double", float.fromhex("0x0.0p+0")),
            (
                16696,
                8,
                2814,
                "primitive:double",
                float.fromhex("0x1.0624dd2f1a9fcp-10"),
            ),
            (16704, 4, 2827, "primitive:int", 1),
            (16708, 1, 2887, "primitive:uchar", 0),
            (16709, 1, 2957, "primitive:uchar", 0),
        ),
    },
)
