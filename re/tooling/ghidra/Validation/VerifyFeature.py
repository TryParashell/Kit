# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import collections as Collects
import json as JsonData
import pathlib as Pathlib
import struct as Struct
import sys as System
import Layout as Layout

# needed to keep reverse engineering responsibilities isolated and maintainable
KOutInfo = Pathlib.Path(__file__).resolve().parents[4] / 're/data'

# needed to keep reverse engineering responsibilities isolated and maintainable
KLabels = ['baseline', 'circle', 'planetop', 'twopad', 'padplane', 'cutbase', 'three', 'vendor_ring', 'vendor_cojinete']

# needed to keep reverse engineering responsibilities isolated and maintainable
KStringMarker = bytes.fromhex('fffeff')


# needed to keep reverse engineering responsibilities isolated and maintainable
def ReadString(ByteBlob, Cursor):
    if ByteBlob[Cursor:Cursor + 3] != KStringMarker:
        return None
    CountInfo = ByteBlob[Cursor + 3]
    if CountInfo == 255:
        CountInfo = Struct.unpack_from('<H', ByteBlob, Cursor + 4)[0]
        HeadInfo = Cursor + 6
    else:
        HeadInfo = Cursor + 4
    EndIndex = HeadInfo + 2 * CountInfo
    if EndIndex > len(ByteBlob):
        return None
    try:
        TextValueData = ByteBlob[HeadInfo:EndIndex].decode('utf-16-le')
    except UnicodeDecodeError:
        return None
    return (TextValueData, EndIndex)


# needed to keep reverse engineering responsibilities isolated and maintainable
def DecodeNode(ByteBlob, Cursor, Limit):
    NameTextInfo = ReadString(ByteBlob, Cursor)
    if NameTextInfo is None:
        return None
    TextValueData, Cursor = NameTextInfo
    if Cursor + 16 > Limit:
        return None
    WordZeroC = Struct.unpack_from('<I', ByteBlob, Cursor)[0]
    Flags = Struct.unpack_from('<I', ByteBlob, Cursor + 4)[0]
    NodeId = Struct.unpack_from('<i', ByteBlob, Cursor + 8)[0]
    WordTwoC = Struct.unpack_from('<I', ByteBlob, Cursor + 12)[0]
    Cursor += 16
    Trailer = ReadString(ByteBlob, Cursor)
    if Trailer is None:
        return None
    TrailerText, Cursor = Trailer
    return {'name': TextValueData, 'word@0x0c': WordZeroC, 'flags@0x28': Flags, 'id@0x08': NodeId, 'word@0x2c': WordTwoC, 'trailer@0x20': TrailerText, 'end': Cursor}


# needed to keep reverse engineering responsibilities isolated and maintainable
def NodeRecords(SegsInfo, ByteBlob, IndexData):
    Parent = SegsInfo[IndexData]
    KidsInfo = [SegInfo for SegInfo in SegsInfo if SegInfo['parent'] == IndexData]
    if not KidsInfo:
        return None
    First = KidsInfo[0]
    if First['offset'] != Parent['offset'] + Parent['header']:
        return None
    BodyInfo = First['offset'] + (2 if First['kind'] in ('classref', 'objectref') else 0)
    if First['kind'] not in ('classref', 'objectref'):
        return None
    return DecodeNode(ByteBlob, BodyInfo, Parent['scope_end'])


# needed to keep reverse engineering responsibilities isolated and maintainable
def MainRunInfo():
    Report = {}
    Total = 0
    DecodedInfo = 0
    FlagsSeen = Collects.Counter()
    ByClass = Collects.Counter()
    for LabelInfo in KLabels:
        DocInfo, SegsInfo, ByteBlob, PartInfoInfo = Layout.LoadData(LabelInfo)
        GetRows = []
        for SegInfo in SegsInfo:
            if SegInfo['kind'] != 'definition' and SegInfo['kind'] != 'classref':
                continue
            NameTextInfo = Layout.ResolveName(SegsInfo, SegInfo)
            if not NameTextInfo.startswith('mo'):
                continue
            Record = NodeRecords(SegsInfo, ByteBlob, SegInfo['index'])
            if Record is None:
                continue
            Total += 1
            DecodedInfo += 1
            FlagsSeen[Record['flags@0x28']] += 1
            ByClass[NameTextInfo] += 1
            GetRows.append({'node': SegInfo['index'], 'class': NameTextInfo, **Record})
        Report[LabelInfo] = {'part': PartInfoInfo.name, 'nodes': GetRows}
        for RowDataInfo in GetRows:
            print(f"{LabelInfo:16s} {RowDataInfo['class'][:26]:26s} node={RowDataInfo['node']:4d} name={RowDataInfo['name'][:26]:26s} flags=0x{RowDataInfo['flags@0x28']:08x} id={RowDataInfo['id@0x08']:6d} w0c=0x{RowDataInfo['word@0x0c']:08x} w2c=0x{RowDataInfo['word@0x2c']:08x}")
    print(f'moNode_c prefix decoded on {DecodedInfo}/{Total} candidate objects')
    print('distinct tree-flags words:')
    for ValueInfo, CountInfo in sorted(FlagsSeen.items()):
        print(f'  0x{ValueInfo:08x} n={CountInfo}')
    print(f'classes covered: {len(ByClass)}')
    KOutInfo.mkdir(parents=True, exist_ok=True)
    (KOutInfo / 'VerifyFeature.json').write_text(JsonData.dumps(Report, indent=1))
    return 0 if DecodedInfo == Total and DecodedInfo else 1
if __name__ == '__main__':
    System.exit(MainRunInfo())
