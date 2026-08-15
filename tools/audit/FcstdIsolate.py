# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

import json as JsonData
from pathlib import Path as FilePath
import subprocess as Subprocess
import sys as System
from typing import Any as AnyValue

from tools.audit.FcstdContext import KRepositoryRoot
from tools.audit.FcstdResult import MakeFailure

# bounded diagnostics keep failed workers useful without flooding recursive audit output
KErrorLimit = 1000

# worker timeout prevents malformed sources from blocking the remaining corpus indefinitely
KWorkerTimeout = 300


# worker invocation stays separate so timeout handling and result decoding remain focused
def RunProcess(
    SourcePath: FilePath, OutputRoot: FilePath, SourceIndex: int
) -> AnyValue:
    return Subprocess.run(
        (
            System.executable,
            str(KRepositoryRoot / "tools" / "AuditFcstdSolidworks.py"),
            "--worker-source",
            str(SourcePath),
            "--worker-output",
            str(OutputRoot),
            "--worker-index",
            str(SourceIndex),
        ),
        cwd=KRepositoryRoot,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        timeout=KWorkerTimeout,
    )


# subprocess isolation lets recursive audits survive malformed or memory intensive sources
def AuditIsolated(
    SourcePath: FilePath,
    OutputRoot: FilePath,
    SourceIndex: int,
) -> dict[str, AnyValue]:
    try:
        ProcessData = RunProcess(SourcePath, OutputRoot, SourceIndex)
    except Subprocess.TimeoutExpired as ErrorInfo:
        ErrorText = f"isolated worker timed out after {ErrorInfo.timeout} seconds"
        return MakeFailure(SourcePath, ErrorText)
    OutputLines = tuple(
        LineText.strip()
        for LineText in ProcessData.stdout.splitlines()
        if LineText.strip()
    )
    if ProcessData.returncode == 0 and OutputLines:
        try:
            ResultData = JsonData.loads(OutputLines[-1])
        except JsonData.JSONDecodeError:
            ResultData = None
        if isinstance(ResultData, dict):
            return ResultData
    ErrorText = ProcessData.stderr.strip() or ProcessData.stdout.strip()
    if len(ErrorText) > KErrorLimit:
        ErrorText = ErrorText[-KErrorLimit:]
    FailureText = f"isolated worker exited {ProcessData.returncode}"
    if ErrorText:
        FailureText += f": {ErrorText}"
    return MakeFailure(SourcePath, FailureText)
