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
        "Contents/Config-0": (
            (20638, 4, 140, "primitive:long", 0),
            (20941, 4, 140, "primitive:long", 0),
            (21262, 4, 140, "primitive:long", 0),
            (21583, 4, 140, "primitive:long", 0),
        ),
        "Contents/Config-0-ResolvedFeatures": (
            (2216, 4, 140, "primitive:long", 0),
            (2829, 4, 140, "primitive:long", 0),
            (3348, 4, 140, "primitive:long", 0),
            (3918, 4, 140, "primitive:long", 0),
            (4506, 4, 140, "primitive:long", 0),
            (5426, 4, 140, "primitive:long", 0),
        ),
    },
)
