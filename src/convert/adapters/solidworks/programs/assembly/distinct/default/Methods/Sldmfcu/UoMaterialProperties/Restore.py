# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Sldmfcu.UoMaterialProperties.Restore import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "Contents/Config-0": (
            (1496, 8, 246, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (1504, 8, 259, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (1512, 8, 272, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (1520, 8, 285, "primitive:double", float.fromhex("0x1.4000000000000p-2")),
            (1528, 8, 479, "primitive:double", float.fromhex("0x0.0p+0")),
            (1536, 8, 492, "primitive:double", float.fromhex("0x0.0p+0")),
            (1544, 4, 521, "primitive:int", 0),
            (1548, 4, 653, "primitive:int", 1),
            (1552, 4, 666, "primitive:int", 0),
            (1556, 4, 679, "primitive:int", 1),
            (1560, 4, 692, "primitive:int", 1),
            (1564, 4, 705, "primitive:int", 1),
            (1572, 4, 763, "primitive:int", 1),
            (1576, 4, 792, "primitive:int", 0),
            (1584, 4, 924, "primitive:int", 0),
        ),
    },
)
