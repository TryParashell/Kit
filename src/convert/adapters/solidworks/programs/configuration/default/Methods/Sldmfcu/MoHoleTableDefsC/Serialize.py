# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Owners.Sldmfcu.MoHoleTableDefsC.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram = (
    KOwnerSites,
    {
        "Configuration": (
            (11495, 4, 256, "primitive:int", 0),
            (11499, 4, 269, "primitive:int", 0),
            (11503, 8, 282, "primitive:double", float.fromhex("0x1.0624dd2f1a9fcp-7")),
            (11511, 8, 295, "primitive:double", float.fromhex("0x1.921fb54442d28p-1")),
            (11519, 4, 308, "primitive:int", 0),
            (11523, 4, 321, "primitive:int", 0),
            (11527, 4, 334, "primitive:int", 2),
            (11531, 4, 347, "primitive:int", 1),
            (11535, 4, 360, "primitive:int", 1),
            (11539, 4, 373, "primitive:int", 1),
            (11543, 4, 403, "primitive:int", 0),
            (11547, 4, 416, "primitive:int", 0),
            (11551, 4, 446, "primitive:int", 2),
            (11555, 4, 484, "primitive:int", 0),
        ),
    },
)
