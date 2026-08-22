# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Sldmodu.SgLogGOneDim.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (13863, 2, 1930, "primitive:ushort", 0),
            (13865, 2, 1953, "primitive:ushort", 0),
            (13869, 2, 2380, "primitive:ushort", 0),
            (13871, 4, 2445, "primitive:long", -1),
            (13875, 4, 2467, "primitive:long", -1),
            (13879, 8, 2531, "primitive:double", float.fromhex("0x0.0p+0")),
            (13887, 8, 2574, "primitive:double", float.fromhex("0x0.0p+0")),
            (13901, 2, 2986, "primitive:ushort", 0),
            (13970, 2, 1930, "primitive:ushort", 0),
            (13972, 2, 1953, "primitive:ushort", 0),
            (13976, 2, 2380, "primitive:ushort", 0),
            (13978, 4, 2445, "primitive:long", -1),
            (13982, 4, 2467, "primitive:long", -1),
            (13986, 8, 2531, "primitive:double", float.fromhex("0x0.0p+0")),
            (13994, 8, 2574, "primitive:double", float.fromhex("0x0.0p+0")),
            (14008, 2, 2986, "primitive:ushort", 0),
        ),
    },
)
