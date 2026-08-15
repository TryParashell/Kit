# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Sldmodu.SgSketchBlockHandle.GetRuntimeClass import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "Contents/Config-0": (
            (24778, 4, 3099, "primitive:long", 0),
            (24784, 4, 3154, "primitive:long", 0),
            (24788, 4, 4083, "primitive:ulong", 0),
        ),
        "Contents/Config-0-ResolvedFeatures": (
            (5060, 4, 15839, "primitive:long", 0),
            (5064, 4, 16002, "primitive:long", 0),
            (5068, 4, 16657, "primitive:long", 0),
        ),
    },
)
