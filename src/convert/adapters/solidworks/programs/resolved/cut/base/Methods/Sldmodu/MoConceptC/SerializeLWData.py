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
        "ResolvedFeatures": (
            (72, 4, 259, "primitive:long", 0),
            (271, 4, 259, "primitive:long", 0),
            (473, 4, 259, "primitive:long", 0),
            (1210, 4, 259, "primitive:long", 0),
            (1409, 4, 259, "primitive:long", 0),
            (1612, 4, 259, "primitive:long", 0),
            (1814, 4, 259, "primitive:long", 0),
            (1886, 4, 259, "primitive:long", 0),
            (2081, 4, 259, "primitive:long", 0),
            (2476, 4, 259, "primitive:long", 0),
            (2694, 4, 259, "primitive:long", 0),
            (2904, 4, 259, "primitive:long", 0),
            (3098, 4, 259, "primitive:long", 0),
            (3327, 4, 259, "primitive:long", 0),
            (3532, 4, 259, "primitive:long", 0),
            (4051, 4, 259, "primitive:long", 0),
            (4621, 4, 259, "primitive:long", 0),
            (5209, 4, 259, "primitive:long", 0),
            (6138, 4, 259, "primitive:long", 0),
            (8345, 4, 259, "primitive:long", 0),
            (11349, 4, 259, "primitive:long", 0),
            (13600, 4, 259, "primitive:long", 0),
        ),
    },
)
