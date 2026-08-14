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
import struct as Struct
from typing import Any as AnyInfo
from convert.adapters.solidworks.container.Archive import ReadString
from convert.adapters.solidworks.container.Container import SldprtArchive

# needed to keep reverse engineering responsibilities isolated and maintainable
KPrimWidths = {
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

# needed to keep reverse engineering responsibilities isolated and maintainable
KPrimFormats = {
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

# needed to keep reverse engineering responsibilities isolated and maintainable
KStreamSpecs = (
    ("Contents/CMgr", "cmgr"),
    ("Contents/Config-0", "config"),
    ("Contents/Config-0-ResolvedFeatures", "resolved"),
    ("Contents/Definition", "definition"),
    ("Contents/Config-0-ModelHeader", "header"),
)

# configuration direct fields preserve manager and assembly payload measurements
KDirectConfig = {
    "Contents/CMgr": (
        (0, "H", "configuration manager archive prefix"),
        (6, "5I", "configuration manager version preamble"),
        (785, "H", "configuration manager inline object tag"),
        (1872, "H", "configuration manager inline object tag"),
    ),
    "Contents/Config-0": (
        (0, "H", "assembly configuration archive prefix"),
        (6, "3I", "assembly configuration version preamble"),
        (2606, "2d", "moTransRefPlaneData_c first inline transform row"),
        (2626, "2d", "moTransRefPlaneData_c second inline transform row"),
        (2830, "I", "moTransRefPlaneData_c inline flag"),
        (17610, "3i", "moLengthUserUnits_c detail scalar triplet"),
        (17662, "3i", "moRelMgr_c detail scalar triplet"),
        (24076, "IHH8B", "moSketchBlockMgr_c persistent identifier"),
    ),
}

# document direct fields preserve resolved definition and header measurements
KDirectDocument = {
    "Contents/Config-0-ResolvedFeatures": (
        (0, "I", "resolved feature continuation base"),
    ),
    "Contents/Definition": (
        (0, "I", "definition document flags"),
        (28, "d", "definition document class identifier tail"),
        (3621, "H", "definition journal inline state"),
        (3654, "I", "definition journal inline state"),
    ),
    "Contents/Config-0-ModelHeader": (
        (0, "H", "model header archive prefix"),
        (6, "5H", "model header string-array preamble"),
        (41, "7H", "model header user and log preamble"),
        (57, "3H", "model header log-list preamble"),
    ),
}

# ordered direct fields keep stream traversal stable across generated assembly programs
KDirectInfo = {**KDirectConfig, **KDirectDocument}

# needed to keep reverse engineering responsibilities isolated and maintainable
KStatusField = (
    "Contents/Config-0",
    3477,
    ("Description", "High Priority", "Low Priority", "Complete", "Reminder"),
    "moRelMgr_c status-name table",
)

# needed to keep reverse engineering responsibilities isolated and maintainable
KRefLengths = {
    "Contents/CMgr": 1914,
    "Contents/Config-0": 24477,
    "Contents/Config-0-ResolvedFeatures": 5442,
    "Contents/Definition": 3894,
    "Contents/Config-0-ModelHeader": 2471,
}

# needed to keep reverse engineering responsibilities isolated and maintainable
KShiftStarts = {"Contents/CMgr": 1872, "Contents/Config-0": 2606}


# needed to keep reverse engineering responsibilities isolated and maintainable
def ParseArguments() -> Argparse.Namespace:
    Parser = Argparse.ArgumentParser()
    Parser.add_argument("assembly", type=PathInfo)
    Parser.add_argument("trace", type=PathInfo)
    Parser.add_argument("segments", type=PathInfo)
    Parser.add_argument("output", type=PathInfo)
    return Parser.parse_args()


# needed to keep reverse engineering responsibilities isolated and maintainable
def ValueLiteral(TypeName: str, FieldValue: AnyInfo) -> str:
    if TypeName in {"float", "double"}:
        return f"float.fromhex({float(FieldValue).hex()!r})"
    return repr(FieldValue)


# needed to keep reverse engineering responsibilities isolated and maintainable
def HasOverlap(Covered: set[int], StartPos: int, FieldWidth: int) -> bool:
    return any(
        (Position in Covered for Position in range(StartPos, StartPos + FieldWidth))
    )


# needed to keep reverse engineering responsibilities isolated and maintainable
def AddOpMut(
    Operations: list[tuple[int, int, str, str, AnyInfo]],
    Covered: set[int],
    StartPos: int,
    FieldWidth: int,
    OwnerText: str,
    KindName: str,
    FieldValue: AnyInfo,
) -> None:
    if HasOverlap(Covered, StartPos, FieldWidth):
        return
    Covered.update(range(StartPos, StartPos + FieldWidth))
    Operations.append((StartPos, FieldWidth, OwnerText, KindName, FieldValue))


# needed to keep reverse engineering responsibilities isolated and maintainable
def TraceRows(TraceText: str) -> tuple[tuple[str, int, str, int], ...]:
    ResultRows: list[tuple[str, int, str, int]] = []
    for SourceLine in TraceText.splitlines():
        if not SourceLine.startswith("A "):
            continue
        PartsList = SourceLine.split()
        if len(PartsList) < 7 or PartsList[1] not in KPrimWidths:
            continue
        OwnerText = " ".join(PartsList[4:-1]).split(" (")[0]
        ResultRows.append(
            (PartsList[1], int(PartsList[2], 16), OwnerText, int(PartsList[-1], 16))
        )
    return tuple(ResultRows)


# needed to keep reverse engineering responsibilities isolated and maintainable
def AddStructures(
    Operations: list[tuple[int, int, str, str, AnyInfo]],
    Covered: set[int],
    StreamData: bytes,
    Segments: tuple[dict[str, AnyInfo], ...],
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
        AddOpMut(
            Operations,
            Covered,
            StartPos,
            HeadWidth,
            "su_CArchive::ReadClass",
            KindName,
            FieldValue,
        )


# needed to keep reverse engineering responsibilities isolated and maintainable
def AddStrings(
    Operations: list[tuple[int, int, str, str, AnyInfo]],
    Covered: set[int],
    StreamData: bytes,
    RowsList: tuple[tuple[str, int, str, int], ...],
) -> None:
    StringStarts = {
        StartPos
        for TypeName, StartPos, OwnerText, StreamSpan in RowsList
        if TypeName == "uchar"
        and "su_CArchive::WriteString+0x53" in OwnerText
        and (StreamData[StartPos : StartPos + 3] == b"\xff\xfe\xff")
    }
    for StartPos in sorted(StringStarts):
        TextValue, FieldWidth = ReadString(StreamData, StartPos)
        AddOpMut(
            Operations,
            Covered,
            StartPos,
            FieldWidth,
            "su_CArchive::WriteString",
            "string",
            TextValue,
        )


# needed to keep reverse engineering responsibilities isolated and maintainable
def FieldPosition(
    StreamName: str,
    StartPos: int,
    OwnerText: str,
    StreamShift: int,
    Segments: tuple[dict[str, AnyInfo], ...],
) -> int:
    if (
        StreamName == "Contents/Config-0"
        and OwnerText.startswith("moTransRefPlaneData_c")
        and OwnerText.endswith("inline transform row")
    ):
        ClassStart = next(
            (
                int(Segment["offset"])
                for Segment in Segments
                if Segment["kind"] == "definition"
                and Segment["class_name"] == "moTransRefPlaneData_c"
            )
        )
        return ClassStart + StartPos - 2470
    ShiftStart = KShiftStarts.get(StreamName)
    if ShiftStart is not None and StartPos >= ShiftStart:
        return StartPos + StreamShift
    return StartPos


# needed to keep reverse engineering responsibilities isolated and maintainable
def AddDirectFields(
    StreamName: str,
    Operations: list[tuple[int, int, str, str, AnyInfo]],
    Covered: set[int],
    StreamData: bytes,
    Segments: tuple[dict[str, AnyInfo], ...],
) -> None:
    StreamShift = len(StreamData) - KRefLengths[StreamName]
    for StartPos, FormatText, OwnerText in KDirectInfo[StreamName]:
        StartPos = FieldPosition(StreamName, StartPos, OwnerText, StreamShift, Segments)
        FieldWidth = Struct.calcsize("<" + FormatText)
        ValuesList = Struct.unpack_from("<" + FormatText, StreamData, StartPos)
        FieldValue: AnyInfo = ValuesList[0] if len(ValuesList) == 1 else ValuesList
        AddOpMut(
            Operations,
            Covered,
            StartPos,
            FieldWidth,
            OwnerText,
            "direct:" + FormatText,
            FieldValue,
        )
    StatusStream, StartPos, TextValues, OwnerText = KStatusField
    if StreamName != StatusStream:
        return
    StartPos = FieldPosition(StreamName, StartPos, OwnerText, StreamShift, Segments)
    FieldWidth = 2
    TextIndex = 0
    while TextIndex < len(TextValues):
        StringWidth = ReadString(StreamData, StartPos + FieldWidth)[1]
        FieldWidth += StringWidth
        TextIndex += 1
    AddOpMut(
        Operations, Covered, StartPos, FieldWidth, OwnerText, "stringlist", TextValues
    )


# needed to keep reverse engineering responsibilities isolated and maintainable
def AddPrimitives(
    Operations: list[tuple[int, int, str, str, AnyInfo]],
    Covered: set[int],
    StreamData: bytes,
    RowsList: tuple[tuple[str, int, str, int], ...],
) -> None:
    for TypeName, StartPos, OwnerText, StreamSpan in RowsList:
        FieldWidth = KPrimWidths[TypeName]
        if HasOverlap(Covered, StartPos, FieldWidth):
            continue
        FormatText = KPrimFormats[TypeName]
        FieldValue = Struct.unpack_from("<" + FormatText, StreamData, StartPos)[0]
        AddOpMut(
            Operations,
            Covered,
            StartPos,
            FieldWidth,
            OwnerText,
            "primitive:" + TypeName,
            FieldValue,
        )


# needed to keep reverse engineering responsibilities isolated and maintainable
def BuildProgram(
    StreamName: str,
    StreamData: bytes,
    Segments: tuple[dict[str, AnyInfo], ...],
    TraceData: tuple[tuple[str, int, str, int], ...],
) -> list[tuple[int, int, str, str, AnyInfo]]:
    RowsList = tuple(
        (RowData for RowData in TraceData if RowData[3] == len(StreamData))
    )
    Operations: list[tuple[int, int, str, str, AnyInfo]] = []
    Covered: set[int] = set()
    AddStructures(Operations, Covered, StreamData, Segments)
    AddDirectFields(StreamName, Operations, Covered, StreamData, Segments)
    AddStrings(Operations, Covered, StreamData, RowsList)
    AddPrimitives(Operations, Covered, StreamData, RowsList)
    Missing = sorted(set(range(len(StreamData))) - Covered)
    if Missing:
        raise ValueError(f"{StreamName} leaves bytes uncovered {Missing[:64]}")
    Operations.sort()
    return Operations


# needed to keep reverse engineering responsibilities isolated and maintainable
def RenderSource(Programs: dict[str, list[tuple[int, int, str, str, AnyInfo]]]) -> str:
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
    SourceLines.extend((f"    {OwnerText!r}," for OwnerText in OwnerNames))
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
            "PrimitiveFormats = " + repr(KPrimFormats),
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


# needed to keep reverse engineering responsibilities isolated and maintainable
def RunMain() -> int:
    Arguments = ParseArguments()
    Archive = SldprtArchive.open(Arguments.assembly)
    TraceText = Arguments.trace.read_text(encoding="utf-8", errors="replace")
    TraceData = TraceRows(TraceText)
    Programs: dict[str, list[tuple[int, int, str, str, AnyInfo]]] = {}
    RunLabel = Arguments.assembly.stem.casefold()
    for StreamName, SegmentLabel in KStreamSpecs:
        StreamData = Archive.require(StreamName)
        SegmentPath = Arguments.segments / f"segments_{RunLabel}_{SegmentLabel}.json"
        SegmentData = JsonData.loads(SegmentPath.read_text(encoding="utf-8"))
        Segments = tuple(SegmentData["segments"])
        Programs[StreamName] = BuildProgram(StreamName, StreamData, Segments, TraceData)
    Arguments.output.write_text(RenderSource(Programs), encoding="utf-8", newline="\n")
    print(
        JsonData.dumps(
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
