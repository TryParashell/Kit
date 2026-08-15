# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Sldmodu.DimensionC.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "Contents/Config-0-ResolvedFeatures": (
            (4850, 4, 1100, "primitive:long", 0),
            (4858, 4, 1380, "primitive:long", -1),
            (4862, 4, 1530, "primitive:long", 0),
            (4866, 4, 1592, "primitive:long", 0),
            (4870, 4, 1658, "primitive:long", 0),
            (4876, 2, 1826, "primitive:ushort", 0),
            (4878, 1, 1895, "primitive:uchar", 0),
        ),
    },
)
