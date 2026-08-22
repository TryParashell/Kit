# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoThreedViewC.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "Configuration": (
            (2502, 4, 2363, "primitive:long", -1431655766),
            (2506, 4, 2379, "primitive:long", -1145324613),
            (24434, 4, 3488, "primitive:long", 0),
            (24442, 4, 3856, "primitive:long", 0),
            (24446, 8, 3923, "primitive:double", float.fromhex("0x0.0p+0")),
            (24456, 4, 4072, "primitive:long", 0),
            (24460, 4, 4088, "primitive:long", 1),
            (24466, 4, 4241, "primitive:long", -1),
            (24470, 4, 4316, "primitive:long", 0),
            (24474, 4, 4389, "primitive:long", -1),
            (24478, 4, 4444, "primitive:long", -1),
            (24690, 4, 3488, "primitive:long", 0),
            (24698, 4, 3856, "primitive:long", 0),
            (24702, 8, 3923, "primitive:double", float.fromhex("0x0.0p+0")),
            (24712, 4, 4072, "primitive:long", 0),
            (24716, 4, 4088, "primitive:long", 1),
            (24722, 4, 4241, "primitive:long", -1),
            (24726, 4, 4316, "primitive:long", 0),
            (24730, 4, 4389, "primitive:long", -1),
            (24734, 4, 4444, "primitive:long", -1),
        ),
    },
)
