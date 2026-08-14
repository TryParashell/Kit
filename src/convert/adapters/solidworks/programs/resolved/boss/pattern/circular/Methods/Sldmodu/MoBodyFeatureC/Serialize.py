# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Owners.Sldmodu.MoBodyFeatureC.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (9716, 4, 752, "primitive:long", 0),
            (12389, 4, 752, "primitive:long", 0),
            (17876, 1, 3992, "primitive:uchar", 0),
            (19535, 1, 4152, "primitive:uchar", 1),
            (19538, 1, 4239, "primitive:uchar", 0),
            (19539, 1, 4264, "primitive:uchar", 0),
            (19540, 1, 4289, "primitive:uchar", 1),
            (19541, 1, 4314, "primitive:uchar", 0),
            (19542, 1, 4339, "primitive:uchar", 0),
            (19543, 4, 4522, "primitive:long", 0),
            (19547, 4, 4884, "primitive:long", 0),
            (
                19591,
                8,
                5154,
                "primitive:double",
                float.fromhex("-0x1.0000000000000p+0"),
            ),
        ),
    },
)
