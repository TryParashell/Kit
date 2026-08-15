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
            (4764, 4, 4641, "primitive:long", 0),
            (4768, 4, 4702, "primitive:long", 1),
            (4789, 4, 6502, "primitive:long", 1),
            (4793, 2, 6535, "primitive:ushort", 0),
            (4795, 2, 6558, "primitive:ushort", 4),
            (4797, 2, 6578, "primitive:ushort", 2),
            (4799, 2, 6598, "primitive:ushort", 1),
            (4809, 2, 6792, "primitive:ushort", 4),
            (4811, 2, 6946, "primitive:ushort", 0),
            (4813, 4, 6996, "primitive:long", 0),
            (4819, 1, 7338, "primitive:uchar", 0),
            (4820, 8, 7492, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (4828, 4, 7550, "primitive:ulong", 0),
            (4832, 4, 7605, "primitive:ulong", 0),
            (5072, 4, 16922, "primitive:long", 2),
            (5076, 4, 16935, "primitive:long", 1),
            (5080, 4, 16948, "primitive:long", 1),
            (5084, 4, 16961, "primitive:long", 1),
            (5088, 4, 17017, "primitive:long", 1),
            (5092, 4, 17030, "primitive:long", 1),
            (5096, 4, 17094, "primitive:long", 1),
            (5100, 4, 17158, "primitive:long", 1),
            (5104, 4, 17222, "primitive:long", 1),
            (5108, 4, 17286, "primitive:long", 1),
            (5112, 4, 17350, "primitive:long", 1),
            (5116, 4, 17414, "primitive:long", 1),
            (5120, 4, 17478, "primitive:long", 1),
            (5124, 4, 17538, "primitive:long", 0),
            (5128, 4, 17594, "primitive:long", 1),
        ),
    },
)
