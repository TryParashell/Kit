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
            (3903, 4, 100, "primitive:long", 0),
            (3907, 4, 100, "primitive:long", 0),
            (3921, 4, 100, "primitive:long", 0),
            (3947, 4, 100, "primitive:long", 0),
            (4422, 4, 100, "primitive:long", 0),
            (4426, 4, 100, "primitive:long", 0),
            (4440, 4, 100, "primitive:long", 0),
            (4466, 4, 100, "primitive:long", 0),
            (4992, 4, 100, "primitive:long", 0),
            (4996, 4, 100, "primitive:long", 0),
            (5010, 4, 100, "primitive:long", 0),
            (5036, 4, 100, "primitive:long", 0),
            (8718, 4, 100, "primitive:long", 1),
            (8726, 4, 100, "primitive:long", 0),
            (8744, 4, 100, "primitive:long", 0),
            (9429, 4, 100, "primitive:long", 0),
            (9657, 4, 100, "primitive:long", 0),
            (9808, 4, 100, "primitive:long", 0),
            (10896, 4, 100, "primitive:long", 0),
            (10900, 4, 100, "primitive:long", 0),
            (13866, 4, 100, "primitive:long", 1),
            (13874, 4, 100, "primitive:long", 1),
            (13896, 4, 100, "primitive:long", 1),
            (14749, 4, 100, "primitive:long", 0),
            (14936, 4, 100, "primitive:long", 0),
            (15087, 4, 100, "primitive:long", 0),
            (16098, 4, 100, "primitive:long", 0),
            (16102, 4, 100, "primitive:long", 0),
            (19016, 4, 100, "primitive:long", 1),
            (19024, 4, 100, "primitive:long", 1),
            (19046, 4, 100, "primitive:long", 1),
            (19819, 4, 100, "primitive:long", 0),
            (20006, 4, 100, "primitive:long", 0),
            (20157, 4, 100, "primitive:long", 0),
            (21168, 4, 100, "primitive:long", 0),
            (21172, 4, 100, "primitive:long", 0),
        ),
    },
)
