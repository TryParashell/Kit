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
        "Contents/Config-0": (
            (19653, 4, 413, "primitive:int", 0),
            (19657, 4, 426, "primitive:int", 0),
            (19661, 8, 439, "primitive:double", float.fromhex("0x1.eb851eb851eb8p-6")),
            (19669, 8, 452, "primitive:double", float.fromhex("0x1.eb851eb851eb8p-6")),
            (19677, 4, 465, "primitive:int", 0),
            (19681, 1, 479, "primitive:uchar", 0),
            (19682, 1, 501, "primitive:uchar", 1),
            (19683, 1, 523, "primitive:uchar", 0),
            (19684, 1, 545, "primitive:uchar", 0),
            (19685, 1, 567, "primitive:uchar", 1),
            (19686, 4, 605, "primitive:int", 0),
            (19690, 8, 618, "primitive:double", float.fromhex("0x0.0p+0")),
            (19698, 4, 631, "primitive:int", -1),
            (19702, 1, 645, "primitive:uchar", 0),
            (19703, 1, 667, "primitive:uchar", 0),
            (19704, 1, 692, "primitive:uchar", 0),
            (19721, 8, 716, "primitive:double", float.fromhex("0x0.0p+0")),
        ),
    },
)
