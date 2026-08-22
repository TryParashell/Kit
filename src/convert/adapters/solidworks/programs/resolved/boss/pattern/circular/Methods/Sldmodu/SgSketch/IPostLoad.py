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
            (5435, 2, 1727, "primitive:ushort", 0),
            (5437, 2, 2487, "primitive:ushort", 0),
            (5439, 2, 3321, "primitive:ushort", 0),
            (5441, 2, 4785, "primitive:ushort", 0),
            (5443, 2, 5374, "primitive:ushort", 1),
            (5517, 2, 5913, "primitive:ushort", 0),
            (5519, 2, 6441, "primitive:ushort", 0),
            (5521, 2, 7044, "primitive:ushort", 0),
            (5523, 2, 7640, "primitive:ushort", 0),
            (5525, 2, 8090, "primitive:ushort", 0),
            (5527, 2, 8542, "primitive:ushort", 0),
            (5529, 2, 9002, "primitive:ushort", 0),
            (5535, 2, 9998, "primitive:ushort", 0),
            (5537, 2, 10423, "primitive:ushort", 0),
            (7799, 2, 1727, "primitive:ushort", 0),
            (7801, 2, 2487, "primitive:ushort", 0),
            (7803, 2, 3321, "primitive:ushort", 0),
            (7805, 2, 4785, "primitive:ushort", 0),
            (7807, 2, 5374, "primitive:ushort", 4),
            (8029, 2, 5913, "primitive:ushort", 1),
            (8138, 2, 6441, "primitive:ushort", 0),
            (8140, 2, 7044, "primitive:ushort", 0),
            (8142, 2, 7640, "primitive:ushort", 0),
            (8144, 2, 8090, "primitive:ushort", 0),
            (8146, 2, 8542, "primitive:ushort", 0),
            (8148, 2, 9002, "primitive:ushort", 0),
            (8154, 2, 9998, "primitive:ushort", 0),
            (8156, 2, 10423, "primitive:ushort", 0),
        ),
    },
)
