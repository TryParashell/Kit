# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Owners.Sldmfcu.MoCenterMarkSymDataHelperC.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram = (
    KOwnerSites,
    {
        "Contents/Config-0": (
            (19888, 1, 297, "primitive:uchar", 0),
            (19889, 8, 317, "primitive:double", float.fromhex("0x0.0p+0")),
            (19897, 1, 330, "primitive:uchar", 1),
            (19898, 8, 350, "primitive:double", float.fromhex("0x0.0p+0")),
            (19906, 1, 363, "primitive:uchar", 0),
            (19907, 1, 383, "primitive:uchar", 0),
            (19908, 1, 403, "primitive:uchar", 0),
            (19909, 1, 423, "primitive:uchar", 0),
            (19910, 1, 443, "primitive:uchar", 0),
            (19911, 1, 463, "primitive:uchar", 0),
            (20051, 4, 534, "primitive:int", 0),
            (20055, 1, 563, "primitive:uchar", 1),
            (20056, 1, 583, "primitive:uchar", 1),
            (20057, 1, 603, "primitive:uchar", 1),
            (20058, 1, 639, "primitive:uchar", 0),
            (20059, 8, 675, "primitive:double", float.fromhex("0x0.0p+0")),
        ),
    },
)
