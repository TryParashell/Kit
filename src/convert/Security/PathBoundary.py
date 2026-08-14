# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations as Annotations

import os as OsLayer
from pathlib import Path as PathInfo
import tempfile as Tempfile


# unsafe filesystem selections need a distinct failure contract at trust boundaries
class UnsafePath(ValueError):
    __slots__ = ()


# normalized containment prevents traversal and symlink escapes before filesystem access
def ResolveWithin(
    PathValue: str | OsLayer.PathLike[str],
    RootValue: str | OsLayer.PathLike[str],
    RequireFile: bool = False,
) -> PathInfo:
    RootText = OsLayer.path.realpath(OsLayer.fspath(RootValue))
    CandidateText = OsLayer.path.realpath(OsLayer.fspath(PathValue))
    RootKey = OsLayer.path.normcase(RootText)
    CandidateKey = OsLayer.path.normcase(CandidateText)
    RootPrefix = RootKey.rstrip("\\/") + OsLayer.sep
    if CandidateKey != RootKey and not CandidateKey.startswith(RootPrefix):
        raise UnsafePath(f"path escapes trusted root {RootText!r}")
    ResultPath = PathInfo(CandidateText)
    if RequireFile and not ResultPath.is_file():
        raise FileNotFoundError(ResultPath)
    return ResultPath


# local paths need one containment primitive before applying file type rules
def ResolveLocal(PathValue: str | OsLayer.PathLike[str]) -> PathInfo:
    return ResolveWithin(PathValue, PathInfo.cwd())


# tool inputs stay inside the operator selected working directory
def ResolveInput(PathValue: str | OsLayer.PathLike[str]) -> PathInfo:
    return ResolveWithin(PathValue, PathInfo.cwd(), True)


# tool output paths stay inside the operator selected working directory
def ResolveOutput(PathValue: str | OsLayer.PathLike[str]) -> PathInfo:
    return ResolveLocal(PathValue)


# tool directory inputs stay inside the operator selected working directory
def ResolveFolder(PathValue: str | OsLayer.PathLike[str]) -> PathInfo:
    ResultPath = ResolveWithin(PathValue, PathInfo.cwd())
    if not ResultPath.is_dir():
        raise NotADirectoryError(ResultPath)
    return ResultPath


# test artifacts stay inside the operating system managed temporary root
def ResolveTemp(PathValue: str | OsLayer.PathLike[str]) -> PathInfo:
    return ResolveWithin(PathValue, Tempfile.gettempdir())


# debugger labels enter command scripts so their character set must stay inert
def ValidateLabel(LabelText: str) -> str:
    IsSafe = 1 <= len(LabelText) <= 64 and all(
        (CharText.isalnum() or CharText in "-_") for CharText in LabelText
    )
    if not IsSafe:
        raise ValueError("debugger label contains unsafe command characters")
    return LabelText
