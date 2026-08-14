# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Owners.Sldmodu.MoReferenceCurveC.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (8020, 4, 3909, "primitive:ulong", 6),
            (8024, 4, 3928, "primitive:long", -1),
            (8028, 4, 3941, "primitive:long", 0),
            (8032, 4, 3954, "primitive:long", 0),
            (8036, 4, 3967, "primitive:ulong", 5),
            (8040, 4, 3986, "primitive:ulong", 5),
            (8048, 2, 4030, "primitive:ushort", 0),
            (8050, 4, 4154, "primitive:ulong", 4294967295),
            (8054, 4, 4250, "primitive:ulong", 0),
            (8062, 4, 4466, "primitive:long", 0),
            (8066, 4, 4482, "primitive:long", 0),
            (8070, 4, 4540, "primitive:long", 0),
        ),
    },
)
