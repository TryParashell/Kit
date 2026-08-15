# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Owners.Sldmfcu.MoSectionLabelDataC.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram = (
    KOwnerSites,
    {
        "Contents/Config-0": (
            (14347, 8, 210, "primitive:double", float.fromhex("0x1.a027525460aa6p-8")),
            (14355, 8, 226, "primitive:double", float.fromhex("0x1.0a569b17481b2p-9")),
            (14363, 8, 242, "primitive:double", float.fromhex("0x1.a027525460aa6p-7")),
            (14371, 4, 258, "primitive:int", 0),
            (14375, 4, 291, "primitive:int", 0),
            (14379, 4, 353, "primitive:int", 0),
            (14383, 4, 386, "primitive:int", 1),
            (14387, 4, 419, "primitive:int", 1),
        ),
    },
)
