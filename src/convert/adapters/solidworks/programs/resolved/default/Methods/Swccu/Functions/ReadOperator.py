# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Swccu.Functions.ReadOperator import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (767, 4, 19, "primitive:ulong", 1785762595),
            (886, 4, 19, "primitive:ulong", 1785762596),
            (5762, 4, 19, "primitive:ulong", 1763334902),
            (7962, 4, 19, "primitive:ulong", 1763334902),
            (8472, 4, 19, "primitive:ulong", 1785762594),
            (8490, 4, 19, "primitive:ulong", 0),
            (8532, 4, 19, "primitive:ulong", 0),
            (8544, 4, 19, "primitive:ulong", 1785762596),
            (8595, 4, 19, "primitive:ulong", 1785762596),
            (8615, 4, 19, "primitive:ulong", 1785762596),
            (8635, 4, 19, "primitive:ulong", 1785762596),
            (8655, 4, 19, "primitive:ulong", 1785762596),
            (8737, 4, 19, "primitive:ulong", 1785762596),
            (8761, 4, 19, "primitive:ulong", 1785762596),
            (8781, 4, 19, "primitive:ulong", 1785762596),
            (8801, 4, 19, "primitive:ulong", 1785762596),
            (8821, 4, 19, "primitive:ulong", 1785762596),
        ),
    },
)
