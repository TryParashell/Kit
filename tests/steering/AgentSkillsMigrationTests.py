# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

import os as OsEnv
import shutil as Shutil
import subprocess as Subprocess
import sys as System
import textwrap as Textwrap
from pathlib import Path as FilePath

import pytest as Pytest

from tools.skills.SkillPaths import GetSourcePath


# command tests need repository context because migration inputs are checked in assets
KRootPath = FilePath(__file__).resolve().parents[2]


# subprocess isolation matters because migration behavior includes command status and diagnostics
def RunMigration(
    RepositoryPath: FilePath, *ArgValues: str
) -> Subprocess.CompletedProcess[str]:
    return Subprocess.run(
        [System.executable, "tools/skills/MigrateKiroSteering.py", *ArgValues],
        cwd=RepositoryPath,
        capture_output=True,
        text=True,
        check=False,
    )


# synchronized copies prevent agent runtimes from receiving stale steering guidance
def CheckMirrored() -> None:
    ResultInfo = RunMigration(KRootPath, "--check")

    assert ResultInfo.returncode == 0, ResultInfo.stdout + ResultInfo.stderr


# source lookup coverage keeps pascal sources aligned with kebab case skill identities
def CheckPascalPath() -> None:
    SourcePath = GetSourcePath("split-large-definitions")

    assert SourcePath.name == "SplitLargeDefinitions.md"
    assert SourcePath.is_file()


# isolated repositories prove stale generated skills are both detected and removed
def CheckStale(TmpPath: FilePath) -> None:
    RepositoryPath = TmpPath / "repository"
    Shutil.copytree(KRootPath / "tools", RepositoryPath / "tools")
    Shutil.copytree(
        KRootPath / ".kiro" / "steering", RepositoryPath / ".kiro" / "steering"
    )
    Shutil.copytree(
        KRootPath / ".agents" / "skills", RepositoryPath / ".agents" / "skills"
    )

    StalePath = RepositoryPath / ".agents" / "skills" / "obsolete-rule" / "SKILL.md"
    StalePath.parent.mkdir()
    StalePath.write_text("obsolete\n", encoding="utf-8")

    CheckResult = RunMigration(RepositoryPath, "--check")
    assert CheckResult.returncode == 1
    assert (
        "unexpected generated skill: .agents/skills/obsolete-rule" in CheckResult.stderr
    )

    WriteResult = RunMigration(RepositoryPath, "--write")
    assert WriteResult.returncode == 0, WriteResult.stdout + WriteResult.stderr
    assert not StalePath.parent.exists()

    FinalResult = RunMigration(RepositoryPath, "--check")
    assert FinalResult.returncode == 0, FinalResult.stdout + FinalResult.stderr


# rendered bytes need direct coverage because structural refactors must not rewrite generated guidance
def CheckByteOutput(TmpPath: FilePath) -> None:
    RepositoryPath = TmpPath / "repository"
    Shutil.copytree(KRootPath / "tools", RepositoryPath / "tools")
    Shutil.copytree(
        KRootPath / ".kiro" / "steering", RepositoryPath / ".kiro" / "steering"
    )
    Shutil.copytree(
        KRootPath / ".agents" / "skills", RepositoryPath / ".agents" / "skills"
    )
    BeforeData = {
        SkillPath.relative_to(RepositoryPath): SkillPath.read_bytes()
        for SkillPath in (RepositoryPath / ".agents" / "skills").glob("*/SKILL.md")
    }

    WriteResult = RunMigration(RepositoryPath, "--write")
    assert WriteResult.returncode == 0, WriteResult.stdout + WriteResult.stderr
    AfterData = {
        SkillPath.relative_to(RepositoryPath): SkillPath.read_bytes()
        for SkillPath in (RepositoryPath / ".agents" / "skills").glob("*/SKILL.md")
    }
    assert AfterData == BeforeData


# subprocess collection proves legacy and compliant test names coexist without source aliases
def CheckCollect(TmpPath: FilePath) -> None:
    TestPath = TmpPath / "test_mixed_names.py"
    TestPath.write_text(
        "def test_legacy_name():\n"
        "    assert True\n\n"
        "def CheckModern():\n"
        "    assert True\n",
        encoding="utf-8",
    )
    EnvValues = dict(OsEnv.environ)
    EnvValues.pop("PYTEST_ADDOPTS", None)
    CommandArgs = [
        System.executable,
        "-m",
        "pytest",
        "--collect-only",
        "-q",
        "--rootdir",
        str(KRootPath),
        "-c",
        str(KRootPath / "pyproject.toml"),
        str(TestPath),
    ]
    ResultInfo = Subprocess.run(
        CommandArgs,
        cwd=KRootPath,
        capture_output=True,
        text=True,
        check=False,
        env=EnvValues,
    )

    assert ResultInfo.returncode == 0, ResultInfo.stdout + ResultInfo.stderr
    assert "::test_legacy_name" in ResultInfo.stdout
    assert "::CheckModern" in ResultInfo.stdout


# subprocess execution proves compliant aliases share builtin values and teardown behavior
def CheckAliases(
    TmpPath: FilePath,
    MonkeyPatch: Pytest.MonkeyPatch,
) -> None:
    ProbePath = KRootPath / "tests" / "test_fixture_aliases_probe.py"
    ProbePath.write_text(
        Textwrap.dedent(
            """
            def test_fixture_aliases(tmp_path, TmpPath, monkeypatch, MonkeyPatch):
                assert TmpPath is tmp_path
                assert MonkeyPatch is monkeypatch
            """
        ),
        encoding="utf-8",
    )
    MonkeyPatch.setenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
    try:
        ResultInfo = Subprocess.run(
            [System.executable, "-m", "pytest", "-q", str(ProbePath)],
            cwd=KRootPath,
            capture_output=True,
            text=True,
            check=False,
        )
    finally:
        ProbePath.unlink(missing_ok=True)

    assert ResultInfo.returncode == 0, ResultInfo.stdout + ResultInfo.stderr
    assert "1 passed" in ResultInfo.stdout
