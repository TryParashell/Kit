# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

import subprocess as Subprocess
from pathlib import Path as FilePath


# isolated repositories let git boundary tests exercise real indexes trees and revisions
class RepoFixture:

    # every fixture needs deterministic authorship before it can create comparable revisions
    def __init__(self, RootPath: FilePath) -> None:
        self.RootPath = RootPath
        self.RunGit("init", "--quiet")
        self.RunGit("config", "user.name", "Policy Tests")
        self.RunGit("config", "user.email", "policy@example.invalid")

    # one checked process helper turns setup failures into immediately useful test failures
    def RunGit(self, *ArgItems: str) -> str:
        RunResult = Subprocess.run(
            ["git", "-C", str(self.RootPath), *ArgItems],
            capture_output=True,
            text=True,
            check=False,
        )
        if RunResult.returncode != 0:
            raise AssertionError(RunResult.stdout + RunResult.stderr)
        return RunResult.stdout.strip()

    # controlled fixture writes make index contents independent from the surrounding worktree
    def WriteFile(self, RepoPath: str, ContentText: str = "sample\n") -> None:
        TargetPath = self.RootPath / RepoPath
        TargetPath.parent.mkdir(parents=True, exist_ok=True)
        TargetPath.write_text(ContentText, encoding="utf-8")

    # git performs fixture moves so rename detection observes the same index metadata as production
    def MoveFile(self, OldPath: str, NewPath: str) -> None:
        self.RunGit("mv", OldPath, NewPath)

    # focused commits expose stable refs for changed destination and head tree assertions
    def CommitAll(self, MsgText: str) -> str:
        self.RunGit("add", "--all")
        self.RunGit("commit", "--quiet", "-m", MsgText)
        return self.RunGit("rev-parse", "HEAD")
