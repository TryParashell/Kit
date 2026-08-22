# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoPSMeshToleranceHandlerC.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (5217, 4, 5750, "primitive:long", 0),
            (5223, 4, 5933, "primitive:long", 0),
            (5925, 2, 8922, "primitive:ushort", 0),
            (5927, 2, 9595, "primitive:ushort", 4),
            (5931, 4, 10266, "primitive:long", -7),
            (5935, 4, 10336, "primitive:long", 0),
            (5939, 4, 10532, "primitive:ulong", 101),
            (5943, 2, 10601, "primitive:ushort", 0),
            (5951, 4, 11123, "primitive:long", 0),
            (6146, 4, 5750, "primitive:long", 0),
            (6152, 4, 5933, "primitive:long", 0),
            (8125, 2, 8922, "primitive:ushort", 0),
            (8127, 2, 9595, "primitive:ushort", 4),
            (8131, 4, 10266, "primitive:long", -1),
            (8135, 4, 10336, "primitive:long", 0),
            (8139, 4, 10532, "primitive:ulong", 102),
            (8143, 2, 10601, "primitive:ushort", 1),
            (8151, 4, 11123, "primitive:long", 0),
        ),
    },
)
