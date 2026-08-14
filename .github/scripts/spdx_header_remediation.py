# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path


def write_missing_header(
    FilePath: Path, SourceLines: list[str], HeaderLines: list[str]
) -> None:
    Offset = 1 if SourceLines and SourceLines[0].startswith("#!") else 0
    UpdatedLines = SourceLines[:Offset] + HeaderLines + [""] + SourceLines[Offset:]
    FilePath.write_text("\n".join(UpdatedLines) + "\n", encoding="utf-8")
