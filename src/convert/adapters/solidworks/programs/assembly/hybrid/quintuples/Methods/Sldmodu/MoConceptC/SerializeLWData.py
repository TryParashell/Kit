# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoConceptC.SerializeLWData import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "Contents/CMgr": (
            (48, 4, 259, "primitive:long", 0),
            (244, 4, 259, "primitive:long", 0),
        ),
        "Contents/Config-0": (
            (22, 4, 864, "primitive:long", 0),
            (26, 4, 923, "primitive:ulong", 18000),
            (84, 4, 259, "primitive:long", 1),
            (151, 4, 259, "primitive:long", 0),
            (712, 4, 259, "primitive:long", 0),
            (1214, 4, 259, "primitive:long", 0),
            (1716, 4, 259, "primitive:long", 0),
            (2218, 4, 259, "primitive:long", 0),
            (22361, 4, 259, "primitive:long", 0),
            (22431, 4, 259, "primitive:long", 0),
            (22734, 4, 259, "primitive:long", 0),
            (23055, 4, 259, "primitive:long", 0),
            (23376, 4, 259, "primitive:long", 0),
            (25869, 4, 259, "primitive:long", 0),
            (26187, 4, 259, "primitive:long", 0),
        ),
        "Contents/Config-0-ResolvedFeatures": (
            (72, 4, 259, "primitive:long", 0),
            (271, 4, 259, "primitive:long", 0),
            (473, 4, 259, "primitive:long", 0),
            (1061, 4, 259, "primitive:long", 0),
            (1260, 4, 259, "primitive:long", 0),
            (1482, 4, 259, "primitive:long", 0),
            (1689, 4, 259, "primitive:long", 0),
            (1891, 4, 259, "primitive:long", 0),
            (1963, 4, 259, "primitive:long", 0),
            (2158, 4, 259, "primitive:long", 0),
            (2539, 4, 259, "primitive:long", 0),
            (2733, 4, 259, "primitive:long", 0),
            (2930, 4, 259, "primitive:long", 0),
            (3449, 4, 259, "primitive:long", 0),
            (4019, 4, 259, "primitive:long", 0),
            (4607, 4, 259, "primitive:long", 0),
            (5527, 4, 259, "primitive:long", 0),
        ),
    },
)
