# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Sldmfcu.MoViewLocationLabelDefsC.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "Configuration": (
            (10891, 4, 175, "primitive:int", 7),
            (10895, 4, 196, "primitive:int", 9),
            (10899, 4, 217, "primitive:int", 11),
            (10903, 4, 257, "primitive:int", 2),
            (10907, 8, 277, "primitive:double", float.fromhex("0x1.4cec41dd1a21fp-7")),
            (10915, 4, 291, "primitive:int", 1),
            (10919, 8, 333, "primitive:double", float.fromhex("0x0.0p+0")),
            (10927, 4, 409, "primitive:int", 0),
        ),
    },
)
