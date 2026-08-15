# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Sldmfcu.MoForceUnitsC.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "Configuration": (
            (994, 2, 72, "primitive:ushort", 0),
            (1445, 2, 72, "primitive:ushort", 4),
            (1529, 2, 72, "primitive:ushort", 2),
            (4365, 2, 72, "primitive:ushort", 0),
            (4809, 2, 72, "primitive:ushort", 0),
            (5311, 2, 72, "primitive:ushort", 0),
            (5809, 2, 72, "primitive:ushort", 0),
            (6315, 2, 72, "primitive:ushort", 0),
            (6817, 2, 72, "primitive:ushort", 0),
            (7331, 2, 72, "primitive:ushort", 0),
            (7869, 2, 72, "primitive:ushort", 0),
            (8309, 2, 72, "primitive:ushort", 0),
            (8827, 2, 72, "primitive:ushort", 0),
        ),
    },
)
