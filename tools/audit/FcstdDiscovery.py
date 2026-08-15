# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from pathlib import Path as FilePath


# normalized discovery prevents duplicate audits when recursive roots overlap
def DiscoverSources(RootPaths: tuple[FilePath, ...]) -> tuple[FilePath, ...]:
    SourcePaths: set[FilePath] = set()
    for RootPath in RootPaths:
        ResolvedPath = RootPath.expanduser().resolve()
        if ResolvedPath.is_file():
            if ResolvedPath.suffix.casefold() == ".fcstd":
                SourcePaths.add(ResolvedPath)
            continue
        if not ResolvedPath.is_dir():
            raise FileNotFoundError(f"audit root does not exist: {ResolvedPath}")
        SourcePaths.update(
            ItemPath.resolve()
            for ItemPath in ResolvedPath.rglob("*")
            if ItemPath.is_file() and ItemPath.suffix.casefold() == ".fcstd"
        )
    return tuple(sorted(SourcePaths, key=FilePath.as_posix))
