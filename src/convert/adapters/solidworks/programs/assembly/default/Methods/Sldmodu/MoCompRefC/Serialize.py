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
            (5090, 4, 1692, "primitive:long", 0),
            (5094, 4, 1754, "primitive:long", 0),
            (5098, 4, 1812, "primitive:long", 0),
            (5102, 4, 1900, "primitive:long", 0),
            (5106, 4, 1913, "primitive:long", 0),
            (5110, 4, 2021, "primitive:long", 0),
            (5114, 4, 2160, "primitive:long", 0),
            (5118, 4, 2341, "primitive:long", 0),
            (5122, 4, 2436, "primitive:ulong", 0),
            (5126, 4, 2495, "primitive:long", 0),
            (5130, 4, 2684, "primitive:long", -1),
            (5134, 4, 2684, "primitive:long", -1),
            (5138, 4, 2684, "primitive:long", -1),
            (5142, 4, 2684, "primitive:long", -1),
            (5146, 4, 2753, "primitive:long", 0),
            (5150, 4, 2975, "primitive:long", 0),
            (5154, 4, 3098, "primitive:long", 0),
            (5158, 4, 3215, "primitive:long", 0),
            (5162, 4, 3345, "primitive:long", 0),
            (5166, 4, 3452, "primitive:ulong", 18000),
        ),
    },
)
