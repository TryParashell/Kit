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
            (3546, 4, 100, "primitive:long", 0),
            (3550, 4, 100, "primitive:long", 0),
            (3564, 4, 100, "primitive:long", 0),
            (3590, 4, 100, "primitive:long", 0),
            (4065, 4, 100, "primitive:long", 0),
            (4069, 4, 100, "primitive:long", 0),
            (4083, 4, 100, "primitive:long", 0),
            (4109, 4, 100, "primitive:long", 0),
            (4635, 4, 100, "primitive:long", 0),
            (4639, 4, 100, "primitive:long", 0),
            (4653, 4, 100, "primitive:long", 0),
            (4679, 4, 100, "primitive:long", 0),
            (8361, 4, 100, "primitive:long", 1),
            (8369, 4, 100, "primitive:long", 0),
            (8387, 4, 100, "primitive:long", 0),
            (9072, 4, 100, "primitive:long", 0),
            (9300, 4, 100, "primitive:long", 0),
            (9451, 4, 100, "primitive:long", 0),
            (10539, 4, 100, "primitive:long", 0),
            (10543, 4, 100, "primitive:long", 0),
            (11378, 4, 100, "primitive:long", 0),
            (11382, 4, 100, "primitive:long", 0),
            (11396, 4, 100, "primitive:long", 0),
            (11422, 4, 100, "primitive:long", 0),
            (12007, 4, 100, "primitive:long", 0),
            (12158, 4, 100, "primitive:long", 0),
            (13169, 4, 100, "primitive:long", 0),
            (13173, 4, 100, "primitive:long", 0),
            (13773, 4, 100, "primitive:long", 0),
            (13924, 4, 100, "primitive:long", 0),
            (14925, 4, 100, "primitive:long", 0),
            (14929, 4, 100, "primitive:long", 0),
        ),
    },
)
