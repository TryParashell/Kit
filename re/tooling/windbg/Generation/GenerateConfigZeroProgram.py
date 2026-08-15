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
from black import FileMode as BlackMode
from black import format_str as FormatBlack
from convert.adapters.solidworks.container.Archive import EncodeString, ReadString
from convert.adapters.solidworks.container.Container import SldprtArchive
from convert.adapters.solidworks.container.Format import (
    CONFIGURATION_STREAM as ConfigStream,
)

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
KDirectInfo = (
    (2542, "2d", "moTransRefPlaneData_c first inline transform row"),
    (2562, "2d", "moTransRefPlaneData_c second inline transform row"),
    (17718, "3i", "moLengthUserUnits_c detail scalar triplet"),
    (17770, "3i", "moRelMgr_c detail scalar triplet"),
    (24208, "IHH8B", "moSketchBlockMgr_c persistent identifier"),
)

# needed to keep reverse engineering responsibilities isolated and maintainable
KDirectFields = (
    (2542, "2d", "moTransRefPlaneData_c first inline transform row"),
    (2562, "2d", "moTransRefPlaneData_c second inline transform row"),
    (17750, "3i", "moLengthUserUnits_c detail scalar triplet"),
    (17802, "3i", "moRelMgr_c detail scalar triplet"),
    (24240, "IHH8B", "moSketchBlockMgr_c persistent identifier"),
)

# needed to keep reverse engineering responsibilities isolated and maintainable
KStatusNames = ("Description", "High Priority", "Low Priority", "Complete", "Reminder")

# needed to keep reverse engineering responsibilities isolated and maintainable
KRefOffset = 44

# needed to keep reverse engineering responsibilities isolated and maintainable
KRefWidth = 4 + len("Part70".encode("utf-16le"))


# needed to keep reverse engineering responsibilities isolated and maintainable
def ParseArguments() -> Argparse.Namespace:
    Parser = Argparse.ArgumentParser()
    Parser.add_argument("part", type=PathInfo)
    Parser.add_argument("trace", type=PathInfo)
    Parser.add_argument("segments", type=PathInfo)
    Parser.add_argument("output", type=PathInfo)

    # needed to keep reverse engineering responsibilities isolated and maintainable
    Parser.add_argument("--range-start", type=lambda Value: int(Value, 0))

    # needed to keep reverse engineering responsibilities isolated and maintainable
    Parser.add_argument("--range-end", type=lambda Value: int(Value, 0))
    Parser.add_argument(
        "--profile", choices=("baseline", "dimensioned-box"), default="baseline"
    )
    Parser.add_argument("--fixed", action="store_true")
    return Parser.parse_args()


# needed to keep reverse engineering responsibilities isolated and maintainable
def ValueLiteral(TypeName: str, FieldValue: AnyInfo) -> str:
    if TypeName in {"float", "double"}:
        return f"float.fromhex({float(FieldValue).hex()!r})"
    return repr(FieldValue)


# needed to keep reverse engineering responsibilities isolated and maintainable
def FormatSource(SourceText: str) -> str:
    return FormatBlack(SourceText, mode=BlackMode())


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
def TraceRows(TraceText: str) -> tuple[tuple[str, int, str], ...]:
    ResultRows: list[tuple[str, int, str]] = []
    for SourceLine in TraceText.splitlines():
        if not SourceLine.startswith(("C ", "F ")):
            continue
        PartsList = SourceLine.split()
        if len(PartsList) < 5 or PartsList[1] not in KPrimWidths:
            continue
        OwnerText = " ".join(PartsList[4:]).split(" (")[0]
        ResultRows.append((PartsList[1], int(PartsList[2], 16), OwnerText))
    return tuple(ResultRows)


# needed to keep reverse engineering responsibilities isolated and maintainable
def SelectSegments(SegmentData: AnyInfo) -> tuple[dict[str, AnyInfo], ...]:
    Records = SegmentData if isinstance(SegmentData, list) else (SegmentData,)
    for RecordData in Records:
        if str(RecordData.get("label", "")).casefold() == "baseline":
            return tuple(RecordData["segments"])
    if len(Records) == 1:
        return tuple(Records[0]["segments"])
    raise ValueError("Config-0 segmentation has no baseline record")


# needed to keep reverse engineering responsibilities isolated and maintainable
def AddStructures(
    Operations: list[tuple[int, int, str, str, AnyInfo]],
    Covered: set[int],
    StreamData: bytes,
    Segments: tuple[dict[str, AnyInfo], ...],
) -> None:
    ClassUnits = int.from_bytes(StreamData[4:6], "little")
    ClassName = StreamData[6 : 6 + ClassUnits].decode("ascii")
    AddOpMut(
        Operations,
        Covered,
        0,
        6 + ClassUnits,
        "su_CArchive::ReadClass",
        "definition",
        (ClassName, int.from_bytes(StreamData[2:4], "little")),
    )
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
    RowsList: tuple[tuple[str, int, str], ...],
) -> None:
    StringStarts = {
        StartPos
        for TypeName, StartPos, OwnerText in RowsList
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
def AddDirectFields(
    Operations: list[tuple[int, int, str, str, AnyInfo]],
    Covered: set[int],
    StreamData: bytes,
    ProfileName: str,
) -> None:
    PartName, PartNameWidth = ReadString(StreamData, KRefOffset)
    OffsetDelta = PartNameWidth - KRefWidth
    ProfileFields = KDirectFields if ProfileName == "dimensioned-box" else KDirectInfo
    for StartPos, FormatText, OwnerText in ProfileFields:
        StartPos += OffsetDelta
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
    StatusData = Struct.pack("<H", len(KStatusNames)) + b"".join(
        (EncodeString(TextValue) for TextValue in KStatusNames)
    )
    StartPos = StreamData.find(StatusData)
    if StartPos < 0 or StreamData.find(StatusData, StartPos + 1) >= 0:
        raise ValueError("Config-0 status-name table is absent or ambiguous")
    AddOpMut(
        Operations,
        Covered,
        StartPos,
        len(StatusData),
        "moRelMgr_c status-name table",
        "stringlist",
        KStatusNames,
    )


# needed to keep reverse engineering responsibilities isolated and maintainable
def AddPrimitives(
    Operations: list[tuple[int, int, str, str, AnyInfo]],
    Covered: set[int],
    StreamData: bytes,
    RowsList: tuple[tuple[str, int, str], ...],
) -> None:
    for TypeName, StartPos, OwnerText in RowsList:
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
def RenderSource(
    Operations: list[tuple[int, int, str, str, AnyInfo]], StreamLength: int
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
    SourceLines.extend((f"    {OwnerText!r}," for OwnerText in OwnerNames))
    SourceLines.extend(
        [
            ")",
            "",
            "# source offsets let dynamic emission preserve proven field order",
            "ConfigOps = (",
        ]
    )
    for StartPos, FieldWidth, OwnerText, KindName, FieldValue in Operations:
        if KindName.startswith("primitive:"):
            TypeName = KindName.split(":", 1)[1]
            ValueText = ValueLiteral(TypeName, FieldValue)
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
            "PrimitiveFormats = " + repr(KPrimFormats),
            "",
            "# recovered boundaries isolate the only two variable-sized record regions",
            "ReferenceLength = " + str(StreamLength),
            "PartNameOffset = 0x2C",
            "SecondUnitStart = 0x34A",
            "SecondUnitEnd = 0x38C",
            "AtomStart = 0xB3A",
            "AtomEnd = 0xB9C",
            "HighWaterOffsets = (0x6085, 0x6089)",
            "AtomClassIndex = 57",
            "AtomLinkStamp = 42358",
            "",
            "",
            "# each field operation serializes one recovered value through its typed contract",
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
            "    raise SldprtFormatError(f'unknown Config-0 operation {KindName!r}')",
            "",
            "",
            "# one semantic atom links a native configuration item to a feature-tree object",
            "def EncodeAtom(AtomId: int, TreeId: int, SessionStamp: int, Position: int, IsLast: bool, Generation: int) -> bytes:",
            "    if not 0 <= AtomId <= 0xFFFFFFFF or not 0 <= TreeId <= 0xFFFFFFFF:",
            "        raise SldprtFormatError('Config-0 atom identifiers must fit in 32 bits')",
            "    OutputData = bytearray()",
            "    if Position:",
            "        OutputData.extend(encode_class_reference(AtomClassIndex))",
            "    OutputData.extend(struct.pack('<H4i', 0, 1, 0x40000000, -1, 0))",
            "    OutputData.extend(encode_string(''))",
            "    OutputData.extend(struct.pack('<iH', 0, 0))",
            "    RecordValues = (0, AtomId, 0 if Position == 0 else 1, TreeId, TreeId, 0, 0, 0, SessionStamp, -1, AtomLinkStamp, SessionStamp, AtomLinkStamp, 6)",
            "    OutputData.extend(struct.pack('<H14i', 0, *RecordValues))",
            "    if IsLast:",
            "        OutputData.extend(struct.pack('<III', Generation, 10000, 0x10000000))",
            "    return bytes(OutputData)",
            "",
            "",
            "# dynamic configuration generation replays every typed field in original order",
            "def EncodeProgram(",
            "    PartName: str = 'Part70',",
            "    Atoms: tuple[tuple[int, int], ...] = ((101, 32),),",
            "    SessionStamp: int = 1,",
            "    Generation: int = 18000,",
            "    DualLengthUnits: bool = True,",
            "    HighWater: tuple[int, int] = (101, 103),",
            "    Overrides: Mapping[int, Any] | None = None,",
            ") -> bytes:",
            "    if not Atoms:",
            "        raise SldprtFormatError('Contents/Config-0 needs at least one atom record')",
            "    if Generation != 18000:",
            "        raise SldprtFormatError(f'Contents/Config-0 fields are recovered at generation 18000, {Generation} was requested')",
            "    FieldOverrides = dict(Overrides or {})",
            "    FieldOverrides[PartNameOffset] = PartName",
            "    FieldOverrides[HighWaterOffsets[0]] = HighWater[0]",
            "    FieldOverrides[HighWaterOffsets[1]] = HighWater[1]",
            "    OutputData = bytearray()",
            "    SourceCursor = 0",
            "    AtomsWritten = False",
            "    for StartPos, FieldWidth, OwnerIndex, KindName, DefaultValue in ConfigOps:",
            "        if StartPos != SourceCursor:",
            "            raise SldprtFormatError(f'Config-0 field program drifted at {StartPos}')",
            "        SourceCursor += FieldWidth",
            "        if not DualLengthUnits and SecondUnitStart <= StartPos < SecondUnitEnd:",
            "            continue",
            "        if AtomStart <= StartPos < AtomEnd:",
            "            if not AtomsWritten:",
            "                for Position, (AtomId, TreeId) in enumerate(Atoms):",
            "                    OutputData.extend(EncodeAtom(AtomId, TreeId, SessionStamp, Position, Position == len(Atoms) - 1, Generation))",
            "                AtomsWritten = True",
            "            continue",
            "        FieldValue = FieldOverrides.get(StartPos, DefaultValue)",
            "        FieldData = EncodeField(KindName, FieldValue)",
            "        if StartPos != PartNameOffset and len(FieldData) != FieldWidth:",
            "            raise SldprtFormatError(f'Config-0 field width changed at {StartPos}')",
            "        OutputData.extend(FieldData)",
            "    if SourceCursor != ReferenceLength or not AtomsWritten:",
            "        raise SldprtFormatError('Config-0 field program did not close its source')",
            "    return bytes(OutputData)",
            "",
        ]
    )
    return "\n".join(SourceLines)


# needed to keep reverse engineering responsibilities isolated and maintainable
def FixedSourceInfo(
    Operations: list[tuple[int, int, str, str, AnyInfo]], StreamLength: int
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
        "from typing import Any",
        "",
        "from .config0_program import EncodeField",
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
            "# source offsets preserve the exact fixed topology field order",
            "ConfigOps = (",
        ]
    )
    for StartPos, FieldWidth, OwnerText, KindName, FieldValue in Operations:
        if KindName.startswith("primitive:"):
            TypeName = KindName.split(":", 1)[1]
            ValueText = ValueLiteral(TypeName, FieldValue)
        else:
            ValueText = repr(FieldValue)
        SourceLines.append(
            f"    ({StartPos}, {FieldWidth}, {OwnerIndex[OwnerText]}, {KindName!r}, {ValueText}),"
        )
    SourceLines.extend(
        [
            ")",
            "",
            "# exact closure proves the fixed program accounts for the complete stream",
            f"ReferenceLength = {StreamLength}",
            "",
            "",
            "# typed replay emits the fixed configuration without retaining vendor byte spans",
            "def EncodeProgram(Overrides: Mapping[int, Any] | None = None) -> bytes:",
            "    FieldOverrides = dict(Overrides or {})",
            "    OutputData = bytearray()",
            "    SourceCursor = 0",
            "    for StartPos, FieldWidth, OwnerIndex, KindName, DefaultValue in ConfigOps:",
            "        if StartPos != SourceCursor:",
            "            raise SldprtFormatError(f'Config-0 field program drifted at {StartPos}')",
            "        FieldValue = FieldOverrides.get(StartPos, DefaultValue)",
            "        FieldData = EncodeField(KindName, FieldValue)",
            "        if len(FieldData) != FieldWidth:",
            "            raise SldprtFormatError(f'Config-0 field width changed at {StartPos}')",
            "        OutputData.extend(FieldData)",
            "        SourceCursor += FieldWidth",
            "    if SourceCursor != ReferenceLength or len(OutputData) != ReferenceLength:",
            "        raise SldprtFormatError('Config-0 field program did not close its source')",
            "    return bytes(OutputData)",
            "",
        ]
    )
    return "\n".join(SourceLines)


# needed to keep reverse engineering responsibilities isolated and maintainable
def RangeSourceInfo(
    Operations: list[tuple[int, int, str, str, AnyInfo]], RangeStart: int, RangeEnd: int
) -> str:
    SelectedOperations = [
        Operation for Operation in Operations if RangeStart <= Operation[0] < RangeEnd
    ]
    OwnerNames = tuple(sorted({Operation[2] for Operation in SelectedOperations}))
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
        "from .config0_program import EncodeField",
        "from .container import SldprtFormatError",
        "",
        "",
        "# recovered callsites make every annotation field traceable to its native serializer",
        "FieldOwners = (",
    ]
    SourceLines.extend((f"    {OwnerText!r}," for OwnerText in OwnerNames))
    SourceLines.extend(
        [
            ")",
            "",
            "# relative offsets preserve the two-view annotation manager's complete typed order",
            "AnnotationOps = (",
        ]
    )
    for StartPos, FieldWidth, OwnerText, KindName, FieldValue in SelectedOperations:
        if KindName.startswith("primitive:"):
            TypeName = KindName.split(":", 1)[1]
            ValueText = ValueLiteral(TypeName, FieldValue)
        else:
            ValueText = repr(FieldValue)
        SourceLines.append(
            f"    ({StartPos - RangeStart}, {FieldWidth}, {OwnerIndex[OwnerText]}, {KindName!r}, {ValueText}),"
        )
    SourceLines.extend(
        [
            ")",
            "",
            "# the source interval records where the reusable manager was observed",
            f"SourceRange = ({RangeStart}, {RangeEnd})",
            "",
            "# exact closure rejects any future field-width or ordering drift",
            f"ReferenceLength = {RangeEnd - RangeStart}",
            "",
            "",
            "# typed field replay emits the two-view manager without retaining vendor byte spans",
            "def EncodeTwoViewAnnotationManager() -> bytes:",
            "    OutputData = bytearray()",
            "    SourceCursor = 0",
            "    for StartPos, FieldWidth, OwnerIndex, KindName, FieldValue in AnnotationOps:",
            "        if StartPos != SourceCursor:",
            "            raise SldprtFormatError(f'annotation field program drifted at {StartPos}')",
            "        FieldData = EncodeField(KindName, FieldValue)",
            "        if len(FieldData) != FieldWidth:",
            "            raise SldprtFormatError(f'annotation field width changed at {StartPos}')",
            "        OutputData.extend(FieldData)",
            "        SourceCursor += FieldWidth",
            "    if SourceCursor != ReferenceLength:",
            "        raise SldprtFormatError('annotation field program did not close its source')",
            "    return bytes(OutputData)",
            "",
        ]
    )
    return "\n".join(SourceLines)


# needed to keep reverse engineering responsibilities isolated and maintainable
def FinishMainMut(
    Arguments, Covered, Operations, RowsList, Segments, StreamData
) -> int:
    AddStructures(Operations, Covered, StreamData, Segments)
    AddDirectFields(Operations, Covered, StreamData, Arguments.profile)
    AddStrings(Operations, Covered, StreamData, RowsList)
    AddPrimitives(Operations, Covered, StreamData, RowsList)
    if Arguments.range_start is not None:
        RangeStart = Arguments.range_start
        RangeEnd = Arguments.range_end
        if not 0 <= RangeStart < RangeEnd <= len(StreamData):
            raise ValueError("Config-0 generation range exceeds the source stream")
        MissingRange = sorted(set(range(RangeStart, RangeEnd)) - Covered)
        if MissingRange:
            raise ValueError(
                f"Config-0 range field program leaves bytes uncovered {MissingRange}"
            )
        Operations.sort()
        Arguments.output.write_text(
            FormatSource(RangeSourceInfo(Operations, RangeStart, RangeEnd)),
            encoding="utf-8",
            newline="\n",
        )
        print(
            JsonData.dumps(
                {
                    "stream_bytes": RangeEnd - RangeStart,
                    "operations": sum(
                        (
                            RangeStart <= Operation[0] < RangeEnd
                            for Operation in Operations
                        )
                    ),
                    "owners": len(
                        {
                            Operation[2]
                            for Operation in Operations
                            if RangeStart <= Operation[0] < RangeEnd
                        }
                    ),
                    "missing": 0,
                },
                indent=2,
            )
        )
        return 0
    Missing = sorted(set(range(len(StreamData))) - Covered)
    if Missing:
        RunsList: list[tuple[int, int]] = []
        for Position in Missing:
            if not RunsList or Position != RunsList[-1][1]:
                RunsList.append((Position, Position + 1))
            else:
                RunsList[-1] = (RunsList[-1][0], Position + 1)
        raise ValueError(f"Config-0 field program leaves ranges uncovered {RunsList}")
    Operations.sort()
    Arguments.output.write_text(
        FormatSource(
            FixedSourceInfo(Operations, len(StreamData))
            if Arguments.fixed
            else RenderSource(Operations, len(StreamData))
        ),
        encoding="utf-8",
        newline="\n",
    )
    print(
        JsonData.dumps(
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


# needed to keep reverse engineering responsibilities isolated and maintainable
def RunMain() -> int:
    Arguments = ParseArguments()
    if (Arguments.range_start is None) != (Arguments.range_end is None):
        raise ValueError("Config-0 range generation needs both range boundaries")
    Archive = SldprtArchive.open(Arguments.part)
    StreamData = Archive.require(ConfigStream)
    TraceText = Arguments.trace.read_text(encoding="utf-8", errors="replace")
    SegmentData = JsonData.loads(Arguments.segments.read_text(encoding="utf-8"))
    Segments = SelectSegments(SegmentData)
    RowsList = TraceRows(TraceText)
    Operations: list[tuple[int, int, str, str, AnyInfo]] = []
    Covered: set[int] = set()
    return FinishMainMut(Arguments, Covered, Operations, RowsList, Segments, StreamData)


if __name__ == "__main__":
    raise SystemExit(RunMain())
