# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Sldarchiveu.MoSharedFileDefC.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "Contents/CMgr": (
            (1608, 2, 1006, "primitive:ushort", 3),
            (1610, 1, 1028, "primitive:uchar", 0),
            (1627, 1, 1519, "primitive:uchar", 0),
            (1774, 2, 1006, "primitive:ushort", 3),
            (1776, 1, 1028, "primitive:uchar", 0),
            (1793, 1, 1519, "primitive:uchar", 0),
            (2069, 2, 1006, "primitive:ushort", 3),
            (2071, 1, 1028, "primitive:uchar", 0),
            (2088, 1, 1519, "primitive:uchar", 0),
            (2198, 2, 1006, "primitive:ushort", 3),
            (2200, 1, 1028, "primitive:uchar", 0),
            (2217, 1, 1519, "primitive:uchar", 0),
            (2493, 2, 1006, "primitive:ushort", 3),
            (2495, 1, 1028, "primitive:uchar", 0),
            (2512, 1, 1519, "primitive:uchar", 0),
            (2622, 2, 1006, "primitive:ushort", 3),
            (2624, 1, 1028, "primitive:uchar", 0),
            (2641, 1, 1519, "primitive:uchar", 0),
        ),
        "Contents/Config-0": (
            (721, 2, 1006, "primitive:ushort", 3),
            (723, 1, 1028, "primitive:uchar", 0),
            (740, 1, 1519, "primitive:uchar", 0),
            (1315, 2, 1006, "primitive:ushort", 3),
            (1317, 1, 1028, "primitive:uchar", 0),
            (1334, 1, 1519, "primitive:uchar", 0),
            (1909, 2, 1006, "primitive:ushort", 3),
            (1911, 1, 1028, "primitive:uchar", 0),
            (1928, 1, 1519, "primitive:uchar", 0),
        ),
        "Contents/Config-0-ModelHeader": (
            (2303, 2, 1006, "primitive:ushort", 2),
            (2305, 1, 1028, "primitive:uchar", 0),
            (2322, 1, 1519, "primitive:uchar", 0),
            (2518, 2, 1006, "primitive:ushort", 3),
            (2520, 1, 1028, "primitive:uchar", 0),
            (2537, 1, 1519, "primitive:uchar", 0),
        ),
    },
)
