# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Swccu.Functions.ReadOperator import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (767, 4, 19, "primitive:ulong", 1786448316),
            (886, 4, 19, "primitive:ulong", 1786448316),
            (1005, 4, 19, "primitive:ulong", 1786448316),
            (5881, 4, 19, "primitive:ulong", 1763334902),
            (8081, 4, 19, "primitive:ulong", 1763334902),
            (8589, 4, 19, "primitive:ulong", 1786448315),
            (8607, 4, 19, "primitive:ulong", 0),
            (8649, 4, 19, "primitive:ulong", 0),
            (8661, 4, 19, "primitive:ulong", 1786448316),
            (8712, 4, 19, "primitive:ulong", 1786448316),
            (8732, 4, 19, "primitive:ulong", 1786448316),
            (8752, 4, 19, "primitive:ulong", 1786448316),
            (8772, 4, 19, "primitive:ulong", 1786448316),
            (8854, 4, 19, "primitive:ulong", 1786448316),
            (8878, 4, 19, "primitive:ulong", 1786448316),
            (8898, 4, 19, "primitive:ulong", 1786448316),
            (8918, 4, 19, "primitive:ulong", 1786448316),
            (8938, 4, 19, "primitive:ulong", 1786448316),
            (11654, 4, 19, "primitive:ulong", 1786448316),
            (11678, 4, 19, "primitive:ulong", 1786448316),
            (11698, 4, 19, "primitive:ulong", 1786448316),
            (11718, 4, 19, "primitive:ulong", 1786448316),
            (11738, 4, 19, "primitive:ulong", 1786448316),
            (13712, 4, 19, "primitive:ulong", 1786448316),
            (13732, 4, 19, "primitive:ulong", 1786448316),
            (13756, 4, 19, "primitive:ulong", 1786448316),
            (13776, 4, 19, "primitive:ulong", 1786448316),
        ),
    },
)
