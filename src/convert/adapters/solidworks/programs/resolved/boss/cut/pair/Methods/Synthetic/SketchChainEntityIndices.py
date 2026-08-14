# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Owners.Synthetic.SketchChainEntityIndices import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (8248, 16, "SketchOneFirstChainEntityIndices", "direct:4i", (1, 2, 3, 4)),
            (8266, 4, "SketchOneSecondChainEntityIndices", "direct:1i", 0),
            (13404, 16, "SketchTwoFirstChainEntityIndices", "direct:4i", (1, 2, 3, 4)),
            (13422, 4, "SketchTwoSecondChainEntityIndices", "direct:1i", 0),
            (
                18565,
                16,
                "SketchThreeFirstChainEntityIndices",
                "direct:4i",
                (1, 2, 3, 4),
            ),
            (18583, 4, "SketchThreeSecondChainEntityIndices", "direct:1i", 0),
        ),
    },
)
