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
            (9784, 4, 4801, "primitive:long", 18),
            (9790, 4, 4848, "primitive:long", 0),
            (9818, 8, 5200, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (9826, 4, 5225, "primitive:long", 0),
            (9830, 4, 5763, "primitive:long", 0),
            (9834, 4, 5810, "primitive:long", 0),
            (9838, 4, 6314, "primitive:long", 0),
            (9842, 8, 6342, "primitive:double", float.fromhex("0x1.0c6f7a0b5ed8dp-20")),
            (9850, 8, 6358, "primitive:double", float.fromhex("0x1.0c6f7a0b5ed8dp-20")),
            (9858, 4, 6383, "primitive:long", 0),
            (9864, 4, 6586, "primitive:long", 0),
            (9868, 4, 6611, "primitive:long", 0),
            (9872, 4, 6636, "primitive:long", 0),
            (9876, 8, 6652, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (9884, 4, 6668, "primitive:long", 0),
        ),
    },
)
