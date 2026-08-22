# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoRefPlnDataC.SerializePlaneData import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "Contents/Config-0-ResolvedFeatures": (
            (3330, 8, 533, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (3372, 8, 812, "primitive:double", float.fromhex("0x1.6c80c73abc947p-4")),
            (3380, 8, 812, "primitive:double", float.fromhex("-0x1.6c80c73abc947p-4")),
            (3388, 8, 812, "primitive:double", float.fromhex("0x1.c28f5c28f5c2ap-5")),
            (3396, 8, 812, "primitive:double", float.fromhex("-0x1.c28f5c28f5c2ap-5")),
            (3406, 4, 1016, "primitive:long", 0),
            (3410, 4, 1089, "primitive:long", -4),
            (3414, 4, 1110, "primitive:long", -4),
            (3418, 1, 1317, "primitive:uchar", 0),
            (3443, 4, 1575, "primitive:long", 1),
            (3447, 4, 1646, "primitive:long", 0),
            (3451, 2, 1711, "primitive:ushort", 0),
            (3824, 8, 533, "primitive:double", float.fromhex("0x0.0p+0")),
            (3938, 8, 812, "primitive:double", float.fromhex("0x1.6c80c73abc947p-4")),
            (3946, 8, 812, "primitive:double", float.fromhex("-0x1.6c80c73abc947p-4")),
            (3954, 8, 812, "primitive:double", float.fromhex("0x1.c28f5c28f5c2ap-5")),
            (3962, 8, 812, "primitive:double", float.fromhex("-0x1.c28f5c28f5c2ap-5")),
            (3972, 4, 1016, "primitive:long", 0),
            (3976, 4, 1089, "primitive:long", -4),
            (3980, 4, 1110, "primitive:long", -4),
            (3984, 1, 1317, "primitive:uchar", 0),
            (4009, 4, 1575, "primitive:long", 1),
            (4013, 4, 1646, "primitive:long", 0),
            (4017, 2, 1711, "primitive:ushort", 0),
            (4394, 8, 533, "primitive:double", float.fromhex("0x0.0p+0")),
            (4508, 8, 812, "primitive:double", float.fromhex("0x1.6c80c73abc947p-4")),
            (4516, 8, 812, "primitive:double", float.fromhex("-0x1.6c80c73abc947p-4")),
            (4524, 8, 812, "primitive:double", float.fromhex("0x1.c28f5c28f5c2ap-5")),
            (4532, 8, 812, "primitive:double", float.fromhex("-0x1.c28f5c28f5c2ap-5")),
            (4542, 4, 1016, "primitive:long", 0),
            (4546, 4, 1089, "primitive:long", -4),
            (4550, 4, 1110, "primitive:long", -4),
            (4554, 1, 1317, "primitive:uchar", 0),
            (4579, 4, 1575, "primitive:long", 1),
            (4583, 4, 1646, "primitive:long", 0),
            (4587, 2, 1711, "primitive:ushort", 0),
        ),
    },
)
