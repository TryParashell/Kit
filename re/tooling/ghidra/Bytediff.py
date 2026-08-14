# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import sys as System
from Layout import FindItem, FindGaps, LoadData


# needed to keep reverse engineering responsibilities isolated and maintainable
def RunsInfo(LabelInfo, NameTextInfo, KindNameInfo):
    DocInfo, SegsInfo, ByteBlob, PartInfoInfo = LoadData(LabelInfo)
    OutputDataInfo = []
    for IndexData in FindItem(SegsInfo, NameTextInfo, KindNameInfo):
        SeqInfo = []
        for ItemData in FindGaps(SegsInfo, IndexData):
            if ItemData[0] == "scalars":
                SeqInfo.append(
                    (
                        "S",
                        ItemData[1],
                        ByteBlob[ItemData[1] : ItemData[1] + ItemData[2]],
                    )
                )
            else:
                SeqInfo.append(("O", ItemData[2], ItemData[3]))
        OutputDataInfo.append((PartInfoInfo.name, IndexData, SeqInfo))
    return OutputDataInfo


# needed to keep reverse engineering responsibilities isolated and maintainable
def MainRun():
    NameTextInfo = System.argv[1]
    LeftInfo, Right = (System.argv[2], System.argv[3])
    KindNameInfo = System.argv[4] if len(System.argv) > 4 else "definition"
    Lrows = RunsInfo(LeftInfo, NameTextInfo, KindNameInfo)
    Rrows = RunsInfo(Right, NameTextInfo, KindNameInfo)
    for (LpInfo, LiInfo, LseqInfo), (RpInfo, RiInfo, RseqInfo) in zip(Lrows, Rrows):
        print(
            f"--- {NameTextInfo}: {LpInfo} node={LiInfo}   vs   {RpInfo} node={RiInfo}"
        )
        if len(LseqInfo) != len(RseqInfo):
            print(f"    SHAPE DIFFERS {len(LseqInfo)} vs {len(RseqInfo)}")
        for PosInfo, (FirstValue, SecondValue) in enumerate(zip(LseqInfo, RseqInfo)):
            if FirstValue[0] != SecondValue[0]:
                print(
                    f"    [{PosInfo}] kind differs {FirstValue[0]} vs {SecondValue[0]}"
                )
                continue
            if FirstValue[0] == "O":
                if FirstValue[1] != SecondValue[1]:
                    print(
                        f"    [{PosInfo}] object class {FirstValue[1]} vs {SecondValue[1]}"
                    )
                continue
            if FirstValue[2] == SecondValue[2]:
                continue
            print(
                f"    [{PosInfo}] scalars n={len(FirstValue[2])}/{len(SecondValue[2])} at {FirstValue[1]}/{SecondValue[1]}"
            )
            for KeyIndex in range(min(len(FirstValue[2]), len(SecondValue[2]))):
                if FirstValue[2][KeyIndex] != SecondValue[2][KeyIndex]:
                    print(
                        f"        +{KeyIndex:4d}  {FirstValue[2][KeyIndex]:02x} -> {SecondValue[2][KeyIndex]:02x}"
                    )


if __name__ == "__main__":
    MainRun()
