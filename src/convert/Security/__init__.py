# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.Security.PathBoundary import (
    ResolveFolder,
    ResolveInput,
    ResolveLocal,
    ResolveOutput,
    ResolveTemp,
    ResolveWithin,
    UnsafePath,
    ValidateLabel,
)
from convert.Security.ProgramBoundary import GetArgPath, GetFreecadPath


# callers need one explicit public surface for repository security boundaries
__all__ = [
    "GetArgPath",
    "GetFreecadPath",
    "ResolveFolder",
    "ResolveInput",
    "ResolveLocal",
    "ResolveOutput",
    "ResolveTemp",
    "ResolveWithin",
    "UnsafePath",
    "ValidateLabel",
]
