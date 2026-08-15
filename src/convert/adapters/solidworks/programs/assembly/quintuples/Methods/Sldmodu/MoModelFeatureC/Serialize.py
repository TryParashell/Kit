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
            (23014, 4, 140, "primitive:long", 0),
            (23317, 4, 140, "primitive:long", 0),
            (23638, 4, 140, "primitive:long", 0),
            (23959, 4, 140, "primitive:long", 0),
        ),
        "Contents/Config-0-ResolvedFeatures": (
            (2440, 4, 140, "primitive:long", 0),
            (3053, 4, 140, "primitive:long", 0),
            (3572, 4, 140, "primitive:long", 0),
            (4142, 4, 140, "primitive:long", 0),
            (4730, 4, 140, "primitive:long", 0),
            (5650, 4, 140, "primitive:long", 0),
        ),
    },
)
