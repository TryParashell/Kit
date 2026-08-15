# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Owners.Sldmfcu.MoVisualPropertiesC.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram = (
    KOwnerSites,
    {
        "Configuration": (
            (110, 4, 364, "primitive:ulong", 15651274),
            (114, 4, 393, "primitive:ulong", 0),
            (118, 4, 425, "primitive:ulong", 0),
            (695, 4, 529, "primitive:int", 0),
            (699, 4, 558, "primitive:int", 1),
            (707, 4, 616, "primitive:int", 0),
            (711, 4, 683, "primitive:int", 1),
            (715, 4, 712, "primitive:int", -1),
            (719, 4, 741, "primitive:int", 0),
            (723, 4, 773, "primitive:int", 0),
            (727, 4, 810, "primitive:int", 0),
        ),
    },
)
