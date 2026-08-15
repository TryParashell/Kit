# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations
import argparse as Argparse
import importlib as Importlib
import json as JsonData
from pathlib import Path as PathInfo
import re as Regex
import shutil as Shutil
import sys as System
import tempfile as Tempfile
from ProgramBuilder import BuildMethods
from ProgramModel import ProgramData
from ProgramReader import LoadPrograms
from ProgramRenderer import (
    RenderManifest,
    RenderMethod,
    RenderOwner,
    RenderRegistry,
    RewriteFacade,
)
from ProgramVerifier import LoadCurrentInfo, VerifyTree

# needed to keep reverse engineering responsibilities isolated and maintainable
KRepoRoot = PathInfo(__file__).resolve().parents[3]

# needed to keep reverse engineering responsibilities isolated and maintainable
KProgramRoot = KRepoRoot / "src" / "convert" / "adapters" / "solidworks" / "programs"

# needed to keep reverse engineering responsibilities isolated and maintainable
KManifestPath = PathInfo(__file__).resolve().parent / "ProgramManifest.py"


# needed to keep reverse engineering responsibilities isolated and maintainable
def ParseArgs() -> Argparse.Namespace:
    ParserData = Argparse.ArgumentParser()
    ModeGroup = ParserData.add_mutually_exclusive_group(required=True)
    ModeGroup.add_argument("--write", action="store_true", dest="WriteMode")
    ModeGroup.add_argument("--check", action="store_true", dest="CheckMode")
    ParserData.add_argument("--source-root", type=PathInfo, dest="SourceRoot")
    ParserData.add_argument(
        "--program-root", type=PathInfo, default=KProgramRoot, dest="ProgramRoot"
    )
    ParserData.add_argument(
        "--manifest", type=PathInfo, default=KManifestPath, dest="ManifestPath"
    )
    return ParserData.parse_args()


# needed to keep reverse engineering responsibilities isolated and maintainable
def CheckPaths(OutputTexts: dict[PathInfo, str]) -> None:
    FoldedPaths: dict[str, PathInfo] = {}
    for RelativePath in OutputTexts:
        FileStem = RelativePath.stem
        if not Regex.fullmatch("[A-Z][A-Za-z]*", FileStem):
            raise ValueError(f"generated filename is invalid {RelativePath}")
        FoldedPath = RelativePath.as_posix().casefold()
        PriorPath = FoldedPaths.get(FoldedPath)
        if PriorPath is not None and PriorPath != RelativePath:
            raise ValueError(
                f"case insensitive output collision {PriorPath} and {RelativePath}"
            )
        FoldedPaths[FoldedPath] = RelativePath


# needed to keep reverse engineering responsibilities isolated and maintainable
def BuildOutputs(Programs: tuple[ProgramData, ...]) -> tuple[dict[PathInfo, str], str]:
    Catalogs, VariantMethods = BuildMethods(Programs)
    OutputTexts: dict[PathInfo, str] = {}
    FacadeTexts: dict[str, str] = {}
    for GroupPath, OwnerSites in Catalogs.items():
        RelativePath = PathInfo("Owners") / PathInfo(GroupPath + ".py")
        OutputTexts[RelativePath] = RenderOwner(OwnerSites)
    MethodTotal = 0
    for ProgramItem in Programs:
        MethodItems = VariantMethods[ProgramItem.VariantPath]
        ModulePaths: list[str] = []
        for MethodItem in MethodItems:
            RelativePath = (
                PathInfo(ProgramItem.VariantPath)
                / "Methods"
                / PathInfo(MethodItem.GroupPath + ".py")
            )
            OwnerModule = (
                "convert.adapters.solidworks.programs.Owners."
                + MethodItem.GroupPath.replace("/", ".")
            )
            OutputTexts[RelativePath] = RenderMethod(OwnerModule, MethodItem)
            ModulePaths.append(
                "convert.adapters.solidworks.programs."
                + ProgramItem.VariantPath.replace("/", ".")
                + ".Methods."
                + MethodItem.GroupPath.replace("/", ".")
            )
        RegistryPath = PathInfo(ProgramItem.VariantPath) / "Registry.py"
        OutputTexts[RegistryPath] = RenderRegistry(ProgramItem, tuple(ModulePaths))
        FacadeText = RewriteFacade(ProgramItem)
        FacadeTexts[ProgramItem.VariantPath] = FacadeText
        FacadePath = PathInfo(ProgramItem.VariantPath) / "Program.py"
        OutputTexts[FacadePath] = FacadeText
        MethodTotal += len(MethodItems)
    GlobalStats = (
        len(Programs),
        sum((len(ProgramItem.Streams) for ProgramItem in Programs)),
        len(Catalogs),
        sum((len(OwnerSites) for OwnerSites in Catalogs.values())),
        MethodTotal,
        sum(
            (
                len(Operations)
                for ProgramItem in Programs
                for SpareValue, Operations in ProgramItem.Streams
            )
        ),
    )
    CheckPaths(OutputTexts)
    return (OutputTexts, RenderManifest(Programs, FacadeTexts, GlobalStats))


# needed to keep reverse engineering responsibilities isolated and maintainable
def IsWithin(TargetPath: PathInfo, ParentPath: PathInfo) -> bool:
    try:
        TargetPath.resolve().relative_to(ParentPath.resolve())
    except ValueError:
        return False
    return True


# needed to keep reverse engineering responsibilities isolated and maintainable
def WriteTree(
    ProgramRoot: PathInfo,
    ManifestPath: PathInfo,
    OutputTexts: dict[PathInfo, str],
    ManifestText: str,
) -> None:
    ProgramRoot = ProgramRoot.resolve()
    ProgramRoot.mkdir(parents=True, exist_ok=True)
    with Tempfile.TemporaryDirectory(prefix="KitProgramTree-") as TempName:
        TempRoot = PathInfo(TempName)
        for RelativePath, SourceText in OutputTexts.items():
            OutputPath = TempRoot / RelativePath
            OutputPath.parent.mkdir(parents=True, exist_ok=True)
            OutputPath.write_text(SourceText, encoding="utf-8", newline="\n")
        TempManifest = TempRoot / "ProgramManifest.py"
        TempManifest.write_text(ManifestText, encoding="utf-8", newline="\n")
        CleanupRoots = [ProgramRoot / "Owners"]
        CleanupRoots.extend(sorted(ProgramRoot.rglob("Methods"), reverse=True))
        for CleanupRoot in CleanupRoots:
            if not IsWithin(CleanupRoot, ProgramRoot):
                raise ValueError(f"cleanup escaped program root {CleanupRoot}")
            if CleanupRoot.exists():
                Shutil.rmtree(CleanupRoot)
        for RelativePath in sorted(OutputTexts):
            OutputPath = ProgramRoot / RelativePath
            OutputPath.parent.mkdir(parents=True, exist_ok=True)
            Shutil.copyfile(TempRoot / RelativePath, OutputPath)
        ManifestPath.parent.mkdir(parents=True, exist_ok=True)
        Shutil.copyfile(TempManifest, ManifestPath)


# needed to keep reverse engineering responsibilities isolated and maintainable
def ClearModules() -> None:
    PrefixText = "convert.adapters.solidworks.programs."
    StaleNames = tuple(
        (
            ModuleName
            for ModuleName in System.modules
            if ModuleName.startswith(PrefixText)
        )
    )
    for ModuleName in StaleNames:
        del System.modules[ModuleName]
    Importlib.invalidate_caches()


# needed to keep reverse engineering responsibilities isolated and maintainable
def AddSourcePath() -> None:
    SourcePath = str(KRepoRoot / "src")
    if SourcePath not in System.path:
        System.path.insert(0, SourcePath)


# needed to keep reverse engineering responsibilities isolated and maintainable
def MainEntry() -> int:
    Arguments = ParseArgs()
    ProgramRoot = Arguments.ProgramRoot.resolve()
    ManifestPath = Arguments.ManifestPath.resolve()
    AddSourcePath()
    if Arguments.CheckMode:
        CheckStats = VerifyTree(ProgramRoot, ManifestPath)
        print(JsonData.dumps(CheckStats, indent=2, sort_keys=True))
        return 0
    if Arguments.SourceRoot is None:
        Programs = LoadCurrentInfo(ProgramRoot, ManifestPath)
    else:
        Programs = LoadPrograms(Arguments.SourceRoot.resolve())
    OutputTexts, ManifestText = BuildOutputs(Programs)
    WriteTree(ProgramRoot, ManifestPath, OutputTexts, ManifestText)
    ClearModules()
    CheckStats = VerifyTree(ProgramRoot, ManifestPath)
    print(JsonData.dumps(CheckStats, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(MainEntry())
