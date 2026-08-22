# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Sldmodu.SgLogGThreeDim.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "Contents/Config-0-ResolvedFeatures": (
            (4724, 2, 13751, "primitive:ushort", 31),
            (4742, 2, 13906, "primitive:ushort", 1),
            (4744, 2, 13996, "primitive:ushort", 0),
            (4750, 2, 14480, "primitive:ushort", 0),
            (4752, 4, 14546, "primitive:long", -2),
            (4788, 2, 14739, "primitive:ushort", 0),
            (4790, 2, 14916, "primitive:ushort", 0),
            (5128, 4, 2988, "primitive:long", 0),
        ),
    },
)
