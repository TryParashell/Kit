# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Owners.Synthetic.DisplayDimensionDerivedScalars import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (
                10583,
                8,
                "DisplayDimensionOneDerivedScalar",
                "direct:d",
                float.fromhex("0x1.47ae147ae147bp-7"),
            ),
            (
                13082,
                8,
                "DisplayDimensionTwoDerivedScalar",
                "direct:d",
                float.fromhex("0x1.0624dd2f1a9fcp-9"),
            ),
        ),
    },
)
