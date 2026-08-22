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
            (8327, 4, 299, "primitive:ulong", 1),
            (8331, 4, 318, "primitive:ulong", 0),
            (8335, 4, 458, "primitive:ulong", 6),
            (8339, 4, 672, "primitive:long", 768),
            (8343, 4, 749, "primitive:ulong", 0),
            (
                8347,
                8,
                1121,
                "primitive:double",
                float.fromhex("0x1.249ad2594c37dp+332"),
            ),
            (
                8355,
                8,
                1134,
                "primitive:double",
                float.fromhex("0x1.249ad2594c37dp+332"),
            ),
            (8665, 4, 1685, "primitive:ulong", 0),
            (8669, 4, 2284, "primitive:long", 0),
            (8673, 4, 2561, "primitive:long", 18000),
            (8677, 4, 2578, "primitive:long", 0),
            (8687, 4, 299, "primitive:ulong", 1),
            (8691, 4, 318, "primitive:ulong", 0),
            (8695, 4, 458, "primitive:ulong", 6),
            (8699, 4, 672, "primitive:long", 768),
            (8703, 4, 749, "primitive:ulong", 0),
            (
                8707,
                8,
                1121,
                "primitive:double",
                float.fromhex("0x1.249ad2594c37dp+332"),
            ),
            (
                8715,
                8,
                1134,
                "primitive:double",
                float.fromhex("0x1.249ad2594c37dp+332"),
            ),
            (8831, 4, 1685, "primitive:ulong", 0),
            (8835, 4, 2284, "primitive:long", 0),
            (8839, 4, 2561, "primitive:long", 18000),
            (8843, 4, 2578, "primitive:long", 0),
        ),
    },
)
