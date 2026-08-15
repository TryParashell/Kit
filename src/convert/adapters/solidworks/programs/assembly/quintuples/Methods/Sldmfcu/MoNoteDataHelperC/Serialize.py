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
            (18557, 1, 953, "primitive:uchar", 1),
            (18558, 1, 973, "primitive:uchar", 1),
            (18559, 1, 993, "primitive:uchar", 0),
            (18560, 1, 1013, "primitive:uchar", 0),
            (18561, 1, 1033, "primitive:uchar", 0),
            (18562, 1, 1053, "primitive:uchar", 0),
            (18563, 4, 1073, "primitive:long", 0),
            (18567, 8, 1092, "primitive:double", float.fromhex("0x0.0p+0")),
            (18575, 1, 1105, "primitive:uchar", 1),
            (18576, 4, 1125, "primitive:long", 0),
            (18580, 4, 1144, "primitive:long", 2),
            (18584, 4, 1163, "primitive:long", 0),
            (18588, 4, 1182, "primitive:long", 0),
            (18592, 4, 1201, "primitive:long", 0),
            (18596, 4, 1223, "primitive:long", 3),
            (18600, 4, 1245, "primitive:long", 10),
            (18604, 4, 1267, "primitive:long", 0),
            (
                18608,
                8,
                1292,
                "primitive:double",
                float.fromhex("0x1.0c6f7a0b5ed8dp-20"),
            ),
            (
                18616,
                8,
                1308,
                "primitive:double",
                float.fromhex("0x1.0c6f7a0b5ed8dp-20"),
            ),
            (18624, 1, 1321, "primitive:uchar", 1),
            (18625, 1, 1344, "primitive:uchar", 1),
            (18626, 1, 1367, "primitive:uchar", 0),
            (18627, 1, 1390, "primitive:uchar", 1),
            (18628, 1, 1413, "primitive:uchar", 1),
            (18629, 1, 1436, "primitive:uchar", 1),
            (18630, 1, 1459, "primitive:uchar", 1),
            (18631, 1, 1482, "primitive:uchar", 1),
            (18632, 1, 1505, "primitive:uchar", 1),
            (18633, 1, 1528, "primitive:uchar", 0),
            (18634, 1, 1551, "primitive:uchar", 0),
            (18635, 1, 1574, "primitive:uchar", 1),
            (18724, 4, 1636, "primitive:int", 0),
            (18728, 4, 1668, "primitive:int", 0),
            (18732, 8, 1720, "primitive:uint64", 0),
            (18740, 1, 2043, "primitive:uchar", 0),
            (18741, 1, 2066, "primitive:uchar", 0),
            (18742, 1, 2089, "primitive:uchar", 0),
            (18882, 1, 2208, "primitive:uchar", 0),
            (18883, 1, 2278, "primitive:uchar", 0),
            (18884, 4, 2344, "primitive:long", 0),
            (18888, 8, 2408, "primitive:double", float.fromhex("0x1.4cec41dd1a21fp-7")),
            (18896, 4, 2498, "primitive:int", 0),
            (18900, 4, 2514, "primitive:int", 1),
            (18910, 4, 2638, "primitive:int", 1),
            (18914, 4, 2654, "primitive:int", 1),
            (18918, 4, 2670, "primitive:int", 0),
            (18922, 4, 2686, "primitive:int", 0),
            (18926, 8, 2741, "primitive:double", float.fromhex("0x0.0p+0")),
            (
                18934,
                8,
                2814,
                "primitive:double",
                float.fromhex("0x1.0624dd2f1a9fcp-10"),
            ),
            (18942, 4, 2827, "primitive:int", 1),
            (18946, 1, 2887, "primitive:uchar", 0),
            (18947, 1, 2957, "primitive:uchar", 0),
        ),
    },
)
