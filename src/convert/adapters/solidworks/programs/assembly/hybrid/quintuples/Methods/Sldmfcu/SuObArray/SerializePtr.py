# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Owners.Sldmfcu.SuObArray.SerializePtr import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram = (
    KOwnerSites,
    {
        "Contents/Config-0-ResolvedFeatures": (
            (3063, 4, 100, "primitive:long", 0),
            (3067, 4, 100, "primitive:long", 0),
            (3081, 4, 100, "primitive:long", 0),
            (3107, 4, 100, "primitive:long", 0),
            (3582, 4, 100, "primitive:long", 0),
            (3586, 4, 100, "primitive:long", 0),
            (3600, 4, 100, "primitive:long", 0),
            (3626, 4, 100, "primitive:long", 0),
            (4152, 4, 100, "primitive:long", 0),
            (4156, 4, 100, "primitive:long", 0),
            (4170, 4, 100, "primitive:long", 0),
            (4196, 4, 100, "primitive:long", 0),
        ),
    },
)
