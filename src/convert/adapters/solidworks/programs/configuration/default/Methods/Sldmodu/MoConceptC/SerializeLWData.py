# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoConceptC.SerializeLWData import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "Configuration": (
            (18, 4, 864, "primitive:long", 0),
            (22, 4, 923, "primitive:ulong", 18000),
            (80, 4, 259, "primitive:long", 0),
            (2896, 4, 259, "primitive:long", 0),
            (20553, 4, 259, "primitive:long", 0),
            (20623, 4, 259, "primitive:long", 0),
            (20926, 4, 259, "primitive:long", 0),
            (21247, 4, 259, "primitive:long", 0),
            (21568, 4, 259, "primitive:long", 0),
            (24085, 4, 259, "primitive:long", 0),
            (25033, 4, 259, "primitive:long", 0),
        ),
    },
)
