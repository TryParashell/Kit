# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

import ast
import hashlib as HashLib
import importlib as ImportLib
from pathlib import Path
import re
import subprocess as Subprocess
import sys
import unittest as UnitTest


# repository anchoring keeps tests independent from the current working directory
KRepoRoot = Path(__file__).resolve().parents[2]


# production decomposition counts must cover every generated program artifact
KProgramRoot = KRepoRoot / "src" / "convert" / "adapters" / "solidworks" / "programs"


# the executable checker owns structural logical public and byte equivalence validation
KGeneratorPath = (
    KRepoRoot / "re" / "tooling" / "ProgramDecomposition" / "GeneratePrograms.py"
)


# immutable evidence remains importable without executing production program modules
KManifestName = "ProgramDecompositionManifest"


# valid generated filenames use letters only and begin with an uppercase letter
KFilenamePattern = re.compile(r"[A-Z][A-Za-z]*")


# cryptographic evidence uses complete lowercase sha two hundred fifty six digests
KDigestPattern = re.compile(r"[a-f0-9]{64}")


# manifest loading isolates generated evidence from reverse engineering package names
def LoadManifest():
    ManifestPath = KGeneratorPath.with_name("ProgramManifest.py")
    ManifestSpec = ImportLib.util.spec_from_file_location(KManifestName, ManifestPath)
    if ManifestSpec is None or ManifestSpec.loader is None:
        raise RuntimeError("program decomposition manifest cannot be loaded")
    ManifestData = ImportLib.util.module_from_spec(ManifestSpec)
    ManifestSpec.loader.exec_module(ManifestData)
    return ManifestData


# exhaustive contract tests keep focused modules equivalent to every legacy facade
class TestProgramDecomposition(UnitTest.TestCase):
    # exact artifact counts expose missing catalogs methods registries or facades immediately
    def TestArtifactCounts(self) -> None:
        OwnerPaths = tuple((KProgramRoot / "Owners").rglob("*.py"))
        MethodPaths = tuple(KProgramRoot.rglob("Methods/**/*.py"))
        RegistryPaths = tuple(KProgramRoot.rglob("Registry.py"))
        ProgramPaths = tuple(KProgramRoot.rglob("Program.py"))
        self.assertEqual(len(OwnerPaths), 212)
        self.assertEqual(len(MethodPaths), 3857)
        self.assertEqual(len(RegistryPaths), 43)
        self.assertEqual(len(ProgramPaths), 43)

    # every generated source path must remain pascal digit free and explicitly imported
    def TestGeneratedSources(self) -> None:
        GeneratedPaths = tuple((KProgramRoot / "Owners").rglob("*.py")) + tuple(
            KProgramRoot.rglob("Methods/**/*.py")
        )
        GeneratedPaths += tuple(KProgramRoot.rglob("Registry.py"))
        for SourcePath in GeneratedPaths:
            self.assertIsNotNone(KFilenamePattern.fullmatch(SourcePath.stem))
            SourceTree = ast.parse(
                SourcePath.read_text(encoding="utf-8"), filename=str(SourcePath)
            )
            WildcardImports = tuple(
                AliasData
                for NodeData in ast.walk(SourceTree)
                if isinstance(NodeData, ast.ImportFrom)
                for AliasData in NodeData.names
                if AliasData.name == "*"
            )
            self.assertFalse(WildcardImports, SourcePath)

    # compact manifest assertions preserve migration scale and permanent logical evidence
    def TestManifestEvidence(self) -> None:
        ManifestData = LoadManifest()
        self.assertEqual(ManifestData.KGlobalStats, (43, 75, 212, 2078, 3857, 185090))
        self.assertEqual(len(ManifestData.KProgramStats), 43)
        self.assertEqual(sum(ItemData[4] for ItemData in ManifestData.KProgramStats), 185090)
        self.assertEqual(
            sum(len(ItemData[7]) for ItemData in ManifestData.KProgramStats), 75
        )
        for ItemData in ManifestData.KProgramStats:
            self.assertIsNotNone(KDigestPattern.fullmatch(ItemData[5]))
            self.assertIsNotNone(KDigestPattern.fullmatch(ItemData[8]))
            for _, _, DigestText in ItemData[7]:
                self.assertIsNotNone(KDigestPattern.fullmatch(DigestText))

    # live encoders must retain every public symbol and byte digest from the oracle
    def TestPublicBytes(self) -> None:
        ManifestData = LoadManifest()
        for ItemData in ManifestData.KProgramStats:
            (
                VariantPath,
                _,
                OpsName,
                StreamNames,
                _,
                _,
                PublicNames,
                ByteStats,
                _,
            ) = ItemData
            ModuleName = (
                "convert.adapters.solidworks.programs."
                + VariantPath.replace("/", ".")
                + ".Program"
            )
            ModuleData = ImportLib.import_module(ModuleName)
            self.assertFalse(
                tuple(NameText for NameText in PublicNames if not hasattr(ModuleData, NameText))
            )
            if OpsName == "StreamPrograms":
                OutputPairs = tuple(
                    (StreamName, ModuleData.EncodeProgram(StreamName))
                    for StreamName in StreamNames
                )
            elif OpsName == "AnnotationOps":
                OutputPairs = (
                    (StreamNames[0], ModuleData.EncodeTwoViewAnnotationManager()),
                )
            else:
                OutputPairs = ((StreamNames[0], ModuleData.EncodeProgram()),)
            ActualStats = tuple(
                (
                    StreamName,
                    len(OutputData),
                    HashLib.sha256(OutputData).hexdigest(),
                )
                for StreamName, OutputData in OutputPairs
            )
            self.assertEqual(ActualStats, ByteStats)

    # executable check proves catalogs registries facades hashes and bytes agree together
    def TestGeneratorCheck(self) -> None:
        CheckResult = Subprocess.run(
            [sys.executable, str(KGeneratorPath), "--check"],
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
