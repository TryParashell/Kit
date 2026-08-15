# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Sldmfcu.SuObArray.SerializePtr import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "Contents/Config-0-ResolvedFeatures": (
            (2895, 4, 100, "primitive:long", 0),
            (2899, 4, 100, "primitive:long", 0),
            (2913, 4, 100, "primitive:long", 0),
            (2939, 4, 100, "primitive:long", 0),
            (3414, 4, 100, "primitive:long", 0),
            (3418, 4, 100, "primitive:long", 0),
            (3432, 4, 100, "primitive:long", 0),
            (3458, 4, 100, "primitive:long", 0),
            (3984, 4, 100, "primitive:long", 0),
            (3988, 4, 100, "primitive:long", 0),
            (4002, 4, 100, "primitive:long", 0),
            (4028, 4, 100, "primitive:long", 0),
        ),
    },
)
