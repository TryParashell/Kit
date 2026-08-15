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
            (1214, 4, 155, "primitive:long", 1),
            (1218, 4, 210, "primitive:long", 0),
            (1413, 4, 155, "primitive:long", 1),
            (1417, 4, 210, "primitive:long", 0),
            (1616, 4, 155, "primitive:long", 1),
            (1620, 4, 210, "primitive:long", 0),
            (1890, 4, 155, "primitive:long", 1),
            (1894, 4, 210, "primitive:long", 0),
            (2085, 4, 155, "primitive:long", 1),
            (2089, 4, 210, "primitive:long", 0),
            (2480, 4, 155, "primitive:long", 1),
            (2484, 4, 210, "primitive:long", 0),
            (2698, 4, 155, "primitive:long", 1),
            (2702, 4, 210, "primitive:long", 0),
            (2908, 4, 155, "primitive:long", 1),
            (2912, 4, 210, "primitive:long", 0),
            (3102, 4, 155, "primitive:long", 1),
            (3106, 4, 210, "primitive:long", 0),
            (3331, 4, 155, "primitive:long", 1),
            (3335, 4, 210, "primitive:long", 0),
            (3343, 4, 640, "primitive:long", 0),
        ),
    },
)
