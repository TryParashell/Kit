# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoRelationC.GetRuntimeClass import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "Configuration": (
            (3026, 4, 3454, "primitive:long", 0),
            (3034, 4, 3580, "primitive:long", 1),
            (3038, 4, 3674, "primitive:long", -1),
            (3044, 4, 3851, "primitive:long", -1),
            (3048, 4, 3872, "primitive:long", 0),
        ),
    },
)
