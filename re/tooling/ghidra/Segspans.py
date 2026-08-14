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
import sys as System
from collections import defaultdict as Defaultdict

# needed to keep reverse engineering responsibilities isolated and maintainable
KRootInfo = Pathlib.Path(__file__).resolve().parents[3]

# needed to keep reverse engineering responsibilities isolated and maintainable
KTrace = KRootInfo / 're/data/segments'


# needed to keep reverse engineering responsibilities isolated and maintainable
def LoadData():
    OutputDataInfo = {}
    for PathInfoData in sorted(KTrace.glob('segments_*.json')):
        OutputDataInfo[PathInfoData.stem[len('segments_'):]] = JsonData.loads(PathInfoData.read_text())
    return OutputDataInfo


# needed to keep reverse engineering responsibilities isolated and maintainable
def ResolveInfo(DocInfo):
    SegsInfo = DocInfo['segments']
    ByObj = {}
    for SegInfo in SegsInfo:
        if SegInfo['kind'] in ('definition', 'classref'):
            ByObj[SegInfo['object_index']] = SegInfo
    Names = []
    for SegInfo in SegsInfo:
        NameTextInfo = SegInfo['class_name']
        MatchDataInfo = Regex.match('backref->(\\d+)$', NameTextInfo)
        if MatchDataInfo:
            TgtInfo = SegsInfo[int(MatchDataInfo.group(1))]
            NameTextInfo = TgtInfo['class_name']
        Names.append(NameTextInfo)
    return (SegsInfo, Names)


# needed to keep reverse engineering responsibilities isolated and maintainable
def MainRun():
    WantInfo = [FirstValue for FirstValue in System.argv[1:]]
    DocsInfo = LoadData()

    # needed to keep reverse engineering responsibilities isolated and maintainable
    Table = Defaultdict(lambda: Defaultdict(list))
    for LabelInfo, DocInfo in DocsInfo.items():
        SegsInfo, Names = ResolveInfo(DocInfo)
        for SegInfo, NameTextInfo in zip(SegsInfo, Names):
            if WantInfo and (not any((WordData.lower() in NameTextInfo.lower() for WordData in WantInfo))):
                continue
            Table[NameTextInfo][LabelInfo].append((SegInfo['offset'], SegInfo['length'], SegInfo['depth'], SegInfo['kind']))
    for NameTextInfo in sorted(Table):
        print('=' * 70)
        print(NameTextInfo)
        for LabelInfo in sorted(Table[NameTextInfo]):
            GetRows = Table[NameTextInfo][LabelInfo]
            LensInfo = sorted({ResultData[1] for ResultData in GetRows})
            print(f'  {LabelInfo:18s} n={len(GetRows):4d} lengths={LensInfo}')
            for OffInfo, LnInfo, Depth, KindNameInfo in GetRows[:12]:
                print(f'      off={OffInfo:6d} len={LnInfo:5d} depth={Depth} kind={KindNameInfo}')
if __name__ == '__main__':
    MainRun()
