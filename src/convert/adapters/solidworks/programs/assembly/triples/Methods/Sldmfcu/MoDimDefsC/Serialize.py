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
            (5015, 4, 587, "primitive:int", 4),
            (5019, 8, 600, "primitive:double", float.fromhex("0x1.0a569b17481b2p-10")),
            (5027, 8, 613, "primitive:double", float.fromhex("0x1.b0ccbc05d52c1p-9")),
            (5035, 8, 626, "primitive:double", float.fromhex("0x1.a027525460aa6p-8")),
            (5043, 8, 639, "primitive:double", float.fromhex("0x1.0624dd2f1a9fcp-10")),
            (5051, 8, 652, "primitive:double", float.fromhex("0x1.0624dd2f1a9fcp-10")),
            (5059, 8, 665, "primitive:double", float.fromhex("0x1.47ae147ae147bp-8")),
            (5067, 8, 678, "primitive:double", float.fromhex("0x1.47ae147ae147bp-7")),
            (5075, 8, 691, "primitive:double", float.fromhex("0x1.a027525460aa6p-9")),
            (5083, 8, 704, "primitive:double", float.fromhex("0x1.8f81e8a2ec28bp-10")),
            (5091, 8, 717, "primitive:double", float.fromhex("0x1.a027525460aa6p-8")),
            (5099, 8, 730, "primitive:double", float.fromhex("-0x1.9000000000000p+4")),
            (5107, 4, 743, "primitive:int", 2),
            (5111, 4, 756, "primitive:int", 0),
            (5115, 4, 769, "primitive:int", 0),
            (5119, 4, 782, "primitive:int", 20),
            (5123, 4, 795, "primitive:int", 1),
            (5127, 8, 808, "primitive:double", float.fromhex("0x0.0p+0")),
            (5135, 8, 824, "primitive:double", float.fromhex("0x0.0p+0")),
            (5143, 4, 840, "primitive:int", 0),
            (5147, 4, 856, "primitive:int", 0),
            (5151, 8, 872, "primitive:double", float.fromhex("0x1.47ae147ae147bp-7")),
            (5159, 8, 888, "primitive:double", float.fromhex("0x1.89374bc6a7efap-8")),
            (5167, 8, 904, "primitive:double", float.fromhex("0x1.0c152382d7370p-2")),
            (5175, 4, 920, "primitive:int", 8368),
            (5179, 4, 1120, "primitive:int", 1),
            (5183, 8, 1136, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (5191, 4, 1150, "primitive:int", 0),
            (5195, 4, 1193, "primitive:int", 1),
            (5199, 4, 1226, "primitive:int", 1),
            (5203, 4, 1259, "primitive:int", 1),
            (5207, 4, 1292, "primitive:int", 1),
            (5211, 4, 1308, "primitive:int", 1),
            (5215, 4, 1341, "primitive:int", 1),
        ),
    },
)
