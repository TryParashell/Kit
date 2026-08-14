# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Owners.Sldmodu.MoPTSRefPlnDataC.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (3676, 4, 13613, "primitive:long", 5),
            (3680, 4, 13784, "primitive:long", 0),
            (3686, 4, 13933, "primitive:long", 0),
            (4195, 4, 13613, "primitive:long", 5),
            (4199, 4, 13784, "primitive:long", 0),
            (4205, 4, 13933, "primitive:long", 0),
            (4765, 4, 13613, "primitive:long", 5),
            (4769, 4, 13784, "primitive:long", 0),
            (4775, 4, 13933, "primitive:long", 0),
            (9032, 4, 3177, "primitive:long", 0),
            (9036, 4, 3190, "primitive:long", 0),
            (9046, 4, 3307, "primitive:long", 0),
        ),
    },
)
