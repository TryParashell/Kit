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
from typing import Any

import black

from ProgramModel import KHeaderText, MethodData, ProgramData


# every emitted module must use the same formatter as handwritten project code
def FormatSource(SourceText: str) -> str:
    return black.format_str(SourceText, mode=black.Mode())


# canonical literals preserve floating point bits and reject hidden byte payloads
def RenderValue(FieldValue: Any) -> str:
    if isinstance(FieldValue, float):
        return f"float.fromhex({FieldValue.hex()!r})"
    if isinstance(FieldValue, tuple):
        ItemTexts = tuple(RenderValue(ItemValue) for ItemValue in FieldValue)
        SuffixText = "," if len(ItemTexts) == 1 else ""
        return "(" + ", ".join(ItemTexts) + SuffixText + ")"
    if isinstance(FieldValue, list):
        return "[" + ", ".join(RenderValue(ItemValue) for ItemValue in FieldValue) + "]"
    if isinstance(FieldValue, dict):
        PairTexts = (
            f"{RenderValue(KeyValue)}: {RenderValue(ItemValue)}"
            for KeyValue, ItemValue in FieldValue.items()
        )
        return "{" + ", ".join(PairTexts) + "}"
    if isinstance(FieldValue, (bytes, bytearray, memoryview)):
        raise ValueError("generated programs cannot contain vendor byte payloads")
    if FieldValue is None or isinstance(FieldValue, (bool, int, str)):
        return repr(FieldValue)
    raise ValueError(f"unsupported generated value {type(FieldValue).__name__}")


# deterministic letter aliases keep explicit registry imports unique without numeric suffixes
def MakeAlias(ItemIndex: int) -> str:
    LetterText = ""
    WorkIndex = ItemIndex + 1
    while WorkIndex:
        WorkIndex, Remainder = divmod(WorkIndex - 1, 26)
        LetterText = chr(ord("A") + Remainder) + LetterText
    return "KMethod" + LetterText


# one owner module keeps every exact trace spelling declared only once
def RenderOwner(OwnerSites: tuple[tuple[object, str], ...]) -> str:
    SourceLines = [
        KHeaderText.rstrip(),
        "",
        "from __future__ import annotations",
        "",
        "",
        "# exact trace spellings stay centralized so variant tables never duplicate owners",
        "KOwnerSites = {",
    ]
    SourceLines.extend(
        f"    {RenderValue(OwnerKey)}: {OwnerText!r},"
        for OwnerKey, OwnerText in OwnerSites
    )
    SourceLines.extend(("}", ""))
    return FormatSource("\n".join(SourceLines))


# one focused module isolates a natural serializer within exactly one variant
def RenderMethod(OwnerModule: str, MethodData: MethodData) -> str:
    SourceLines = [
        KHeaderText.rstrip(),
        "",
        "from __future__ import annotations",
        "",
        f"from {OwnerModule} import KOwnerSites",
        "",
        "",
        "# isolated method data lets new reverse engineered serializers compose independently",
        "KMethodProgram = (",
        "    KOwnerSites,",
        "    {",
    ]
    for StreamName, Operations in MethodData.StreamOps:
        SourceLines.append(f"        {StreamName!r}: (")
        SourceLines.extend(
            "            "
            + RenderValue((StartPos, FieldWidth, OwnerKey, KindName, DefaultValue))
            + ","
            for StartPos, FieldWidth, OwnerKey, KindName, DefaultValue in Operations
        )
        SourceLines.append("        ),")
    SourceLines.extend(("    },", ")", ""))
    return FormatSource("\n".join(SourceLines))


# explicit registries make every serializer dependency reviewable without wildcard discovery
def RenderRegistry(ProgramData: ProgramData, ModulePaths: tuple[str, ...]) -> str:
    BuildName = (
        "BuildStreams" if ProgramData.OpsName == "StreamPrograms" else "BuildProgram"
    )
    SourceLines = [
        KHeaderText.rstrip(),
        "",
        "from __future__ import annotations",
        "",
        f"from convert.adapters.solidworks.programs.Common.ProgramComposer import {BuildName}",
    ]
    AliasNames: list[str] = []
    for ItemIndex, ModulePath in enumerate(ModulePaths):
        AliasName = MakeAlias(ItemIndex)
        AliasNames.append(AliasName)
        SourceLines.append(f"from {ModulePath} import KMethodProgram as {AliasName}")
    SourceLines.extend(
        (
            "",
            "",
            "# explicit ordering keeps generated imports deterministic while offsets govern composition",
            "KMethodPrograms = (",
        )
    )
    SourceLines.extend(f"    {AliasName}," for AliasName in AliasNames)
    SourceLines.extend(
        (
            ")",
            "",
            "",
            "# compatibility tables preserve every established public import after decomposition",
        )
    )
    if ProgramData.OpsName == "StreamPrograms":
        StreamNames = tuple(StreamName for StreamName, _ in ProgramData.Streams)
        SourceLines.append(
            f"{ProgramData.OwnerName}, {ProgramData.OpsName} = BuildStreams("
        )
        SourceLines.append("    KMethodPrograms,")
        SourceLines.append(f"    {RenderValue(StreamNames)},")
        SourceLines.append(")")
    else:
        StreamName = ProgramData.Streams[0][0]
        SourceLines.append(
            f"{ProgramData.OwnerName}, {ProgramData.OpsName} = BuildProgram("
        )
        SourceLines.append("    KMethodPrograms,")
        SourceLines.append(f"    {StreamName!r},")
        SourceLines.append(")")
    SourceLines.append("")
    return FormatSource("\n".join(SourceLines))


# facades retain handwritten encoding behavior while replacing only duplicated data tables
def RewriteFacade(ProgramData: ProgramData) -> str:
    SourceLines = ProgramData.SourceText.splitlines()
    TreeData = ast.parse(ProgramData.SourceText, filename=str(ProgramData.SourcePath))
    RemovedLines: set[int] = set()
    TargetNames = {ProgramData.OwnerName, ProgramData.OpsName}
    for NodeData in TreeData.body:
        if isinstance(NodeData, ast.Assign):
            NameTexts = {
                TargetNode.id
                for TargetNode in NodeData.targets
                if isinstance(TargetNode, ast.Name)
            }
        elif isinstance(NodeData, ast.AnnAssign) and isinstance(
            NodeData.target, ast.Name
        ):
            NameTexts = {NodeData.target.id}
        else:
            NameTexts = set()
        if not NameTexts.intersection(TargetNames):
            continue
        RemovedLines.update(range(NodeData.lineno, NodeData.end_lineno + 1))
        CommentIndex = NodeData.lineno - 2
        if CommentIndex >= 0 and SourceLines[CommentIndex].lstrip().startswith("#"):
            RemovedLines.add(CommentIndex + 1)
    ImportEnds = (
        NodeData.end_lineno
        for NodeData in TreeData.body
        if isinstance(NodeData, (ast.Import, ast.ImportFrom))
    )
    InsertAfter = max(ImportEnds)
    ImportLines = [
        "",
        "from .Registry import (",
        f"    {ProgramData.OwnerName},",
        f"    {ProgramData.OpsName},",
        ")",
    ]
    OutputLines: list[str] = []
    for LineNumber, SourceLine in enumerate(SourceLines, start=1):
        if LineNumber not in RemovedLines:
            OutputLines.append(SourceLine)
        if LineNumber == InsertAfter:
            OutputLines.extend(ImportLines)
    OutputLines.append("")
    return FormatSource("\n".join(OutputLines))


# stable source hashes make generated and handwritten compatibility drift immediately visible
def HashText(SourceText: str) -> str:
    return hashlib.sha256(SourceText.encode("utf-8")).hexdigest()


# logical hashes prove owner and operation equality independently from source formatting
def HashProgram(ProgramData: ProgramData) -> str:
    CanonicalData = (
        ProgramData.OwnerName,
        ProgramData.OpsName,
        ProgramData.Streams,
    )
    return HashText(RenderValue(CanonicalData))


# one compact manifest preserves permanent counts hashes imports and byte equivalence evidence
def RenderManifest(
    Programs: tuple[ProgramData, ...],
    FacadeTexts: dict[str, str],
    GlobalStats: tuple[int, int, int, int, int, int],
) -> str:
    SourceLines = [
        KHeaderText.rstrip(),
        "",
        "from __future__ import annotations",
        "",
        "",
        "# global counts catch missing variants streams owners methods or recovered operations",
        f"KGlobalStats = {RenderValue(GlobalStats)}",
        "",
        "",
        "# variant evidence preserves public surfaces logical tables and encoded byte identities",
        "KProgramStats = (",
    ]
    for ProgramItem in Programs:
        StatRecord = (
            ProgramItem.VariantPath,
            ProgramItem.OwnerName,
            ProgramItem.OpsName,
            tuple(StreamName for StreamName, _ in ProgramItem.Streams),
            sum(len(Operations) for _, Operations in ProgramItem.Streams),
            HashProgram(ProgramItem),
            ProgramItem.PublicNames,
            ProgramItem.ByteStats,
            HashText(FacadeTexts[ProgramItem.VariantPath]),
        )
        SourceLines.append(f"    {RenderValue(StatRecord)},")
    SourceLines.extend((")", ""))
    return FormatSource("\n".join(SourceLines))
