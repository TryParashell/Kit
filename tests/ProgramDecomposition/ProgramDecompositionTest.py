# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

import ast as AstTree
import hashlib as HashLib
import importlib as ImportLib
from importlib.util import module_from_spec as BuildModule
from importlib.util import spec_from_file_location as BuildSpec
from pathlib import Path as FilePath
import re as RegexLib
import subprocess as Subprocess
import sys as SysModule
from typing import Callable, cast, Protocol, TypeAlias
import unittest as UnitTest

# manifest digest entries need one exact shape so generated evidence remains statically checkable
DigestStat: TypeAlias = tuple[str, int, str]


# manifest program entries need a direct contract independent from generated module execution
ProgramStat: TypeAlias = tuple[
    str,
    str,
    str,
    tuple[str, ...],
    int,
    str,
    tuple[str, ...],
    tuple[DigestStat, ...],
    str,
]


# dynamic manifest loading needs a structural contract for immutable decomposition evidence
class ManifestContract(Protocol):
    KGlobalStats: tuple[int, int, int, int, int, int]
    KProgramStats: tuple[ProgramStat, ...]


# stream encoders need their argument contract separated from parameterless generated encoders
class StreamProgram(Protocol):
    EncodeProgram: Callable[[str], bytes]


# ordinary generated programs need a direct contract for their parameterless encoder
class DefaultProgram(Protocol):
    EncodeProgram: Callable[[], bytes]


# annotation programs need a direct contract for their specialized encoder
class AnnotationProgram(Protocol):
    EncodeTwoViewAnnotationManager: Callable[[], bytes]


# repository anchoring keeps tests independent from the current working directory
KRepoRoot = FilePath(__file__).resolve().parents[2]


# production decomposition counts must cover every generated program artifact
KProgramRoot = KRepoRoot / "src" / "convert" / "adapters" / "solidworks" / "programs"


# the executable checker owns structural logical public and byte equivalence validation
KGeneratorPath = (
    KRepoRoot / "re" / "tooling" / "ProgramDecomposition" / "GeneratePrograms.py"
)


# immutable evidence remains importable without executing production program modules
KManifestName = "ProgramDecompositionManifest"


# valid generated filenames use letters only and begin with an uppercase letter
KFilenamePattern = RegexLib.compile(r"[A-Z][A-Za-z]*")


# cryptographic evidence uses complete lowercase sha two hundred fifty six digests
KDigestPattern = RegexLib.compile(r"[a-f0-9]{64}")


# manifest loading isolates generated evidence from reverse engineering package names
def LoadManifest() -> ManifestContract:
    ManifestPath = KGeneratorPath.with_name("ProgramManifest.py")
    ManifestSpec = BuildSpec(KManifestName, ManifestPath)
    if ManifestSpec is None or ManifestSpec.loader is None:
        raise RuntimeError("program decomposition manifest cannot be loaded")
    ManifestData = BuildModule(ManifestSpec)
    ManifestSpec.loader.exec_module(ManifestData)
    return cast(ManifestContract, ManifestData)


# artifact tests keep the generated tree complete and explicitly imported
class TestArtifacts(UnitTest.TestCase):

    # exact artifact counts expose missing catalogs methods registries or facades immediately
    def TestCounts(self) -> None:
        OwnerPaths = tuple((KProgramRoot / "Owners").rglob("*.py"))
        MethodPaths = tuple(KProgramRoot.rglob("Methods/**/*.py"))
        RegistryPaths = tuple(KProgramRoot.rglob("Registry.py"))
        ProgramPaths = tuple(KProgramRoot.rglob("Program.py"))
        self.assertEqual(len(OwnerPaths), 212)
        self.assertEqual(len(MethodPaths), 3857)
        self.assertEqual(len(RegistryPaths), 43)
        self.assertEqual(len(ProgramPaths), 43)

    # every generated source path must remain pascal digit free and explicitly imported
    def TestSources(self) -> None:
        GeneratedPaths = tuple((KProgramRoot / "Owners").rglob("*.py")) + tuple(
            KProgramRoot.rglob("Methods/**/*.py")
        )
        GeneratedPaths += tuple(KProgramRoot.rglob("Registry.py"))
        for SourcePath in GeneratedPaths:
            self.assertIsNotNone(KFilenamePattern.fullmatch(SourcePath.stem))
            SourceTree = AstTree.parse(
                SourcePath.read_text(encoding="utf-8"), filename=str(SourcePath)
            )
            WildcardImports = tuple(
                AliasData
                for NodeData in AstTree.walk(SourceTree)
                if isinstance(NodeData, AstTree.ImportFrom)
                for AliasData in NodeData.names
                if AliasData.name == "*"
            )
            self.assertFalse(WildcardImports, SourcePath)


# manifest tests preserve migration scale and permanent logical evidence
class TestEvidence(UnitTest.TestCase):

    # compact manifest assertions preserve migration scale and permanent logical evidence
    def TestManifest(self) -> None:
        ManifestData = LoadManifest()
        self.assertEqual(ManifestData.KGlobalStats, (43, 75, 212, 2078, 3857, 185090))
        self.assertEqual(len(ManifestData.KProgramStats), 43)
        self.assertEqual(
            sum(ItemData[4] for ItemData in ManifestData.KProgramStats), 185090
        )
        self.assertEqual(
            sum(len(ItemData[7]) for ItemData in ManifestData.KProgramStats), 75
        )
        for ItemData in ManifestData.KProgramStats:
            self.assertIsNotNone(KDigestPattern.fullmatch(ItemData[5]))
            self.assertIsNotNone(KDigestPattern.fullmatch(ItemData[8]))
            for DigestData in ItemData[7]:
                self.assertIsNotNone(KDigestPattern.fullmatch(DigestData[2]))


# encoder tests preserve public symbols and byte exact program output
class TestEncoding(UnitTest.TestCase):

    # live encoders must retain every public symbol and byte digest from the oracle
    def TestPublicBytes(self) -> None:
        ManifestData = LoadManifest()
        for ItemData in ManifestData.KProgramStats:
            VariantPath = ItemData[0]
            OpsName = ItemData[2]
            StreamNames = ItemData[3]
            PublicNames = ItemData[6]
            ByteStats = ItemData[7]
            ModuleName = (
                "convert.adapters.solidworks.programs."
                + VariantPath.replace("/", ".")
                + ".Program"
            )
            ModuleData = ImportLib.import_module(ModuleName)
            self.assertFalse(
                tuple(
                    NameText
                    for NameText in PublicNames
                    if not hasattr(ModuleData, NameText)
                )
            )
            if OpsName == "StreamPrograms":
                StreamModule = cast(StreamProgram, ModuleData)
                OutputPairs = tuple(
                    (StreamName, StreamModule.EncodeProgram(StreamName))
                    for StreamName in StreamNames
                )
            elif OpsName == "AnnotationOps":
                AnnotationModule = cast(AnnotationProgram, ModuleData)
                OutputPairs = (
                    (
                        StreamNames[0],
                        AnnotationModule.EncodeTwoViewAnnotationManager(),
                    ),
                )
            else:
                DefaultModule = cast(DefaultProgram, ModuleData)
                OutputPairs = ((StreamNames[0], DefaultModule.EncodeProgram()),)
            ActualStats = tuple(
                (
                    StreamName,
                    len(OutputData),
                    HashLib.sha256(OutputData).hexdigest(),
                )
                for StreamName, OutputData in OutputPairs
            )
            self.assertEqual(ActualStats, ByteStats)


# generator tests keep checked output synchronized with canonical recovery data
class TestGenerator(UnitTest.TestCase):

    # executable check proves catalogs registries facades hashes and bytes agree together
    def TestGenCheck(self) -> None:
        CheckResult = Subprocess.run(
            [SysModule.executable, str(KGeneratorPath), "--check"],
            cwd=KRepoRoot,
            capture_output=True,
            check=False,
            text=True,
            timeout=300,
        )
        self.assertEqual(
            CheckResult.returncode,
            0,
            CheckResult.stdout + CheckResult.stderr,
        )
