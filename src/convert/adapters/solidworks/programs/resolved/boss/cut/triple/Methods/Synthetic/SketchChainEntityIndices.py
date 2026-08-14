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
            (8486, 16, "SketchOneFirstChainEntityIndices", "direct:4i", (1, 2, 3, 4)),
            (8504, 4, "SketchOneSecondChainEntityIndices", "direct:1i", 0),
            (13642, 16, "SketchTwoFirstChainEntityIndices", "direct:4i", (1, 2, 3, 4)),
            (13660, 4, "SketchTwoSecondChainEntityIndices", "direct:1i", 0),
            (
                18803,
                16,
                "SketchThreeFirstChainEntityIndices",
                "direct:4i",
                (1, 2, 3, 4),
            ),
            (18821, 4, "SketchThreeSecondChainEntityIndices", "direct:1i", 0),
            (23873, 16, "SketchFourFirstChainEntityIndices", "direct:4i", (1, 2, 3, 4)),
            (23891, 4, "SketchFourSecondChainEntityIndices", "direct:1i", 0),
        ),
    },
)
