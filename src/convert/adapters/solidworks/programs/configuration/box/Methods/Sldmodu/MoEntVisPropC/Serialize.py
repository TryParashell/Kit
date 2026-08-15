# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoEntVisPropC.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "Configuration": (
            (20713, 2, 122, "primitive:ushort", 65535),
            (20715, 2, 135, "primitive:ushort", 0),
            (20717, 1, 188, "primitive:uchar", 3),
            (21016, 2, 122, "primitive:ushort", 65535),
            (21018, 2, 135, "primitive:ushort", 0),
            (21020, 1, 188, "primitive:uchar", 3),
            (21337, 2, 122, "primitive:ushort", 65535),
            (21339, 2, 135, "primitive:ushort", 0),
            (21341, 1, 188, "primitive:uchar", 3),
            (21658, 2, 122, "primitive:ushort", 65535),
            (21660, 2, 135, "primitive:ushort", 0),
            (21662, 1, 188, "primitive:uchar", 3),
            (21919, 2, 122, "primitive:ushort", 65535),
            (21921, 2, 135, "primitive:ushort", 0),
            (21923, 1, 188, "primitive:uchar", 3),
            (24175, 2, 122, "primitive:ushort", 65535),
            (24177, 2, 135, "primitive:ushort", 0),
            (24179, 1, 188, "primitive:uchar", 3),
            (25037, 2, 122, "primitive:ushort", 65535),
            (25039, 2, 135, "primitive:ushort", 0),
            (25041, 1, 188, "primitive:uchar", 3),
        ),
    },
)
