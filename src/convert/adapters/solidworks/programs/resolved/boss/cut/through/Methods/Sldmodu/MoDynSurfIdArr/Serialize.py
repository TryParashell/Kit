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
            (13848, 4, 4151, "primitive:long", 0),
            (13852, 4, 4164, "primitive:long", 0),
            (13892, 4, 4151, "primitive:long", 1),
            (13896, 4, 4164, "primitive:long", 0),
            (14061, 4, 2398, "primitive:long", 3),
            (14065, 4, 2410, "primitive:long", -1),
            (14069, 4, 2422, "primitive:long", 0),
            (14089, 4, 4151, "primitive:long", 0),
            (14093, 4, 4164, "primitive:long", 0),
            (14113, 4, 2398, "primitive:long", 2),
            (14117, 4, 2410, "primitive:long", -1),
            (14121, 4, 2422, "primitive:long", 0),
            (14141, 4, 4151, "primitive:long", 1),
            (14145, 4, 4164, "primitive:long", 0),
            (14165, 4, 2398, "primitive:long", 4),
            (14169, 4, 2410, "primitive:long", -1),
            (14173, 4, 2422, "primitive:long", 0),
            (14255, 4, 2398, "primitive:long", 2),
            (14259, 4, 2410, "primitive:long", -1),
            (14263, 4, 2422, "primitive:long", 0),
            (14283, 4, 4151, "primitive:long", 0),
            (14287, 4, 4164, "primitive:long", 0),
            (14307, 4, 2398, "primitive:long", 1),
            (14311, 4, 2410, "primitive:long", -1),
            (14315, 4, 2422, "primitive:long", 0),
            (14335, 4, 4151, "primitive:long", 1),
            (14339, 4, 4164, "primitive:long", 0),
            (14359, 4, 2398, "primitive:long", 3),
            (14363, 4, 2410, "primitive:long", -1),
            (14367, 4, 2422, "primitive:long", 0),
        ),
    },
)
