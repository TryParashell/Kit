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
            (6306, 4, 15839, "primitive:long", 0),
            (6310, 4, 16002, "primitive:long", 0),
            (6314, 4, 16657, "primitive:long", 0),
            (8427, 4, 15839, "primitive:long", 0),
            (8431, 4, 16002, "primitive:long", 0),
            (8435, 4, 16657, "primitive:long", 0),
            (13602, 4, 15839, "primitive:long", 0),
            (13606, 4, 16002, "primitive:long", 0),
            (13610, 4, 16657, "primitive:long", 0),
            (18763, 4, 15839, "primitive:long", 0),
            (18767, 4, 16002, "primitive:long", 0),
            (18771, 4, 16657, "primitive:long", 0),
            (23833, 4, 15839, "primitive:long", 0),
            (23837, 4, 16002, "primitive:long", 0),
            (23841, 4, 16657, "primitive:long", 0),
        ),
    },
)
