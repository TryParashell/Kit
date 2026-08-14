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
import importlib as Importlib
from operator import itemgetter as ItemGetter
from pathlib import Path as PathInfo
from typing import Any as AnyInfo
from ProgramModel import MethodData, ProgramData
from ProgramReader import GetByteStats, ReadAssigns
from ProgramRenderer import HashProgram, HashText, RenderRegistry


# needed to keep reverse engineering responsibilities isolated and maintainable
def LoadManifest(ManifestPath: PathInfo) -> tuple[tuple[AnyInfo, ...], tuple[AnyInfo, ...]]:
    SourceText = ManifestPath.read_text(encoding='utf-8')
    AssignData = ReadAssigns(AstLib.parse(SourceText, filename=str(ManifestPath)))
    try:
        GlobalStats = AssignData['KGlobalStats'][1]
        ProgramStats = AssignData['KProgramStats'][1]
    except KeyError as ErrorData:
        raise ValueError('program decomposition manifest is incomplete') from ErrorData
    return (GlobalStats, ProgramStats)


# needed to keep reverse engineering responsibilities isolated and maintainable
def ReadOwners(ProgramRoot: PathInfo) -> dict[str, tuple[tuple[object, str], ...]]:
    OwnerRoot = ProgramRoot / 'Owners'
    Catalogs: dict[str, tuple[tuple[object, str], ...]] = {}
    for OwnerPath in sorted(OwnerRoot.rglob('*.py')):
        GroupPath = OwnerPath.relative_to(OwnerRoot).with_suffix('').as_posix()
        SourceText = OwnerPath.read_text(encoding='utf-8')
        AssignData = ReadAssigns(AstLib.parse(SourceText, filename=str(OwnerPath)))
        try:
            OwnerMap = AssignData['KOwnerSites'][1]
        except KeyError as ErrorData:
            raise ValueError(f'owner catalog is incomplete {OwnerPath}') from ErrorData
        OwnerSites = tuple(OwnerMap.items())
        Catalogs[GroupPath] = OwnerSites
    return Catalogs


# needed to keep reverse engineering responsibilities isolated and maintainable
def ReadMethod(MethodPath: PathInfo, MethodRoot: PathInfo, Catalogs: dict[str, tuple[tuple[object, str], ...]]) -> MethodData:
    GroupPath = MethodPath.relative_to(MethodRoot).with_suffix('').as_posix()
    try:
        OwnerSites = Catalogs[GroupPath]
    except KeyError as ErrorData:
        raise ValueError(f'method owner catalog is missing {GroupPath}') from ErrorData
    SourceText = MethodPath.read_text(encoding='utf-8')
    TreeData = AstLib.parse(SourceText, filename=str(MethodPath))
    ProgramNode: AstLib.AST | None = None
    for NodeData in TreeData.body:
        if not isinstance(NodeData, AstLib.Assign):
            continue
        if any((isinstance(TargetNode, AstLib.Name) and TargetNode.id == 'KMethodProgram' for TargetNode in NodeData.targets)):
            ProgramNode = NodeData.value
            break
    if not isinstance(ProgramNode, AstLib.Tuple) or len(ProgramNode.elts) != 2:
        raise ValueError(f'method program is incomplete {MethodPath}')
    StreamMap = ReadAssigns(AstLib.Module(body=[AstLib.Assign(targets=[AstLib.Name(id='KStreamData', ctx=AstLib.Store())], value=ProgramNode.elts[1])], type_ignores=[]))['KStreamData'][1]
    StreamOps = tuple(((StreamName, tuple(Operations)) for StreamName, Operations in StreamMap.items()))
    MethodItem = MethodData(GroupPath=GroupPath, OwnerSites=OwnerSites, StreamOps=StreamOps)
    return MethodItem


# needed to keep reverse engineering responsibilities isolated and maintainable
def SortMethodPath(MethodPath: PathInfo) -> str:
    return MethodPath.as_posix()


# needed to keep reverse engineering responsibilities isolated and maintainable
def ReadMethods(ProgramRoot: PathInfo, VariantPath: str, Catalogs: dict[str, tuple[tuple[object, str], ...]]) -> tuple[MethodData, ...]:
    MethodRoot = ProgramRoot / VariantPath / 'Methods'
    MethodPaths = tuple(sorted(MethodRoot.rglob('*.py'), key=SortMethodPath))
    if not MethodPaths:
        raise ValueError(f'variant methods are missing {VariantPath}')
    return tuple((ReadMethod(MethodPath, MethodRoot, Catalogs) for MethodPath in MethodPaths))


# needed to keep reverse engineering responsibilities isolated and maintainable
def ComposeStreams(MethodItems: tuple[MethodData, ...], StreamNames: tuple[str, ...]) -> tuple[tuple[str, tuple[tuple[int, int, str, str, AnyInfo], ...]], ...]:
    StreamResults: list[tuple[str, tuple[AnyInfo, ...]]] = []
    for StreamName in StreamNames:
        OwnedOps: list[tuple[int, int, str, str, AnyInfo]] = []
        for MethodItem in MethodItems:
            OwnerMap = dict(MethodItem.OwnerSites)
            StreamMap = dict(MethodItem.StreamOps)
            for StartPos, FieldWidth, OwnerKey, KindName, DefaultValue in StreamMap.get(StreamName, ()):
                try:
                    OwnerText = OwnerMap[OwnerKey]
                except KeyError as ErrorData:
                    raise ValueError(f'method owner key is missing {MethodItem.GroupPath} {OwnerKey!r}') from ErrorData
                OwnedOps.append((StartPos, FieldWidth, OwnerText, KindName, DefaultValue))
        OwnedOps.sort(key=ItemGetter(0))
        SourceCursor = 0
        for StartPos, FieldWidth, OwnerText, KindName, DefaultValue in OwnedOps:
            if FieldWidth <= 0 or StartPos != SourceCursor:
                raise ValueError(f'variant stream order drifted {StreamName!r} at {StartPos}')
            SourceCursor += FieldWidth
        StreamResults.append((StreamName, tuple(OwnedOps)))
    return tuple(StreamResults)


# needed to keep reverse engineering responsibilities isolated and maintainable
def MakeLegacy(Streams: tuple[tuple[str, tuple[AnyInfo, ...]], ...], OpsName: str) -> tuple[tuple[str, ...], AnyInfo]:
    OwnerNames = tuple(sorted({OwnerText for SpareValue, Operations in Streams for SpareValue, SpareValue, OwnerText, SpareValue, SpareValue in Operations}))
    OwnerIndex = {OwnerText: Index for Index, OwnerText in enumerate(OwnerNames)}
    LegacyStreams = {StreamName: tuple(((StartPos, FieldWidth, OwnerIndex[OwnerText], KindName, DefaultValue) for StartPos, FieldWidth, OwnerText, KindName, DefaultValue in Operations)) for StreamName, Operations in Streams}
    if OpsName == 'StreamPrograms':
        return (OwnerNames, LegacyStreams)
    return (OwnerNames, next(iter(LegacyStreams.values())))


# needed to keep reverse engineering responsibilities isolated and maintainable
def GetLiveStats(ModuleData: AnyInfo, OpsName: str, StreamNames: tuple[str, ...]) -> tuple[tuple[str, int, str], ...]:
    ByteStats: list[tuple[str, int, str]] = []
    if OpsName == 'StreamPrograms':
        OutputPairs = ((StreamName, ModuleData.EncodeProgram(StreamName)) for StreamName in StreamNames)
    elif OpsName == 'AnnotationOps':
        OutputPairs = ((StreamNames[0], ModuleData.EncodeTwoViewAnnotationManager()),)
    else:
        OutputPairs = ((StreamNames[0], ModuleData.EncodeProgram()),)
    for StreamName, OutputData in OutputPairs:
        ByteStats.append((StreamName, len(OutputData), Hashlib.sha256(OutputData).hexdigest()))
    return tuple(ByteStats)


# needed to keep reverse engineering responsibilities isolated and maintainable
def LoadCurrentInfo(ProgramRoot: PathInfo, ManifestPath: PathInfo) -> tuple[ProgramData, ...]:
    SpareValue, ProgramStats = LoadManifest(ManifestPath)
    Catalogs = ReadOwners(ProgramRoot)
    Programs: list[ProgramData] = []
    for StatRecord in ProgramStats:
        VariantPath, OwnerName, OpsName, StreamNames, SpareValue, SpareValue, PublicNames, SpareValue, SpareValue = StatRecord
        MethodItems = ReadMethods(ProgramRoot, VariantPath, Catalogs)
        Streams = ComposeStreams(MethodItems, StreamNames)
        ProgramPath = ProgramRoot / VariantPath / 'Program.py'
        Programs.append(ProgramData(VariantPath=VariantPath, SourcePath=ProgramPath, SourceText=ProgramPath.read_text(encoding='utf-8'), OwnerName=OwnerName, OpsName=OpsName, Streams=Streams, PublicNames=PublicNames, ByteStats=GetByteStats(Streams)))
    return tuple(Programs)


# runtime validation stays separate so filesystem equivalence never depends on module loading
def VerifyRuntime(
    ProgramItem: ProgramData, StreamNames: tuple[str, ...]
) -> None:
    VariantPath = ProgramItem.VariantPath
    ModuleName = 'convert.adapters.solidworks.programs.' + VariantPath.replace('/', '.') + '.Program'
    ModuleData = Importlib.import_module(ModuleName)
    MissingNames = tuple((NameText for NameText in ProgramItem.PublicNames if not hasattr(ModuleData, NameText)))
    if MissingNames:
        raise ValueError(f'public symbols are missing {VariantPath} {MissingNames}')
    OwnerNames, LegacyOps = MakeLegacy(ProgramItem.Streams, ProgramItem.OpsName)
    if getattr(ModuleData, ProgramItem.OwnerName) != OwnerNames:
        raise ValueError(f'legacy owners drifted {VariantPath}')
    if getattr(ModuleData, ProgramItem.OpsName) != LegacyOps:
        raise ValueError(f'legacy operations drifted {VariantPath}')
    if GetLiveStats(ModuleData, ProgramItem.OpsName, StreamNames) != ProgramItem.ByteStats:
        raise ValueError(f'encoded bytes drifted {VariantPath}')


# one variant verifier keeps logical byte public and registry checks together
def VerifyVariant(
    ProgramRoot: PathInfo,
    Catalogs: dict[str, tuple[tuple[object, str], ...]],
    StatRecord: tuple[AnyInfo, ...],
    CheckRuntime: bool,
) -> tuple[tuple[str, ...], int, int, int]:
    VariantPath, OwnerName, OpsName, StreamNames, ExpectedOps, ExpectedHash, PublicNames, ByteStats, FacadeHash = StatRecord
    MethodItems = ReadMethods(ProgramRoot, VariantPath, Catalogs)
    Streams = ComposeStreams(MethodItems, StreamNames)
    ProgramPath = ProgramRoot / VariantPath / 'Program.py'
    SourceText = ProgramPath.read_text(encoding='utf-8')
    ProgramItem = ProgramData(VariantPath=VariantPath, SourcePath=ProgramPath, SourceText=SourceText, OwnerName=OwnerName, OpsName=OpsName, Streams=Streams, PublicNames=PublicNames, ByteStats=ByteStats)
    OperationCount = sum((len(Operations) for SpareValue, Operations in Streams))
    if OperationCount != ExpectedOps or HashProgram(ProgramItem) != ExpectedHash:
        raise ValueError(f'logical program drifted {VariantPath}')
    if HashText(SourceText) != FacadeHash:
        raise ValueError(f'compatibility facade drifted {VariantPath}')
    if CheckRuntime:
        VerifyRuntime(ProgramItem, StreamNames)
    ModulePaths = tuple(('convert.adapters.solidworks.programs.' + VariantPath.replace('/', '.') + '.Methods.' + MethodItem.GroupPath.replace('/', '.') for MethodItem in MethodItems))
    RegistryPath = ProgramRoot / VariantPath / 'Registry.py'
    if RegistryPath.read_text(encoding='utf-8') != RenderRegistry(ProgramItem, ModulePaths):
        raise ValueError(f'variant registry drifted {VariantPath}')
    UsedGroups = tuple((MethodItem.GroupPath for MethodItem in MethodItems))
    return UsedGroups, len(MethodItems), len(Streams), OperationCount


# tree verification aggregates focused variant results so global evidence stays independently checkable
def VerifyTree(ProgramRoot: PathInfo, ManifestPath: PathInfo, CheckRuntime: bool=True) -> dict[str, int]:
    ExpectedGlobal, ProgramStats = LoadManifest(ManifestPath)
    Catalogs = ReadOwners(ProgramRoot)
    MethodTotal = 0
    StreamTotal = 0
    OperationTotal = 0
    UsedGroups: set[str] = set()
    for StatRecord in ProgramStats:
        VariantGroups, MethodCount, StreamCount, OperationCount = VerifyVariant(ProgramRoot, Catalogs, StatRecord, CheckRuntime)
        UsedGroups.update(VariantGroups)
        MethodTotal += MethodCount
        StreamTotal += StreamCount
        OperationTotal += OperationCount
    if UsedGroups != set(Catalogs):
        raise ValueError('owner catalogs contain missing or unused groups')
    ActualGlobal = (len(ProgramStats), StreamTotal, len(Catalogs), sum((len(OwnerSites) for OwnerSites in Catalogs.values())), MethodTotal, OperationTotal)
    if ActualGlobal != ExpectedGlobal:
        raise ValueError(f'program decomposition counts drifted {ActualGlobal} expected {ExpectedGlobal}')
    return {'Programs': ActualGlobal[0], 'Streams': ActualGlobal[1], 'Catalogs': ActualGlobal[2], 'Owners': ActualGlobal[3], 'Methods': ActualGlobal[4], 'Operations': ActualGlobal[5]}
