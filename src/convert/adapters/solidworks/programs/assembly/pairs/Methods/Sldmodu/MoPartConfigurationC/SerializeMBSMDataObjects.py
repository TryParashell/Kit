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
            (24476, 1, 16117, "primitive:uchar", 0),
            (24477, 4, 16148, "primitive:int", 50),
            (24481, 4, 16164, "primitive:int", 108),
            (24489, 4, 16294, "primitive:long", 10),
            (24493, 4, 16327, "primitive:int", 0),
            (24497, 4, 16766, "primitive:long", 0),
            (24704, 4, 16801, "primitive:long", 199),
            (24708, 4, 16829, "primitive:long", 199),
            (24712, 4, 16880, "primitive:long", 0),
            (24718, 4, 17155, "primitive:ulong", 0),
            (24722, 4, 17186, "primitive:long", 0),
            (24748, 4, 20761, "primitive:long", 0),
            (24752, 4, 20779, "primitive:long", 0),
            (24756, 4, 21792, "primitive:long", 0),
            (24760, 4, 22806, "primitive:long", 0),
            (24764, 4, 22893, "primitive:long", 0),
            (24768, 4, 23013, "primitive:long", 0),
            (24776, 4, 23196, "primitive:long", 0),
            (24792, 4, 24585, "primitive:long", 0),
        ),
    },
)
