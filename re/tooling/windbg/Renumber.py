# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations
from dataclasses import dataclass as DataClass
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
import Streamlib as Streamlib
from convert.adapters.solidworks import resolved as Resolvedlib


# needed to keep reverse engineering responsibilities isolated and maintainable
def GetLegacyAttr(SelfRef, NameText):
    AliasName = SelfRef.KAliasNames.get(NameText)
    if AliasName is None:
        raise AttributeError(NameText)
    return getattr(SelfRef, AliasName)


# needed to keep reverse engineering responsibilities isolated and maintainable
def SetLegacyMut(SelfRef, NameText, ValueData):
    TargetName = SelfRef.KAliasNames.get(NameText, NameText)
    object.__setattr__(SelfRef, TargetName, ValueData)

# needed to keep reverse engineering responsibilities isolated and maintainable
KOutInfo = KScratch / 'trace' / 'out'

# needed to keep reverse engineering responsibilities isolated and maintainable
KCompClass = 'moCompFeature_c'

# needed to keep reverse engineering responsibilities isolated and maintainable
KHistoryClass = 'moHistoryFeatItemData_c'


# needed to keep reverse engineering responsibilities isolated and maintainable
class RenumberError(RuntimeError):
    __slots__ = ()


# needed to keep reverse engineering responsibilities isolated and maintainable
@DataClass(frozen=True, slots=True)
class Block:
    StartRun: int
    StopInfo: int


    # needed to keep reverse engineering responsibilities isolated and maintainable
    @property
    def ByteSize(SelfRef) -> int:
        return SelfRef.StopInfo - SelfRef.StartRun


    # needed to keep reverse engineering responsibilities isolated and maintainable
    def __contains__(SelfRef, PosInfoInfo: int) -> bool:
        return SelfRef.StartRun <= PosInfoInfo < SelfRef.StopInfo
    KAliasNames = {'start': 'StartRun', 'stop': 'StopInfo', 'size': 'ByteSize'}

# needed to keep reverse engineering responsibilities isolated and maintainable
Block.__getattr__ = GetLegacyAttr


# needed to keep reverse engineering responsibilities isolated and maintainable
def HistoryNode(ModelInfo: Modellib.Model) -> int:
    for PosInfoInfo, NodeInfoInfo in enumerate(ModelInfo.nodes):
        if NodeInfoInfo.class_name == KHistoryClass:
            if PosInfoInfo == 0:
                raise RenumberError(f'{KHistoryClass} is the first object; the array count cannot precede it')
            return PosInfoInfo - 1
    raise RenumberError(f'{KHistoryClass} never appears in the stream')


# needed to keep reverse engineering responsibilities isolated and maintainable
def ReadCount(ModelInfo: Modellib.Model) -> int:
    NodeInfoInfo = ModelInfo.nodes[HistoryNode(ModelInfo)]
    if len(NodeInfoInfo.body) < 2:
        raise RenumberError('the object preceding the history array is too short')
    return int.from_bytes(NodeInfoInfo.body[-2:], 'little')


# needed to keep reverse engineering responsibilities isolated and maintainable
def SetHistoryCount(ModelInfo: Modellib.Model, ValueInfo: int) -> None:
    if not 0 < ValueInfo < 65536:
        raise RenumberError(f'history item count {ValueInfo} does not fit in a u16')
    PosInfoInfo = HistoryNode(ModelInfo)
    NodeInfoInfo = ModelInfo.nodes[PosInfoInfo]
    setattr(NodeInfoInfo, 'body', NodeInfoInfo.body[:-2] + ValueInfo.to_bytes(2, 'little'))


# needed to keep reverse engineering responsibilities isolated and maintainable
def NodeRange(ModelInfo: Modellib.Model, StartByte: int, StopByte: int) -> Block:
    Offsets = Modellib.NodeOffsets(ModelInfo)
    try:
        StartRun = Offsets.index(StartByte)
        StopInfo = Offsets.index(StopByte)
    except ValueError as Error:
        raise RenumberError(f'byte span [{StartByte}, {StopByte}) does not align with object boundaries') from Error
    return Block(StartRun, StopInfo)


# needed to keep reverse engineering responsibilities isolated and maintainable
def CompUnit(ModelInfo: Modellib.Model, ByteBlob: bytes) -> Block:
    Entries = Streamlib.CompFeatEntries(ByteBlob)
    if len(Entries) < 4 or len(Entries) % 2:
        raise RenumberError(f'{KCompClass} holds {len(Entries)} entries; an even count of at least four is required to duplicate one feature')
    return NodeRange(ModelInfo, Entries[-2][0], Entries[-1][1])


# needed to keep reverse engineering responsibilities isolated and maintainable
def FeatUnit(ByteBlob: bytes, SegmentsInfo: tuple[Segmentlib.Segment, ...]) -> Block:
    Sketches = [ItemData for ItemData in Resolvedlib.tree_nodes(ByteBlob) if ItemData.name.startswith('Sketch')]
    if len(Sketches) < 2:
        raise RenumberError(f'the donor exposes {len(Sketches)} sketch nodes; at least two are needed so the duplicated group is not the first feature')
    Anchor = Sketches[-1].text_end
    PosInfoInfo = -1
    for ItemData in SegmentsInfo:
        if ItemData.offset <= Anchor < ItemData.end:
            PosInfoInfo = ItemData.index
            break
    if PosInfoInfo < 0:
        raise RenumberError(f'sketch name record at {Anchor} is outside every object')
    while PosInfoInfo > 0 and SegmentsInfo[PosInfoInfo].depth != 0:
        PosInfoInfo -= 1
    if SegmentsInfo[PosInfoInfo].depth != 0:
        raise RenumberError('no top-level object precedes the last sketch')
    return Block(PosInfoInfo, len(SegmentsInfo))


# needed to keep reverse engineering responsibilities isolated and maintainable
def FinishCopyMut(BlockInfo, CopyId, Cursor, ModelInfo, OrderedInfo, PlanInfo, Source) -> tuple[Modellib.Model, tuple[tuple[int, int], ...]]:
    while Cursor < len(ModelInfo.nodes):
        PlanInfo.append((Cursor, 0))
        Cursor += 1
    Lookup = {KeyName: PosInfoInfo for PosInfoInfo, KeyName in enumerate(PlanInfo)}


    # needed to keep reverse engineering responsibilities isolated and maintainable
    def IsDuplicated(Source: int) -> bool:
        return any((Source in BlockInfo for BlockInfo in OrderedInfo))
    Result = Modellib.Model(Header=ModelInfo.header, BaseInfo=ModelInfo.base, Nodes=[])
    for Source, CopyId in PlanInfo:
        Original = ModelInfo.nodes[Source]
        KindNameInfo = Original.kind
        Target = Original.target
        Literal = Original.literal
        if CopyId and KindNameInfo == 'definition':
            KindNameInfo = 'classref'
            Target = Lookup[Source, 0]
            Literal = Modellib.KClassTagBit
        if Target >= 0:
            if CopyId and IsDuplicated(Target):
                Target = Lookup[Target, CopyId]
            else:
                Target = Lookup[Target, 0]
        Result.nodes.append(Modellib.NodeInfo(KindNameInfo=KindNameInfo, BodyInfo=Original.body, Schema=Original.schema, ClassNameData=Original.class_name, Target=Target, Literal=Literal, Origin=Original.origin))
    Result.assign()
    return (Result, tuple(PlanInfo))


# needed to keep reverse engineering responsibilities isolated and maintainable
def Duplicate(ModelInfo: Modellib.Model, Blocks: tuple[Block, ...], Copies: int) -> tuple[Modellib.Model, tuple[tuple[int, int], ...]]:
    if Copies < 1:
        raise RenumberError('copies must be at least 1')

    # needed to keep reverse engineering responsibilities isolated and maintainable
    OrderedInfo = sorted(Blocks, key=lambda ItemData: ItemData.start)
    for BlockInfo in OrderedInfo:
        if BlockInfo.start < 0 or BlockInfo.stop > len(ModelInfo.nodes) or BlockInfo.size <= 0:
            raise RenumberError(f'block {BlockInfo} is out of range')
    for LeftInfo, Right in zip(OrderedInfo, OrderedInfo[1:]):
        if LeftInfo.stop > Right.start:
            raise RenumberError('blocks overlap')
    PlanInfo: list[tuple[int, int]] = []
    Cursor = 0
    for BlockInfo in OrderedInfo:
        while Cursor < BlockInfo.stop:
            PlanInfo.append((Cursor, 0))
            Cursor += 1
        for CopyId in range(1, Copies + 1):
            for Source in range(BlockInfo.start, BlockInfo.stop):
                PlanInfo.append((Source, CopyId))
    return FinishCopyMut(BlockInfo, CopyId, Cursor, ModelInfo, OrderedInfo, PlanInfo, Source)


# needed to keep reverse engineering responsibilities isolated and maintainable
def Remove(ModelInfo: Modellib.Model, Blocks: tuple[Block, ...]) -> tuple[Modellib.Model, tuple[int, ...]]:

    # needed to keep reverse engineering responsibilities isolated and maintainable
    OrderedInfo = sorted(Blocks, key=lambda ItemData: ItemData.start)
    Dropped: set[int] = set()
    for BlockInfo in OrderedInfo:
        for PosInfoInfo in range(BlockInfo.start, BlockInfo.stop):
            Dropped.add(PosInfoInfo)
    for PosInfoInfo in sorted(Dropped):
        NodeInfoInfo = ModelInfo.nodes[PosInfoInfo]
        if NodeInfoInfo.kind == 'definition':
            raise RenumberError(f'node {PosInfoInfo} defines {NodeInfoInfo.class_name}; deleting a class definition needs the definition moved to its first surviving use')
    Survivors = [PosInfoInfo for PosInfoInfo in range(len(ModelInfo.nodes)) if PosInfoInfo not in Dropped]
    Lookup = {Source: IndexData for IndexData, Source in enumerate(Survivors)}
    Result = Modellib.Model(Header=ModelInfo.header, BaseInfo=ModelInfo.base, Nodes=[])
    for Source in Survivors:
        Original = ModelInfo.nodes[Source]
        Target = Original.target
        if Target >= 0:
            if Target not in Lookup:
                raise RenumberError(f'node {Source} references deleted node {Target}; the deletion set is not closed')
            Target = Lookup[Target]
        Result.nodes.append(Modellib.NodeInfo(KindNameInfo=Original.kind, BodyInfo=Original.body, Schema=Original.schema, ClassNameData=Original.class_name, Target=Target, Literal=Original.literal, Origin=Original.origin))
    Result.assign()
    return (Result, tuple(Survivors))


# needed to keep reverse engineering responsibilities isolated and maintainable
def Renumbering(Before: Modellib.Model, After: Modellib.Model, PlanInfo: tuple[tuple[int, int], ...]) -> list[dict[str, int | str]]:
    Before.assign()
    After.assign()
    GetRows: list[dict[str, int | str]] = []
    for PosInfoInfo, (Source, CopyId) in enumerate(PlanInfo):
        OldNode = Before.nodes[Source]
        NewNode = After.nodes[PosInfoInfo]
        GetRows.append({'source_node': Source, 'copy': CopyId, 'target_node': PosInfoInfo, 'kind': NewNode.kind, 'class_name': NewNode.class_name, 'old_class_index': OldNode.class_index, 'new_class_index': NewNode.class_index, 'old_map_index': OldNode.object_index, 'new_map_index': NewNode.object_index, 'shift': NewNode.object_index - OldNode.object_index})
    return GetRows


# needed to keep reverse engineering responsibilities isolated and maintainable
def GrowInfo(PartInfoInfo: PathInfo, LogInfo: PathInfo, Copies: int) -> tuple[bytes, bytes, Modellib.Model, dict[str, object]]:
    ByteBlob, BaseModel, SegmentsInfo = Modellib.LoadData(PartInfoInfo, LogInfo)
    CompInfo = CompUnit(BaseModel, ByteBlob)
    FeatInfo = FeatUnit(ByteBlob, SegmentsInfo)
    print(f'comp unit nodes=[{CompInfo.start},{CompInfo.stop}) size={CompInfo.size}')
    print(f'feature unit nodes=[{FeatInfo.start},{FeatInfo.stop}) size={FeatInfo.size}')
    Grown, PlanInfo = Duplicate(BaseModel, (CompInfo, FeatInfo), Copies)
    BeforeCount = ReadCount(BaseModel)
    EntriesBefore = len(Streamlib.CompFeatEntries(ByteBlob))
    if BeforeCount != EntriesBefore:
        raise RenumberError(f'history array count {BeforeCount} disagrees with the {EntriesBefore} moCompFeature_c entries in {PartInfoInfo.name}')
    SetHistoryCount(Grown, BeforeCount + 2 * Copies)
    PayloadInfo = Grown.emit()
    Table = Renumbering(BaseModel, Grown, PlanInfo)
    Facts = {'renumbering_table': Table, 'part': str(PartInfoInfo), 'copies': Copies, 'comp_block': [CompInfo.start, CompInfo.stop], 'feature_block': [FeatInfo.start, FeatInfo.stop], 'nodes_before': len(BaseModel.nodes), 'nodes_after': len(Grown.nodes), 'bytes_before': len(ByteBlob), 'bytes_after': len(PayloadInfo), 'map_indices_before': len(BaseModel.nodes) and BaseModel.nodes[-1].object_index, 'map_indices_after': Grown.nodes[-1].object_index, 'comp_entries_before': EntriesBefore, 'comp_entries_after': len(Streamlib.CompFeatEntries(PayloadInfo)), 'history_count_before': BeforeCount, 'history_count_after': ReadCount(Grown), 'layouts_before': len(Resolvedlib.locate_features(ByteBlob)), 'layouts_after': len(Resolvedlib.locate_features(PayloadInfo))}
    return (ByteBlob, PayloadInfo, Grown, Facts)


# needed to keep reverse engineering responsibilities isolated and maintainable
def MainRun() -> int:
    PartInfoInfo = PathInfo(System.argv[1]).resolve()
    LogInfo = PathInfo(System.argv[2]).resolve()
    Copies = int(System.argv[3]) if len(System.argv) > 3 else 1
    ByteBlob, PayloadInfo, Grown, Facts = GrowInfo(PartInfoInfo, LogInfo, Copies)
    KOutInfo.mkdir(parents=True, exist_ok=True)
    Table = Facts.pop('renumbering_table')
    (KOutInfo / f'grown_{PartInfoInfo.stem}_{Copies}.bin').write_bytes(PayloadInfo)
    (KOutInfo / f'renumbering_{PartInfoInfo.stem}_{Copies}.json').write_text(JsonData.dumps(Table, indent=2), encoding='utf-8')
    Shifts = sorted({int(RowDataInfo['shift']) for RowDataInfo in Table})
    Facts['distinct_map_index_shifts'] = Shifts
    (KOutInfo / f'grown_{PartInfoInfo.stem}_{Copies}.json').write_text(JsonData.dumps(Facts, indent=2), encoding='utf-8')
    Nodes = Resolvedlib.tree_nodes(PayloadInfo)
    Sketches = [ItemData.name for ItemData in Nodes if ItemData.name.startswith('Sketch')]
    FeatInfoInfo = [ItemData.name for ItemData in Nodes if Resolvedlib.feature_kind(ItemData.flags) is not None]
    print(JsonData.dumps(Facts, indent=2))
    print(f'sketch nodes={Sketches}')
    print(f'feature nodes={FeatInfoInfo}')
    print(f'comp ids={[Entry[2] for Entry in Streamlib.CompFeatEntries(PayloadInfo)]}')
    return 0
if __name__ == '__main__':
    raise SystemExit(MainRun())
