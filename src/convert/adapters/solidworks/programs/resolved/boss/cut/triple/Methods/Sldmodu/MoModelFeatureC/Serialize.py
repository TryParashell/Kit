# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoModelFeatureC.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (2839, 4, 140, "primitive:long", 0),
            (4131, 4, 140, "primitive:long", 0),
            (4650, 4, 140, "primitive:long", 0),
            (5220, 4, 140, "primitive:long", 0),
            (5808, 4, 140, "primitive:long", 0),
            (6737, 4, 140, "primitive:long", 0),
            (8946, 4, 140, "primitive:long", 0),
            (11948, 4, 140, "primitive:long", 0),
            (14094, 4, 140, "primitive:long", 0),
            (17109, 4, 140, "primitive:long", 0),
            (19244, 4, 140, "primitive:long", 0),
            (22179, 4, 140, "primitive:long", 0),
            (24314, 4, 140, "primitive:long", 0),
        ),
    },
)
