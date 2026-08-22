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
            (8135, 4, 515, "primitive:long", 4),
            (8139, 2, 537, "primitive:ushort", 2),
            (8141, 2, 560, "primitive:ushort", 0),
            (8143, 2, 590, "primitive:ushort", 0),
            (8190, 4, 515, "primitive:long", 5),
            (8194, 2, 537, "primitive:ushort", 2),
            (8196, 2, 560, "primitive:ushort", 0),
            (8198, 2, 590, "primitive:ushort", 0),
            (8245, 4, 515, "primitive:long", 4),
            (8249, 2, 537, "primitive:ushort", 2),
            (8251, 2, 560, "primitive:ushort", 0),
            (8253, 2, 590, "primitive:ushort", 0),
            (8300, 4, 515, "primitive:long", 5),
            (8304, 2, 537, "primitive:ushort", 2),
            (8306, 2, 560, "primitive:ushort", 0),
            (8308, 2, 590, "primitive:ushort", 0),
            (8355, 4, 515, "primitive:long", 4),
            (8359, 2, 537, "primitive:ushort", 2),
            (8361, 2, 560, "primitive:ushort", 0),
            (8363, 2, 590, "primitive:ushort", 0),
            (8410, 4, 515, "primitive:long", 5),
            (8414, 2, 537, "primitive:ushort", 2),
            (8416, 2, 560, "primitive:ushort", 0),
            (8418, 2, 590, "primitive:ushort", 0),
            (8467, 4, 515, "primitive:long", 9),
            (8471, 2, 537, "primitive:ushort", 2),
            (8473, 2, 560, "primitive:ushort", 0),
            (8475, 2, 590, "primitive:ushort", 0),
        ),
    },
)
