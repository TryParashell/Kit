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
            (140, 8, 246, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (148, 8, 259, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (156, 8, 272, "primitive:double", float.fromhex("0x1.0000000000000p-1")),
            (164, 8, 285, "primitive:double", float.fromhex("0x1.4000000000000p-2")),
            (172, 8, 479, "primitive:double", float.fromhex("0x0.0p+0")),
            (180, 8, 492, "primitive:double", float.fromhex("0x0.0p+0")),
            (188, 4, 521, "primitive:int", 0),
            (192, 4, 653, "primitive:int", 1),
            (196, 4, 666, "primitive:int", 0),
            (200, 4, 679, "primitive:int", 1),
            (204, 4, 692, "primitive:int", 1),
            (208, 4, 705, "primitive:int", 1),
            (216, 4, 763, "primitive:int", 1),
            (220, 4, 792, "primitive:int", 1),
            (683, 4, 924, "primitive:int", 0),
        ),
    },
)
