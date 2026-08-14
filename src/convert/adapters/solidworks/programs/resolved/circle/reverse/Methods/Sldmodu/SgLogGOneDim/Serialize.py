# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Owners.Sldmodu.SgLogGOneDim.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (7253, 2, 1930, "primitive:ushort", 0),
            (7255, 2, 1953, "primitive:ushort", 0),
            (7259, 2, 2380, "primitive:ushort", 0),
            (7261, 4, 2445, "primitive:long", -1),
            (7265, 4, 2467, "primitive:long", -1),
            (7269, 8, 2531, "primitive:double", float.fromhex("0x0.0p+0")),
            (7277, 8, 2574, "primitive:double", float.fromhex("0x0.0p+0")),
            (7291, 2, 2986, "primitive:ushort", 0),
        ),
    },
)
