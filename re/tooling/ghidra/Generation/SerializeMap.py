# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import json as JsonData
import pathlib as Pathlib
import sys as System

# needed to keep reverse engineering responsibilities isolated and maintainable
KRootInfo = Pathlib.Path(__file__).resolve().parents[4]

# needed to keep reverse engineering responsibilities isolated and maintainable
KDumps = KRootInfo / '.rescratch/ghidra/out'

# needed to keep reverse engineering responsibilities isolated and maintainable
KOutInfo = KRootInfo / 're/data'

# needed to keep reverse engineering responsibilities isolated and maintainable
KVtInfo = KDumps / 'sldmodu_vtslots.txt'

# needed to keep reverse engineering responsibilities isolated and maintainable
KSlotInfo = 5


# needed to keep reverse engineering responsibilities isolated and maintainable
def Tables(PathInfoData):
    CurInfo = None
    GetRows = []
    for LineText in PathInfoData.read_text(errors='replace').splitlines():
        if LineText.startswith('=== VFTABLE '):
            if CurInfo is not None:
                yield (CurInfo, GetRows)
            BodyInfo = LineText[len('=== VFTABLE '):]
            NameTextInfo, SpareValue, AddrInfo = BodyInfo.rpartition(' @ ')
            CurInfo = (NameTextInfo.strip(), AddrInfo.strip())
            GetRows = []
        elif LineText.startswith('VT '):
            if CurInfo is not None:
                yield (CurInfo, GetRows)
            BodyInfo = LineText[3:]
            HeadInfo, SpareValue, RestInfo = BodyInfo.partition(' @ ')
            AddrInfo = RestInfo.split(' ')[0]
            CurInfo = (HeadInfo.strip(), AddrInfo.strip())
            GetRows = []
        elif CurInfo is not None and LineText.startswith('  '):
            Parts = LineText.replace('|', ' ').split()
            if len(Parts) >= 3 and Parts[0].isdigit():
                GetRows.append((int(Parts[0]), Parts[1], Parts[2]))
    if CurInfo is not None:
        yield (CurInfo, GetRows)


# needed to keep reverse engineering responsibilities isolated and maintainable
def Build(PathInfoData=KVtInfo, SlotIndex=KSlotInfo):
    BestInfo = {}
    for (NameTextInfo, AddrInfo), GetRows in Tables(PathInfoData):
        if not GetRows:
            continue
        if GetRows[0][2].split('::')[-1] != 'GetRuntimeClass':
            continue
        HitInfo = [ResultData for ResultData in GetRows if ResultData[0] == SlotIndex]
        if not HitInfo:
            continue
        Target, FnInfo = (HitInfo[0][1], HitInfo[0][2])
        PrevInfo = BestInfo.get(NameTextInfo)
        if PrevInfo is None or len(GetRows) > PrevInfo[2]:
            BestInfo[NameTextInfo] = (Target, FnInfo, len(GetRows))
    return BestInfo


# needed to keep reverse engineering responsibilities isolated and maintainable
def MainRun():
    PathInfoData = KVtInfo
    if len(System.argv) > 1:
        PathInfoData = Pathlib.Path(System.argv[1])
    BestInfo = Build(PathInfoData)
    KOutInfo.mkdir(parents=True, exist_ok=True)
    DocInfo = {NameTextInfo: {'serialize_addr': ValueData[0], 'serialize_name': ValueData[1], 'vtable_slots': ValueData[2]} for NameTextInfo, ValueData in sorted(BestInfo.items())}
    (KOutInfo / 'SerializeMap.json').write_text(JsonData.dumps(DocInfo, indent=1))
    print('classes', len(DocInfo))
    Shared = {}
    for NameTextInfo, ValueData in DocInfo.items():
        Shared.setdefault(ValueData['serialize_addr'], []).append(NameTextInfo)
    print('distinct serialize functions', len(Shared))
    for KeyName in System.argv[2:]:
        for NameTextInfo, ValueData in DocInfo.items():
            if KeyName.lower() in NameTextInfo.lower():
                print(f"{NameTextInfo:34s} {ValueData['serialize_addr']} {ValueData['serialize_name']} shared_with={len(Shared[ValueData['serialize_addr']])}")
if __name__ == '__main__':
    MainRun()
