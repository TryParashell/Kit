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
            (197, 4, 259, "primitive:long", 0),
            (20445, 4, 259, "primitive:long", 0),
            (20515, 4, 259, "primitive:long", 0),
            (20818, 4, 259, "primitive:long", 0),
            (21139, 4, 259, "primitive:long", 0),
            (21460, 4, 259, "primitive:long", 0),
            (23953, 4, 259, "primitive:long", 0),
            (24271, 4, 259, "primitive:long", 0),
        ),
        "Contents/Config-0-ResolvedFeatures": (
            (72, 4, 259, "primitive:long", 0),
            (271, 4, 259, "primitive:long", 0),
            (473, 4, 259, "primitive:long", 0),
            (837, 4, 259, "primitive:long", 0),
            (1036, 4, 259, "primitive:long", 0),
            (1258, 4, 259, "primitive:long", 0),
            (1465, 4, 259, "primitive:long", 0),
            (1667, 4, 259, "primitive:long", 0),
            (1739, 4, 259, "primitive:long", 0),
            (1934, 4, 259, "primitive:long", 0),
            (2315, 4, 259, "primitive:long", 0),
            (2509, 4, 259, "primitive:long", 0),
            (2706, 4, 259, "primitive:long", 0),
            (3225, 4, 259, "primitive:long", 0),
            (3795, 4, 259, "primitive:long", 0),
            (4383, 4, 259, "primitive:long", 0),
            (5303, 4, 259, "primitive:long", 0),
        ),
    },
)
