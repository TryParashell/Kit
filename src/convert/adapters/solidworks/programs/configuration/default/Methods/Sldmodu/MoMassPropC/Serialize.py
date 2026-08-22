# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoMassPropC.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "Configuration": (
            (24725, 8, 724, "primitive:double", float.fromhex("0x0.0p+0")),
            (24733, 8, 737, "primitive:double", float.fromhex("0x0.0p+0")),
            (24741, 8, 750, "primitive:double", float.fromhex("0x1.47ae147ae147bp-8")),
            (24749, 8, 783, "primitive:double", float.fromhex("0x1.0c6f7a0b5ed8ep-17")),
            (24757, 8, 796, "primitive:double", float.fromhex("0x1.6f0068db8bac7p-9")),
            (24765, 8, 809, "primitive:double", float.fromhex("0x1.0624dd2f1a9fdp-7")),
            (24773, 8, 822, "primitive:double", float.fromhex("0x1.65e9f80f29213p-22")),
            (24781, 8, 835, "primitive:double", float.fromhex("0x1.303a12d9afc2ap-20")),
            (24789, 8, 848, "primitive:double", float.fromhex("0x1.65e9f80f29213p-20")),
            (24797, 8, 861, "primitive:double", float.fromhex("0x0.0p+0")),
            (24805, 8, 874, "primitive:double", float.fromhex("0x0.0p+0")),
            (24813, 8, 887, "primitive:double", float.fromhex("0x0.0p+0")),
            (24821, 4, 952, "primitive:long", 1),
            (24825, 4, 1017, "primitive:long", 0),
            (24829, 4, 1082, "primitive:long", 0),
            (24833, 4, 1149, "primitive:long", 0),
            (24837, 4, 1236, "primitive:long", 0),
            (24841, 8, 1430, "primitive:double", float.fromhex("0x1.fd70a3d70a3d7p-1")),
            (24849, 4, 1499, "primitive:long", 0),
            (24853, 4, 1515, "primitive:long", 0),
            (24857, 4, 1531, "primitive:long", 0),
            (24861, 4, 1547, "primitive:long", 0),
            (24873, 4, 1728, "primitive:long", 0),
            (24877, 8, 1843, "primitive:double", float.fromhex("0x0.0p+0")),
            (24885, 8, 1859, "primitive:double", float.fromhex("0x0.0p+0")),
            (24893, 8, 1875, "primitive:double", float.fromhex("0x0.0p+0")),
            (24917, 8, 1979, "primitive:double", float.fromhex("0x0.0p+0")),
            (24941, 8, 1995, "primitive:double", float.fromhex("0x0.0p+0")),
            (24965, 8, 2011, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (24973, 4, 2089, "primitive:long", 1),
            (24977, 2, 2140, "primitive:ushort", 0),
        ),
    },
)
