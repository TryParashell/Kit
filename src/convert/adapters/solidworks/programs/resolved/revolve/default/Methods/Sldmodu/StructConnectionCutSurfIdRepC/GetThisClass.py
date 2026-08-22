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
            (9351, 4, 299, "primitive:ulong", 1),
            (9355, 4, 318, "primitive:ulong", 0),
            (9359, 4, 458, "primitive:ulong", 5),
            (9363, 4, 672, "primitive:long", 768),
            (9367, 4, 749, "primitive:ulong", 8021),
            (
                9371,
                8,
                1121,
                "primitive:double",
                float.fromhex("0x1.249ad2594c37dp+332"),
            ),
            (
                9379,
                8,
                1134,
                "primitive:double",
                float.fromhex("0x1.249ad2594c37dp+332"),
            ),
            (9621, 4, 1685, "primitive:ulong", 0),
            (9625, 4, 2284, "primitive:long", 0),
            (9629, 4, 2561, "primitive:long", 18000),
            (9633, 4, 2578, "primitive:long", 0),
            (9643, 4, 299, "primitive:ulong", 1),
            (9647, 4, 318, "primitive:ulong", 0),
            (9651, 4, 458, "primitive:ulong", 5),
            (9655, 4, 672, "primitive:long", 768),
            (9659, 4, 749, "primitive:ulong", 8030),
            (
                9663,
                8,
                1121,
                "primitive:double",
                float.fromhex("0x1.249ad2594c37dp+332"),
            ),
            (
                9671,
                8,
                1134,
                "primitive:double",
                float.fromhex("0x1.249ad2594c37dp+332"),
            ),
            (9745, 4, 1685, "primitive:ulong", 0),
            (9749, 4, 2284, "primitive:long", 0),
            (9753, 4, 2561, "primitive:long", 18000),
            (9757, 4, 2578, "primitive:long", 0),
        ),
    },
)
