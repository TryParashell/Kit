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
        "Configuration": (
            (17692, 4, 441, "primitive:long", 2),
            (17800, 4, 495, "primitive:long", 1),
            (17804, 4, 514, "primitive:long", 2),
            (17812, 1, 546, "primitive:uchar", 0),
            (17813, 1, 566, "primitive:uchar", 1),
            (17814, 1, 586, "primitive:uchar", 1),
            (17815, 1, 606, "primitive:uchar", 0),
            (17816, 4, 663, "primitive:long", 0),
            (17820, 1, 682, "primitive:uchar", 0),
            (17829, 1, 744, "primitive:uchar", 0),
            (17838, 1, 799, "primitive:uchar", 0),
            (17843, 1, 857, "primitive:uchar", 0),
            (17844, 1, 880, "primitive:uchar", 1),
            (17845, 1, 903, "primitive:uchar", 0),
            (17846, 1, 926, "primitive:uchar", 0),
            (18074, 1, 1077, "primitive:uchar", 0),
            (18075, 1, 1100, "primitive:uchar", 0),
            (18076, 1, 1120, "primitive:uchar", 0),
            (18077, 1, 1200, "primitive:uchar", 0),
            (18078, 1, 1223, "primitive:uchar", 0),
            (18079, 1, 1299, "primitive:uchar", 0),
        ),
    },
)
