# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoDimPatternRegenStatusC.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (9122, 4, 4418, "primitive:long", 1),
            (9126, 4, 4434, "primitive:long", 0),
            (9130, 4, 4450, "primitive:long", 0),
            (9136, 4, 4635, "primitive:long", 0),
            (9140, 4, 4648, "primitive:long", 0),
            (11012, 1, 5935, "primitive:uchar", 1),
            (11015, 1, 6017, "primitive:uchar", 1),
            (11018, 8, 5486, "primitive:double", float.fromhex("0x0.0p+0")),
            (11026, 4, 5502, "primitive:long", 0),
            (11030, 4, 5518, "primitive:long", 0),
            (11034, 4, 5534, "primitive:long", 0),
            (11038, 4, 5550, "primitive:long", 0),
            (11042, 4, 5608, "primitive:long", 0),
            (11046, 4, 5624, "primitive:long", 0),
            (11054, 4, 5712, "primitive:long", 0),
            (11058, 4, 5728, "primitive:long", 0),
            (11062, 4, 5786, "primitive:long", 0),
            (11066, 4, 5802, "primitive:long", 0),
            (11074, 4, 6288, "primitive:long", 1),
            (11078, 4, 6346, "primitive:long", 0),
            (11082, 4, 6427, "primitive:long", 0),
            (11111, 4, 6762, "primitive:long", 1348739666),
            (11115, 4, 6778, "primitive:long", 0),
            (11119, 4, 6794, "primitive:long", 1168530297),
            (11123, 4, 6810, "primitive:long", 52818912),
            (11127, 4, 6888, "primitive:long", 0),
            (11131, 8, 8809, "primitive:double", float.fromhex("0x0.0p+0")),
            (11139, 4, 8833, "primitive:long", -1),
        ),
    },
)
