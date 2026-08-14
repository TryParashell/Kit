# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations
from dataclasses import dataclass as DataClass
import difflib as Difflib
import json as JsonData
from pathlib import Path as PathInfo
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
import Segment as Segmentlib

# needed to keep reverse engineering responsibilities isolated and maintainable
KOutInfo = KScratch / 'trace' / 'out'


# needed to keep reverse engineering responsibilities isolated and maintainable
class BlockError(RuntimeError):
    __slots__ = ()


# needed to keep reverse engineering responsibilities isolated and maintainable
@DataClass(frozen=True, slots=True)
class Insertion:
    LowValue: int
    HighValue: int


    # needed to keep reverse engineering responsibilities isolated and maintainable
    @property
    def ByteSize(SelfRef) -> int:
        return SelfRef.HighValue - SelfRef.LowValue
    KAliasNames = {'low': 'LowValue', 'high': 'HighValue', 'size': 'ByteSize'}


    # needed to keep reverse engineering responsibilities isolated and maintainable
    def __getattr__(SelfRef, NameText):
        AliasName = SelfRef.KAliasNames.get(NameText)
        if AliasName is None:
            raise AttributeError(NameText)
        return getattr(SelfRef, AliasName)


# needed to keep reverse engineering responsibilities isolated and maintainable
def SigInfoInfo(NodeInfoInfo: Modellib.NodeInfo) -> tuple[str, str, int]:
    if NodeInfoInfo.kind == 'definition':
        return ('class', NodeInfoInfo.class_name, len(NodeInfoInfo.body))
    if NodeInfoInfo.kind == 'classref':
        return ('instance', NodeInfoInfo.class_name, len(NodeInfoInfo.body))
    return (NodeInfoInfo.kind, '', len(NodeInfoInfo.body))


# needed to keep reverse engineering responsibilities isolated and maintainable
def Signatures(ModelInfo: Modellib.Model) -> list[tuple[str, str, int]]:
    return [SigInfoInfo(NodeInfoInfo) for NodeInfoInfo in ModelInfo.nodes]


# needed to keep reverse engineering responsibilities isolated and maintainable
def Insertions(Smaller: Modellib.Model, Larger: Modellib.Model) -> tuple[Insertion, ...]:
    LeftInfo = Signatures(Smaller)
    Right = Signatures(Larger)
    Matcher = Difflib.SequenceMatcher(a=LeftInfo, b=Right, autojunk=False)
    Result: list[Insertion] = []
    for TagInfoInfo, AlowInfo, Ahigh, BlowInfo, Bhigh in Matcher.get_opcodes():
        if TagInfoInfo == 'equal':
            continue
        if TagInfoInfo == 'insert':
            Result.append(Insertion(BlowInfo, Bhigh))
            continue
        if TagInfoInfo == 'replace' and Bhigh - BlowInfo > Ahigh - AlowInfo:
            Result.append(Insertion(BlowInfo + (Ahigh - AlowInfo), Bhigh))
            continue
        if TagInfoInfo != 'replace':
            raise BlockError(f'unexpected opcode {TagInfoInfo} at [{BlowInfo},{Bhigh})')
        Result.append(Insertion(BlowInfo, Bhigh))
    return tuple(Result)


# needed to keep reverse engineering responsibilities isolated and maintainable
def LoadModel(PartInfoInfo: PathInfo, LogInfo: PathInfo, Stream: str) -> Modellib.Model:
    ByteBlob, SegmentsInfo = Segmentlib.LoadData(PartInfoInfo, LogInfo, Stream=Stream)
    return Modellib.Parse(ByteBlob, SegmentsInfo)


# needed to keep reverse engineering responsibilities isolated and maintainable
def Describe(ModelInfo: Modellib.Model, BlockInfo: Insertion) -> list[str]:
    return [f"{PosInfoInfo}:{ModelInfo.nodes[PosInfoInfo].kind}:{ModelInfo.nodes[PosInfoInfo].class_name or '-'}:{len(ModelInfo.nodes[PosInfoInfo].body)}" for PosInfoInfo in range(BlockInfo.low, BlockInfo.high)]


# needed to keep reverse engineering responsibilities isolated and maintainable
def Compare(Stream: str, GetRows: list[tuple[str, PathInfo, PathInfo]]) -> dict[str, object]:
    Models = [(LabelInfo, LoadModel(PartInfoInfo, LogInfo, Stream)) for LabelInfo, PartInfoInfo, LogInfo in GetRows]
    PayloadInfo: dict[str, object] = {'stream': Stream, 'parts': [{'label': LabelInfo, 'nodes': len(ModelInfo.nodes), 'base': ModelInfo.base} for LabelInfo, ModelInfo in Models], 'steps': []}
    Steps: list[dict[str, object]] = []
    for (LeftLabel, LeftInfo), (RightLabel, Right) in zip(Models, Models[1:]):
        Found = Insertions(LeftInfo, Right)
        Steps.append({'from': LeftLabel, 'to': RightLabel, 'insertions': [{'low': BlockInfo.low, 'high': BlockInfo.high, 'size': BlockInfo.size, 'nodes': Describe(Right, BlockInfo)} for BlockInfo in Found], 'inserted_nodes': sum((BlockInfo.size for BlockInfo in Found))})
    PayloadInfo['steps'] = Steps
    return PayloadInfo


# needed to keep reverse engineering responsibilities isolated and maintainable
def MainRunInfo() -> int:
    ArgsInfo = System.argv[1:]
    if len(ArgsInfo) < 4 or (len(ArgsInfo) - 1) % 3:
        raise SystemExit('usage: Blocks.py <stream> <label> <part> <log> [...]')
    Stream = ArgsInfo[0]
    GetRows: list[tuple[str, PathInfo, PathInfo]] = []
    for PosInfoInfo in range(1, len(ArgsInfo), 3):
        GetRows.append((ArgsInfo[PosInfoInfo], PathInfo(ArgsInfo[PosInfoInfo + 1]).resolve(), PathInfo(ArgsInfo[PosInfoInfo + 2]).resolve()))
    PayloadInfo = Compare(Stream, GetRows)
    KOutInfo.mkdir(parents=True, exist_ok=True)
    TagInfoInfo = Stream.replace('/', '_').replace('-', '_')
    (KOutInfo / f'blocks_{TagInfoInfo}.json').write_text(JsonData.dumps(PayloadInfo, indent=2), encoding='utf-8')
    print(f'stream {Stream}')
    for RowDataInfo in PayloadInfo['parts']:
        print(f"  {RowDataInfo['label']:14s} nodes={RowDataInfo['nodes']:5d} base={RowDataInfo['base']}")
    for StepInfo in PayloadInfo['steps']:
        print(f"  {StepInfo['from']} -> {StepInfo['to']} inserted={StepInfo['inserted_nodes']} blocks={len(StepInfo['insertions'])}")
        for BlockInfo in StepInfo['insertions']:
            print(f"    [{BlockInfo['low']},{BlockInfo['high']}) size={BlockInfo['size']}")
            print('      ' + ' '.join(BlockInfo['nodes'][:24]))
    return 0
if __name__ == '__main__':
    raise SystemExit(MainRunInfo())
