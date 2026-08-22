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
        "Contents/Config-0": (
            (21844, 4, 155, "primitive:long", 1),
            (21848, 4, 210, "primitive:long", 0),
        ),
        "Contents/Config-0-ResolvedFeatures": (
            (195, 4, 155, "primitive:long", 0),
            (199, 4, 210, "primitive:long", 0),
            (394, 4, 155, "primitive:long", 1),
            (398, 4, 210, "primitive:long", 0),
            (596, 4, 155, "primitive:long", 1),
            (600, 4, 210, "primitive:long", 0),
            (960, 4, 155, "primitive:long", 1),
            (964, 4, 210, "primitive:long", 0),
            (1159, 4, 155, "primitive:long", 1),
            (1163, 4, 210, "primitive:long", 0),
            (1381, 4, 155, "primitive:long", 1),
            (1385, 4, 210, "primitive:long", 0),
            (1389, 4, 376, "primitive:long", 1),
            (1588, 4, 155, "primitive:long", 1),
            (1592, 4, 210, "primitive:long", 0),
            (1862, 4, 155, "primitive:long", 1),
            (1866, 4, 210, "primitive:long", 0),
            (2057, 4, 155, "primitive:long", 1),
            (2061, 4, 210, "primitive:long", 0),
            (2438, 4, 155, "primitive:long", 1),
            (2442, 4, 210, "primitive:long", 0),
            (2632, 4, 155, "primitive:long", 1),
            (2636, 4, 210, "primitive:long", 0),
        ),
    },
)
