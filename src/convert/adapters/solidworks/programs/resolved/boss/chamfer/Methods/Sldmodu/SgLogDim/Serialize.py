# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Owners.Sldmodu.SgLogDim.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (5484, 2, 239, "primitive:ushort", 65534),
            (5486, 2, 334, "primitive:ushort", 0),
            (7383, 2, 239, "primitive:ushort", 65534),
            (7385, 2, 334, "primitive:ushort", 0),
            (7438, 2, 239, "primitive:ushort", 65534),
            (7440, 2, 334, "primitive:ushort", 0),
            (7493, 2, 239, "primitive:ushort", 65534),
            (7495, 2, 334, "primitive:ushort", 0),
            (7548, 2, 239, "primitive:ushort", 65534),
            (7550, 2, 334, "primitive:ushort", 0),
        ),
    },
)
