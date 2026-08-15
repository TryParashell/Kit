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
            (16289, 1, 953, "primitive:uchar", 1),
            (16290, 1, 973, "primitive:uchar", 1),
            (16291, 1, 993, "primitive:uchar", 0),
            (16292, 1, 1013, "primitive:uchar", 0),
            (16293, 1, 1033, "primitive:uchar", 0),
            (16294, 1, 1053, "primitive:uchar", 0),
            (16295, 4, 1073, "primitive:long", 0),
            (16299, 8, 1092, "primitive:double", float.fromhex("0x0.0p+0")),
            (16307, 1, 1105, "primitive:uchar", 1),
            (16308, 4, 1125, "primitive:long", 0),
            (16312, 4, 1144, "primitive:long", 2),
            (16316, 4, 1163, "primitive:long", 0),
            (16320, 4, 1182, "primitive:long", 0),
            (16324, 4, 1201, "primitive:long", 0),
            (16328, 4, 1223, "primitive:long", 3),
            (16332, 4, 1245, "primitive:long", 10),
            (16336, 4, 1267, "primitive:long", 0),
            (
                16340,
                8,
                1292,
                "primitive:double",
                float.fromhex("0x1.0c6f7a0b5ed8dp-20"),
            ),
            (
                16348,
                8,
                1308,
                "primitive:double",
                float.fromhex("0x1.0c6f7a0b5ed8dp-20"),
            ),
            (16356, 1, 1321, "primitive:uchar", 1),
            (16357, 1, 1344, "primitive:uchar", 1),
            (16358, 1, 1367, "primitive:uchar", 0),
            (16359, 1, 1390, "primitive:uchar", 1),
            (16360, 1, 1413, "primitive:uchar", 1),
            (16361, 1, 1436, "primitive:uchar", 1),
            (16362, 1, 1459, "primitive:uchar", 1),
            (16363, 1, 1482, "primitive:uchar", 1),
            (16364, 1, 1505, "primitive:uchar", 1),
            (16365, 1, 1528, "primitive:uchar", 0),
            (16366, 1, 1551, "primitive:uchar", 0),
            (16367, 1, 1574, "primitive:uchar", 1),
            (16456, 4, 1636, "primitive:int", 0),
            (16460, 4, 1668, "primitive:int", 0),
            (16464, 8, 1720, "primitive:uint64", 0),
            (16472, 1, 2043, "primitive:uchar", 0),
            (16473, 1, 2066, "primitive:uchar", 0),
            (16474, 1, 2089, "primitive:uchar", 0),
            (16614, 1, 2208, "primitive:uchar", 0),
            (16615, 1, 2278, "primitive:uchar", 0),
            (16616, 4, 2344, "primitive:long", 0),
            (16620, 8, 2408, "primitive:double", float.fromhex("0x1.4cec41dd1a21fp-7")),
            (16628, 4, 2498, "primitive:int", 0),
            (16632, 4, 2514, "primitive:int", 1),
            (16642, 4, 2638, "primitive:int", 1),
            (16646, 4, 2654, "primitive:int", 1),
            (16650, 4, 2670, "primitive:int", 0),
            (16654, 4, 2686, "primitive:int", 0),
            (16658, 8, 2741, "primitive:double", float.fromhex("0x0.0p+0")),
            (
                16666,
                8,
                2814,
                "primitive:double",
                float.fromhex("0x1.0624dd2f1a9fcp-10"),
            ),
            (16674, 4, 2827, "primitive:int", 1),
            (16678, 1, 2887, "primitive:uchar", 0),
            (16679, 1, 2957, "primitive:uchar", 0),
        ),
    },
)
