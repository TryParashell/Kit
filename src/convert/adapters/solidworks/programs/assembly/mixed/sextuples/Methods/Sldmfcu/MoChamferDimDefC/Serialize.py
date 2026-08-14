# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Owners.Sldmfcu.MoChamferDimDefC.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram = (
    KOwnerSites,
    {
        "Contents/Config-0": (
            (9149, 4, 203, "primitive:int", 0),
            (9153, 4, 219, "primitive:int", 1),
            (9157, 4, 252, "primitive:int", 2),
            (9161, 4, 287, "primitive:int", 2),
            (9165, 8, 303, "primitive:double", float.fromhex("0x0.0p+0")),
            (9173, 8, 319, "primitive:double", float.fromhex("0x0.0p+0")),
            (9181, 4, 335, "primitive:int", 0),
            (9185, 4, 351, "primitive:int", 0),
        ),
    },
)
