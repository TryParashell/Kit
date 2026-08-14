# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

import ast
import hashlib
from pathlib import Path
import struct
from typing import Any

from ProgramModel import KOperationNames, KOwnerNames, KSingleStreams, ProgramData


# primitive layouts mirror the recovered archive readers without importing production packages
KPrimitiveFormats = {
    "char": "b",
    "uchar": "B",
    "short": "h",
    "ushort": "H",
    "int": "i",
    "long": "i",
    "ulong": "I",
    "float": "f",
    "double": "d",
    "int64": "q",
    "uint64": "Q",
}


# archive tags are irreducible format vocabulary needed for independent byte evidence
KArchiveTags = {
    "Null": 0x0000,
    "NewClass": 0xFFFF,
    "BigObject": 0x7FFF,
    "ClassBit": 0x8000,
    "BigClassBit": 0x80000000,
    "StringMarker": b"\xff\xfe\xff",
    "ShortString": 0xFF,
    "LongString": 0xFFFE,
}


# generated tables allow only literals and exact hexadecimal floating point reconstruction
def ReadLiteral(NodeData: ast.AST) -> Any:
    if isinstance(NodeData, ast.Constant):
        return NodeData.value
    if isinstance(NodeData, ast.Tuple):
        return tuple(ReadLiteral(ItemNode) for ItemNode in NodeData.elts)
    if isinstance(NodeData, ast.List):
        return [ReadLiteral(ItemNode) for ItemNode in NodeData.elts]
    if isinstance(NodeData, ast.Dict):
        return {
            ReadLiteral(KeyNode): ReadLiteral(ValueNode)
            for KeyNode, ValueNode in zip(NodeData.keys, NodeData.values, strict=True)
        }
    if isinstance(NodeData, ast.UnaryOp) and isinstance(
        NodeData.op, (ast.UAdd, ast.USub)
    ):
        OperandValue = ReadLiteral(NodeData.operand)
        return OperandValue if isinstance(NodeData.op, ast.UAdd) else -OperandValue
    if (
        isinstance(NodeData, ast.Call)
        and isinstance(NodeData.func, ast.Attribute)
        and isinstance(NodeData.func.value, ast.Name)
        and NodeData.func.value.id == "float"
        and NodeData.func.attr == "fromhex"
        and len(NodeData.args) == 1
    ):
        return float.fromhex(ReadLiteral(NodeData.args[0]))
    raise ValueError(f"unsupported generated expression {ast.dump(NodeData)}")


# program declarations need one safe lookup without executing generated source
def ReadAssigns(TreeData: ast.Module) -> dict[str, tuple[ast.AST, Any]]:
    AssignData: dict[str, tuple[ast.AST, Any]] = {}
    for NodeData in TreeData.body:
        if isinstance(NodeData, ast.Assign):
            TargetNodes = NodeData.targets
            ValueNode = NodeData.value
        elif isinstance(NodeData, ast.AnnAssign):
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
            if isinstance(TargetNode, ast.Name):
                AssignData[TargetNode.id] = (NodeData, LiteralValue)
    return AssignData


# compatibility tests need the complete declared surface from every original facade
def ListPublic(TreeData: ast.Module) -> tuple[str, ...]:
    PublicNames: list[str] = []
    for NodeData in TreeData.body:
        if isinstance(NodeData, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            CandidateNames = (NodeData.name,)
        elif isinstance(NodeData, ast.Assign):
            CandidateNames = tuple(
                TargetNode.id
                for TargetNode in NodeData.targets
                if isinstance(TargetNode, ast.Name)
            )
        elif isinstance(NodeData, ast.AnnAssign) and isinstance(
            NodeData.target, ast.Name
        ):
            CandidateNames = (NodeData.target.id,)
        else:
            CandidateNames = ()
        for NameText in CandidateNames:
            if not NameText.startswith("_") and NameText not in PublicNames:
                PublicNames.append(NameText)
    return tuple(PublicNames)


# typed field encoding proves byte identity without importing a cad adapter package
def EncodeField(KindName: str, FieldValue: Any) -> bytes:
    if KindName == "definition":
        ClassName, SchemaCode = FieldValue
        ClassData = ClassName.encode("ascii")
        return (
            struct.pack("<HHH", KArchiveTags["NewClass"], SchemaCode, len(ClassData))
            + ClassData
        )
    if KindName == "classref":
        if FieldValue >= KArchiveTags["BigObject"]:
            return struct.pack(
                "<HI",
                KArchiveTags["BigObject"],
                FieldValue | KArchiveTags["BigClassBit"],
            )
        return struct.pack("<H", KArchiveTags["ClassBit"] | FieldValue)
    if KindName == "objectref":
        if FieldValue >= KArchiveTags["BigObject"]:
            return struct.pack("<HI", KArchiveTags["BigObject"], FieldValue)
        return struct.pack("<H", FieldValue)
    if KindName == "null":
        return struct.pack("<H", KArchiveTags["Null"])
    if KindName in {"string", "stringlist"}:
        StringItems = (FieldValue,) if KindName == "string" else FieldValue
        OutputData = bytearray()
        if KindName == "stringlist":
            OutputData.extend(struct.pack("<H", len(StringItems)))
        for StringText in StringItems:
            StringData = StringText.encode("utf-16-le")
            UnitCount = len(StringData) // 2
            OutputData.extend(KArchiveTags["StringMarker"])
            if UnitCount < KArchiveTags["ShortString"]:
                OutputData.extend(bytes((UnitCount,)))
            elif UnitCount < KArchiveTags["LongString"]:
                OutputData.extend(b"\xff" + struct.pack("<H", UnitCount))
            else:
                OutputData.extend(b"\xff\xff\xff" + struct.pack("<I", UnitCount))
            OutputData.extend(StringData)
        return bytes(OutputData)
    if KindName.startswith("primitive:"):
        TypeName = KindName.split(":", 1)[1]
        return struct.pack("<" + KPrimitiveFormats[TypeName], FieldValue)
    if KindName.startswith("direct:"):
        FormatText = KindName.split(":", 1)[1]
        ValueItems = FieldValue if isinstance(FieldValue, tuple) else (FieldValue,)
        return struct.pack("<" + FormatText, *ValueItems)
    raise ValueError(f"unknown generated operation {KindName!r}")


# byte digests preserve permanent proof after the monolithic migration oracle is removed
def GetByteStats(
    Streams: tuple[tuple[str, tuple[Any, ...]], ...],
) -> tuple[tuple[str, int, str], ...]:
    ByteStats: list[tuple[str, int, str]] = []
    for StreamName, Operations in Streams:
        OutputData = bytearray()
        SourceCursor = 0
        for StartPos, FieldWidth, OwnerText, KindName, DefaultValue in Operations:
            if StartPos != SourceCursor:
                raise ValueError(f"program field order drifted at {StartPos}")
            FieldData = EncodeField(KindName, DefaultValue)
            if (
                KindName not in {"string", "stringlist"}
                and len(FieldData) != FieldWidth
            ):
                raise ValueError(
                    f"program field width drifted at {StartPos} for {OwnerText!r}"
                )
            OutputData.extend(FieldData)
            SourceCursor += FieldWidth
        ByteStats.append(
            (
                StreamName,
                len(OutputData),
                hashlib.sha256(OutputData).hexdigest(),
            )
        )
    return tuple(ByteStats)


# one reader keeps owner resolution and stream naming identical for all legacy shapes
def ReadProgram(SourcePath: Path, SourceRoot: Path) -> ProgramData:
    SourceText = SourcePath.read_text(encoding="utf-8")
    TreeData = ast.parse(SourceText, filename=str(SourcePath))
    AssignData = ReadAssigns(TreeData)
    OwnerName = next(
        (NameText for NameText in KOwnerNames if NameText in AssignData), None
    )
    OpsName = next(
        (NameText for NameText in KOperationNames if NameText in AssignData), None
    )
    if OwnerName is None or OpsName is None:
        raise ValueError(f"program tables are missing from {SourcePath}")
    OwnerNames = AssignData[OwnerName][1]
    OperationData = AssignData[OpsName][1]
    if OpsName == "StreamPrograms":
        RawStreams = tuple(OperationData.items())
    else:
        RawStreams = ((KSingleStreams[OpsName], OperationData),)
    OwnedStreams: list[tuple[str, tuple[Any, ...]]] = []
    for StreamName, Operations in RawStreams:
        OwnedOps: list[tuple[int, int, str, str, Any]] = []
        for Operation in Operations:
            if not isinstance(Operation, tuple) or len(Operation) != 5:
                raise ValueError(f"invalid operation in {SourcePath}")
            StartPos, FieldWidth, OwnerIndex, KindName, DefaultValue = Operation
            if not isinstance(OwnerIndex, int) or not 0 <= OwnerIndex < len(OwnerNames):
                raise ValueError(f"invalid owner index in {SourcePath}")
            OwnedOps.append(
                (
                    StartPos,
                    FieldWidth,
                    OwnerNames[OwnerIndex],
                    KindName,
                    DefaultValue,
                )
            )
        OwnedStreams.append((StreamName, tuple(OwnedOps)))
    VariantPath = SourcePath.parent.relative_to(SourceRoot).as_posix()
    StreamData = tuple(OwnedStreams)
    return ProgramData(
        VariantPath=VariantPath,
        SourcePath=SourcePath,
        SourceText=SourceText,
        OwnerName=OwnerName,
        OpsName=OpsName,
        Streams=StreamData,
        PublicNames=ListPublic(TreeData),
        ByteStats=GetByteStats(StreamData),
    )


# full generation must see every variant before global owner catalogs are emitted
def LoadPrograms(SourceRoot: Path) -> tuple[ProgramData, ...]:
    ProgramFiles = tuple(sorted(SourceRoot.rglob("Program.py")))
    if not ProgramFiles:
        raise ValueError(f"no program facades found below {SourceRoot}")
    return tuple(ReadProgram(SourcePath, SourceRoot) for SourcePath in ProgramFiles)
