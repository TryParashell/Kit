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
            (11697, 4, 175, "primitive:int", 0),
            (11701, 4, 196, "primitive:int", 10),
            (11705, 4, 216, "primitive:int", 0),
            (11709, 8, 246, "primitive:double", float.fromhex("0x1.4cec41dd1a21fp-7")),
            (11717, 8, 276, "primitive:double", float.fromhex("0x0.0p+0")),
            (11725, 8, 306, "primitive:double", float.fromhex("0x1.0624dd2f1a9fcp-10")),
            (11733, 4, 355, "primitive:int", 1),
        ),
    },
)
