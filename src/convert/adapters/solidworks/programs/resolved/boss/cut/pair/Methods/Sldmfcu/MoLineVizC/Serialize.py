# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Owners.Sldmfcu.MoLineVizC.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (5990, 4, 166, "primitive:int", -1),
            (5994, 4, 245, "primitive:int", 1),
            (8037, 4, 166, "primitive:int", -1),
            (8041, 4, 245, "primitive:int", 1),
            (13232, 4, 166, "primitive:int", -1),
            (13236, 4, 245, "primitive:int", 1),
            (18393, 4, 166, "primitive:int", -1),
            (18397, 4, 245, "primitive:int", 1),
        ),
    },
)
