# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Sldmfcu.UtLineWidthPrintDataC.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "Contents/Config-0": (
            (21740, 4, 108, "primitive:float", float.fromhex("0x1.797cc40000000p-13")),
            (21744, 4, 108, "primitive:float", float.fromhex("0x1.0624de0000000p-12")),
            (21748, 4, 108, "primitive:float", float.fromhex("0x1.6f00680000000p-12")),
            (21752, 4, 108, "primitive:float", float.fromhex("0x1.0624de0000000p-11")),
            (21756, 4, 108, "primitive:float", float.fromhex("0x1.6f00680000000p-11")),
            (21760, 4, 108, "primitive:float", float.fromhex("0x1.0624de0000000p-10")),
            (21764, 4, 108, "primitive:float", float.fromhex("0x1.6f00680000000p-10")),
            (21768, 4, 108, "primitive:float", float.fromhex("0x1.0624de0000000p-9")),
        ),
    },
)
