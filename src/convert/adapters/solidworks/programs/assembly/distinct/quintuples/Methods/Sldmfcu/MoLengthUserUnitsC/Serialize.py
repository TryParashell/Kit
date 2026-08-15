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
        "Contents/Config-0": (
            (2971, 2, 112, "primitive:ushort", 0),
            (3037, 2, 112, "primitive:ushort", 3),
            (6011, 2, 112, "primitive:ushort", 0),
            (6077, 2, 112, "primitive:ushort", 3),
            (6521, 2, 112, "primitive:ushort", 2),
            (6957, 2, 112, "primitive:ushort", 0),
            (7023, 2, 112, "primitive:ushort", 3),
            (7455, 2, 112, "primitive:ushort", 0),
            (7521, 2, 112, "primitive:ushort", 3),
            (7961, 2, 112, "primitive:ushort", 0),
            (8027, 2, 112, "primitive:ushort", 3),
            (8463, 2, 112, "primitive:ushort", 0),
            (8529, 2, 112, "primitive:ushort", 3),
            (8977, 2, 112, "primitive:ushort", 0),
            (9043, 2, 112, "primitive:ushort", 3),
            (9515, 2, 112, "primitive:ushort", 0),
            (9581, 2, 112, "primitive:ushort", 3),
            (10021, 2, 112, "primitive:ushort", 2),
            (10473, 2, 112, "primitive:ushort", 0),
            (10539, 2, 112, "primitive:ushort", 3),
        ),
    },
)
