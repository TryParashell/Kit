# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Sldmgu.MgXformC.Restore import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "AnnotationManager": (
            (36, 1, 35, "primitive:uchar", 1),
            (109, 8, 67, "primitive:double", float.fromhex("0x0.0p+0")),
            (117, 8, 80, "primitive:double", float.fromhex("0x0.0p+0")),
            (125, 8, 93, "primitive:double", float.fromhex("0x0.0p+0")),
            (133, 8, 106, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (141, 1, 120, "primitive:uchar", 0),
            (142, 1, 35, "primitive:uchar", 0),
            (143, 8, 67, "primitive:double", float.fromhex("0x0.0p+0")),
            (151, 8, 80, "primitive:double", float.fromhex("0x0.0p+0")),
            (159, 8, 93, "primitive:double", float.fromhex("0x0.0p+0")),
            (167, 8, 106, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (175, 1, 120, "primitive:uchar", 0),
            (296, 1, 35, "primitive:uchar", 0),
            (297, 8, 67, "primitive:double", float.fromhex("0x0.0p+0")),
            (305, 8, 80, "primitive:double", float.fromhex("0x0.0p+0")),
            (313, 8, 93, "primitive:double", float.fromhex("0x0.0p+0")),
            (321, 8, 106, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (329, 1, 120, "primitive:uchar", 0),
            (330, 1, 35, "primitive:uchar", 0),
            (331, 8, 67, "primitive:double", float.fromhex("0x0.0p+0")),
            (339, 8, 80, "primitive:double", float.fromhex("0x0.0p+0")),
            (347, 8, 93, "primitive:double", float.fromhex("0x0.0p+0")),
            (355, 8, 106, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (363, 1, 120, "primitive:uchar", 0),
        ),
    },
)
