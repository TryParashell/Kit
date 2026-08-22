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
            (12180, 4, 299, "primitive:ulong", 1),
            (12184, 4, 318, "primitive:ulong", 0),
            (12188, 4, 458, "primitive:ulong", 6),
            (12192, 4, 672, "primitive:long", 768),
            (12196, 4, 749, "primitive:ulong", 0),
            (
                12200,
                8,
                1121,
                "primitive:double",
                float.fromhex("0x1.249ad2594c37dp+332"),
            ),
            (
                12208,
                8,
                1134,
                "primitive:double",
                float.fromhex("0x1.249ad2594c37dp+332"),
            ),
            (12516, 4, 1685, "primitive:ulong", 0),
            (12520, 4, 2284, "primitive:long", 0),
            (12524, 4, 2561, "primitive:long", 18000),
            (12528, 4, 2578, "primitive:long", 0),
            (12538, 4, 299, "primitive:ulong", 1),
            (12542, 4, 318, "primitive:ulong", 0),
            (12546, 4, 458, "primitive:ulong", 6),
            (12550, 4, 672, "primitive:long", 768),
            (12554, 4, 749, "primitive:ulong", 0),
            (
                12558,
                8,
                1121,
                "primitive:double",
                float.fromhex("0x1.249ad2594c37dp+332"),
            ),
            (
                12566,
                8,
                1134,
                "primitive:double",
                float.fromhex("0x1.249ad2594c37dp+332"),
            ),
            (12682, 4, 1685, "primitive:ulong", 0),
            (12686, 4, 2284, "primitive:long", 0),
            (12690, 4, 2561, "primitive:long", 18000),
            (12694, 4, 2578, "primitive:long", 0),
        ),
    },
)
