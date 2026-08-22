# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Sldmodu.SgSketch.IPostLoad import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "Contents/Config-0-ResolvedFeatures": (
            (4728, 2, 1727, "primitive:ushort", 0),
            (4730, 2, 2487, "primitive:ushort", 0),
            (4732, 2, 3321, "primitive:ushort", 0),
            (4734, 2, 4785, "primitive:ushort", 0),
            (4736, 2, 5374, "primitive:ushort", 1),
            (4810, 2, 5913, "primitive:ushort", 0),
            (4812, 2, 6441, "primitive:ushort", 0),
            (4814, 2, 7044, "primitive:ushort", 0),
            (4816, 2, 7640, "primitive:ushort", 0),
            (4818, 2, 8090, "primitive:ushort", 0),
            (4820, 2, 8542, "primitive:ushort", 0),
            (4822, 2, 9002, "primitive:ushort", 0),
            (4828, 2, 9998, "primitive:ushort", 0),
            (4830, 2, 10423, "primitive:ushort", 0),
        ),
    },
)
