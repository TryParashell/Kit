# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Owners.Sldmfcu.MoNoteDefsC.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram = (
    KOwnerSites,
    {
        "Contents/Config-0": (
            (10633, 4, 175, "primitive:int", 0),
            (10637, 4, 196, "primitive:int", 10),
            (10641, 4, 216, "primitive:int", 0),
            (10645, 8, 246, "primitive:double", float.fromhex("0x1.4cec41dd1a21fp-7")),
            (10653, 8, 276, "primitive:double", float.fromhex("0x0.0p+0")),
            (10661, 8, 306, "primitive:double", float.fromhex("0x1.0624dd2f1a9fcp-10")),
            (10669, 4, 355, "primitive:int", 1),
        ),
    },
)
