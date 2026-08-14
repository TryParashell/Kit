# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations
from dataclasses import dataclass as DataClass, field as FieldInfo
from pathlib import Path as PathInfo
import struct as Struct
import sys as System

# needed to keep reverse engineering responsibilities isolated and maintainable
KHereInfo = PathInfo(__file__).resolve().parent

# needed to keep reverse engineering responsibilities isolated and maintainable
KGrammar = KHereInfo.parent / 'harness'
for CandInfo in (KHereInfo, KGrammar):
    if str(CandInfo) not in System.path:
        System.path.insert(0, str(CandInfo))
import Segment as Segmentlib

# needed to keep reverse engineering responsibilities isolated and maintainable
KNewClassTag = 65535

# needed to keep reverse engineering responsibilities isolated and maintainable
KClassTagBit = 32768

# needed to keep reverse engineering responsibilities isolated and maintainable
KBigObjectTag = 32767

# needed to keep reverse engineering responsibilities isolated and maintainable
KNullTag = 0


# needed to keep reverse engineering responsibilities isolated and maintainable
class ModelError(RuntimeError):
    __slots__ = ()


# needed to keep reverse engineering responsibilities isolated and maintainable
@DataClass(slots=True)
class NodeInfo:
    KindNameInfo: str
    BodyInfo: bytes
    Schema: int = 0
    ClassNameData: str = ''
    Target: int = -1
    Literal: int = 0
    Origin: int = -1
    ClassIndex: int = 0
    ObjectIndex: int = 0
    KAliasNames = {'kind': 'KindNameInfo', 'body': 'BodyInfo', 'schema': 'Schema', 'class_name': 'ClassNameData', 'target': 'Target', 'literal': 'Literal', 'origin': 'Origin', 'class_index': 'ClassIndex', 'object_index': 'ObjectIndex'}


    # needed to keep reverse engineering responsibilities isolated and maintainable
    def __getattr__(SelfRef, NameText):
        AliasName = SelfRef.KAliasNames.get(NameText)
        if AliasName is None:
            raise AttributeError(NameText)
        return getattr(SelfRef, AliasName)


    # needed to keep reverse engineering responsibilities isolated and maintainable
    def __setattr__(SelfRef, NameText, ValueData):
        TargetName = SelfRef.KAliasNames.get(NameText, NameText)
        object.__setattr__(SelfRef, TargetName, ValueData)


# needed to keep reverse engineering responsibilities isolated and maintainable
@DataClass(slots=True)
class Model:
    Header: bytes
    BaseInfo: int
    Nodes: list[NodeInfo] = FieldInfo(default_factory=list)


    # needed to keep reverse engineering responsibilities isolated and maintainable
    def Clone(SelfRef) -> 'Model':
        return Model(Header=SelfRef.Header, BaseInfo=SelfRef.BaseInfo, Nodes=[NodeInfo(KindNameInfo=NodeInfoInfo.kind, BodyInfo=NodeInfoInfo.body, Schema=NodeInfoInfo.schema, ClassNameData=NodeInfoInfo.class_name, Target=NodeInfoInfo.target, Literal=NodeInfoInfo.literal, Origin=NodeInfoInfo.origin) for NodeInfoInfo in SelfRef.Nodes])


    # needed to keep reverse engineering responsibilities isolated and maintainable
    def DefnIndex(SelfRef, NameTextInfo: str) -> int:
        for PosInfoInfo, NodeInfoInfo in enumerate(SelfRef.Nodes):
            if NodeInfoInfo.kind == 'definition' and NodeInfoInfo.class_name == NameTextInfo:
                return PosInfoInfo
        raise KeyError(NameTextInfo)


    # needed to keep reverse engineering responsibilities isolated and maintainable
    def Assign(SelfRef) -> None:
        CounterInfo = SelfRef.BaseInfo
        for NodeInfoInfo in SelfRef.Nodes:
            if NodeInfoInfo.kind == 'definition':
                setattr(NodeInfoInfo, 'class_index', CounterInfo)
                setattr(NodeInfoInfo, 'object_index', CounterInfo + 1)
                CounterInfo += 2
            elif NodeInfoInfo.kind == 'classref':
                setattr(NodeInfoInfo, 'class_index', 0)
                setattr(NodeInfoInfo, 'object_index', CounterInfo)
                CounterInfo += 1
            else:
                setattr(NodeInfoInfo, 'class_index', 0)
                setattr(NodeInfoInfo, 'object_index', 0)


    # needed to keep reverse engineering responsibilities isolated and maintainable
    def EmitData(SelfRef) -> bytes:
        SelfRef.Assign()
        OutputDataInfo = bytearray(SelfRef.Header)
        for NodeInfoInfo in SelfRef.Nodes:
            if NodeInfoInfo.kind == 'definition':
                Encoded = NodeInfoInfo.class_name.encode('ascii')
                OutputDataInfo += Struct.pack('<HHH', KNewClassTag, NodeInfoInfo.schema, len(Encoded))
                OutputDataInfo += Encoded
            elif NodeInfoInfo.kind == 'classref':
                if NodeInfoInfo.target < 0:
                    Token = NodeInfoInfo.literal
                else:
                    Token = KClassTagBit | SelfRef.Nodes[NodeInfoInfo.target].class_index
                if Token & ~KClassTagBit >= KBigObjectTag:
                    raise ModelError(f'class index {Token & ~KClassTagBit} needs wBigObjectTag')
                OutputDataInfo += Struct.pack('<H', Token)
            elif NodeInfoInfo.kind == 'objectref':
                Token = NodeInfoInfo.literal if NodeInfoInfo.target < 0 else SelfRef.Nodes[NodeInfoInfo.target].object_index
                if Token >= KBigObjectTag:
                    raise ModelError(f'object index {Token} needs wBigObjectTag')
                OutputDataInfo += Struct.pack('<H', Token)
            elif NodeInfoInfo.kind == 'null':
                OutputDataInfo += Struct.pack('<H', KNullTag)
            else:
                raise ModelError(f'cannot emit node kind {NodeInfoInfo.kind}')
            OutputDataInfo += NodeInfoInfo.body
        return bytes(OutputDataInfo)
    KAliasNames = {'header': 'Header', 'base': 'BaseInfo', 'nodes': 'Nodes', 'clone': 'Clone', 'definition_index': 'DefnIndex', 'assign': 'Assign', 'emit': 'EmitData'}


    # needed to keep reverse engineering responsibilities isolated and maintainable
    def __getattr__(SelfRef, NameText):
        AliasName = SelfRef.KAliasNames.get(NameText)
        if AliasName is None:
            raise AttributeError(NameText)
        return getattr(SelfRef, AliasName)


    # needed to keep reverse engineering responsibilities isolated and maintainable
    def __setattr__(SelfRef, NameText, ValueData):
        TargetName = SelfRef.KAliasNames.get(NameText, NameText)
        object.__setattr__(SelfRef, TargetName, ValueData)


# needed to keep reverse engineering responsibilities isolated and maintainable
def Parse(ByteBlob: bytes, SegmentsInfo: tuple[Segmentlib.Segment, ...]) -> Model:
    if not SegmentsInfo:
        raise ModelError('empty segmentation')
    BaseInfo = SegmentsInfo[0].map_index
    ModelInfo = Model(Header=ByteBlob[:SegmentsInfo[0].offset], BaseInfo=BaseInfo)
    ClassPos: dict[int, int] = {}
    ObjectPos: dict[int, int] = {}
    for PosInfoInfo, ItemData in enumerate(SegmentsInfo):
        BodyInfo = ByteBlob[ItemData.offset + ItemData.header:ItemData.end]
        if ItemData.kind == 'definition':
            Schema = Struct.unpack_from('<H', ByteBlob, ItemData.offset + 2)[0]
            NodeInfoInfo = NodeInfo(KindNameInfo='definition', BodyInfo=BodyInfo, Schema=Schema, ClassNameData=ItemData.class_name, Origin=ItemData.offset)
            ClassPos[ItemData.class_index] = PosInfoInfo
            ObjectPos[ItemData.object_index] = PosInfoInfo
        elif ItemData.kind == 'classref':
            NodeInfoInfo = NodeInfo(KindNameInfo='classref', BodyInfo=BodyInfo, Literal=ItemData.tag, Target=ClassPos.get(ItemData.class_index, -1), ClassNameData=ItemData.class_name, Origin=ItemData.offset)
            ObjectPos[ItemData.object_index] = PosInfoInfo
        elif ItemData.kind == 'objectref':
            NodeInfoInfo = NodeInfo(KindNameInfo='objectref', BodyInfo=BodyInfo, Literal=ItemData.tag, Target=ObjectPos.get(ItemData.tag, -1), Origin=ItemData.offset)
        elif ItemData.kind == 'null':
            NodeInfoInfo = NodeInfo(KindNameInfo='null', BodyInfo=BodyInfo, Origin=ItemData.offset)
        else:
            raise ModelError(f'unsupported tag kind {ItemData.kind} at {ItemData.offset}')
        ModelInfo.nodes.append(NodeInfoInfo)
    for PosInfoInfo, ItemData in enumerate(SegmentsInfo):
        NodeInfoInfo = ModelInfo.nodes[PosInfoInfo]
        if NodeInfoInfo.kind == 'objectref' and NodeInfoInfo.target < 0 and (ItemData.tag >= BaseInfo):
            raise ModelError(f'object reference {ItemData.tag} at {ItemData.offset} is unresolved')
        if NodeInfoInfo.kind == 'classref' and NodeInfoInfo.target < 0 and (ItemData.class_index >= BaseInfo):
            raise ModelError(f'class reference {ItemData.class_index} at {ItemData.offset} is unresolved')
    ModelInfo.assign()
    return ModelInfo


# needed to keep reverse engineering responsibilities isolated and maintainable
def LoadData(PartInfoInfo: PathInfo, LogInfo: PathInfo, *, Stream: str | None=None) -> tuple[bytes, Model, tuple[Segmentlib.Segment, ...]]:
    if Stream is None:
        ByteBlob, SegmentsInfo = Segmentlib.LoadData(PartInfoInfo, LogInfo)
    else:
        ByteBlob, SegmentsInfo = Segmentlib.LoadData(PartInfoInfo, LogInfo, Stream=Stream)
    return (ByteBlob, Parse(ByteBlob, SegmentsInfo), SegmentsInfo)


# needed to keep reverse engineering responsibilities isolated and maintainable
def TokenTable(ModelInfo: Model) -> list[dict[str, int | str]]:
    ModelInfo.assign()
    Offsets = NodeOffsets(ModelInfo)
    GetRows: list[dict[str, int | str]] = []
    for PosInfoInfo, NodeInfoInfo in enumerate(ModelInfo.nodes):
        GetRows.append({'node': PosInfoInfo, 'offset': Offsets[PosInfoInfo], 'kind': NodeInfoInfo.kind, 'class_name': NodeInfoInfo.class_name, 'map_index': NodeInfoInfo.object_index, 'class_index': NodeInfoInfo.class_index, 'target': NodeInfoInfo.target, 'literal': NodeInfoInfo.literal})
    return GetRows


# needed to keep reverse engineering responsibilities isolated and maintainable
def NodeOffsets(ModelInfo: Model) -> list[int]:
    Offsets: list[int] = []
    Cursor = len(ModelInfo.header)
    for NodeInfoInfo in ModelInfo.nodes:
        Offsets.append(Cursor)
        if NodeInfoInfo.kind == 'definition':
            Cursor += 6 + len(NodeInfoInfo.class_name.encode('ascii'))
        else:
            Cursor += 2
        Cursor += len(NodeInfoInfo.body)
    Offsets.append(Cursor)
    return Offsets


# needed to keep reverse engineering responsibilities isolated and maintainable
def MainRunInfo() -> int:
    ArgsInfo = System.argv[1:]
    if len(ArgsInfo) % 3:
        raise SystemExit('usage: Model.py <label> <part> <log> [...]')
    for PosInfoInfo in range(0, len(ArgsInfo), 3):
        LabelInfo = ArgsInfo[PosInfoInfo]
        PartInfoInfo = PathInfo(ArgsInfo[PosInfoInfo + 1]).resolve()
        LogInfo = PathInfo(ArgsInfo[PosInfoInfo + 2]).resolve()
        ByteBlob, ModelInfo, SpareValue = LoadData(PartInfoInfo, LogInfo)
        Rebuilt = ModelInfo.emit()
        ExternClasses = sum((1 for NodeInfoInfo in ModelInfo.nodes if NodeInfoInfo.kind == 'classref' and NodeInfoInfo.target < 0))
        ExternObjects = sum((1 for NodeInfoInfo in ModelInfo.nodes if NodeInfoInfo.kind == 'objectref' and NodeInfoInfo.target < 0))
        Status = 'IDENTICAL' if Rebuilt == ByteBlob else 'DIFFERS'
        print(f'{LabelInfo:14s} nodes={len(ModelInfo.nodes):4d} base={ModelInfo.base} external classrefs={ExternClasses:3d} objectrefs={ExternObjects:3d} round-trip={Status} {len(Rebuilt)}/{len(ByteBlob)}')
    return 0
if __name__ == '__main__':
    raise SystemExit(MainRunInfo())
