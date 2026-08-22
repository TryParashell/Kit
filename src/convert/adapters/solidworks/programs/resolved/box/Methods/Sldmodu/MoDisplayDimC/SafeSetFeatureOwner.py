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
            (5620, 4, 4724, "primitive:ulong", 0),
            (5624, 4, 4744, "primitive:long", 0),
            (5628, 4, 1931, "primitive:long", 3),
            (5633, 4, 2342, "primitive:long", 0),
            (5643, 4, 3319, "primitive:ulong", 100000),
            (11594, 4, 4724, "primitive:ulong", 1),
            (11598, 4, 4744, "primitive:long", 1),
            (11701, 4, 1931, "primitive:long", 3),
            (11706, 4, 2342, "primitive:long", 0),
            (11716, 4, 3319, "primitive:ulong", 100000),
        ),
    },
)
