# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations as Annotations
from dataclasses import dataclass as Dataclass
import re as RegexLib
import struct as Struct
from typing import Iterable, Sequence

# this binding exists because shared behavior needs one stable value
KMagic = b"V5_CFV2\x00"

# this binding exists because shared behavior needs one stable value
KFolderMagic = b"CATIA_V5 CB0001\x00"

# this binding exists because shared behavior needs one stable value
KFolderEnd = b"CB__END"

# this binding exists because shared behavior needs one stable value
KOsmxMagic = b"OSMX"

# this binding exists because shared behavior needs one stable value
KMaxOsmxSymbols = 65536

# this binding exists because shared behavior needs one stable value
KMaxOsmxSymbolBytes = 16 * 1024 * 1024


# this definition exists because focused behavior needs one stable owner
class CfvTwoFormat(ValueError):
    KSlots = ()


# this definition exists because focused behavior needs one stable owner
class OsmxFormatError(ValueError):
    KSlots = ()


# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class CfvTwoExtent:
    locals().setdefault("__annotations__", {})
    __annotations__["physical_offset"] = "int"
    __annotations__["physical_length"] = "int"
    __annotations__["logical_offset"] = "int"
    __annotations__["flags"] = "int"


# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class CfvTwoStream:
    locals().setdefault("__annotations__", {})
    __annotations__["name"] = "str"
    __annotations__["logical_length"] = "int"
    __annotations__["descriptor_offset"] = "int"
    __annotations__["extents"] = "tuple[CfvTwoExtent, ...]"


# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class CfvTwoFolder:
    locals().setdefault("__annotations__", {})
    __annotations__["physical_base"] = "int"
    __annotations__["offset"] = "int"
    __annotations__["length"] = "int"
    __annotations__["streams"] = "tuple[CfvTwoStream, ...]"

    # this definition exists because focused behavior needs one stable owner
    def Stream(Instance, NameValue: str) -> CfvTwoStream | None:
        Matches = tuple(
            (ItemValue for ItemValue in Instance.streams if ItemValue.name == NameValue)
        )
        if not Matches:
            return None

        # this callback exists because local behavior needs one focused transformation
        Selected = max(Matches, key=lambda ItemValue: ItemValue.logical_length)
        if (
            sum(
                (
                    ItemValue.logical_length == Selected.logical_length
                    for ItemValue in Matches
                )
            )
            > 1
        ):
            raise CfvTwoFormat(f"ambiguous CFV2 stream {NameValue!r}")
        return Selected

    locals()["stream"] = Stream


# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class CfvTwoDecl:
    locals().setdefault("__annotations__", {})
    __annotations__["ordinal"] = "int"
    __annotations__["class_name"] = "str"
    __annotations__["base_class"] = "str"
    __annotations__["stream_name"] = "str"


# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class OsmxSymbol:
    locals().setdefault("__annotations__", {})
    __annotations__["index"] = "int"
    __annotations__["offset"] = "int"
    __annotations__["value"] = "str"


# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class OsmxArchive:
    locals().setdefault("__annotations__", {})
    __annotations__["data"] = "bytes"
    __annotations__["version"] = "str"
    __annotations__["symbol_table_offset"] = "int"
    __annotations__["symbol_data_offset"] = "int"
    __annotations__["symbols"] = "tuple[OsmxSymbol, ...]"

    # this definition exists because focused behavior needs one stable owner
    @classmethod
    def FromBytes(ClassType, Source: bytes | bytearray) -> OsmxArchive:
        DataValue = bytes(Source)
        if len(DataValue) < 104 or not DataValue.startswith(KOsmxMagic):
            raise OsmxFormatError("not an OSMX stream")
        SymbolTableOffset = Struct.unpack_from("<I", DataValue, 100)[0]
        if SymbolTableOffset < 104 or SymbolTableOffset + 8 > len(DataValue):
            raise OsmxFormatError("OSMX symbol table offset is outside the stream")
        if DataValue[SymbolTableOffset : SymbolTableOffset + 2] != b"|\x02":
            raise OsmxFormatError("OSMX symbol table marker is missing")
        SectionLength = Struct.unpack_from("<I", DataValue, SymbolTableOffset + 2)[0]
        if SectionLength != len(DataValue) - SymbolTableOffset:
            raise OsmxFormatError("OSMX symbol table length is inconsistent")
        Candidates, LimitExceeded = OsmxSymbolA(DataValue, SymbolTableOffset)
        if LimitExceeded and (not Candidates):
            raise OsmxFormatError("OSMX symbol table exceeds the safety limit")
        if len(Candidates) != 1:
            raise OsmxFormatError("OSMX symbol data boundary is ambiguous")
        SymbolDataOffset, SymbolCount = Candidates[0]
        Symbols = DecodeOsmx(DataValue, SymbolDataOffset, SymbolCount)
        Match = RegexLib.search(
            b"V5R\\d+(?:SP\\d+)?(?:HF\\d+)?", DataValue[:SymbolTableOffset]
        )
        Version = Match.group().decode("ascii") if Match else ""
        return ClassType(
            DataValue, Version, SymbolTableOffset, SymbolDataOffset, Symbols
        )

    # this definition exists because focused behavior needs one stable owner
    @property
    def Values(Instance) -> tuple[str, ...]:
        return tuple((Symbol.value for Symbol in Instance.symbols))

    # this definition exists because focused behavior needs one stable owner
    def FirstAfter(Instance, Value: str) -> OsmxSymbol | None:
        for Index, Symbol in enumerate(Instance.symbols[:-1]):
            if Symbol.value == Value:
                return Instance.symbols[Index + 1]
        return None

    locals()["first_after"] = FirstAfter
    locals()["from_bytes"] = FromBytes
    locals()["values"] = Values


# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class CfvTwoArchive:
    locals().setdefault("__annotations__", {})
    __annotations__["data"] = "bytes"
    __annotations__["outer"] = "CfvTwoFolder"
    __annotations__["nested"] = "tuple[CfvTwoFolder, ...]"

    # this definition exists because focused behavior needs one stable owner
    @classmethod
    def FromBytes(ClassType, Source: bytes | bytearray) -> CfvTwoArchive:
        DataValue = bytes(Source)
        if len(DataValue) < 16 or not DataValue.startswith(KMagic):
            raise CfvTwoFormat("not a V5_CFV2 container")
        OuterOffset, OuterLength = Struct.unpack_from(">II", DataValue, 8)
        if OuterOffset + OuterLength != len(DataValue):
            raise CfvTwoFormat("outer CFV2 directory does not end at EOF")
        Outer = ParseFolder(DataValue, 0, OuterOffset, OuterLength)
        Nested = FindNested(DataValue, Outer)
        return ClassType(DataValue, Outer, Nested)

    # this definition exists because focused behavior needs one stable owner
    def StreamBytes(
        Instance, Stream: Cfv2Stream, Folder: Cfv2Directory | None = None
    ) -> bytes:
        Selected = Folder or Instance.outer
        Payload = bytearray()
        Expected = 0
        for Extent in Stream.extents:
            if Extent.logical_offset != Expected:
                raise CfvTwoFormat("non-contiguous logical CFV2 extents")
            Start = Selected.physical_base + Extent.physical_offset
            EndValue = Start + Extent.physical_length
            if EndValue > len(Instance.data):
                raise CfvTwoFormat("CFV2 extent exceeds the file")
            Payload.extend(Instance.data[Start:EndValue])
            Expected += Extent.physical_length
        if Expected != Stream.logical_length:
            raise CfvTwoFormat("CFV2 logical stream length mismatch")
        return bytes(Payload)

    # this definition exists because focused behavior needs one stable owner
    def NamedStream(
        Instance, NameValue: str, Folder: Cfv2Directory | None = None
    ) -> bytes | None:
        Selected = Folder or Instance.outer
        Stream = Selected.stream(NameValue)
        return None if Stream is None else Instance.stream_bytes(Stream, Selected)

    # this definition exists because focused behavior needs one stable owner
    def Declarations(Instance) -> tuple[CfvTwoDecl, ...]:
        DataValue = Instance.named_stream("Data")
        if DataValue is None:
            return ()
        Names = {Stream.name for Stream in Instance.outer.streams}
        return Parse(DataValue, Names)

    locals()["declarations"] = Declarations
    locals()["from_bytes"] = FromBytes
    locals()["named_stream"] = NamedStream
    locals()["stream_bytes"] = StreamBytes


# this definition exists because focused behavior needs one stable owner
def BuildCfvTwo(Streams: Sequence[tuple[str, bytes]]) -> bytes:
    if not Streams:
        raise ValueError("a CFV2 container requires at least one stream")
    Names = [NameValue for NameValue, Ignored in Streams]
    if len(Names) != len(set(Names)):
        raise ValueError("CFV2 stream names must be unique")
    Offset = 16
    Payload = bytearray()
    Descriptors = bytearray(KFolderMagic)
    for NameValue, Value in Streams:
        DataValue = bytes(Value)
        ValidateStream(NameValue)
        if not DataValue:
            raise ValueError(f"CFV2 stream {NameValue!r} is empty")
        Payload.extend(DataValue)
        Descriptors.extend(BuildDescriptor(NameValue, Offset, len(DataValue)))
        Offset += len(DataValue)
    Descriptors.extend(KFolderEnd)
    Result = bytearray(KMagic)
    Result.extend(Struct.pack(">II", Offset, len(Descriptors)))
    Result.extend(Payload)
    Result.extend(Descriptors)
    Archive = CfvTwoArchive.from_bytes(Result)
    if tuple((Stream.name for Stream in Archive.outer.streams)) != tuple(Names):
        raise CfvTwoFormat("generated CFV2 directory failed validation")
    return bytes(Result)


# this definition exists because focused behavior needs one stable owner
def AppendCfvTwo(
    Source: bytes | bytearray, NameValue: str, Value: bytes | bytearray
) -> bytes:
    DataValue = bytes(Source)
    Payload = bytes(Value)
    ValidateStream(NameValue)
    if not Payload:
        raise ValueError(f"CFV2 stream {NameValue!r} is empty")
    Archive = CfvTwoArchive.from_bytes(DataValue)
    if any(
        (
            Stream.name == NameValue
            for Folder in (Archive.outer, *Archive.nested)
            for Stream in Folder.streams
        )
    ):
        raise ValueError(f"CFV2 stream {NameValue!r} already exists")
    FolderStart = Archive.outer.offset
    FolderEnd = FolderStart + Archive.outer.length
    Folder = DataValue[FolderStart:FolderEnd]
    Marker = Folder.rfind(KFolderEnd)
    if Marker < 0 or any(Folder[Marker + len(KFolderEnd) :]):
        raise CfvTwoFormat("CFV2 directory end marker is missing")
    Descriptor = BuildDescriptor(NameValue, FolderStart, len(Payload))
    ExtendedFolder = b"".join((Folder[:Marker], Descriptor, Folder[Marker:]))
    NewFolderStart = FolderStart + len(Payload)
    Result = bytearray(DataValue[:FolderStart])
    Result.extend(Payload)
    Result.extend(ExtendedFolder)
    Result[8:16] = Struct.pack(">II", NewFolderStart, len(ExtendedFolder))
    Generated = CfvTwoArchive.from_bytes(Result)
    OriginalStreams = tuple(
        (
            (Stream.name, Archive.stream_bytes(Stream, Archive.outer))
            for Stream in Archive.outer.streams
        )
    )
    RetainedStreams = tuple(
        (
            (Stream.name, Generated.stream_bytes(Stream, Generated.outer))
            for Stream in Generated.outer.streams
            if Stream.name != NameValue
        )
    )
    AddedStreams = tuple(
        (
            Generated.stream_bytes(Stream, Generated.outer)
            for Stream in Generated.outer.streams
            if Stream.name == NameValue
        )
    )
    if RetainedStreams != OriginalStreams or AddedStreams != (Payload,):
        raise CfvTwoFormat("extended CFV2 directory failed validation")
    return bytes(Result)


# this definition exists because focused behavior needs one stable owner
def BuildDecl(
    ClassName: str, BaseClass: str, StreamName: str, Ordinal: int = 2
) -> bytes:
    ValidateClass(ClassName)
    ValidateClass(BaseClass)
    Parts = StreamName.split("_")
    if len(Parts) != 3:
        raise ValueError("CFV2 declaration stream name must contain three words")
    try:
        Words = tuple((int(PartValue, 16) for PartValue in Parts))
    except ValueError as ErrorInfo:
        raise ValueError(
            "CFV2 declaration stream name is not hexadecimal"
        ) from ErrorInfo
    if any((Value < 0 or Value > 4294967295 for Value in Words)):
        raise ValueError("CFV2 declaration word exceeds 32 bits")
    DataValue = bytearray(40)
    DataValue[8:12] = b"\x01\x00\x03\x00"
    DataValue[12:16] = Struct.pack("<I", Ordinal)
    DataValue[16:24] = b"\x01\x00l\x00\x02\x00\x00\x00"
    DataValue[32:36] = b"\x02\x00\x81 "
    DataValue.extend(ClassName.encode("ascii") + b"\x00")
    DataValue.extend(BaseClass.encode("ascii") + b"\x00\x00")
    DataValue.extend(b"\x03\x00\xf7\x00\x03\x00\x00\x00")
    DataValue.extend(Struct.pack(">IIII", 1270622556, Words[0], Words[1], Words[2]))
    return bytes(DataValue)


# this definition exists because focused behavior needs one stable owner
def ExtractAscii(DataValue: bytes, Minimum: int = 4) -> tuple[str, ...]:
    Values: list[str] = []
    Start = 0
    for Index, Value in enumerate(DataValue + b"\x00"):
        if 32 <= Value <= 126:
            continue
        if Index - Start >= Minimum:
            Values.append(DataValue[Start:Index].decode("ascii"))
        Start = Index + 1
    return tuple(Values)


# this definition exists because focused behavior needs one stable owner
def ParseFolder(
    DataValue: bytes, PhysicalBase: int, Offset: int, Length: int
) -> CfvTwoFolder:
    if Length < len(KFolderMagic) + len(KFolderEnd):
        raise CfvTwoFormat("CFV2 directory is too short")
    EndValue = Offset + Length
    if EndValue > len(DataValue):
        raise CfvTwoFormat("CFV2 directory exceeds the file")
    Folder = DataValue[Offset:EndValue]
    if not Folder.startswith(KFolderMagic):
        raise CfvTwoFormat("CFV2 directory magic is missing")
    Marker = Folder.rfind(KFolderEnd)
    if Marker < 0 or any(Folder[Marker + len(KFolderEnd) :]):
        raise CfvTwoFormat("CFV2 directory end marker is missing")
    Sequential = ReadSequential(DataValue, Folder, PhysicalBase, Offset, Marker)
    if Sequential is not None:
        Result = CfvTwoFolder(PhysicalBase, Offset, Length, Sequential)
        ValidateExtent(Result)
        return Result
    Streams: list[CfvTwoStream] = []
    SeenOffsets: set[int] = set()
    for CountOffset in range(len(KFolderMagic), len(Folder) - 3):
        Count = UThreeTwobe(Folder, CountOffset)
        if Count < 1 or Count > 64:
            continue
        DescriptorOffset = CountOffset - 80
        if DescriptorOffset < 0 or DescriptorOffset in SeenOffsets:
            continue
        ExtentEnd = CountOffset + 4 + 20 * Count
        if ExtentEnd > len(Folder):
            continue
        LogicalLength = UThreeTwobe(Folder, DescriptorOffset + 12)
        LogicalOffset = 0
        Extents: list[CfvTwoExtent] = []
        Valid = LogicalLength > 0
        for Index in range(Count):
            AtValue = CountOffset + 4 + 20 * Index
            PhysicalOffset, PhysicalLength, LogicalLengthPart, StoredOffset, Flags = (
                Struct.unpack_from(">IIIII", Folder, AtValue)
            )
            PhysicalEnd = PhysicalBase + PhysicalOffset + PhysicalLength
            if (
                PhysicalLength == 0
                or PhysicalLength != LogicalLengthPart
                or StoredOffset != LogicalOffset
                or (PhysicalEnd > len(DataValue))
            ):
                Valid = False
                break
            Extents.append(
                CfvTwoExtent(PhysicalOffset, PhysicalLength, StoredOffset, Flags)
            )
            LogicalOffset += LogicalLengthPart
        if not Valid or LogicalOffset != LogicalLength:
            continue
        NameValue = DescriptorName(Folder, DescriptorOffset)
        if len(NameValue) < 3:
            continue
        Streams.append(
            CfvTwoStream(
                NameValue, LogicalLength, Offset + DescriptorOffset, tuple(Extents)
            )
        )
        SeenOffsets.add(DescriptorOffset)
    if not Streams:
        raise CfvTwoFormat("CFV2 directory has no valid stream descriptors")

    # this callback exists because local behavior needs one focused transformation
    Streams.sort(key=lambda Stream: Stream.descriptor_offset)
    Result = CfvTwoFolder(PhysicalBase, Offset, Length, tuple(Streams))
    ValidateExtent(Result)
    return Result


# this definition exists because focused behavior needs one stable owner
def ReadSequential(
    DataValue: bytes, Folder: bytes, PhysicalBase: int, FolderOffset: int, Marker: int
) -> tuple[CfvTwoStream, ...] | None:
    Cursor = len(KFolderMagic)
    Streams: list[CfvTwoStream] = []
    while Cursor < Marker:
        Count = UThreeTwobe(Folder, Cursor + 80)
        if Count < 1 or Count > 64:
            return None
        EndValue = Cursor + 84 + 20 * Count
        if EndValue > Marker:
            return None
        LogicalLength = UThreeTwobe(Folder, Cursor + 12)
        LogicalOffset = 0
        Extents: list[CfvTwoExtent] = []
        for Index in range(Count):
            AtValue = Cursor + 84 + 20 * Index
            PhysicalOffset, PhysicalLength, PartLength, StoredOffset, Flags = (
                Struct.unpack_from(">IIIII", Folder, AtValue)
            )
            if (
                PhysicalLength == 0
                or PhysicalLength != PartLength
                or StoredOffset != LogicalOffset
                or (PhysicalBase + PhysicalOffset + PhysicalLength > len(DataValue))
            ):
                return None
            Extents.append(
                CfvTwoExtent(PhysicalOffset, PhysicalLength, StoredOffset, Flags)
            )
            LogicalOffset += PartLength
        NameValue = SequentialName(Folder, Cursor)
        if LogicalOffset != LogicalLength or not NameValue:
            return None
        Streams.append(
            CfvTwoStream(
                NameValue, LogicalLength, FolderOffset + Cursor, tuple(Extents)
            )
        )
        Cursor = EndValue
    return tuple(Streams) if Cursor == Marker and Streams else None


# this definition exists because focused behavior needs one stable owner
def SequentialName(DataValue: bytes, Offset: int) -> str:
    Region = DataValue[Offset + 16 : Offset + 80]
    Value = bytearray()
    for Index in range(0, len(Region), 2):
        Character, HighValue = Region[Index : Index + 2]
        if Character == 0 and HighValue == 0:
            break
        if HighValue != 0 or not 32 <= Character <= 126:
            return ""
        Value.append(Character)
    try:
        NameValue = Value.decode("ascii")
    except UnicodeDecodeError:
        return ""
    return NameValue if 3 <= len(NameValue) <= 32 else ""


# this definition exists because focused behavior needs one stable owner
def ValidateExtent(Folder: Cfv2Directory) -> None:
    Ranges: list[tuple[int, int]] = []
    PayloadStart = Folder.physical_base + 16
    for Stream in Folder.streams:
        for Extent in Stream.extents:
            Start = Folder.physical_base + Extent.physical_offset
            EndValue = Start + Extent.physical_length
            if Start < PayloadStart or EndValue > Folder.offset:
                raise CfvTwoFormat("CFV2 extent is outside the payload region")
            Ranges.append((Start, EndValue))
    Ranges.sort()
    for Prior, Current in zip(Ranges, Ranges[1:]):
        if Current[0] < Prior[1]:
            raise CfvTwoFormat("CFV2 stream extents overlap")


# this definition exists because focused behavior needs one stable owner
def FindNested(DataValue: bytes, Folder: Cfv2Directory) -> tuple[CfvTwoFolder, ...]:
    Nested: list[CfvTwoFolder] = []
    SeenValue: set[int] = set()
    for Stream in Folder.streams:
        PhysicalRange = ContiguousRange(Folder, Stream)
        if PhysicalRange is None:
            continue
        Start, EndValue = PhysicalRange
        if Start in SeenValue or DataValue[Start : Start + len(KMagic)] != KMagic:
            continue
        SeenValue.add(Start)
        if Start + 16 > EndValue:
            raise CfvTwoFormat("nested CFV2 header exceeds its owning stream")
        Offset, Length = Struct.unpack_from(">II", DataValue, Start + 8)
        Absolute = Start + Offset
        if Absolute + Length != EndValue:
            raise CfvTwoFormat("nested CFV2 container does not fill its owning stream")
        Nested.append(ParseFolder(DataValue, Start, Absolute, Length))

    # this callback exists because local behavior needs one focused transformation
    Nested.sort(key=lambda Value: Value.physical_base)
    return tuple(Nested)


# this definition exists because focused behavior needs one stable owner
def ContiguousRange(
    Folder: Cfv2Directory, Stream: Cfv2Stream
) -> tuple[int, int] | None:

    # this callback exists because local behavior needs one focused transformation
    Extents = sorted(Stream.extents, key=lambda Extent: Extent.logical_offset)
    if not Extents:
        return None
    Ranges = tuple(
        (
            (
                Folder.physical_base + Extent.physical_offset,
                Folder.physical_base + Extent.physical_offset + Extent.physical_length,
            )
            for Extent in Extents
        )
    )
    if any((Current[0] != Prior[1] for Prior, Current in zip(Ranges, Ranges[1:]))):
        return None
    if sum((EndValue - Start for Start, EndValue in Ranges)) != Stream.logical_length:
        return None
    return (Ranges[0][0], Ranges[-1][1])


# this definition exists because focused behavior needs one stable owner
def DescriptorName(DataValue: bytes, Offset: int) -> str:
    Start = max(0, Offset - 40)
    EndValue = min(len(DataValue), Offset + 80)
    BestValue = b""
    Cursor = Start
    while Cursor + 1 < EndValue:
        RunValue = bytearray()
        AtValue = Cursor
        while (
            AtValue + 1 < EndValue
            and 32 <= DataValue[AtValue] <= 126
            and (DataValue[AtValue + 1] == 0)
        ):
            RunValue.append(DataValue[AtValue])
            AtValue += 2
        if len(RunValue) > len(BestValue):
            BestValue = bytes(RunValue)
        Cursor = AtValue if AtValue > Cursor else Cursor + 1
    return BestValue.decode("ascii")


# this definition exists because focused behavior needs one stable owner
def BuildDescriptor(NameValue: str, PhysicalOffset: int, Length: int) -> bytes:
    if Length <= 0 or Length > 4294967295:
        raise ValueError("CFV2 stream length is outside the 32-bit range")
    DataValue = bytearray(84)
    DataValue[12:16] = Struct.pack(">I", Length)
    Encoded = NameValue.encode("utf-16le")
    DataValue[16 : 16 + len(Encoded)] = Encoded
    DataValue[80:84] = Struct.pack(">I", 1)
    DataValue.extend(Struct.pack(">IIIII", PhysicalOffset, Length, Length, 0, 0))
    return bytes(DataValue)


# this definition exists because focused behavior needs one stable owner
def Parse(DataValue: bytes, StreamNames: set[str]) -> tuple[CfvTwoDecl, ...]:
    Terminal = b"\x03\x00\xf7\x00\x03\x00\x00\x00"
    Results: list[CfvTwoDecl] = []
    for Start in range(max(0, len(DataValue) - 63)):
        if (
            DataValue[Start + 8 : Start + 12] != b"\x01\x00\x03\x00"
            or DataValue[Start + 16 : Start + 24] != b"\x01\x00l\x00\x02\x00\x00\x00"
            or DataValue[Start + 32 : Start + 36] != b"\x02\x00\x81 "
        ):
            continue
        StringsStart = Start + 40
        TerminalAt = DataValue.find(
            Terminal, StringsStart, min(len(DataValue), StringsStart + 192)
        )
        if TerminalAt < 0:
            continue
        Values = DataValue[StringsStart:TerminalAt].split(b"\x00")
        Names = tuple((Value.decode("ascii") for Value in Values if Value))
        if len(Names) != 2:
            continue
        UuidAt = TerminalAt + len(Terminal)
        if UuidAt + 16 > len(DataValue):
            continue
        Ignored, First, Middle, LastValue = Struct.unpack_from(
            ">IIII", DataValue, UuidAt
        )
        Canonical = f"{First:x}_{Middle:08x}_{LastValue:x}"
        Selected = Canonical if Canonical in StreamNames else f"_{Canonical}"
        if Selected not in StreamNames:
            continue
        Results.append(
            CfvTwoDecl(
                Struct.unpack_from("<I", DataValue, Start + 12)[0],
                Names[0],
                Names[1],
                Selected,
            )
        )
    if len({Value.stream_name for Value in Results}) != len(Results):
        raise CfvTwoFormat("CFV2 declarations select duplicate streams")
    return tuple(Results)


# this definition exists because focused behavior needs one stable owner
def ValidateStream(NameValue: str) -> None:
    if (
        not 3 <= len(NameValue) <= 32
        or not NameValue.isascii()
        or (not NameValue.isprintable())
    ):
        raise ValueError("CFV2 stream names must be 3-32 printable ASCII characters")


# this definition exists because focused behavior needs one stable owner
def ValidateClass(NameValue: str) -> None:
    if (
        not NameValue
        or not NameValue.isascii()
        or (
            not all(
                (Character.isalnum() or Character == "_" for Character in NameValue)
            )
        )
    ):
        raise ValueError("CFV2 class names must be ASCII identifiers")


# this definition exists because focused behavior needs one stable owner
def OsmxSymbolA(
    DataValue: bytes, SymbolTableOffset: int
) -> tuple[tuple[tuple[int, int], ...], bool]:
    Results: list[tuple[int, int]] = []
    LimitExceeded = False
    Start = SymbolTableOffset + 6
    StopValue = min(SymbolTableOffset + 16, len(DataValue))
    for SymbolDataOffset in range(Start, StopValue):
        Cursor = SymbolDataOffset
        SymbolCount = 0
        SymbolBytes = 0
        Valid = True
        while Cursor < len(DataValue):
            StoredLength = DataValue[Cursor]
            ValueOffset = Cursor + 1
            ValueLength = StoredLength - 1
            ValueEnd = ValueOffset + ValueLength
            SymbolCount += 1
            SymbolBytes += ValueLength
            if SymbolCount > KMaxOsmxSymbols or SymbolBytes > KMaxOsmxSymbolBytes:
                LimitExceeded = True
                Valid = False
                break
            if (
                StoredLength == 0
                or ValueEnd > len(DataValue)
                or any(
                    (
                        DataValue[Index] < 32 or DataValue[Index] > 126
                        for Index in range(ValueOffset, ValueEnd)
                    )
                )
            ):
                Valid = False
                break
            Cursor = ValueEnd
        if Valid and Cursor == len(DataValue) and SymbolCount:
            Results.append((SymbolDataOffset, SymbolCount))
    return (tuple(Results), LimitExceeded)


# this definition exists because focused behavior needs one stable owner
def DecodeOsmx(
    DataValue: bytes, SymbolDataOffset: int, SymbolCount: int
) -> tuple[OsmxSymbol, ...]:
    Cursor = SymbolDataOffset
    Symbols: list[OsmxSymbol] = []
    for Index in range(SymbolCount):
        StoredLength = DataValue[Cursor]
        ValueOffset = Cursor + 1
        ValueEnd = ValueOffset + StoredLength - 1
        Symbols.append(
            OsmxSymbol(
                Index, ValueOffset, DataValue[ValueOffset:ValueEnd].decode("ascii")
            )
        )
        Cursor = ValueEnd
    if Cursor != len(DataValue):
        raise OsmxFormatError("OSMX symbol table decode is incomplete")
    return tuple(Symbols)


# this definition exists because focused behavior needs one stable owner
def UThreeTwobe(DataValue: bytes, Offset: int) -> int:
    if Offset < 0 or Offset + 4 > len(DataValue):
        return -1
    return Struct.unpack_from(">I", DataValue, Offset)[0]


# this definition exists because focused behavior needs one stable owner
def StreamItems(
    Archive: Cfv2Archive, Folder: Cfv2Directory
) -> Iterable[tuple[str, bytes]]:
    for Stream in Folder.streams:
        yield (Stream.name, Archive.stream_bytes(Stream, Folder))


# this binding exists because shared behavior needs one stable value
globals()["Cfv2Archive"] = CfvTwoArchive

# this binding exists because shared behavior needs one stable value
globals()["Cfv2Declaration"] = CfvTwoDecl

# this binding exists because shared behavior needs one stable value
globals()["Cfv2Directory"] = CfvTwoFolder

# this binding exists because shared behavior needs one stable value
globals()["Cfv2Extent"] = CfvTwoExtent

# this binding exists because shared behavior needs one stable value
globals()["Cfv2FormatError"] = CfvTwoFormat

# this binding exists because shared behavior needs one stable value
globals()["Cfv2Stream"] = CfvTwoStream

# this binding exists because shared behavior needs one stable value
globals()["DIRECTORY_END"] = KFolderEnd

# this binding exists because shared behavior needs one stable value
globals()["DIRECTORY_MAGIC"] = KFolderMagic

# this binding exists because shared behavior needs one stable value
globals()["MAGIC"] = KMagic

# this binding exists because shared behavior needs one stable value
globals()["OSMX_MAGIC"] = KOsmxMagic

# this binding exists because shared behavior needs one stable value
globals()["_MAX_OSMX_SYMBOLS"] = KMaxOsmxSymbols

# this binding exists because shared behavior needs one stable value
globals()["_MAX_OSMX_SYMBOL_BYTES"] = KMaxOsmxSymbolBytes

# this binding exists because shared behavior needs one stable value
globals()["_contiguous_stream_range"] = ContiguousRange

# this binding exists because shared behavior needs one stable value
globals()["_decode_osmx_symbols"] = DecodeOsmx

# this binding exists because shared behavior needs one stable value
globals()["_descriptor"] = BuildDescriptor

# this binding exists because shared behavior needs one stable value
globals()["_descriptor_name"] = DescriptorName

# this binding exists because shared behavior needs one stable value
globals()["_nested_directories"] = FindNested

# this binding exists because shared behavior needs one stable value
globals()["_osmx_symbol_candidates"] = OsmxSymbolA

# this binding exists because shared behavior needs one stable value
globals()["_parse_declarations"] = Parse

# this binding exists because shared behavior needs one stable value
globals()["_parse_directory"] = ParseFolder

# this binding exists because shared behavior needs one stable value
globals()["_sequential_name"] = SequentialName

# this binding exists because shared behavior needs one stable value
globals()["_sequential_streams"] = ReadSequential

# this binding exists because shared behavior needs one stable value
globals()["_u32be"] = UThreeTwobe

# this binding exists because shared behavior needs one stable value
globals()["_validate_class_name"] = ValidateClass

# this binding exists because shared behavior needs one stable value
globals()["_validate_extent_layout"] = ValidateExtent

# this binding exists because shared behavior needs one stable value
globals()["_validate_stream_name"] = ValidateStream

# this binding exists because shared behavior needs one stable value
globals()["annotations"] = Annotations

# this binding exists because shared behavior needs one stable value
globals()["append_cfv2_stream"] = AppendCfvTwo

# this binding exists because shared behavior needs one stable value
globals()["build_cfv2"] = BuildCfvTwo

# this binding exists because shared behavior needs one stable value
globals()["build_declaration"] = BuildDecl

# this binding exists because shared behavior needs one stable value
globals()["dataclass"] = Dataclass

# this binding exists because shared behavior needs one stable value
globals()["extract_ascii_values"] = ExtractAscii

# this binding exists because shared behavior needs one stable value
globals()["re"] = RegexLib

# this binding exists because shared behavior needs one stable value
globals()["stream_items"] = StreamItems

# this binding exists because shared behavior needs one stable value
globals()["struct"] = Struct
