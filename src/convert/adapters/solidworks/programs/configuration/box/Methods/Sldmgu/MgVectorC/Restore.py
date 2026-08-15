# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Owners.Sldmgu.MgVectorC.Restore import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram = (
    KOwnerSites,
    {
        "Configuration": (
            (18531, 8, 28, "primitive:double", float.fromhex("0x0.0p+0")),
            (18539, 8, 41, "primitive:double", float.fromhex("0x0.0p+0")),
            (21193, 8, 28, "primitive:double", float.fromhex("0x1.c666666666666p+2")),
            (21201, 8, 41, "primitive:double", float.fromhex("0x1.c666666666666p+2")),
            (21514, 8, 28, "primitive:double", float.fromhex("-0x1.b333333333333p+1")),
            (21522, 8, 41, "primitive:double", float.fromhex("0x1.8666666666666p+2")),
            (21835, 8, 28, "primitive:double", float.fromhex("-0x1.2666666666666p+3")),
            (21843, 8, 41, "primitive:double", float.fromhex("0x1.b333333333333p+1")),
        ),
    },
)
