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
KHandleClasses = ('sgEntHandle', 'sgLineHandle', 'sgArcHandle', 'sgPointHandle')


# needed to keep reverse engineering responsibilities isolated and maintainable
def ScalarRuns(SegsInfo, IndexData, ByteBlob):
    RunsInfo = []
    for ItemData in Layout.FindGaps(SegsInfo, IndexData):
        if ItemData[0] == 'scalars' and ItemData[2] > 0:
            RunsInfo.append((ItemData[1], ByteBlob[ItemData[1]:ItemData[1] + ItemData[2]]))
    return RunsInfo


# needed to keep reverse engineering responsibilities isolated and maintainable
def DecodeHandle(RawData):
    if len(RawData) < 2:
        return None
    EntInfo = Struct.unpack_from('<H', RawData, 0)[0]
    Cursor = 2
    if EntInfo == 30591:
        if len(RawData) < 6:
            return None
        EntInfo = Struct.unpack_from('<i', RawData, 2)[0]
        Cursor = 6
    if len(RawData) < Cursor + 8:
        return None
    RefId = Struct.unpack_from('<i', RawData, Cursor)[0]
    DimOnCm = Struct.unpack_from('<i', RawData, Cursor + 4)[0]
    return {'bytes': Cursor + 8, 'escaped': Cursor == 6, 'EntIndex': EntInfo, 'RefId': RefId, 'DimOnCM': DimOnCm}


# needed to keep reverse engineering responsibilities isolated and maintainable
def MainRunInfo():
    Report = {}
    Total = 0
    Passed = 0
    Tally = Collects.Counter()
    EntValues = Collects.Counter()
    RefValues = Collects.Counter()
    DimValues = Collects.Counter()
    for LabelInfo in KLabels:
        DocInfo, SegsInfo, ByteBlob, PartInfoInfo = Layout.LoadData(LabelInfo)
        GetRows = []
        for NameTextInfo in KHandleClasses:
            for KindNameInfo in ('definition', 'classref'):
                for IndexData in Layout.FindItem(SegsInfo, NameTextInfo, KindNameInfo):
                    RunsInfo = ScalarRuns(SegsInfo, IndexData, ByteBlob)
                    Total += 1
                    if not RunsInfo:
                        GetRows.append({'node': IndexData, 'class': NameTextInfo, 'kind': KindNameInfo, 'ok': False})
                        Tally[NameTextInfo, KindNameInfo, 'no-scalars'] += 1
                        continue
                    Offset, RawData = RunsInfo[0]
                    DecodedInfo = DecodeHandle(RawData)
                    OkInfo = DecodedInfo is not None and DecodedInfo['bytes'] == len(RawData)
                    if OkInfo:
                        Passed += 1
                        EntValues[DecodedInfo['EntIndex']] += 1
                        RefValues[DecodedInfo['RefId']] += 1
                        DimValues[DecodedInfo['DimOnCM']] += 1
                    Tally[NameTextInfo, KindNameInfo, 'ok' if OkInfo else 'mismatch'] += 1
                    GetRows.append({'node': IndexData, 'class': NameTextInfo, 'kind': KindNameInfo, 'ok': OkInfo, 'first_run_bytes': len(RawData), 'extra_runs': len(RunsInfo) - 1, 'decoded': DecodedInfo})
        Report[LabelInfo] = {'part': PartInfoInfo.name, 'handles': GetRows}
    for KeyName in sorted(Tally):
        print(f'{KeyName[0]:16s} {KeyName[1]:11s} {KeyName[2]:12s} {Tally[KeyName]}')
    print(f'sgEntHandle chain: {Passed}/{Total} traced handle records tile exactly')
    print(f'EntIndex distinct={len(EntValues)} escaped_sentinel_used=0x777f')
    print(f'RefId  values {dict(sorted(RefValues.items())[:8])}')
    print(f'DimOnCM values {dict(sorted(DimValues.items())[:8])}')
    KOutInfo.mkdir(parents=True, exist_ok=True)
    (KOutInfo / 'VerifySketch.json').write_text(JsonData.dumps(Report, indent=1))
    return 0 if Passed == Total else 1
if __name__ == '__main__':
    System.exit(MainRunInfo())
