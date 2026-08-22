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
            (5008, 2, 1727, "primitive:ushort", 0),
            (5010, 2, 2487, "primitive:ushort", 0),
            (5012, 2, 3321, "primitive:ushort", 0),
            (5014, 2, 4785, "primitive:ushort", 0),
            (5016, 2, 5374, "primitive:ushort", 1),
            (5090, 2, 5913, "primitive:ushort", 0),
            (5092, 2, 6441, "primitive:ushort", 0),
            (5094, 2, 7044, "primitive:ushort", 0),
            (5096, 2, 7640, "primitive:ushort", 0),
            (5098, 2, 8090, "primitive:ushort", 0),
            (5100, 2, 8542, "primitive:ushort", 0),
            (5102, 2, 9002, "primitive:ushort", 0),
            (5108, 2, 9998, "primitive:ushort", 0),
            (5110, 2, 10423, "primitive:ushort", 0),
        ),
    },
)
