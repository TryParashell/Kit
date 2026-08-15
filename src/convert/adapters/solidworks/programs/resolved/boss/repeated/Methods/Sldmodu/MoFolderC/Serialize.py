# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoFolderC.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (195, 4, 155, "primitive:long", 0),
            (199, 4, 210, "primitive:long", 0),
            (394, 4, 155, "primitive:long", 1),
            (398, 4, 210, "primitive:long", 0),
            (596, 4, 155, "primitive:long", 1),
            (600, 4, 210, "primitive:long", 0),
            (1333, 4, 155, "primitive:long", 1),
            (1337, 4, 210, "primitive:long", 0),
            (1532, 4, 155, "primitive:long", 1),
            (1536, 4, 210, "primitive:long", 0),
            (1735, 4, 155, "primitive:long", 1),
            (1739, 4, 210, "primitive:long", 0),
            (2009, 4, 155, "primitive:long", 1),
            (2013, 4, 210, "primitive:long", 0),
            (2204, 4, 155, "primitive:long", 1),
            (2208, 4, 210, "primitive:long", 0),
            (2599, 4, 155, "primitive:long", 1),
            (2603, 4, 210, "primitive:long", 0),
            (2817, 4, 155, "primitive:long", 1),
            (2821, 4, 210, "primitive:long", 0),
            (3027, 4, 155, "primitive:long", 1),
            (3031, 4, 210, "primitive:long", 0),
            (3221, 4, 155, "primitive:long", 1),
            (3225, 4, 210, "primitive:long", 0),
            (3450, 4, 155, "primitive:long", 1),
            (3454, 4, 210, "primitive:long", 0),
            (3462, 4, 640, "primitive:long", 0),
        ),
    },
)
