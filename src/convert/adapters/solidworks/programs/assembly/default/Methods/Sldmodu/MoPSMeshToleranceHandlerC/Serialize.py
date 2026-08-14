# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Owners.Sldmodu.MoPSMeshToleranceHandlerC.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram = (
    KOwnerSites,
    {
        "Contents/Config-0-ResolvedFeatures": (
            (4510, 4, 5750, "primitive:long", 0),
            (4516, 4, 5933, "primitive:long", 0),
            (5218, 2, 8922, "primitive:ushort", 0),
            (5220, 2, 9595, "primitive:ushort", 4),
            (5224, 4, 10266, "primitive:long", -7),
            (5228, 4, 10336, "primitive:long", 0),
            (5232, 4, 10532, "primitive:ulong", 101),
            (5236, 2, 10601, "primitive:ushort", 0),
            (5244, 4, 11123, "primitive:long", 0),
        ),
    },
)
