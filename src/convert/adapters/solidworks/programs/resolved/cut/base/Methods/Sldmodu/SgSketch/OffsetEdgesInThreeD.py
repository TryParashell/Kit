# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Sldmodu.SgSketch.OffsetEdgesInThreeD import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (5808, 4, 37887, "primitive:long", 0),
            (5812, 4, 37887, "primitive:long", 0),
            (5816, 4, 37887, "primitive:long", 0),
            (5820, 4, 37887, "primitive:long", 0),
            (7855, 4, 37887, "primitive:long", 0),
            (7859, 4, 37887, "primitive:long", 0),
            (7863, 4, 37887, "primitive:long", 0),
            (7867, 4, 37887, "primitive:long", 0),
            (13157, 4, 37887, "primitive:long", 0),
            (13161, 4, 37887, "primitive:long", 0),
            (13165, 4, 37887, "primitive:long", 0),
            (13169, 4, 37887, "primitive:long", 0),
        ),
    },
)
