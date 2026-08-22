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
            (749, 2, 19, "primitive:ushort", 16),
            (2500, 2, 19, "primitive:ushort", 0),
            (2530, 2, 19, "primitive:ushort", 0),
            (2844, 2, 19, "primitive:ushort", 0),
            (2900, 2, 19, "primitive:ushort", 0),
            (3018, 2, 19, "primitive:ushort", 0),
            (3020, 2, 19, "primitive:ushort", 0),
            (3042, 2, 19, "primitive:ushort", 0),
            (3052, 2, 19, "primitive:ushort", 0),
            (20500, 2, 19, "primitive:ushort", 0),
            (20589, 2, 19, "primitive:ushort", 4),
            (20659, 2, 19, "primitive:ushort", 0),
            (20962, 2, 19, "primitive:ushort", 0),
            (21283, 2, 19, "primitive:ushort", 0),
            (21604, 2, 19, "primitive:ushort", 0),
            (22006, 2, 19, "primitive:ushort", 0),
            (24121, 2, 19, "primitive:ushort", 0),
            (24270, 2, 19, "primitive:ushort", 1),
            (24582, 2, 19, "primitive:ushort", 0),
            (24584, 2, 19, "primitive:ushort", 0),
            (24586, 2, 19, "primitive:ushort", 0),
            (24588, 2, 19, "primitive:ushort", 0),
            (24590, 2, 19, "primitive:ushort", 0),
            (24592, 2, 19, "primitive:ushort", 0),
            (24594, 2, 19, "primitive:ushort", 0),
            (24596, 2, 19, "primitive:ushort", 0),
            (24600, 2, 19, "primitive:ushort", 0),
            (24673, 2, 19, "primitive:ushort", 0),
            (24801, 2, 19, "primitive:ushort", 0),
            (24938, 2, 19, "primitive:ushort", 0),
        ),
    },
)
