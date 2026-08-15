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
            (9266, 4, 100, "primitive:long", 1),
            (9274, 4, 100, "primitive:long", 0),
            (9292, 4, 100, "primitive:long", 0),
            (9865, 4, 100, "primitive:long", 0),
            (10397, 4, 100, "primitive:long", 0),
            (10548, 4, 100, "primitive:long", 0),
            (11573, 4, 100, "primitive:long", 0),
            (11577, 4, 100, "primitive:long", 0),
        ),
    },
)
