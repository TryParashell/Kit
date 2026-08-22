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
            (8915, 4, 3177, "primitive:long", 0),
            (8919, 4, 3190, "primitive:long", 0),
            (8929, 4, 3307, "primitive:long", 0),
        ),
    },
)
