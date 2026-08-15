# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Owners.Sldmodu.MoPTSRefPlnDataC.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram = (
    KOwnerSites,
    {
        "Contents/Config-0-ResolvedFeatures": (
            (2969, 4, 13613, "primitive:long", 5),
            (2973, 4, 13784, "primitive:long", 0),
            (2979, 4, 13933, "primitive:long", 0),
            (3488, 4, 13613, "primitive:long", 5),
            (3492, 4, 13784, "primitive:long", 0),
            (3498, 4, 13933, "primitive:long", 0),
            (4058, 4, 13613, "primitive:long", 5),
            (4062, 4, 13784, "primitive:long", 0),
            (4068, 4, 13933, "primitive:long", 0),
        ),
    },
)
