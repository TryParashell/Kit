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
            (19508, 1, 492, "primitive:uchar", 0),
            (19517, 1, 538, "primitive:uchar", 0),
            (19538, 4, 963, "primitive:int", 0),
            (19542, 4, 976, "primitive:int", 0),
            (19546, 2, 1007, "primitive:ushort", 0),
            (19552, 4, 1131, "primitive:int", 0),
            (19560, 1, 492, "primitive:uchar", 0),
            (19569, 1, 538, "primitive:uchar", 0),
            (19590, 4, 963, "primitive:int", 0),
            (19594, 4, 976, "primitive:int", 0),
            (19598, 2, 1007, "primitive:ushort", 0),
            (19604, 4, 1131, "primitive:int", 0),
        ),
    },
)
