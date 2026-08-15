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
            (18097, 1, 953, "primitive:uchar", 1),
            (18098, 1, 973, "primitive:uchar", 1),
            (18099, 1, 993, "primitive:uchar", 0),
            (18100, 1, 1013, "primitive:uchar", 0),
            (18101, 1, 1033, "primitive:uchar", 0),
            (18102, 1, 1053, "primitive:uchar", 0),
            (18103, 4, 1073, "primitive:long", 0),
            (18107, 8, 1092, "primitive:double", float.fromhex("0x0.0p+0")),
            (18115, 1, 1105, "primitive:uchar", 1),
            (18116, 4, 1125, "primitive:long", 0),
            (18120, 4, 1144, "primitive:long", 2),
            (18124, 4, 1163, "primitive:long", 0),
            (18128, 4, 1182, "primitive:long", 0),
            (18132, 4, 1201, "primitive:long", 0),
            (18136, 4, 1223, "primitive:long", 3),
            (18140, 4, 1245, "primitive:long", 10),
            (18144, 4, 1267, "primitive:long", 0),
            (
                18148,
                8,
                1292,
                "primitive:double",
                float.fromhex("0x1.0c6f7a0b5ed8dp-20"),
            ),
            (
                18156,
                8,
                1308,
                "primitive:double",
                float.fromhex("0x1.0c6f7a0b5ed8dp-20"),
            ),
            (18164, 1, 1321, "primitive:uchar", 1),
            (18165, 1, 1344, "primitive:uchar", 1),
            (18166, 1, 1367, "primitive:uchar", 0),
            (18167, 1, 1390, "primitive:uchar", 1),
            (18168, 1, 1413, "primitive:uchar", 1),
            (18169, 1, 1436, "primitive:uchar", 1),
            (18170, 1, 1459, "primitive:uchar", 1),
            (18171, 1, 1482, "primitive:uchar", 1),
            (18172, 1, 1505, "primitive:uchar", 1),
            (18173, 1, 1528, "primitive:uchar", 0),
            (18174, 1, 1551, "primitive:uchar", 0),
            (18175, 1, 1574, "primitive:uchar", 1),
            (18264, 4, 1636, "primitive:int", 0),
            (18268, 4, 1668, "primitive:int", 0),
            (18272, 8, 1720, "primitive:uint64", 0),
            (18280, 1, 2043, "primitive:uchar", 0),
            (18281, 1, 2066, "primitive:uchar", 0),
            (18282, 1, 2089, "primitive:uchar", 0),
            (18422, 1, 2208, "primitive:uchar", 0),
            (18423, 1, 2278, "primitive:uchar", 0),
            (18424, 4, 2344, "primitive:long", 0),
            (18428, 8, 2408, "primitive:double", float.fromhex("0x1.4cec41dd1a21fp-7")),
            (18436, 4, 2498, "primitive:int", 0),
            (18440, 4, 2514, "primitive:int", 1),
            (18450, 4, 2638, "primitive:int", 1),
            (18454, 4, 2654, "primitive:int", 1),
            (18458, 4, 2670, "primitive:int", 0),
            (18462, 4, 2686, "primitive:int", 0),
            (18466, 8, 2741, "primitive:double", float.fromhex("0x0.0p+0")),
            (
                18474,
                8,
                2814,
                "primitive:double",
                float.fromhex("0x1.0624dd2f1a9fcp-10"),
            ),
            (18482, 4, 2827, "primitive:int", 1),
            (18486, 1, 2887, "primitive:uchar", 0),
            (18487, 1, 2957, "primitive:uchar", 0),
        ),
    },
)
