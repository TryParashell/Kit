# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Owners.Sldmfcu.MoForceUnitsC.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram = (
    KOwnerSites,
    {
        "Configuration": (
            (996, 2, 72, "primitive:ushort", 0),
            (1447, 2, 72, "primitive:ushort", 4),
            (1531, 2, 72, "primitive:ushort", 2),
            (4335, 2, 72, "primitive:ushort", 0),
            (4779, 2, 72, "primitive:ushort", 0),
            (5281, 2, 72, "primitive:ushort", 0),
            (5779, 2, 72, "primitive:ushort", 0),
            (6285, 2, 72, "primitive:ushort", 0),
            (6787, 2, 72, "primitive:ushort", 0),
            (7301, 2, 72, "primitive:ushort", 0),
            (7839, 2, 72, "primitive:ushort", 0),
            (8279, 2, 72, "primitive:ushort", 0),
            (8797, 2, 72, "primitive:ushort", 0),
        ),
    },
)
