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
            (5474, 4, 515, "primitive:long", 17),
            (5478, 2, 537, "primitive:ushort", 2),
            (5480, 2, 560, "primitive:ushort", 0),
            (5482, 2, 590, "primitive:ushort", 0),
            (7373, 4, 515, "primitive:long", 5),
            (7377, 2, 537, "primitive:ushort", 2),
            (7379, 2, 560, "primitive:ushort", 0),
            (7381, 2, 590, "primitive:ushort", 0),
            (7428, 4, 515, "primitive:long", 4),
            (7432, 2, 537, "primitive:ushort", 2),
            (7434, 2, 560, "primitive:ushort", 0),
            (7436, 2, 590, "primitive:ushort", 0),
            (7483, 4, 515, "primitive:long", 5),
            (7487, 2, 537, "primitive:ushort", 2),
            (7489, 2, 560, "primitive:ushort", 0),
            (7491, 2, 590, "primitive:ushort", 0),
            (7538, 4, 515, "primitive:long", 4),
            (7542, 2, 537, "primitive:ushort", 2),
            (7544, 2, 560, "primitive:ushort", 0),
            (7546, 2, 590, "primitive:ushort", 0),
        ),
    },
)
