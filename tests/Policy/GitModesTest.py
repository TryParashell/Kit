# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

import tempfile as Tempfile
import unittest as UnitTest
from pathlib import Path as FilePath

from tests.Policy.RepoFixture import RepoFixture
from tools.Policy.CheckPathPolicy import CheckPathPolicy
from tools.Policy.LoadChanged import LoadChanged
from tools.Policy.LoadTracked import LoadTracked
from tools.Policy.LoadTree import LoadTree


# real git coverage ensures index tree and rename behavior match command line expectations
class TestGitModes(UnitTest.TestCase):

    # rename detection must expose only the destination while full scans retain the complete head tree
    def CheckGitModes(CaseSelf) -> None:
        with Tempfile.TemporaryDirectory() as TmpPath:
            RootPath = FilePath(TmpPath)
            FixtureInfo = RepoFixture(RootPath)
            FixtureInfo.WriteFile("Alpha.py")
            BaseRef = FixtureInfo.CommitAll("base")
            FixtureInfo.MoveFile("Alpha.py", "bad_name.py")
            FixtureInfo.WriteFile("Bravo.py")
            HeadRef = FixtureInfo.CommitAll("head")
            NestedPath = RootPath / "Nested"
            NestedPath.mkdir()
            TrackedPaths = LoadTracked(NestedPath)
            TreePaths = LoadTree(NestedPath, HeadRef)
            ChangedPaths = LoadChanged(NestedPath, BaseRef, HeadRef)
        CaseSelf.assertEqual(set(TrackedPaths), {"Bravo.py", "bad_name.py"})
        CaseSelf.assertEqual(set(TreePaths), {"Bravo.py", "bad_name.py"})
        CaseSelf.assertEqual(set(ChangedPaths), {"Bravo.py", "bad_name.py"})
        FindingList = CheckPathPolicy(TreePaths, ChangedPaths)
        CaseSelf.assertEqual(
            [FindingInfo.RepoPath for FindingInfo in FindingList],
            ["bad_name.py"],
        )
