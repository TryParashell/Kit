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
from convert.adapters.solidworks.format import RESOLVED_FEATURES_STREAM


# primitive widths keep debugger reads aligned with their archive contracts
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

# recovered class names anchor direct fields that bypass primitive archive helpers
SketchChainClassName = "moSketchChain_c"
BoundingBoxClassName = "moBBoxCenterData_c"
ComponentEdgeClassName = "moCompEdge_c"
# chamfer records finish with counted surface identifiers written without primitive helpers
ChamferClassName = "Chamfer_c"
# linear and angular display dimensions share the recovered direct-index layout
DisplayDimensionClassNames = frozenset(
    {
        "moDisplayDim_c",
        "moDisplayDistanceDim_c",
        "moDisplayAngularDim_c",
        "moDisplayRadialDim_c",
    }
)

# payload-relative direct offsets survive both class definitions and compact class references
BoundingBoxIndexPayloadOffset = 46
# every recovered display-dimension family places its direct index at this payload offset
DisplayDimensionIndexPayloadOffsets = {
    "moDisplayDistanceDim_c": 526,
    "moDisplayAngularDim_c": 526,
    "moDisplayRadialDim_c": 526,
}
# derived display dimensions read a composite direct slot before their index field
DisplayDimensionDirectSlotPayloadOffset = 522

# fillet component-edge buckets store a counted direct array after their fixed payload
ComponentEdgeCountPayloadOffset = 62


# command arguments keep program generation reproducible across workstations
def ParseArguments() -> argparse.Namespace:
    Parser = argparse.ArgumentParser()
    Parser.add_argument("part", type=Path)
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


# trace parsing retains the exact caller that owns every primitive field
def TraceRows(TraceText: str) -> tuple[tuple[str, int, str], ...]:
    ResultRows: list[tuple[str, int, str]] = []
    for SourceLine in TraceText.splitlines():
        if not SourceLine.startswith("F "):
            continue
        PartsList = SourceLine.split()
        if len(PartsList) < 5 or PartsList[1] not in PrimitiveWidths:
            continue
        OwnerText = " ".join(PartsList[4:]).split(" (")[0]
        ResultRows.append((PartsList[1], int(PartsList[2], 16), OwnerText))
    return tuple(ResultRows)


# structural archive operations replace raw tag and string framing bytes
def AddStructures(
    Operations: list[tuple[int, int, str, str, Any]],
    Covered: set[int],
    StreamData: bytes,
    Segments: tuple[dict[str, Any], ...],
    RowsList: tuple[tuple[str, int, str], ...],
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
    StringStarts = {
        StartPos
        for TypeName, StartPos, OwnerText in RowsList
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


# matching class segments provide structural anchors instead of donor offsets
def ClassSegments(
    Segments: tuple[dict[str, Any], ...],
    ClassName: str,
) -> tuple[dict[str, Any], ...]:
    MatchesList = tuple(
        Segment for Segment in Segments if Segment.get("class_name") == ClassName
    )
    if not MatchesList:
        raise ValueError(f"resolved field program expected {ClassName} segments")
    return MatchesList


# direct field discovery derives typed locations from class and feature structure
def DirectFields(
    StreamData: bytes,
    Segments: tuple[dict[str, Any], ...],
) -> tuple[tuple[int, str, str], ...]:
    SketchSegments = ClassSegments(Segments, SketchChainClassName)
    BoundingSegments = ClassSegments(Segments, BoundingBoxClassName)
    ComponentEdgeSegments = tuple(
        Segment
        for Segment in Segments
        if Segment.get("class_name") == ComponentEdgeClassName
    )
    ChamferSegments = tuple(
        Segment for Segment in Segments if Segment.get("class_name") == ChamferClassName
    )
    DisplaySegments = tuple(
        Segment
        for Segment in Segments
        if Segment.get("class_name") in DisplayDimensionClassNames
    )
    if not DisplaySegments:
        raise ValueError(
            "resolved field program expected a supported display dimension segment"
        )
    DirectList: list[tuple[int, str, str]] = [(0, "I", "archive continuation base")]
    for SketchIndex, SketchSegment in enumerate(SketchSegments, start=1):
        SketchStart = int(SketchSegment["offset"]) + int(SketchSegment["header"])
        FirstCount = struct.unpack_from("<H", StreamData, SketchStart)[0]
        FirstStart = SketchStart + 2
        SecondCountOffset = FirstStart + FirstCount * 4
        SecondCount = struct.unpack_from("<H", StreamData, SecondCountOffset)[0]
        SecondStart = SecondCountOffset + 2
        if FirstCount < 1 or SecondCount < 1:
            raise ValueError(
                "resolved field program direct layout requires populated sketch "
                f"chains at sketch {SketchIndex}"
            )
        DirectList.extend(
            (
                (
                    FirstStart,
                    f"{FirstCount}i",
                    f"sketch {SketchIndex} first chain entity indices",
                ),
                (
                    SecondStart,
                    f"{SecondCount}i",
                    f"sketch {SketchIndex} second chain entity indices",
                ),
            )
        )
    for BoxIndex, BoundingSegment in enumerate(BoundingSegments, start=1):
        DirectList.append(
            (
                int(BoundingSegment["offset"])
                + int(BoundingSegment["header"])
                + BoundingBoxIndexPayloadOffset,
                "i",
                f"bounding box {BoxIndex} per body chooser index",
            )
        )
    for DimensionIndex, DisplaySegment in enumerate(DisplaySegments, start=1):
        DisplayChildren = tuple(
            Segment
            for Segment in Segments
            if Segment.get("parent") == DisplaySegment.get("index")
            and Segment.get("kind") == "null"
            and int(Segment["end"]) - int(Segment["offset"]) == 42
        )
        if len(DisplayChildren) != 1:
            raise ValueError(
                "resolved field program direct layout requires one derived scalar "
                f"at display dimension {DimensionIndex}"
            )
        DisplayClassName = str(DisplaySegment["class_name"])
        DisplayPayloadStart = int(DisplaySegment["offset"]) + int(
            DisplaySegment["header"]
        )
        if DisplayClassName == "moDisplayDim_c":
            DisplayIndexPayloadOffset = (
                526 if int(DisplaySegment["header"]) > 2 else 522
            )
        else:
            DisplayIndexPayloadOffset = DisplayDimensionIndexPayloadOffsets[
                DisplayClassName
            ]
            DirectList.append(
                (
                    DisplayPayloadStart + DisplayDimensionDirectSlotPayloadOffset,
                    "I",
                    f"display dimension {DimensionIndex} direct slot",
                )
            )
        DirectList.extend(
            (
                (
                    DisplayPayloadStart + DisplayIndexPayloadOffset,
                    "H",
                    f"display dimension {DimensionIndex} index",
                ),
                (
                    int(DisplayChildren[0]["offset"]) + 30,
                    "d",
                    f"display dimension {DimensionIndex} derived scalar",
                ),
            )
        )
    for EdgeIndex, ComponentSegment in enumerate(ComponentEdgeSegments, start=1):
        BucketChildren = tuple(
            Segment
            for Segment in Segments
            if Segment.get("parent") == ComponentSegment.get("index")
            and Segment.get("kind") == "null"
            and int(Segment["end"]) - int(Segment["offset"]) >= 64
        )
        for BucketIndex, BucketSegment in enumerate(BucketChildren, start=1):
            CountOffset = int(BucketSegment["offset"]) + ComponentEdgeCountPayloadOffset
            CountValue = struct.unpack_from("<H", StreamData, CountOffset)[0]
            ValuesOffset = CountOffset + 2
            if CountValue and ValuesOffset + CountValue * 4 <= int(
                BucketSegment["end"]
            ):
                DirectList.append(
                    (
                        ValuesOffset,
                        f"{CountValue}i",
                        f"component edge {EdgeIndex} bucket {BucketIndex} indices",
                    )
                )
    for ChamferIndex, ChamferSegment in enumerate(ChamferSegments, start=1):
        ChamferChildren = tuple(
            Segment
            for Segment in Segments
            if Segment.get("parent") == ChamferSegment.get("index")
            and Segment.get("kind") == "null"
            and int(Segment["end"]) - int(Segment["offset"]) >= 8
        )
        for ChildIndex, ChildSegment in enumerate(ChamferChildren, start=1):
            ChildOffset = int(ChildSegment["offset"])
            ChildEnd = int(ChildSegment["end"])
            CountValue = struct.unpack_from("<H", StreamData, ChildOffset + 6)[0]
            ValuesOffset = ChildOffset + 8
            if CountValue and ValuesOffset + CountValue * 4 == ChildEnd:
                DirectList.append(
                    (
                        ValuesOffset,
                        f"{CountValue}i",
                        f"chamfer {ChamferIndex} child {ChildIndex} surface identifiers",
                    )
                )
    return tuple(DirectList)


# direct arrays remain typed and named instead of becoming residual byte spans
def AddDirectFields(
    Operations: list[tuple[int, int, str, str, Any]],
    Covered: set[int],
    StreamData: bytes,
    Segments: tuple[dict[str, Any], ...],
) -> None:
    for StartPos, FormatText, OwnerText in DirectFields(StreamData, Segments):
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


# primitive operations expose all remaining fields by serializer callsite
def AddPrimitives(
    Operations: list[tuple[int, int, str, str, Any]],
    Covered: set[int],
    StreamData: bytes,
    RowsList: tuple[tuple[str, int, str], ...],
) -> None:
    for TypeName, StartPos, OwnerText in RowsList:
        FieldWidth = PrimitiveWidths[TypeName]
        if (
            StartPos < 0
            or StartPos + FieldWidth > len(StreamData)
            or HasOverlap(Covered, StartPos, FieldWidth)
        ):
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


# generated source is readable vocabulary rather than encoded vendor payload
def RenderSource(
    Operations: list[tuple[int, int, str, str, Any]],
    StreamLength: int,
) -> str:
    OwnerNames = tuple(sorted({Operation[2] for Operation in Operations}))
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
            "# the resolved field program contains typed values and no vendor byte spans",
            "ResolvedOps = (",
        ]
    )
    for StartPos, FieldWidth, OwnerText, KindName, FieldValue in Operations:
        if KindName.startswith("primitive:"):
            TypeName = KindName.split(":", 1)[1]
            ValueText = ValueLiteral(TypeName, FieldValue)
        elif KindName.startswith("direct:") and isinstance(FieldValue, tuple):
            ValueText = repr(FieldValue)
        else:
            ValueText = repr(FieldValue)
        SourceLines.append(
            f"    ({StartPos}, {FieldWidth}, {OwnerIndex[OwnerText]}, {KindName!r}, {ValueText}),"
        )
    SourceLines.extend(
        [
            ")",
            "",
            "# primitive formats keep signed and floating fields faithful to their reader",
            "PrimitiveFormats = " + repr(PrimitiveFormats),
            "",
            "",
            "# callers can replace semantic fields while retaining recovered object framing",
            "def EncodeProgram(Overrides: Mapping[int, Any] | None = None) -> bytes:",
            "    FieldOverrides = Overrides or {}",
            "    OutputData = bytearray()",
            "    for StartPos, FieldWidth, OwnerIndex, KindName, DefaultValue in ResolvedOps:",
            "        if len(OutputData) != StartPos:",
            "            raise SldprtFormatError(f'resolved field program drifted at {StartPos}')",
            "        FieldValue = FieldOverrides.get(StartPos, DefaultValue)",
            "        if KindName == 'definition':",
            "            ClassName, SchemaCode = FieldValue",
            "            FieldData = encode_class_definition(ClassName, SchemaCode)",
            "        elif KindName == 'classref':",
            "            FieldData = encode_class_reference(FieldValue)",
            "        elif KindName == 'objectref':",
            "            FieldData = encode_object_reference(FieldValue)",
            "        elif KindName == 'null':",
            "            FieldData = struct.pack('<H', 0)",
            "        elif KindName == 'string':",
            "            FieldData = encode_string(FieldValue)",
            "        elif KindName.startswith('primitive:'):",
            "            TypeName = KindName.split(':', 1)[1]",
            "            FieldData = struct.pack('<' + PrimitiveFormats[TypeName], FieldValue)",
            "        elif KindName.startswith('direct:'):",
            "            FormatText = KindName.split(':', 1)[1]",
            "            ValuesList = FieldValue if isinstance(FieldValue, tuple) else (FieldValue,)",
            "            FieldData = struct.pack('<' + FormatText, *ValuesList)",
            "        else:",
            "            raise SldprtFormatError(f'unknown resolved operation {KindName!r}')",
            "        if len(FieldData) != FieldWidth:",
            "            raise SldprtFormatError(f'resolved field width changed at {StartPos}')",
            "        OutputData.extend(FieldData)",
            f"    if len(OutputData) != {StreamLength}:",
            "        raise SldprtFormatError('resolved field program length changed')",
            "    return bytes(OutputData)",
            "",
        ]
    )
    return "\n".join(SourceLines)


# full coverage is required before a generated program can enter production
def RunMain() -> int:
    Arguments = ParseArguments()
    Archive = SldprtArchive.open(Arguments.part)
    StreamData = Archive.require(RESOLVED_FEATURES_STREAM)
    TraceText = Arguments.trace.read_text(encoding="utf-8", errors="replace")
    SegmentData = json.loads(Arguments.segments.read_text(encoding="utf-8"))
    Segments = tuple(SegmentData["segments"])
    RowsList = TraceRows(TraceText)
    Operations: list[tuple[int, int, str, str, Any]] = []
    Covered: set[int] = set()
    AddStructures(Operations, Covered, StreamData, Segments, RowsList)
    AddDirectFields(Operations, Covered, StreamData, Segments)
    AddPrimitives(Operations, Covered, StreamData, RowsList)
    Missing = sorted(set(range(len(StreamData))) - Covered)
    if Missing:
        raise ValueError(
            f"resolved field program leaves bytes uncovered {Missing[:32]}"
        )
    Operations.sort()
    Arguments.output.write_text(
        RenderSource(Operations, len(StreamData)),
        encoding="utf-8",
        newline="\n",
    )
    print(
        json.dumps(
            {
                "stream_bytes": len(StreamData),
                "operations": len(Operations),
                "owners": len({Operation[2] for Operation in Operations}),
                "missing": len(Missing),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(RunMain())
