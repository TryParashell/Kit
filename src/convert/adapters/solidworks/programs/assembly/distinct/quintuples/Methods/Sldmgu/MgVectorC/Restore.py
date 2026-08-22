# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Sldmgu.MgVectorC.Restore import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "Contents/CMgr": (
            (565, 8, 28, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (573, 8, 41, "primitive:double", float.fromhex("0x0.0p+0")),
            (589, 8, 28, "primitive:double", float.fromhex("0x0.0p+0")),
            (597, 8, 41, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (613, 8, 28, "primitive:double", float.fromhex("0x0.0p+0")),
            (621, 8, 41, "primitive:double", float.fromhex("0x0.0p+0")),
        ),
        "Contents/Config-0": (
            (20309, 8, 28, "primitive:double", float.fromhex("0x0.0p+0")),
            (20317, 8, 41, "primitive:double", float.fromhex("0x0.0p+0")),
            (22971, 8, 28, "primitive:double", float.fromhex("0x1.c666666666666p+2")),
            (22979, 8, 41, "primitive:double", float.fromhex("0x1.c666666666666p+2")),
            (23292, 8, 28, "primitive:double", float.fromhex("-0x1.b333333333333p+1")),
            (23300, 8, 41, "primitive:double", float.fromhex("0x1.8666666666666p+2")),
            (23613, 8, 28, "primitive:double", float.fromhex("-0x1.2666666666666p+3")),
            (23621, 8, 41, "primitive:double", float.fromhex("0x1.b333333333333p+1")),
        ),
        "Contents/Config-0-ResolvedFeatures": (
            (3258, 8, 28, "primitive:double", float.fromhex("0x0.0p+0")),
            (3266, 8, 41, "primitive:double", float.fromhex("0x0.0p+0")),
            (3752, 8, 28, "primitive:double", float.fromhex("0x0.0p+0")),
            (3760, 8, 41, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (4322, 8, 28, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (4330, 8, 41, "primitive:double", float.fromhex("0x0.0p+0")),
        ),
    },
)
