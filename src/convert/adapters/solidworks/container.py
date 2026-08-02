from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import struct
from typing import Iterable, Mapping
import zlib

from .format import CONTAINER_VERSIONS


_LOCAL_SIGNATURE_PREFIX = bytes.fromhex("140006000800")
_LOCAL_SIGNATURE_SIZE = 10
_MAX_STREAM_COUNT = 100_000
_MAX_NAME_BYTES = 16_384
_MAX_UNCOMPRESSED_STREAM = 1 << 31


class SldprtFormatError(ValueError):
    __slots__ = ()


@dataclass(frozen=True, slots=True)
class StreamRecord:
    name: str
    data: bytes
    offset: int
    payload_offset: int
    compressed_size: int
    uncompressed_size: int
    crc32: int
    signature: bytes


@dataclass(frozen=True, slots=True)
class SldprtArchive:
    path: Path
    file_id: int
    format_version: int
    records: tuple[StreamRecord, ...]

    @classmethod
    def open(cls, path: str | Path) -> SldprtArchive:
        source = Path(path).expanduser().resolve()
        try:
            blob = source.read_bytes()
        except OSError as exc:
            raise SldprtFormatError(f"cannot read {source}: {exc}") from exc
        return cls.from_bytes(blob, source)

    @classmethod
    def from_bytes(
        cls, blob: bytes | bytearray, path: str | Path = "<memory>"
    ) -> SldprtArchive:
        source = Path(path)
        data = bytes(blob)
        if len(data) < 8:
            raise SldprtFormatError("file is too short to contain an SLDPRT header")
        file_id, format_version = struct.unpack_from(">II", data, 0)
        if format_version not in CONTAINER_VERSIONS:
            raise SldprtFormatError(
                f"unsupported SLDPRT container version {format_version}"
            )
        records = _scan_records(data)
        return cls(source, file_id, format_version, records)

    @property
    def streams(self) -> dict[str, bytes]:
        return {record.name: record.data for record in self.records}

    def get(self, name: str) -> bytes | None:
        for record in self.records:
            if record.name == name:
                return record.data
        return None

    def require(self, name: str) -> bytes:
        data = self.get(name)
        if data is None:
            raise SldprtFormatError(f"required stream is missing: {name}")
        return data


def build_sldprt(
    streams: Mapping[str, bytes] | Iterable[tuple[str, bytes]],
    *,
    file_id: int = 1,
    format_version: int = 4,
) -> bytes:
    if not 0 <= file_id <= 0xFFFFFFFF:
        raise ValueError("SLDPRT file id must fit in 32 bits")
    if format_version not in CONTAINER_VERSIONS:
        raise ValueError("SLDPRT container version must be 3 or 4")
    items = list(streams.items() if isinstance(streams, Mapping) else streams)
    names = [name for name, _ in items]
    if len(names) != len(set(names)):
        raise ValueError("SLDPRT stream names must be unique")
    output = bytearray(struct.pack(">II", file_id, format_version))
    encoded: list[tuple[int, str, bytes]] = []
    for index, (name, payload) in enumerate(items):
        type_id = 0x20 + index
        data = bytes(payload)
        output.extend(_encode_record(name, data, type_id))
        encoded.append((type_id, name, data))
    for type_id, name, data in encoded:
        output.extend(_encode_directory_entry(name, len(data), type_id))
    return bytes(output)


def _scan_records(blob: bytes) -> tuple[StreamRecord, ...]:
    candidates: list[StreamRecord] = []
    cursor = 0
    while True:
        offset = blob.find(_LOCAL_SIGNATURE_PREFIX, cursor)
        if offset < 0:
            break
        cursor = offset + 1
        signature_end = offset + _LOCAL_SIGNATURE_SIZE
        if signature_end > len(blob):
            continue
        signature = blob[offset:signature_end]
        record = _decode_scanned_candidate(blob, offset, signature)
        if record is None:
            continue
        candidates.append(record)
        if len(candidates) > _MAX_STREAM_COUNT:
            raise SldprtFormatError("unreasonable number of streams")
    if not candidates:
        raise SldprtFormatError("no valid compressed SLDPRT streams were found")
    candidates.sort(key=lambda record: record.offset)
    records: list[StreamRecord] = []
    by_name: dict[str, StreamRecord] = {}
    for candidate in candidates:
        prior = by_name.get(candidate.name)
        if prior is None:
            by_name[candidate.name] = candidate
            records.append(candidate)
            continue
        same = (
            prior.crc32 == candidate.crc32
            and prior.uncompressed_size == candidate.uncompressed_size
            and prior.data == candidate.data
        )
        if not same:
            raise SldprtFormatError(
                f"ambiguous valid stream records for {candidate.name!r}"
            )
    return tuple(records)


def _decode_scanned_candidate(
    blob: bytes, offset: int, signature: bytes
) -> StreamRecord | None:
    header_offset = offset + len(signature)
    if header_offset + 16 > len(blob):
        return None
    crc32_value, compressed_size, uncompressed_size, name_size = struct.unpack_from(
        "<IIII", blob, header_offset
    )
    if not 0 < name_size <= _MAX_NAME_BYTES:
        return None
    if not 0 <= uncompressed_size <= _MAX_UNCOMPRESSED_STREAM:
        return None
    name_offset = header_offset + 16
    payload_offset = name_offset + name_size
    payload_end = payload_offset + compressed_size
    if payload_end > len(blob):
        return None
    try:
        name = _nibble_swap(blob[name_offset:payload_offset]).decode("utf-8")
    except UnicodeDecodeError:
        return None
    if not name or any(ord(character) < 0x20 for character in name):
        return None
    try:
        data = zlib.decompress(blob[payload_offset:payload_end], wbits=-15)
    except zlib.error:
        return None
    if len(data) != uncompressed_size:
        return None
    if zlib.crc32(data) & 0xFFFFFFFF != crc32_value:
        return None
    return StreamRecord(
        name=name,
        data=data,
        offset=offset,
        payload_offset=payload_offset,
        compressed_size=compressed_size,
        uncompressed_size=uncompressed_size,
        crc32=crc32_value,
        signature=signature,
    )


def _nibble_swap(data: bytes) -> bytes:
    return bytes(((value >> 4) | ((value & 0x0F) << 4)) for value in data)


def _encoded_name(name: str) -> bytes:
    if not name or any(ord(character) < 0x20 for character in name):
        raise ValueError("SLDPRT stream name must contain printable characters")
    value = name.encode("utf-8")
    if len(value) > _MAX_NAME_BYTES:
        raise ValueError("SLDPRT stream name is too long")
    return _nibble_swap(value)


def _encode_record(name: str, data: bytes, type_id: int) -> bytes:
    compressor = zlib.compressobj(level=6, wbits=-15)
    compressed = compressor.compress(data) + compressor.flush()
    encoded_name = _encoded_name(name)
    return b"".join(
        (
            _LOCAL_SIGNATURE_PREFIX,
            struct.pack("<I", type_id),
            struct.pack(
                "<IIII",
                zlib.crc32(data) & 0xFFFFFFFF,
                len(compressed),
                len(data),
                len(encoded_name),
            ),
            encoded_name,
            compressed,
        )
    )


def _encode_directory_entry(name: str, size: int, type_id: int) -> bytes:
    encoded_name = _encoded_name(name)
    return b"".join(
        (
            _LOCAL_SIGNATURE_PREFIX,
            struct.pack("<I", type_id),
            struct.pack("<IIII", 0, size, 0, len(encoded_name)),
            bytes(14),
            encoded_name,
            bytes.fromhex("e54b575b0000"),
        )
    )
