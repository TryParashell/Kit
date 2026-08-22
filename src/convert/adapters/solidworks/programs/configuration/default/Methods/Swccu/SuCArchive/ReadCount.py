# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Swccu.SuCArchive.ReadCount import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "Configuration": (
            (751, 2, 19, "primitive:ushort", 16),
            (2502, 2, 19, "primitive:ushort", 0),
            (2532, 2, 19, "primitive:ushort", 0),
            (2846, 2, 19, "primitive:ushort", 0),
            (2902, 2, 19, "primitive:ushort", 0),
            (2988, 2, 19, "primitive:ushort", 0),
            (2990, 2, 19, "primitive:ushort", 0),
            (3012, 2, 19, "primitive:ushort", 0),
            (3022, 2, 19, "primitive:ushort", 0),
            (20470, 2, 19, "primitive:ushort", 0),
            (20559, 2, 19, "primitive:ushort", 4),
            (20629, 2, 19, "primitive:ushort", 0),
            (20932, 2, 19, "primitive:ushort", 0),
            (21253, 2, 19, "primitive:ushort", 0),
            (21574, 2, 19, "primitive:ushort", 0),
            (21976, 2, 19, "primitive:ushort", 0),
            (24091, 2, 19, "primitive:ushort", 0),
            (24240, 2, 19, "primitive:ushort", 1),
            (24546, 2, 19, "primitive:ushort", 0),
            (24548, 2, 19, "primitive:ushort", 0),
            (24550, 2, 19, "primitive:ushort", 0),
            (24552, 2, 19, "primitive:ushort", 0),
            (24554, 2, 19, "primitive:ushort", 0),
            (24556, 2, 19, "primitive:ushort", 0),
            (24558, 2, 19, "primitive:ushort", 0),
            (24560, 2, 19, "primitive:ushort", 0),
            (24564, 2, 19, "primitive:ushort", 0),
            (24637, 2, 19, "primitive:ushort", 0),
            (25039, 2, 19, "primitive:ushort", 0),
            (25176, 2, 19, "primitive:ushort", 0),
        ),
    },
)
