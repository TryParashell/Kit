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
        "Contents/Config-0": (
            (19370, 1, 492, "primitive:uchar", 0),
            (19379, 1, 538, "primitive:uchar", 0),
            (19400, 4, 963, "primitive:int", 0),
            (19404, 4, 976, "primitive:int", 0),
            (19408, 2, 1007, "primitive:ushort", 0),
            (19414, 4, 1131, "primitive:int", 0),
            (19422, 1, 492, "primitive:uchar", 0),
            (19431, 1, 538, "primitive:uchar", 0),
            (19452, 4, 963, "primitive:int", 0),
            (19456, 4, 976, "primitive:int", 0),
            (19460, 2, 1007, "primitive:ushort", 0),
            (19466, 4, 1131, "primitive:int", 0),
        ),
    },
)
