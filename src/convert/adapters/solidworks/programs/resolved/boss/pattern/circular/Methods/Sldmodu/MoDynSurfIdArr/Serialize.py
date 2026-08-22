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
            (9237, 4, 4151, "primitive:long", 0),
            (9241, 4, 4164, "primitive:long", 0),
            (9430, 4, 4151, "primitive:long", 1),
            (9434, 4, 4164, "primitive:long", 0),
            (12181, 4, 4151, "primitive:long", 0),
            (12185, 4, 4164, "primitive:long", 0),
            (12225, 4, 4151, "primitive:long", 1),
            (12229, 4, 4164, "primitive:long", 0),
            (17641, 4, 4151, "primitive:long", 1),
            (17645, 4, 4164, "primitive:long", 0),
            (17665, 4, 4151, "primitive:long", 0),
            (17669, 4, 4164, "primitive:long", 0),
        ),
    },
)
