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
            (4734, 4, 5750, "primitive:long", 0),
            (4740, 4, 5933, "primitive:long", 0),
            (5442, 2, 8922, "primitive:ushort", 0),
            (5444, 2, 9595, "primitive:ushort", 4),
            (5448, 4, 10266, "primitive:long", -7),
            (5452, 4, 10336, "primitive:long", 0),
            (5456, 4, 10532, "primitive:ulong", 101),
            (5460, 2, 10601, "primitive:ushort", 0),
            (5468, 4, 11123, "primitive:long", 0),
        ),
    },
)
