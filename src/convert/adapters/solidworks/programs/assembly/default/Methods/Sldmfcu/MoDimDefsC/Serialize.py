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
            (3703, 4, 587, "primitive:int", 4),
            (3707, 8, 600, "primitive:double", float.fromhex("0x1.0a569b17481b2p-10")),
            (3715, 8, 613, "primitive:double", float.fromhex("0x1.b0ccbc05d52c1p-9")),
            (3723, 8, 626, "primitive:double", float.fromhex("0x1.a027525460aa6p-8")),
            (3731, 8, 639, "primitive:double", float.fromhex("0x1.0624dd2f1a9fcp-10")),
            (3739, 8, 652, "primitive:double", float.fromhex("0x1.0624dd2f1a9fcp-10")),
            (3747, 8, 665, "primitive:double", float.fromhex("0x1.47ae147ae147bp-8")),
            (3755, 8, 678, "primitive:double", float.fromhex("0x1.47ae147ae147bp-7")),
            (3763, 8, 691, "primitive:double", float.fromhex("0x1.a027525460aa6p-9")),
            (3771, 8, 704, "primitive:double", float.fromhex("0x1.8f81e8a2ec28bp-10")),
            (3779, 8, 717, "primitive:double", float.fromhex("0x1.a027525460aa6p-8")),
            (3787, 8, 730, "primitive:double", float.fromhex("-0x1.9000000000000p+4")),
            (3795, 4, 743, "primitive:int", 2),
            (3799, 4, 756, "primitive:int", 0),
            (3803, 4, 769, "primitive:int", 0),
            (3807, 4, 782, "primitive:int", 20),
            (3811, 4, 795, "primitive:int", 1),
            (3815, 8, 808, "primitive:double", float.fromhex("0x0.0p+0")),
            (3823, 8, 824, "primitive:double", float.fromhex("0x0.0p+0")),
            (3831, 4, 840, "primitive:int", 0),
            (3835, 4, 856, "primitive:int", 0),
            (3839, 8, 872, "primitive:double", float.fromhex("0x1.47ae147ae147bp-7")),
            (3847, 8, 888, "primitive:double", float.fromhex("0x1.89374bc6a7efap-8")),
            (3855, 8, 904, "primitive:double", float.fromhex("0x1.0c152382d7370p-2")),
            (3863, 4, 920, "primitive:int", 8368),
            (3867, 4, 1120, "primitive:int", 1),
            (3871, 8, 1136, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (3879, 4, 1150, "primitive:int", 0),
            (3883, 4, 1193, "primitive:int", 1),
            (3887, 4, 1226, "primitive:int", 1),
            (3891, 4, 1259, "primitive:int", 1),
            (3895, 4, 1292, "primitive:int", 1),
            (3899, 4, 1308, "primitive:int", 1),
            (3903, 4, 1341, "primitive:int", 1),
        ),
    },
)
