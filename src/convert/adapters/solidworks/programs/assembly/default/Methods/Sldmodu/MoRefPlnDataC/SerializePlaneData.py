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
            (3050, 8, 533, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (3092, 8, 812, "primitive:double", float.fromhex("0x1.6872b020c49bap-6")),
            (3100, 8, 812, "primitive:double", float.fromhex("-0x1.6872b020c49bap-6")),
            (3108, 8, 812, "primitive:double", float.fromhex("0x1.6872b020c49bap-7")),
            (3116, 8, 812, "primitive:double", float.fromhex("-0x1.6872b020c49bap-7")),
            (3126, 4, 1016, "primitive:long", 0),
            (3130, 4, 1089, "primitive:long", -4),
            (3134, 4, 1110, "primitive:long", -4),
            (3138, 1, 1317, "primitive:uchar", 0),
            (3163, 4, 1575, "primitive:long", 1),
            (3167, 4, 1646, "primitive:long", 0),
            (3171, 2, 1711, "primitive:ushort", 0),
            (3544, 8, 533, "primitive:double", float.fromhex("0x0.0p+0")),
            (3658, 8, 812, "primitive:double", float.fromhex("0x1.6872b020c49bap-6")),
            (3666, 8, 812, "primitive:double", float.fromhex("-0x1.6872b020c49bap-6")),
            (3674, 8, 812, "primitive:double", float.fromhex("0x1.6872b020c49bap-8")),
            (3682, 8, 812, "primitive:double", float.fromhex("-0x1.6872b020c49bap-8")),
            (3692, 4, 1016, "primitive:long", 0),
            (3696, 4, 1089, "primitive:long", -4),
            (3700, 4, 1110, "primitive:long", -4),
            (3704, 1, 1317, "primitive:uchar", 0),
            (3729, 4, 1575, "primitive:long", 1),
            (3733, 4, 1646, "primitive:long", 0),
            (3737, 2, 1711, "primitive:ushort", 0),
            (4114, 8, 533, "primitive:double", float.fromhex("0x0.0p+0")),
            (4228, 8, 812, "primitive:double", float.fromhex("0x1.6872b020c49bap-8")),
            (4236, 8, 812, "primitive:double", float.fromhex("-0x1.6872b020c49bap-8")),
            (4244, 8, 812, "primitive:double", float.fromhex("0x1.6872b020c49bap-7")),
            (4252, 8, 812, "primitive:double", float.fromhex("-0x1.6872b020c49bap-7")),
            (4262, 4, 1016, "primitive:long", 0),
            (4266, 4, 1089, "primitive:long", -4),
            (4270, 4, 1110, "primitive:long", -4),
            (4274, 1, 1317, "primitive:uchar", 0),
            (4299, 4, 1575, "primitive:long", 1),
            (4303, 4, 1646, "primitive:long", 0),
            (4307, 2, 1711, "primitive:ushort", 0),
        ),
    },
)
