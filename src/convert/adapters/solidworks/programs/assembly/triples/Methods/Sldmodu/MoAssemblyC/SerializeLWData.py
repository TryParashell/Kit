# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoAssemblyC.SerializeLWData import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "Contents/Config-0": (
            (3980, 1, 487, "primitive:uchar", 1),
            (4053, 8, 515, "primitive:double", float.fromhex("0x1.225aa716cda9cp-4")),
            (4061, 1, 572, "primitive:uchar", 1),
            (4134, 8, 600, "primitive:double", float.fromhex("0x1.225aa716cda9cp-4")),
        ),
    },
)
