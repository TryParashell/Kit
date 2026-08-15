# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Sldmfcu.MoVisualPropertiesC.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "Contents/Config-0": (
            (1476, 4, 364, "primitive:ulong", 12632256),
            (1480, 4, 393, "primitive:ulong", 0),
            (1484, 4, 425, "primitive:ulong", 12632256),
            (1596, 4, 529, "primitive:int", 0),
            (1600, 4, 558, "primitive:int", 1),
            (1608, 4, 616, "primitive:int", 0),
            (1612, 4, 683, "primitive:int", 0),
            (1616, 4, 712, "primitive:int", -1),
            (1620, 4, 741, "primitive:int", 0),
            (1624, 4, 773, "primitive:int", 0),
            (1628, 4, 810, "primitive:int", 0),
        ),
    },
)
