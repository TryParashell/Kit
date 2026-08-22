# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from os import PathLike as PathLikeValue
from os.path import abspath as AbsolutePath
from pathlib import Path as PathInfo


# lexical containment blocks traversal before candidate paths reach filesystem operations
def ResolveLexical(PathValue: str | PathLikeValue[str], RootPath: PathInfo) -> PathInfo:
    CandidatePath = PathInfo(PathValue)
    if not CandidatePath.is_absolute():
        CandidatePath = RootPath / CandidatePath
    LexicalPath = PathInfo(AbsolutePath(CandidatePath))
    LexicalPath.relative_to(RootPath)
    return LexicalPath
