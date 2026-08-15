# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Sldmfcu.MoDimDefsC.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "Contents/Config-0": (
            (4297, 4, 587, "primitive:int", 4),
            (4301, 8, 600, "primitive:double", float.fromhex("0x1.0a569b17481b2p-10")),
            (4309, 8, 613, "primitive:double", float.fromhex("0x1.b0ccbc05d52c1p-9")),
            (4317, 8, 626, "primitive:double", float.fromhex("0x1.a027525460aa6p-8")),
            (4325, 8, 639, "primitive:double", float.fromhex("0x1.0624dd2f1a9fcp-10")),
            (4333, 8, 652, "primitive:double", float.fromhex("0x1.0624dd2f1a9fcp-10")),
            (4341, 8, 665, "primitive:double", float.fromhex("0x1.47ae147ae147bp-8")),
            (4349, 8, 678, "primitive:double", float.fromhex("0x1.47ae147ae147bp-7")),
            (4357, 8, 691, "primitive:double", float.fromhex("0x1.a027525460aa6p-9")),
            (4365, 8, 704, "primitive:double", float.fromhex("0x1.8f81e8a2ec28bp-10")),
            (4373, 8, 717, "primitive:double", float.fromhex("0x1.a027525460aa6p-8")),
            (4381, 8, 730, "primitive:double", float.fromhex("-0x1.9000000000000p+4")),
            (4389, 4, 743, "primitive:int", 2),
            (4393, 4, 756, "primitive:int", 0),
            (4397, 4, 769, "primitive:int", 0),
            (4401, 4, 782, "primitive:int", 20),
            (4405, 4, 795, "primitive:int", 1),
            (4409, 8, 808, "primitive:double", float.fromhex("0x0.0p+0")),
            (4417, 8, 824, "primitive:double", float.fromhex("0x0.0p+0")),
            (4425, 4, 840, "primitive:int", 0),
            (4429, 4, 856, "primitive:int", 0),
            (4433, 8, 872, "primitive:double", float.fromhex("0x1.47ae147ae147bp-7")),
            (4441, 8, 888, "primitive:double", float.fromhex("0x1.89374bc6a7efap-8")),
            (4449, 8, 904, "primitive:double", float.fromhex("0x1.0c152382d7370p-2")),
            (4457, 4, 920, "primitive:int", 8368),
            (4461, 4, 1120, "primitive:int", 1),
            (4465, 8, 1136, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (4473, 4, 1150, "primitive:int", 0),
            (4477, 4, 1193, "primitive:int", 1),
            (4481, 4, 1226, "primitive:int", 1),
            (4485, 4, 1259, "primitive:int", 1),
            (4489, 4, 1292, "primitive:int", 1),
            (4493, 4, 1308, "primitive:int", 1),
            (4497, 4, 1341, "primitive:int", 1),
        ),
    },
)
