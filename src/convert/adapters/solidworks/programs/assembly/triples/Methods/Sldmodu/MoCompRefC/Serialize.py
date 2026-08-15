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
            (5202, 4, 1692, "primitive:long", 0),
            (5206, 4, 1754, "primitive:long", 0),
            (5210, 4, 1812, "primitive:long", 0),
            (5214, 4, 1900, "primitive:long", 0),
            (5218, 4, 1913, "primitive:long", 0),
            (5222, 4, 2021, "primitive:long", 0),
            (5226, 4, 2160, "primitive:long", 0),
            (5230, 4, 2341, "primitive:long", 0),
            (5234, 4, 2436, "primitive:ulong", 0),
            (5238, 4, 2495, "primitive:long", 0),
            (5242, 4, 2684, "primitive:long", -1),
            (5246, 4, 2684, "primitive:long", -1),
            (5250, 4, 2684, "primitive:long", -1),
            (5254, 4, 2684, "primitive:long", -1),
            (5258, 4, 2753, "primitive:long", 0),
            (5262, 4, 2975, "primitive:long", 0),
            (5266, 4, 3098, "primitive:long", 0),
            (5270, 4, 3215, "primitive:long", 0),
            (5274, 4, 3345, "primitive:long", 0),
            (5278, 4, 3452, "primitive:ulong", 18000),
        ),
    },
)
