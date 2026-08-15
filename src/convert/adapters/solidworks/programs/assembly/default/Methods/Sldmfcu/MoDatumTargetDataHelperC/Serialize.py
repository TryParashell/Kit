# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Owners.Sldmfcu.MoDatumTargetDataHelperC.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram = (
    KOwnerSites,
    {
        "Contents/Config-0": (
            (18341, 4, 413, "primitive:int", 0),
            (18345, 4, 426, "primitive:int", 0),
            (18349, 8, 439, "primitive:double", float.fromhex("0x1.eb851eb851eb8p-6")),
            (18357, 8, 452, "primitive:double", float.fromhex("0x1.eb851eb851eb8p-6")),
            (18365, 4, 465, "primitive:int", 0),
            (18369, 1, 479, "primitive:uchar", 0),
            (18370, 1, 501, "primitive:uchar", 1),
            (18371, 1, 523, "primitive:uchar", 0),
            (18372, 1, 545, "primitive:uchar", 0),
            (18373, 1, 567, "primitive:uchar", 1),
            (18374, 4, 605, "primitive:int", 0),
            (18378, 8, 618, "primitive:double", float.fromhex("0x0.0p+0")),
            (18386, 4, 631, "primitive:int", -1),
            (18390, 1, 645, "primitive:uchar", 0),
            (18391, 1, 667, "primitive:uchar", 0),
            (18392, 1, 692, "primitive:uchar", 0),
            (18409, 8, 716, "primitive:double", float.fromhex("0x0.0p+0")),
        ),
    },
)
