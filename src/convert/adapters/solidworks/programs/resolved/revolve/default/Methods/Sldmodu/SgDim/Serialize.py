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
            (5355, 4, 515, "primitive:long", 17),
            (5359, 2, 537, "primitive:ushort", 2),
            (5361, 2, 560, "primitive:ushort", 0),
            (5363, 2, 590, "primitive:ushort", 0),
            (8115, 4, 515, "primitive:long", 5),
            (8119, 2, 537, "primitive:ushort", 2),
            (8121, 2, 560, "primitive:ushort", 0),
            (8123, 2, 590, "primitive:ushort", 0),
            (8170, 4, 515, "primitive:long", 5),
            (8174, 2, 537, "primitive:ushort", 2),
            (8176, 2, 560, "primitive:ushort", 0),
            (8178, 2, 590, "primitive:ushort", 0),
            (8225, 4, 515, "primitive:long", 4),
            (8229, 2, 537, "primitive:ushort", 2),
            (8231, 2, 560, "primitive:ushort", 0),
            (8233, 2, 590, "primitive:ushort", 0),
            (8280, 4, 515, "primitive:long", 5),
            (8284, 2, 537, "primitive:ushort", 2),
            (8286, 2, 560, "primitive:ushort", 0),
            (8288, 2, 590, "primitive:ushort", 0),
            (8335, 4, 515, "primitive:long", 4),
            (8339, 2, 537, "primitive:ushort", 2),
            (8341, 2, 560, "primitive:ushort", 0),
            (8343, 2, 590, "primitive:ushort", 0),
            (8392, 4, 515, "primitive:long", 9),
            (8396, 2, 537, "primitive:ushort", 2),
            (8398, 2, 560, "primitive:ushort", 0),
            (8400, 2, 590, "primitive:ushort", 0),
        ),
    },
)
