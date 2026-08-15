# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from collections.abc import Iterable
from pathlib import PurePosixPath as PosixPath

from tools.Policy.IsBroadSkip import IsBroadSkip
from tools.Policy.PathFinding import PathFinding
from tools.Policy.PolicyRules import KMaxDirectFiles


# direct file counts stop touched directories from becoming unreviewable flat dumping grounds
def CheckDirCounts(
    TrackedPaths: Iterable[str],
    TargetPaths: Iterable[str],
) -> list[PathFinding]:
    TrackedSet = set(TrackedPaths)
    TargetSet = set(TargetPaths) & TrackedSet
    FolderCounts: dict[str, int] = {}
    for RepoPath in TrackedSet:
        if IsBroadSkip(RepoPath):
            continue
        FolderText = str(PosixPath(RepoPath).parent)
        FolderCounts[FolderText] = FolderCounts.get(FolderText, 0) + 1
    TargetFolders = {
        str(PosixPath(RepoPath).parent)
        for RepoPath in TargetSet
        if not IsBroadSkip(RepoPath)
    }
    FindingList: list[PathFinding] = []
    for FolderText in sorted(TargetFolders):
        CountValue = FolderCounts.get(FolderText, 0)
        if CountValue <= KMaxDirectFiles:
            continue
        MessageText = (
            f"directory contains {CountValue} direct tracked files but policy allows "
            f"at most {KMaxDirectFiles}; create focused subfolders"
        )
        FindingList.append(PathFinding(FolderText, "PTH002", MessageText))
    return FindingList
