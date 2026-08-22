# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoVisualOverlayObjectC.GetThisClass import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "Contents/CMgr": (
            (765, 4, 2847, "primitive:long", 0),
            (777, 4, 2847, "primitive:long", 0),
            (781, 4, 3167, "primitive:long", 0),
            (817, 4, 4159, "primitive:long", 0),
            (825, 4, 2847, "primitive:long", 0),
            (2400, 4, 4159, "primitive:long", 0),
        ),
        "Contents/Config-0": (
            (18, 4, 6976, "primitive:long", 3498),
            (3520, 4, 6976, "primitive:long", 21639),
        ),
    },
)
