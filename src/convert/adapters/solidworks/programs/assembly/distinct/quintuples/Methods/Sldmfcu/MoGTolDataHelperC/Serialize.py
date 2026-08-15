# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Sldmfcu.MoGTolDataHelperC.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "Contents/Config-0": (
            (19500, 4, 441, "primitive:long", 2),
            (19608, 4, 495, "primitive:long", 1),
            (19612, 4, 514, "primitive:long", 2),
            (19620, 1, 546, "primitive:uchar", 0),
            (19621, 1, 566, "primitive:uchar", 1),
            (19622, 1, 586, "primitive:uchar", 1),
            (19623, 1, 606, "primitive:uchar", 0),
            (19624, 4, 663, "primitive:long", 0),
            (19628, 1, 682, "primitive:uchar", 0),
            (19637, 1, 744, "primitive:uchar", 0),
            (19646, 1, 799, "primitive:uchar", 0),
            (19651, 1, 857, "primitive:uchar", 0),
            (19652, 1, 880, "primitive:uchar", 1),
            (19653, 1, 903, "primitive:uchar", 0),
            (19654, 1, 926, "primitive:uchar", 0),
            (19882, 1, 1077, "primitive:uchar", 0),
            (19883, 1, 1100, "primitive:uchar", 0),
            (19884, 1, 1120, "primitive:uchar", 0),
            (19885, 1, 1200, "primitive:uchar", 0),
            (19886, 1, 1223, "primitive:uchar", 0),
            (19887, 1, 1299, "primitive:uchar", 0),
        ),
    },
)
