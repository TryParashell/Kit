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
            (11658, 4, 4151, "primitive:long", 1),
            (11662, 4, 4164, "primitive:long", 0),
            (13736, 4, 4151, "primitive:long", 0),
            (13740, 4, 4164, "primitive:long", 0),
        ),
    },
)
