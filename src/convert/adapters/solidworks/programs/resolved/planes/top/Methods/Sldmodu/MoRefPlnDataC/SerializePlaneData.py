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
            (3638, 8, 533, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (3680, 8, 812, "primitive:double", float.fromhex("0x1.6872b020c49bap-6")),
            (3688, 8, 812, "primitive:double", float.fromhex("-0x1.6872b020c49bap-6")),
            (3696, 8, 812, "primitive:double", float.fromhex("0x1.6872b020c49bap-8")),
            (3704, 8, 812, "primitive:double", float.fromhex("-0x1.6872b020c49bap-8")),
            (3714, 4, 1016, "primitive:long", 0),
            (3718, 4, 1089, "primitive:long", -4),
            (3722, 4, 1110, "primitive:long", -4),
            (3726, 1, 1317, "primitive:uchar", 0),
            (3751, 4, 1575, "primitive:long", 1),
            (3755, 4, 1646, "primitive:long", 0),
            (3759, 2, 1711, "primitive:ushort", 0),
            (4132, 8, 533, "primitive:double", float.fromhex("0x0.0p+0")),
            (4246, 8, 812, "primitive:double", float.fromhex("0x1.6872b020c49bap-6")),
            (4254, 8, 812, "primitive:double", float.fromhex("-0x1.6872b020c49bap-6")),
            (4262, 8, 812, "primitive:double", float.fromhex("0x1.6872b020c49bap-7")),
            (4270, 8, 812, "primitive:double", float.fromhex("-0x1.6872b020c49bap-7")),
            (4280, 4, 1016, "primitive:long", 0),
            (4284, 4, 1089, "primitive:long", -4),
            (4288, 4, 1110, "primitive:long", -4),
            (4292, 1, 1317, "primitive:uchar", 0),
            (4317, 4, 1575, "primitive:long", 1),
            (4321, 4, 1646, "primitive:long", 0),
            (4325, 2, 1711, "primitive:ushort", 0),
            (4702, 8, 533, "primitive:double", float.fromhex("0x0.0p+0")),
            (4816, 8, 812, "primitive:double", float.fromhex("0x1.6872b020c49bap-7")),
            (4824, 8, 812, "primitive:double", float.fromhex("-0x1.6872b020c49bap-7")),
            (4832, 8, 812, "primitive:double", float.fromhex("0x1.6872b020c49bap-8")),
            (4840, 8, 812, "primitive:double", float.fromhex("-0x1.6872b020c49bap-8")),
            (4850, 4, 1016, "primitive:long", 0),
            (4854, 4, 1089, "primitive:long", -4),
            (4858, 4, 1110, "primitive:long", -4),
            (4862, 1, 1317, "primitive:uchar", 0),
            (4887, 4, 1575, "primitive:long", 1),
            (4891, 4, 1646, "primitive:long", 0),
            (4895, 2, 1711, "primitive:ushort", 0),
        ),
    },
)
