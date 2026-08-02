from __future__ import annotations

from dataclasses import dataclass
import re
import struct
from typing import Iterable, Sequence


MAGIC = b"V5_CFV2\x00"
DIRECTORY_MAGIC = b"CATIA_V5 CB0001\x00"
DIRECTORY_END = b"CB__END"
OSMX_MAGIC = b"OSMX"
_MAX_OSMX_SYMBOLS = 65_536
_MAX_OSMX_SYMBOL_BYTES = 16 * 1024 * 1024


class Cfv2FormatError(ValueError):
    __slots__ = ()


class OsmxFormatError(ValueError):
    __slots__ = ()


@dataclass(frozen=True, slots=True)
class Cfv2Extent:
    physical_offset: int
    physical_length: int
    logical_offset: int
    flags: int


@dataclass(frozen=True, slots=True)
class Cfv2Stream:
    name: str
    logical_length: int
    descriptor_offset: int
    extents: tuple[Cfv2Extent, ...]


@dataclass(frozen=True, slots=True)
class Cfv2Directory:
    physical_base: int
    offset: int
    length: int
    streams: tuple[Cfv2Stream, ...]

    def stream(self, name: str) -> Cfv2Stream | None:
        matches = tuple(item for item in self.streams if item.name == name)
        if not matches:
            return None
        selected = max(matches, key=lambda item: item.logical_length)
        if sum(item.logical_length == selected.logical_length for item in matches) > 1:
            raise Cfv2FormatError(f"ambiguous CFV2 stream {name!r}")
        return selected


@dataclass(frozen=True, slots=True)
class Cfv2Declaration:
    ordinal: int
    class_name: str
    base_class: str
    stream_name: str


@dataclass(frozen=True, slots=True)
class OsmxSymbol:
    index: int
    offset: int
    value: str


@dataclass(frozen=True, slots=True)
class OsmxArchive:
    data: bytes
    version: str
    symbol_table_offset: int
    symbol_data_offset: int
    symbols: tuple[OsmxSymbol, ...]

    @classmethod
    def from_bytes(cls, source: bytes | bytearray) -> OsmxArchive:
        data = bytes(source)
        if len(data) < 0x68 or not data.startswith(OSMX_MAGIC):
            raise OsmxFormatError("not an OSMX stream")
        symbol_table_offset = struct.unpack_from("<I", data, 0x64)[0]
        if symbol_table_offset < 0x68 or symbol_table_offset + 8 > len(data):
            raise OsmxFormatError("OSMX symbol table offset is outside the stream")
        if data[symbol_table_offset : symbol_table_offset + 2] != b"\x7c\x02":
            raise OsmxFormatError("OSMX symbol table marker is missing")
        section_length = struct.unpack_from("<I", data, symbol_table_offset + 2)[0]
        if section_length != len(data) - symbol_table_offset:
            raise OsmxFormatError("OSMX symbol table length is inconsistent")
        candidates, limit_exceeded = _osmx_symbol_candidates(data, symbol_table_offset)
        if limit_exceeded and not candidates:
            raise OsmxFormatError("OSMX symbol table exceeds the safety limit")
        if len(candidates) != 1:
            raise OsmxFormatError("OSMX symbol data boundary is ambiguous")
        symbol_data_offset, symbol_count = candidates[0]
        symbols = _decode_osmx_symbols(data, symbol_data_offset, symbol_count)
        match = re.search(rb"V5R\d+(?:SP\d+)?(?:HF\d+)?", data[:symbol_table_offset])
        version = match.group().decode("ascii") if match else ""
        return cls(
            data,
            version,
            symbol_table_offset,
            symbol_data_offset,
            symbols,
        )

    @property
    def values(self) -> tuple[str, ...]:
        return tuple(symbol.value for symbol in self.symbols)

    def first_after(self, value: str) -> OsmxSymbol | None:
        for index, symbol in enumerate(self.symbols[:-1]):
            if symbol.value == value:
                return self.symbols[index + 1]
        return None


@dataclass(frozen=True, slots=True)
class Cfv2Archive:
    data: bytes
    outer: Cfv2Directory
    nested: tuple[Cfv2Directory, ...]

    @classmethod
    def from_bytes(cls, source: bytes | bytearray) -> Cfv2Archive:
        data = bytes(source)
        if len(data) < 16 or not data.startswith(MAGIC):
            raise Cfv2FormatError("not a V5_CFV2 container")
        outer_offset, outer_length = struct.unpack_from(">II", data, 8)
        if outer_offset + outer_length != len(data):
            raise Cfv2FormatError("outer CFV2 directory does not end at EOF")
        outer = _parse_directory(data, 0, outer_offset, outer_length)
        nested = _nested_directories(data, outer)
        return cls(data, outer, nested)

    def stream_bytes(
        self, stream: Cfv2Stream, directory: Cfv2Directory | None = None
    ) -> bytes:
        selected = directory or self.outer
        payload = bytearray()
        expected = 0
        for extent in stream.extents:
            if extent.logical_offset != expected:
                raise Cfv2FormatError("non-contiguous logical CFV2 extents")
            start = selected.physical_base + extent.physical_offset
            end = start + extent.physical_length
            if end > len(self.data):
                raise Cfv2FormatError("CFV2 extent exceeds the file")
            payload.extend(self.data[start:end])
            expected += extent.physical_length
        if expected != stream.logical_length:
            raise Cfv2FormatError("CFV2 logical stream length mismatch")
        return bytes(payload)

    def named_stream(
        self, name: str, directory: Cfv2Directory | None = None
    ) -> bytes | None:
        selected = directory or self.outer
        stream = selected.stream(name)
        return None if stream is None else self.stream_bytes(stream, selected)

    def declarations(self) -> tuple[Cfv2Declaration, ...]:
        data = self.named_stream("Data")
        if data is None:
            return ()
        names = {stream.name for stream in self.outer.streams}
        return _parse_declarations(data, names)


def build_cfv2(streams: Sequence[tuple[str, bytes]]) -> bytes:
    if not streams:
        raise ValueError("a CFV2 container requires at least one stream")
    names = [name for name, _ in streams]
    if len(names) != len(set(names)):
        raise ValueError("CFV2 stream names must be unique")
    offset = 16
    payload = bytearray()
    descriptors = bytearray(DIRECTORY_MAGIC)
    for name, value in streams:
        data = bytes(value)
        _validate_stream_name(name)
        if not data:
            raise ValueError(f"CFV2 stream {name!r} is empty")
        payload.extend(data)
        descriptors.extend(_descriptor(name, offset, len(data)))
        offset += len(data)
    descriptors.extend(DIRECTORY_END)
    result = bytearray(MAGIC)
    result.extend(struct.pack(">II", offset, len(descriptors)))
    result.extend(payload)
    result.extend(descriptors)
    archive = Cfv2Archive.from_bytes(result)
    if tuple(stream.name for stream in archive.outer.streams) != tuple(names):
        raise Cfv2FormatError("generated CFV2 directory failed validation")
    return bytes(result)


def append_cfv2_stream(
    source: bytes | bytearray, name: str, value: bytes | bytearray
) -> bytes:
    data = bytes(source)
    payload = bytes(value)
    _validate_stream_name(name)
    if not payload:
        raise ValueError(f"CFV2 stream {name!r} is empty")
    archive = Cfv2Archive.from_bytes(data)
    if any(
        stream.name == name
        for directory in (archive.outer, *archive.nested)
        for stream in directory.streams
    ):
        raise ValueError(f"CFV2 stream {name!r} already exists")
    directory_start = archive.outer.offset
    directory_end = directory_start + archive.outer.length
    directory = data[directory_start:directory_end]
    marker = directory.rfind(DIRECTORY_END)
    if marker < 0 or any(directory[marker + len(DIRECTORY_END) :]):
        raise Cfv2FormatError("CFV2 directory end marker is missing")
    descriptor = _descriptor(name, directory_start, len(payload))
    extended_directory = b"".join(
        (directory[:marker], descriptor, directory[marker:])
    )
    new_directory_start = directory_start + len(payload)
    result = bytearray(data[:directory_start])
    result.extend(payload)
    result.extend(extended_directory)
    result[8:16] = struct.pack(
        ">II", new_directory_start, len(extended_directory)
    )
    generated = Cfv2Archive.from_bytes(result)
    original_streams = tuple(
        (stream.name, archive.stream_bytes(stream, archive.outer))
        for stream in archive.outer.streams
    )
    retained_streams = tuple(
        (stream.name, generated.stream_bytes(stream, generated.outer))
        for stream in generated.outer.streams
        if stream.name != name
    )
    added_streams = tuple(
        generated.stream_bytes(stream, generated.outer)
        for stream in generated.outer.streams
        if stream.name == name
    )
    if retained_streams != original_streams or added_streams != (payload,):
        raise Cfv2FormatError("extended CFV2 directory failed validation")
    return bytes(result)


def build_declaration(
    class_name: str, base_class: str, stream_name: str, ordinal: int = 2
) -> bytes:
    _validate_class_name(class_name)
    _validate_class_name(base_class)
    parts = stream_name.split("_")
    if len(parts) != 3:
        raise ValueError("CFV2 declaration stream name must contain three words")
    try:
        words = tuple(int(part, 16) for part in parts)
    except ValueError as exc:
        raise ValueError("CFV2 declaration stream name is not hexadecimal") from exc
    if any(value < 0 or value > 0xFFFFFFFF for value in words):
        raise ValueError("CFV2 declaration word exceeds 32 bits")
    data = bytearray(40)
    data[8:12] = b"\x01\x00\x03\x00"
    data[12:16] = struct.pack("<I", ordinal)
    data[16:24] = b"\x01\x00\x6c\x00\x02\x00\x00\x00"
    data[32:36] = b"\x02\x00\x81\x20"
    data.extend(class_name.encode("ascii") + b"\x00")
    data.extend(base_class.encode("ascii") + b"\x00\x00")
    data.extend(b"\x03\x00\xf7\x00\x03\x00\x00\x00")
    data.extend(struct.pack(">IIII", 0x4BBC295C, words[0], words[1], words[2]))
    return bytes(data)


def extract_ascii_values(data: bytes, minimum: int = 4) -> tuple[str, ...]:
    values: list[str] = []
    start = 0
    for index, value in enumerate(data + b"\x00"):
        if 0x20 <= value <= 0x7E:
            continue
        if index - start >= minimum:
            values.append(data[start:index].decode("ascii"))
        start = index + 1
    return tuple(values)


def _parse_directory(
    data: bytes, physical_base: int, offset: int, length: int
) -> Cfv2Directory:
    if length < len(DIRECTORY_MAGIC) + len(DIRECTORY_END):
        raise Cfv2FormatError("CFV2 directory is too short")
    end = offset + length
    if end > len(data):
        raise Cfv2FormatError("CFV2 directory exceeds the file")
    directory = data[offset:end]
    if not directory.startswith(DIRECTORY_MAGIC):
        raise Cfv2FormatError("CFV2 directory magic is missing")
    marker = directory.rfind(DIRECTORY_END)
    if marker < 0 or any(directory[marker + len(DIRECTORY_END) :]):
        raise Cfv2FormatError("CFV2 directory end marker is missing")
    sequential = _sequential_streams(
        data,
        directory,
        physical_base,
        offset,
        marker,
    )
    if sequential is not None:
        result = Cfv2Directory(physical_base, offset, length, sequential)
        _validate_extent_layout(result)
        return result
    streams: list[Cfv2Stream] = []
    seen_offsets: set[int] = set()
    for count_offset in range(len(DIRECTORY_MAGIC), len(directory) - 3):
        count = _u32be(directory, count_offset)
        if count < 1 or count > 64:
            continue
        descriptor_offset = count_offset - 0x50
        if descriptor_offset < 0 or descriptor_offset in seen_offsets:
            continue
        extent_end = count_offset + 4 + 20 * count
        if extent_end > len(directory):
            continue
        logical_length = _u32be(directory, descriptor_offset + 0x0C)
        logical_offset = 0
        extents: list[Cfv2Extent] = []
        valid = logical_length > 0
        for index in range(count):
            at = count_offset + 4 + 20 * index
            (
                physical_offset,
                physical_length,
                logical_length_part,
                stored_offset,
                flags,
            ) = struct.unpack_from(">IIIII", directory, at)
            physical_end = physical_base + physical_offset + physical_length
            if (
                physical_length == 0
                or physical_length != logical_length_part
                or stored_offset != logical_offset
                or physical_end > len(data)
            ):
                valid = False
                break
            extents.append(
                Cfv2Extent(
                    physical_offset,
                    physical_length,
                    stored_offset,
                    flags,
                )
            )
            logical_offset += logical_length_part
        if not valid or logical_offset != logical_length:
            continue
        name = _descriptor_name(directory, descriptor_offset)
        if len(name) < 3:
            continue
        streams.append(
            Cfv2Stream(
                name,
                logical_length,
                offset + descriptor_offset,
                tuple(extents),
            )
        )
        seen_offsets.add(descriptor_offset)
    if not streams:
        raise Cfv2FormatError("CFV2 directory has no valid stream descriptors")
    streams.sort(key=lambda stream: stream.descriptor_offset)
    result = Cfv2Directory(physical_base, offset, length, tuple(streams))
    _validate_extent_layout(result)
    return result


def _sequential_streams(
    data: bytes,
    directory: bytes,
    physical_base: int,
    directory_offset: int,
    marker: int,
) -> tuple[Cfv2Stream, ...] | None:
    cursor = len(DIRECTORY_MAGIC)
    streams: list[Cfv2Stream] = []
    while cursor < marker:
        count = _u32be(directory, cursor + 0x50)
        if count < 1 or count > 64:
            return None
        end = cursor + 0x54 + 20 * count
        if end > marker:
            return None
        logical_length = _u32be(directory, cursor + 0x0C)
        logical_offset = 0
        extents: list[Cfv2Extent] = []
        for index in range(count):
            at = cursor + 0x54 + 20 * index
            physical_offset, physical_length, part_length, stored_offset, flags = (
                struct.unpack_from(">IIIII", directory, at)
            )
            if (
                physical_length == 0
                or physical_length != part_length
                or stored_offset != logical_offset
                or physical_base + physical_offset + physical_length > len(data)
            ):
                return None
            extents.append(
                Cfv2Extent(
                    physical_offset,
                    physical_length,
                    stored_offset,
                    flags,
                )
            )
            logical_offset += part_length
        name = _sequential_name(directory, cursor)
        if logical_offset != logical_length or not name:
            return None
        streams.append(
            Cfv2Stream(
                name,
                logical_length,
                directory_offset + cursor,
                tuple(extents),
            )
        )
        cursor = end
    return tuple(streams) if cursor == marker and streams else None


def _sequential_name(data: bytes, offset: int) -> str:
    region = data[offset + 0x10 : offset + 0x50]
    value = bytearray()
    for index in range(0, len(region), 2):
        character, high = region[index : index + 2]
        if character == 0 and high == 0:
            break
        if high != 0 or not 0x20 <= character <= 0x7E:
            return ""
        value.append(character)
    try:
        name = value.decode("ascii")
    except UnicodeDecodeError:
        return ""
    return name if 3 <= len(name) <= 32 else ""


def _validate_extent_layout(directory: Cfv2Directory) -> None:
    ranges: list[tuple[int, int]] = []
    payload_start = directory.physical_base + 16
    for stream in directory.streams:
        for extent in stream.extents:
            start = directory.physical_base + extent.physical_offset
            end = start + extent.physical_length
            if start < payload_start or end > directory.offset:
                raise Cfv2FormatError("CFV2 extent is outside the payload region")
            ranges.append((start, end))
    ranges.sort()
    for prior, current in zip(ranges, ranges[1:]):
        if current[0] < prior[1]:
            raise Cfv2FormatError("CFV2 stream extents overlap")


def _nested_directories(
    data: bytes, directory: Cfv2Directory
) -> tuple[Cfv2Directory, ...]:
    nested: list[Cfv2Directory] = []
    seen: set[int] = set()
    for stream in directory.streams:
        physical_range = _contiguous_stream_range(directory, stream)
        if physical_range is None:
            continue
        start, end = physical_range
        if start in seen or data[start : start + len(MAGIC)] != MAGIC:
            continue
        seen.add(start)
        if start + 16 > end:
            raise Cfv2FormatError("nested CFV2 header exceeds its owning stream")
        offset, length = struct.unpack_from(">II", data, start + 8)
        absolute = start + offset
        if absolute + length != end:
            raise Cfv2FormatError(
                "nested CFV2 container does not fill its owning stream"
            )
        nested.append(_parse_directory(data, start, absolute, length))
    nested.sort(key=lambda value: value.physical_base)
    return tuple(nested)


def _contiguous_stream_range(
    directory: Cfv2Directory, stream: Cfv2Stream
) -> tuple[int, int] | None:
    extents = sorted(stream.extents, key=lambda extent: extent.logical_offset)
    if not extents:
        return None
    ranges = tuple(
        (
            directory.physical_base + extent.physical_offset,
            directory.physical_base + extent.physical_offset + extent.physical_length,
        )
        for extent in extents
    )
    if any(current[0] != prior[1] for prior, current in zip(ranges, ranges[1:])):
        return None
    if sum(end - start for start, end in ranges) != stream.logical_length:
        return None
    return ranges[0][0], ranges[-1][1]


def _descriptor_name(data: bytes, offset: int) -> str:
    start = max(0, offset - 40)
    end = min(len(data), offset + 0x50)
    best = b""
    cursor = start
    while cursor + 1 < end:
        run = bytearray()
        at = cursor
        while at + 1 < end and 0x20 <= data[at] <= 0x7E and data[at + 1] == 0:
            run.append(data[at])
            at += 2
        if len(run) > len(best):
            best = bytes(run)
        cursor = at if at > cursor else cursor + 1
    return best.decode("ascii")


def _descriptor(name: str, physical_offset: int, length: int) -> bytes:
    if length <= 0 or length > 0xFFFFFFFF:
        raise ValueError("CFV2 stream length is outside the 32-bit range")
    data = bytearray(0x54)
    data[0x0C:0x10] = struct.pack(">I", length)
    encoded = name.encode("utf-16le")
    data[0x10 : 0x10 + len(encoded)] = encoded
    data[0x50:0x54] = struct.pack(">I", 1)
    data.extend(struct.pack(">IIIII", physical_offset, length, length, 0, 0))
    return bytes(data)


def _parse_declarations(
    data: bytes, stream_names: set[str]
) -> tuple[Cfv2Declaration, ...]:
    terminal = b"\x03\x00\xf7\x00\x03\x00\x00\x00"
    results: list[Cfv2Declaration] = []
    for start in range(max(0, len(data) - 63)):
        if (
            data[start + 8 : start + 12] != b"\x01\x00\x03\x00"
            or data[start + 16 : start + 24] != b"\x01\x00\x6c\x00\x02\x00\x00\x00"
            or data[start + 32 : start + 36] != b"\x02\x00\x81\x20"
        ):
            continue
        strings_start = start + 40
        terminal_at = data.find(
            terminal, strings_start, min(len(data), strings_start + 192)
        )
        if terminal_at < 0:
            continue
        values = data[strings_start:terminal_at].split(b"\x00")
        names = tuple(value.decode("ascii") for value in values if value)
        if len(names) != 2:
            continue
        uuid_at = terminal_at + len(terminal)
        if uuid_at + 16 > len(data):
            continue
        _, first, middle, last = struct.unpack_from(">IIII", data, uuid_at)
        canonical = f"{first:x}_{middle:08x}_{last:x}"
        selected = canonical if canonical in stream_names else f"_{canonical}"
        if selected not in stream_names:
            continue
        results.append(
            Cfv2Declaration(
                struct.unpack_from("<I", data, start + 12)[0],
                names[0],
                names[1],
                selected,
            )
        )
    if len({value.stream_name for value in results}) != len(results):
        raise Cfv2FormatError("CFV2 declarations select duplicate streams")
    return tuple(results)


def _validate_stream_name(name: str) -> None:
    if not 3 <= len(name) <= 32 or not name.isascii() or not name.isprintable():
        raise ValueError("CFV2 stream names must be 3-32 printable ASCII characters")


def _validate_class_name(name: str) -> None:
    if (
        not name
        or not name.isascii()
        or not all(character.isalnum() or character == "_" for character in name)
    ):
        raise ValueError("CFV2 class names must be ASCII identifiers")


def _osmx_symbol_candidates(
    data: bytes, symbol_table_offset: int
) -> tuple[tuple[tuple[int, int], ...], bool]:
    results: list[tuple[int, int]] = []
    limit_exceeded = False
    start = symbol_table_offset + 6
    stop = min(symbol_table_offset + 16, len(data))
    for symbol_data_offset in range(start, stop):
        cursor = symbol_data_offset
        symbol_count = 0
        symbol_bytes = 0
        valid = True
        while cursor < len(data):
            stored_length = data[cursor]
            value_offset = cursor + 1
            value_length = stored_length - 1
            value_end = value_offset + value_length
            symbol_count += 1
            symbol_bytes += value_length
            if (
                symbol_count > _MAX_OSMX_SYMBOLS
                or symbol_bytes > _MAX_OSMX_SYMBOL_BYTES
            ):
                limit_exceeded = True
                valid = False
                break
            if (
                stored_length == 0
                or value_end > len(data)
                or any(
                    data[index] < 0x20 or data[index] > 0x7E
                    for index in range(value_offset, value_end)
                )
            ):
                valid = False
                break
            cursor = value_end
        if valid and cursor == len(data) and symbol_count:
            results.append((symbol_data_offset, symbol_count))
    return tuple(results), limit_exceeded


def _decode_osmx_symbols(
    data: bytes, symbol_data_offset: int, symbol_count: int
) -> tuple[OsmxSymbol, ...]:
    cursor = symbol_data_offset
    symbols: list[OsmxSymbol] = []
    for index in range(symbol_count):
        stored_length = data[cursor]
        value_offset = cursor + 1
        value_end = value_offset + stored_length - 1
        symbols.append(
            OsmxSymbol(
                index,
                value_offset,
                data[value_offset:value_end].decode("ascii"),
            )
        )
        cursor = value_end
    if cursor != len(data):
        raise OsmxFormatError("OSMX symbol table decode is incomplete")
    return tuple(symbols)


def _u32be(data: bytes, offset: int) -> int:
    if offset < 0 or offset + 4 > len(data):
        return -1
    return struct.unpack_from(">I", data, offset)[0]


def stream_items(
    archive: Cfv2Archive, directory: Cfv2Directory
) -> Iterable[tuple[str, bytes]]:
    for stream in directory.streams:
        yield stream.name, archive.stream_bytes(stream, directory)
