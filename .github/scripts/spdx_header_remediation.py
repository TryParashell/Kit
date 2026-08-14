# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path


def write_missing_header(FilePath: Path, HeaderLines: list[str]) -> None:
    SourceBytes = FilePath.read_bytes()
    Newline = b"\r\n" if b"\r\n" in SourceBytes else b"\n"
    HeaderBytes = (
        Newline.join(Line.encode("utf-8") for Line in HeaderLines) + Newline * 2
    )
    Offset = SourceBytes.find(b"\n") + 1 if SourceBytes.startswith(b"#!") else 0
    FilePath.write_bytes(SourceBytes[:Offset] + HeaderBytes + SourceBytes[Offset:])


def write_mangled_header(FilePath: Path, HeaderLines: list[str], Style: str) -> bool:
    SourceBytes = FilePath.read_bytes()
    Newline = b"\r\n" if b"\r\n" in SourceBytes else b"\n"
    HeaderBytes = (
        Newline.join(Line.encode("utf-8") for Line in HeaderLines) + Newline * 2
    )
    Offset = SourceBytes.find(b"\n") + 1 if SourceBytes.startswith(b"#!") else 0
    LeadingLines = SourceBytes[Offset:].splitlines(keepends=True)
    Index = 0
    while Index < len(LeadingLines):
        StrippedLine = LeadingLines[Index].strip()
        if not StrippedLine or (
            Style != "block" and StrippedLine.startswith(Style.encode())
        ):
            Index += 1
            continue
        if Style == "block" and StrippedLine.startswith(b"<!--"):
            while Index < len(LeadingLines):
                ClosingLine = LeadingLines[Index]
                Index += 1
                if b"-->" in ClosingLine:
                    break
            else:
                return False
            continue
        break
    FilePath.write_bytes(
        SourceBytes[:Offset] + HeaderBytes + b"".join(LeadingLines[Index:])
    )
    return True
