# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Sldmfcu.MoLineVizC.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (6228, 4, 166, "primitive:int", -1),
            (6232, 4, 245, "primitive:int", 1),
            (8275, 4, 166, "primitive:int", -1),
            (8279, 4, 245, "primitive:int", 1),
            (13470, 4, 166, "primitive:int", -1),
            (13474, 4, 245, "primitive:int", 1),
            (18631, 4, 166, "primitive:int", -1),
            (18635, 4, 245, "primitive:int", 1),
            (23701, 4, 166, "primitive:int", -1),
            (23705, 4, 245, "primitive:int", 1),
        ),
    },
)
