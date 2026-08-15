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
            (3166, 4, 364, "primitive:ulong", 12632256),
            (3170, 4, 393, "primitive:ulong", 0),
            (3174, 4, 425, "primitive:ulong", 12632256),
            (3286, 4, 529, "primitive:int", 0),
            (3290, 4, 558, "primitive:int", 1),
            (3298, 4, 616, "primitive:int", 0),
            (3302, 4, 683, "primitive:int", 0),
            (3306, 4, 712, "primitive:int", -1),
            (3310, 4, 741, "primitive:int", 0),
            (3314, 4, 773, "primitive:int", 0),
            (3318, 4, 810, "primitive:int", 0),
        ),
    },
)
