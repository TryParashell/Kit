# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

import subprocess as Subprocess
from collections.abc import Sequence
from pathlib import Path as FilePath

from tools.Policy.GitFailure import GitFailure


# one byte preserving process boundary prevents path decoding before nul record parsing
def RunGitCommand(RootPath: FilePath, ArgItems: Sequence[str]) -> bytes:
    CommandArgs = ["git", "-C", str(RootPath), *ArgItems]
    try:
        RunResult = Subprocess.run(
            CommandArgs,
            stdout=Subprocess.PIPE,
            stderr=Subprocess.PIPE,
            check=False,
        )
    except OSError as ErrorInfo:
        raise GitFailure(f"unable to run git in {RootPath}: {ErrorInfo}") from ErrorInfo
    if RunResult.returncode != 0:
        ErrorText = RunResult.stderr.decode(errors="replace").strip()
        CommandText = " ".join(ArgItems)
        raise GitFailure(
            f"git {CommandText} failed in {RootPath} with exit "
            f"{RunResult.returncode}: {ErrorText}"
        )
    return RunResult.stdout
