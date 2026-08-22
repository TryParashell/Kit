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
            (5365, 2, 239, "primitive:ushort", 65534),
            (5367, 2, 334, "primitive:ushort", 0),
            (8125, 2, 239, "primitive:ushort", 65534),
            (8127, 2, 334, "primitive:ushort", 0),
            (8180, 2, 239, "primitive:ushort", 65534),
            (8182, 2, 334, "primitive:ushort", 0),
            (8235, 2, 239, "primitive:ushort", 65534),
            (8237, 2, 334, "primitive:ushort", 0),
            (8290, 2, 239, "primitive:ushort", 65534),
            (8292, 2, 334, "primitive:ushort", 0),
            (8345, 2, 239, "primitive:ushort", 65534),
            (8347, 2, 334, "primitive:ushort", 0),
            (8402, 2, 239, "primitive:ushort", 65534),
            (8404, 2, 334, "primitive:ushort", 0),
        ),
    },
)
