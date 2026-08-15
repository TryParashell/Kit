# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoArrowSizeC.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "Contents/Config-0-ResolvedFeatures": (
            (2446, 8, 12364, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (2454, 8, 12380, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (2464, 4, 12686, "primitive:long", 0),
            (2468, 4, 12862, "primitive:long", 0),
        ),
    },
)
