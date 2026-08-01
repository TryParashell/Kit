from __future__ import annotations

from dataclasses import dataclass
import struct
from typing import Iterable, Sequence


MAGIC = b"V5_CFV2\x00"
DIRECTORY_MAGIC = b"CATIA_V5 CB0001\x00"
DIRECTORY_END = b"CB__END"


class Cfv2FormatError(ValueError):
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
        nested: list[Cfv2Directory] = []
        cursor = len(MAGIC)
        while True:
            position = data.find(MAGIC, cursor)
            if position < 0:
                break
            cursor = position + 1
            if position + 16 > len(data):
                continue
            offset, length = struct.unpack_from(">II", data, position + 8)
            absolute = position + offset
            if absolute + length > len(data):
                continue
            try:
                directory = _parse_directory(data, position, absolute, length)
            except Cfv2FormatError:
                continue
            nested.append(directory)
        return cls(data, outer, tuple(nested))

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
        return Cfv2Directory(physical_base, offset, length, sequential)
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
    return Cfv2Directory(physical_base, offset, length, tuple(streams))


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


def _u32be(data: bytes, offset: int) -> int:
    if offset < 0 or offset + 4 > len(data):
        return -1
    return struct.unpack_from(">I", data, offset)[0]


def stream_items(
    archive: Cfv2Archive, directory: Cfv2Directory
) -> Iterable[tuple[str, bytes]]:
    for stream in directory.streams:
        yield stream.name, archive.stream_bytes(stream, directory)
