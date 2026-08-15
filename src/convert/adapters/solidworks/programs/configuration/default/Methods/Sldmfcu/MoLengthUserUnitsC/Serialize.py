# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Sldmfcu.MoLengthUserUnitsC.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "Configuration": (
            (840, 2, 112, "primitive:ushort", 0),
            (906, 2, 112, "primitive:ushort", 3),
            (4203, 2, 112, "primitive:ushort", 0),
            (4269, 2, 112, "primitive:ushort", 3),
            (4713, 2, 112, "primitive:ushort", 2),
            (5149, 2, 112, "primitive:ushort", 0),
            (5215, 2, 112, "primitive:ushort", 3),
            (5647, 2, 112, "primitive:ushort", 0),
            (5713, 2, 112, "primitive:ushort", 3),
            (6153, 2, 112, "primitive:ushort", 0),
            (6219, 2, 112, "primitive:ushort", 3),
            (6655, 2, 112, "primitive:ushort", 0),
            (6721, 2, 112, "primitive:ushort", 3),
            (7169, 2, 112, "primitive:ushort", 0),
            (7235, 2, 112, "primitive:ushort", 3),
            (7707, 2, 112, "primitive:ushort", 0),
            (7773, 2, 112, "primitive:ushort", 3),
            (8213, 2, 112, "primitive:ushort", 2),
            (8665, 2, 112, "primitive:ushort", 0),
            (8731, 2, 112, "primitive:ushort", 3),
        ),
    },
)
