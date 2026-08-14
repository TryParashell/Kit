# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Owners.Sldmodu.MoCompRefC.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram = (
    KOwnerSites,
    {
        "Contents/Config-0-ResolvedFeatures": (
            (5370, 4, 1692, "primitive:long", 0),
            (5374, 4, 1754, "primitive:long", 0),
            (5378, 4, 1812, "primitive:long", 0),
            (5382, 4, 1900, "primitive:long", 0),
            (5386, 4, 1913, "primitive:long", 0),
            (5390, 4, 2021, "primitive:long", 0),
            (5394, 4, 2160, "primitive:long", 0),
            (5398, 4, 2341, "primitive:long", 0),
            (5402, 4, 2436, "primitive:ulong", 0),
            (5406, 4, 2495, "primitive:long", 0),
            (5410, 4, 2684, "primitive:long", -1),
            (5414, 4, 2684, "primitive:long", -1),
            (5418, 4, 2684, "primitive:long", -1),
            (5422, 4, 2684, "primitive:long", -1),
            (5426, 4, 2753, "primitive:long", 0),
            (5430, 4, 2975, "primitive:long", 0),
            (5434, 4, 3098, "primitive:long", 0),
            (5438, 4, 3215, "primitive:long", 0),
            (5442, 4, 3345, "primitive:long", 0),
            (5446, 4, 3452, "primitive:ulong", 18000),
        ),
    },
)
