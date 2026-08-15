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
            (8772, 4, 4151, "primitive:long", 0),
            (8776, 4, 4164, "primitive:long", 0),
            (8965, 4, 4151, "primitive:long", 1),
            (8969, 4, 4164, "primitive:long", 0),
            (11710, 4, 4151, "primitive:long", 0),
            (11714, 4, 4164, "primitive:long", 0),
            (11754, 4, 4151, "primitive:long", 1),
            (11758, 4, 4164, "primitive:long", 0),
            (18815, 4, 4151, "primitive:long", 1),
            (18819, 4, 4164, "primitive:long", 0),
            (18839, 4, 4151, "primitive:long", 0),
            (18843, 4, 4164, "primitive:long", 0),
        ),
    },
)
