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
            (4652, 4, 4641, "primitive:long", 0),
            (4656, 4, 4702, "primitive:long", 1),
            (4677, 4, 6502, "primitive:long", 1),
            (4681, 2, 6535, "primitive:ushort", 0),
            (4683, 2, 6558, "primitive:ushort", 4),
            (4685, 2, 6578, "primitive:ushort", 2),
            (4687, 2, 6598, "primitive:ushort", 1),
            (4697, 2, 6792, "primitive:ushort", 4),
            (4699, 2, 6946, "primitive:ushort", 0),
            (4701, 4, 6996, "primitive:long", 0),
            (4707, 1, 7338, "primitive:uchar", 0),
            (4708, 8, 7492, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (4716, 4, 7550, "primitive:ulong", 0),
            (4720, 4, 7605, "primitive:ulong", 0),
            (4960, 4, 16922, "primitive:long", 2),
            (4964, 4, 16935, "primitive:long", 1),
            (4968, 4, 16948, "primitive:long", 1),
            (4972, 4, 16961, "primitive:long", 1),
            (4976, 4, 17017, "primitive:long", 1),
            (4980, 4, 17030, "primitive:long", 1),
            (4984, 4, 17094, "primitive:long", 1),
            (4988, 4, 17158, "primitive:long", 1),
            (4992, 4, 17222, "primitive:long", 1),
            (4996, 4, 17286, "primitive:long", 1),
            (5000, 4, 17350, "primitive:long", 1),
            (5004, 4, 17414, "primitive:long", 1),
            (5008, 4, 17478, "primitive:long", 1),
            (5012, 4, 17538, "primitive:long", 0),
            (5016, 4, 17594, "primitive:long", 1),
        ),
    },
)
