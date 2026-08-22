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
            (8665, 4, 4151, "primitive:long", 0),
            (8669, 4, 4164, "primitive:long", 0),
            (8858, 4, 4151, "primitive:long", 1),
            (8862, 4, 4164, "primitive:long", 0),
            (11495, 4, 141, "primitive:long", 2),
            (11691, 4, 4151, "primitive:long", 1),
            (11695, 4, 4164, "primitive:long", 0),
            (11715, 4, 4151, "primitive:long", 0),
            (11719, 4, 4164, "primitive:long", 0),
            (11739, 4, 141, "primitive:long", 0),
            (14186, 4, 4151, "primitive:long", 1),
            (14190, 4, 4164, "primitive:long", 0),
            (14230, 4, 4151, "primitive:long", 0),
            (14234, 4, 4164, "primitive:long", 0),
            (14466, 4, 4151, "primitive:long", 1),
            (14470, 4, 4164, "primitive:long", 0),
            (14490, 4, 4151, "primitive:long", 0),
            (14494, 4, 4164, "primitive:long", 0),
            (14806, 4, 4151, "primitive:long", 1),
            (14810, 4, 4164, "primitive:long", 0),
            (14830, 4, 4151, "primitive:long", 0),
            (14834, 4, 4164, "primitive:long", 0),
        ),
    },
)
