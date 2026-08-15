# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoRefSurfaceC.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (10145, 1, 4024, "primitive:uchar", 0),
            (10148, 4, 4122, "primitive:long", 0),
            (10156, 4, 4309, "primitive:long", 3),
            (10160, 4, 4571, "primitive:long", 1),
            (10437, 4, 2857, "primitive:long", 0),
            (10441, 4, 2873, "primitive:long", 0),
            (10445, 4, 2889, "primitive:long", 0),
            (10449, 4, 2902, "primitive:long", 0),
            (10453, 4, 2915, "primitive:long", 0),
            (10465, 8, 2988, "primitive:double", float.fromhex("0x1.47ae147ae147bp-7")),
            (10473, 8, 3001, "primitive:double", float.fromhex("0x1.47ae147ae147bp-7")),
            (10481, 4, 3017, "primitive:long", 0),
            (10485, 4, 3033, "primitive:long", 0),
            (14060, 1, 4924, "primitive:uchar", 0),
        ),
    },
)
