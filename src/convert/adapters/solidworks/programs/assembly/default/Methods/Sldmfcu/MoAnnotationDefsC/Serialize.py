# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Sldmfcu.MoAnnotationDefsC.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "Contents/Config-0": (
            (8867, 4, 222, "primitive:int", 4),
            (8871, 8, 235, "primitive:double", float.fromhex("0x1.a027525460aa6p-8")),
            (8879, 4, 248, "primitive:int", 0),
            (8883, 4, 261, "primitive:int", 0),
            (8887, 4, 274, "primitive:int", 3),
            (8891, 4, 287, "primitive:int", 0),
            (8895, 4, 324, "primitive:int", 0),
            (8899, 4, 337, "primitive:int", 0),
            (8903, 4, 374, "primitive:int", 1),
            (8907, 4, 387, "primitive:int", 1),
            (8911, 4, 449, "primitive:int", 0),
            (8915, 4, 488, "primitive:int", 1),
            (10621, 8, 742, "primitive:double", float.fromhex("0x1.4cec41dd1a21fp-8")),
        ),
    },
)
