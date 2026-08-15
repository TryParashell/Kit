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
            (7371, 4, 203, "primitive:int", 0),
            (7375, 4, 219, "primitive:int", 1),
            (7379, 4, 252, "primitive:int", 2),
            (7383, 4, 287, "primitive:int", 2),
            (7387, 8, 303, "primitive:double", float.fromhex("0x0.0p+0")),
            (7395, 8, 319, "primitive:double", float.fromhex("0x0.0p+0")),
            (7403, 4, 335, "primitive:int", 0),
            (7407, 4, 351, "primitive:int", 0),
        ),
    },
)
