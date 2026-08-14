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
        "Contents/Config-0": (
            (12073, 4, 256, "primitive:int", 0),
            (12077, 4, 269, "primitive:int", 0),
            (12081, 8, 282, "primitive:double", float.fromhex("0x1.0624dd2f1a9fcp-7")),
            (12089, 8, 295, "primitive:double", float.fromhex("0x1.921fb54442d28p-1")),
            (12097, 4, 308, "primitive:int", 0),
            (12101, 4, 321, "primitive:int", 0),
            (12105, 4, 334, "primitive:int", 2),
            (12109, 4, 347, "primitive:int", 1),
            (12113, 4, 360, "primitive:int", 1),
            (12117, 4, 373, "primitive:int", 1),
            (12121, 4, 403, "primitive:int", 0),
            (12125, 4, 416, "primitive:int", 0),
            (12129, 4, 446, "primitive:int", 2),
            (12133, 4, 484, "primitive:int", 0),
        ),
    },
)
