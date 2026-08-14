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
import importlib
from operator import itemgetter as ItemGetter
from pathlib import Path
from typing import Any

from ProgramModel import MethodData, ProgramData
from ProgramReader import ReadAssigns
from ProgramRenderer import (
    HashProgram,
    HashText,
    RenderMethod,
    RenderOwner,
    RenderRegistry,
)


# checks need immutable expected evidence without importing reverse engineering tooling as a package
def LoadManifest(ManifestPath: Path) -> tuple[tuple[Any, ...], tuple[Any, ...]]:
    SourceText = ManifestPath.read_text(encoding="utf-8")
    AssignData = ReadAssigns(ast.parse(SourceText, filename=str(ManifestPath)))
    try:
        GlobalStats = AssignData["KGlobalStats"][1]
        ProgramStats = AssignData["KProgramStats"][1]
    except KeyError as ErrorData:
        raise ValueError("program decomposition manifest is incomplete") from ErrorData
    return GlobalStats, ProgramStats


# canonical owner modules are the single allowed source for exact trace spellings
def ReadOwners(ProgramRoot: Path) -> dict[str, tuple[tuple[object, str], ...]]:
    OwnerRoot = ProgramRoot / "Owners"
    Catalogs: dict[str, tuple[tuple[object, str], ...]] = {}
    for OwnerPath in sorted(OwnerRoot.rglob("*.py")):
        GroupPath = OwnerPath.relative_to(OwnerRoot).with_suffix("").as_posix()
        SourceText = OwnerPath.read_text(encoding="utf-8")
        AssignData = ReadAssigns(ast.parse(SourceText, filename=str(OwnerPath)))
        try:
            OwnerMap = AssignData["KOwnerSites"][1]
        except KeyError as ErrorData:
            raise ValueError(f"owner catalog is incomplete {OwnerPath}") from ErrorData
        OwnerSites = tuple(OwnerMap.items())
        if SourceText != RenderOwner(OwnerSites):
            raise ValueError(f"owner catalog is not canonical {OwnerPath}")
        Catalogs[GroupPath] = OwnerSites
    return Catalogs


# method modules must remain focused on one owner catalog and one variant table
def ReadMethod(
    MethodPath: Path,
    MethodRoot: Path,
    Catalogs: dict[str, tuple[tuple[object, str], ...]],
) -> MethodData:
    GroupPath = MethodPath.relative_to(MethodRoot).with_suffix("").as_posix()
    try:
        OwnerSites = Catalogs[GroupPath]
    except KeyError as ErrorData:
        raise ValueError(f"method owner catalog is missing {GroupPath}") from ErrorData
    SourceText = MethodPath.read_text(encoding="utf-8")
    TreeData = ast.parse(SourceText, filename=str(MethodPath))
    ProgramNode: ast.AST | None = None
    for NodeData in TreeData.body:
        if not isinstance(NodeData, ast.Assign):
            continue
        if any(
            isinstance(TargetNode, ast.Name) and TargetNode.id == "KMethodProgram"
            for TargetNode in NodeData.targets
        ):
            ProgramNode = NodeData.value
            break
    if not isinstance(ProgramNode, ast.Tuple) or len(ProgramNode.elts) != 2:
        raise ValueError(f"method program is incomplete {MethodPath}")
    StreamMap = ReadAssigns(
        ast.Module(
            body=[
                ast.Assign(
                    targets=[ast.Name(id="KStreamData", ctx=ast.Store())],
                    value=ProgramNode.elts[1],
                )
            ],
            type_ignores=[],
        )
    )["KStreamData"][1]
    StreamOps = tuple(
        (StreamName, tuple(Operations)) for StreamName, Operations in StreamMap.items()
    )
    MethodItem = MethodData(
        GroupPath=GroupPath,
        OwnerSites=OwnerSites,
        StreamOps=StreamOps,
    )
    OwnerModule = "convert.adapters.solidworks.programs.Owners." + GroupPath.replace(
        "/", "."
    )
    if SourceText != RenderMethod(OwnerModule, MethodItem):
        raise ValueError(f"method module is not canonical {MethodPath}")
    return MethodItem


# each variant needs deterministic method ordering before its explicit registry is checked
def ReadMethods(
    ProgramRoot: Path,
    VariantPath: str,
    Catalogs: dict[str, tuple[tuple[object, str], ...]],
) -> tuple[MethodData, ...]:
    MethodRoot = ProgramRoot / VariantPath / "Methods"
    MethodPaths = tuple(sorted(MethodRoot.rglob("*.py")))
    if not MethodPaths:
        raise ValueError(f"variant methods are missing {VariantPath}")
    return tuple(
        ReadMethod(MethodPath, MethodRoot, Catalogs) for MethodPath in MethodPaths
    )


# verification composes independent method modules into the original contiguous stream order
def ComposeStreams(
    MethodItems: tuple[MethodData, ...], StreamNames: tuple[str, ...]
) -> tuple[tuple[str, tuple[tuple[int, int, str, str, Any], ...]], ...]:
    StreamResults: list[tuple[str, tuple[Any, ...]]] = []
    for StreamName in StreamNames:
        OwnedOps: list[tuple[int, int, str, str, Any]] = []
        for MethodItem in MethodItems:
            OwnerMap = dict(MethodItem.OwnerSites)
            StreamMap = dict(MethodItem.StreamOps)
            for StartPos, FieldWidth, OwnerKey, KindName, DefaultValue in StreamMap.get(
                StreamName, ()
            ):
                try:
                    OwnerText = OwnerMap[OwnerKey]
                except KeyError as ErrorData:
                    raise ValueError(
                        f"method owner key is missing {MethodItem.GroupPath} {OwnerKey!r}"
                    ) from ErrorData
                OwnedOps.append(
                    (StartPos, FieldWidth, OwnerText, KindName, DefaultValue)
                )
        OwnedOps.sort(key=ItemGetter(0))
        SourceCursor = 0
        for StartPos, FieldWidth, OwnerText, KindName, DefaultValue in OwnedOps:
            if FieldWidth <= 0 or StartPos != SourceCursor:
                raise ValueError(
                    f"variant stream order drifted {StreamName!r} at {StartPos}"
                )
            SourceCursor += FieldWidth
        StreamResults.append((StreamName, tuple(OwnedOps)))
    return tuple(StreamResults)


# imported facades must expose the exact legacy tuples even though storage is decomposed
def MakeLegacy(
    Streams: tuple[tuple[str, tuple[Any, ...]], ...], OpsName: str
) -> tuple[tuple[str, ...], Any]:
    OwnerNames = tuple(
        sorted(
            {
                OwnerText
                for _, Operations in Streams
                for _, _, OwnerText, _, _ in Operations
            }
        )
    )
    OwnerIndex = {OwnerText: Index for Index, OwnerText in enumerate(OwnerNames)}
    LegacyStreams = {
        StreamName: tuple(
            (
                StartPos,
                FieldWidth,
                OwnerIndex[OwnerText],
                KindName,
                DefaultValue,
            )
            for StartPos, FieldWidth, OwnerText, KindName, DefaultValue in Operations
        )
        for StreamName, Operations in Streams
    }
    if OpsName == "StreamPrograms":
        return OwnerNames, LegacyStreams
    return OwnerNames, next(iter(LegacyStreams.values()))


# live byte checks prove compatibility facades still execute every original encoder policy
def GetLiveStats(
    ModuleData: Any,
    OpsName: str,
    StreamNames: tuple[str, ...],
) -> tuple[tuple[str, int, str], ...]:
    ByteStats: list[tuple[str, int, str]] = []
    if OpsName == "StreamPrograms":
        OutputPairs = (
            (StreamName, ModuleData.EncodeProgram(StreamName))
            for StreamName in StreamNames
        )
    elif OpsName == "AnnotationOps":
        OutputPairs = ((StreamNames[0], ModuleData.EncodeTwoViewAnnotationManager()),)
    else:
        OutputPairs = ((StreamNames[0], ModuleData.EncodeProgram()),)
    for StreamName, OutputData in OutputPairs:
        ByteStats.append(
            (
                StreamName,
                len(OutputData),
                hashlib.sha256(OutputData).hexdigest(),
            )
        )
    return tuple(ByteStats)


# one exhaustive verifier guards structure formatting public imports and encoded bytes together
def VerifyTree(ProgramRoot: Path, ManifestPath: Path) -> dict[str, int]:
    ExpectedGlobal, ProgramStats = LoadManifest(ManifestPath)
    Catalogs = ReadOwners(ProgramRoot)
    MethodTotal = 0
    StreamTotal = 0
    OperationTotal = 0
    UsedGroups: set[str] = set()
    for StatRecord in ProgramStats:
        (
            VariantPath,
            OwnerName,
            OpsName,
            StreamNames,
            ExpectedOps,
            ExpectedHash,
            PublicNames,
            ByteStats,
            FacadeHash,
        ) = StatRecord
        MethodItems = ReadMethods(ProgramRoot, VariantPath, Catalogs)
        UsedGroups.update(MethodItem.GroupPath for MethodItem in MethodItems)
        Streams = ComposeStreams(MethodItems, StreamNames)
        ProgramPath = ProgramRoot / VariantPath / "Program.py"
        SourceText = ProgramPath.read_text(encoding="utf-8")
        ProgramItem = ProgramData(
            VariantPath=VariantPath,
            SourcePath=ProgramPath,
            SourceText=SourceText,
            OwnerName=OwnerName,
            OpsName=OpsName,
            Streams=Streams,
            PublicNames=PublicNames,
            ByteStats=ByteStats,
        )
        OperationCount = sum(len(Operations) for _, Operations in Streams)
        if OperationCount != ExpectedOps or HashProgram(ProgramItem) != ExpectedHash:
            raise ValueError(f"logical program drifted {VariantPath}")
        if HashText(SourceText) != FacadeHash:
            raise ValueError(f"compatibility facade drifted {VariantPath}")
        ModuleName = (
            "convert.adapters.solidworks.programs."
            + VariantPath.replace("/", ".")
            + ".Program"
        )
        ModuleData = importlib.import_module(ModuleName)
        MissingNames = tuple(
            NameText for NameText in PublicNames if not hasattr(ModuleData, NameText)
        )
        if MissingNames:
            raise ValueError(f"public symbols are missing {VariantPath} {MissingNames}")
        OwnerNames, LegacyOps = MakeLegacy(Streams, OpsName)
        if getattr(ModuleData, OwnerName) != OwnerNames:
            raise ValueError(f"legacy owners drifted {VariantPath}")
        if getattr(ModuleData, OpsName) != LegacyOps:
            raise ValueError(f"legacy operations drifted {VariantPath}")
        if GetLiveStats(ModuleData, OpsName, StreamNames) != ByteStats:
            raise ValueError(f"encoded bytes drifted {VariantPath}")
        ModulePaths = tuple(
            "convert.adapters.solidworks.programs."
            + VariantPath.replace("/", ".")
            + ".Methods."
            + MethodItem.GroupPath.replace("/", ".")
            for MethodItem in MethodItems
        )
        RegistryPath = ProgramRoot / VariantPath / "Registry.py"
        if RegistryPath.read_text(encoding="utf-8") != RenderRegistry(
            ProgramItem, ModulePaths
        ):
            raise ValueError(f"variant registry drifted {VariantPath}")
        MethodTotal += len(MethodItems)
        StreamTotal += len(Streams)
        OperationTotal += OperationCount
    if UsedGroups != set(Catalogs):
        raise ValueError("owner catalogs contain missing or unused groups")
    ActualGlobal = (
        len(ProgramStats),
        StreamTotal,
        len(Catalogs),
        sum(len(OwnerSites) for OwnerSites in Catalogs.values()),
        MethodTotal,
        OperationTotal,
    )
    if ActualGlobal != ExpectedGlobal:
        raise ValueError(
            f"program decomposition counts drifted {ActualGlobal} expected {ExpectedGlobal}"
        )
    return {
        "Programs": ActualGlobal[0],
        "Streams": ActualGlobal[1],
        "Catalogs": ActualGlobal[2],
        "Owners": ActualGlobal[3],
        "Methods": ActualGlobal[4],
        "Operations": ActualGlobal[5],
    }
