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
            (3760, 2, 208, "primitive:ushort", 3),
            (3762, 2, 261, "primitive:ushort", 1),
            (3764, 1, 307, "primitive:uchar", 0),
            (3765, 2, 431, "primitive:ushort", 3),
            (3767, 4, 461, "primitive:int", 0),
        ),
    },
)
