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
                11155,
                8,
                "DisplayDimensionOneDerivedScalar",
                "direct:d",
                float.fromhex("0x1.47ae147ae147bp-8"),
            ),
            (
                13831,
                8,
                "DisplayDimensionTwoDerivedScalar",
                "direct:d",
                float.fromhex("0x1.0000000000000p+2"),
            ),
            (
                15330,
                8,
                "DisplayDimensionThreeDerivedScalar",
                "direct:d",
                float.fromhex("0x0.0p+0"),
            ),
            (
                16922,
                8,
                "DisplayDimensionFourDerivedScalar",
                "direct:d",
                float.fromhex("0x0.0p+0"),
            ),
            (
                19050,
                8,
                "DisplayDimensionFiveDerivedScalar",
                "direct:d",
                float.fromhex("0x1.921fb54442d18p+2"),
            ),
        ),
    },
)
