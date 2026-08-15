# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoDisplayDimC.SafeSetFeatureOwner import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (5858, 4, 4724, "primitive:ulong", 0),
            (5862, 4, 4744, "primitive:long", 0),
            (5866, 4, 1931, "primitive:long", 3),
            (5871, 4, 2342, "primitive:long", 0),
            (5881, 4, 3319, "primitive:ulong", 100000),
            (7979, 4, 4724, "primitive:ulong", 1),
            (7983, 4, 4744, "primitive:long", 1),
            (8086, 4, 1931, "primitive:long", 3),
            (8091, 4, 2342, "primitive:long", 0),
            (8101, 4, 3319, "primitive:ulong", 100000),
            (13154, 4, 4724, "primitive:ulong", 1),
            (13158, 4, 4744, "primitive:long", 1),
            (13242, 4, 1931, "primitive:long", 3),
            (13247, 4, 2342, "primitive:long", 0),
            (13257, 4, 3319, "primitive:ulong", 100000),
        ),
    },
)
