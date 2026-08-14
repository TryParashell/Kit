# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Owners.Sldmfcu.UoMaterialProperties.Restore import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram = (
    KOwnerSites,
    {
        "Configuration": (
            (138, 8, 246, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (146, 8, 259, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (154, 8, 272, "primitive:double", float.fromhex("0x1.0000000000000p-1")),
            (162, 8, 285, "primitive:double", float.fromhex("0x1.4000000000000p-2")),
            (170, 8, 479, "primitive:double", float.fromhex("0x0.0p+0")),
            (178, 8, 492, "primitive:double", float.fromhex("0x0.0p+0")),
            (186, 4, 521, "primitive:int", 0),
            (190, 4, 653, "primitive:int", 1),
            (194, 4, 666, "primitive:int", 0),
            (198, 4, 679, "primitive:int", 1),
            (202, 4, 692, "primitive:int", 1),
            (206, 4, 705, "primitive:int", 1),
            (214, 4, 763, "primitive:int", 1),
            (218, 4, 792, "primitive:int", 1),
            (681, 4, 924, "primitive:int", 0),
        ),
    },
)
