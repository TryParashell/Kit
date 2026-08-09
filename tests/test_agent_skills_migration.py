# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

"""Regression coverage for the Kiro-to-Agent-Skills migration."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run_migration(repository: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "tools/migrate_kiro_steering.py", *args],
        cwd=repository,
        capture_output=True,
        text=True,
        check=False,
    )


def test_kiro_steering_is_mirrored_as_agent_skills() -> None:
    """The checked-in Agent Skills copy must stay synchronized with Kiro steering."""

    result = run_migration(ROOT, "--check")

    assert result.returncode == 0, result.stdout + result.stderr


def test_migration_removes_and_detects_stale_generated_skills(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    shutil.copytree(ROOT / "tools", repository / "tools")
    shutil.copytree(ROOT / ".kiro" / "steering", repository / ".kiro" / "steering")
    shutil.copytree(ROOT / ".agents" / "skills", repository / ".agents" / "skills")

    stale_skill = repository / ".agents" / "skills" / "obsolete-rule" / "SKILL.md"
    stale_skill.parent.mkdir()
    stale_skill.write_text("obsolete\n", encoding="utf-8")

    check_result = run_migration(repository, "--check")
    assert check_result.returncode == 1
    assert (
        "unexpected generated skill: .agents/skills/obsolete-rule"
        in check_result.stderr
    )

    write_result = run_migration(repository, "--write")
    assert write_result.returncode == 0, write_result.stdout + write_result.stderr
    assert not stale_skill.parent.exists()

    final_check_result = run_migration(repository, "--check")
    assert final_check_result.returncode == 0, (
        final_check_result.stdout + final_check_result.stderr
    )
