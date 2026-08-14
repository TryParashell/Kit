# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Owners.Sldmfcu.MoDensityUnitsC.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram = (
    KOwnerSites,
    {
        "Contents/Config-0": (
            (1384, 2, 208, "primitive:ushort", 3),
            (1386, 2, 261, "primitive:ushort", 1),
            (1388, 1, 307, "primitive:uchar", 0),
            (1389, 2, 431, "primitive:ushort", 3),
            (1391, 4, 461, "primitive:int", 0),
        ),
    },
)
