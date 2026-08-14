# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations
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
import Blocks as Blockslib
import Model as Modellib

# needed to keep reverse engineering responsibilities isolated and maintainable
KOutInfo = KScratch / 'trace' / 'out'


# needed to keep reverse engineering responsibilities isolated and maintainable
def KeyName(NodeInfoInfo: Modellib.NodeInfo) -> tuple[str, str]:
    if NodeInfoInfo.kind == 'definition':
        return ('class', NodeInfoInfo.class_name)
    if NodeInfoInfo.kind == 'classref':
        return ('instance', NodeInfoInfo.class_name)
    return (NodeInfoInfo.kind, '')


# needed to keep reverse engineering responsibilities isolated and maintainable
def Align(Models: list[tuple[str, Modellib.Model]]) -> list[list[int | None]]:
    RefInfo = Models[-1][1]
    GetRows: list[list[int | None]] = [[None] * len(Models) for SpareValue in RefInfo.nodes]
    for Column, (Label, ModelInfo) in enumerate(Models):
        Matcher = Difflib.SequenceMatcher(a=[KeyName(NodeInfoInfo) for NodeInfoInfo in ModelInfo.nodes], b=[KeyName(NodeInfoInfo) for NodeInfoInfo in RefInfo.nodes], autojunk=False)
        for AlowInfo, BlowInfo, ByteSize in Matcher.get_matching_blocks():
            for StepInfo in range(ByteSize):
                GetRows[BlowInfo + StepInfo][Column] = AlowInfo + StepInfo
    return GetRows


# needed to keep reverse engineering responsibilities isolated and maintainable
def FinishMain(GetRows, LabelInfo, Models, PosInfoInfo, Stream) -> int:
    RefInfo = Models[-1][1]
    Labels = [LabelInfo for LabelInfo, SpareValue in Models]
    print(f'stream {Stream}')
    print('ref  kind        class                          ' + '  '.join(Labels))
    PayloadInfo: list[dict[str, object]] = []
    for PosInfoInfo, RowDataInfo in enumerate(GetRows):
        NodeInfoInfo = RefInfo.nodes[PosInfoInfo]
        Sizes: list[str] = []
        Lengths: list[int | None] = []
        for Column, (Label, ModelInfo) in enumerate(Models):
            Source = RowDataInfo[Column]
            if Source is None:
                Sizes.append('   -')
                Lengths.append(None)
            else:
                Sizes.append(f'{len(ModelInfo.nodes[Source].body):4d}')
                Lengths.append(len(ModelInfo.nodes[Source].body))
        FlagInfo = ''
        Present = [ValueInfo for ValueInfo in Lengths if ValueInfo is not None]
        if len(Present) != len(Models):
            FlagInfo = ' NEW'
        elif len(set(Present)) > 1:
            FlagInfo = ' GROWS'
        print(f"{PosInfoInfo:3d}  {NodeInfoInfo.kind:11s} {NodeInfoInfo.class_name or '-':30s} " + ' '.join(Sizes) + FlagInfo)
        PayloadInfo.append({'node': PosInfoInfo, 'kind': NodeInfoInfo.kind, 'class_name': NodeInfoInfo.class_name, 'sources': RowDataInfo, 'body_lengths': Lengths, 'state': FlagInfo.strip() or 'same'})
    KOutInfo.mkdir(parents=True, exist_ok=True)
    TagInfoInfo = Stream.replace('/', '_').replace('-', '_')
    (KOutInfo / f'nodediff_{TagInfoInfo}.json').write_text(JsonData.dumps({'stream': Stream, 'labels': Labels, 'rows': PayloadInfo}, indent=2), encoding='utf-8')
    return 0


# needed to keep reverse engineering responsibilities isolated and maintainable
def MainRun() -> int:
    ArgsInfo = System.argv[1:]
    Stream = ArgsInfo[0]
    Models: list[tuple[str, Modellib.Model]] = []
    for PosInfoInfo in range(1, len(ArgsInfo), 3):
        LabelInfo = ArgsInfo[PosInfoInfo]
        PartInfoInfo = PathInfo(ArgsInfo[PosInfoInfo + 1]).resolve()
        LogInfo = PathInfo(ArgsInfo[PosInfoInfo + 2]).resolve()
        Models.append((LabelInfo, Blockslib.LoadModel(PartInfoInfo, LogInfo, Stream)))
    GetRows = Align(Models)
    return FinishMain(GetRows, LabelInfo, Models, PosInfoInfo, Stream)
if __name__ == '__main__':
    raise SystemExit(MainRun())
