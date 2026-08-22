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
            (24556, 4, 16801, "primitive:long", 200),
            (24560, 4, 16829, "primitive:long", 199),
            (24564, 4, 16880, "primitive:long", 1),
            (24568, 4, 16917, "primitive:long", 199),
            (24574, 4, 17155, "primitive:ulong", 0),
            (24578, 4, 17186, "primitive:long", 0),
            (24627, 4, 20761, "primitive:long", 1),
            (24631, 4, 20779, "primitive:long", 0),
            (24635, 4, 20974, "primitive:long", 0),
            (24639, 4, 21792, "primitive:long", 0),
            (24643, 4, 22399, "primitive:long", 20),
            (24647, 4, 22456, "primitive:long", 0),
            (24651, 4, 22611, "primitive:long", 20),
            (24655, 4, 22625, "primitive:long", 0),
            (24659, 4, 22806, "primitive:long", 0),
            (24663, 4, 22893, "primitive:long", 0),
            (24667, 4, 23013, "primitive:long", 0),
            (24675, 4, 23196, "primitive:long", 0),
            (24720, 4, 24585, "primitive:long", 0),
            (24724, 4, 25430, "primitive:long", 0),
            (24728, 1, 25452, "primitive:uchar", 0),
            (24729, 4, 25478, "primitive:long", 0),
            (24733, 4, 26141, "primitive:long", 1),
            (24737, 4, 26442, "primitive:long", 0),
            (24741, 4, 26665, "primitive:long", 0),
            (24940, 4, 26768, "primitive:long", 20),
            (24944, 4, 26856, "primitive:long", 1),
            (24948, 4, 27154, "primitive:long", 0),
            (24960, 4, 27668, "primitive:long", 0),
            (24964, 4, 27756, "primitive:ulong", 101),
            (24968, 4, 27844, "primitive:long", 0),
            (24972, 4, 28024, "primitive:long", 0),
        ),
    },
)
