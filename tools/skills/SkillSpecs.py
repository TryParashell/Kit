# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

import re as Regex

from tools.skills.Descriptions import KDescriptions
from tools.skills.SkillNames import GetSourceStem
from tools.skills.SkillPaths import KSourceDir


# inventory validation prevents generation from silently dropping or inventing steering rules
def ValidateSpecs() -> list[str]:
    ErrorList: list[str] = []
    SourceNames = {SourceFile.stem for SourceFile in KSourceDir.glob("*.md")}
    SkillNames = set(KDescriptions)
    ExpectedNames = {GetSourceStem(SkillName) for SkillName in SkillNames}
    MissingSkills = SourceNames - ExpectedNames
    if MissingSkills:
        ErrorList.append(
            f"source files without skills: {', '.join(sorted(MissingSkills))}"
        )
    MissingSources = ExpectedNames - SourceNames
    if MissingSources:
        ErrorList.append(
            f"skills without source files: {', '.join(sorted(MissingSources))}"
        )
    for SkillName, DescriptionText in KDescriptions.items():
        if not Regex.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", SkillName):
            ErrorList.append(f"invalid Agent Skills name: {SkillName}")
        if not DescriptionText or len(DescriptionText) > 1024:
            ErrorList.append(f"invalid Agent Skills description length: {SkillName}")
    return ErrorList
