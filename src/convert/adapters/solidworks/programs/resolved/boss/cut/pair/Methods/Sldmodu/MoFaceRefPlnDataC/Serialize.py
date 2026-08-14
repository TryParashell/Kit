# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Owners.Sldmodu.MoFaceRefPlnDataC.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (9353, 4, 7121, "primitive:long", 1),
            (9381, 8, 7292, "primitive:double", float.fromhex("0x1.f32cae0a1dfa5p-5")),
            (14677, 4, 7121, "primitive:long", 1),
            (14705, 8, 7292, "primitive:double", float.fromhex("0x1.f32cae0a1dfa5p-5")),
            (19747, 4, 7121, "primitive:long", 1),
            (19775, 8, 7292, "primitive:double", float.fromhex("0x1.f32cae0a1dfa5p-5")),
        ),
    },
)
