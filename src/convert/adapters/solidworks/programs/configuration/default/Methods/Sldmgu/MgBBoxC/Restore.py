# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Owners.Sldmgu.MgBBoxC.Restore import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram = (
    KOwnerSites,
    {
        "Configuration": (
            (2378, 8, 30, "primitive:double", float.fromhex("0x0.0p+0")),
            (2386, 8, 55, "primitive:double", float.fromhex("0x0.0p+0")),
            (2394, 8, 80, "primitive:double", float.fromhex("0x1.47ae147ae147bp-8")),
            (2402, 8, 105, "primitive:double", float.fromhex("0x1.47ae147ae147bp-6")),
            (2410, 8, 130, "primitive:double", float.fromhex("0x1.47ae147ae147bp-7")),
            (2418, 8, 155, "primitive:double", float.fromhex("0x1.47ae147ae147bp-7")),
            (2426, 8, 180, "primitive:double", float.fromhex("-0x1.47ae147ae147bp-6")),
            (2434, 8, 205, "primitive:double", float.fromhex("-0x1.47ae147ae147bp-7")),
            (2442, 8, 230, "primitive:double", float.fromhex("0x0.0p+0")),
        ),
    },
)
