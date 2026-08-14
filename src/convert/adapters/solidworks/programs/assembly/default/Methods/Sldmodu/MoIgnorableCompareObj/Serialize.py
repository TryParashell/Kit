# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Owners.Sldmodu.MoIgnorableCompareObj.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram = (
    KOwnerSites,
    {
        "Contents/CMgr": (
            (1385, 2, 25791, "primitive:ushort", 0),
            (1587, 4, 26469, "primitive:long", 0),
            (1595, 4, 26636, "primitive:long", -1),
        ),
        "Contents/Config-0": (
            (320, 1, 30609, "primitive:uchar", 1),
            (355, 1, 30762, "primitive:uchar", 1),
            (428, 8, 30831, "primitive:double", float.fromhex("0x1.776793ed35a44p-6")),
            (438, 2, 32508, "primitive:ushort", 3),
            (440, 2, 32533, "primitive:ushort", 0),
            (442, 4, 32610, "primitive:ulong", 121),
            (464, 4, 32669, "primitive:long", 0),
            (468, 1, 32833, "primitive:uchar", 0),
            (469, 1, 32975, "primitive:uchar", 0),
            (470, 4, 33297, "primitive:long", 0),
            (474, 4, 33493, "primitive:ulong", 102),
            (480, 4, 33676, "primitive:long", 0),
            (488, 4, 33934, "primitive:long", -1),
            (494, 4, 34234, "primitive:long", 15),
            (498, 4, 34293, "primitive:long", 0),
            (504, 4, 34442, "primitive:long", 0),
            (508, 4, 34516, "primitive:long", 0),
            (512, 4, 34530, "primitive:long", 0),
            (516, 4, 34664, "primitive:long", 0),
            (520, 4, 34723, "primitive:long", 0),
            (528, 4, 34839, "primitive:long", 0),
            (704, 4, 35013, "primitive:long", 0),
            (716, 4, 35422, "primitive:long", 0),
            (720, 4, 35481, "primitive:long", 0),
            (724, 4, 35540, "primitive:long", 0),
            (728, 4, 35599, "primitive:ulong", 101),
            (732, 4, 35658, "primitive:ulong", 102),
            (736, 4, 35674, "primitive:ulong", 101),
            (744, 4, 35943, "primitive:long", 0),
            (748, 4, 35959, "primitive:long", 0),
            (752, 4, 35975, "primitive:long", -1),
            (756, 4, 36034, "primitive:long", -1),
        ),
        "Contents/Config-0-ResolvedFeatures": (
            (707, 2, 25791, "primitive:ushort", 0),
            (739, 4, 26469, "primitive:long", 20),
            (747, 4, 26636, "primitive:long", -1),
            (5430, 4, 8369, "primitive:long", 0),
            (5434, 4, 8515, "primitive:long", 0),
            (5438, 4, 8528, "primitive:long", 0),
        ),
    },
)
