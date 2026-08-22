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
        "Contents/Config-0": (
            (11469, 4, 175, "primitive:int", 7),
            (11473, 4, 196, "primitive:int", 9),
            (11477, 4, 217, "primitive:int", 11),
            (11481, 4, 257, "primitive:int", 2),
            (11485, 8, 277, "primitive:double", float.fromhex("0x1.4cec41dd1a21fp-7")),
            (11493, 4, 291, "primitive:int", 1),
            (11497, 8, 333, "primitive:double", float.fromhex("0x0.0p+0")),
            (11505, 4, 409, "primitive:int", 0),
        ),
    },
)
