# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Owners.Sldmodu.MoDynSurfIdArr.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (8784, 4, 4151, "primitive:long", 0),
            (8788, 4, 4164, "primitive:long", 0),
            (8977, 4, 4151, "primitive:long", 1),
            (8981, 4, 4164, "primitive:long", 0),
            (14991, 4, 4151, "primitive:long", 0),
            (14995, 4, 4164, "primitive:long", 0),
            (15035, 4, 4151, "primitive:long", 1),
            (15039, 4, 4164, "primitive:long", 0),
            (15317, 4, 4151, "primitive:long", 0),
            (15321, 4, 4164, "primitive:long", 0),
            (15361, 4, 4151, "primitive:long", 1),
            (15365, 4, 4164, "primitive:long", 0),
        ),
    },
)
