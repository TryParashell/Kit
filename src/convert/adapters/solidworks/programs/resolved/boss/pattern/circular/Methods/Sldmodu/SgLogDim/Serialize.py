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
            (7848, 2, 239, "primitive:ushort", 65534),
            (7850, 2, 334, "primitive:ushort", 0),
            (7903, 2, 239, "primitive:ushort", 65534),
            (7905, 2, 334, "primitive:ushort", 0),
            (7958, 2, 239, "primitive:ushort", 65534),
            (7960, 2, 334, "primitive:ushort", 0),
            (8013, 2, 239, "primitive:ushort", 65534),
            (8015, 2, 334, "primitive:ushort", 0),
            (8070, 2, 239, "primitive:ushort", 65534),
            (8072, 2, 334, "primitive:ushort", 0),
        ),
    },
)
