# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Sldmfcu.MoSectionLabelDataC.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "Configuration": (
            (13769, 8, 210, "primitive:double", float.fromhex("0x1.a027525460aa6p-8")),
            (13777, 8, 226, "primitive:double", float.fromhex("0x1.0a569b17481b2p-9")),
            (13785, 8, 242, "primitive:double", float.fromhex("0x1.a027525460aa6p-7")),
            (13793, 4, 258, "primitive:int", 0),
            (13797, 4, 291, "primitive:int", 0),
            (13801, 4, 353, "primitive:int", 0),
            (13805, 4, 386, "primitive:int", 1),
            (13809, 4, 419, "primitive:int", 1),
        ),
    },
)
