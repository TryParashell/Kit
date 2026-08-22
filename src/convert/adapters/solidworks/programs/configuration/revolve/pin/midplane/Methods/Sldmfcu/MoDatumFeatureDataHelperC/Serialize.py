# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Sldmfcu.MoDatumFeatureDataHelperC.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "Configuration": (
            (18289, 1, 188, "primitive:uchar", 0),
            (18290, 1, 210, "primitive:uchar", 0),
            (18291, 1, 232, "primitive:uchar", 0),
            (18292, 4, 253, "primitive:int", 0),
            (18296, 4, 266, "primitive:int", 0),
            (18308, 4, 322, "primitive:int", 0),
            (18312, 4, 335, "primitive:int", 0),
            (18316, 4, 348, "primitive:int", 0),
        ),
    },
)
