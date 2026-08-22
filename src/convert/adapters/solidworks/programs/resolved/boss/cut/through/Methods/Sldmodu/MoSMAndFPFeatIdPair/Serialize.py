# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoSMAndFPFeatIdPair.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (682, 1, 4509, "primitive:uchar", 0),
            (801, 1, 4509, "primitive:uchar", 0),
            (920, 1, 4509, "primitive:uchar", 0),
            (1039, 1, 4509, "primitive:uchar", 0),
            (5915, 1, 4509, "primitive:uchar", 0),
            (8115, 1, 4509, "primitive:uchar", 0),
            (13271, 1, 4509, "primitive:uchar", 0),
            (13691, 1, 4509, "primitive:uchar", 0),
        ),
    },
)
