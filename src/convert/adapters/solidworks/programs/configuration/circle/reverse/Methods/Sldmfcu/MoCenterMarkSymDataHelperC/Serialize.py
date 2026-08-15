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
        "Configuration": (
            (18110, 1, 297, "primitive:uchar", 0),
            (18111, 8, 317, "primitive:double", float.fromhex("0x0.0p+0")),
            (18119, 1, 330, "primitive:uchar", 1),
            (18120, 8, 350, "primitive:double", float.fromhex("0x0.0p+0")),
            (18128, 1, 363, "primitive:uchar", 0),
            (18129, 1, 383, "primitive:uchar", 0),
            (18130, 1, 403, "primitive:uchar", 0),
            (18131, 1, 423, "primitive:uchar", 0),
            (18132, 1, 443, "primitive:uchar", 0),
            (18133, 1, 463, "primitive:uchar", 0),
            (18273, 4, 534, "primitive:int", 0),
            (18277, 1, 563, "primitive:uchar", 1),
            (18278, 1, 583, "primitive:uchar", 1),
            (18279, 1, 603, "primitive:uchar", 1),
            (18280, 1, 639, "primitive:uchar", 0),
            (18281, 8, 675, "primitive:double", float.fromhex("0x0.0p+0")),
        ),
    },
)
