# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Owners.Sldmfcu.MoViewLocationLabelDefsC.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram = (
    KOwnerSites,
    {
        "Contents/Config-0": (
            (12699, 4, 175, "primitive:int", 7),
            (12703, 4, 196, "primitive:int", 9),
            (12707, 4, 217, "primitive:int", 11),
            (12711, 4, 257, "primitive:int", 2),
            (12715, 8, 277, "primitive:double", float.fromhex("0x1.4cec41dd1a21fp-7")),
            (12723, 4, 291, "primitive:int", 1),
            (12727, 8, 333, "primitive:double", float.fromhex("0x0.0p+0")),
            (12735, 4, 409, "primitive:int", 0),
        ),
    },
)
