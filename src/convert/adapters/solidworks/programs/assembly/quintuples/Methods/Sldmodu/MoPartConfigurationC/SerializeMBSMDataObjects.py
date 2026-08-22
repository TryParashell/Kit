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
        "Contents/Config-0": (
            (26258, 1, 16117, "primitive:uchar", 0),
            (26259, 4, 16148, "primitive:int", 50),
            (26263, 4, 16164, "primitive:int", 108),
            (26271, 4, 16294, "primitive:long", 10),
            (26275, 4, 16327, "primitive:int", 0),
            (26279, 4, 16766, "primitive:long", 0),
            (26486, 4, 16801, "primitive:long", 199),
            (26490, 4, 16829, "primitive:long", 199),
            (26494, 4, 16880, "primitive:long", 0),
            (26500, 4, 17155, "primitive:ulong", 0),
            (26504, 4, 17186, "primitive:long", 0),
            (26530, 4, 20761, "primitive:long", 0),
            (26534, 4, 20779, "primitive:long", 0),
            (26538, 4, 21792, "primitive:long", 0),
            (26542, 4, 22806, "primitive:long", 0),
            (26546, 4, 22893, "primitive:long", 0),
            (26550, 4, 23013, "primitive:long", 0),
            (26558, 4, 23196, "primitive:long", 0),
            (26574, 4, 24585, "primitive:long", 0),
        ),
    },
)
