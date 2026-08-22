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
            (18488, 1, 719, "primitive:uchar", 0),
            (18557, 1, 878, "primitive:uchar", 0),
            (18558, 1, 901, "primitive:uchar", 0),
            (18559, 1, 924, "primitive:uchar", 0),
            (18560, 1, 947, "primitive:uchar", 0),
            (18565, 1, 986, "primitive:uchar", 0),
            (18566, 1, 1009, "primitive:uchar", 0),
            (18567, 4, 1039, "primitive:long", 0),
            (18571, 4, 1058, "primitive:long", 0),
            (18575, 1, 1076, "primitive:uchar", 0),
            (18576, 1, 1096, "primitive:uchar", 0),
            (18577, 1, 1116, "primitive:uchar", 0),
            (18578, 4, 1039, "primitive:long", 0),
            (18582, 4, 1058, "primitive:long", 0),
            (18586, 1, 1076, "primitive:uchar", 0),
            (18587, 1, 1096, "primitive:uchar", 0),
            (18588, 1, 1116, "primitive:uchar", 0),
            (18589, 4, 1146, "primitive:long", 0),
            (18593, 1, 1168, "primitive:uchar", 0),
            (18594, 1, 1191, "primitive:uchar", 1),
            (18615, 1, 1251, "primitive:uchar", 0),
            (18616, 1, 1274, "primitive:uchar", 0),
            (18617, 1, 1297, "primitive:uchar", 0),
            (18618, 1, 1320, "primitive:uchar", 0),
            (18619, 1, 1343, "primitive:uchar", 0),
            (18620, 1, 1366, "primitive:uchar", 0),
            (18621, 1, 1389, "primitive:uchar", 0),
            (18710, 1, 1444, "primitive:uchar", 1),
            (18799, 1, 1499, "primitive:uchar", 1),
        ),
    },
)
