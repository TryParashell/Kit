# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoVisPropC.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "Contents/CMgr": (
            (107, 4, 77, "primitive:ulong", 4294967295),
            (111, 2, 90, "primitive:ushort", 65535),
            (303, 4, 77, "primitive:ulong", 4294967295),
            (307, 2, 90, "primitive:ushort", 65535),
        ),
        "Contents/Config-0": (
            (216, 4, 77, "primitive:ulong", 4294967295),
            (220, 2, 90, "primitive:ushort", 65535),
            (777, 4, 77, "primitive:ulong", 4294967295),
            (781, 2, 90, "primitive:ushort", 65535),
            (1279, 4, 77, "primitive:ulong", 4294967295),
            (1283, 2, 90, "primitive:ushort", 65535),
            (1781, 4, 77, "primitive:ulong", 4294967295),
            (1785, 2, 90, "primitive:ushort", 65535),
            (2283, 4, 77, "primitive:ulong", 4294967295),
            (2287, 2, 90, "primitive:ushort", 65535),
            (22496, 4, 77, "primitive:ulong", 4294967295),
            (22500, 2, 90, "primitive:ushort", 65535),
            (22799, 4, 77, "primitive:ulong", 4294967295),
            (22803, 2, 90, "primitive:ushort", 65535),
            (23120, 4, 77, "primitive:ulong", 4294967295),
            (23124, 2, 90, "primitive:ushort", 65535),
            (23441, 4, 77, "primitive:ulong", 4294967295),
            (23445, 2, 90, "primitive:ushort", 65535),
            (23702, 4, 77, "primitive:ulong", 4294967295),
            (23706, 2, 90, "primitive:ushort", 65535),
            (25934, 4, 77, "primitive:ulong", 4294967295),
            (25938, 2, 90, "primitive:ushort", 65535),
            (26252, 4, 77, "primitive:ulong", 4294967295),
            (26256, 2, 90, "primitive:ushort", 65535),
        ),
        "Contents/Config-0-ResolvedFeatures": (
            (137, 4, 77, "primitive:ulong", 4294967295),
            (141, 2, 90, "primitive:ushort", 65535),
            (336, 4, 77, "primitive:ulong", 4294967295),
            (340, 2, 90, "primitive:ushort", 65535),
            (538, 4, 77, "primitive:ulong", 4294967295),
            (542, 2, 90, "primitive:ushort", 65535),
            (1126, 4, 77, "primitive:ulong", 4294967295),
            (1130, 2, 90, "primitive:ushort", 65535),
            (1325, 4, 77, "primitive:ulong", 4294967295),
            (1329, 2, 90, "primitive:ushort", 65535),
            (1547, 4, 77, "primitive:ulong", 4294967295),
            (1551, 2, 90, "primitive:ushort", 65535),
            (1754, 4, 77, "primitive:ulong", 4294967295),
            (1758, 2, 90, "primitive:ushort", 65535),
            (2028, 4, 77, "primitive:ulong", 4294967295),
            (2032, 2, 90, "primitive:ushort", 65535),
            (2223, 4, 77, "primitive:ulong", 4294967295),
            (2227, 2, 90, "primitive:ushort", 65535),
            (2382, 4, 77, "primitive:ulong", 4294967295),
            (2386, 2, 90, "primitive:ushort", 65535),
            (2604, 4, 77, "primitive:ulong", 4294967295),
            (2608, 2, 90, "primitive:ushort", 65535),
            (2798, 4, 77, "primitive:ulong", 4294967295),
            (2802, 2, 90, "primitive:ushort", 65535),
            (2995, 4, 77, "primitive:ulong", 4294967295),
            (2999, 2, 90, "primitive:ushort", 65535),
            (3514, 4, 77, "primitive:ulong", 4294967295),
            (3518, 2, 90, "primitive:ushort", 65535),
            (4084, 4, 77, "primitive:ulong", 4294967295),
            (4088, 2, 90, "primitive:ushort", 65535),
            (4672, 4, 77, "primitive:ulong", 4294967295),
            (4676, 2, 90, "primitive:ushort", 65535),
            (4777, 4, 77, "primitive:ulong", 4294967295),
            (4781, 2, 90, "primitive:ushort", 65535),
            (5592, 4, 77, "primitive:ulong", 4294967295),
            (5596, 2, 90, "primitive:ushort", 65535),
        ),
    },
)
