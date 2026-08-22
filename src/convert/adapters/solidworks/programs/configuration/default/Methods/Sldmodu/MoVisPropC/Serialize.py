# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoVisPropC.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "Configuration": (
            (20688, 4, 77, "primitive:ulong", 4294967295),
            (20692, 2, 90, "primitive:ushort", 65535),
            (20991, 4, 77, "primitive:ulong", 4294967295),
            (20995, 2, 90, "primitive:ushort", 65535),
            (21312, 4, 77, "primitive:ulong", 4294967295),
            (21316, 2, 90, "primitive:ushort", 65535),
            (21633, 4, 77, "primitive:ulong", 4294967295),
            (21637, 2, 90, "primitive:ushort", 65535),
            (21894, 4, 77, "primitive:ulong", 4294967295),
            (21898, 2, 90, "primitive:ushort", 65535),
            (24150, 4, 77, "primitive:ulong", 4294967295),
            (24154, 2, 90, "primitive:ushort", 65535),
            (25098, 4, 77, "primitive:ulong", 4294967295),
            (25102, 2, 90, "primitive:ushort", 65535),
        ),
    },
)
