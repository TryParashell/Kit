# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Sldmgu.MgMatrixC.Restore import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (4141, 8, 90, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (4149, 8, 103, "primitive:double", float.fromhex("0x0.0p+0")),
            (4157, 8, 116, "primitive:double", float.fromhex("0x0.0p+0")),
            (4165, 8, 130, "primitive:double", float.fromhex("0x0.0p+0")),
            (4173, 8, 144, "primitive:double", float.fromhex("0x0.0p+0")),
            (4181, 8, 158, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (4189, 8, 172, "primitive:double", float.fromhex("0x0.0p+0")),
            (4197, 8, 186, "primitive:double", float.fromhex("-0x1.0000000000000p+0")),
            (4205, 8, 200, "primitive:double", float.fromhex("0x0.0p+0")),
            (4711, 8, 90, "primitive:double", float.fromhex("-0x0.0p+0")),
            (4719, 8, 103, "primitive:double", float.fromhex("0x0.0p+0")),
            (4727, 8, 116, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (4735, 8, 130, "primitive:double", float.fromhex("-0x0.0p+0")),
            (4743, 8, 144, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (4751, 8, 158, "primitive:double", float.fromhex("0x0.0p+0")),
            (4759, 8, 172, "primitive:double", float.fromhex("-0x1.0000000000000p+0")),
            (4767, 8, 186, "primitive:double", float.fromhex("0x0.0p+0")),
            (4775, 8, 200, "primitive:double", float.fromhex("0x0.0p+0")),
            (11318, 8, 90, "primitive:double", float.fromhex("-0x1.0000000000000p+0")),
            (11326, 8, 103, "primitive:double", float.fromhex("-0x0.0p+0")),
            (11334, 8, 116, "primitive:double", float.fromhex("0x0.0p+0")),
            (11342, 8, 130, "primitive:double", float.fromhex("0x0.0p+0")),
            (11350, 8, 144, "primitive:double", float.fromhex("-0x0.0p+0")),
            (11358, 8, 158, "primitive:double", float.fromhex("-0x1.0000000000000p+0")),
            (11366, 8, 172, "primitive:double", float.fromhex("0x0.0p+0")),
            (11374, 8, 186, "primitive:double", float.fromhex("-0x1.0000000000000p+0")),
            (11382, 8, 200, "primitive:double", float.fromhex("0x0.0p+0")),
        ),
    },
)
