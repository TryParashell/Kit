# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoIgnorableCompareObj.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "Contents/CMgr": (
            (1385, 2, 25791, "primitive:ushort", 0),
            (1715, 4, 26469, "primitive:long", 0),
            (1723, 4, 26636, "primitive:long", -1),
            (2055, 2, 25791, "primitive:ushort", 0),
            (2160, 4, 26469, "primitive:long", 0),
            (2168, 4, 26636, "primitive:long", -1),
        ),
        "Contents/Config-0": (
            (316, 1, 30609, "primitive:uchar", 1),
            (351, 1, 30762, "primitive:uchar", 1),
            (424, 8, 30831, "primitive:double", float.fromhex("0x1.776793ed35a44p-6")),
            (434, 2, 32508, "primitive:ushort", 3),
            (436, 2, 32533, "primitive:ushort", 0),
            (438, 4, 32610, "primitive:ulong", 121),
            (460, 4, 32669, "primitive:long", 0),
            (464, 1, 32833, "primitive:uchar", 0),
            (465, 1, 32975, "primitive:uchar", 0),
            (466, 4, 33297, "primitive:long", 0),
            (470, 4, 33493, "primitive:ulong", 102),
            (476, 4, 33676, "primitive:long", 0),
            (484, 4, 33934, "primitive:long", -1),
            (490, 4, 34234, "primitive:long", 15),
            (494, 4, 34293, "primitive:long", 0),
            (500, 4, 34442, "primitive:long", 0),
            (504, 4, 34516, "primitive:long", 0),
            (508, 4, 34530, "primitive:long", 0),
            (512, 4, 34664, "primitive:long", 0),
            (516, 4, 34723, "primitive:long", 0),
            (524, 4, 34839, "primitive:long", 0),
            (828, 4, 35013, "primitive:long", 0),
            (840, 4, 35422, "primitive:long", 0),
            (844, 4, 35481, "primitive:long", 0),
            (848, 4, 35540, "primitive:long", 0),
            (852, 4, 35599, "primitive:ulong", 101),
            (856, 4, 35658, "primitive:ulong", 102),
            (860, 4, 35674, "primitive:ulong", 101),
            (868, 4, 35943, "primitive:long", 0),
            (872, 4, 35959, "primitive:long", 0),
            (876, 4, 35975, "primitive:long", -1),
            (880, 4, 36034, "primitive:long", -1),
            (1081, 1, 30609, "primitive:uchar", 1),
            (1116, 1, 30762, "primitive:uchar", 1),
            (1189, 8, 30831, "primitive:double", float.fromhex("0x1.776793ed35a44p-6")),
            (1199, 2, 32508, "primitive:ushort", 0),
            (1201, 2, 32533, "primitive:ushort", 0),
            (1203, 4, 32610, "primitive:ulong", 121),
            (1225, 4, 32669, "primitive:long", 0),
            (1229, 1, 32833, "primitive:uchar", 0),
            (1230, 1, 32975, "primitive:uchar", 0),
            (1231, 4, 33297, "primitive:long", 0),
            (1235, 4, 33493, "primitive:ulong", 102),
            (1241, 4, 33676, "primitive:long", 0),
            (1249, 4, 33934, "primitive:long", -1),
            (1255, 4, 34234, "primitive:long", 16),
            (1259, 4, 34293, "primitive:long", 0),
            (1265, 4, 34442, "primitive:long", 0),
            (1269, 4, 34516, "primitive:long", 0),
            (1273, 4, 34530, "primitive:long", 0),
            (1277, 4, 34664, "primitive:long", 0),
            (1281, 4, 34723, "primitive:long", 0),
            (1289, 4, 34839, "primitive:long", 0),
            (1390, 4, 35013, "primitive:long", 0),
            (1402, 4, 35422, "primitive:long", 0),
            (1406, 4, 35481, "primitive:long", 0),
            (1410, 4, 35540, "primitive:long", 0),
            (1414, 4, 35599, "primitive:ulong", 101),
            (1418, 4, 35658, "primitive:ulong", 102),
            (1422, 4, 35674, "primitive:ulong", 101),
            (1430, 4, 35943, "primitive:long", 0),
            (1434, 4, 35959, "primitive:long", 0),
            (1438, 4, 35975, "primitive:long", -1),
            (1442, 4, 36034, "primitive:long", -1),
        ),
        "Contents/Config-0-ResolvedFeatures": (
            (707, 2, 25791, "primitive:ushort", 0),
            (739, 4, 26469, "primitive:long", 90),
            (747, 4, 26636, "primitive:long", -1),
            (785, 2, 25791, "primitive:ushort", 0),
            (795, 4, 26469, "primitive:long", 85),
            (803, 4, 26636, "primitive:long", -1),
            (5486, 4, 8369, "primitive:long", 0),
            (5490, 4, 8515, "primitive:long", 0),
            (5494, 4, 8528, "primitive:long", 0),
        ),
    },
)
