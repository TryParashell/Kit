# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoDimTextC.GetRuntimeClass import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (11164, 4, 4801, "primitive:long", 13),
            (11170, 4, 4848, "primitive:long", 0),
            (11198, 8, 5200, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (11206, 4, 5225, "primitive:long", 0),
            (11210, 4, 5763, "primitive:long", 0),
            (11214, 4, 5810, "primitive:long", 0),
            (11218, 4, 6314, "primitive:long", 0),
            (
                11222,
                8,
                6342,
                "primitive:double",
                float.fromhex("0x1.0c6f7a0b5ed8dp-20"),
            ),
            (
                11230,
                8,
                6358,
                "primitive:double",
                float.fromhex("0x1.0c6f7a0b5ed8dp-20"),
            ),
            (11244, 4, 6586, "primitive:long", 0),
            (11248, 4, 6611, "primitive:long", 0),
            (11252, 4, 6636, "primitive:long", 0),
            (11256, 8, 6652, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (11264, 4, 6668, "primitive:long", 0),
        ),
    },
)
