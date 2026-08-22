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
        "ResolvedFeatures": (
            (3876, 8, 533, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (3918, 8, 812, "primitive:double", float.fromhex("0x1.6872b020c49bcp-6")),
            (3926, 8, 812, "primitive:double", float.fromhex("-0x1.6872b020c49bcp-6")),
            (3934, 8, 812, "primitive:double", float.fromhex("0x1.6872b020c49bap-7")),
            (3942, 8, 812, "primitive:double", float.fromhex("-0x1.6872b020c49bap-7")),
            (3952, 4, 1016, "primitive:long", 0),
            (3956, 4, 1089, "primitive:long", -4),
            (3960, 4, 1110, "primitive:long", -4),
            (3964, 1, 1317, "primitive:uchar", 0),
            (3989, 4, 1575, "primitive:long", 1),
            (3993, 4, 1646, "primitive:long", 0),
            (3997, 2, 1711, "primitive:ushort", 0),
            (4370, 8, 533, "primitive:double", float.fromhex("0x0.0p+0")),
            (4484, 8, 812, "primitive:double", float.fromhex("0x1.6872b020c49bcp-6")),
            (4492, 8, 812, "primitive:double", float.fromhex("-0x1.6872b020c49bcp-6")),
            (4500, 8, 812, "primitive:double", float.fromhex("0x1.6872b020c49bap-8")),
            (4508, 8, 812, "primitive:double", float.fromhex("-0x1.6872b020c49bap-8")),
            (4518, 4, 1016, "primitive:long", 0),
            (4522, 4, 1089, "primitive:long", -4),
            (4526, 4, 1110, "primitive:long", -4),
            (4530, 1, 1317, "primitive:uchar", 0),
            (4555, 4, 1575, "primitive:long", 1),
            (4559, 4, 1646, "primitive:long", 0),
            (4563, 2, 1711, "primitive:ushort", 0),
            (4940, 8, 533, "primitive:double", float.fromhex("0x0.0p+0")),
            (5054, 8, 812, "primitive:double", float.fromhex("0x1.6872b020c49bap-8")),
            (5062, 8, 812, "primitive:double", float.fromhex("-0x1.6872b020c49bap-8")),
            (5070, 8, 812, "primitive:double", float.fromhex("0x1.6872b020c49bap-7")),
            (5078, 8, 812, "primitive:double", float.fromhex("-0x1.6872b020c49bap-7")),
            (5088, 4, 1016, "primitive:long", 0),
            (5092, 4, 1089, "primitive:long", -4),
            (5096, 4, 1110, "primitive:long", -4),
            (5100, 1, 1317, "primitive:uchar", 0),
            (5125, 4, 1575, "primitive:long", 1),
            (5129, 4, 1646, "primitive:long", 0),
            (5133, 2, 1711, "primitive:ushort", 0),
        ),
    },
)
