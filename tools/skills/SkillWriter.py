# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

import shutil as Shutil

from tools.skills.Descriptions import KDescriptions
from tools.skills.SkillPaths import GetStaleDirs, GetTargetPath
from tools.skills.SkillRender import RenderSkill


# single write path keeps stale cleanup and fresh output synchronized
def WriteSkills() -> None:
    for StalePath in GetStaleDirs():
        Shutil.rmtree(StalePath)
    for SkillName in sorted(KDescriptions):
        TargetFile = GetTargetPath(SkillName)
        TargetFile.parent.mkdir(parents=True, exist_ok=True)
        TargetFile.write_text(RenderSkill(SkillName), encoding="utf-8", newline="\n")
