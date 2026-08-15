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
            (13558, 2, 239, "primitive:ushort", 65534),
            (13560, 2, 334, "primitive:ushort", 0),
            (13613, 2, 239, "primitive:ushort", 65534),
            (13615, 2, 334, "primitive:ushort", 0),
            (13668, 2, 239, "primitive:ushort", 65534),
            (13670, 2, 334, "primitive:ushort", 0),
            (13723, 2, 239, "primitive:ushort", 65534),
            (13725, 2, 334, "primitive:ushort", 0),
            (13778, 2, 239, "primitive:ushort", 65534),
            (13780, 2, 334, "primitive:ushort", 0),
            (13835, 2, 239, "primitive:ushort", 65534),
            (13837, 2, 334, "primitive:ushort", 0),
            (13942, 2, 239, "primitive:ushort", 65534),
            (13944, 2, 334, "primitive:ushort", 0),
        ),
    },
)
