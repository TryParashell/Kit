# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Owners.Sldmodu.MoAssemblyC.SerializeResolvedData import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram = (
    KOwnerSites,
    {
        "Contents/Config-0": (
            (25980, 4, 771, "primitive:long", 6),
            (25984, 2, 806, "primitive:ushort", 3),
            (25994, 4, 1314, "primitive:long", 0),
            (25998, 4, 1373, "primitive:long", 0),
            (26235, 4, 1565, "primitive:long", 1),
            (26247, 4, 1727, "primitive:long", 0),
            (26251, 4, 1823, "primitive:long", -1),
        ),
    },
)
