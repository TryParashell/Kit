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
            (23622, 4, 155, "primitive:long", 1),
            (23626, 4, 210, "primitive:long", 0),
        ),
        "Contents/Config-0-ResolvedFeatures": (
            (195, 4, 155, "primitive:long", 0),
            (199, 4, 210, "primitive:long", 0),
            (394, 4, 155, "primitive:long", 1),
            (398, 4, 210, "primitive:long", 0),
            (596, 4, 155, "primitive:long", 1),
            (600, 4, 210, "primitive:long", 0),
            (1240, 4, 155, "primitive:long", 1),
            (1244, 4, 210, "primitive:long", 0),
            (1439, 4, 155, "primitive:long", 1),
            (1443, 4, 210, "primitive:long", 0),
            (1661, 4, 155, "primitive:long", 1),
            (1665, 4, 210, "primitive:long", 0),
            (1669, 4, 376, "primitive:long", 1),
            (1868, 4, 155, "primitive:long", 1),
            (1872, 4, 210, "primitive:long", 0),
            (2142, 4, 155, "primitive:long", 1),
            (2146, 4, 210, "primitive:long", 0),
            (2337, 4, 155, "primitive:long", 1),
            (2341, 4, 210, "primitive:long", 0),
            (2718, 4, 155, "primitive:long", 1),
            (2722, 4, 210, "primitive:long", 0),
            (2912, 4, 155, "primitive:long", 1),
            (2916, 4, 210, "primitive:long", 0),
        ),
    },
)
