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
            (4762, 2, 11741, "primitive:ushort", 0),
            (4904, 4, 12263, "primitive:int", 0),
            (4908, 4, 13401, "primitive:int", 0),
            (4912, 4, 13971, "primitive:int", 0),
            (4916, 4, 14506, "primitive:int", 0),
            (4920, 4, 15727, "primitive:int", 0),
            (4924, 4, 16737, "primitive:int", 0),
            (4928, 4, 18519, "primitive:int", 0),
            (4932, 4, 22406, "primitive:int", 0),
            (4936, 4, 22957, "primitive:int", 0),
            (4940, 4, 23845, "primitive:int", 0),
            (4944, 4, 24627, "primitive:int", 0),
            (4948, 4, 25143, "primitive:long", 0),
            (5056, 2, 25628, "primitive:ushort", 0),
            (5058, 2, 26166, "primitive:ushort", 0),
            (5060, 2, 26708, "primitive:ushort", 0),
            (5062, 2, 27254, "primitive:ushort", 0),
            (5064, 2, 27765, "primitive:ushort", 2),
            (5066, 2, 27788, "primitive:ushort", 1),
            (5068, 4, 27811, "primitive:long", 1),
            (5132, 2, 28607, "primitive:ushort", 0),
            (5134, 2, 28687, "primitive:ushort", 0),
            (5136, 2, 28767, "primitive:ushort", 0),
            (5138, 2, 28930, "primitive:ushort", 0),
            (5158, 4, 31115, "primitive:long", -1),
            (5186, 4, 31190, "primitive:ulong", 1),
            (5190, 4, 31249, "primitive:long", 0),
            (5194, 4, 31383, "primitive:long", 0),
            (5202, 4, 31770, "primitive:long", 0),
            (5226, 2, 32600, "primitive:ushort", 0),
            (5244, 4, 37366, "primitive:long", 0),
            (5248, 4, 37852, "primitive:long", 0),
            (5252, 4, 34431, "primitive:long", 0),
        ),
    },
)
