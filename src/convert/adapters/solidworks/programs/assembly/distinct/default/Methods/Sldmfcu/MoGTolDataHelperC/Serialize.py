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
            (18270, 4, 441, "primitive:long", 2),
            (18378, 4, 495, "primitive:long", 1),
            (18382, 4, 514, "primitive:long", 2),
            (18390, 1, 546, "primitive:uchar", 0),
            (18391, 1, 566, "primitive:uchar", 1),
            (18392, 1, 586, "primitive:uchar", 1),
            (18393, 1, 606, "primitive:uchar", 0),
            (18394, 4, 663, "primitive:long", 0),
            (18398, 1, 682, "primitive:uchar", 0),
            (18407, 1, 744, "primitive:uchar", 0),
            (18416, 1, 799, "primitive:uchar", 0),
            (18421, 1, 857, "primitive:uchar", 0),
            (18422, 1, 880, "primitive:uchar", 1),
            (18423, 1, 903, "primitive:uchar", 0),
            (18424, 1, 926, "primitive:uchar", 0),
            (18652, 1, 1077, "primitive:uchar", 0),
            (18653, 1, 1100, "primitive:uchar", 0),
            (18654, 1, 1120, "primitive:uchar", 0),
            (18655, 1, 1200, "primitive:uchar", 0),
            (18656, 1, 1223, "primitive:uchar", 0),
            (18657, 1, 1299, "primitive:uchar", 0),
        ),
    },
)
