# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Owners.Sldmodu.MoCompBucketDataC.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (11854, 4, 1075, "primitive:long", 0),
            (11906, 4, 1203, "primitive:ulong", 0),
            (11910, 4, 1227, "primitive:long", 0),
            (15693, 4, 1075, "primitive:long", 0),
            (15745, 4, 1203, "primitive:ulong", 0),
            (15749, 4, 1227, "primitive:long", 0),
        ),
    },
)
