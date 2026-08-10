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
import struct
from typing import Any

from convert.adapters.solidworks.archive import read_string
from convert.adapters.solidworks.container import SldprtArchive


# primitive widths keep debugger reads aligned with native archive contracts
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
    "int64": 8,
    "uint64": 8,
}

# primitive formats preserve signedness and floating point values declaratively
PrimitiveFormats = {
    "char": "b",
    "uchar": "B",
    "short": "h",
    "ushort": "H",
    "int": "i",
    "long": "i",
    "ulong": "I",
    "float": "f",
    "double": "d",
    "int64": "q",
    "uint64": "Q",
}

# stream names and segmentation labels keep generation deterministic
StreamSpecs = (
    ("Contents/CMgr", "cmgr"),
    ("Contents/Config-0", "config"),
    ("Contents/Config-0-ResolvedFeatures", "resolved"),
    ("Contents/Definition", "definition"),
    ("Contents/Config-0-ModelHeader", "header"),
)

# direct fields name compound values that bypass primitive archive helpers
DirectFields = {
    "Contents/CMgr": (
        (0x0000, "H", "configuration manager archive prefix"),
        (0x0006, "5I", "configuration manager version preamble"),
        (0x0311, "H", "configuration manager inline object tag"),
        (0x0750, "H", "configuration manager inline object tag"),
    ),
    "Contents/Config-0": (
        (0x0000, "H", "assembly configuration archive prefix"),
        (0x0006, "3I", "assembly configuration version preamble"),
        (0x0A2E, "2d", "moTransRefPlaneData_c first inline transform row"),
        (0x0A42, "2d", "moTransRefPlaneData_c second inline transform row"),
        (0x0B0E, "I", "moTransRefPlaneData_c inline flag"),
        (0x44CA, "3i", "moLengthUserUnits_c detail scalar triplet"),
        (0x44FE, "3i", "moRelMgr_c detail scalar triplet"),
        (0x5E0C, "IHH8B", "moSketchBlockMgr_c persistent identifier"),
    ),
    "Contents/Config-0-ResolvedFeatures": (
        (0x0000, "I", "resolved feature continuation base"),
    ),
    "Contents/Definition": (
        (0x0000, "I", "definition document flags"),
        (0x001C, "d", "definition document class identifier tail"),
        (0x0E25, "H", "definition journal inline state"),
        (0x0E46, "I", "definition journal inline state"),
    ),
    "Contents/Config-0-ModelHeader": (
        (0x0000, "H", "model header archive prefix"),
        (0x0006, "5H", "model header string-array preamble"),
        (0x0029, "7H", "model header user and log preamble"),
        (0x0039, "3H", "model header log-list preamble"),
    ),
}

# native status names are serialized as one counted semantic list
StatusField = (
    "Contents/Config-0",
    0x0D95,
    (
        "Description",
        "High Priority",
        "Low Priority",
        "Complete",
        "Reminder",
    ),
    "moRelMgr_c status-name table",
)

# reference lengths locate fields that follow repeated component records
ReferenceLengths = {
    "Contents/CMgr": 1914,
    "Contents/Config-0": 24477,
    "Contents/Config-0-ResolvedFeatures": 5442,
    "Contents/Definition": 3894,
    "Contents/Config-0-ModelHeader": 2471,
}

# fields at or beyond these offsets move with each inserted component unit
ShiftStarts = {
    "Contents/CMgr": 0x0750,
    "Contents/Config-0": 0x0A2E,
}


# command arguments keep program generation reproducible across workstations
def ParseArguments() -> argparse.Namespace:
    Parser = argparse.ArgumentParser()
    Parser.add_argument("assembly", type=Path)
    Parser.add_argument("trace", type=Path)
    Parser.add_argument("segments", type=Path)
    Parser.add_argument("output", type=Path)
    return Parser.parse_args()


# traced values need stable source literals without losing floating point bits
def ValueLiteral(TypeName: str, FieldValue: Any) -> str:
    if TypeName in {"float", "double"}:
        return f"float.fromhex({float(FieldValue).hex()!r})"
    return repr(FieldValue)


# interval insertion prevents overlapping debugger aliases from duplicating bytes
def HasOverlap(Covered: set[int], StartPos: int, FieldWidth: int) -> bool:
    return any(
        Position in Covered for Position in range(StartPos, StartPos + FieldWidth)
    )


# each operation must own every byte it claims before another operation can
def AddOperation(
    Operations: list[tuple[int, int, str, str, Any]],
    Covered: set[int],
    StartPos: int,
    FieldWidth: int,
    OwnerText: str,
    KindName: str,
    FieldValue: Any,
) -> None:
    if HasOverlap(Covered, StartPos, FieldWidth):
        return
    Covered.update(range(StartPos, StartPos + FieldWidth))
    Operations.append((StartPos, FieldWidth, OwnerText, KindName, FieldValue))


# trace parsing retains the exact native caller and stream span for every field
def TraceRows(TraceText: str) -> tuple[tuple[str, int, str, int], ...]:
    ResultRows: list[tuple[str, int, str, int]] = []
    for SourceLine in TraceText.splitlines():
        if not SourceLine.startswith("A "):
            continue
        PartsList = SourceLine.split()
        if len(PartsList) < 7 or PartsList[1] not in PrimitiveWidths:
            continue
        OwnerText = " ".join(PartsList[4:-1]).split(" (")[0]
        ResultRows.append(
            (
                PartsList[1],
                int(PartsList[2], 16),
                OwnerText,
                int(PartsList[-1], 16),
            )
        )
    return tuple(ResultRows)


# archive object tags are structural vocabulary rather than anonymous bytes
def AddStructures(
    Operations: list[tuple[int, int, str, str, Any]],
    Covered: set[int],
    StreamData: bytes,
    Segments: tuple[dict[str, Any], ...],
) -> None:
    for Segment in Segments:
        StartPos = int(Segment["offset"])
        HeadWidth = int(Segment["header"])
        KindName = str(Segment["kind"])
        if KindName == "definition":
            FieldValue = (
                str(Segment["class_name"]),
                int.from_bytes(StreamData[StartPos + 2 : StartPos + 4], "little"),
            )
        elif KindName == "classref":
            FieldValue = int(Segment["class_index"])
        elif KindName == "objectref":
            FieldValue = int(Segment["object_index"])
        elif KindName == "null":
            FieldValue = 0
        else:
            raise ValueError(f"unknown archive object kind {KindName!r}")
        AddOperation(
            Operations,
            Covered,
            StartPos,
            HeadWidth,
            "su_CArchive::ReadClass",
            KindName,
            FieldValue,
        )


# traced string calls replace their marker length and payload as one value
def AddStrings(
    Operations: list[tuple[int, int, str, str, Any]],
    Covered: set[int],
    StreamData: bytes,
    RowsList: tuple[tuple[str, int, str, int], ...],
) -> None:
    StringStarts = {
        StartPos
        for TypeName, StartPos, OwnerText, _StreamSpan in RowsList
        if TypeName == "uchar"
        and "su_CArchive::WriteString+0x53" in OwnerText
        and StreamData[StartPos : StartPos + 3] == b"\xff\xfe\xff"
    }
    for StartPos in sorted(StringStarts):
        TextValue, FieldWidth = read_string(StreamData, StartPos)
        AddOperation(
            Operations,
            Covered,
            StartPos,
            FieldWidth,
            "su_CArchive::WriteString",
            "string",
            TextValue,
        )


# compound fields remain typed named values instead of residual byte spans
def AddDirectFields(
    StreamName: str,
    Operations: list[tuple[int, int, str, str, Any]],
    Covered: set[int],
    StreamData: bytes,
) -> None:
    StreamShift = len(StreamData) - ReferenceLengths[StreamName]
    ShiftStart = ShiftStarts.get(StreamName)
    for StartPos, FormatText, OwnerText in DirectFields[StreamName]:
        if ShiftStart is not None and StartPos >= ShiftStart:
            StartPos += StreamShift
        FieldWidth = struct.calcsize("<" + FormatText)
        ValuesList = struct.unpack_from("<" + FormatText, StreamData, StartPos)
        FieldValue: Any = ValuesList[0] if len(ValuesList) == 1 else ValuesList
        AddOperation(
            Operations,
            Covered,
            StartPos,
            FieldWidth,
            OwnerText,
            "direct:" + FormatText,
            FieldValue,
        )
    StatusStream, StartPos, TextValues, OwnerText = StatusField
    if StreamName != StatusStream:
        return
    if ShiftStart is not None and StartPos >= ShiftStart:
        StartPos += StreamShift
    FieldWidth = 2
    for _TextValue in TextValues:
        _Decoded, StringWidth = read_string(StreamData, StartPos + FieldWidth)
        FieldWidth += StringWidth
    AddOperation(
        Operations,
        Covered,
        StartPos,
        FieldWidth,
        OwnerText,
        "stringlist",
        TextValues,
    )


# primitive operations expose all remaining fields by serializer callsite
def AddPrimitives(
    Operations: list[tuple[int, int, str, str, Any]],
    Covered: set[int],
    StreamData: bytes,
    RowsList: tuple[tuple[str, int, str, int], ...],
) -> None:
    for TypeName, StartPos, OwnerText, _StreamSpan in RowsList:
        FieldWidth = PrimitiveWidths[TypeName]
        if HasOverlap(Covered, StartPos, FieldWidth):
            continue
        FormatText = PrimitiveFormats[TypeName]
        FieldValue = struct.unpack_from("<" + FormatText, StreamData, StartPos)[0]
        AddOperation(
            Operations,
            Covered,
            StartPos,
            FieldWidth,
            OwnerText,
            "primitive:" + TypeName,
            FieldValue,
        )


# one stream must achieve complete closure before it enters the generated module
def BuildProgram(
    StreamName: str,
    StreamData: bytes,
    Segments: tuple[dict[str, Any], ...],
    TraceData: tuple[tuple[str, int, str, int], ...],
) -> list[tuple[int, int, str, str, Any]]:
    RowsList = tuple(RowData for RowData in TraceData if RowData[3] == len(StreamData))
    Operations: list[tuple[int, int, str, str, Any]] = []
    Covered: set[int] = set()
    AddStructures(Operations, Covered, StreamData, Segments)
    AddDirectFields(StreamName, Operations, Covered, StreamData)
    AddStrings(Operations, Covered, StreamData, RowsList)
    AddPrimitives(Operations, Covered, StreamData, RowsList)
    Missing = sorted(set(range(len(StreamData))) - Covered)
    if Missing:
        raise ValueError(f"{StreamName} leaves bytes uncovered {Missing[:64]}")
    Operations.sort()
    return Operations


# generated source is readable typed vocabulary with no vendor byte spans
def RenderSource(
    Programs: dict[str, list[tuple[int, int, str, str, Any]]],
) -> str:
    OwnerNames = tuple(
        sorted(
            {
                Operation[2]
                for Operations in Programs.values()
                for Operation in Operations
            }
        )
    )
    OwnerIndex = {OwnerText: Index for Index, OwnerText in enumerate(OwnerNames)}
    SourceLines = [
        "# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0",
        "# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin",
        "#",
        "# This SPDX license identifier and copyright notice must not be",
        "# removed, altered, or obscured. Doing so is a material breach of",
        "# the PolyForm Strict License 1.0.0 and voids all licenses granted",
        "# to you under it immediately and permanently.",
        "",
        "from __future__ import annotations",
        "",
        "from collections.abc import Mapping",
        "import struct",
        "from typing import Any",
        "",
        "from .archive import encode_class_definition, encode_class_reference, encode_object_reference, encode_string",
        "from .container import SldprtFormatError",
        "",
        "",
        "# recovered callsites make every declared field traceable to its native serializer",
        "FieldOwners = (",
    ]
    SourceLines.extend(f"    {OwnerText!r}," for OwnerText in OwnerNames)
    SourceLines.extend(
        [
            ")",
            "",
            "# each stream program contains only typed field values",
            "StreamPrograms = {",
        ]
    )
    for StreamName, Operations in Programs.items():
        SourceLines.append(f"    {StreamName!r}: (")
        for StartPos, FieldWidth, OwnerText, KindName, FieldValue in Operations:
            if KindName.startswith("primitive:"):
                ValueText = ValueLiteral(KindName.split(":", 1)[1], FieldValue)
            else:
                ValueText = repr(FieldValue)
            SourceLines.append(
                f"        ({StartPos}, {FieldWidth}, {OwnerIndex[OwnerText]}, {KindName!r}, {ValueText}),"
            )
        SourceLines.append("    ),")
    SourceLines.extend(
        [
            "}",
            "",
            "# primitive formats keep signed and floating fields faithful to their reader",
            "PrimitiveFormats = " + repr(PrimitiveFormats),
            "",
            "",
            "# each operation serializes one recovered value through its typed contract",
            "def EncodeField(KindName: str, FieldValue: Any) -> bytes:",
            "    if KindName == 'definition':",
            "        ClassName, SchemaCode = FieldValue",
            "        return encode_class_definition(ClassName, SchemaCode)",
            "    if KindName == 'classref':",
            "        return encode_class_reference(FieldValue)",
            "    if KindName == 'objectref':",
            "        return encode_object_reference(FieldValue)",
            "    if KindName == 'null':",
            "        return struct.pack('<H', 0)",
            "    if KindName == 'string':",
            "        return encode_string(FieldValue)",
            "    if KindName == 'stringlist':",
            "        return struct.pack('<H', len(FieldValue)) + b''.join(encode_string(ItemText) for ItemText in FieldValue)",
            "    if KindName.startswith('primitive:'):",
            "        TypeName = KindName.split(':', 1)[1]",
            "        return struct.pack('<' + PrimitiveFormats[TypeName], FieldValue)",
            "    if KindName.startswith('direct:'):",
            "        FormatText = KindName.split(':', 1)[1]",
            "        ValuesList = FieldValue if isinstance(FieldValue, tuple) else (FieldValue,)",
            "        return struct.pack('<' + FormatText, *ValuesList)",
            "    raise SldprtFormatError(f'unknown assembly operation {KindName!r}')",
            "",
            "",
            "# callers may replace semantic fields while source offsets preserve field order",
            "def EncodeProgram(StreamName: str, Overrides: Mapping[int, Any] | None = None) -> bytes:",
            "    try:",
            "        Operations = StreamPrograms[StreamName]",
            "    except KeyError as ErrorData:",
            "        raise SldprtFormatError(f'unknown assembly stream {StreamName!r}') from ErrorData",
            "    FieldOverrides = Overrides or {}",
            "    OutputData = bytearray()",
            "    SourceCursor = 0",
            "    for StartPos, FieldWidth, OwnerIndex, KindName, DefaultValue in Operations:",
            "        if StartPos != SourceCursor:",
            "            raise SldprtFormatError(f'assembly field program drifted at {StartPos}')",
            "        SourceCursor += FieldWidth",
            "        FieldValue = FieldOverrides.get(StartPos, DefaultValue)",
            "        FieldData = EncodeField(KindName, FieldValue)",
            "        if KindName not in {'string', 'stringlist'} and len(FieldData) != FieldWidth:",
            "            raise SldprtFormatError(f'assembly field width changed at {StartPos}')",
            "        OutputData.extend(FieldData)",
            "    return bytes(OutputData)",
            "",
        ]
    )
    return "\n".join(SourceLines)


# all five coupled assembly programs must close before writing generated source
def RunMain() -> int:
    Arguments = ParseArguments()
    Archive = SldprtArchive.open(Arguments.assembly)
    TraceText = Arguments.trace.read_text(encoding="utf-8", errors="replace")
    TraceData = TraceRows(TraceText)
    Programs: dict[str, list[tuple[int, int, str, str, Any]]] = {}
    RunLabel = Arguments.assembly.stem.casefold()
    for StreamName, SegmentLabel in StreamSpecs:
        StreamData = Archive.require(StreamName)
        SegmentPath = Arguments.segments / f"segments_{RunLabel}_{SegmentLabel}.json"
        SegmentData = json.loads(SegmentPath.read_text(encoding="utf-8"))
        Segments = tuple(SegmentData["segments"])
        Programs[StreamName] = BuildProgram(StreamName, StreamData, Segments, TraceData)
    Arguments.output.write_text(RenderSource(Programs), encoding="utf-8", newline="\n")
    print(
        json.dumps(
            {
                StreamName: {
                    "bytes": len(Archive.require(StreamName)),
                    "operations": len(Operations),
                }
                for StreamName, Operations in Programs.items()
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(RunMain())
