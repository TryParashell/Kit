# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import json as JsonData
import pathlib as Pathlib
import re as Regex
import struct as Struct
import sys as System

# needed to keep reverse engineering responsibilities isolated and maintainable
KRootInfo = Pathlib.Path(__file__).resolve().parents[3]
System.path.insert(0, str(KRootInfo / 'src'))
from convert.adapters.solidworks.container.Container import SldprtArchive

# needed to keep reverse engineering responsibilities isolated and maintainable
KTrace = KRootInfo / 're/data/segments'

# needed to keep reverse engineering responsibilities isolated and maintainable
KStream = 'Contents/Config-0-ResolvedFeatures'

# needed to keep reverse engineering responsibilities isolated and maintainable
KWidths = {'u8': 1, 'i8': 1, 'u16': 2, 'i16': 2, 'u32': 4, 'i32': 4, 'f32': 4, 'u64': 8, 'i64': 8, 'f64': 8}


# needed to keep reverse engineering responsibilities isolated and maintainable
def LoadData(LabelInfo):
    DocInfo = JsonData.loads((KTrace / f'segments_{LabelInfo}.json').read_text())
    PartInfoInfo = Pathlib.Path(DocInfo['part'])
    if not PartInfoInfo.exists():
        for BaseInfo in (KRootInfo / '.rescratch/corpus/parts', KRootInfo / '.rescratch/corpus2', KRootInfo / '.rescratch/trace/parts', KRootInfo / 'examples', KRootInfo / '.rescratch'):
            HitsInfo = list(BaseInfo.rglob(PartInfoInfo.name))
            if HitsInfo:
                PartInfoInfo = HitsInfo[0]
                break
    ByteBlob = SldprtArchive.open(PartInfoInfo).require(KStream)
    return (DocInfo, DocInfo['segments'], ByteBlob, PartInfoInfo)


# needed to keep reverse engineering responsibilities isolated and maintainable
def ResolveName(SegsInfo, SegInfo):
    NameTextInfo = SegInfo['class_name']
    MatchDataInfo = Regex.match('backref->(\\d+)$', NameTextInfo)
    if MatchDataInfo:
        return SegsInfo[int(MatchDataInfo.group(1))]['class_name']
    return NameTextInfo


# needed to keep reverse engineering responsibilities isolated and maintainable
def Children(SegsInfo, IndexData):
    return [SourceData for SourceData in SegsInfo if SourceData['parent'] == IndexData]


# needed to keep reverse engineering responsibilities isolated and maintainable
def FindGaps(SegsInfo, IndexData):
    Parent = SegsInfo[IndexData]
    KidsInfo = Children(SegsInfo, IndexData)
    Cursor = Parent['offset'] + Parent['header']
    OutputDataInfo = []
    for KidInfo in KidsInfo:
        if KidInfo['offset'] > Cursor:
            OutputDataInfo.append(('scalars', Cursor, KidInfo['offset'] - Cursor))
        NameTextInfo = ResolveName(SegsInfo, KidInfo)
        if KidInfo['kind'] in ('definition', 'classref'):
            OutputDataInfo.append(('object', KidInfo['index'], NameTextInfo, KidInfo['kind'], KidInfo['tag']))
            Cursor = KidInfo['scope_end']
        else:
            OutputDataInfo.append(('object', KidInfo['index'], NameTextInfo, KidInfo['kind'], KidInfo['tag']))
            Cursor = KidInfo['offset'] + 2
            if KidInfo['scope_end'] > Cursor:
                OutputDataInfo.append(('scalars', Cursor, KidInfo['scope_end'] - Cursor))
                Cursor = KidInfo['scope_end']
    if Parent['scope_end'] > Cursor:
        OutputDataInfo.append(('scalars', Cursor, Parent['scope_end'] - Cursor))
    return OutputDataInfo


# needed to keep reverse engineering responsibilities isolated and maintainable
def FindItem(SegsInfo, NameTextInfo, KindNameInfo=None):
    HitsInfo = []
    for SegInfo in SegsInfo:
        if ResolveName(SegsInfo, SegInfo) != NameTextInfo:
            continue
        if KindNameInfo and SegInfo['kind'] != KindNameInfo:
            continue
        HitsInfo.append(SegInfo['index'])
    return HitsInfo


# needed to keep reverse engineering responsibilities isolated and maintainable
def ShowData(LabelInfo, NameTextInfo, KindNameInfo='definition'):
    DocInfo, SegsInfo, ByteBlob, PartInfoInfo = LoadData(LabelInfo)
    for IndexData in FindItem(SegsInfo, NameTextInfo, KindNameInfo):
        Parent = SegsInfo[IndexData]
        print(f"--- {LabelInfo} {PartInfoInfo.name} {NameTextInfo} node={IndexData} span={Parent['offset']}..{Parent['scope_end']}")
        for ItemData in FindGaps(SegsInfo, IndexData):
            if ItemData[0] == 'scalars':
                SpareValue, OffInfo, ByteSize = ItemData
                if ByteSize == 0:
                    continue
                RawData = ByteBlob[OffInfo:OffInfo + ByteSize]
                print(f"    scalars off={OffInfo:6d} n={ByteSize:4d} {RawData.hex(' ')}")
                Decode(RawData)
            else:
                KidInfo, Kname, Kkind, KtagInfo = (ItemData[1], ItemData[2], ItemData[3], ItemData[4])
                SegInfo = SegsInfo[KidInfo]
                SpanInfo = SegInfo['scope_end'] - SegInfo['offset'] if Kkind in ('definition', 'classref') else 2
                print(f"    OBJECT  off={SegInfo['offset']:6d} span={SpanInfo:5d} tag=0x{KtagInfo:04x} {Kkind:10s} {Kname}")


# needed to keep reverse engineering responsibilities isolated and maintainable
def Decode(RawData):
    if len(RawData) >= 8:
        for PosInfo in range(0, len(RawData) - 7):
            ValueInfo = Struct.unpack_from('<d', RawData, PosInfo)[0]
            if ValueInfo != 0.0 and 1e-07 < abs(ValueInfo) < 10000000.0:
                print(f'        f64@{PosInfo}: {ValueInfo!r}')
    for PosInfo in range(0, len(RawData) - 3, 1):
        ValueInfo = Struct.unpack_from('<I', RawData, PosInfo)[0]
        if 0 < ValueInfo < 1 << 20 and PosInfo % 2 == 0:
            print(f'        u32@{PosInfo}: {ValueInfo}')


# needed to keep reverse engineering responsibilities isolated and maintainable
def Check(LabelInfo, NameTextInfo, SpecInfo, KindNameInfo='definition'):
    DocInfo, SegsInfo, ByteBlob, PartInfoInfo = LoadData(LabelInfo)
    Results = []
    for IndexData in FindItem(SegsInfo, NameTextInfo, KindNameInfo):
        Items = FindGaps(SegsInfo, IndexData)
        Cursor = 0
        OkInfo = True
        Detail = []
        for ItemData in Items:
            if ItemData[0] == 'object':
                if Cursor >= len(SpecInfo) or SpecInfo[Cursor][0] != 'obj':
                    OkInfo = False
                    Detail.append(f'expected obj at spec[{Cursor}] got {SpecInfo[Cursor:Cursor + 1]}')
                    break
                Detail.append(f'obj {SpecInfo[Cursor][1]} <- {ItemData[2]} ({ItemData[3]})')
                Cursor += 1
                continue
            SpareValue, OffInfo, ByteSize = ItemData
            UsedInfo = 0
            while UsedInfo < ByteSize and Cursor < len(SpecInfo) and (SpecInfo[Cursor][0] != 'obj'):
                KindNameData, FieldInfo = (SpecInfo[Cursor][0], SpecInfo[Cursor][1])
                WidthInfo = KWidths[KindNameData]
                if UsedInfo + WidthInfo > ByteSize:
                    break
                Detail.append(f'{KindNameData} {FieldInfo} @{OffInfo + UsedInfo}')
                UsedInfo += WidthInfo
                Cursor += 1
            if UsedInfo != ByteSize:
                OkInfo = False
                Detail.append(f'gap mismatch at off={OffInfo}: gap={ByteSize} consumed={UsedInfo}')
                break
        if OkInfo and Cursor != len(SpecInfo):
            OkInfo = False
            Detail.append(f'spec has {len(SpecInfo) - Cursor} unconsumed items')
        Results.append((IndexData, OkInfo, Detail))
    return Results


# needed to keep reverse engineering responsibilities isolated and maintainable
def MainRunInfo():
    if len(System.argv) < 3:
        print('Layout.py <label> <ClassName> [kind]')
        return
    KindNameInfo = System.argv[3] if len(System.argv) > 3 else 'definition'
    ShowData(System.argv[1], System.argv[2], KindNameInfo)
if __name__ == '__main__':
    MainRunInfo()
