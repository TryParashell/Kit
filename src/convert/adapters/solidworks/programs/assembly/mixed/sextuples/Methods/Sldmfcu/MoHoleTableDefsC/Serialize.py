# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Sldmfcu.MoHoleTableDefsC.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "Contents/Config-0": (
            (13165, 4, 256, "primitive:int", 0),
            (13169, 4, 269, "primitive:int", 0),
            (13173, 8, 282, "primitive:double", float.fromhex("0x1.0624dd2f1a9fcp-7")),
            (13181, 8, 295, "primitive:double", float.fromhex("0x1.921fb54442d28p-1")),
            (13189, 4, 308, "primitive:int", 0),
            (13193, 4, 321, "primitive:int", 0),
            (13197, 4, 334, "primitive:int", 2),
            (13201, 4, 347, "primitive:int", 1),
            (13205, 4, 360, "primitive:int", 1),
            (13209, 4, 373, "primitive:int", 1),
            (13213, 4, 403, "primitive:int", 0),
            (13217, 4, 416, "primitive:int", 0),
            (13221, 4, 446, "primitive:int", 2),
            (13225, 4, 484, "primitive:int", 0),
        ),
    },
)
