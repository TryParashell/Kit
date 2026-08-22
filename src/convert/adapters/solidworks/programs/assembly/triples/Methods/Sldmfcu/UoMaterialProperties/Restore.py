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
            (2122, 8, 246, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (2130, 8, 259, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (2138, 8, 272, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (2146, 8, 285, "primitive:double", float.fromhex("0x1.4000000000000p-2")),
            (2154, 8, 479, "primitive:double", float.fromhex("0x0.0p+0")),
            (2162, 8, 492, "primitive:double", float.fromhex("0x0.0p+0")),
            (2170, 4, 521, "primitive:int", 0),
            (2174, 4, 653, "primitive:int", 1),
            (2178, 4, 666, "primitive:int", 0),
            (2182, 4, 679, "primitive:int", 1),
            (2186, 4, 692, "primitive:int", 1),
            (2190, 4, 705, "primitive:int", 1),
            (2198, 4, 763, "primitive:int", 1),
            (2202, 4, 792, "primitive:int", 0),
            (2210, 4, 924, "primitive:int", 0),
        ),
    },
)
