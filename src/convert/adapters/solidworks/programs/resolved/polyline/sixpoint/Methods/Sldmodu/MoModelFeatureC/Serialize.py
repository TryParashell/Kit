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
            (2125, 4, 140, "primitive:long", 0),
            (3417, 4, 140, "primitive:long", 0),
            (3936, 4, 140, "primitive:long", 0),
            (4506, 4, 140, "primitive:long", 0),
            (5094, 4, 140, "primitive:long", 0),
            (6023, 4, 140, "primitive:long", 0),
            (9362, 4, 140, "primitive:long", 0),
        ),
    },
)
