# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoVectorParameterC.GetThisClass import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "Configuration": (
            (2780, 8, 1992, "primitive:double", float.fromhex("0x1.f400000000000p+9")),
            (2788, 1, 2107, "primitive:uchar", 0),
            (2848, 4, 8936, "primitive:long", 0),
            (2904, 4, 8936, "primitive:long", 0),
            (20631, 4, 8936, "primitive:long", 0),
            (20934, 4, 8936, "primitive:long", 0),
            (21255, 4, 8936, "primitive:long", 0),
            (21576, 4, 8936, "primitive:long", 0),
            (21837, 4, 8936, "primitive:long", 0),
            (24093, 4, 8936, "primitive:long", 0),
            (25041, 4, 8936, "primitive:long", 0),
        ),
    },
)
