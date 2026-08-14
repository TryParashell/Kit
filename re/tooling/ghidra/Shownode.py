# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import struct as Struct
import sys as System
import Layout as Layout


# needed to keep reverse engineering responsibilities isolated and maintainable
def DumpData(LabelInfo, NameTextInfo, KindNameInfo, Limit):
    DocInfo, SegsInfo, ByteBlob, PartInfoInfo = Layout.LoadData(LabelInfo)
    print(f'=== {LabelInfo} {PartInfoInfo.name} {NameTextInfo} {KindNameInfo}')
    HitsInfo = Layout.FindItem(SegsInfo, NameTextInfo, KindNameInfo)
    for IndexData in HitsInfo[:Limit]:
        Parent = SegsInfo[IndexData]
        print(f"--- node={IndexData} kind={Parent['kind']} span={Parent['offset']}..{Parent['scope_end']} hdr={Parent['header']}")
        for ItemData in Layout.FindGaps(SegsInfo, IndexData):
            if ItemData[0] == 'scalars':
                OffInfo, ByteSize = (ItemData[1], ItemData[2])
                RawData = ByteBlob[OffInfo:OffInfo + ByteSize]
                HeadInfo = RawData[:96].hex(' ')
                print(f'  scalars off={OffInfo} n={ByteSize} {HeadInfo}')
                for PosInfo in range(0, min(ByteSize, 96) - 3, 4):
                    ValueInfo = Struct.unpack_from('<I', RawData, PosInfo)[0]
                    print(f'      u32@{PosInfo}=0x{ValueInfo:08x} {ValueInfo}')
            else:
                KidInfo = SegsInfo[ItemData[1]]
                SpanInfo = KidInfo['scope_end'] - KidInfo['offset'] if ItemData[3] in ('definition', 'classref') else 2
                print(f"  OBJ off={KidInfo['offset']} span={SpanInfo} tag=0x{ItemData[4]:04x} {ItemData[3]} {ItemData[2]}")


# needed to keep reverse engineering responsibilities isolated and maintainable
def MainRunInfo():
    LabelInfo = System.argv[1]
    NameTextInfo = System.argv[2]
    KindNameInfo = System.argv[3] if len(System.argv) > 3 else 'definition'
    Limit = int(System.argv[4]) if len(System.argv) > 4 else 2
    DumpData(LabelInfo, NameTextInfo, KindNameInfo, Limit)
if __name__ == '__main__':
    MainRunInfo()
