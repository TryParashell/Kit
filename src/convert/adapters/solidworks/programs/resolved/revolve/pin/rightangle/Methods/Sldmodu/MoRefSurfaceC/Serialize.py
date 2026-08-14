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
            (10345, 1, 4024, "primitive:uchar", 0),
            (10348, 4, 4122, "primitive:long", 0),
            (10356, 4, 4309, "primitive:long", 3),
            (10360, 4, 4571, "primitive:long", 1),
            (10637, 4, 2857, "primitive:long", 1),
            (10641, 4, 2873, "primitive:long", 0),
            (10645, 4, 2889, "primitive:long", 0),
            (10649, 4, 2902, "primitive:long", 0),
            (10653, 4, 2915, "primitive:long", 0),
            (10665, 8, 2988, "primitive:double", float.fromhex("0x1.47ae147ae147bp-7")),
            (10673, 8, 3001, "primitive:double", float.fromhex("0x1.47ae147ae147bp-7")),
            (10681, 4, 3017, "primitive:long", 0),
            (10685, 4, 3033, "primitive:long", 0),
            (12532, 1, 4924, "primitive:uchar", 0),
        ),
    },
)
