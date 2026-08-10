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
from convert.adapters.solidworks.format import CONFIGURATION_STREAM


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

# direct fields name compound values that bypass primitive archive helpers
DirectFields = (
    (0x09EE, "2d", "moTransRefPlaneData_c first inline transform row"),
    (0x0A02, "2d", "moTransRefPlaneData_c second inline transform row"),
    (0x4536, "3i", "moLengthUserUnits_c detail scalar triplet"),
    (0x456A, "3i", "moRelMgr_c detail scalar triplet"),
    (0x5E90, "IHH8B", "moSketchBlockMgr_c persistent identifier"),
)

# native status names are serialized as one counted semantic list
StatusField = (
    0x0E01,
    (
        "Description",
        "High Priority",
        "Low Priority",
        "Complete",
        "Reminder",
    ),
    "moRelMgr_c status-name table",
)


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


# trace parsing retains the exact native caller owning each primitive field
def TraceRows(TraceText: str) -> tuple[tuple[str, int, str], ...]:
    ResultRows: list[tuple[str, int, str]] = []
    for SourceLine in TraceText.splitlines():
        if not SourceLine.startswith("C "):
            continue
        PartsList = SourceLine.split()
        if len(PartsList) < 5 or PartsList[1] not in PrimitiveWidths:
            continue
        OwnerText = " ".join(PartsList[4:]).split(" (")[0]
        ResultRows.append((PartsList[1], int(PartsList[2], 16), OwnerText))
    return tuple(ResultRows)


# the selected trace record ties segmentation to the same reference part
def SelectSegments(SegmentData: Any) -> tuple[dict[str, Any], ...]:
    Records = SegmentData if isinstance(SegmentData, list) else (SegmentData,)
    for RecordData in Records:
        if str(RecordData.get("label", "")).casefold() == "baseline":
            return tuple(RecordData["segments"])
    if len(Records) == 1:
        return tuple(Records[0]["segments"])
    raise ValueError("Config-0 segmentation has no baseline record")


# archive object tags are structural vocabulary rather than anonymous bytes
def AddStructures(
    Operations: list[tuple[int, int, str, str, Any]],
    Covered: set[int],
    StreamData: bytes,
    Segments: tuple[dict[str, Any], ...],
) -> None:
    ClassUnits = int.from_bytes(StreamData[4:6], "little")
    ClassName = StreamData[6 : 6 + ClassUnits].decode("ascii")
    AddOperation(
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
    RowsList: tuple[tuple[str, int, str], ...],
) -> None:
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


# compound fields remain typed named values instead of residual byte spans
def AddDirectFields(
    Operations: list[tuple[int, int, str, str, Any]],
    Covered: set[int],
    StreamData: bytes,
) -> None:
    for StartPos, FormatText, OwnerText in DirectFields:
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
    StartPos, TextValues, OwnerText = StatusField
    FieldWidth = 2
    for TextValue in TextValues:
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
    RowsList: tuple[tuple[str, int, str], ...],
) -> None:
    for TypeName, StartPos, OwnerText in RowsList:
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


# generated source is readable typed vocabulary with no vendor byte spans
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
            "PrimitiveFormats = " + repr(PrimitiveFormats),
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


# full closure is mandatory before a generated program can enter production
def RunMain() -> int:
    Arguments = ParseArguments()
    Archive = SldprtArchive.open(Arguments.part)
    StreamData = Archive.require(CONFIGURATION_STREAM)
    TraceText = Arguments.trace.read_text(encoding="utf-8", errors="replace")
    SegmentData = json.loads(Arguments.segments.read_text(encoding="utf-8"))
    Segments = SelectSegments(SegmentData)
    RowsList = TraceRows(TraceText)
    Operations: list[tuple[int, int, str, str, Any]] = []
    Covered: set[int] = set()
    AddStructures(Operations, Covered, StreamData, Segments)
    AddDirectFields(Operations, Covered, StreamData)
    AddStrings(Operations, Covered, StreamData, RowsList)
    AddPrimitives(Operations, Covered, StreamData, RowsList)
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
