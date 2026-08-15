# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from dataclasses import replace as ReplaceValue
from functools import partial as PartialFunc
import os as OsSystem
from pathlib import Path as FilePath
from tempfile import TemporaryDirectory as TempDirectory

from interchange import CadDocument
from interchange import frozen_mapping as FreezeMapping

from convert.adapters.base.AdapterProtocols import CadWriterAdapter
from convert.adapters.registry.RegistryErrors import RegistryError
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.base.WritePolicy import RunCheckedMut
from convert.adapters.base.WriteResult import WriteResult


# symlink aware existence protects replacement checks from dangling destination entries
def HasPath(FileValue: FilePath) -> bool:
    return FileValue.exists() or FileValue.is_symlink()


# missing ancestry tracking allows failed staging to restore the original directory tree
def GetAbsentPaths(FileValue: FilePath) -> tuple[FilePath, ...]:
    PathValues: list[FilePath] = []
    CurrentPath = FileValue
    while not HasPath(CurrentPath):
        PathValues.append(CurrentPath)
        ParentPath = CurrentPath.parent
        if ParentPath == CurrentPath:
            break
        CurrentPath = ParentPath
    return tuple(PathValues)


# inode identity prevents cleanup from deleting concurrently replaced directories
def GetPathIdentity(FileValue: FilePath) -> tuple[int, int, int]:
    StatusData = FileValue.stat(follow_symlinks=False)
    return StatusData.st_dev, StatusData.st_ino, StatusData.st_mode


# failed staging removes only empty directories created by the current write operation
def RemoveCreated(
    CreatedValues: tuple[tuple[FilePath, tuple[int, int, int]], ...],
) -> None:
    for FileValue, IdentityData in CreatedValues:
        try:
            if GetPathIdentity(FileValue) != IdentityData:
                break
            FileValue.rmdir()
        except FileNotFoundError:
            continue
        except OSError:
            break


# deterministic ordering commits requested output first while preserving companion filename order
def GetOutputPaths(
    StagingPath: FilePath,
    TargetPath: FilePath,
) -> tuple[tuple[FilePath, FilePath], ...]:
    OutputPaths = tuple(
        sorted(
            StagingPath.iterdir(),
            key=PartialFunc(GetOutputKey, TargetPath=TargetPath),
        )
    )
    if not OutputPaths or not HasPath(StagingPath / TargetPath.name):
        raise RegistryError("writer did not create the requested destination")
    return tuple(
        (OutputPath, TargetPath.parent / OutputPath.name) for OutputPath in OutputPaths
    )


# output ordering keeps the requested file first before deterministic companion names
def GetOutputKey(FileValue: FilePath, TargetPath: FilePath) -> tuple[bool, str, str]:
    return (
        FileValue.name.casefold() != TargetPath.name.casefold(),
        FileValue.name.casefold(),
        FileValue.name,
    )


# backup creation isolates overwrite rollback from ordinary staged companion outputs
def BackupTargets(
    TargetValues: tuple[tuple[FilePath, FilePath], ...],
    BackupPath: FilePath,
) -> list[tuple[FilePath, FilePath]]:
    ReplacedValues: list[tuple[FilePath, FilePath]] = []
    if not any(HasPath(TargetPair[1]) for TargetPair in TargetValues):
        return ReplacedValues
    BackupPath.mkdir()
    for TargetPair in TargetValues:
        TargetPath = TargetPair[1]
        if not HasPath(TargetPath):
            continue
        SavedPath = BackupPath / TargetPath.name
        OsSystem.replace(TargetPath, SavedPath)
        ReplacedValues.append((SavedPath, TargetPath))
    return ReplacedValues


# rollback restores both committed outputs and overwritten originals after any failure
def RestoreOutputs(
    CommitValues: list[tuple[FilePath, FilePath]],
    ReplacedValues: list[tuple[FilePath, FilePath]],
) -> None:
    for TargetPath, SourcePath in reversed(CommitValues):
        if HasPath(TargetPath):
            OsSystem.replace(TargetPath, SourcePath)
    for SavedPath, TargetPath in reversed(ReplacedValues):
        if HasPath(SavedPath):
            OsSystem.replace(SavedPath, TargetPath)


# atomic commit keeps requested and companion files consistent under overwrite failures
def CommitOutputs(
    StagingPath: FilePath,
    TargetPath: FilePath,
    Overwrite: bool,
) -> None:
    TargetValues = GetOutputPaths(StagingPath, TargetPath)
    if not Overwrite:
        ConflictPath = next(
            (OutputPair[1] for OutputPair in TargetValues if HasPath(OutputPair[1])),
            None,
        )
        if ConflictPath is not None:
            raise FileExistsError(ConflictPath)
    ReplacedValues: list[tuple[FilePath, FilePath]] = []
    CommitValues: list[tuple[FilePath, FilePath]] = []
    try:
        if Overwrite:
            ReplacedValues = BackupTargets(
                TargetValues,
                StagingPath / ".kit-backup",
            )
        for SourcePath, OutputPath in TargetValues:
            OsSystem.replace(SourcePath, OutputPath)
            CommitValues.append((OutputPath, SourcePath))
    except BaseException:
        RestoreOutputs(CommitValues, ReplacedValues)
        raise


# directory creation records exact identities so cleanup cannot remove concurrent replacements
def MakeParentsMut(
    AbsentPaths: tuple[FilePath, ...],
    CreatedValues: list[tuple[FilePath, tuple[int, int, int]]],
) -> list[tuple[FilePath, tuple[int, int, int]]]:
    for FileValue in reversed(AbsentPaths):
        try:
            FileValue.mkdir()
        except FileExistsError:
            if FileValue.is_symlink() or not FileValue.is_dir():
                raise
            continue
        CreatedValues.append((FileValue, GetPathIdentity(FileValue)))
    return CreatedValues


# path writes remain transactional because validation completes before destination replacement
def WritePathStaged(
    DocumentData: CadDocument,
    AdapterData: CadWriterAdapter,
    TargetData: str | FilePath,
    OptionsData: WriteOptions,
    AllowCarrier: bool,
    NeedSelfContained: bool,
) -> WriteResult:
    FinalPath = FilePath(TargetData).expanduser().resolve()
    if HasPath(FinalPath) and not OptionsData.Overwrite:
        raise FileExistsError(FinalPath)
    AbsentPaths = GetAbsentPaths(FinalPath.parent)
    CreatedValues: list[tuple[FilePath, tuple[int, int, int]]] = []
    try:
        MakeParentsMut(AbsentPaths, CreatedValues)
        PrefixText = f".{FinalPath.name}.kit-"
        with TempDirectory(prefix=PrefixText, dir=FinalPath.parent) as TempName:
            StagingPath = FilePath(TempName)
            StagedTarget = StagingPath / FinalPath.name
            OptionValues = dict(OptionsData.OptionValues)
            OptionValues["final_destination"] = str(FinalPath)
            OptionValues["final_overwrite"] = OptionsData.Overwrite
            ResultData = RunCheckedMut(
                DocumentData,
                AdapterData,
                StagedTarget,
                ReplaceValue(
                    OptionsData,
                    Overwrite=False,
                    OptionValues=FreezeMapping(OptionValues),
                ),
                AllowCarrier,
                NeedSelfContained,
            )
            if (
                ResultData.OutputPath is None
                or ResultData.OutputPath.resolve() != StagedTarget.resolve()
            ):
                raise RegistryError("path writer returned an unexpected destination")
            CommitOutputs(StagingPath, FinalPath, OptionsData.Overwrite)
    except BaseException:
        RemoveCreated(tuple(reversed(CreatedValues)))
        raise
    return ReplaceValue(ResultData, OutputPath=FinalPath)
