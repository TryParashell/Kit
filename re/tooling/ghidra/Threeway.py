# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import sys as System
from Layout import FindGaps, LoadData, ResolveName


# needed to keep reverse engineering responsibilities isolated and maintainable
def Collect(LabelInfo, Names):
    DocInfo, SegsInfo, ByteBlob, PartInfoInfo = LoadData(LabelInfo)
    OutputDataInfo = []
    for SegInfo in SegsInfo:
        NameTextInfo = ResolveName(SegsInfo, SegInfo)
        if NameTextInfo not in Names:
            continue
        if SegInfo['kind'] not in ('definition', 'classref'):
            continue
        SeqInfo = []
        for ItemData in FindGaps(SegsInfo, SegInfo['index']):
            if ItemData[0] == 'scalars':
                SeqInfo.append(('S', ItemData[1], ByteBlob[ItemData[1]:ItemData[1] + ItemData[2]]))
            else:
                SeqInfo.append(('O', ItemData[2], ItemData[3]))
        OutputDataInfo.append((SegInfo['index'], NameTextInfo, SegInfo['kind'], SegInfo['offset'], SeqInfo))
    return (PartInfoInfo.name, OutputDataInfo)


# needed to keep reverse engineering responsibilities isolated and maintainable
def Shape(SeqInfo):
    return tuple(((ErrorInfo[0], len(ErrorInfo[2]) if ErrorInfo[0] == 'S' else 0) for ErrorInfo in SeqInfo))


# needed to keep reverse engineering responsibilities isolated and maintainable
def MainRunInfo():
    LabelInfo = System.argv[1]
    Names = set(System.argv[2:]) or {'moExtrusion_c', 'moICE_c'}
    PartInfoInfo, GetRows = Collect(LabelInfo, Names)
    print(f'{LabelInfo} = {PartInfoInfo}')
    for IndexData, NameTextInfo, KindNameInfo, Offset, SeqInfo in GetRows:
        print(f'  node={IndexData:4d} {KindNameInfo:10s} off={Offset:6d} {NameTextInfo} shape={Shape(SeqInfo)}')
    Groups = {}
    for RowDataInfo in GetRows:
        Groups.setdefault(Shape(RowDataInfo[4]), []).append(RowDataInfo)
    for KeyName, Members in Groups.items():
        if len(Members) < 2:
            continue
        print(f'--- shape group with {len(Members)} members')
        BaseInfo = Members[0]
        for Other in Members[1:]:
            print(f'    node {BaseInfo[0]} vs {Other[0]}')
            for PosInfo, (FirstValue, SecondValue) in enumerate(zip(BaseInfo[4], Other[4])):
                if FirstValue[0] != 'S' or FirstValue[2] == SecondValue[2]:
                    continue
                Diffs = [KeyIndex for KeyIndex in range(len(FirstValue[2])) if FirstValue[2][KeyIndex] != SecondValue[2][KeyIndex]]
                print(f'      [{PosInfo}] n={len(FirstValue[2])} ndiff={len(Diffs)} at {Diffs[:24]}')
                for KeyIndex in Diffs[:24]:
                    print(f'          +{KeyIndex:4d} {FirstValue[2][KeyIndex]:02x} -> {SecondValue[2][KeyIndex]:02x}')
if __name__ == '__main__':
    MainRunInfo()
