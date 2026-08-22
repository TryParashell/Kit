# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Sldarchiveu.Functions.MoGetModelnameFromPath import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (9617, 1, 3156, "primitive:uchar", 0),
            (9622, 4, 3701, "primitive:long", 0),
            (9626, 4, 3762, "primitive:long", 0),
            (9630, 4, 3826, "primitive:long", 0),
            (9652, 4, 3839, "primitive:long", 0),
            (9656, 4, 3934, "primitive:long", 0),
            (9664, 4, 4388, "primitive:long", 0),
        ),
    },
)
