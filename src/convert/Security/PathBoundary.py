# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations as Annotations

from os import PathLike as PathLikeValue
from pathlib import Path as PathInfo
import tempfile as Tempfile

from convert.Security.LexicalBoundary import ResolveLexical

# command argument paths permit only inert characters after fixed root resolution
KCommandPathCharacters = frozenset(" ._-/\\:")


# unsafe filesystem selections need a distinct failure contract at trust boundaries
class UnsafePath(ValueError):
    __slots__ = ()


# canonical containment prevents traversal and symlink escapes before protected filesystem operations
def ResolveWithin(
    PathValue: str | PathLikeValue[str],
    RootValue: str | PathLikeValue[str],
    RequireFile: bool = False,
) -> PathInfo:
    RootPath = PathInfo(RootValue).resolve(strict=True)
    try:
        CandidatePath = ResolveLexical(PathValue, RootPath)
    except ValueError as ErrorInfo:
        raise UnsafePath(f"path escapes trusted root {str(RootPath)!r}") from ErrorInfo
    ResultPath = CandidatePath.resolve(strict=RequireFile)
    try:
        ResultPath.relative_to(RootPath)
    except ValueError as ErrorInfo:
        raise UnsafePath(f"path escapes trusted root {str(RootPath)!r}") from ErrorInfo
    if RequireFile and not ResultPath.is_file():
        raise FileNotFoundError(ResultPath)
    return ResultPath


# local paths need one containment primitive before applying file type rules
def ResolveLocal(PathValue: str | PathLikeValue[str]) -> PathInfo:
    return ResolveWithin(PathValue, PathInfo.cwd())


# tool inputs stay inside the operator selected working directory
def ResolveInput(PathValue: str | PathLikeValue[str]) -> PathInfo:
    return ResolveWithin(PathValue, PathInfo.cwd(), True)


# subprocess file arguments need containment plus a command inert absolute spelling
def ResolveArgPath(PathValue: str | PathLikeValue[str]) -> PathInfo:
    ResultPath = ResolveInput(PathValue)
    if any(
        not CharText.isalnum() and CharText not in KCommandPathCharacters
        for CharText in str(ResultPath)
    ):
        raise UnsafePath("command argument path contains unsafe characters")
    return ResultPath


# tool output paths stay inside the operator selected working directory
def ResolveOutput(PathValue: str | PathLikeValue[str]) -> PathInfo:
    return ResolveLocal(PathValue)


# tool directory inputs stay inside the operator selected working directory
def ResolveFolder(PathValue: str | PathLikeValue[str]) -> PathInfo:
    ResultPath = ResolveWithin(PathValue, PathInfo.cwd())
    if not ResultPath.is_dir():
        raise NotADirectoryError(ResultPath)
    return ResultPath


# test artifacts stay inside the operating system managed temporary root
def ResolveTemp(PathValue: str | PathLikeValue[str]) -> PathInfo:
    return ResolveWithin(PathValue, Tempfile.gettempdir())


# debugger labels enter command scripts so their character set must stay inert
def ValidateLabel(LabelText: str) -> str:
    IsSafe = 1 <= len(LabelText) <= 64 and all(
        (CharText.isalnum() or CharText in "-_") for CharText in LabelText
    )
    if not IsSafe:
        raise ValueError("debugger label contains unsafe command characters")
    return LabelText
