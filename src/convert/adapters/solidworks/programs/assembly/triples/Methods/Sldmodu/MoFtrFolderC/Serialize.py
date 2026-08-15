# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Owners.Sldmodu.MoFtrFolderC.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram = (
    KOwnerSites,
    {
        "Contents/Config-0-ResolvedFeatures": (
            (2179, 4, 281, "primitive:long", 0),
            (2183, 4, 350, "primitive:long", 0),
            (2187, 4, 429, "primitive:long", 1),
            (2191, 4, 484, "primitive:long", 1),
            (2195, 4, 281, "primitive:long", 1),
            (2199, 4, 350, "primitive:long", 0),
            (2203, 4, 429, "primitive:long", 1),
            (2207, 4, 484, "primitive:long", 1),
        ),
    },
)
