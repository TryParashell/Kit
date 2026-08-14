# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Owners.Sldmfcu.MoSFDefsC.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram = (
    KOwnerSites,
    {
        "Contents/Config-0": (
            (10451, 4, 167, "primitive:int", 0),
            (10455, 4, 188, "primitive:int", 2),
            (10459, 8, 208, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (10467, 8, 221, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
        ),
    },
)
