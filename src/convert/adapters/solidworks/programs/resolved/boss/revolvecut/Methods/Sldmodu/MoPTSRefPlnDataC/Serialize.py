# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoPTSRefPlnDataC.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (3795, 4, 13613, "primitive:long", 5),
            (3799, 4, 13784, "primitive:long", 0),
            (3805, 4, 13933, "primitive:long", 0),
            (4314, 4, 13613, "primitive:long", 5),
            (4318, 4, 13784, "primitive:long", 0),
            (4324, 4, 13933, "primitive:long", 0),
            (4884, 4, 13613, "primitive:long", 5),
            (4888, 4, 13784, "primitive:long", 0),
            (4894, 4, 13933, "primitive:long", 0),
            (9151, 4, 3177, "primitive:long", 0),
            (9155, 4, 3190, "primitive:long", 0),
            (9165, 4, 3307, "primitive:long", 0),
            (12017, 2, 16845, "primitive:ushort", 0),
            (12021, 4, 17007, "primitive:long", 0),
            (12025, 4, 17062, "primitive:long", 106),
            (12029, 2, 17130, "primitive:ushort", 0),
            (12031, 2, 17256, "primitive:ushort", 0),
            (12033, 4, 17382, "primitive:long", 0),
            (12037, 4, 17599, "primitive:long", 0),
            (12041, 4, 17717, "primitive:long", -12345),
            (12045, 4, 17736, "primitive:long", -12345),
            (12049, 4, 17797, "primitive:long", -12345),
            (12053, 4, 17953, "primitive:long", 0),
            (12057, 4, 18072, "primitive:long", 18000),
            (12061, 4, 18195, "primitive:long", 0),
            (12065, 4, 18208, "primitive:long", 0),
            (12069, 4, 18380, "primitive:long", 0),
            (12073, 4, 18442, "primitive:long", -1),
            (15453, 4, 3177, "primitive:long", 0),
            (15457, 4, 3190, "primitive:long", 0),
            (15714, 2, 16845, "primitive:ushort", 1),
            (15718, 4, 17007, "primitive:long", 0),
            (15722, 4, 17062, "primitive:long", 108),
            (15726, 2, 17130, "primitive:ushort", 0),
            (15728, 2, 17256, "primitive:ushort", 0),
            (15730, 4, 17382, "primitive:long", 0),
            (15734, 4, 17599, "primitive:long", 0),
            (15738, 4, 17717, "primitive:long", -12345),
            (15742, 4, 17736, "primitive:long", -12345),
            (15746, 4, 17797, "primitive:long", -12345),
            (15750, 4, 17953, "primitive:long", 0),
            (15754, 4, 18072, "primitive:long", 18000),
            (15758, 4, 18195, "primitive:long", 0),
            (15762, 4, 18208, "primitive:long", 0),
            (15766, 4, 18380, "primitive:long", 0),
            (15770, 4, 18442, "primitive:long", -1),
        ),
    },
)
