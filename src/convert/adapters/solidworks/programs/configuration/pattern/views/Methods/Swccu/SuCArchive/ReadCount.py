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
            (492, 2, 19, "primitive:ushort", 0),
            (494, 2, 19, "primitive:ushort", 0),
            (496, 2, 19, "primitive:ushort", 0),
            (498, 2, 19, "primitive:ushort", 0),
            (500, 2, 19, "primitive:ushort", 0),
            (502, 2, 19, "primitive:ushort", 0),
            (504, 2, 19, "primitive:ushort", 0),
            (506, 2, 19, "primitive:ushort", 0),
            (510, 2, 19, "primitive:ushort", 0),
        ),
    },
)
