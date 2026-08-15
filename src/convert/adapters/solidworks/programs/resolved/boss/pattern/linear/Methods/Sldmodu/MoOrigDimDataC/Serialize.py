# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoOrigDimDataC.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (12018, 1, 764, "primitive:uchar", 1),
            (12021, 1, 861, "primitive:uchar", 0),
            (12022, 1, 893, "primitive:uchar", 0),
            (12023, 8, 913, "primitive:double", float.fromhex("0x0.0p+0")),
            (12031, 1, 937, "primitive:uchar", 0),
            (12032, 8, 963, "primitive:double", float.fromhex("0x0.0p+0")),
            (12040, 8, 979, "primitive:double", float.fromhex("0x0.0p+0")),
            (12048, 4, 1044, "primitive:long", 0),
            (12052, 4, 1102, "primitive:long", -1),
            (12056, 4, 1118, "primitive:long", -1),
            (12060, 4, 1134, "primitive:long", 0),
            (12064, 4, 1150, "primitive:long", 0),
            (12068, 4, 1163, "primitive:long", 0),
            (12072, 4, 1185, "primitive:long", 0),
            (12076, 4, 1207, "primitive:long", 0),
            (12080, 4, 1232, "primitive:long", -1),
            (12084, 1, 1245, "primitive:uchar", 0),
            (12085, 4, 1321, "primitive:long", 0),
            (12089, 4, 1406, "primitive:long", 0),
            (12095, 4, 1480, "primitive:long", 0),
            (12099, 1, 764, "primitive:uchar", 1),
            (12102, 1, 861, "primitive:uchar", 0),
            (12103, 1, 893, "primitive:uchar", 0),
            (12104, 8, 913, "primitive:double", float.fromhex("0x0.0p+0")),
            (12112, 1, 937, "primitive:uchar", 0),
            (12113, 8, 963, "primitive:double", float.fromhex("0x0.0p+0")),
            (12121, 8, 979, "primitive:double", float.fromhex("0x0.0p+0")),
            (12129, 4, 1044, "primitive:long", 0),
            (12133, 4, 1102, "primitive:long", -1),
            (12137, 4, 1118, "primitive:long", -1),
            (12141, 4, 1134, "primitive:long", 0),
            (12145, 4, 1150, "primitive:long", 0),
            (12149, 4, 1163, "primitive:long", 0),
            (12153, 4, 1185, "primitive:long", 0),
            (12157, 4, 1207, "primitive:long", 0),
            (12161, 4, 1232, "primitive:long", -1),
            (12165, 1, 1245, "primitive:uchar", 0),
            (12166, 4, 1321, "primitive:long", 0),
            (12170, 4, 1406, "primitive:long", 0),
            (12176, 4, 1480, "primitive:long", 0),
        ),
    },
)
