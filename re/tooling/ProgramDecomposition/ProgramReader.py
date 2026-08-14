# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations
import ast as AstLib
import hashlib as Hashlib
from pathlib import Path as PathInfo
import struct as Struct
from typing import Any as AnyInfo
from ProgramModel import KOperationNames, KOwnerNames, KSingleStreams, ProgramData

# needed to keep reverse engineering responsibilities isolated and maintainable
KPrimitiveFormats = {'char': 'b', 'uchar': 'B', 'short': 'h', 'ushort': 'H', 'int': 'i', 'long': 'i', 'ulong': 'I', 'float': 'f', 'double': 'd', 'int64': 'q', 'uint64': 'Q'}

# needed to keep reverse engineering responsibilities isolated and maintainable
KArchiveTags = {'Null': 0, 'NewClass': 65535, 'BigObject': 32767, 'ClassBit': 32768, 'BigClassBit': 2147483648, 'StringMarker': b'\xff\xfe\xff', 'ShortString': 255, 'LongString': 65534}


# needed to keep reverse engineering responsibilities isolated and maintainable
def ReadLiteral(NodeData: AstLib.AST) -> AnyInfo:
    if isinstance(NodeData, AstLib.Constant):
        return NodeData.value
    if isinstance(NodeData, AstLib.Tuple):
        return tuple((ReadLiteral(ItemNode) for ItemNode in NodeData.elts))
    if isinstance(NodeData, AstLib.List):
        return [ReadLiteral(ItemNode) for ItemNode in NodeData.elts]
    if isinstance(NodeData, AstLib.Dict):
        return {ReadLiteral(KeyNode): ReadLiteral(ValueNode) for KeyNode, ValueNode in zip(NodeData.keys, NodeData.values, strict=True)}
    if isinstance(NodeData, AstLib.UnaryOp) and isinstance(NodeData.op, (AstLib.UAdd, AstLib.USub)):
        OperandValue = ReadLiteral(NodeData.operand)
        return OperandValue if isinstance(NodeData.op, AstLib.UAdd) else -OperandValue
    if isinstance(NodeData, AstLib.Call) and isinstance(NodeData.func, AstLib.Attribute) and isinstance(NodeData.func.value, AstLib.Name) and (NodeData.func.value.id == 'float') and (NodeData.func.attr == 'fromhex') and (len(NodeData.args) == 1):
        return float.fromhex(ReadLiteral(NodeData.args[0]))
    raise ValueError(f'unsupported generated expression {AstLib.dump(NodeData)}')


# needed to keep reverse engineering responsibilities isolated and maintainable
def ReadAssigns(TreeData: AstLib.Module) -> dict[str, tuple[AstLib.AST, AnyInfo]]:
    AssignData: dict[str, tuple[AstLib.AST, AnyInfo]] = {}
    for NodeData in TreeData.body:
        if isinstance(NodeData, AstLib.Assign):
            TargetNodes = NodeData.targets
            ValueNode = NodeData.value
        elif isinstance(NodeData, AstLib.AnnAssign):
            TargetNodes = (NodeData.target,)
            ValueNode = NodeData.value
        else:
            continue
        if ValueNode is None:
            continue
        try:
            LiteralValue = ReadLiteral(ValueNode)
        except ValueError:
            continue
        for TargetNode in TargetNodes:
            if isinstance(TargetNode, AstLib.Name):
                AssignData[TargetNode.id] = (NodeData, LiteralValue)
    return AssignData


# needed to keep reverse engineering responsibilities isolated and maintainable
def ListPublic(TreeData: AstLib.Module) -> tuple[str, ...]:
    PublicNames: list[str] = []
    for NodeData in TreeData.body:
        if isinstance(NodeData, (AstLib.ClassDef, AstLib.FunctionDef, AstLib.AsyncFunctionDef)):
            CandidateNames = (NodeData.name,)
        elif isinstance(NodeData, AstLib.Assign):
            CandidateNames = tuple((TargetNode.id for TargetNode in NodeData.targets if isinstance(TargetNode, AstLib.Name)))
        elif isinstance(NodeData, AstLib.AnnAssign) and isinstance(NodeData.target, AstLib.Name):
            CandidateNames = (NodeData.target.id,)
        else:
            CandidateNames = ()
        for NameText in CandidateNames:
            if not NameText.startswith('_') and NameText not in PublicNames:
                PublicNames.append(NameText)
    return tuple(PublicNames)


# needed to keep reverse engineering responsibilities isolated and maintainable
def EncodeField(KindName: str, FieldValue: AnyInfo) -> bytes:
    if KindName == 'definition':
        ClassName, SchemaCode = FieldValue
        ClassData = ClassName.encode('ascii')
        return Struct.pack('<HHH', KArchiveTags['NewClass'], SchemaCode, len(ClassData)) + ClassData
    if KindName == 'classref':
        if FieldValue >= KArchiveTags['BigObject']:
            return Struct.pack('<HI', KArchiveTags['BigObject'], FieldValue | KArchiveTags['BigClassBit'])
        return Struct.pack('<H', KArchiveTags['ClassBit'] | FieldValue)
    if KindName == 'objectref':
        if FieldValue >= KArchiveTags['BigObject']:
            return Struct.pack('<HI', KArchiveTags['BigObject'], FieldValue)
        return Struct.pack('<H', FieldValue)
    if KindName == 'null':
        return Struct.pack('<H', KArchiveTags['Null'])
    if KindName in {'string', 'stringlist'}:
        StringItems = (FieldValue,) if KindName == 'string' else FieldValue
        OutputData = bytearray()
        if KindName == 'stringlist':
            OutputData.extend(Struct.pack('<H', len(StringItems)))
        for StringText in StringItems:
            StringData = StringText.encode('utf-16-le')
            UnitCount = len(StringData) // 2
            OutputData.extend(KArchiveTags['StringMarker'])
            if UnitCount < KArchiveTags['ShortString']:
                OutputData.extend(bytes((UnitCount,)))
            elif UnitCount < KArchiveTags['LongString']:
                OutputData.extend(b'\xff' + Struct.pack('<H', UnitCount))
            else:
                OutputData.extend(b'\xff\xff\xff' + Struct.pack('<I', UnitCount))
            OutputData.extend(StringData)
        return bytes(OutputData)
    if KindName.startswith('primitive:'):
        TypeName = KindName.split(':', 1)[1]
        return Struct.pack('<' + KPrimitiveFormats[TypeName], FieldValue)
    if KindName.startswith('direct:'):
        FormatText = KindName.split(':', 1)[1]
        ValueItems = FieldValue if isinstance(FieldValue, tuple) else (FieldValue,)
        return Struct.pack('<' + FormatText, *ValueItems)
    raise ValueError(f'unknown generated operation {KindName!r}')


# needed to keep reverse engineering responsibilities isolated and maintainable
def GetByteStats(Streams: tuple[tuple[str, tuple[AnyInfo, ...]], ...]) -> tuple[tuple[str, int, str], ...]:
    ByteStats: list[tuple[str, int, str]] = []
    for StreamName, Operations in Streams:
        OutputData = bytearray()
        SourceCursor = 0
        for StartPos, FieldWidth, OwnerText, KindName, DefaultValue in Operations:
            if StartPos != SourceCursor:
                raise ValueError(f'program field order drifted at {StartPos}')
            FieldData = EncodeField(KindName, DefaultValue)
            if KindName not in {'string', 'stringlist'} and len(FieldData) != FieldWidth:
                raise ValueError(f'program field width drifted at {StartPos} for {OwnerText!r}')
            OutputData.extend(FieldData)
            SourceCursor += FieldWidth
        ByteStats.append((StreamName, len(OutputData), Hashlib.sha256(OutputData).hexdigest()))
    return tuple(ByteStats)


# needed to keep reverse engineering responsibilities isolated and maintainable
def ReadProgram(SourcePath: PathInfo, SourceRoot: PathInfo) -> ProgramData:
    SourceText = SourcePath.read_text(encoding='utf-8')
    TreeData = AstLib.parse(SourceText, filename=str(SourcePath))
    AssignData = ReadAssigns(TreeData)
    OwnerName = next((NameText for NameText in KOwnerNames if NameText in AssignData), None)
    OpsName = next((NameText for NameText in KOperationNames if NameText in AssignData), None)
    if OwnerName is None or OpsName is None:
        raise ValueError(f'program tables are missing from {SourcePath}')
    OwnerNames = AssignData[OwnerName][1]
    OperationData = AssignData[OpsName][1]
    if OpsName == 'StreamPrograms':
        RawStreams = tuple(OperationData.items())
    else:
        RawStreams = ((KSingleStreams[OpsName], OperationData),)
    OwnedStreams: list[tuple[str, tuple[AnyInfo, ...]]] = []
    for StreamName, Operations in RawStreams:
        OwnedOps: list[tuple[int, int, str, str, AnyInfo]] = []
        for Operation in Operations:
            if not isinstance(Operation, tuple) or len(Operation) != 5:
                raise ValueError(f'invalid operation in {SourcePath}')
            StartPos, FieldWidth, OwnerIndex, KindName, DefaultValue = Operation
            if not isinstance(OwnerIndex, int) or not 0 <= OwnerIndex < len(OwnerNames):
                raise ValueError(f'invalid owner index in {SourcePath}')
            OwnedOps.append((StartPos, FieldWidth, OwnerNames[OwnerIndex], KindName, DefaultValue))
        OwnedStreams.append((StreamName, tuple(OwnedOps)))
    VariantPath = SourcePath.parent.relative_to(SourceRoot).as_posix()
    StreamData = tuple(OwnedStreams)
    return ProgramData(VariantPath=VariantPath, SourcePath=SourcePath, SourceText=SourceText, OwnerName=OwnerName, OpsName=OpsName, Streams=StreamData, PublicNames=ListPublic(TreeData), ByteStats=GetByteStats(StreamData))


# needed to keep reverse engineering responsibilities isolated and maintainable
def LoadPrograms(SourceRoot: PathInfo) -> tuple[ProgramData, ...]:
    ProgramFiles = tuple(sorted(SourceRoot.rglob('Program.py')))
    if not ProgramFiles:
        raise ValueError(f'no program facades found below {SourceRoot}')
    return tuple((ReadProgram(SourcePath, SourceRoot) for SourcePath in ProgramFiles))
