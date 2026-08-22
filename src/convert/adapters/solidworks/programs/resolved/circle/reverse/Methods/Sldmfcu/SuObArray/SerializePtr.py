# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Sldmfcu.SuObArray.SerializePtr import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (3427, 4, 100, "primitive:long", 0),
            (3431, 4, 100, "primitive:long", 0),
            (3445, 4, 100, "primitive:long", 0),
            (3471, 4, 100, "primitive:long", 0),
            (3946, 4, 100, "primitive:long", 0),
            (3950, 4, 100, "primitive:long", 0),
            (3964, 4, 100, "primitive:long", 0),
            (3990, 4, 100, "primitive:long", 0),
            (4516, 4, 100, "primitive:long", 0),
            (4520, 4, 100, "primitive:long", 0),
            (4534, 4, 100, "primitive:long", 0),
            (4560, 4, 100, "primitive:long", 0),
            (7418, 4, 100, "primitive:long", 0),
            (7569, 4, 100, "primitive:long", 0),
            (8327, 4, 100, "primitive:long", 0),
            (8331, 4, 100, "primitive:long", 0),
            (9648, 4, 100, "primitive:long", 1),
            (9656, 4, 100, "primitive:long", 0),
            (9674, 4, 100, "primitive:long", 0),
            (10439, 4, 100, "primitive:long", 0),
            (10667, 4, 100, "primitive:long", 0),
            (10818, 4, 100, "primitive:long", 0),
            (11883, 4, 100, "primitive:long", 0),
            (11887, 4, 100, "primitive:long", 0),
        ),
    },
)
