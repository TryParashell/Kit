# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoMateBeltDimC.GetThisClass import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (10567, 4, 290, "primitive:ulong", 8),
            (10571, 4, 350, "primitive:ulong", 16),
            (10575, 4, 363, "primitive:ulong", 1),
            (10579, 4, 376, "primitive:ulong", 1),
            (13066, 4, 290, "primitive:ulong", 8),
            (13070, 4, 350, "primitive:ulong", 16),
            (13074, 4, 363, "primitive:ulong", 1),
            (13078, 4, 376, "primitive:ulong", 1),
        ),
    },
)
