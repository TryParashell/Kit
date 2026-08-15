# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Swccu.SuCArchive.ReadObject import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (8599, 4, 370, "primitive:long", 4),
            (8619, 4, 370, "primitive:long", 3),
            (8639, 4, 370, "primitive:long", 2),
            (8659, 4, 370, "primitive:long", 1),
            (8765, 4, 370, "primitive:long", 4),
            (8785, 4, 370, "primitive:long", 1),
            (8805, 4, 370, "primitive:long", 2),
            (8825, 4, 370, "primitive:long", 3),
            (8965, 4, 370, "primitive:long", 5),
        ),
    },
)
