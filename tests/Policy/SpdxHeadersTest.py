# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from importlib.util import module_from_spec as BuildModule
from importlib.util import spec_from_file_location as BuildSpec
from pathlib import Path as FilePath
import sys as System
import unittest as UnitTest
from types import ModuleType as ModuleKind
from typing import Callable as CallType
from typing import Protocol
from typing import cast as TypeCast


# dynamic guard loading needs concrete signatures so policy tests retain strict call validation
class GuardContract(Protocol):
    CheckFile: CallType[[FilePath, list[str], FilePath], tuple[bool, str]]
    CheckWorktree: CallType[[FilePath, str], tuple[FilePath | None, str]]
    GetDiffFiles: CallType[[str, str, FilePath], list[str]]
    IsCommit: CallType[[str, FilePath], bool]
    IsPathExempt: CallType[[str], bool]
    LoadCanon: CallType[[], list[str]]
    ParseDiff: CallType[[bytes], list[str]]
    RenderLines: CallType[[list[str], str], list[str]]
    RepairHeadMut: CallType[[FilePath, list[str], FilePath], tuple[bool, str]]
    ResolvePath: CallType[[FilePath, str], FilePath | None]
    StatLib: ModuleKind


# workflow code needs direct loading because its host directory is not a python package
def LoadGuard() -> GuardContract:
    GuardPath = (
        FilePath(__file__).parents[2] / ".github" / "scripts" / "VerifySpdxHeaders.py"
    )
    GuardSpec = BuildSpec("SpdxGuardTest", GuardPath)
    if GuardSpec is None or GuardSpec.loader is None:
        raise RuntimeError("spdx guard script cannot be loaded")
    GuardModule = BuildModule(GuardSpec)
    OriginalPaths = System.path.copy()
    try:
        System.path.insert(0, str(GuardPath.parent))
        GuardSpec.loader.exec_module(GuardModule)
        return TypeCast(GuardContract, GuardModule)
    finally:
        System.path[:] = OriginalPaths


# exemptions need regression coverage so consumer sensitive scope cannot expand silently
class TestSpdxGuard(UnitTest.TestCase):

    # raw artifacts need exact exemptions because their record grammar has no comments
    def TestRawExempt(self) -> None:
        IsPathExempt = LoadGuard().IsPathExempt
        RawPaths = (
            "re/data/Serialization/SldmfcuSigtableRefs.txt",
            "re/data/vocabulary/Flagmap.txt",
            "re/data/vocabulary/Vocabulary.txt",
        )
        for RelPath in RawPaths:
            self.assertTrue(IsPathExempt(RelPath))

    # neighboring documentation must remain governed despite the narrow data exemptions
    def TestDocsInScope(self) -> None:
        IsPathExempt = LoadGuard().IsPathExempt
        GovernedPaths = (
            "re/Methodology.md",
            "re/data/vocabulary/README.md",
            "re/data/vocabulary/VocabularyNotes.txt",
        )
        for RelPath in GovernedPaths:
            self.assertFalse(IsPathExempt(RelPath))

    # newly added guard tests need direct coverage before git revisions can include them
    def TestOwnHeader(self) -> None:
        GuardModule = LoadGuard()
        IsValid, ReasonText = GuardModule.CheckFile(
            FilePath(__file__),
            GuardModule.LoadCanon(),
            FilePath(__file__).parents[2],
        )
        self.assertTrue(IsValid, ReasonText)
