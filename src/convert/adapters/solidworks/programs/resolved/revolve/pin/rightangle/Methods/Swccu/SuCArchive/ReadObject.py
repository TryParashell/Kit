# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Swccu.SuCArchive.ReadObject import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (9823, 4, 370, "primitive:long", 7),
            (9867, 4, 370, "primitive:long", 3),
            (9887, 4, 370, "primitive:long", 4),
            (9907, 4, 370, "primitive:long", 5),
            (9927, 4, 370, "primitive:long", 6),
            (10033, 4, 370, "primitive:long", 7),
            (10053, 4, 370, "primitive:long", 6),
            (10073, 4, 370, "primitive:long", 5),
            (10093, 4, 370, "primitive:long", 4),
            (10113, 4, 370, "primitive:long", 3),
            (10277, 4, 370, "primitive:long", 5),
        ),
    },
)
