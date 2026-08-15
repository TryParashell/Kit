# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path as FilePath
import subprocess as ProcessLib
import sys as SystemLib

from tests.convert.runtime.IsolatedRuntime import KIsolatedRuntime
from tests.convert.runtime.RuntimeRules import KRootPath


# isolated execution proves the built wheel cannot reach external runtime hooks
def RunIsolated(
    TmpPath: FilePath, InstallRoot: FilePath
) -> ProcessLib.CompletedProcess[str]:
    OutputFolder = TmpPath / "runtime"
    OutputFolder.mkdir()
    return ProcessLib.run(
        (
            SystemLib.executable,
            "-I",
            "-S",
            "-c",
            KIsolatedRuntime,
            str(InstallRoot),
            str(KRootPath),
            str(OutputFolder),
        ),
        cwd=TmpPath,
        check=False,
        capture_output=True,
        text=True,
    )
