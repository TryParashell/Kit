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
            (5619, 4, 587, "primitive:int", 4),
            (5623, 8, 600, "primitive:double", float.fromhex("0x1.0a569b17481b2p-10")),
            (5631, 8, 613, "primitive:double", float.fromhex("0x1.b0ccbc05d52c1p-9")),
            (5639, 8, 626, "primitive:double", float.fromhex("0x1.a027525460aa6p-8")),
            (5647, 8, 639, "primitive:double", float.fromhex("0x1.0624dd2f1a9fcp-10")),
            (5655, 8, 652, "primitive:double", float.fromhex("0x1.0624dd2f1a9fcp-10")),
            (5663, 8, 665, "primitive:double", float.fromhex("0x1.47ae147ae147bp-8")),
            (5671, 8, 678, "primitive:double", float.fromhex("0x1.47ae147ae147bp-7")),
            (5679, 8, 691, "primitive:double", float.fromhex("0x1.a027525460aa6p-9")),
            (5687, 8, 704, "primitive:double", float.fromhex("0x1.8f81e8a2ec28bp-10")),
            (5695, 8, 717, "primitive:double", float.fromhex("0x1.a027525460aa6p-8")),
            (5703, 8, 730, "primitive:double", float.fromhex("-0x1.9000000000000p+4")),
            (5711, 4, 743, "primitive:int", 2),
            (5715, 4, 756, "primitive:int", 0),
            (5719, 4, 769, "primitive:int", 0),
            (5723, 4, 782, "primitive:int", 20),
            (5727, 4, 795, "primitive:int", 1),
            (5731, 8, 808, "primitive:double", float.fromhex("0x0.0p+0")),
            (5739, 8, 824, "primitive:double", float.fromhex("0x0.0p+0")),
            (5747, 4, 840, "primitive:int", 0),
            (5751, 4, 856, "primitive:int", 0),
            (5755, 8, 872, "primitive:double", float.fromhex("0x1.47ae147ae147bp-7")),
            (5763, 8, 888, "primitive:double", float.fromhex("0x1.89374bc6a7efap-8")),
            (5771, 8, 904, "primitive:double", float.fromhex("0x1.0c152382d7370p-2")),
            (5779, 4, 920, "primitive:int", 8368),
            (5783, 4, 1120, "primitive:int", 1),
            (5787, 8, 1136, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (5795, 4, 1150, "primitive:int", 0),
            (5799, 4, 1193, "primitive:int", 1),
            (5803, 4, 1226, "primitive:int", 1),
            (5807, 4, 1259, "primitive:int", 1),
            (5811, 4, 1292, "primitive:int", 1),
            (5815, 4, 1308, "primitive:int", 1),
            (5819, 4, 1341, "primitive:int", 1),
        ),
    },
)
