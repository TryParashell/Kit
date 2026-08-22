# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoFtrFolderC.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (1976, 4, 281, "primitive:long", 0),
            (1980, 4, 350, "primitive:long", 0),
            (1984, 4, 429, "primitive:long", 1),
            (1988, 4, 484, "primitive:long", 1),
            (1992, 4, 281, "primitive:long", 1),
            (1996, 4, 350, "primitive:long", 0),
            (2000, 4, 429, "primitive:long", 1),
            (2004, 4, 484, "primitive:long", 1),
        ),
    },
)
