# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Sldmfcu.MoCenterMarkSymDataHelperC.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "Contents/Config-0": (
            (19750, 1, 297, "primitive:uchar", 0),
            (19751, 8, 317, "primitive:double", float.fromhex("0x0.0p+0")),
            (19759, 1, 330, "primitive:uchar", 1),
            (19760, 8, 350, "primitive:double", float.fromhex("0x0.0p+0")),
            (19768, 1, 363, "primitive:uchar", 0),
            (19769, 1, 383, "primitive:uchar", 0),
            (19770, 1, 403, "primitive:uchar", 0),
            (19771, 1, 423, "primitive:uchar", 0),
            (19772, 1, 443, "primitive:uchar", 0),
            (19773, 1, 463, "primitive:uchar", 0),
            (19913, 4, 534, "primitive:int", 0),
            (19917, 1, 563, "primitive:uchar", 1),
            (19918, 1, 583, "primitive:uchar", 1),
            (19919, 1, 603, "primitive:uchar", 1),
            (19920, 1, 639, "primitive:uchar", 0),
            (19921, 8, 675, "primitive:double", float.fromhex("0x0.0p+0")),
        ),
    },
)
