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
            (6334, 4, 4724, "primitive:ulong", 0),
            (6338, 4, 4744, "primitive:long", 0),
            (6342, 4, 1931, "primitive:long", 3),
            (6347, 4, 2342, "primitive:long", 0),
            (6357, 4, 3319, "primitive:ulong", 100000),
            (8455, 4, 4724, "primitive:ulong", 1),
            (8459, 4, 4744, "primitive:long", 1),
            (8562, 4, 1931, "primitive:long", 3),
            (8567, 4, 2342, "primitive:long", 0),
            (8577, 4, 3319, "primitive:ulong", 100000),
            (13630, 4, 4724, "primitive:ulong", 1),
            (13634, 4, 4744, "primitive:long", 1),
            (13718, 4, 1931, "primitive:long", 3),
            (13723, 4, 2342, "primitive:long", 0),
            (13733, 4, 3319, "primitive:ulong", 100000),
            (18791, 4, 4724, "primitive:ulong", 1),
            (18795, 4, 4744, "primitive:long", 1),
            (18879, 4, 1931, "primitive:long", 3),
            (18884, 4, 2342, "primitive:long", 0),
            (18894, 4, 3319, "primitive:ulong", 100000),
            (23861, 4, 4724, "primitive:ulong", 1),
            (23865, 4, 4744, "primitive:long", 1),
            (23949, 4, 1931, "primitive:long", 3),
            (23954, 4, 2342, "primitive:long", 0),
            (23964, 4, 3319, "primitive:ulong", 100000),
        ),
    },
)
