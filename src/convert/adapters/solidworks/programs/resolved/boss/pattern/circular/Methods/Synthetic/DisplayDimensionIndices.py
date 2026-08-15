# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Synthetic.DisplayDimensionIndices import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (10315, 2, "DisplayDimensionOneIndex", "direct:H", 0),
            (13213, 2, "DisplayDimensionTwoIndex", "direct:H", 0),
            (14753, 2, "DisplayDimensionThreeIndex", "direct:H", 0),
            (16279, 2, "DisplayDimensionFourIndex", "direct:H", 0),
            (18405, 2, "DisplayDimensionFiveIndex", "direct:H", 0),
        ),
    },
)
