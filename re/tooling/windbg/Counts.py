# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations
from pathlib import Path as PathInfo
import json as JsonData
import struct as Struct
import sys as System

# needed to keep reverse engineering responsibilities isolated and maintainable
KHereInfo = PathInfo(__file__).resolve().parent

# needed to keep reverse engineering responsibilities isolated and maintainable
KScratch = KHereInfo.parents[2] / '.rescratch'

# needed to keep reverse engineering responsibilities isolated and maintainable
KGrammar = KHereInfo.parent / 'harness'
for CandInfo in (KHereInfo, KGrammar):
    if str(CandInfo) not in System.path:
        System.path.insert(0, str(CandInfo))
import Model as Modellib
import Streamlib as Streamlib

# needed to keep reverse engineering responsibilities isolated and maintainable
KOutInfo = KScratch / 'trace' / 'out'

# needed to keep reverse engineering responsibilities isolated and maintainable
KHistoryClass = 'moHistoryFeatItemData_c'


# needed to keep reverse engineering responsibilities isolated and maintainable
def ItemCount(ByteBlob: bytes, ModeInfo: str) -> int:
    Entries = len(Streamlib.CompFeatEntries(ByteBlob))
    if ModeInfo == 'items':
        return Entries
    if ModeInfo == 'features':
        return Entries // 2
    raise SystemExit(f'unknown mode {ModeInfo!r}')


# needed to keep reverse engineering responsibilities isolated and maintainable
def FirstItemNode(ModelInfo: Modellib.Model) -> int:
    for PosInfoInfo, NodeInfoInfo in enumerate(ModelInfo.nodes):
        if NodeInfoInfo.class_name == KHistoryClass:
            return PosInfoInfo
    raise KeyError(KHistoryClass)


# needed to keep reverse engineering responsibilities isolated and maintainable
def Candidates(ModelInfo: Modellib.Model, CountInfo: int, Keying: str) -> set[tuple[object, ...]]:
    Anchor = FirstItemNode(ModelInfo)
    Total = len(ModelInfo.nodes)
    Found: set[tuple[object, ...]] = set()
    for PosInfoInfo, NodeInfoInfo in enumerate(ModelInfo.nodes):
        if Keying == 'anchor':
            KeyName: object = PosInfoInfo - Anchor
        elif Keying == 'tail':
            KeyName = PosInfoInfo - Total
        elif Keying == 'class':
            KeyName = (NodeInfoInfo.class_name, NodeInfoInfo.kind)
        else:
            raise SystemExit(f'unknown keying {Keying!r}')
        BodyInfo = NodeInfoInfo.body
        for Offset in range(len(BodyInfo) - 1):
            if Struct.unpack_from('<H', BodyInfo, Offset)[0] == CountInfo:
                Found.add((KeyName, Offset, 2))
            if Offset + 4 <= len(BodyInfo):
                if Struct.unpack_from('<I', BodyInfo, Offset)[0] == CountInfo:
                    Found.add((KeyName, Offset, 4))
    return Found


# needed to keep reverse engineering responsibilities isolated and maintainable
def MainRun() -> int:
    ModeInfo = System.argv[1]
    ArgsInfo = System.argv[2:]
    if not ArgsInfo or len(ArgsInfo) % 3:
        raise SystemExit('usage: Counts.py <items|features> <label> <part> <log> [...]')
    Loaded: list[tuple[str, PathInfo, bytes, Modellib.Model, int]] = []
    for PosInfoInfo in range(0, len(ArgsInfo), 3):
        LabelInfo = ArgsInfo[PosInfoInfo]
        PartInfoInfo = PathInfo(ArgsInfo[PosInfoInfo + 1]).resolve()
        LogInfo = PathInfo(ArgsInfo[PosInfoInfo + 2]).resolve()
        ByteBlob, ModelInfo, SpareValue = Modellib.LoadData(PartInfoInfo, LogInfo)
        CountInfo = ItemCount(ByteBlob, ModeInfo)
        Loaded.append((LabelInfo, PartInfoInfo, ByteBlob, ModelInfo, CountInfo))
        print(f'{LabelInfo:12s} target={CountInfo:3d} nodes={len(ModelInfo.nodes)} anchor_node={FirstItemNode(ModelInfo)}')
    Report: dict[str, list[list[object]]] = {}
    for Keying in ('anchor', 'tail', 'class'):
        SetsInfo = [Candidates(ModelInfo, CountInfo, Keying) for SpareValue, SpareValue, SpareValue, ModelInfo, CountInfo in Loaded]
        Shared = set.intersection(*SetsInfo)
        Report[Keying] = sorted([list(ItemData) for ItemData in Shared], key=repr)
        print(f'keying={Keying:7s} shared fields={len(Shared)}')
        for Entry in sorted(Shared, key=repr):
            print(f'  key={Entry[0]!r} body_offset={Entry[1]} width={Entry[2]}')
    KOutInfo.mkdir(parents=True, exist_ok=True)
    (KOutInfo / f'counts_{ModeInfo}.json').write_text(JsonData.dumps({'mode': ModeInfo, 'parts': [{'label': LabelInfo, 'part': str(PartInfoInfo), 'target': CountInfo} for LabelInfo, PartInfoInfo, SpareValue, SpareValue, CountInfo in Loaded], 'shared': Report}, indent=2), encoding='utf-8')
    return 0
if __name__ == '__main__':
    raise SystemExit(MainRun())
