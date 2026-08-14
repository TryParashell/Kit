# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Owners.Sldmfcu.MoPunchTableDefsC.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram = (
    KOwnerSites,
    {
        "Contents/Config-0": (
            (12685, 4, 220, "primitive:int", 0),
            (12689, 4, 233, "primitive:int", 0),
            (12693, 8, 246, "primitive:double", float.fromhex("0x1.0624dd2f1a9fcp-7")),
            (12701, 8, 259, "primitive:double", float.fromhex("0x1.921fb54442d28p-1")),
            (12709, 4, 272, "primitive:int", 0),
            (12713, 4, 285, "primitive:int", 0),
            (12717, 4, 298, "primitive:int", 2),
            (12721, 4, 311, "primitive:int", 0),
            (12725, 4, 324, "primitive:int", 2),
            (12729, 4, 337, "primitive:int", 1),
        ),
    },
)
