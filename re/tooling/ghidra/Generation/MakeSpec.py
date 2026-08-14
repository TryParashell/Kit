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

# needed to keep reverse engineering responsibilities isolated and maintainable
KRootInfo = Pathlib.Path(__file__).resolve().parents[4]

# needed to keep reverse engineering responsibilities isolated and maintainable
KTrace = KRootInfo / 're/data/segments'

# needed to keep reverse engineering responsibilities isolated and maintainable
KOutInfo = KRootInfo / '.rescratch/ghidra/out'

# needed to keep reverse engineering responsibilities isolated and maintainable
KGhInfo = KRootInfo / 're/tooling/ghidra'

# needed to keep reverse engineering responsibilities isolated and maintainable
KPriority = ['moExtrusion_c', 'moICE_c', 'moEndSpec_c', 'moFromEndSpec_c', 'moRevEndSpec_c', 'moRevolution_c', 'moRevolutionThin_c', 'moRevCut_c', 'moCut_c', 'moProfileFeature_c', 'moOriginProfileFeature_c', 'moLengthParameter_c', 'moAngleParameter_c', 'moBodyFeature_c', 'moFeature_c', 'moModelFeature_c', 'moCompFeature_c', 'moPerBodyChooserData_c', 'moFaceRef_c', 'moFR_c', 'moBBoxCenterData_c', 'moDisplayDistanceDim_c', 'moFeatureDimHandle_c', 'moFavoriteHandle_c', 'sgSketch', 'sgArc', 'sgLine', 'sgSpline', 'sgPoint', 'sgEntHandle', 'sgArcHandle', 'sgLineHandle', 'sgSplineHandle', 'sgPointHandle', 'sgDim', 'sgLogDim', 'moHistoryFeatItemData_c', 'moSketchChain_c', 'moSketchRegion_c']


# needed to keep reverse engineering responsibilities isolated and maintainable
def Observed():
    Names = set()
    for PathInfoData in sorted(KTrace.glob('segments_*.json')):
        DocInfo = JsonData.loads(PathInfoData.read_text())
        SegsInfo = DocInfo['segments']
        for SegInfo in SegsInfo:
            NameTextInfo = SegInfo['class_name']
            MatchDataInfo = Regex.match('backref->(\\d+)$', NameTextInfo)
            if MatchDataInfo:
                NameTextInfo = SegsInfo[int(MatchDataInfo.group(1))]['class_name']
            if NameTextInfo in ('null',) or NameTextInfo.startswith('external#') or NameTextInfo.startswith('backref->'):
                continue
            Names.add(NameTextInfo)
    return Names


# needed to keep reverse engineering responsibilities isolated and maintainable
def MainRunInfo():
    SmapInfo = JsonData.loads((KOutInfo / 'SerializeMap.json').read_text())
    WantInfo = []
    for NameTextInfo in KPriority:
        if NameTextInfo in SmapInfo:
            WantInfo.append(NameTextInfo)
    for NameTextInfo in sorted(Observed()):
        if NameTextInfo in SmapInfo and NameTextInfo not in WantInfo:
            WantInfo.append(NameTextInfo)
    Lines = []
    SeenInfo = set()
    GetRows = []
    for NameTextInfo in WantInfo:
        AddrInfo = SmapInfo[NameTextInfo]['serialize_addr']
        GetRows.append((NameTextInfo, AddrInfo, SmapInfo[NameTextInfo]['serialize_name']))
        if AddrInfo in SeenInfo:
            continue
        SeenInfo.add(AddrInfo)
        Lines.append('0x' + AddrInfo)
    (KGhInfo / 'SpecSldmodu.txt').write_text('\n'.join(Lines) + '\n')
    (KOutInfo / 'SpecSldmoduClasses.json').write_text(JsonData.dumps([{'class': ItemCountInfo, 'addr': FirstValue, 'name': FileData} for ItemCountInfo, FirstValue, FileData in GetRows], indent=1))
    print('classes requested', len(GetRows), 'distinct functions', len(Lines))
    MissingInfo = [ItemCountInfo for ItemCountInfo in KPriority if ItemCountInfo not in SmapInfo]
    print('priority classes with no vtable entry:', MissingInfo)
if __name__ == '__main__':
    MainRunInfo()
