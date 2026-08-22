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
            (3186, 8, 246, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (3194, 8, 259, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (3202, 8, 272, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (3210, 8, 285, "primitive:double", float.fromhex("0x1.4000000000000p-2")),
            (3218, 8, 479, "primitive:double", float.fromhex("0x0.0p+0")),
            (3226, 8, 492, "primitive:double", float.fromhex("0x0.0p+0")),
            (3234, 4, 521, "primitive:int", 0),
            (3238, 4, 653, "primitive:int", 1),
            (3242, 4, 666, "primitive:int", 0),
            (3246, 4, 679, "primitive:int", 1),
            (3250, 4, 692, "primitive:int", 1),
            (3254, 4, 705, "primitive:int", 1),
            (3262, 4, 763, "primitive:int", 1),
            (3266, 4, 792, "primitive:int", 0),
            (3274, 4, 924, "primitive:int", 0),
        ),
    },
)
