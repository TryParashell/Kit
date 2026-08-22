# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoFolderC.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (195, 4, 155, "primitive:long", 0),
            (199, 4, 210, "primitive:long", 0),
            (394, 4, 155, "primitive:long", 1),
            (398, 4, 210, "primitive:long", 0),
            (596, 4, 155, "primitive:long", 1),
            (600, 4, 210, "primitive:long", 0),
            (1571, 4, 155, "primitive:long", 1),
            (1575, 4, 210, "primitive:long", 0),
            (1770, 4, 155, "primitive:long", 1),
            (1774, 4, 210, "primitive:long", 0),
            (1973, 4, 155, "primitive:long", 1),
            (1977, 4, 210, "primitive:long", 0),
            (2247, 4, 155, "primitive:long", 1),
            (2251, 4, 210, "primitive:long", 0),
            (2442, 4, 155, "primitive:long", 1),
            (2446, 4, 210, "primitive:long", 0),
            (2837, 4, 155, "primitive:long", 1),
            (2841, 4, 210, "primitive:long", 0),
            (3055, 4, 155, "primitive:long", 1),
            (3059, 4, 210, "primitive:long", 0),
            (3265, 4, 155, "primitive:long", 1),
            (3269, 4, 210, "primitive:long", 0),
            (3459, 4, 155, "primitive:long", 1),
            (3463, 4, 210, "primitive:long", 0),
            (3688, 4, 155, "primitive:long", 1),
            (3692, 4, 210, "primitive:long", 0),
            (3700, 4, 640, "primitive:long", 0),
        ),
    },
)
