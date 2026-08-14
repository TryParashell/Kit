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
        "Contents/Config-0": (
            (11449, 4, 349, "primitive:int", 2),
            (11453, 4, 370, "primitive:int", 2),
            (11457, 4, 391, "primitive:int", 1),
            (11461, 4, 412, "primitive:int", 1),
            (11465, 4, 433, "primitive:int", 1),
            (11469, 4, 471, "primitive:int", 2),
            (11481, 4, 537, "primitive:int", 1),
            (11485, 8, 629, "primitive:double", float.fromhex("0x1.4cec41dd1a21fp-7")),
            (11493, 8, 645, "primitive:double", float.fromhex("0x1.4cec41dd1a21fp-7")),
            (11501, 4, 678, "primitive:int", 0),
            (11505, 4, 694, "primitive:int", 1),
            (11515, 8, 743, "primitive:double", float.fromhex("0x0.0p+0")),
            (11523, 8, 759, "primitive:double", float.fromhex("0x0.0p+0")),
            (11531, 8, 792, "primitive:double", float.fromhex("0x1.0624dd2f1a9fcp-10")),
            (11539, 4, 849, "primitive:int", 0),
        ),
    },
)
