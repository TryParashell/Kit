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
        "Contents/Config-0": (
            (17959, 1, 953, "primitive:uchar", 1),
            (17960, 1, 973, "primitive:uchar", 1),
            (17961, 1, 993, "primitive:uchar", 0),
            (17962, 1, 1013, "primitive:uchar", 0),
            (17963, 1, 1033, "primitive:uchar", 0),
            (17964, 1, 1053, "primitive:uchar", 0),
            (17965, 4, 1073, "primitive:long", 0),
            (17969, 8, 1092, "primitive:double", float.fromhex("0x0.0p+0")),
            (17977, 1, 1105, "primitive:uchar", 1),
            (17978, 4, 1125, "primitive:long", 0),
            (17982, 4, 1144, "primitive:long", 2),
            (17986, 4, 1163, "primitive:long", 0),
            (17990, 4, 1182, "primitive:long", 0),
            (17994, 4, 1201, "primitive:long", 0),
            (17998, 4, 1223, "primitive:long", 3),
            (18002, 4, 1245, "primitive:long", 10),
            (18006, 4, 1267, "primitive:long", 0),
            (
                18010,
                8,
                1292,
                "primitive:double",
                float.fromhex("0x1.0c6f7a0b5ed8dp-20"),
            ),
            (
                18018,
                8,
                1308,
                "primitive:double",
                float.fromhex("0x1.0c6f7a0b5ed8dp-20"),
            ),
            (18026, 1, 1321, "primitive:uchar", 1),
            (18027, 1, 1344, "primitive:uchar", 1),
            (18028, 1, 1367, "primitive:uchar", 0),
            (18029, 1, 1390, "primitive:uchar", 1),
            (18030, 1, 1413, "primitive:uchar", 1),
            (18031, 1, 1436, "primitive:uchar", 1),
            (18032, 1, 1459, "primitive:uchar", 1),
            (18033, 1, 1482, "primitive:uchar", 1),
            (18034, 1, 1505, "primitive:uchar", 1),
            (18035, 1, 1528, "primitive:uchar", 0),
            (18036, 1, 1551, "primitive:uchar", 0),
            (18037, 1, 1574, "primitive:uchar", 1),
            (18126, 4, 1636, "primitive:int", 0),
            (18130, 4, 1668, "primitive:int", 0),
            (18134, 8, 1720, "primitive:uint64", 0),
            (18142, 1, 2043, "primitive:uchar", 0),
            (18143, 1, 2066, "primitive:uchar", 0),
            (18144, 1, 2089, "primitive:uchar", 0),
            (18284, 1, 2208, "primitive:uchar", 0),
            (18285, 1, 2278, "primitive:uchar", 0),
            (18286, 4, 2344, "primitive:long", 0),
            (18290, 8, 2408, "primitive:double", float.fromhex("0x1.4cec41dd1a21fp-7")),
            (18298, 4, 2498, "primitive:int", 0),
            (18302, 4, 2514, "primitive:int", 1),
            (18312, 4, 2638, "primitive:int", 1),
            (18316, 4, 2654, "primitive:int", 1),
            (18320, 4, 2670, "primitive:int", 0),
            (18324, 4, 2686, "primitive:int", 0),
            (18328, 8, 2741, "primitive:double", float.fromhex("0x0.0p+0")),
            (
                18336,
                8,
                2814,
                "primitive:double",
                float.fromhex("0x1.0624dd2f1a9fcp-10"),
            ),
            (18344, 4, 2827, "primitive:int", 1),
            (18348, 1, 2887, "primitive:uchar", 0),
            (18349, 1, 2957, "primitive:uchar", 0),
        ),
    },
)
