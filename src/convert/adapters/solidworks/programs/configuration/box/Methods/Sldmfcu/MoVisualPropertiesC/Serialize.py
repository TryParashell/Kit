# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Sldmfcu.MoVisualPropertiesC.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "Configuration": (
            (108, 4, 364, "primitive:ulong", 15651274),
            (112, 4, 393, "primitive:ulong", 0),
            (116, 4, 425, "primitive:ulong", 0),
            (693, 4, 529, "primitive:int", 0),
            (697, 4, 558, "primitive:int", 1),
            (705, 4, 616, "primitive:int", 0),
            (709, 4, 683, "primitive:int", 1),
            (713, 4, 712, "primitive:int", -1),
            (717, 4, 741, "primitive:int", 0),
            (721, 4, 773, "primitive:int", 0),
            (725, 4, 810, "primitive:int", 0),
        ),
    },
)
