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
            (7254, 4, 515, "primitive:long", 5),
            (7258, 2, 537, "primitive:ushort", 2),
            (7260, 2, 560, "primitive:ushort", 0),
            (7262, 2, 590, "primitive:ushort", 0),
            (7309, 4, 515, "primitive:long", 4),
            (7313, 2, 537, "primitive:ushort", 2),
            (7315, 2, 560, "primitive:ushort", 0),
            (7317, 2, 590, "primitive:ushort", 0),
            (7364, 4, 515, "primitive:long", 5),
            (7368, 2, 537, "primitive:ushort", 2),
            (7370, 2, 560, "primitive:ushort", 0),
            (7372, 2, 590, "primitive:ushort", 0),
            (7419, 4, 515, "primitive:long", 4),
            (7423, 2, 537, "primitive:ushort", 2),
            (7425, 2, 560, "primitive:ushort", 0),
            (7427, 2, 590, "primitive:ushort", 0),
        ),
    },
)
