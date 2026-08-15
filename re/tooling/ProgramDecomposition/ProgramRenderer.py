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
from typing import Any as AnyInfo
import black as Black
from ProgramModel import KHeaderText, MethodData, ProgramData


# needed to keep reverse engineering responsibilities isolated and maintainable
def FormatSource(SourceText: str) -> str:
    return Black.format_str(SourceText, mode=Black.Mode())


# needed to keep reverse engineering responsibilities isolated and maintainable
def RenderValue(FieldValue: AnyInfo) -> str:
    if isinstance(FieldValue, float):
        return f"float.fromhex({FieldValue.hex()!r})"
    if isinstance(FieldValue, tuple):
        ItemTexts = tuple((RenderValue(ItemValue) for ItemValue in FieldValue))
        SuffixText = "," if len(ItemTexts) == 1 else ""
        return "(" + ", ".join(ItemTexts) + SuffixText + ")"
    if isinstance(FieldValue, list):
        return (
            "[" + ", ".join((RenderValue(ItemValue) for ItemValue in FieldValue)) + "]"
        )
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


# needed to keep reverse engineering responsibilities isolated and maintainable
def MakeAlias(ItemIndex: int) -> str:
    LetterText = ""
    WorkIndex = ItemIndex + 1
    while WorkIndex:
        WorkIndex, Remainder = divmod(WorkIndex - 1, 26)
        LetterText = chr(ord("A") + Remainder) + LetterText
    return "KMethod" + LetterText


# needed to keep reverse engineering responsibilities isolated and maintainable
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
        (
            f"    {RenderValue(OwnerKey)}: {OwnerText!r},"
            for OwnerKey, OwnerText in OwnerSites
        )
    )
    SourceLines.extend(("}", ""))
    return FormatSource("\n".join(SourceLines))


# needed to keep reverse engineering responsibilities isolated and maintainable
def RenderMethod(OwnerModule: str, MethodData: MethodData) -> str:
    SourceLines = [
        KHeaderText.rstrip(),
        "",
        "from __future__ import annotations",
        "",
        "from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram",
        f"from {OwnerModule} import KOwnerSites",
        "",
        "",
        "# isolated method data lets new reverse engineered serializers compose independently",
        "KMethodProgram: MethodProgram = (",
        "    KOwnerSites,",
        "    {",
    ]
    for StreamName, Operations in MethodData.StreamOps:
        SourceLines.append(f"        {StreamName!r}: (")
        SourceLines.extend(
            (
                "            "
                + RenderValue((StartPos, FieldWidth, OwnerKey, KindName, DefaultValue))
                + ","
                for StartPos, FieldWidth, OwnerKey, KindName, DefaultValue in Operations
            )
        )
        SourceLines.append("        ),")
    SourceLines.extend(("    },", ")", ""))
    return FormatSource("\n".join(SourceLines))


# canonical constant names keep generated registries compliant without changing legacy public symbols
def GetConstNames(ProgramData: ProgramData) -> tuple[str, str]:
    OwnerConst = (
        ProgramData.OwnerName
        if ProgramData.OwnerName.startswith("K")
        else "K" + ProgramData.OwnerName
    )
    OpsConst = (
        ProgramData.OpsName
        if ProgramData.OpsName.startswith("K")
        else "K" + ProgramData.OpsName
    )
    return OwnerConst, OpsConst


# explicit dynamic bindings preserve legacy imports while canonical source bindings retain compliant casing
def AddAliasesMut(
    SourceLines: list[str], ProgramData: ProgramData, OwnerConst: str, OpsConst: str
) -> None:
    AliasPairs = tuple(
        (OriginalName, ConstName)
        for OriginalName, ConstName in (
            (ProgramData.OwnerName, OwnerConst),
            (ProgramData.OpsName, OpsConst),
        )
        if OriginalName != ConstName
    )
    if not AliasPairs:
        return
    for OriginalName, ConstName in AliasPairs:
        SourceLines.extend(
            (
                "",
                "# compatibility binding preserves its established public import after decomposition",
                f"{OriginalName} = {ConstName}",
            )
        )


# needed to keep reverse engineering responsibilities isolated and maintainable
def RenderRegistry(ProgramData: ProgramData, ModulePaths: tuple[str, ...]) -> str:
    BuildName = (
        "BuildStreams" if ProgramData.OpsName == "StreamPrograms" else "BuildProgram"
    )
    OwnerConst, OpsConst = GetConstNames(ProgramData)
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
    SourceLines.extend((f"    {AliasName}," for AliasName in AliasNames))
    SourceLines.extend(
        (
            ")",
            "",
            "",
            "# composed tables stay immutable because generated registries expose stable format facts",
        )
    )
    if ProgramData.OpsName == "StreamPrograms":
        StreamNames = tuple(
            (StreamName for StreamName, SpareValue in ProgramData.Streams)
        )
        SourceLines.append(f"{OwnerConst}, {OpsConst} = BuildStreams(")
        SourceLines.append("    KMethodPrograms,")
        SourceLines.append(f"    {RenderValue(StreamNames)},")
        SourceLines.append(")")
    else:
        StreamName = ProgramData.Streams[0][0]
        SourceLines.append(f"{OwnerConst}, {OpsConst} = BuildProgram(")
        SourceLines.append("    KMethodPrograms,")
        SourceLines.append(f"    {StreamName!r},")
        SourceLines.append(")")
    SourceLines.extend(
        (
            "",
            "# generated registry exports remain explicit for facade composition and extension imports",
            f"__all__ = [{OwnerConst!r}, {OpsConst!r}, 'KMethodPrograms']",
        )
    )
    AddAliasesMut(SourceLines, ProgramData, OwnerConst, OpsConst)
    SourceLines.append("")
    return FormatSource("\n".join(SourceLines))


# removal discovery stays isolated so facade parsing and source reconstruction have separate contracts
def GetRemovedLines(
    TreeData: AstLib.Module, SourceLines: list[str], TargetNames: set[str]
) -> set[int]:
    RemovedLines: set[int] = set()
    for NodeData in TreeData.body:
        if isinstance(NodeData, AstLib.Assign):
            NameTexts = {
                TargetNode.id
                for TargetNode in NodeData.targets
                if isinstance(TargetNode, AstLib.Name)
            }
        elif isinstance(NodeData, AstLib.AnnAssign) and isinstance(
            NodeData.target, AstLib.Name
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
    return RemovedLines


# registry insertion stays isolated so source ordering remains deterministic across generated facades
def InsertRegistry(
    SourceLines: list[str],
    RemovedLines: set[int],
    InsertAfter: int,
    ImportLines: list[str],
) -> str:
    OutputLines: list[str] = []
    for LineNumber, SourceLine in enumerate(SourceLines, start=1):
        if LineNumber not in RemovedLines:
            OutputLines.append(SourceLine)
        if LineNumber == InsertAfter:
            OutputLines.extend(ImportLines)
    OutputLines.append("")
    return FormatSource("\n".join(OutputLines))


# facade rewriting stays small so parsing removal and insertion can evolve independently
def RewriteFacade(ProgramData: ProgramData) -> str:
    SourceLines = ProgramData.SourceText.splitlines()
    TreeData = AstLib.parse(
        ProgramData.SourceText, filename=str(ProgramData.SourcePath)
    )
    TargetNames = {ProgramData.OwnerName, ProgramData.OpsName}
    RegistryNames = {
        AliasData.asname or AliasData.name
        for NodeData in TreeData.body
        if isinstance(NodeData, AstLib.ImportFrom)
        and NodeData.level == 1
        and (NodeData.module == "Registry")
        for AliasData in NodeData.names
    }
    if TargetNames.issubset(RegistryNames):
        return FormatSource(ProgramData.SourceText)
    RemovedLines = GetRemovedLines(TreeData, SourceLines, TargetNames)
    ImportEnds = (
        NodeData.end_lineno
        for NodeData in TreeData.body
        if isinstance(NodeData, (AstLib.Import, AstLib.ImportFrom))
    )
    InsertAfter = max(ImportEnds)
    ImportLines = [
        "",
        "from .Registry import (",
        f"    {ProgramData.OwnerName},",
        f"    {ProgramData.OpsName},",
        ")",
    ]
    return InsertRegistry(SourceLines, RemovedLines, InsertAfter, ImportLines)


# needed to keep reverse engineering responsibilities isolated and maintainable
def HashText(SourceText: str) -> str:
    return Hashlib.sha256(SourceText.encode("utf-8")).hexdigest()


# needed to keep reverse engineering responsibilities isolated and maintainable
def HashProgram(ProgramData: ProgramData) -> str:
    CanonicalData = (ProgramData.OwnerName, ProgramData.OpsName, ProgramData.Streams)
    return HashText(RenderValue(CanonicalData))


# manifest records preserve every program identity and its reproducible evidence
def BuildStat(ProgramItem: ProgramData, FacadeTexts: dict[str, str]) -> tuple:
    return (
        ProgramItem.VariantPath,
        ProgramItem.OwnerName,
        ProgramItem.OpsName,
        tuple((StreamName for StreamName, SpareValue in ProgramItem.Streams)),
        sum((len(Operations) for SpareValue, Operations in ProgramItem.Streams)),
        HashProgram(ProgramItem),
        ProgramItem.PublicNames,
        ProgramItem.ByteStats,
        HashText(FacadeTexts[ProgramItem.VariantPath]),
    )


# manifest assembly keeps the large focused evidence table isolated from source scaffolding
def AppendStatsMut(
    SourceLines: list[str],
    Programs: tuple[ProgramData, ...],
    FacadeTexts: dict[str, str],
) -> None:
    SourceLines.extend(
        (
            "",
            "# focused program manifest data preserves all variant evidence in one dedicated module",
            "KProgramManifest = (",
        )
    )
    for ProgramItem in Programs:
        SourceLines.append(f"    {RenderValue(BuildStat(ProgramItem, FacadeTexts))},")
    SourceLines.extend(
        (
            ")",
            "",
            "# verifier compatibility exposes the focused manifest through its stable public name",
            "KProgramStats = KProgramManifest",
            "",
        )
    )


# needed to keep reverse engineering responsibilities isolated and maintainable
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
    ]
    AppendStatsMut(SourceLines, Programs, FacadeTexts)
    return FormatSource("\n".join(SourceLines))
