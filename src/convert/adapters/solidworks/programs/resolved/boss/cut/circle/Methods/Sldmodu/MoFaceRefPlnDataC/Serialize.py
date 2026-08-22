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
            (9353, 4, 7121, "primitive:long", 1),
            (9381, 8, 7292, "primitive:double", float.fromhex("0x1.d69835def1fedp-4")),
            (14665, 4, 7121, "primitive:long", 1),
            (14693, 8, 7292, "primitive:double", float.fromhex("0x1.d69835def1fedp-4")),
            (18988, 4, 7121, "primitive:long", 1),
            (19016, 8, 7292, "primitive:double", float.fromhex("0x1.d69835def1fedp-4")),
        ),
    },
)
