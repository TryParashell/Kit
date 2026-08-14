# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Owners.Sldmfcu.MoBalloonDefsC.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram = (
    KOwnerSites,
    {
        "Configuration": (
            (9181, 4, 349, "primitive:int", 2),
            (9185, 4, 370, "primitive:int", 2),
            (9189, 4, 391, "primitive:int", 1),
            (9193, 4, 412, "primitive:int", 1),
            (9197, 4, 433, "primitive:int", 1),
            (9201, 4, 471, "primitive:int", 2),
            (9213, 4, 537, "primitive:int", 1),
            (9217, 8, 629, "primitive:double", float.fromhex("0x1.4cec41dd1a21fp-7")),
            (9225, 8, 645, "primitive:double", float.fromhex("0x1.4cec41dd1a21fp-7")),
            (9233, 4, 678, "primitive:int", 0),
            (9237, 4, 694, "primitive:int", 1),
            (9247, 8, 743, "primitive:double", float.fromhex("0x0.0p+0")),
            (9255, 8, 759, "primitive:double", float.fromhex("0x0.0p+0")),
            (9263, 8, 792, "primitive:double", float.fromhex("0x1.0624dd2f1a9fcp-10")),
            (9271, 4, 849, "primitive:int", 0),
        ),
    },
)
