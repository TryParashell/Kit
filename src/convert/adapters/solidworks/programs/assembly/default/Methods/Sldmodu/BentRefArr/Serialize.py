# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Sldmodu.BentRefArr.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "Contents/Config-0-ResolvedFeatures": (
            (4540, 4, 4641, "primitive:long", 0),
            (4544, 4, 4702, "primitive:long", 1),
            (4565, 4, 6502, "primitive:long", 1),
            (4569, 2, 6535, "primitive:ushort", 0),
            (4571, 2, 6558, "primitive:ushort", 4),
            (4573, 2, 6578, "primitive:ushort", 2),
            (4575, 2, 6598, "primitive:ushort", 1),
            (4585, 2, 6792, "primitive:ushort", 4),
            (4587, 2, 6946, "primitive:ushort", 0),
            (4589, 4, 6996, "primitive:long", 0),
            (4595, 1, 7338, "primitive:uchar", 0),
            (4596, 8, 7492, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (4604, 4, 7550, "primitive:ulong", 0),
            (4608, 4, 7605, "primitive:ulong", 0),
            (4848, 4, 16922, "primitive:long", 2),
            (4852, 4, 16935, "primitive:long", 1),
            (4856, 4, 16948, "primitive:long", 1),
            (4860, 4, 16961, "primitive:long", 1),
            (4864, 4, 17017, "primitive:long", 1),
            (4868, 4, 17030, "primitive:long", 1),
            (4872, 4, 17094, "primitive:long", 1),
            (4876, 4, 17158, "primitive:long", 1),
            (4880, 4, 17222, "primitive:long", 1),
            (4884, 4, 17286, "primitive:long", 1),
            (4888, 4, 17350, "primitive:long", 1),
            (4892, 4, 17414, "primitive:long", 1),
            (4896, 4, 17478, "primitive:long", 1),
            (4900, 4, 17538, "primitive:long", 0),
            (4904, 4, 17594, "primitive:long", 1),
        ),
    },
)
