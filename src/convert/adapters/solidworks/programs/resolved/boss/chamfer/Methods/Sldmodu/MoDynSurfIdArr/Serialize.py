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
            (11498, 4, 141, "primitive:long", 2),
            (11694, 4, 4151, "primitive:long", 1),
            (11698, 4, 4164, "primitive:long", 0),
            (11718, 4, 4151, "primitive:long", 0),
            (11722, 4, 4164, "primitive:long", 0),
            (15643, 4, 4151, "primitive:long", 1),
            (15647, 4, 4164, "primitive:long", 0),
            (15667, 4, 4151, "primitive:long", 0),
            (15671, 4, 4164, "primitive:long", 0),
        ),
    },
)
