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
        "Contents/Config-0": (
            (2728, 4, 364, "primitive:ulong", 12632256),
            (2732, 4, 393, "primitive:ulong", 0),
            (2736, 4, 425, "primitive:ulong", 12632256),
            (2848, 4, 529, "primitive:int", 0),
            (2852, 4, 558, "primitive:int", 1),
            (2860, 4, 616, "primitive:int", 0),
            (2864, 4, 683, "primitive:int", 0),
            (2868, 4, 712, "primitive:int", -1),
            (2872, 4, 741, "primitive:int", 0),
            (2876, 4, 773, "primitive:int", 0),
            (2880, 4, 810, "primitive:int", 0),
        ),
    },
)
