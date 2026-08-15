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
            (882, 4, 126, "primitive:long", 32),
            (5758, 4, 126, "primitive:long", 2),
            (7958, 4, 126, "primitive:long", 3),
            (8612, 4, 126, "primitive:long", 32),
            (8663, 4, 126, "primitive:long", 32),
            (8683, 4, 126, "primitive:long", 32),
            (8703, 4, 126, "primitive:long", 32),
            (8723, 4, 126, "primitive:long", 32),
            (8805, 4, 126, "primitive:long", 32),
            (8829, 4, 126, "primitive:long", 32),
            (8849, 4, 126, "primitive:long", 32),
            (8869, 4, 126, "primitive:long", 32),
            (8889, 4, 126, "primitive:long", 32),
        ),
    },
)
