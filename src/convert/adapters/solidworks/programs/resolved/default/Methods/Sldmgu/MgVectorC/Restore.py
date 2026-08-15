# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Sldmgu.MgVectorC.Restore import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (3622, 8, 28, "primitive:double", float.fromhex("0x0.0p+0")),
            (3630, 8, 41, "primitive:double", float.fromhex("0x0.0p+0")),
            (4116, 8, 28, "primitive:double", float.fromhex("0x0.0p+0")),
            (4124, 8, 41, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (4686, 8, 28, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (4694, 8, 41, "primitive:double", float.fromhex("0x0.0p+0")),
            (9193, 8, 28, "primitive:double", float.fromhex("0x0.0p+0")),
            (9201, 8, 41, "primitive:double", float.fromhex("0x0.0p+0")),
            (9472, 8, 28, "primitive:double", float.fromhex("0x0.0p+0")),
            (9480, 8, 41, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (9496, 8, 28, "primitive:double", float.fromhex("0x0.0p+0")),
            (9504, 8, 41, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (9988, 8, 28, "primitive:double", float.fromhex("0x0.0p+0")),
            (9996, 8, 41, "primitive:double", float.fromhex("0x0.0p+0")),
            (10012, 8, 28, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (10020, 8, 41, "primitive:double", float.fromhex("0x0.0p+0")),
            (10168, 8, 28, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (10176, 8, 41, "primitive:double", float.fromhex("0x0.0p+0")),
            (10362, 8, 28, "primitive:double", float.fromhex("0x0.0p+0")),
            (10370, 8, 41, "primitive:double", float.fromhex("-0x1.0000000000000p+0")),
        ),
    },
)
