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
            (9850, 2, "DisplayDimensionOneIndex", "direct:H", 0),
            (12742, 2, "DisplayDimensionTwoIndex", "direct:H", 0),
            (14284, 2, "DisplayDimensionThreeIndex", "direct:H", 0),
            (16021, 2, "DisplayDimensionFourIndex", "direct:H", 0),
            (17522, 2, "DisplayDimensionFiveIndex", "direct:H", 0),
            (19613, 2, "DisplayDimensionSixIndex", "direct:H", 0),
            (21196, 2, "DisplayDimensionSevenIndex", "direct:H", 0),
        ),
    },
)
