# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Owners.Sldmfcu.MoAnnotationDefsC.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram = (
    KOwnerSites,
    {
        "Contents/Config-0": (
            (10179, 4, 222, "primitive:int", 4),
            (10183, 8, 235, "primitive:double", float.fromhex("0x1.a027525460aa6p-8")),
            (10191, 4, 248, "primitive:int", 0),
            (10195, 4, 261, "primitive:int", 0),
            (10199, 4, 274, "primitive:int", 3),
            (10203, 4, 287, "primitive:int", 0),
            (10207, 4, 324, "primitive:int", 0),
            (10211, 4, 337, "primitive:int", 0),
            (10215, 4, 374, "primitive:int", 1),
            (10219, 4, 387, "primitive:int", 1),
            (10223, 4, 449, "primitive:int", 0),
            (10227, 4, 488, "primitive:int", 1),
            (11933, 8, 742, "primitive:double", float.fromhex("0x1.4cec41dd1a21fp-8")),
        ),
    },
)
