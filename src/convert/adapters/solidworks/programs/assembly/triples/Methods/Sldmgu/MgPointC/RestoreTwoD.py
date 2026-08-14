# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Owners.Sldmgu.MgPointC.RestoreTwoD import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram = (
    KOwnerSites,
    {
        "Contents/Config-0-ResolvedFeatures": (
            (4726, 8, 30, "primitive:double", float.fromhex("0x0.0p+0")),
            (4734, 8, 54, "primitive:double", float.fromhex("0x0.0p+0")),
            (4756, 8, 30, "primitive:double", float.fromhex("0x0.0p+0")),
            (4764, 8, 54, "primitive:double", float.fromhex("0x0.0p+0")),
            (4772, 8, 30, "primitive:double", float.fromhex("0x0.0p+0")),
            (4780, 8, 54, "primitive:double", float.fromhex("0x0.0p+0")),
        ),
    },
)
