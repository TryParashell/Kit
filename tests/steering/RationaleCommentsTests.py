# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

import subprocess as Subprocess
import sys as System
import tempfile as Tempfile
import unittest as UnitTest
from pathlib import Path as FilePath

from tests.Policy.RepoFixture import RepoFixture

# fixture sources must carry one compliant rationale so clean cases prove real coverage
KCleanSource = """\
# doubling lives here because several fixture assertions reuse the same math
def Double(Value):
    return Value * 2
"""

# fixture sources omit the mandatory rationale so violation detection gets exercised
KBadSource = """\
def Broken():
    return 1
"""


# subprocess execution exercises the real entry point including argument handling
def RunModule(
    RootPath: FilePath,
    BaseRef: str | None = None,
    HeadRef: str | None = None,
) -> Subprocess.CompletedProcess[str]:
    WorkPath = FilePath(__file__).resolve().parents[2]
    ArgItems = [
        System.executable,
        "-m",
        "tools.steering.CheckRationaleComments",
        "--root",
        str(RootPath),
    ]
    if BaseRef is not None:
        ArgItems.extend(["--base", BaseRef])
    if HeadRef is not None:
        ArgItems.extend(["--head", HeadRef])
    return Subprocess.run(
        ArgItems,
        cwd=WorkPath,
        capture_output=True,
        text=True,
        check=False,
    )


# diff coverage proves the gate fails only for violations a reviewed change deepens
class TestDiffGate(UnitTest.TestCase):

    # diff gates must fail only for violations the reviewed change introduces or deepens
    def CheckDiffGate(self) -> None:
        with Tempfile.TemporaryDirectory() as TmpPath:
            RootPath = FilePath(TmpPath)
            FixtureInfo = RepoFixture(RootPath)
            FixtureInfo.WriteFile("Alpha.py", KCleanSource)
            FixtureInfo.WriteFile("Legacy.py", KBadSource)
            BaseRef = FixtureInfo.CommitAll("base")
            FixtureInfo.WriteFile("Bravo.py", KBadSource)
            FixtureInfo.WriteFile("re/Nested.py", KBadSource)
            HeadRef = FixtureInfo.CommitAll("head")
            ResultInfo = RunModule(RootPath, BaseRef, HeadRef)
        self.assertEqual(ResultInfo.returncode, 1, ResultInfo.stderr)
        self.assertIn("Bravo.py", ResultInfo.stdout)
        self.assertNotIn("Legacy.py", ResultInfo.stdout)
        self.assertNotIn("Nested.py", ResultInfo.stdout)

    # deleting one mandated rationale must fail the gate even without touching code
    def CheckCommentLoss(self) -> None:
        with Tempfile.TemporaryDirectory() as TmpPath:
            RootPath = FilePath(TmpPath)
            FixtureInfo = RepoFixture(RootPath)
            FixtureInfo.WriteFile("Alpha.py", KCleanSource)
            BaseRef = FixtureInfo.CommitAll("base")
            FixtureInfo.WriteFile("Alpha.py", KBadSource)
            HeadRef = FixtureInfo.CommitAll("head")
            ResultInfo = RunModule(RootPath, BaseRef, HeadRef)
        self.assertEqual(ResultInfo.returncode, 1, ResultInfo.stderr)
        self.assertIn("Alpha.py", ResultInfo.stdout)


# scope coverage proves excluded trees and non python edits never trigger failures
class TestScopeGate(UnitTest.TestCase):

    # full tree mode proves tracked exclusions keep vendored debt out of scope
    def CheckFullPass(self) -> None:
        with Tempfile.TemporaryDirectory() as TmpPath:
            RootPath = FilePath(TmpPath)
            FixtureInfo = RepoFixture(RootPath)
            FixtureInfo.WriteFile("Alpha.py", KCleanSource)
            FixtureInfo.WriteFile("re/Nested.py", KBadSource)
            _ = FixtureInfo.CommitAll("base")
            ResultInfo = RunModule(RootPath)
        self.assertEqual(ResultInfo.returncode, 0, ResultInfo.stdout)
        self.assertIn("passed", ResultInfo.stdout)
        self.assertNotIn("Nested", ResultInfo.stdout)

    # non python edits must stay out of scope so documentation work never triggers gates
    def CheckTxtOnly(self) -> None:
        with Tempfile.TemporaryDirectory() as TmpPath:
            RootPath = FilePath(TmpPath)
            FixtureInfo = RepoFixture(RootPath)
            FixtureInfo.WriteFile("Alpha.py", KCleanSource)
            BaseRef = FixtureInfo.CommitAll("base")
            FixtureInfo.WriteFile("Note.txt", "notes\n")
            HeadRef = FixtureInfo.CommitAll("head")
            ResultInfo = RunModule(RootPath, BaseRef, HeadRef)
        self.assertEqual(ResultInfo.returncode, 0, ResultInfo.stdout)


# argument coverage proves partial revision flags fail fast before any comparison
class TestArgGate(UnitTest.TestCase):

    # partial revision flags must fail fast so automation never compares half ranges
    def CheckBadArgs(self) -> None:
        with Tempfile.TemporaryDirectory() as TmpPath:
            RootPath = FilePath(TmpPath)
            FixtureInfo = RepoFixture(RootPath)
            FixtureInfo.WriteFile("Alpha.py", KCleanSource)
            BaseRef = FixtureInfo.CommitAll("base")
            ResultInfo = RunModule(RootPath, BaseRef)
        self.assertEqual(ResultInfo.returncode, 2)
