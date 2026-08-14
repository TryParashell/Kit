# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

"""Repair only safely identifiable top level SPDX headers without rewriting file content."""

from __future__ import annotations

import pathlib as Pathlib


# inserted bytes must follow the existing file ending so remediation creates no unrelated churn
def GetNewline(SourceBytes: bytes) -> bytes:
    FirstBreak = SourceBytes.find(b"\n")
    if FirstBreak > 0 and SourceBytes[FirstBreak - 1 : FirstBreak + 1] == b"\r\n":
        return b"\r\n"
    return b"\n"


# one renderer keeps missing and mangled repairs byte identical for a given source file
def MakeHeader(HeaderLines: list[str], Newline: bytes) -> bytes:
    HeaderBytes = Newline.join(LineText.encode("utf-8") for LineText in HeaderLines)
    return HeaderBytes + Newline * 2


# shebang boundaries need byte handling because an unterminated first line has no insertion offset
def GetLeadEnd(SourceBytes: bytes) -> int | None:
    if not SourceBytes.startswith(b"#!"):
        return 0
    FirstBreak = SourceBytes.find(b"\n")
    if FirstBreak < 0:
        return None
    return FirstBreak + 1


# absent notices can be inserted without decoding or normalizing any existing source bytes
def WriteMissingMut(FilePath: Pathlib.Path, HeaderLines: list[str]) -> None:
    SourceBytes = FilePath.read_bytes()
    Newline = GetNewline(SourceBytes)
    HeaderBytes = MakeHeader(HeaderLines, Newline)
    LeadOffset = GetLeadEnd(SourceBytes)
    if LeadOffset is None:
        FilePath.write_bytes(SourceBytes + Newline + HeaderBytes)
        return
    FilePath.write_bytes(
        SourceBytes[:LeadOffset] + HeaderBytes + SourceBytes[LeadOffset:]
    )


# line notice bounds prevent automated repair from consuming unrelated leading documentation
def GetLineEnd(
    SourceLines: list[bytes], PrefixBytes: bytes, HeaderSize: int
) -> int | None:
    MarkerFound = False
    CommentCount = 0
    for LineIndex, LineBytes in enumerate(SourceLines):
        StrippedLine = LineBytes.strip()
        if not StrippedLine:
            if MarkerFound:
                return LineIndex + 1
            continue
        if not StrippedLine.startswith(PrefixBytes):
            return LineIndex if MarkerFound else None
        CommentCount += 1
        if CommentCount > HeaderSize:
            return None
        MarkerFound = MarkerFound or b"SPDX-License-Identifier" in StrippedLine
        MarkerFound = MarkerFound or b"SPDX-FileCopyrightText" in StrippedLine
    return len(SourceLines) if MarkerFound else None


# block notice bounds require a closing delimiter so malformed markup cannot swallow source content
def GetBlockEnd(SourceLines: list[bytes], HeaderSize: int) -> int | None:
    StartIndex = next(
        (
            LineIndex
            for LineIndex, LineBytes in enumerate(SourceLines)
            if LineBytes.strip()
        ),
        None,
    )
    if StartIndex is None or SourceLines[StartIndex].strip() != b"<!--":
        return None
    MarkerFound = False
    MaxIndex = min(len(SourceLines), StartIndex + HeaderSize + 3)
    for LineIndex in range(StartIndex + 1, MaxIndex):
        StrippedLine = SourceLines[LineIndex].strip()
        MarkerFound = MarkerFound or b"SPDX-License-Identifier" in StrippedLine
        MarkerFound = MarkerFound or b"SPDX-FileCopyrightText" in StrippedLine
        if b"-->" in StrippedLine:
            EndIndex = LineIndex + 1
            if EndIndex < len(SourceLines) and not SourceLines[EndIndex].strip():
                EndIndex += 1
            return EndIndex if MarkerFound else None
    return None


# guarded replacement repairs only a bounded leading notice proven to contain an spdx marker
def CanRepairMut(
    FilePath: Pathlib.Path, HeaderLines: list[str], StyleText: str
) -> bool:
    SourceBytes = FilePath.read_bytes()
    Newline = GetNewline(SourceBytes)
    LeadOffset = GetLeadEnd(SourceBytes)
    if LeadOffset is None:
        return False
    SourceLines = SourceBytes[LeadOffset:].splitlines(keepends=True)
    if StyleText == "block":
        EndIndex = GetBlockEnd(SourceLines, len(HeaderLines))
    else:
        EndIndex = GetLineEnd(
            SourceLines, StyleText.encode("utf-8"), len(HeaderLines)
        )
    if EndIndex is None:
        return False
    BodyBytes = b"".join(SourceLines[EndIndex:])
    FilePath.write_bytes(
        SourceBytes[:LeadOffset] + MakeHeader(HeaderLines, Newline) + BodyBytes
    )
    return True
