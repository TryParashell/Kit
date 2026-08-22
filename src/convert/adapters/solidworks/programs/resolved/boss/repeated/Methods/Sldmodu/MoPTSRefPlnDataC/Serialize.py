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
            (14477, 4, 3177, "primitive:long", 0),
            (14481, 4, 3190, "primitive:long", 0),
        ),
    },
)
