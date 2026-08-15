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
            (767, 4, 19, "primitive:ulong", 1785762561),
            (886, 4, 19, "primitive:ulong", 1785762563),
            (5762, 4, 19, "primitive:ulong", 1763334902),
            (7962, 4, 19, "primitive:ulong", 1763334902),
            (8544, 4, 19, "primitive:ulong", 1785762560),
            (8562, 4, 19, "primitive:ulong", 0),
            (8604, 4, 19, "primitive:ulong", 0),
            (8616, 4, 19, "primitive:ulong", 1785762563),
            (8667, 4, 19, "primitive:ulong", 1785762563),
            (8687, 4, 19, "primitive:ulong", 1785762563),
            (8707, 4, 19, "primitive:ulong", 1785762563),
            (8727, 4, 19, "primitive:ulong", 1785762563),
            (8809, 4, 19, "primitive:ulong", 1785762563),
            (8833, 4, 19, "primitive:ulong", 1785762563),
            (8853, 4, 19, "primitive:ulong", 1785762563),
            (8873, 4, 19, "primitive:ulong", 1785762563),
            (8893, 4, 19, "primitive:ulong", 1785762563),
        ),
    },
)
