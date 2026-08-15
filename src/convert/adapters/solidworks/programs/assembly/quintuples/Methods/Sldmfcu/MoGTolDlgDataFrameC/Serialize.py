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
            (19968, 1, 492, "primitive:uchar", 0),
            (19977, 1, 538, "primitive:uchar", 0),
            (19998, 4, 963, "primitive:int", 0),
            (20002, 4, 976, "primitive:int", 0),
            (20006, 2, 1007, "primitive:ushort", 0),
            (20012, 4, 1131, "primitive:int", 0),
            (20020, 1, 492, "primitive:uchar", 0),
            (20029, 1, 538, "primitive:uchar", 0),
            (20050, 4, 963, "primitive:int", 0),
            (20054, 4, 976, "primitive:int", 0),
            (20058, 2, 1007, "primitive:ushort", 0),
            (20064, 4, 1131, "primitive:int", 0),
        ),
    },
)
