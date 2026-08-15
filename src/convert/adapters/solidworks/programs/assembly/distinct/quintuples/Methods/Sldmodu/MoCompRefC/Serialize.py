# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoCompRefC.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "Contents/Config-0-ResolvedFeatures": (
            (5314, 4, 1692, "primitive:long", 0),
            (5318, 4, 1754, "primitive:long", 0),
            (5322, 4, 1812, "primitive:long", 0),
            (5326, 4, 1900, "primitive:long", 0),
            (5330, 4, 1913, "primitive:long", 0),
            (5334, 4, 2021, "primitive:long", 0),
            (5338, 4, 2160, "primitive:long", 0),
            (5342, 4, 2341, "primitive:long", 0),
            (5346, 4, 2436, "primitive:ulong", 0),
            (5350, 4, 2495, "primitive:long", 0),
            (5354, 4, 2684, "primitive:long", -1),
            (5358, 4, 2684, "primitive:long", -1),
            (5362, 4, 2684, "primitive:long", -1),
            (5366, 4, 2684, "primitive:long", -1),
            (5370, 4, 2753, "primitive:long", 0),
            (5374, 4, 2975, "primitive:long", 0),
            (5378, 4, 3098, "primitive:long", 0),
            (5382, 4, 3215, "primitive:long", 0),
            (5386, 4, 3345, "primitive:long", 0),
            (5390, 4, 3452, "primitive:ulong", 18000),
        ),
    },
)
