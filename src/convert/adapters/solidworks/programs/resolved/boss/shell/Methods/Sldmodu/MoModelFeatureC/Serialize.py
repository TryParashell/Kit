# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Owners.Sldmodu.MoModelFeatureC.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (2244, 4, 140, "primitive:long", 0),
            (3536, 4, 140, "primitive:long", 0),
            (4055, 4, 140, "primitive:long", 0),
            (4625, 4, 140, "primitive:long", 0),
            (5213, 4, 140, "primitive:long", 0),
            (6142, 4, 140, "primitive:long", 0),
            (8351, 4, 140, "primitive:long", 0),
            (11364, 4, 140, "primitive:long", 0),
        ),
    },
)
