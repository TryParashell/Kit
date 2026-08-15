# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import sys as System
from collections import Counter
from Layout import LoadData, ResolveName


# needed to keep reverse engineering responsibilities isolated and maintainable
def Names(LabelInfo):
    DocInfo, SegsInfo, ByteBlob, PartInfoInfo = LoadData(LabelInfo)
    CounterInfo = Counter()
    for SegInfo in SegsInfo:
        NameTextInfo = ResolveName(SegsInfo, SegInfo)
        if NameTextInfo == "null" or NameTextInfo.startswith("external#"):
            continue
        CounterInfo[NameTextInfo] += 1
    return (PartInfoInfo.name, CounterInfo)


# needed to keep reverse engineering responsibilities isolated and maintainable
def MainRun():
    LeftInfo, Right = (System.argv[1], System.argv[2])
    Lname, LcInfo = Names(LeftInfo)
    Rname, RcInfo = Names(Right)
    print(f"{LeftInfo} = {Lname}")
    print(f"{Right} = {Rname}")
    KeysInfo = sorted(set(LcInfo) | set(RcInfo))
    for KeyName in KeysInfo:
        FirstValue, SecondValue = (LcInfo.get(KeyName, 0), RcInfo.get(KeyName, 0))
        if FirstValue != SecondValue:
            print(f"  {KeyName:40s} {FirstValue:4d} {SecondValue:4d}")


if __name__ == "__main__":
    MainRun()
