# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Owners.Slduiu.PVDocSpecificOptionsDataC.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram = (
    KOwnerSites,
    {
        "Contents/Definition": (
            (3682, 4, 245, "primitive:long", 0),
            (3686, 4, 258, "primitive:long", 100),
            (3690, 4, 271, "primitive:long", 5),
            (3694, 4, 284, "primitive:long", 0),
            (3698, 4, 297, "primitive:long", 0),
            (3702, 4, 310, "primitive:long", 1),
            (3706, 4, 323, "primitive:ulong", 0),
            (3710, 4, 387, "primitive:long", 0),
            (3714, 4, 400, "primitive:long", 0),
            (3718, 4, 456, "primitive:long", 1),
            (3722, 4, 469, "primitive:long", 0),
            (3726, 4, 482, "primitive:long", 0),
        ),
    },
)
