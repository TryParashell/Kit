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
            (5645, 8, 22, "primitive:double", float.fromhex("0x0.0p+0")),
            (5653, 8, 35, "primitive:double", float.fromhex("0x0.0p+0")),
            (5661, 8, 48, "primitive:double", float.fromhex("0x0.0p+0")),
            (7692, 8, 22, "primitive:double", float.fromhex("0x0.0p+0")),
            (7700, 8, 35, "primitive:double", float.fromhex("0x0.0p+0")),
            (7708, 8, 48, "primitive:double", float.fromhex("0x0.0p+0")),
            (10965, 8, 22, "primitive:double", float.fromhex("0x0.0p+0")),
            (10973, 8, 35, "primitive:double", float.fromhex("0x0.0p+0")),
            (10981, 8, 48, "primitive:double", float.fromhex("0x0.0p+0")),
            (11021, 8, 22, "primitive:double", float.fromhex("0x0.0p+0")),
            (11029, 8, 35, "primitive:double", float.fromhex("0x0.0p+0")),
            (11037, 8, 48, "primitive:double", float.fromhex("0x0.0p+0")),
            (13573, 8, 22, "primitive:double", float.fromhex("0x0.0p+0")),
            (13581, 8, 35, "primitive:double", float.fromhex("0x0.0p+0")),
            (13589, 8, 48, "primitive:double", float.fromhex("0x0.0p+0")),
            (13629, 8, 22, "primitive:double", float.fromhex("0x0.0p+0")),
            (13637, 8, 35, "primitive:double", float.fromhex("0x0.0p+0")),
            (13645, 8, 48, "primitive:double", float.fromhex("0x0.0p+0")),
            (15329, 8, 22, "primitive:double", float.fromhex("0x0.0p+0")),
            (15337, 8, 35, "primitive:double", float.fromhex("0x0.0p+0")),
            (15345, 8, 48, "primitive:double", float.fromhex("0x0.0p+0")),
        ),
    },
)
