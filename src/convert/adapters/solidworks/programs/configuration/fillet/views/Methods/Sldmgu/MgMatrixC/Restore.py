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
        "AnnotationManager": (
            (37, 8, 90, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (45, 8, 103, "primitive:double", float.fromhex("0x0.0p+0")),
            (53, 8, 116, "primitive:double", float.fromhex("0x0.0p+0")),
            (61, 8, 130, "primitive:double", float.fromhex("0x0.0p+0")),
            (69, 8, 144, "primitive:double", float.fromhex("0x0.0p+0")),
            (77, 8, 158, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (85, 8, 172, "primitive:double", float.fromhex("-0x0.0p+0")),
            (93, 8, 186, "primitive:double", float.fromhex("-0x1.0000000000000p+0")),
            (101, 8, 200, "primitive:double", float.fromhex("-0x0.0p+0")),
            (295, 8, 90, "primitive:double", float.fromhex("-0x1.0000000000000p+0")),
            (303, 8, 103, "primitive:double", float.fromhex("-0x0.0p+0")),
            (311, 8, 116, "primitive:double", float.fromhex("-0x0.0p+0")),
            (319, 8, 130, "primitive:double", float.fromhex("0x0.0p+0")),
            (327, 8, 144, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (335, 8, 158, "primitive:double", float.fromhex("0x0.0p+0")),
            (343, 8, 172, "primitive:double", float.fromhex("-0x0.0p+0")),
            (351, 8, 186, "primitive:double", float.fromhex("-0x0.0p+0")),
            (359, 8, 200, "primitive:double", float.fromhex("-0x1.0000000000000p+0")),
        ),
    },
)
