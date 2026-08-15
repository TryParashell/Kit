# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoThreedViewC.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "Contents/CMgr": (
            (365, 4, 9208, "primitive:int", 5),
            (369, 4, 9386, "primitive:int", -2147221120),
            (377, 4, 9593, "primitive:ulong", 28),
            (381, 4, 9687, "primitive:ulong", 113),
            (385, 4, 9856, "primitive:ulong", 0),
            (651, 4, 10585, "primitive:int", 0),
            (655, 1, 10656, "primitive:uchar", 0),
            (656, 1, 10730, "primitive:uchar", 0),
            (659, 4, 11222, "primitive:ulong", 18000),
            (663, 1, 11284, "primitive:uchar", 1),
            (664, 1, 11596, "primitive:uchar", 0),
            (669, 4, 11910, "primitive:int", 0),
            (673, 4, 11926, "primitive:int", 1),
            (677, 4, 12494, "primitive:int", 0),
            (681, 4, 12644, "primitive:int", 0),
            (685, 4, 12709, "primitive:int", 1),
            (689, 4, 12739, "primitive:float", float.fromhex("-0x1.0000000000000p+0")),
            (693, 4, 12739, "primitive:float", float.fromhex("-0x1.0000000000000p+0")),
            (697, 4, 12815, "primitive:int", 0),
            (701, 4, 12922, "primitive:int", 0),
            (705, 4, 13138, "primitive:int", 1),
            (709, 4, 13206, "primitive:int", 0),
            (713, 4, 13235, "primitive:int", 0),
            (717, 4, 13235, "primitive:int", 0),
            (721, 4, 13235, "primitive:int", 0),
            (725, 4, 13235, "primitive:int", 0),
            (729, 4, 13235, "primitive:int", 0),
            (733, 4, 13235, "primitive:int", 0),
            (737, 4, 13261, "primitive:int", 1),
            (741, 4, 13364, "primitive:int", 0),
            (745, 4, 13831, "primitive:int", -1),
            (749, 4, 13890, "primitive:int", 1),
            (753, 4, 14017, "primitive:int", 0),
            (757, 4, 14783, "primitive:int", 0),
            (761, 4, 15182, "primitive:int", 0),
            (769, 4, 16020, "primitive:int", 0),
            (773, 4, 16245, "primitive:int", 0),
            (787, 4, 16869, "primitive:int", 0),
            (791, 4, 17194, "primitive:int", 0),
            (801, 4, 17798, "primitive:int", 0),
            (805, 4, 18253, "primitive:long", 0),
            (809, 4, 18736, "primitive:long", 0),
            (813, 4, 18989, "primitive:long", 0),
            (821, 4, 19240, "primitive:long", 0),
            (829, 4, 19435, "primitive:long", 0),
            (833, 4, 19525, "primitive:long", 0),
            (837, 4, 19615, "primitive:long", 0),
            (843, 4, 20833, "primitive:long", 0),
            (1599, 4, 22843, "primitive:ulong", 203),
            (2040, 4, 22843, "primitive:ulong", 203),
            (2464, 4, 22843, "primitive:ulong", 203),
            (2888, 4, 22843, "primitive:ulong", 203),
            (3312, 4, 22843, "primitive:ulong", 203),
        ),
        "Contents/Config-0": (
            (4944, 4, 2363, "primitive:long", -1431655766),
            (4948, 4, 2379, "primitive:long", -1145324613),
        ),
        "Contents/Config-0-ResolvedFeatures": (
            (751, 4, 22843, "primitive:ulong", 203),
            (807, 4, 22843, "primitive:ulong", 203),
            (863, 4, 22843, "primitive:ulong", 203),
            (919, 4, 22843, "primitive:ulong", 203),
            (975, 4, 22843, "primitive:ulong", 203),
        ),
    },
)
