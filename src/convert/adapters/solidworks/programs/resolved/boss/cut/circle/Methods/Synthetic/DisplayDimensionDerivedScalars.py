# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Synthetic.DisplayDimensionDerivedScalars import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (
                10940,
                8,
                "DisplayDimensionOneDerivedScalar",
                "direct:d",
                float.fromhex("0x1.47ae147ae147bp-5"),
            ),
            (
                16130,
                8,
                "DisplayDimensionTwoDerivedScalar",
                "direct:d",
                float.fromhex("0x1.eb851eb851eb8p-7"),
            ),
            (
                20453,
                8,
                "DisplayDimensionThreeDerivedScalar",
                "direct:d",
                float.fromhex("0x1.999999999999ap-5"),
            ),
        ),
    },
)
