# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Sldmfcu.MoDatumDefsC.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "Configuration": (
            (9623, 4, 133, "primitive:int", 0),
            (9627, 4, 153, "primitive:int", 1),
            (9631, 4, 166, "primitive:int", 0),
            (9635, 4, 179, "primitive:int", 1),
            (9639, 4, 192, "primitive:int", 0),
            (9643, 4, 206, "primitive:int", 0),
        ),
    },
)
