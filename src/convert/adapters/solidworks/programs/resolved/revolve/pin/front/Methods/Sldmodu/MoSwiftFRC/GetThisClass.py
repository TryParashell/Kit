# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoSwiftFRC.GetThisClass import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (763, 4, 126, "primitive:long", 26),
            (882, 4, 126, "primitive:long", 31),
            (5758, 4, 126, "primitive:long", 2),
            (6560, 4, 126, "primitive:long", 5),
            (9121, 4, 126, "primitive:long", 2),
            (9695, 4, 126, "primitive:long", 31),
            (9715, 4, 126, "primitive:long", 31),
            (9737, 4, 126, "primitive:long", 31),
            (9819, 4, 126, "primitive:long", 31),
            (9839, 4, 126, "primitive:long", 31),
            (9861, 4, 126, "primitive:long", 31),
            (10196, 4, 126, "primitive:long", 26),
        ),
    },
)
