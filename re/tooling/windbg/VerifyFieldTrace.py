# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations
import argparse as Argparse
import json as JsonData
from pathlib import Path as PathInfo
import re as Regex
from typing import Any as AnyInfo
from convert.adapters.solidworks.container.Archive import ReadString
from convert.adapters.solidworks.container.Container import SldprtArchive
from convert.adapters.solidworks.container.Format import RESOLVED_FEATURES_STREAM as ResolvedStream

# needed to keep reverse engineering responsibilities isolated and maintainable
KPrimWidths = {'char': 1, 'uchar': 1, 'short': 2, 'ushort': 2, 'int': 4, 'long': 4, 'ulong': 4, 'float': 4, 'double': 8, 'dbkey': 0, 'int64': 8, 'uint64': 8}

# needed to keep reverse engineering responsibilities isolated and maintainable
KPrimPattern = Regex.compile('^F (\\w+) ([0-9a-f]+) ', Regex.MULTILINE)

# needed to keep reverse engineering responsibilities isolated and maintainable
KStringPattern = Regex.compile('^F uchar ([0-9a-f]+) [0-9a-f`]+ swccu!su_CArchive::WriteString\\+0x53 ', Regex.MULTILINE)

# needed to keep reverse engineering responsibilities isolated and maintainable
KDirectReads = ((0, 4, 'archive continuation base'), (7772, 16, 'first sketch chain entity index array'), (7790, 4, 'second sketch chain entity index array'), (8925, 4, 'per body chooser index array'), (9626, 2, 'display dimension index array'), (10466, 8, 'extrusion depth scalar'))

# needed to keep reverse engineering responsibilities isolated and maintainable
KExpectTotals = {'stream': 11075, 'primitive': 9876, 'class_names': 701, 'string_payloads': 460, 'direct': 38}


# needed to keep reverse engineering responsibilities isolated and maintainable
def ParseArguments() -> Argparse.Namespace:
    Parser = Argparse.ArgumentParser()
    Parser.add_argument('part', type=PathInfo)
    Parser.add_argument('trace', type=PathInfo)
    Parser.add_argument('segments', type=PathInfo)
    return Parser.parse_args()


# needed to keep reverse engineering responsibilities isolated and maintainable
def AddSpanMut(Positions: set[int], Start: int, Width: int, StreamLength: int) -> None:
    if Start < 0 or Width < 0 or Start + Width > StreamLength:
        raise ValueError(f'interval {Start}+{Width} exceeds {StreamLength} stream bytes')
    Positions.update(range(Start, Start + Width))


# needed to keep reverse engineering responsibilities isolated and maintainable
def PrimPos(Trace: str, StreamLength: int) -> set[int]:
    Positions: set[int] = set()
    for TypeName, HexPosition in KPrimPattern.findall(Trace):
        if TypeName not in KPrimWidths:
            raise ValueError(f'unknown primitive reader {TypeName!r}')
        AddSpanMut(Positions, int(HexPosition, 16), KPrimWidths[TypeName], StreamLength)
    return Positions


# needed to keep reverse engineering responsibilities isolated and maintainable
def ClassNamePos(Segments: tuple[dict[str, AnyInfo], ...], StreamLength: int) -> set[int]:
    Positions: set[int] = set()
    for Segment in Segments:
        if Segment['kind'] != 'definition':
            continue
        Start = int(Segment['offset']) + 6
        Width = int(Segment['header']) - 6
        AddSpanMut(Positions, Start, Width, StreamLength)
    return Positions


# needed to keep reverse engineering responsibilities isolated and maintainable
def StringPos(BlobInfo: bytes, Trace: str) -> tuple[set[int], int]:
    Positions: set[int] = set()
    Count = 0
    for HexPosition in KStringPattern.findall(Trace):
        Start = int(HexPosition, 16)
        if BlobInfo[Start:Start + 3] != b'\xff\xfe\xff':
            continue
        TextInfo, Consumed = ReadString(BlobInfo, Start)
        Width = len(TextInfo.encode('utf-16-le'))
        AddSpanMut(Positions, Start + Consumed - Width, Width, len(BlobInfo))
        Count += 1
    return (Positions, Count)


# needed to keep reverse engineering responsibilities isolated and maintainable
def DirectPositions(StreamLength: int) -> set[int]:
    Positions: set[int] = set()
    for Start, Width, SpareValue in KDirectReads:
        AddSpanMut(Positions, Start, Width, StreamLength)
    return Positions


# needed to keep reverse engineering responsibilities isolated and maintainable
def MainRun() -> int:
    Arguments = ParseArguments()
    Archive = SldprtArchive.open(Arguments.part)
    BlobInfo = Archive.require(ResolvedStream)
    Trace = Arguments.trace.read_text(encoding='utf-8', errors='replace')
    Payload = JsonData.loads(Arguments.segments.read_text(encoding='utf-8'))
    Segments = tuple(Payload['segments'])
    Primitive = PrimPos(Trace, len(BlobInfo))
    ClassNames = ClassNamePos(Segments, len(BlobInfo))
    StringPayloads, StringCount = StringPos(BlobInfo, Trace)
    Direct = DirectPositions(len(BlobInfo))
    Covered = Primitive | ClassNames | StringPayloads | Direct
    Missing = sorted(set(range(len(BlobInfo))) - Covered)
    Actual = {'stream': len(BlobInfo), 'primitive': len(Primitive), 'class_names': len(ClassNames), 'string_payloads': len(StringPayloads), 'direct': len(Direct), 'strings': StringCount, 'covered': len(Covered), 'missing': len(Missing)}
    if any((Actual[NameInfo] != Value for NameInfo, Value in KExpectTotals.items())):
        raise ValueError(f'field trace totals changed: {Actual}')
    if Missing:
        raise ValueError(f'field trace leaves bytes uncovered: {Missing[:32]}')
    print(JsonData.dumps(Actual, indent=2))
    return 0
if __name__ == '__main__':
    raise SystemExit(MainRun())
