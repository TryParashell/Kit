# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Sldmfcu.MoDatumTargetDataHelperC.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "Configuration": (
            (18449, 4, 413, "primitive:int", 0),
            (18453, 4, 426, "primitive:int", 0),
            (18457, 8, 439, "primitive:double", float.fromhex("0x1.eb851eb851eb8p-6")),
            (18465, 8, 452, "primitive:double", float.fromhex("0x1.eb851eb851eb8p-6")),
            (18473, 4, 465, "primitive:int", 0),
            (18477, 1, 479, "primitive:uchar", 0),
            (18478, 1, 501, "primitive:uchar", 1),
            (18479, 1, 523, "primitive:uchar", 0),
            (18480, 1, 545, "primitive:uchar", 0),
            (18481, 1, 567, "primitive:uchar", 1),
            (18482, 4, 605, "primitive:int", 0),
            (18486, 8, 618, "primitive:double", float.fromhex("0x0.0p+0")),
            (18494, 4, 631, "primitive:int", -1),
            (18498, 1, 645, "primitive:uchar", 0),
            (18499, 1, 667, "primitive:uchar", 0),
            (18500, 1, 692, "primitive:uchar", 0),
            (18517, 8, 716, "primitive:double", float.fromhex("0x0.0p+0")),
        ),
    },
)
