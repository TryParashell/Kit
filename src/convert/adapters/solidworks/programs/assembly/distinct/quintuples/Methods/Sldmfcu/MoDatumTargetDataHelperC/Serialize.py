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
            (20257, 4, 413, "primitive:int", 0),
            (20261, 4, 426, "primitive:int", 0),
            (20265, 8, 439, "primitive:double", float.fromhex("0x1.eb851eb851eb8p-6")),
            (20273, 8, 452, "primitive:double", float.fromhex("0x1.eb851eb851eb8p-6")),
            (20281, 4, 465, "primitive:int", 0),
            (20285, 1, 479, "primitive:uchar", 0),
            (20286, 1, 501, "primitive:uchar", 1),
            (20287, 1, 523, "primitive:uchar", 0),
            (20288, 1, 545, "primitive:uchar", 0),
            (20289, 1, 567, "primitive:uchar", 1),
            (20290, 4, 605, "primitive:int", 0),
            (20294, 8, 618, "primitive:double", float.fromhex("0x0.0p+0")),
            (20302, 4, 631, "primitive:int", -1),
            (20306, 1, 645, "primitive:uchar", 0),
            (20307, 1, 667, "primitive:uchar", 0),
            (20308, 1, 692, "primitive:uchar", 0),
            (20325, 8, 716, "primitive:double", float.fromhex("0x0.0p+0")),
        ),
    },
)
