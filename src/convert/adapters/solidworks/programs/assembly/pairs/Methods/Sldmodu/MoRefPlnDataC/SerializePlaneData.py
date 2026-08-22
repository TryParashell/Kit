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
            (3106, 8, 533, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (3148, 8, 812, "primitive:double", float.fromhex("0x1.95810624dd2f2p-5")),
            (3156, 8, 812, "primitive:double", float.fromhex("-0x1.95810624dd2f2p-5")),
            (3164, 8, 812, "primitive:double", float.fromhex("0x1.6872b020c49bap-7")),
            (3172, 8, 812, "primitive:double", float.fromhex("-0x1.6872b020c49bap-7")),
            (3182, 4, 1016, "primitive:long", 0),
            (3186, 4, 1089, "primitive:long", -4),
            (3190, 4, 1110, "primitive:long", -4),
            (3194, 1, 1317, "primitive:uchar", 0),
            (3219, 4, 1575, "primitive:long", 1),
            (3223, 4, 1646, "primitive:long", 0),
            (3227, 2, 1711, "primitive:ushort", 0),
            (3600, 8, 533, "primitive:double", float.fromhex("0x0.0p+0")),
            (3714, 8, 812, "primitive:double", float.fromhex("0x1.95810624dd2f2p-5")),
            (3722, 8, 812, "primitive:double", float.fromhex("-0x1.95810624dd2f2p-5")),
            (3730, 8, 812, "primitive:double", float.fromhex("0x1.6872b020c49bap-8")),
            (3738, 8, 812, "primitive:double", float.fromhex("-0x1.6872b020c49bap-8")),
            (3748, 4, 1016, "primitive:long", 0),
            (3752, 4, 1089, "primitive:long", -4),
            (3756, 4, 1110, "primitive:long", -4),
            (3760, 1, 1317, "primitive:uchar", 0),
            (3785, 4, 1575, "primitive:long", 1),
            (3789, 4, 1646, "primitive:long", 0),
            (3793, 2, 1711, "primitive:ushort", 0),
            (4170, 8, 533, "primitive:double", float.fromhex("0x0.0p+0")),
            (4284, 8, 812, "primitive:double", float.fromhex("0x1.6872b020c49bap-8")),
            (4292, 8, 812, "primitive:double", float.fromhex("-0x1.6872b020c49bap-8")),
            (4300, 8, 812, "primitive:double", float.fromhex("0x1.6872b020c49bap-7")),
            (4308, 8, 812, "primitive:double", float.fromhex("-0x1.6872b020c49bap-7")),
            (4318, 4, 1016, "primitive:long", 0),
            (4322, 4, 1089, "primitive:long", -4),
            (4326, 4, 1110, "primitive:long", -4),
            (4330, 1, 1317, "primitive:uchar", 0),
            (4355, 4, 1575, "primitive:long", 1),
            (4359, 4, 1646, "primitive:long", 0),
            (4363, 2, 1711, "primitive:ushort", 0),
        ),
    },
)
