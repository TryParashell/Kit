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


# full scans use the index so untracked build products never affect repository policy
def LoadTracked(RootPath: FilePath) -> tuple[str, ...]:
    OutputData = RunGitCommand(
        RootPath,
        ["ls-files", "--cached", "--full-name", "-z", "--", ":(top)"],
    )
    return ParseGitPaths(OutputData)
