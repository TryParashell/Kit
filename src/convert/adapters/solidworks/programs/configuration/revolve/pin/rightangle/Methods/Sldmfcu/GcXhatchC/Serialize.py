# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Owners.Sldmfcu.GcXhatchC.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram = (
    KOwnerSites,
    {
        "Configuration": (
            (2670, 8, 812, "primitive:double", float.fromhex("0x0.0p+0")),
            (2678, 8, 825, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (2686, 4, 927, "primitive:int", 0),
            (2690, 4, 968, "primitive:int", 0),
            (2694, 4, 997, "primitive:int", 1),
            (2698, 4, 1026, "primitive:int", -1),
            (2702, 4, 1039, "primitive:int", -1),
            (2706, 4, 1098, "primitive:int", 0),
        ),
    },
)
