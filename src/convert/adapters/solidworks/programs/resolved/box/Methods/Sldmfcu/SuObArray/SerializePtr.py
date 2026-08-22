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
            (8469, 4, 100, "primitive:long", 0),
            (8620, 4, 100, "primitive:long", 0),
            (9357, 4, 100, "primitive:long", 0),
            (9361, 4, 100, "primitive:long", 0),
            (9958, 4, 100, "primitive:long", 0),
            (10109, 4, 100, "primitive:long", 0),
            (10822, 4, 100, "primitive:long", 0),
            (10826, 4, 100, "primitive:long", 0),
            (12095, 4, 100, "primitive:long", 1),
            (12103, 4, 100, "primitive:long", 0),
            (12121, 4, 100, "primitive:long", 0),
            (12806, 4, 100, "primitive:long", 0),
            (13008, 4, 100, "primitive:long", 0),
            (13159, 4, 100, "primitive:long", 0),
            (14224, 4, 100, "primitive:long", 0),
            (14228, 4, 100, "primitive:long", 0),
        ),
    },
)
