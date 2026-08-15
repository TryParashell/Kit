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
        "Contents/Config-0": (
            (3149, 2, 72, "primitive:ushort", 0),
            (3600, 2, 72, "primitive:ushort", 4),
            (3684, 2, 72, "primitive:ushort", 2),
            (6005, 2, 72, "primitive:ushort", 0),
            (6449, 2, 72, "primitive:ushort", 0),
            (6951, 2, 72, "primitive:ushort", 0),
            (7449, 2, 72, "primitive:ushort", 0),
            (7955, 2, 72, "primitive:ushort", 0),
            (8457, 2, 72, "primitive:ushort", 0),
            (8971, 2, 72, "primitive:ushort", 0),
            (9509, 2, 72, "primitive:ushort", 0),
            (9949, 2, 72, "primitive:ushort", 0),
            (10467, 2, 72, "primitive:ushort", 0),
        ),
    },
)
