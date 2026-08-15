# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Sldmfcu.MoWeldDataHelperC.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "Contents/Config-0": (
            (18948, 1, 719, "primitive:uchar", 0),
            (19017, 1, 878, "primitive:uchar", 0),
            (19018, 1, 901, "primitive:uchar", 0),
            (19019, 1, 924, "primitive:uchar", 0),
            (19020, 1, 947, "primitive:uchar", 0),
            (19025, 1, 986, "primitive:uchar", 0),
            (19026, 1, 1009, "primitive:uchar", 0),
            (19027, 4, 1039, "primitive:long", 0),
            (19031, 4, 1058, "primitive:long", 0),
            (19035, 1, 1076, "primitive:uchar", 0),
            (19036, 1, 1096, "primitive:uchar", 0),
            (19037, 1, 1116, "primitive:uchar", 0),
            (19038, 4, 1039, "primitive:long", 0),
            (19042, 4, 1058, "primitive:long", 0),
            (19046, 1, 1076, "primitive:uchar", 0),
            (19047, 1, 1096, "primitive:uchar", 0),
            (19048, 1, 1116, "primitive:uchar", 0),
            (19049, 4, 1146, "primitive:long", 0),
            (19053, 1, 1168, "primitive:uchar", 0),
            (19054, 1, 1191, "primitive:uchar", 1),
            (19075, 1, 1251, "primitive:uchar", 0),
            (19076, 1, 1274, "primitive:uchar", 0),
            (19077, 1, 1297, "primitive:uchar", 0),
            (19078, 1, 1320, "primitive:uchar", 0),
            (19079, 1, 1343, "primitive:uchar", 0),
            (19080, 1, 1366, "primitive:uchar", 0),
            (19081, 1, 1389, "primitive:uchar", 0),
            (19170, 1, 1444, "primitive:uchar", 1),
            (19259, 1, 1499, "primitive:uchar", 1),
        ),
    },
)
