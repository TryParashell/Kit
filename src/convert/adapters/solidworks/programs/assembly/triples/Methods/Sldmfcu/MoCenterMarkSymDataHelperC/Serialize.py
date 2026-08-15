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
            (19284, 1, 297, "primitive:uchar", 0),
            (19285, 8, 317, "primitive:double", float.fromhex("0x0.0p+0")),
            (19293, 1, 330, "primitive:uchar", 1),
            (19294, 8, 350, "primitive:double", float.fromhex("0x0.0p+0")),
            (19302, 1, 363, "primitive:uchar", 0),
            (19303, 1, 383, "primitive:uchar", 0),
            (19304, 1, 403, "primitive:uchar", 0),
            (19305, 1, 423, "primitive:uchar", 0),
            (19306, 1, 443, "primitive:uchar", 0),
            (19307, 1, 463, "primitive:uchar", 0),
            (19447, 4, 534, "primitive:int", 0),
            (19451, 1, 563, "primitive:uchar", 1),
            (19452, 1, 583, "primitive:uchar", 1),
            (19453, 1, 603, "primitive:uchar", 1),
            (19454, 1, 639, "primitive:uchar", 0),
            (19455, 8, 675, "primitive:double", float.fromhex("0x0.0p+0")),
        ),
    },
)
