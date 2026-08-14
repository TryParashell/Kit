# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Owners.Sldarchiveu.MoSharedFileDefC.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram = (
    KOwnerSites,
    {
        "Contents/CMgr": (
            (1480, 2, 1006, "primitive:ushort", 3),
            (1482, 1, 1028, "primitive:uchar", 0),
            (1499, 1, 1519, "primitive:uchar", 0),
            (1626, 2, 1006, "primitive:ushort", 3),
            (1628, 1, 1028, "primitive:uchar", 0),
            (1645, 1, 1519, "primitive:uchar", 0),
        ),
        "Contents/Config-0": (
            (597, 2, 1006, "primitive:ushort", 3),
            (599, 1, 1028, "primitive:uchar", 0),
            (616, 1, 1519, "primitive:uchar", 0),
        ),
        "Contents/Config-0-ModelHeader": (
            (2095, 2, 1006, "primitive:ushort", 2),
            (2097, 1, 1028, "primitive:uchar", 0),
            (2114, 1, 1519, "primitive:uchar", 0),
            (2182, 2, 1006, "primitive:ushort", 3),
            (2184, 1, 1028, "primitive:uchar", 0),
            (2201, 1, 1519, "primitive:uchar", 0),
        ),
    },
)
