# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from tools.skills.Descriptions import KDescriptions
from tools.skills.SkillPaths import KRootPath, GetStaleDirs, GetTargetPath
from tools.skills.SkillRender import RenderSkill
from tools.skills.SkillSpecs import ValidateSpecs


# shared comparison logic exposes every source and generated tree mismatch together
def CheckSkills() -> list[str]:
    ErrorList = ValidateSpecs()
    for StalePath in GetStaleDirs():
        LocationText = StalePath.relative_to(KRootPath).as_posix()
        ErrorList.append(f"unexpected generated skill: {LocationText}")
    for SkillName in sorted(KDescriptions):
        TargetFile = GetTargetPath(SkillName)
        LocationText = TargetFile.relative_to(KRootPath).as_posix()
        if not TargetFile.is_file():
            ErrorList.append(f"missing generated skill: {LocationText}")
            continue
        if TargetFile.read_text(encoding="utf-8") != RenderSkill(SkillName):
            ErrorList.append(f"out-of-date generated skill: {LocationText}")
    return ErrorList
