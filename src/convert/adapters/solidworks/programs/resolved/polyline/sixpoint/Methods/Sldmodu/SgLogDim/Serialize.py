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
            (8145, 2, 239, "primitive:ushort", 65534),
            (8147, 2, 334, "primitive:ushort", 0),
            (8200, 2, 239, "primitive:ushort", 65534),
            (8202, 2, 334, "primitive:ushort", 0),
            (8255, 2, 239, "primitive:ushort", 65534),
            (8257, 2, 334, "primitive:ushort", 0),
            (8310, 2, 239, "primitive:ushort", 65534),
            (8312, 2, 334, "primitive:ushort", 0),
            (8365, 2, 239, "primitive:ushort", 65534),
            (8367, 2, 334, "primitive:ushort", 0),
            (8420, 2, 239, "primitive:ushort", 65534),
            (8422, 2, 334, "primitive:ushort", 0),
            (8477, 2, 239, "primitive:ushort", 65534),
            (8479, 2, 334, "primitive:ushort", 0),
        ),
    },
)
