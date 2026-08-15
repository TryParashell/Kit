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
            (12489, 1, 764, "primitive:uchar", 1),
            (12492, 1, 861, "primitive:uchar", 0),
            (12493, 1, 893, "primitive:uchar", 0),
            (12494, 8, 913, "primitive:double", float.fromhex("0x0.0p+0")),
            (12502, 1, 937, "primitive:uchar", 0),
            (12503, 8, 963, "primitive:double", float.fromhex("0x0.0p+0")),
            (12511, 8, 979, "primitive:double", float.fromhex("0x0.0p+0")),
            (12519, 4, 1044, "primitive:long", 0),
            (12523, 4, 1102, "primitive:long", -1),
            (12527, 4, 1118, "primitive:long", -1),
            (12531, 4, 1134, "primitive:long", 0),
            (12535, 4, 1150, "primitive:long", 0),
            (12539, 4, 1163, "primitive:long", 0),
            (12543, 4, 1185, "primitive:long", 0),
            (12547, 4, 1207, "primitive:long", 0),
            (12551, 4, 1232, "primitive:long", -1),
            (12555, 1, 1245, "primitive:uchar", 0),
            (12556, 4, 1321, "primitive:long", 0),
            (12560, 4, 1406, "primitive:long", 0),
            (12566, 4, 1480, "primitive:long", 0),
            (12570, 1, 764, "primitive:uchar", 1),
            (12573, 1, 861, "primitive:uchar", 0),
            (12574, 1, 893, "primitive:uchar", 0),
            (12575, 8, 913, "primitive:double", float.fromhex("0x0.0p+0")),
            (12583, 1, 937, "primitive:uchar", 0),
            (12584, 8, 963, "primitive:double", float.fromhex("0x0.0p+0")),
            (12592, 8, 979, "primitive:double", float.fromhex("0x0.0p+0")),
            (12600, 4, 1044, "primitive:long", 0),
            (12604, 4, 1102, "primitive:long", -1),
            (12608, 4, 1118, "primitive:long", -1),
            (12612, 4, 1134, "primitive:long", 0),
            (12616, 4, 1150, "primitive:long", 0),
            (12620, 4, 1163, "primitive:long", 0),
            (12624, 4, 1185, "primitive:long", 0),
            (12628, 4, 1207, "primitive:long", 0),
            (12632, 4, 1232, "primitive:long", -1),
            (12636, 1, 1245, "primitive:uchar", 0),
            (12637, 4, 1321, "primitive:long", 0),
            (12641, 4, 1406, "primitive:long", 0),
            (12647, 4, 1480, "primitive:long", 0),
        ),
    },
)
