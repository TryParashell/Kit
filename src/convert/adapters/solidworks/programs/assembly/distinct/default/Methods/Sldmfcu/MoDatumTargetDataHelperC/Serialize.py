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
            (19027, 4, 413, "primitive:int", 0),
            (19031, 4, 426, "primitive:int", 0),
            (19035, 8, 439, "primitive:double", float.fromhex("0x1.eb851eb851eb8p-6")),
            (19043, 8, 452, "primitive:double", float.fromhex("0x1.eb851eb851eb8p-6")),
            (19051, 4, 465, "primitive:int", 0),
            (19055, 1, 479, "primitive:uchar", 0),
            (19056, 1, 501, "primitive:uchar", 1),
            (19057, 1, 523, "primitive:uchar", 0),
            (19058, 1, 545, "primitive:uchar", 0),
            (19059, 1, 567, "primitive:uchar", 1),
            (19060, 4, 605, "primitive:int", 0),
            (19064, 8, 618, "primitive:double", float.fromhex("0x0.0p+0")),
            (19072, 4, 631, "primitive:int", -1),
            (19076, 1, 645, "primitive:uchar", 0),
            (19077, 1, 667, "primitive:uchar", 0),
            (19078, 1, 692, "primitive:uchar", 0),
            (19095, 8, 716, "primitive:double", float.fromhex("0x0.0p+0")),
        ),
    },
)
