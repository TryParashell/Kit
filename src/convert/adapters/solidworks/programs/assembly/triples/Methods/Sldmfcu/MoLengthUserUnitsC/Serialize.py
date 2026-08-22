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
            (2367, 2, 112, "primitive:ushort", 0),
            (2433, 2, 112, "primitive:ushort", 3),
            (5407, 2, 112, "primitive:ushort", 0),
            (5473, 2, 112, "primitive:ushort", 3),
            (5917, 2, 112, "primitive:ushort", 2),
            (6353, 2, 112, "primitive:ushort", 0),
            (6419, 2, 112, "primitive:ushort", 3),
            (6851, 2, 112, "primitive:ushort", 0),
            (6917, 2, 112, "primitive:ushort", 3),
            (7357, 2, 112, "primitive:ushort", 0),
            (7423, 2, 112, "primitive:ushort", 3),
            (7859, 2, 112, "primitive:ushort", 0),
            (7925, 2, 112, "primitive:ushort", 3),
            (8373, 2, 112, "primitive:ushort", 0),
            (8439, 2, 112, "primitive:ushort", 3),
            (8911, 2, 112, "primitive:ushort", 0),
            (8977, 2, 112, "primitive:ushort", 3),
            (9417, 2, 112, "primitive:ushort", 2),
            (9869, 2, 112, "primitive:ushort", 0),
            (9935, 2, 112, "primitive:ushort", 3),
        ),
    },
)
