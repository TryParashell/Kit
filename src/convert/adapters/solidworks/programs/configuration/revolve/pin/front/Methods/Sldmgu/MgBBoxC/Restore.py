# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Sldmgu.MgBBoxC.Restore import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "Configuration": (
            (2376, 8, 30, "primitive:double", float.fromhex("0x0.0p+0")),
            (2384, 8, 55, "primitive:double", float.fromhex("-0x1.999999999999ap-6")),
            (2392, 8, 80, "primitive:double", float.fromhex("0x0.0p+0")),
            (2400, 8, 105, "primitive:double", float.fromhex("0x1.47ae147ae147bp-9")),
            (2408, 8, 130, "primitive:double", float.fromhex("0x0.0p+0")),
            (2416, 8, 155, "primitive:double", float.fromhex("0x1.47ae147ae147bp-9")),
            (2424, 8, 180, "primitive:double", float.fromhex("-0x1.47ae147ae147bp-9")),
            (2432, 8, 205, "primitive:double", float.fromhex("-0x1.999999999999ap-5")),
            (2440, 8, 230, "primitive:double", float.fromhex("-0x1.47ae147ae147bp-9")),
        ),
    },
)
