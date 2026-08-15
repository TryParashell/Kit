# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations as Annotations

from pathlib import Path as FilePath
from runpy import run_path as RunPath
import sys as System
import unittest as UnitTest


# workflow code needs direct loading because its host directory is not a python package
def LoadGuard() -> dict[str, object]:
    GuardPath = (
        FilePath(__file__).parents[2] / ".github" / "scripts" / "VerifySpdxHeaders.py"
    )
    OriginalPaths = System.path.copy()
    try:
        System.path.insert(0, str(GuardPath.parent))
        return RunPath(str(GuardPath), run_name="SpdxGuardTest")
    finally:
        System.path[:] = OriginalPaths


# exemptions need regression coverage so consumer sensitive scope cannot expand silently
class TestSpdxGuard(UnitTest.TestCase):

    # raw artifacts need exact exemptions because their record grammar has no comments
    def TestRawExempt(SelfValue) -> None:
        IsPathExempt = LoadGuard()["IsPathExempt"]
        RawPaths = (
            "re/data/Serialization/SldmfcuSigtableRefs.txt",
            "re/data/vocabulary/Flagmap.txt",
            "re/data/vocabulary/Vocabulary.txt",
        )
        for RelPath in RawPaths:
            SelfValue.assertTrue(IsPathExempt(RelPath))

    # neighboring documentation must remain governed despite the narrow data exemptions
    def TestDocsInScope(SelfValue) -> None:
        IsPathExempt = LoadGuard()["IsPathExempt"]
        GovernedPaths = (
            "re/Methodology.md",
            "re/data/vocabulary/README.md",
            "re/data/vocabulary/VocabularyNotes.txt",
        )
        for RelPath in GovernedPaths:
            SelfValue.assertFalse(IsPathExempt(RelPath))

    # newly added guard tests need direct coverage before git revisions can include them
    def TestOwnHeader(SelfValue) -> None:
        GuardValues = LoadGuard()
        IsValid, ReasonText = GuardValues["CheckFile"](
            FilePath(__file__), GuardValues["LoadCanon"]()
        )
        SelfValue.assertTrue(IsValid, ReasonText)
