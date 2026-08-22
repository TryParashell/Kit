# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Swccu.SuCArchive.ReadCount import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "AnnotationManager": (
            (562, 2, 19, "primitive:ushort", 0),
            (564, 2, 19, "primitive:ushort", 0),
            (566, 2, 19, "primitive:ushort", 0),
            (568, 2, 19, "primitive:ushort", 0),
            (570, 2, 19, "primitive:ushort", 0),
            (572, 2, 19, "primitive:ushort", 0),
            (574, 2, 19, "primitive:ushort", 0),
            (576, 2, 19, "primitive:ushort", 0),
            (580, 2, 19, "primitive:ushort", 0),
        ),
    },
)
