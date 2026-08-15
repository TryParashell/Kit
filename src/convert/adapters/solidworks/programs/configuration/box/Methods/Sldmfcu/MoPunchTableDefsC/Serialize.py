# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Sldmfcu.MoPunchTableDefsC.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "Configuration": (
            (12229, 4, 220, "primitive:int", 0),
            (12233, 4, 233, "primitive:int", 0),
            (12237, 8, 246, "primitive:double", float.fromhex("0x1.0624dd2f1a9fcp-7")),
            (12245, 8, 259, "primitive:double", float.fromhex("0x1.921fb54442d28p-1")),
            (12253, 4, 272, "primitive:int", 0),
            (12257, 4, 285, "primitive:int", 0),
            (12261, 4, 298, "primitive:int", 2),
            (12265, 4, 311, "primitive:int", 0),
            (12269, 4, 324, "primitive:int", 2),
            (12273, 4, 337, "primitive:int", 1),
        ),
    },
)
