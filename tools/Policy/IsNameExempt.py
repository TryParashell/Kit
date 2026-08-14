# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from pathlib import PurePosixPath as PosixPath

from tools.Policy.PolicyRules import KBinarySuffixes
from tools.Policy.PolicyRules import KStandardNames
from tools.Policy.PolicyRules import KToolPathSet


# narrow identity checks protect required tool and binary names without hiding neighboring files
def IsNameExempt(RepoPath: str) -> bool:
    PathInfo = PosixPath(RepoPath)
    PathParts = PathInfo.parts
    if RepoPath in KToolPathSet or PathInfo.name in KStandardNames:
        return True
    if (
        len(PathParts) == 4
        and PathParts[:2] == (".agents", "skills")
        and PathInfo.name == "SKILL.md"
    ):
        return True
    if len(PathParts) >= 3 and PathParts[:2] == (".kiro", "skills"):
        return True
    return (
        len(PathParts) >= 3
        and PathParts[:2] == ("re", "binaries")
        and PathInfo.suffix.lower() in KBinarySuffixes
    )
