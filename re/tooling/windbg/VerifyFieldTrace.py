# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Any

from convert.adapters.solidworks.container.Archive import read_string
from convert.adapters.solidworks.container.Container import SldprtArchive
from convert.adapters.solidworks.container.Format import RESOLVED_FEATURES_STREAM

# primitive widths reproduce each native archive reader contract
PrimitiveWidths = {
    "char": 1,
    "uchar": 1,
    "short": 2,
    "ushort": 2,
    "int": 4,
    "long": 4,
    "ulong": 4,
    "float": 4,
    "double": 8,
    "dbkey": 0,
    "int64": 8,
    "uint64": 8,
}

# trace rows retain the primitive type and pre read cursor
PrimitivePattern = re.compile(r"^F (\w+) ([0-9a-f]+) ", re.MULTILINE)

# string rows identify payloads read outside primitive archive helpers
StringPattern = re.compile(
    r"^F uchar ([0-9a-f]+) [0-9a-f`]+ " r"swccu!su_CArchive::WriteString\+0x53 ",
    re.MULTILINE,
)

# direct reads are counted arrays or scalars confirmed by decompilation
DirectReads = (
    (0, 4, "archive continuation base"),
    (7772, 16, "first sketch chain entity index array"),
    (7790, 4, "second sketch chain entity index array"),
    (8925, 4, "per body chooser index array"),
    (9626, 2, "display dimension index array"),
    (10466, 8, "extrusion depth scalar"),
)

# closure totals guard the complete baseline wire accounting
ExpectedTotals = {
    "stream": 11075,
    "primitive": 9876,
    "class_names": 701,
    "string_payloads": 460,
    "direct": 38,
}


# argument parsing keeps the verifier reproducible from command line
def ParseArguments() -> argparse.Namespace:
    Parser = argparse.ArgumentParser()
    Parser.add_argument("part", type=Path)
    Parser.add_argument("trace", type=Path)
    Parser.add_argument("segments", type=Path)
    return Parser.parse_args()


# interval insertion rejects any read extending beyond the stream
def AddInterval(Positions: set[int], Start: int, Width: int, StreamLength: int) -> None:
    if Start < 0 or Width < 0 or Start + Width > StreamLength:
        raise ValueError(
            f"interval {Start}+{Width} exceeds {StreamLength} stream bytes"
        )
    Positions.update(range(Start, Start + Width))


# primitive extraction converts debugger cursors into covered byte positions
def PrimitivePositions(Trace: str, StreamLength: int) -> set[int]:
    Positions: set[int] = set()
    for TypeName, HexPosition in PrimitivePattern.findall(Trace):
        if TypeName not in PrimitiveWidths:
            raise ValueError(f"unknown primitive reader {TypeName!r}")
        AddInterval(
            Positions,
            int(HexPosition, 16),
            PrimitiveWidths[TypeName],
            StreamLength,
        )
    return Positions


# class definition payloads are direct ascii reads after archive framing
def ClassNamePositions(
    Segments: tuple[dict[str, Any], ...], StreamLength: int
) -> set[int]:
    Positions: set[int] = set()
    for Segment in Segments:
        if Segment["kind"] != "definition":
            continue
        Start = int(Segment["offset"]) + 6
        Width = int(Segment["header"]) - 6
        AddInterval(Positions, Start, Width, StreamLength)
    return Positions


# cstring payload extraction excludes the already traced length framing
def StringPayloadPositions(Blob: bytes, Trace: str) -> tuple[set[int], int]:
    Positions: set[int] = set()
    Count = 0
    for HexPosition in StringPattern.findall(Trace):
        Start = int(HexPosition, 16)
        if Blob[Start : Start + 3] != b"\xff\xfe\xff":
            continue
        Text, Consumed = read_string(Blob, Start)
        Width = len(Text.encode("utf-16-le"))
        AddInterval(Positions, Start + Consumed - Width, Width, len(Blob))
        Count += 1
    return Positions, Count


# direct span expansion verifies every bypass around primitive helpers
def DirectPositions(StreamLength: int) -> set[int]:
    Positions: set[int] = set()
    for Start, Width, _ in DirectReads:
        AddInterval(Positions, Start, Width, StreamLength)
    return Positions


# verification proves every stream byte belongs to one recovered path
def Main() -> int:
    Arguments = ParseArguments()
    Archive = SldprtArchive.open(Arguments.part)
    Blob = Archive.require(RESOLVED_FEATURES_STREAM)
    Trace = Arguments.trace.read_text(encoding="utf-8", errors="replace")
    Payload = json.loads(Arguments.segments.read_text(encoding="utf-8"))
    Segments = tuple(Payload["segments"])

    Primitive = PrimitivePositions(Trace, len(Blob))
    ClassNames = ClassNamePositions(Segments, len(Blob))
    StringPayloads, StringCount = StringPayloadPositions(Blob, Trace)
    Direct = DirectPositions(len(Blob))
    Covered = Primitive | ClassNames | StringPayloads | Direct
    Missing = sorted(set(range(len(Blob))) - Covered)

    Actual = {
        "stream": len(Blob),
        "primitive": len(Primitive),
        "class_names": len(ClassNames),
        "string_payloads": len(StringPayloads),
        "direct": len(Direct),
        "strings": StringCount,
        "covered": len(Covered),
        "missing": len(Missing),
    }
    if any(Actual[Name] != Value for Name, Value in ExpectedTotals.items()):
        raise ValueError(f"field trace totals changed: {Actual}")
    if Missing:
        raise ValueError(f"field trace leaves bytes uncovered: {Missing[:32]}")
    print(json.dumps(Actual, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(Main())
