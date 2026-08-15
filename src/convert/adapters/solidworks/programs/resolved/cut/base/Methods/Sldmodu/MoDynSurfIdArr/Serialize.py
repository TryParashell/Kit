# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoDynSurfIdArr.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (8784, 4, 4151, "primitive:long", 0),
            (8788, 4, 4164, "primitive:long", 0),
            (8977, 4, 4151, "primitive:long", 1),
            (8981, 4, 4164, "primitive:long", 0),
            (13955, 4, 4151, "primitive:long", 0),
            (13959, 4, 4164, "primitive:long", 0),
            (13999, 4, 4151, "primitive:long", 1),
            (14003, 4, 4164, "primitive:long", 0),
            (14165, 4, 3283, "primitive:long", 1),
            (14169, 4, 3296, "primitive:long", 0),
            (14173, 4, 3309, "primitive:long", 0),
            (14224, 4, 2398, "primitive:long", 4),
            (14228, 4, 2410, "primitive:long", -1),
            (14232, 4, 2422, "primitive:long", 0),
            (14252, 4, 2398, "primitive:long", 3),
            (14256, 4, 2410, "primitive:long", -1),
            (14260, 4, 2422, "primitive:long", 0),
            (14280, 4, 2398, "primitive:long", 2),
            (14284, 4, 2410, "primitive:long", -1),
            (14288, 4, 2422, "primitive:long", 0),
            (14308, 4, 2398, "primitive:long", 1),
            (14312, 4, 2410, "primitive:long", -1),
            (14316, 4, 2422, "primitive:long", 0),
            (14398, 4, 2398, "primitive:long", 3),
            (14402, 4, 2410, "primitive:long", -1),
            (14406, 4, 2422, "primitive:long", 0),
            (14426, 4, 4151, "primitive:long", 0),
            (14430, 4, 4164, "primitive:long", 0),
            (14450, 4, 2398, "primitive:long", 2),
            (14454, 4, 2410, "primitive:long", -1),
            (14458, 4, 2422, "primitive:long", 0),
            (14478, 4, 3283, "primitive:long", 1),
            (14482, 4, 3296, "primitive:long", 0),
            (14486, 4, 3309, "primitive:long", 0),
            (14506, 4, 2398, "primitive:long", 4),
            (14510, 4, 2410, "primitive:long", -1),
            (14514, 4, 2422, "primitive:long", 0),
        ),
    },
)
