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
            (9739, 4, 4418, "primitive:long", 1),
            (9743, 4, 4434, "primitive:long", 0),
            (9747, 4, 4450, "primitive:long", 0),
            (9753, 4, 4635, "primitive:long", 0),
            (9757, 4, 4648, "primitive:long", 0),
            (11629, 1, 5935, "primitive:uchar", 1),
            (11632, 1, 6017, "primitive:uchar", 1),
            (11635, 8, 5486, "primitive:double", float.fromhex("0x0.0p+0")),
            (11643, 4, 5502, "primitive:long", 0),
            (11647, 4, 5518, "primitive:long", 0),
            (11651, 4, 5534, "primitive:long", 0),
            (11655, 4, 5550, "primitive:long", 0),
            (11659, 4, 5608, "primitive:long", 0),
            (11663, 4, 5624, "primitive:long", 0),
            (11671, 4, 5712, "primitive:long", 0),
            (11675, 4, 5728, "primitive:long", 0),
            (11679, 4, 5786, "primitive:long", 0),
            (11683, 4, 5802, "primitive:long", 0),
            (11691, 4, 6288, "primitive:long", 1),
            (11695, 4, 6346, "primitive:long", 0),
            (11699, 4, 6427, "primitive:long", 0),
            (11728, 4, 6762, "primitive:long", -1571478958),
            (11732, 4, 6778, "primitive:long", 0),
            (11736, 4, 6794, "primitive:long", 1168530297),
            (11740, 4, 6810, "primitive:long", 116857184),
            (11744, 4, 6888, "primitive:long", 0),
            (11748, 8, 8809, "primitive:double", float.fromhex("0x0.0p+0")),
            (11756, 4, 8833, "primitive:long", -1),
        ),
    },
)
