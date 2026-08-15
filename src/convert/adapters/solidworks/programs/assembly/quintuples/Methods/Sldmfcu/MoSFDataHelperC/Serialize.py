# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Sldmfcu.MoSFDataHelperC.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "Contents/Config-0": (
            (18235, 4, 373, "primitive:long", 0),
            (18279, 1, 538, "primitive:uchar", 0),
            (18280, 1, 558, "primitive:uchar", 0),
            (18281, 1, 578, "primitive:uchar", 0),
            (18282, 1, 598, "primitive:uchar", 0),
            (18283, 4, 618, "primitive:long", 0),
            (18287, 1, 637, "primitive:uchar", 0),
            (18288, 1, 660, "primitive:uchar", 0),
            (18289, 1, 683, "primitive:uchar", 0),
            (18290, 1, 722, "primitive:uchar", 0),
            (18291, 8, 764, "primitive:double", float.fromhex("0x0.0p+0")),
            (18299, 1, 777, "primitive:uchar", 1),
            (18388, 1, 860, "primitive:uchar", 0),
            (18389, 1, 939, "primitive:uchar", 0),
            (18529, 4, 1055, "primitive:int", 0),
            (18533, 8, 1074, "primitive:double", float.fromhex("0x1.921fb54442d28p-1")),
            (19348, 4, 373, "primitive:long", 0),
            (19392, 1, 538, "primitive:uchar", 0),
            (19393, 1, 558, "primitive:uchar", 0),
            (19394, 1, 578, "primitive:uchar", 0),
            (19395, 1, 598, "primitive:uchar", 0),
            (19396, 4, 618, "primitive:long", 0),
            (19400, 1, 637, "primitive:uchar", 0),
            (19401, 1, 660, "primitive:uchar", 0),
            (19402, 1, 683, "primitive:uchar", 0),
            (19403, 1, 722, "primitive:uchar", 0),
            (19404, 8, 764, "primitive:double", float.fromhex("0x0.0p+0")),
            (19412, 1, 777, "primitive:uchar", 1),
            (19501, 1, 860, "primitive:uchar", 0),
            (19502, 1, 939, "primitive:uchar", 0),
            (19642, 4, 1055, "primitive:int", 0),
            (19646, 8, 1074, "primitive:double", float.fromhex("0x1.921fb54442d28p-1")),
            (19654, 4, 373, "primitive:long", 0),
            (19698, 1, 538, "primitive:uchar", 0),
            (19699, 1, 558, "primitive:uchar", 0),
            (19700, 1, 578, "primitive:uchar", 0),
            (19701, 1, 598, "primitive:uchar", 0),
            (19702, 4, 618, "primitive:long", 0),
            (19706, 1, 637, "primitive:uchar", 0),
            (19707, 1, 660, "primitive:uchar", 0),
            (19708, 1, 683, "primitive:uchar", 0),
            (19709, 1, 722, "primitive:uchar", 0),
            (19710, 8, 764, "primitive:double", float.fromhex("0x0.0p+0")),
            (19718, 1, 777, "primitive:uchar", 1),
            (19807, 1, 860, "primitive:uchar", 0),
            (19808, 1, 939, "primitive:uchar", 0),
            (19948, 4, 1055, "primitive:int", 0),
            (19952, 8, 1074, "primitive:double", float.fromhex("0x1.921fb54442d28p-1")),
        ),
    },
)
