# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoFaceRefPlnDataC.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (9591, 4, 7121, "primitive:long", 1),
            (9619, 8, 7292, "primitive:double", float.fromhex("0x1.1b11a14904e08p-4")),
            (14915, 4, 7121, "primitive:long", 1),
            (14943, 8, 7292, "primitive:double", float.fromhex("0x1.1b11a14904e08p-4")),
            (19985, 4, 7121, "primitive:long", 1),
            (20013, 8, 7292, "primitive:double", float.fromhex("0x1.1b11a14904e08p-4")),
            (25059, 4, 7121, "primitive:long", 1),
            (25087, 8, 7292, "primitive:double", float.fromhex("0x1.1b11a14904e08p-4")),
        ),
    },
)
