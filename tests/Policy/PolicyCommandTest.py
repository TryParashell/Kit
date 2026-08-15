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


# process level coverage protects exit codes summaries and revision flag validation for automation
class TestCommand(UnitTest.TestCase):

    # full and changed invocations must distinguish legacy paths new destinations and invalid arguments
    def CheckExitCodes(self) -> None:
        with Tempfile.TemporaryDirectory() as TmpPath:
            RootPath = FilePath(TmpPath)
            FixtureInfo = RepoFixture(RootPath)
            FixtureInfo.WriteFile("bad_name.py")
            BaseRef = FixtureInfo.CommitAll("base")
            FixtureInfo.WriteFile("Bravo.py")
            HeadRef = FixtureInfo.CommitAll("head")
            WorkPath = FilePath(__file__).resolve().parents[2]
            BaseArgs = [
                System.executable,
                "-m",
                "tools.Policy.CheckPaths",
                "--root",
                str(RootPath),
            ]
            FullResult = Subprocess.run(
                BaseArgs,
                cwd=WorkPath,
                capture_output=True,
                text=True,
                check=False,
            )
            ChangeResult = Subprocess.run(
                [*BaseArgs, "--base", BaseRef, "--head", HeadRef],
                cwd=WorkPath,
                capture_output=True,
                text=True,
                check=False,
            )
            InvalidResult = Subprocess.run(
                [*BaseArgs, "--base", BaseRef],
                cwd=WorkPath,
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(FullResult.returncode, 1)
        self.assertIn("bad_name.py", FullResult.stdout)
        self.assertEqual(
            ChangeResult.returncode,
            0,
            ChangeResult.stdout + ChangeResult.stderr,
        )
        self.assertEqual(InvalidResult.returncode, 2)
