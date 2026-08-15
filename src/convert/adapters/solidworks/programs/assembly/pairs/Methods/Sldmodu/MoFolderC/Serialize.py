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
            (22438, 4, 155, "primitive:long", 1),
            (22442, 4, 210, "primitive:long", 0),
        ),
        "Contents/Config-0-ResolvedFeatures": (
            (195, 4, 155, "primitive:long", 0),
            (199, 4, 210, "primitive:long", 0),
            (394, 4, 155, "primitive:long", 1),
            (398, 4, 210, "primitive:long", 0),
            (596, 4, 155, "primitive:long", 1),
            (600, 4, 210, "primitive:long", 0),
            (1016, 4, 155, "primitive:long", 1),
            (1020, 4, 210, "primitive:long", 0),
            (1215, 4, 155, "primitive:long", 1),
            (1219, 4, 210, "primitive:long", 0),
            (1437, 4, 155, "primitive:long", 1),
            (1441, 4, 210, "primitive:long", 0),
            (1445, 4, 376, "primitive:long", 1),
            (1644, 4, 155, "primitive:long", 1),
            (1648, 4, 210, "primitive:long", 0),
            (1918, 4, 155, "primitive:long", 1),
            (1922, 4, 210, "primitive:long", 0),
            (2113, 4, 155, "primitive:long", 1),
            (2117, 4, 210, "primitive:long", 0),
            (2494, 4, 155, "primitive:long", 1),
            (2498, 4, 210, "primitive:long", 0),
            (2688, 4, 155, "primitive:long", 1),
            (2692, 4, 210, "primitive:long", 0),
        ),
    },
)
