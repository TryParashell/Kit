# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

import unittest as UnitTest

from tools.Policy.IsBroadSkip import IsBroadSkip
from tools.Policy.IsNameExempt import IsNameExempt
from tools.Policy.IsValidStem import IsValidStem


# exemption tests keep required identities narrow enough that neighboring files remain governed
class TestPathRules(UnitTest.TestCase):

    # broad exclusion belongs only to example inputs because project code must stay enforceable
    def CheckExamples(self) -> None:
        self.assertTrue(IsBroadSkip("examples/vendor/part_2.SLDPRT"))
        self.assertFalse(IsBroadSkip("example/vendor/part_2.SLDPRT"))
        self.assertFalse(IsBroadSkip("examples.md"))

    # standards retain fixed filenames because their consumers cannot discover renamed alternatives
    def CheckStandards(self) -> None:
        AllowedPaths = (
            ".gitattributes",
            ".github/CodeQL/extensions/KitPython/codeql-pack.yml",
            ".github/dependabot.yml",
            "Source/__init__.py",
            "tests/Feature/conftest.py",
            ".agents/skills/naming/SKILL.md",
        )
        for RepoPath in AllowedPaths:
            with self.subTest(RepoPath=RepoPath):
                self.assertTrue(IsNameExempt(RepoPath))
        self.assertFalse(IsNameExempt("Source/settings.json"))
        self.assertFalse(IsNameExempt("Source/SKILL.md"))
        self.assertFalse(
            IsNameExempt(".github/CodeQL/extensions/OtherPython/codeql-pack.yml")
        )
        self.assertFalse(
            IsNameExempt(".github/CodeQL/extensions/KitPython/codeql-config.yml")
        )

    # bundled skills and native identities stay loadable without exempting adjacent project metadata
    def CheckBundles(self) -> None:
        self.assertTrue(IsNameExempt(".kiro/skills/vendor/random_2.json"))
        self.assertTrue(IsNameExempt("re/binaries/sldmfcu.dll"))
        self.assertFalse(IsNameExempt("re/binaries/manifest.json"))
        self.assertFalse(IsNameExempt("Source/sldmfcu.dll"))

    # the exact ascii predicate rejects separators digits lowercase starts and empty stems
    def CheckStemRule(self) -> None:
        for StemText in ("Alpha", "HTTPServer", "ValueName"):
            self.assertTrue(IsValidStem(StemText))
        for StemText in ("alpha", "Alpha_Name", "Alpha2", ""):
            self.assertFalse(IsValidStem(StemText))
