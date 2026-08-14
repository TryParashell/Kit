# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

import argparse
import importlib
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile

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
from ProgramVerifier import VerifyTree


# repository discovery stays anchored to this script so commands work from any directory
KRepoRoot = Path(__file__).resolve().parents[3]


# production program output has one canonical root shared by write and check modes
KProgramRoot = KRepoRoot / "src" / "convert" / "adapters" / "solidworks" / "programs"


# compact golden evidence lives beside the generator rather than production runtime modules
KManifestPath = Path(__file__).resolve().parent / "ProgramManifest.py"


# command parsing keeps destructive generation explicit and verification read only
def ParseArgs() -> argparse.Namespace:
    ParserData = argparse.ArgumentParser()
    ModeGroup = ParserData.add_mutually_exclusive_group(required=True)
    ModeGroup.add_argument("--write", action="store_true", dest="WriteMode")
    ModeGroup.add_argument("--check", action="store_true", dest="CheckMode")
    ParserData.add_argument("--source-root", type=Path, dest="SourceRoot")
    ParserData.add_argument(
        "--program-root", type=Path, default=KProgramRoot, dest="ProgramRoot"
    )
    ParserData.add_argument(
        "--manifest", type=Path, default=KManifestPath, dest="ManifestPath"
    )
    return ParserData.parse_args()


# generated filenames must stay pascal and digit free before anything reaches disk
def CheckPaths(OutputTexts: dict[Path, str]) -> None:
    FoldedPaths: dict[str, Path] = {}
    for RelativePath in OutputTexts:
        FileStem = RelativePath.stem
        if not re.fullmatch(r"[A-Z][A-Za-z]*", FileStem):
            raise ValueError(f"generated filename is invalid {RelativePath}")
        FoldedPath = RelativePath.as_posix().casefold()
        PriorPath = FoldedPaths.get(FoldedPath)
        if PriorPath is not None and PriorPath != RelativePath:
            raise ValueError(
                f"case insensitive output collision {PriorPath} and {RelativePath}"
            )
        FoldedPaths[FoldedPath] = RelativePath


# one in memory render pass prevents partial output when any owner or path is invalid
def BuildOutputs(
    Programs: tuple[ProgramData, ...],
) -> tuple[dict[Path, str], str]:
    Catalogs, VariantMethods = BuildMethods(Programs)
    OutputTexts: dict[Path, str] = {}
    FacadeTexts: dict[str, str] = {}
    for GroupPath, OwnerSites in Catalogs.items():
        RelativePath = Path("Owners") / Path(GroupPath + ".py")
        OutputTexts[RelativePath] = RenderOwner(OwnerSites)
    MethodTotal = 0
    for ProgramItem in Programs:
        MethodItems = VariantMethods[ProgramItem.VariantPath]
        ModulePaths: list[str] = []
        for MethodItem in MethodItems:
            RelativePath = (
                Path(ProgramItem.VariantPath)
                / "Methods"
                / Path(MethodItem.GroupPath + ".py")
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
        RegistryPath = Path(ProgramItem.VariantPath) / "Registry.py"
        OutputTexts[RegistryPath] = RenderRegistry(ProgramItem, tuple(ModulePaths))
        FacadeText = RewriteFacade(ProgramItem)
        FacadeTexts[ProgramItem.VariantPath] = FacadeText
        FacadePath = Path(ProgramItem.VariantPath) / "Program.py"
        OutputTexts[FacadePath] = FacadeText
        MethodTotal += len(MethodItems)
    GlobalStats = (
        len(Programs),
        sum(len(ProgramItem.Streams) for ProgramItem in Programs),
        len(Catalogs),
        sum(len(OwnerSites) for OwnerSites in Catalogs.values()),
        MethodTotal,
        sum(
            len(Operations)
            for ProgramItem in Programs
            for _, Operations in ProgramItem.Streams
        ),
    )
    CheckPaths(OutputTexts)
    return OutputTexts, RenderManifest(Programs, FacadeTexts, GlobalStats)


# resolved path checks confine cleanup to the generated production subtree
def IsWithin(TargetPath: Path, ParentPath: Path) -> bool:
    try:
        TargetPath.resolve().relative_to(ParentPath.resolve())
    except ValueError:
        return False
    return True


# validated temporary output replaces only known generated roots and facade files
def WriteTree(
    ProgramRoot: Path,
    ManifestPath: Path,
    OutputTexts: dict[Path, str],
    ManifestText: str,
) -> None:
    ProgramRoot = ProgramRoot.resolve()
    ProgramRoot.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="KitProgramTree-") as TempName:
        TempRoot = Path(TempName)
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
                shutil.rmtree(CleanupRoot)
        for RelativePath in sorted(OutputTexts):
            OutputPath = ProgramRoot / RelativePath
            OutputPath.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(TempRoot / RelativePath, OutputPath)
        ManifestPath.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(TempManifest, ManifestPath)


# stale imports must not hide freshly generated facades during same process verification
def ClearModules() -> None:
    PrefixText = "convert.adapters.solidworks.programs."
    StaleNames = tuple(
        ModuleName for ModuleName in sys.modules if ModuleName.startswith(PrefixText)
    )
    for ModuleName in StaleNames:
        del sys.modules[ModuleName]
    importlib.invalidate_caches()


# direct script execution needs the source tree available for compatibility imports
def AddSourcePath() -> None:
    SourcePath = str(KRepoRoot / "src")
    if SourcePath not in sys.path:
        sys.path.insert(0, SourcePath)


# one executable owns decomposition writes and exhaustive deterministic checks
def MainEntry() -> int:
    Arguments = ParseArgs()
    ProgramRoot = Arguments.ProgramRoot.resolve()
    ManifestPath = Arguments.ManifestPath.resolve()
    AddSourcePath()
    if Arguments.CheckMode:
        CheckStats = VerifyTree(ProgramRoot, ManifestPath)
        print(json.dumps(CheckStats, indent=2, sort_keys=True))
        return 0
    if Arguments.SourceRoot is None:
        raise ValueError("write mode requires a monolithic source root")
    SourceRoot = Arguments.SourceRoot.resolve()
    Programs = LoadPrograms(SourceRoot)
    OutputTexts, ManifestText = BuildOutputs(Programs)
    WriteTree(ProgramRoot, ManifestPath, OutputTexts, ManifestText)
    ClearModules()
    CheckStats = VerifyTree(ProgramRoot, ManifestPath)
    print(json.dumps(CheckStats, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(MainEntry())
