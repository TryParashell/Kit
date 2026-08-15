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
        "Configuration": (
            (18501, 8, 28, "primitive:double", float.fromhex("0x0.0p+0")),
            (18509, 8, 41, "primitive:double", float.fromhex("0x0.0p+0")),
            (21163, 8, 28, "primitive:double", float.fromhex("0x1.c666666666666p+2")),
            (21171, 8, 41, "primitive:double", float.fromhex("0x1.c666666666666p+2")),
            (21484, 8, 28, "primitive:double", float.fromhex("-0x1.b333333333333p+1")),
            (21492, 8, 41, "primitive:double", float.fromhex("0x1.8666666666666p+2")),
            (21805, 8, 28, "primitive:double", float.fromhex("-0x1.2666666666666p+3")),
            (21813, 8, 41, "primitive:double", float.fromhex("0x1.b333333333333p+1")),
            (24901, 8, 28, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (24909, 8, 41, "primitive:double", float.fromhex("0x0.0p+0")),
            (24925, 8, 28, "primitive:double", float.fromhex("0x0.0p+0")),
            (24933, 8, 41, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (24949, 8, 28, "primitive:double", float.fromhex("0x0.0p+0")),
            (24957, 8, 41, "primitive:double", float.fromhex("0x0.0p+0")),
        ),
    },
)
