# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from pathlib import Path as FilePath

from tools.Policy.ParseGitPaths import ParseGitPaths
from tools.Policy.RunGitCommand import RunGitCommand


# changed scans need the exact head tree so directory counts ignore checkout drift
def LoadTree(RootPath: FilePath, HeadRef: str) -> tuple[str, ...]:
    OutputData = RunGitCommand(
        RootPath,
        [
            "ls-tree",
            "-r",
            "-z",
            "--name-only",
            "--full-tree",
            "--end-of-options",
            HeadRef,
        ],
    )
    return ParseGitPaths(OutputData)
