# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Owners.Sldmodu.MoThreedViewC.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram = (
    KOwnerSites,
    {
        "AnnotationManager": (
            (230, 4, 3488, "primitive:long", 0),
            (238, 4, 3856, "primitive:long", 0),
            (242, 8, 3923, "primitive:double", float.fromhex("0x0.0p+0")),
            (252, 4, 4072, "primitive:long", 0),
            (256, 4, 4088, "primitive:long", 1),
            (262, 4, 4241, "primitive:long", -1),
            (266, 4, 4316, "primitive:long", 0),
            (270, 4, 4389, "primitive:long", -1),
            (274, 4, 4444, "primitive:long", -1),
            (490, 4, 3488, "primitive:long", 0),
            (498, 4, 3856, "primitive:long", 0),
            (502, 8, 3923, "primitive:double", float.fromhex("0x0.0p+0")),
            (512, 4, 4072, "primitive:long", 0),
            (516, 4, 4088, "primitive:long", 1),
            (522, 4, 4241, "primitive:long", -1),
            (526, 4, 4316, "primitive:long", 0),
            (530, 4, 4389, "primitive:long", -1),
            (534, 4, 4444, "primitive:long", -1),
        ),
    },
)
