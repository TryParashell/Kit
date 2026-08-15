# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Sldmodu.SgDim.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (5593, 4, 515, "primitive:long", 17),
            (5597, 2, 537, "primitive:ushort", 2),
            (5599, 2, 560, "primitive:ushort", 0),
            (5601, 2, 590, "primitive:ushort", 0),
            (7492, 4, 515, "primitive:long", 5),
            (7496, 2, 537, "primitive:ushort", 2),
            (7498, 2, 560, "primitive:ushort", 0),
            (7500, 2, 590, "primitive:ushort", 0),
            (7547, 4, 515, "primitive:long", 4),
            (7551, 2, 537, "primitive:ushort", 2),
            (7553, 2, 560, "primitive:ushort", 0),
            (7555, 2, 590, "primitive:ushort", 0),
            (7602, 4, 515, "primitive:long", 5),
            (7606, 2, 537, "primitive:ushort", 2),
            (7608, 2, 560, "primitive:ushort", 0),
            (7610, 2, 590, "primitive:ushort", 0),
            (7657, 4, 515, "primitive:long", 4),
            (7661, 2, 537, "primitive:ushort", 2),
            (7663, 2, 560, "primitive:ushort", 0),
            (7665, 2, 590, "primitive:ushort", 0),
            (12687, 4, 515, "primitive:long", 5),
            (12691, 2, 537, "primitive:ushort", 2),
            (12693, 2, 560, "primitive:ushort", 0),
            (12695, 2, 590, "primitive:ushort", 0),
            (12742, 4, 515, "primitive:long", 4),
            (12746, 2, 537, "primitive:ushort", 2),
            (12748, 2, 560, "primitive:ushort", 0),
            (12750, 2, 590, "primitive:ushort", 0),
            (12797, 4, 515, "primitive:long", 5),
            (12801, 2, 537, "primitive:ushort", 2),
            (12803, 2, 560, "primitive:ushort", 0),
            (12805, 2, 590, "primitive:ushort", 0),
            (12852, 4, 515, "primitive:long", 4),
            (12856, 2, 537, "primitive:ushort", 2),
            (12858, 2, 560, "primitive:ushort", 0),
            (12860, 2, 590, "primitive:ushort", 0),
        ),
    },
)
