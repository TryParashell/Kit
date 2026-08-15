# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Owners.Sldmodu.MoRefSurfaceC.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (15567, 1, 4024, "primitive:uchar", 0),
            (15570, 4, 4122, "primitive:long", 0),
            (15578, 4, 4309, "primitive:long", 3),
            (15582, 4, 4571, "primitive:long", 1),
            (15859, 4, 2857, "primitive:long", 1),
            (15863, 4, 2873, "primitive:long", 0),
            (15867, 4, 2889, "primitive:long", 0),
            (15871, 4, 2902, "primitive:long", 0),
            (15875, 4, 2915, "primitive:long", 0),
            (15887, 8, 2988, "primitive:double", float.fromhex("0x1.47ae147ae147bp-7")),
            (15895, 8, 3001, "primitive:double", float.fromhex("0x1.47ae147ae147bp-7")),
            (15903, 4, 3017, "primitive:long", 0),
            (15907, 4, 3033, "primitive:long", 0),
            (17708, 1, 4924, "primitive:uchar", 0),
        ),
    },
)
