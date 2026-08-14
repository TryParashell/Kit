# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path as FilePath
import shutil as ShutilLib
import subprocess as ProcessLib

from tests.convert.runtime.RuntimeRules import KRootPath


# isolated wheel checks need one reproducible offline build artifact
def BuildWheel(TmpPath: FilePath) -> FilePath:
    UvPath = ShutilLib.which("uv")
    assert UvPath is not None
    WheelFolder = TmpPath / "wheel"
    BuildResult = ProcessLib.run(
        (
            UvPath,
            "build",
            "--wheel",
            "--offline",
            "--no-progress",
            "--out-dir",
            str(WheelFolder),
        ),
        cwd=KRootPath,
        check=True,
        capture_output=True,
        text=True,
    )
    WheelPaths = tuple(WheelFolder.glob("*.whl"))
    assert BuildResult.returncode == 0
    assert len(WheelPaths) == 1
    return WheelPaths[0]
