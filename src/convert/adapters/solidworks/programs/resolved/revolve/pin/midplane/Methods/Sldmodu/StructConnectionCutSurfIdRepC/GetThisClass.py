# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Sldmodu.StructConnectionCutSurfIdRepC.GetThisClass import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (9553, 4, 299, "primitive:ulong", 1),
            (9557, 4, 318, "primitive:ulong", 0),
            (9561, 4, 458, "primitive:ulong", 5),
            (9565, 4, 672, "primitive:long", 768),
            (9569, 4, 749, "primitive:ulong", 794),
            (
                9573,
                8,
                1121,
                "primitive:double",
                float.fromhex("0x1.249ad2594c37dp+332"),
            ),
            (
                9581,
                8,
                1134,
                "primitive:double",
                float.fromhex("0x1.249ad2594c37dp+332"),
            ),
            (9823, 4, 1685, "primitive:ulong", 0),
            (9827, 4, 2284, "primitive:long", 0),
            (9831, 4, 2561, "primitive:long", 18000),
            (9835, 4, 2578, "primitive:long", 0),
            (9845, 4, 299, "primitive:ulong", 1),
            (9849, 4, 318, "primitive:ulong", 0),
            (9853, 4, 458, "primitive:ulong", 5),
            (9857, 4, 672, "primitive:long", 768),
            (9861, 4, 749, "primitive:ulong", 803),
            (
                9865,
                8,
                1121,
                "primitive:double",
                float.fromhex("0x1.249ad2594c37dp+332"),
            ),
            (
                9873,
                8,
                1134,
                "primitive:double",
                float.fromhex("0x1.249ad2594c37dp+332"),
            ),
            (9947, 4, 1685, "primitive:ulong", 0),
            (9951, 4, 2284, "primitive:long", 0),
            (9955, 4, 2561, "primitive:long", 18000),
            (9959, 4, 2578, "primitive:long", 0),
        ),
    },
)
