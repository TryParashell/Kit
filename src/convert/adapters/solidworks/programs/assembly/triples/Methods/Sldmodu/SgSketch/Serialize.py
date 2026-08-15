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
            (4650, 2, 11741, "primitive:ushort", 0),
            (4792, 4, 12263, "primitive:int", 0),
            (4796, 4, 13401, "primitive:int", 0),
            (4800, 4, 13971, "primitive:int", 0),
            (4804, 4, 14506, "primitive:int", 0),
            (4808, 4, 15727, "primitive:int", 0),
            (4812, 4, 16737, "primitive:int", 0),
            (4816, 4, 18519, "primitive:int", 0),
            (4820, 4, 22406, "primitive:int", 0),
            (4824, 4, 22957, "primitive:int", 0),
            (4828, 4, 23845, "primitive:int", 0),
            (4832, 4, 24627, "primitive:int", 0),
            (4836, 4, 25143, "primitive:long", 0),
            (4944, 2, 25628, "primitive:ushort", 0),
            (4946, 2, 26166, "primitive:ushort", 0),
            (4948, 2, 26708, "primitive:ushort", 0),
            (4950, 2, 27254, "primitive:ushort", 0),
            (4952, 2, 27765, "primitive:ushort", 2),
            (4954, 2, 27788, "primitive:ushort", 1),
            (4956, 4, 27811, "primitive:long", 1),
            (5020, 2, 28607, "primitive:ushort", 0),
            (5022, 2, 28687, "primitive:ushort", 0),
            (5024, 2, 28767, "primitive:ushort", 0),
            (5026, 2, 28930, "primitive:ushort", 0),
            (5046, 4, 31115, "primitive:long", -1),
            (5074, 4, 31190, "primitive:ulong", 1),
            (5078, 4, 31249, "primitive:long", 0),
            (5082, 4, 31383, "primitive:long", 0),
            (5090, 4, 31770, "primitive:long", 0),
            (5114, 2, 32600, "primitive:ushort", 0),
            (5132, 4, 37366, "primitive:long", 0),
            (5136, 4, 37852, "primitive:long", 0),
            (5140, 4, 34431, "primitive:long", 0),
        ),
    },
)
