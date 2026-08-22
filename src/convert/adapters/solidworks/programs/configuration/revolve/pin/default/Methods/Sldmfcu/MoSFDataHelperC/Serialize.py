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
        "Configuration": (
            (15997, 4, 373, "primitive:long", 0),
            (16041, 1, 538, "primitive:uchar", 0),
            (16042, 1, 558, "primitive:uchar", 0),
            (16043, 1, 578, "primitive:uchar", 0),
            (16044, 1, 598, "primitive:uchar", 0),
            (16045, 4, 618, "primitive:long", 0),
            (16049, 1, 637, "primitive:uchar", 0),
            (16050, 1, 660, "primitive:uchar", 0),
            (16051, 1, 683, "primitive:uchar", 0),
            (16052, 1, 722, "primitive:uchar", 0),
            (16053, 8, 764, "primitive:double", float.fromhex("0x0.0p+0")),
            (16061, 1, 777, "primitive:uchar", 1),
            (16150, 1, 860, "primitive:uchar", 0),
            (16151, 1, 939, "primitive:uchar", 0),
            (16291, 4, 1055, "primitive:int", 0),
            (16295, 8, 1074, "primitive:double", float.fromhex("0x1.921fb54442d28p-1")),
            (17110, 4, 373, "primitive:long", 0),
            (17154, 1, 538, "primitive:uchar", 0),
            (17155, 1, 558, "primitive:uchar", 0),
            (17156, 1, 578, "primitive:uchar", 0),
            (17157, 1, 598, "primitive:uchar", 0),
            (17158, 4, 618, "primitive:long", 0),
            (17162, 1, 637, "primitive:uchar", 0),
            (17163, 1, 660, "primitive:uchar", 0),
            (17164, 1, 683, "primitive:uchar", 0),
            (17165, 1, 722, "primitive:uchar", 0),
            (17166, 8, 764, "primitive:double", float.fromhex("0x0.0p+0")),
            (17174, 1, 777, "primitive:uchar", 1),
            (17263, 1, 860, "primitive:uchar", 0),
            (17264, 1, 939, "primitive:uchar", 0),
            (17404, 4, 1055, "primitive:int", 0),
            (17408, 8, 1074, "primitive:double", float.fromhex("0x1.921fb54442d28p-1")),
            (17416, 4, 373, "primitive:long", 0),
            (17460, 1, 538, "primitive:uchar", 0),
            (17461, 1, 558, "primitive:uchar", 0),
            (17462, 1, 578, "primitive:uchar", 0),
            (17463, 1, 598, "primitive:uchar", 0),
            (17464, 4, 618, "primitive:long", 0),
            (17468, 1, 637, "primitive:uchar", 0),
            (17469, 1, 660, "primitive:uchar", 0),
            (17470, 1, 683, "primitive:uchar", 0),
            (17471, 1, 722, "primitive:uchar", 0),
            (17472, 8, 764, "primitive:double", float.fromhex("0x0.0p+0")),
            (17480, 1, 777, "primitive:uchar", 1),
            (17569, 1, 860, "primitive:uchar", 0),
            (17570, 1, 939, "primitive:uchar", 0),
            (17710, 4, 1055, "primitive:int", 0),
            (17714, 8, 1074, "primitive:double", float.fromhex("0x1.921fb54442d28p-1")),
        ),
    },
)
