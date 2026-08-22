# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoDisplayItemC.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (9100, 2, 7349, "primitive:ushort", 0),
            (9108, 4, 7550, "primitive:long", 0),
            (9112, 4, 7718, "primitive:long", 0),
            (9137, 4, 7917, "primitive:long", 0),
            (9143, 4, 8109, "primitive:long", 0),
            (9147, 4, 8386, "primitive:long", 18000),
            (9151, 4, 1016, "primitive:long", 0),
            (9155, 4, 1055, "primitive:long", 524416),
            (9187, 4, 1275, "primitive:long", 0),
            (9209, 8, 1602, "primitive:double", float.fromhex("0x0.0p+0")),
            (9251, 4, 1650, "primitive:long", 1),
            (9255, 4, 1685, "primitive:long", 200),
            (9259, 1, 1897, "primitive:uchar", 0),
            (9260, 8, 1990, "primitive:double", float.fromhex("0x0.0p+0")),
            (9268, 4, 2003, "primitive:long", 0),
            (9272, 4, 2121, "primitive:long", 0),
            (9278, 8, 2319, "primitive:double", float.fromhex("-0x1.0000000000000p+0")),
            (9286, 4, 2666, "primitive:long", 0),
            (9290, 4, 3709, "primitive:long", 1),
            (9300, 4, 3748, "primitive:long", 0),
            (9304, 4, 3764, "primitive:long", 1),
            (9314, 4, 3803, "primitive:long", 0),
            (9318, 4, 3943, "primitive:long", 0),
            (9322, 4, 3959, "primitive:long", 0),
            (9326, 4, 3976, "primitive:long", -1),
            (9330, 4, 4005, "primitive:long", -1),
            (9338, 4, 4272, "primitive:long", 1),
            (9342, 4, 4288, "primitive:long", 0),
            (9352, 4, 4326, "primitive:long", 0),
            (9356, 4, 4410, "primitive:long", 0),
            (9360, 4, 4891, "primitive:long", 0),
            (9364, 4, 5194, "primitive:long", 0),
            (9368, 4, 5593, "primitive:long", 4),
            (9468, 4, 5761, "primitive:long", 2),
            (9488, 8, 5816, "primitive:double", float.fromhex("0x0.0p+0")),
            (9512, 8, 5816, "primitive:double", float.fromhex("0x0.0p+0")),
        ),
    },
)
