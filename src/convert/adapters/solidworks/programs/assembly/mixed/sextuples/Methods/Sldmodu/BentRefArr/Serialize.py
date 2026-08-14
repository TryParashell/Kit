# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Owners.Sldmodu.BentRefArr.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram = (
    KOwnerSites,
    {
        "Contents/Config-0-ResolvedFeatures": (
            (4820, 4, 4641, "primitive:long", 0),
            (4824, 4, 4702, "primitive:long", 1),
            (4845, 4, 6502, "primitive:long", 1),
            (4849, 2, 6535, "primitive:ushort", 0),
            (4851, 2, 6558, "primitive:ushort", 4),
            (4853, 2, 6578, "primitive:ushort", 2),
            (4855, 2, 6598, "primitive:ushort", 1),
            (4865, 2, 6792, "primitive:ushort", 4),
            (4867, 2, 6946, "primitive:ushort", 0),
            (4869, 4, 6996, "primitive:long", 0),
            (4875, 1, 7338, "primitive:uchar", 0),
            (4876, 8, 7492, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (4884, 4, 7550, "primitive:ulong", 0),
            (4888, 4, 7605, "primitive:ulong", 0),
            (5128, 4, 16922, "primitive:long", 2),
            (5132, 4, 16935, "primitive:long", 1),
            (5136, 4, 16948, "primitive:long", 1),
            (5140, 4, 16961, "primitive:long", 1),
            (5144, 4, 17017, "primitive:long", 1),
            (5148, 4, 17030, "primitive:long", 1),
            (5152, 4, 17094, "primitive:long", 1),
            (5156, 4, 17158, "primitive:long", 1),
            (5160, 4, 17222, "primitive:long", 1),
            (5164, 4, 17286, "primitive:long", 1),
            (5168, 4, 17350, "primitive:long", 1),
            (5172, 4, 17414, "primitive:long", 1),
            (5176, 4, 17478, "primitive:long", 1),
            (5180, 4, 17538, "primitive:long", 0),
            (5184, 4, 17594, "primitive:long", 1),
        ),
    },
)
