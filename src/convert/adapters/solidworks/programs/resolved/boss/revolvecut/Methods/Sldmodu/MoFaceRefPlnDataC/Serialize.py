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
            (9115, 4, 7121, "primitive:long", 1),
            (9143, 8, 7292, "primitive:double", float.fromhex("0x1.776793ed35a44p-5")),
            (15417, 4, 7121, "primitive:long", 1),
            (15445, 8, 7292, "primitive:double", float.fromhex("0x1.776793ed35a45p-5")),
            (15830, 8, 5803, "primitive:double", float.fromhex("0x0.0p+0")),
            (15838, 1, 5864, "primitive:uchar", 0),
        ),
    },
)
