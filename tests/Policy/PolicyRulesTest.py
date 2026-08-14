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
    def CheckExamples(CaseSelf) -> None:
        CaseSelf.assertTrue(IsBroadSkip("examples/vendor/part_2.SLDPRT"))
        CaseSelf.assertFalse(IsBroadSkip("example/vendor/part_2.SLDPRT"))
        CaseSelf.assertFalse(IsBroadSkip("examples.md"))

    # standards retain fixed filenames because their consumers cannot discover renamed alternatives
    def CheckStandards(CaseSelf) -> None:
        AllowedPaths = (
            ".gitattributes",
            ".github/dependabot.yml",
            "Source/__init__.py",
            "tests/Feature/conftest.py",
            ".agents/skills/naming/SKILL.md",
        )
        for RepoPath in AllowedPaths:
            with CaseSelf.subTest(RepoPath=RepoPath):
                CaseSelf.assertTrue(IsNameExempt(RepoPath))
        CaseSelf.assertFalse(IsNameExempt("Source/settings.json"))
        CaseSelf.assertFalse(IsNameExempt("Source/SKILL.md"))

    # bundled skills and native identities stay loadable without exempting adjacent project metadata
    def CheckBundles(CaseSelf) -> None:
        CaseSelf.assertTrue(IsNameExempt(".kiro/skills/vendor/random_2.json"))
        CaseSelf.assertTrue(IsNameExempt("re/binaries/sldmfcu.dll"))
        CaseSelf.assertFalse(IsNameExempt("re/binaries/manifest.json"))
        CaseSelf.assertFalse(IsNameExempt("Source/sldmfcu.dll"))

    # the exact ascii predicate rejects separators digits lowercase starts and empty stems
    def CheckStemRule(CaseSelf) -> None:
        for StemText in ("Alpha", "HTTPServer", "ValueName"):
            CaseSelf.assertTrue(IsValidStem(StemText))
        for StemText in ("alpha", "Alpha_Name", "Alpha2", ""):
            CaseSelf.assertFalse(IsValidStem(StemText))
