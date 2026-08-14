# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import sys as System
from Layout import FindItem, FindGaps, LoadData, ResolveName

# needed to keep reverse engineering responsibilities isolated and maintainable
KLabels = [
    "baseline",
    "circle",
    "planetop",
    "twopad",
    "padplane",
    "cutbase",
    "three",
    "vendor_ring",
    "vendor_cojinete",
]


# needed to keep reverse engineering responsibilities isolated and maintainable
def GetRows(LabelInfo, NameTextInfo, KindNameInfo):
    DocInfo, SegsInfo, ByteBlob, PartInfoInfo = LoadData(LabelInfo)
    OutputDataInfo = []
    for IndexData in FindItem(SegsInfo, NameTextInfo, KindNameInfo):
        SeqInfo = []
        for ItemData in FindGaps(SegsInfo, IndexData):
            if ItemData[0] == "scalars":
                SeqInfo.append(
                    (
                        "S",
                        ItemData[2],
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
    KindNameInfo = System.argv[2] if len(System.argv) > 2 else "definition"
    for LabelInfo in KLabels:
        try:
            DataValue = GetRows(LabelInfo, NameTextInfo, KindNameInfo)
        except Exception as Problem:
            print(LabelInfo, "ERROR", Problem)
            continue
        for PartInfoInfo, IndexData, SeqInfo in DataValue:
            if "-bytes" in System.argv:
                print(f"{LabelInfo:16s} {PartInfoInfo[:30]:30s} node={IndexData:4d}")
                for Entry in SeqInfo:
                    if Entry[0] == "S":
                        print(f"    S{Entry[1]:<5d} {Entry[2].hex(' ')}")
                    else:
                        print(f"    O     {Entry[1]} ({Entry[2]})")
                continue
            SigInfo = " ".join(
                (
                    f"{KeyIndex}{ValueData}" if KeyIndex == "S" else f"O:{ValueData}"
                    for KeyIndex, ValueData, *SpareValue in SeqInfo
                )
            )
            print(
                f"{LabelInfo:16s} {PartInfoInfo[:26]:26s} node={IndexData:4d} {SigInfo}"
            )


if __name__ == "__main__":
    MainRun()
