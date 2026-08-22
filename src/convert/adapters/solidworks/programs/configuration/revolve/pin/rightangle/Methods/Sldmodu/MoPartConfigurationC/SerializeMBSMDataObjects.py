# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoPartConfigurationC.SerializeMBSMDataObjects import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "Configuration": (
            (24020, 1, 16117, "primitive:uchar", 0),
            (24021, 4, 16148, "primitive:int", 50),
            (24025, 4, 16164, "primitive:int", 108),
            (24057, 4, 16294, "primitive:long", 10),
            (24061, 4, 16327, "primitive:int", 0),
            (24065, 4, 16766, "primitive:long", 0),
            (24482, 4, 16801, "primitive:long", 200),
            (24486, 4, 16829, "primitive:long", 199),
            (24490, 4, 16880, "primitive:long", 1),
            (24494, 4, 16917, "primitive:long", 199),
            (24500, 4, 17155, "primitive:ulong", 0),
            (24504, 4, 17186, "primitive:long", 0),
            (24553, 4, 20761, "primitive:long", 1),
            (24557, 4, 20779, "primitive:long", 0),
            (24561, 4, 20974, "primitive:long", 0),
            (24565, 4, 21792, "primitive:long", 0),
            (24569, 4, 22399, "primitive:long", 20),
            (24573, 4, 22456, "primitive:long", 0),
            (24577, 4, 22611, "primitive:long", 20),
            (24581, 4, 22625, "primitive:long", 0),
            (24585, 4, 22806, "primitive:long", 0),
            (24589, 4, 22893, "primitive:long", 0),
            (24593, 4, 23013, "primitive:long", 0),
            (24601, 4, 23196, "primitive:long", 0),
            (24646, 4, 24585, "primitive:long", 0),
            (24650, 4, 25430, "primitive:long", 0),
            (24654, 1, 25452, "primitive:uchar", 0),
            (24655, 4, 25478, "primitive:long", 0),
            (24659, 4, 26141, "primitive:long", 1),
            (24663, 4, 26442, "primitive:long", 0),
            (24667, 4, 26665, "primitive:long", 0),
            (24866, 4, 26768, "primitive:long", 20),
            (24870, 4, 26856, "primitive:long", 1),
            (24874, 4, 27154, "primitive:long", 0),
            (24886, 4, 27668, "primitive:long", 0),
            (24890, 4, 27756, "primitive:ulong", 101),
            (24894, 4, 27844, "primitive:long", 0),
            (24898, 4, 28024, "primitive:long", 0),
        ),
    },
)
