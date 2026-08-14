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

from convert.Security.PathBoundary import ResolveWithin, UnsafePath


# exact executable names prevent the oracle setting from selecting another program
KFreecadNames = frozenset(("FreeCADCmd", "FreeCADCmd.exe", "freecadcmd"))

# administrator controlled install roots keep executable selection outside writable worktrees
KFreecadRoots = (
    PathInfo("C:/Program Files"),
    PathInfo("C:/Program Files (x86)"),
    PathInfo("/Applications/FreeCAD.app/Contents/MacOS"),
    PathInfo("/opt"),
    PathInfo("/usr/bin"),
    PathInfo("/usr/local/bin"),
)


# oracle execution is optional but any configured program must cross a strict allowlist
def GetFreecadPath() -> PathInfo:
    RawText = OsLayer.environ.get("KIT_FREECAD_ORACLE", "").strip()
    if not RawText:
        return PathInfo()
    Candidate = PathInfo(OsLayer.path.realpath(RawText))
    if Candidate.name not in KFreecadNames:
        raise UnsafePath("freecad oracle executable name is not allowed")
    for RootPath in KFreecadRoots:
        if not RootPath.is_dir():
            continue
        try:
            return ResolveWithin(Candidate, RootPath, True)
        except (FileNotFoundError, UnsafePath):
            continue
    raise UnsafePath("freecad oracle executable is outside trusted install roots")
