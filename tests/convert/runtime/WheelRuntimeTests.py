# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path as FilePath

from tests.convert.runtime.WheelBuild import BuildWheel
from tests.convert.runtime.WheelExecute import RunIsolated
from tests.convert.runtime.WheelInspect import ExtractWheel


# built distribution behavior must match source behavior with every external hook blocked
def CheckWheel(TmpPath: FilePath) -> None:
    WheelPath = BuildWheel(TmpPath)
    InstallRoot = TmpPath / "site"
    ExtractWheel(WheelPath, InstallRoot)
    RuntimeResult = RunIsolated(TmpPath, InstallRoot)
    assert RuntimeResult.returncode == 0, RuntimeResult.stderr
