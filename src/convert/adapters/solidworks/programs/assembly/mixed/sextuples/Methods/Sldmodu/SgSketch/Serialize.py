# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Sldmodu.SgSketch.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "Contents/Config-0-ResolvedFeatures": (
            (4818, 2, 11741, "primitive:ushort", 0),
            (4960, 4, 12263, "primitive:int", 0),
            (4964, 4, 13401, "primitive:int", 0),
            (4968, 4, 13971, "primitive:int", 0),
            (4972, 4, 14506, "primitive:int", 0),
            (4976, 4, 15727, "primitive:int", 0),
            (4980, 4, 16737, "primitive:int", 0),
            (4984, 4, 18519, "primitive:int", 0),
            (4988, 4, 22406, "primitive:int", 0),
            (4992, 4, 22957, "primitive:int", 0),
            (4996, 4, 23845, "primitive:int", 0),
            (5000, 4, 24627, "primitive:int", 0),
            (5004, 4, 25143, "primitive:long", 0),
            (5112, 2, 25628, "primitive:ushort", 0),
            (5114, 2, 26166, "primitive:ushort", 0),
            (5116, 2, 26708, "primitive:ushort", 0),
            (5118, 2, 27254, "primitive:ushort", 0),
            (5120, 2, 27765, "primitive:ushort", 2),
            (5122, 2, 27788, "primitive:ushort", 1),
            (5124, 4, 27811, "primitive:long", 1),
            (5188, 2, 28607, "primitive:ushort", 0),
            (5190, 2, 28687, "primitive:ushort", 0),
            (5192, 2, 28767, "primitive:ushort", 0),
            (5194, 2, 28930, "primitive:ushort", 0),
            (5214, 4, 31115, "primitive:long", -1),
            (5242, 4, 31190, "primitive:ulong", 1),
            (5246, 4, 31249, "primitive:long", 0),
            (5250, 4, 31383, "primitive:long", 0),
            (5258, 4, 31770, "primitive:long", 0),
            (5282, 2, 32600, "primitive:ushort", 0),
            (5300, 4, 37366, "primitive:long", 0),
            (5304, 4, 37852, "primitive:long", 0),
            (5308, 4, 34431, "primitive:long", 0),
        ),
    },
)
