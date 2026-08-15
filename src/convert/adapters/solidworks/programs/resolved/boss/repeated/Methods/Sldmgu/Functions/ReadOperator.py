# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Sldmgu.Functions.ReadOperator import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (5764, 8, 22, "primitive:double", float.fromhex("0x0.0p+0")),
            (5772, 8, 35, "primitive:double", float.fromhex("0x0.0p+0")),
            (5780, 8, 48, "primitive:double", float.fromhex("0x0.0p+0")),
            (7811, 8, 22, "primitive:double", float.fromhex("0x0.0p+0")),
            (7819, 8, 35, "primitive:double", float.fromhex("0x0.0p+0")),
            (7827, 8, 48, "primitive:double", float.fromhex("0x0.0p+0")),
            (11084, 8, 22, "primitive:double", float.fromhex("0x0.0p+0")),
            (11092, 8, 35, "primitive:double", float.fromhex("0x0.0p+0")),
            (11100, 8, 48, "primitive:double", float.fromhex("0x0.0p+0")),
            (11140, 8, 22, "primitive:double", float.fromhex("0x0.0p+0")),
            (11148, 8, 35, "primitive:double", float.fromhex("0x0.0p+0")),
            (11156, 8, 48, "primitive:double", float.fromhex("0x0.0p+0")),
            (13006, 8, 22, "primitive:double", float.fromhex("0x0.0p+0")),
            (13014, 8, 35, "primitive:double", float.fromhex("0x0.0p+0")),
            (13022, 8, 48, "primitive:double", float.fromhex("0x0.0p+0")),
            (16266, 8, 22, "primitive:double", float.fromhex("0x0.0p+0")),
            (16274, 8, 35, "primitive:double", float.fromhex("0x0.0p+0")),
            (16282, 8, 48, "primitive:double", float.fromhex("0x0.0p+0")),
            (16322, 8, 22, "primitive:double", float.fromhex("0x0.0p+0")),
            (16330, 8, 35, "primitive:double", float.fromhex("0x0.0p+0")),
            (16338, 8, 48, "primitive:double", float.fromhex("0x0.0p+0")),
        ),
    },
)
