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
            (16453, 4, 373, "primitive:long", 0),
            (16497, 1, 538, "primitive:uchar", 0),
            (16498, 1, 558, "primitive:uchar", 0),
            (16499, 1, 578, "primitive:uchar", 0),
            (16500, 1, 598, "primitive:uchar", 0),
            (16501, 4, 618, "primitive:long", 0),
            (16505, 1, 637, "primitive:uchar", 0),
            (16506, 1, 660, "primitive:uchar", 0),
            (16507, 1, 683, "primitive:uchar", 0),
            (16508, 1, 722, "primitive:uchar", 0),
            (16509, 8, 764, "primitive:double", float.fromhex("0x0.0p+0")),
            (16517, 1, 777, "primitive:uchar", 1),
            (16606, 1, 860, "primitive:uchar", 0),
            (16607, 1, 939, "primitive:uchar", 0),
            (16747, 4, 1055, "primitive:int", 0),
            (16751, 8, 1074, "primitive:double", float.fromhex("0x1.921fb54442d28p-1")),
            (17566, 4, 373, "primitive:long", 0),
            (17610, 1, 538, "primitive:uchar", 0),
            (17611, 1, 558, "primitive:uchar", 0),
            (17612, 1, 578, "primitive:uchar", 0),
            (17613, 1, 598, "primitive:uchar", 0),
            (17614, 4, 618, "primitive:long", 0),
            (17618, 1, 637, "primitive:uchar", 0),
            (17619, 1, 660, "primitive:uchar", 0),
            (17620, 1, 683, "primitive:uchar", 0),
            (17621, 1, 722, "primitive:uchar", 0),
            (17622, 8, 764, "primitive:double", float.fromhex("0x0.0p+0")),
            (17630, 1, 777, "primitive:uchar", 1),
            (17719, 1, 860, "primitive:uchar", 0),
            (17720, 1, 939, "primitive:uchar", 0),
            (17860, 4, 1055, "primitive:int", 0),
            (17864, 8, 1074, "primitive:double", float.fromhex("0x1.921fb54442d28p-1")),
            (17872, 4, 373, "primitive:long", 0),
            (17916, 1, 538, "primitive:uchar", 0),
            (17917, 1, 558, "primitive:uchar", 0),
            (17918, 1, 578, "primitive:uchar", 0),
            (17919, 1, 598, "primitive:uchar", 0),
            (17920, 4, 618, "primitive:long", 0),
            (17924, 1, 637, "primitive:uchar", 0),
            (17925, 1, 660, "primitive:uchar", 0),
            (17926, 1, 683, "primitive:uchar", 0),
            (17927, 1, 722, "primitive:uchar", 0),
            (17928, 8, 764, "primitive:double", float.fromhex("0x0.0p+0")),
            (17936, 1, 777, "primitive:uchar", 1),
            (18025, 1, 860, "primitive:uchar", 0),
            (18026, 1, 939, "primitive:uchar", 0),
            (18166, 4, 1055, "primitive:int", 0),
            (18170, 8, 1074, "primitive:double", float.fromhex("0x1.921fb54442d28p-1")),
        ),
    },
)
