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
            (3557, 4, 13613, "primitive:long", 5),
            (3561, 4, 13784, "primitive:long", 0),
            (3567, 4, 13933, "primitive:long", 0),
            (4076, 4, 13613, "primitive:long", 5),
            (4080, 4, 13784, "primitive:long", 0),
            (4086, 4, 13933, "primitive:long", 0),
            (4646, 4, 13613, "primitive:long", 5),
            (4650, 4, 13784, "primitive:long", 0),
            (4656, 4, 13933, "primitive:long", 0),
            (6584, 2, 16845, "primitive:ushort", 0),
            (6588, 4, 17007, "primitive:long", 0),
            (6592, 4, 17062, "primitive:long", 102),
            (6596, 2, 17130, "primitive:ushort", 0),
            (6598, 2, 17256, "primitive:ushort", 0),
            (6600, 4, 17382, "primitive:long", 0),
            (6604, 4, 17599, "primitive:long", 0),
            (6608, 4, 17717, "primitive:long", -12345),
            (6612, 4, 17736, "primitive:long", -12345),
            (6616, 4, 17797, "primitive:long", -12345),
            (6620, 4, 17953, "primitive:long", 0),
            (6624, 4, 18072, "primitive:long", 18000),
            (6628, 4, 18195, "primitive:long", 0),
            (6632, 4, 18208, "primitive:long", 0),
            (6636, 4, 18380, "primitive:long", 0),
            (6640, 4, 18442, "primitive:long", -1),
            (9829, 4, 3177, "primitive:long", 0),
            (9833, 4, 3190, "primitive:long", 0),
            (10090, 2, 16845, "primitive:ushort", 1),
            (10094, 4, 17007, "primitive:long", 0),
            (10098, 4, 17062, "primitive:long", 104),
            (10102, 2, 17130, "primitive:ushort", 0),
            (10104, 2, 17256, "primitive:ushort", 0),
            (10106, 4, 17382, "primitive:long", 0),
            (10110, 4, 17599, "primitive:long", 0),
            (10114, 4, 17717, "primitive:long", -12345),
            (10118, 4, 17736, "primitive:long", -12345),
            (10122, 4, 17797, "primitive:long", -12345),
            (10126, 4, 17953, "primitive:long", 0),
            (10130, 4, 18072, "primitive:long", 18000),
            (10134, 4, 18195, "primitive:long", 0),
            (10138, 4, 18208, "primitive:long", 0),
            (10142, 4, 18380, "primitive:long", 0),
            (10146, 4, 18442, "primitive:long", -1),
        ),
    },
)
