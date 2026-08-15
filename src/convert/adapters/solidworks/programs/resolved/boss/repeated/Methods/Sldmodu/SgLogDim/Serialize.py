# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Sldmodu.SgLogDim.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (5603, 2, 239, "primitive:ushort", 65534),
            (5605, 2, 334, "primitive:ushort", 0),
            (7502, 2, 239, "primitive:ushort", 65534),
            (7504, 2, 334, "primitive:ushort", 0),
            (7557, 2, 239, "primitive:ushort", 65534),
            (7559, 2, 334, "primitive:ushort", 0),
            (7612, 2, 239, "primitive:ushort", 65534),
            (7614, 2, 334, "primitive:ushort", 0),
            (7667, 2, 239, "primitive:ushort", 65534),
            (7669, 2, 334, "primitive:ushort", 0),
            (12697, 2, 239, "primitive:ushort", 65534),
            (12699, 2, 334, "primitive:ushort", 0),
            (12752, 2, 239, "primitive:ushort", 65534),
            (12754, 2, 334, "primitive:ushort", 0),
            (12807, 2, 239, "primitive:ushort", 65534),
            (12809, 2, 334, "primitive:ushort", 0),
            (12862, 2, 239, "primitive:ushort", 65534),
            (12864, 2, 334, "primitive:ushort", 0),
        ),
    },
)
