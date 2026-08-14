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
            (5365, 2, 239, "primitive:ushort", 65534),
            (5367, 2, 334, "primitive:ushort", 0),
            (8052, 2, 239, "primitive:ushort", 65534),
            (8054, 2, 334, "primitive:ushort", 0),
            (8107, 2, 239, "primitive:ushort", 65534),
            (8109, 2, 334, "primitive:ushort", 0),
            (8162, 2, 239, "primitive:ushort", 65534),
            (8164, 2, 334, "primitive:ushort", 0),
            (8217, 2, 239, "primitive:ushort", 65534),
            (8219, 2, 334, "primitive:ushort", 0),
            (8274, 2, 239, "primitive:ushort", 65534),
            (8276, 2, 334, "primitive:ushort", 0),
        ),
    },
)
