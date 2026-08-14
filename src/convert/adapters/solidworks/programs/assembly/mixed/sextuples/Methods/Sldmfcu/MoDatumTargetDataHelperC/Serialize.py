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
            (20119, 4, 413, "primitive:int", 0),
            (20123, 4, 426, "primitive:int", 0),
            (20127, 8, 439, "primitive:double", float.fromhex("0x1.eb851eb851eb8p-6")),
            (20135, 8, 452, "primitive:double", float.fromhex("0x1.eb851eb851eb8p-6")),
            (20143, 4, 465, "primitive:int", 0),
            (20147, 1, 479, "primitive:uchar", 0),
            (20148, 1, 501, "primitive:uchar", 1),
            (20149, 1, 523, "primitive:uchar", 0),
            (20150, 1, 545, "primitive:uchar", 0),
            (20151, 1, 567, "primitive:uchar", 1),
            (20152, 4, 605, "primitive:int", 0),
            (20156, 8, 618, "primitive:double", float.fromhex("0x0.0p+0")),
            (20164, 4, 631, "primitive:int", -1),
            (20168, 1, 645, "primitive:uchar", 0),
            (20169, 1, 667, "primitive:uchar", 0),
            (20170, 1, 692, "primitive:uchar", 0),
            (20187, 8, 716, "primitive:double", float.fromhex("0x0.0p+0")),
        ),
    },
)
