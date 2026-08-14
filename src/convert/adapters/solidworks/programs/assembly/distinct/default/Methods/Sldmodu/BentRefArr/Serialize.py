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
            (4596, 4, 4641, "primitive:long", 0),
            (4600, 4, 4702, "primitive:long", 1),
            (4621, 4, 6502, "primitive:long", 1),
            (4625, 2, 6535, "primitive:ushort", 0),
            (4627, 2, 6558, "primitive:ushort", 4),
            (4629, 2, 6578, "primitive:ushort", 2),
            (4631, 2, 6598, "primitive:ushort", 1),
            (4641, 2, 6792, "primitive:ushort", 4),
            (4643, 2, 6946, "primitive:ushort", 0),
            (4645, 4, 6996, "primitive:long", 0),
            (4651, 1, 7338, "primitive:uchar", 0),
            (4652, 8, 7492, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (4660, 4, 7550, "primitive:ulong", 0),
            (4664, 4, 7605, "primitive:ulong", 0),
            (4904, 4, 16922, "primitive:long", 2),
            (4908, 4, 16935, "primitive:long", 1),
            (4912, 4, 16948, "primitive:long", 1),
            (4916, 4, 16961, "primitive:long", 1),
            (4920, 4, 17017, "primitive:long", 1),
            (4924, 4, 17030, "primitive:long", 1),
            (4928, 4, 17094, "primitive:long", 1),
            (4932, 4, 17158, "primitive:long", 1),
            (4936, 4, 17222, "primitive:long", 1),
            (4940, 4, 17286, "primitive:long", 1),
            (4944, 4, 17350, "primitive:long", 1),
            (4948, 4, 17414, "primitive:long", 1),
            (4952, 4, 17478, "primitive:long", 1),
            (4956, 4, 17538, "primitive:long", 0),
            (4960, 4, 17594, "primitive:long", 1),
        ),
    },
)
