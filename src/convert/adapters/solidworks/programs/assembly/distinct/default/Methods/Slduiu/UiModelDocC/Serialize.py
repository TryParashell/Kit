# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Slduiu.UiModelDocC.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "Contents/Definition": (
            (4, 4, 3149, "primitive:long", 6),
            (8, 4, 3232, "primitive:long", 50),
            (12, 4, 3248, "primitive:long", 1),
            (16, 4, 3340, "primitive:long", 1),
            (38, 1, 4088, "primitive:uchar", 0),
            (179, 2, 4145, "primitive:ushort", 3),
            (181, 2, 4213, "primitive:ushort", 1),
            (183, 1, 4238, "primitive:uchar", 2),
            (184, 4, 4315, "primitive:long", 796921082),
            (188, 4, 4400, "primitive:long", 2046825472),
            (3047, 2, 5996, "primitive:ushort", 1),
            (3479, 4, 8006, "primitive:long", 2),
            (3483, 4, 8073, "primitive:long", -1),
            (3487, 4, 8089, "primitive:long", -1),
            (3491, 4, 8151, "primitive:long", 73781),
            (3495, 1, 8328, "primitive:uchar", 0),
            (3520, 2, 8494, "primitive:ushort", 2),
            (3522, 2, 8519, "primitive:ushort", 38281),
            (3524, 4, 8620, "primitive:long", 0),
            (3530, 4, 8769, "primitive:long", 515),
            (3615, 4, 9943, "primitive:ulong", 0),
            (3619, 1, 10045, "primitive:uchar", 0),
            (3620, 1, 10121, "primitive:uchar", 1),
            (3625, 2, 11159, "primitive:ushort", 0),
            (3627, 1, 11245, "primitive:uchar", 1),
            (3658, 4, 11758, "primitive:long", 0),
            (3662, 4, 11779, "primitive:long", 0),
            (3666, 4, 11758, "primitive:long", 0),
            (3670, 4, 11779, "primitive:long", 0),
            (3674, 4, 11827, "primitive:long", 0),
            (3678, 4, 11904, "primitive:long", 0),
            (3730, 4, 12002, "primitive:long", 1),
            (3734, 4, 12069, "primitive:long", 1),
            (3738, 4, 12136, "primitive:long", 0),
            (3742, 4, 12208, "primitive:long", 1),
            (3746, 4, 12275, "primitive:long", 0),
            (3752, 4, 12358, "primitive:long", 1),
            (3756, 4, 12425, "primitive:long", 1),
            (3760, 4, 12497, "primitive:long", 0),
            (3764, 4, 12564, "primitive:long", 0),
            (3768, 4, 12631, "primitive:long", 0),
            (3772, 4, 12703, "primitive:long", 2),
            (3778, 4, 12968, "primitive:long", 0),
            (3782, 4, 13035, "primitive:long", 0),
            (3786, 4, 13102, "primitive:long", 0),
            (3790, 4, 13169, "primitive:long", 3),
            (3794, 4, 13236, "primitive:long", 1),
            (3798, 4, 13295, "primitive:long", 0),
        ),
    },
)
