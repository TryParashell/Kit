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
            (18904, 1, 492, "primitive:uchar", 0),
            (18913, 1, 538, "primitive:uchar", 0),
            (18934, 4, 963, "primitive:int", 0),
            (18938, 4, 976, "primitive:int", 0),
            (18942, 2, 1007, "primitive:ushort", 0),
            (18948, 4, 1131, "primitive:int", 0),
            (18956, 1, 492, "primitive:uchar", 0),
            (18965, 1, 538, "primitive:uchar", 0),
            (18986, 4, 963, "primitive:int", 0),
            (18990, 4, 976, "primitive:int", 0),
            (18994, 2, 1007, "primitive:ushort", 0),
            (19000, 4, 1131, "primitive:int", 0),
        ),
    },
)
