# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations as Annotations

from pathlib import Path as PathInfo

import pytest as Pytest

import convert.Security.ProgramBoundary as ProgramBoundary
from convert.Security.PathBoundary import ResolveWithin, UnsafePath


# valid nested files prove normalization preserves intended local access
def TestNestedPath(TmpPath: PathInfo) -> None:
    InputPath = TmpPath / "Input.bin"
    InputPath.write_bytes(b"safe")
    assert ResolveWithin(InputPath, TmpPath, True) == InputPath.resolve()


# parent traversal must fail before any filesystem sink receives the path
def TestBlocksEscape(TmpPath: PathInfo) -> None:
    OutsidePath = TmpPath.parent / "Outside.bin"
    with Pytest.raises(UnsafePath):
        ResolveWithin(OutsidePath, TmpPath)


# executable validation proves modeled command sanitization has a concrete allowlist
def TestFreecadPath(TmpPath: PathInfo, MonkeyPatch: Pytest.MonkeyPatch) -> None:
    ProgramPath = TmpPath / "FreeCADCmd.exe"
    ProgramPath.write_bytes(b"program")
    MonkeyPatch.setenv("KIT_FREECAD_ORACLE", str(ProgramPath))
    MonkeyPatch.setattr(ProgramBoundary, "KFreecadRoots", (TmpPath,))
    assert ProgramBoundary.GetFreecadPath() == ProgramPath.resolve()


# executable validation rejects allowed looking paths with the wrong program identity
def TestBlocksProgram(TmpPath: PathInfo, MonkeyPatch: Pytest.MonkeyPatch) -> None:
    ProgramPath = TmpPath / "OtherProgram.exe"
    ProgramPath.write_bytes(b"program")
    MonkeyPatch.setenv("KIT_FREECAD_ORACLE", str(ProgramPath))
    MonkeyPatch.setattr(ProgramBoundary, "KFreecadRoots", (TmpPath,))
    with Pytest.raises(UnsafePath):
        ProgramBoundary.GetFreecadPath()
