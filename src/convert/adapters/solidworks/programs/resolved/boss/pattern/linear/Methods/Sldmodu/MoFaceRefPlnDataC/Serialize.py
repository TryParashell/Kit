# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Owners.Sldmodu.MoFaceRefPlnDataC.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (9103, 4, 7121, "primitive:long", 1),
            (9131, 8, 7292, "primitive:double", float.fromhex("0x1.eb851eb851eb9p-7")),
            (
                19041,
                8,
                5803,
                "primitive:double",
                float.fromhex("-0x1.0000000000000p+0"),
            ),
            (19049, 1, 5864, "primitive:uchar", 0),
        ),
    },
)
