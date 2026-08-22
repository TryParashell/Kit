# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoViewC.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "AnnotationManager": (
            (176, 2, 573, "primitive:ushort", 0),
            (178, 4, 599, "primitive:long", -1),
            (182, 8, 664, "primitive:double", float.fromhex("-0x1.0000000000000p+0")),
            (190, 4, 760, "primitive:long", 0),
            (194, 4, 990, "primitive:long", 200),
            (198, 4, 1128, "primitive:long", 0),
            (202, 4, 1141, "primitive:long", 0),
            (206, 4, 1309, "primitive:long", 0),
            (210, 8, 1325, "primitive:double", float.fromhex("0x0.0p+0")),
            (218, 4, 1338, "primitive:long", 0),
            (222, 4, 1511, "primitive:long", 0),
            (226, 4, 1569, "primitive:long", 0),
            (436, 2, 573, "primitive:ushort", 0),
            (438, 4, 599, "primitive:long", -1),
            (442, 8, 664, "primitive:double", float.fromhex("-0x1.0000000000000p+0")),
            (450, 4, 760, "primitive:long", 0),
            (454, 4, 990, "primitive:long", 201),
            (458, 4, 1128, "primitive:long", 0),
            (462, 4, 1141, "primitive:long", 0),
            (466, 4, 1309, "primitive:long", 0),
            (470, 8, 1325, "primitive:double", float.fromhex("0x0.0p+0")),
            (478, 4, 1338, "primitive:long", 0),
            (482, 4, 1511, "primitive:long", 0),
            (486, 4, 1569, "primitive:long", 0),
        ),
    },
)
