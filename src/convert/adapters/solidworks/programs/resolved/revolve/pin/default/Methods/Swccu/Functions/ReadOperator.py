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
            (767, 4, 19, "primitive:ulong", 1785928014),
            (886, 4, 19, "primitive:ulong", 1785928014),
            (5762, 4, 19, "primitive:ulong", 1763334902),
            (6564, 4, 19, "primitive:ulong", 1763334902),
            (9125, 4, 19, "primitive:ulong", 1763334902),
            (9699, 4, 19, "primitive:ulong", 1785928009),
            (9717, 4, 19, "primitive:ulong", 0),
            (9759, 4, 19, "primitive:ulong", 0),
            (9771, 4, 19, "primitive:ulong", 1785928014),
            (9791, 4, 19, "primitive:ulong", 1785928014),
            (9813, 4, 19, "primitive:ulong", 1785928014),
            (9895, 4, 19, "primitive:ulong", 1785928014),
            (9915, 4, 19, "primitive:ulong", 1785928014),
            (9937, 4, 19, "primitive:ulong", 1785928014),
            (10272, 4, 19, "primitive:ulong", 1785928014),
        ),
    },
)
