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
        "ResolvedFeatures": (
            (5316, 2, 1727, "primitive:ushort", 0),
            (5318, 2, 2487, "primitive:ushort", 0),
            (5320, 2, 3321, "primitive:ushort", 0),
            (5322, 2, 4785, "primitive:ushort", 0),
            (5324, 2, 5374, "primitive:ushort", 1),
            (5398, 2, 5913, "primitive:ushort", 0),
            (5400, 2, 6441, "primitive:ushort", 0),
            (5402, 2, 7044, "primitive:ushort", 0),
            (5404, 2, 7640, "primitive:ushort", 0),
            (5406, 2, 8090, "primitive:ushort", 0),
            (5408, 2, 8542, "primitive:ushort", 0),
            (5410, 2, 9002, "primitive:ushort", 0),
            (5416, 2, 9998, "primitive:ushort", 0),
            (5418, 2, 10423, "primitive:ushort", 0),
            (8076, 2, 1727, "primitive:ushort", 0),
            (8078, 2, 2487, "primitive:ushort", 0),
            (8080, 2, 3321, "primitive:ushort", 0),
            (8082, 2, 4785, "primitive:ushort", 0),
            (8084, 2, 5374, "primitive:ushort", 5),
            (8361, 2, 5913, "primitive:ushort", 1),
            (8470, 2, 6441, "primitive:ushort", 0),
            (8472, 2, 7044, "primitive:ushort", 0),
            (8474, 2, 7640, "primitive:ushort", 0),
            (8476, 2, 8090, "primitive:ushort", 0),
            (8478, 2, 8542, "primitive:ushort", 0),
            (8480, 2, 9002, "primitive:ushort", 0),
            (8486, 2, 9998, "primitive:ushort", 0),
            (8488, 2, 10423, "primitive:ushort", 0),
        ),
    },
)
