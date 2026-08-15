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
            (2601, 4, 140, "primitive:long", 0),
            (3893, 4, 140, "primitive:long", 0),
            (4412, 4, 140, "primitive:long", 0),
            (4982, 4, 140, "primitive:long", 0),
            (5570, 4, 140, "primitive:long", 0),
            (6499, 4, 140, "primitive:long", 0),
            (8708, 4, 140, "primitive:long", 0),
            (11710, 4, 140, "primitive:long", 0),
            (13856, 4, 140, "primitive:long", 0),
            (16859, 4, 140, "primitive:long", 0),
            (18039, 4, 140, "primitive:long", 0),
        ),
    },
)
