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
            (1404, 8, 246, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (1412, 8, 259, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (1420, 8, 272, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (1428, 8, 285, "primitive:double", float.fromhex("0x1.4000000000000p-2")),
            (1436, 8, 479, "primitive:double", float.fromhex("0x0.0p+0")),
            (1444, 8, 492, "primitive:double", float.fromhex("0x0.0p+0")),
            (1452, 4, 521, "primitive:int", 0),
            (1456, 4, 653, "primitive:int", 1),
            (1460, 4, 666, "primitive:int", 0),
            (1464, 4, 679, "primitive:int", 1),
            (1468, 4, 692, "primitive:int", 1),
            (1472, 4, 705, "primitive:int", 1),
            (1480, 4, 763, "primitive:int", 1),
            (1484, 4, 792, "primitive:int", 0),
            (1492, 4, 924, "primitive:int", 0),
        ),
    },
)
