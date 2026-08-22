# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Sldmfcu.MoGTolDlgDataFrameC.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "Configuration": (
            (17730, 1, 492, "primitive:uchar", 0),
            (17739, 1, 538, "primitive:uchar", 0),
            (17760, 4, 963, "primitive:int", 0),
            (17764, 4, 976, "primitive:int", 0),
            (17768, 2, 1007, "primitive:ushort", 0),
            (17774, 4, 1131, "primitive:int", 0),
            (17782, 1, 492, "primitive:uchar", 0),
            (17791, 1, 538, "primitive:uchar", 0),
            (17812, 4, 963, "primitive:int", 0),
            (17816, 4, 976, "primitive:int", 0),
            (17820, 2, 1007, "primitive:ushort", 0),
            (17826, 4, 1131, "primitive:int", 0),
        ),
    },
)
