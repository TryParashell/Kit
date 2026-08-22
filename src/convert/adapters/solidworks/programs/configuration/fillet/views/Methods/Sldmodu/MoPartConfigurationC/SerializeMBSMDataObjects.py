# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoPartConfigurationC.SerializeMBSMDataObjects import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "AnnotationManager": (
            (536, 4, 16801, "primitive:long", 201),
            (540, 4, 16829, "primitive:long", 199),
            (544, 4, 16880, "primitive:long", 1),
            (548, 4, 16917, "primitive:long", 199),
            (554, 4, 17155, "primitive:ulong", 0),
            (558, 4, 17186, "primitive:long", 0),
        ),
    },
)
