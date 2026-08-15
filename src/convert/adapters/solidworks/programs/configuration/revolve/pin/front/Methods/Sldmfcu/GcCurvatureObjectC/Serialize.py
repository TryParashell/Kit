# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Sldmfcu.GcCurvatureObjectC.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "Configuration": (
            (2276, 8, 140, "primitive:double", float.fromhex("0x1.f400000000000p+9")),
            (2284, 8, 140, "primitive:double", float.fromhex("0x1.f99999999999ap+4")),
            (2292, 8, 140, "primitive:double", float.fromhex("0x1.0000000000000p+2")),
            (2300, 8, 140, "primitive:double", float.fromhex("0x1.3333333333333p+0")),
            (2308, 8, 140, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (2316, 4, 182, "primitive:ulong", 2264523360),
            (2320, 4, 195, "primitive:ulong", 31270090),
        ),
    },
)
