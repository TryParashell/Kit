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
            (14007, 4, 220, "primitive:int", 0),
            (14011, 4, 233, "primitive:int", 0),
            (14015, 8, 246, "primitive:double", float.fromhex("0x1.0624dd2f1a9fcp-7")),
            (14023, 8, 259, "primitive:double", float.fromhex("0x1.921fb54442d28p-1")),
            (14031, 4, 272, "primitive:int", 0),
            (14035, 4, 285, "primitive:int", 0),
            (14039, 4, 298, "primitive:int", 2),
            (14043, 4, 311, "primitive:int", 0),
            (14047, 4, 324, "primitive:int", 2),
            (14051, 4, 337, "primitive:int", 1),
        ),
    },
)
