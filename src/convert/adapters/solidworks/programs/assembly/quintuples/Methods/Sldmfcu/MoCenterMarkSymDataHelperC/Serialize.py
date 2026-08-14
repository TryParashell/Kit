# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Owners.Sldmfcu.MoCenterMarkSymDataHelperC.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram = (
    KOwnerSites,
    {
        "Contents/Config-0": (
            (20348, 1, 297, "primitive:uchar", 0),
            (20349, 8, 317, "primitive:double", float.fromhex("0x0.0p+0")),
            (20357, 1, 330, "primitive:uchar", 1),
            (20358, 8, 350, "primitive:double", float.fromhex("0x0.0p+0")),
            (20366, 1, 363, "primitive:uchar", 0),
            (20367, 1, 383, "primitive:uchar", 0),
            (20368, 1, 403, "primitive:uchar", 0),
            (20369, 1, 423, "primitive:uchar", 0),
            (20370, 1, 443, "primitive:uchar", 0),
            (20371, 1, 463, "primitive:uchar", 0),
            (20511, 4, 534, "primitive:int", 0),
            (20515, 1, 563, "primitive:uchar", 1),
            (20516, 1, 583, "primitive:uchar", 1),
            (20517, 1, 603, "primitive:uchar", 1),
            (20518, 1, 639, "primitive:uchar", 0),
            (20519, 8, 675, "primitive:double", float.fromhex("0x0.0p+0")),
        ),
    },
)
