# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Sldmfcu.MoGTolDataHelperC.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "Contents/Config-0": (
            (17584, 4, 441, "primitive:long", 2),
            (17692, 4, 495, "primitive:long", 1),
            (17696, 4, 514, "primitive:long", 2),
            (17704, 1, 546, "primitive:uchar", 0),
            (17705, 1, 566, "primitive:uchar", 1),
            (17706, 1, 586, "primitive:uchar", 1),
            (17707, 1, 606, "primitive:uchar", 0),
            (17708, 4, 663, "primitive:long", 0),
            (17712, 1, 682, "primitive:uchar", 0),
            (17721, 1, 744, "primitive:uchar", 0),
            (17730, 1, 799, "primitive:uchar", 0),
            (17735, 1, 857, "primitive:uchar", 0),
            (17736, 1, 880, "primitive:uchar", 1),
            (17737, 1, 903, "primitive:uchar", 0),
            (17738, 1, 926, "primitive:uchar", 0),
            (17966, 1, 1077, "primitive:uchar", 0),
            (17967, 1, 1100, "primitive:uchar", 0),
            (17968, 1, 1120, "primitive:uchar", 0),
            (17969, 1, 1200, "primitive:uchar", 0),
            (17970, 1, 1223, "primitive:uchar", 0),
            (17971, 1, 1299, "primitive:uchar", 0),
        ),
    },
)
