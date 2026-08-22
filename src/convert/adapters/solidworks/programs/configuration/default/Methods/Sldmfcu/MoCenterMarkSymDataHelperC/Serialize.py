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
        "Configuration": (
            (18080, 1, 297, "primitive:uchar", 0),
            (18081, 8, 317, "primitive:double", float.fromhex("0x0.0p+0")),
            (18089, 1, 330, "primitive:uchar", 1),
            (18090, 8, 350, "primitive:double", float.fromhex("0x0.0p+0")),
            (18098, 1, 363, "primitive:uchar", 0),
            (18099, 1, 383, "primitive:uchar", 0),
            (18100, 1, 403, "primitive:uchar", 0),
            (18101, 1, 423, "primitive:uchar", 0),
            (18102, 1, 443, "primitive:uchar", 0),
            (18103, 1, 463, "primitive:uchar", 0),
            (18243, 4, 534, "primitive:int", 0),
            (18247, 1, 563, "primitive:uchar", 1),
            (18248, 1, 583, "primitive:uchar", 1),
            (18249, 1, 603, "primitive:uchar", 1),
            (18250, 1, 639, "primitive:uchar", 0),
            (18251, 8, 675, "primitive:double", float.fromhex("0x0.0p+0")),
        ),
    },
)
