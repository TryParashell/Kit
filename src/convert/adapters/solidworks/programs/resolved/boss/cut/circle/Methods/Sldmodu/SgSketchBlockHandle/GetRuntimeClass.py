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
        "ResolvedFeatures": (
            (6068, 4, 15839, "primitive:long", 0),
            (6072, 4, 16002, "primitive:long", 0),
            (6076, 4, 16657, "primitive:long", 0),
            (8189, 4, 15839, "primitive:long", 0),
            (8193, 4, 16002, "primitive:long", 0),
            (8197, 4, 16657, "primitive:long", 0),
            (13364, 4, 15839, "primitive:long", 0),
            (13368, 4, 16002, "primitive:long", 0),
            (13372, 4, 16657, "primitive:long", 0),
            (17570, 4, 15839, "primitive:long", 0),
            (17574, 4, 16002, "primitive:long", 0),
            (17578, 4, 16657, "primitive:long", 0),
        ),
    },
)
