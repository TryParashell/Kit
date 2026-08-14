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
import unittest as UnitTest


# workflow code needs direct loading because its host directory is not a python package
def LoadGuard() -> dict[str, object]:
    GuardPath = (
        FilePath(__file__).parents[2] / ".github" / "scripts" / "VerifySpdxHeaders.py"
    )
    return RunPath(str(GuardPath), run_name="SpdxGuardTest")


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
