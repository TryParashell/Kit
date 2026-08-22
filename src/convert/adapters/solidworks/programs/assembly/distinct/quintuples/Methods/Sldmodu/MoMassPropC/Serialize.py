# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoMassPropC.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "Contents/CMgr": (
            (389, 8, 724, "primitive:double", float.fromhex("0x0.0p+0")),
            (397, 8, 737, "primitive:double", float.fromhex("0x0.0p+0")),
            (405, 8, 750, "primitive:double", float.fromhex("0x0.0p+0")),
            (413, 8, 783, "primitive:double", float.fromhex("0x0.0p+0")),
            (421, 8, 796, "primitive:double", float.fromhex("0x0.0p+0")),
            (429, 8, 809, "primitive:double", float.fromhex("0x0.0p+0")),
            (437, 8, 822, "primitive:double", float.fromhex("0x0.0p+0")),
            (445, 8, 835, "primitive:double", float.fromhex("0x0.0p+0")),
            (453, 8, 848, "primitive:double", float.fromhex("0x0.0p+0")),
            (461, 8, 861, "primitive:double", float.fromhex("0x0.0p+0")),
            (469, 8, 874, "primitive:double", float.fromhex("0x0.0p+0")),
            (477, 8, 887, "primitive:double", float.fromhex("0x0.0p+0")),
            (485, 4, 952, "primitive:long", 1),
            (489, 4, 1017, "primitive:long", 0),
            (493, 4, 1082, "primitive:long", 0),
            (497, 4, 1149, "primitive:long", 0),
            (501, 4, 1236, "primitive:long", 0),
            (505, 8, 1430, "primitive:double", float.fromhex("0x0.0p+0")),
            (513, 4, 1499, "primitive:long", 0),
            (517, 4, 1515, "primitive:long", 0),
            (521, 4, 1531, "primitive:long", 0),
            (525, 4, 1547, "primitive:long", 0),
            (537, 4, 1728, "primitive:long", 0),
            (541, 8, 1843, "primitive:double", float.fromhex("0x0.0p+0")),
            (549, 8, 1859, "primitive:double", float.fromhex("0x0.0p+0")),
            (557, 8, 1875, "primitive:double", float.fromhex("0x0.0p+0")),
            (581, 8, 1979, "primitive:double", float.fromhex("0x0.0p+0")),
            (605, 8, 1995, "primitive:double", float.fromhex("0x0.0p+0")),
            (629, 8, 2011, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (637, 4, 2089, "primitive:long", 1),
            (641, 2, 2140, "primitive:ushort", 0),
        ),
    },
)
