# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoAtomC.GetRuntimeClass import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "Configuration": (
            (2850, 4, 328, "primitive:long", 101),
            (2854, 4, 341, "primitive:long", 1),
            (2906, 4, 1764, "primitive:long", 101),
            (2910, 4, 1777, "primitive:long", 0),
            (2914, 4, 1899, "primitive:long", 31),
            (2918, 4, 1915, "primitive:long", 31),
            (2922, 4, 1931, "primitive:ulong", 0),
            (2926, 4, 1954, "primitive:long", 0),
            (2930, 4, 2420, "primitive:long", 0),
            (2934, 4, 2458, "primitive:long", 1),
            (2938, 4, 2487, "primitive:long", -1),
            (2942, 4, 2311, "primitive:long", 1393),
            (2946, 4, 2338, "primitive:long", 1),
            (2950, 4, 2354, "primitive:long", 1393),
            (2954, 4, 2379, "primitive:long", 6),
            (2958, 4, 688, "primitive:ulong", 18000),
        ),
    },
)
