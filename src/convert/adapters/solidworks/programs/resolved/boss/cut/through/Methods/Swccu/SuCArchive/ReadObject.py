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
            (8835, 4, 370, "primitive:long", 4),
            (8855, 4, 370, "primitive:long", 3),
            (8875, 4, 370, "primitive:long", 2),
            (8895, 4, 370, "primitive:long", 1),
            (9001, 4, 370, "primitive:long", 4),
            (9021, 4, 370, "primitive:long", 1),
            (9041, 4, 370, "primitive:long", 2),
            (9061, 4, 370, "primitive:long", 3),
            (9201, 4, 370, "primitive:long", 5),
            (13828, 4, 370, "primitive:long", 4),
            (13872, 4, 370, "primitive:long", 1),
            (13916, 4, 370, "primitive:long", 3),
            (14481, 4, 370, "primitive:long", 8),
        ),
    },
)
