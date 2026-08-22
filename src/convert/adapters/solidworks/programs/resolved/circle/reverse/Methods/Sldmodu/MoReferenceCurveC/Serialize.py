# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoReferenceCurveC.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (9200, 4, 3909, "primitive:ulong", 6),
            (9204, 4, 3928, "primitive:long", -1),
            (9208, 4, 3941, "primitive:long", 0),
            (9212, 4, 3954, "primitive:long", 0),
            (9216, 4, 3967, "primitive:ulong", 5),
            (9220, 4, 3986, "primitive:ulong", 5),
            (9228, 2, 4030, "primitive:ushort", 0),
            (9230, 4, 4154, "primitive:ulong", 4294967295),
            (9234, 4, 4250, "primitive:ulong", 0),
            (9242, 4, 4466, "primitive:long", 0),
            (9246, 4, 4482, "primitive:long", 0),
            (9250, 4, 4540, "primitive:long", 0),
        ),
    },
)
