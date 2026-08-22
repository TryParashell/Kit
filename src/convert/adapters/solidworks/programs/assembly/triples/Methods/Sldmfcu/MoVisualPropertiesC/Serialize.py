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
            (2102, 4, 364, "primitive:ulong", 12632256),
            (2106, 4, 393, "primitive:ulong", 0),
            (2110, 4, 425, "primitive:ulong", 12632256),
            (2222, 4, 529, "primitive:int", 0),
            (2226, 4, 558, "primitive:int", 1),
            (2234, 4, 616, "primitive:int", 0),
            (2238, 4, 683, "primitive:int", 0),
            (2242, 4, 712, "primitive:int", -1),
            (2246, 4, 741, "primitive:int", 0),
            (2250, 4, 773, "primitive:int", 0),
            (2254, 4, 810, "primitive:int", 0),
        ),
    },
)
