# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from operator import attrgetter as AttrGetter
from pathlib import Path as FilePath

from tools.descriptions import KDescriptions


# repository location anchors generation so copied tools resolve their local assets
KRootPath = FilePath(__file__).resolve().parents[1]

# steering sources share one root so every migration operation sees identical inputs
KSourceDir = KRootPath / ".kiro" / "steering"

# generated skills share one root so checking and writing cannot diverge
KTargetDir = KRootPath / ".agents" / "skills"


# source lookup stays centralized so rendering and validation cannot disagree on paths
def GetSourcePath(SkillName: str) -> FilePath:
    return KSourceDir / f"{SkillName}.md"


# target lookup stays centralized so checking and writing cannot disagree on paths
def GetTargetPath(SkillName: str) -> FilePath:
    return KTargetDir / SkillName / "SKILL.md"


# unexpected directory discovery protects generated output from silently retaining removed rules
def GetStaleDirs() -> list[FilePath]:
    if not KTargetDir.is_dir():
        return []
    ExpectedNames = set(KDescriptions)
    StalePaths = (
        FolderPath
        for FolderPath in KTargetDir.iterdir()
        if FolderPath.is_dir() and FolderPath.name not in ExpectedNames
    )
    return sorted(StalePaths, key=AttrGetter("name"))
