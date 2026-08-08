# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import struct
from typing import Iterable, Mapping
import zlib

from .format import CONTENT_TYPES_STREAM, CONTAINER_VERSIONS, RELATIONSHIPS_STREAM

_LOCAL_SIGNATURE_PREFIX = bytes.fromhex("140006000800")
_LOCAL_SIGNATURE_SIZE = 10
_DEFAULT_FILE_ID = 0xEC6E2386
_DEFAULT_TYPE_ID = 0x1C34D281
_TYPE_IDS_BY_NAME = {
    "Header2": 0x1C74D22C,
    "Preview": 0x1C74D22C,
}
DEFAULT_FILE_ID = _DEFAULT_FILE_ID
DEFAULT_SIGNATURES = (
    bytes.fromhex("64d80045"),
    bytes.fromhex("ae0d4ef6"),
    bytes.fromhex("54ce179a"),
)
_ARCHIVE_OFFSET = 8
_MAX_STREAM_COUNT = 100_000
_MAX_DIRECTORY_STREAM_COUNT = 0xFFFF
_MAX_NAME_BYTES = 16_384
_MAX_UNCOMPRESSED_STREAM = 1 << 31
_MAX_ARCHIVE_OFFSET = 0xFFFFFFFF


class SldprtFormatError(ValueError):
    __slots__ = ()


def signature_triplet(file_id: int) -> tuple[bytes, bytes, bytes] | None:
    if file_id == DEFAULT_FILE_ID:
        return DEFAULT_SIGNATURES
    return None


def container_signatures(blob: bytes | bytearray) -> tuple[bytes, bytes, bytes]:
    data = bytes(blob)
    signatures, _ = _template_fields(data, SldprtArchive.from_bytes(data))
    return signatures


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
    file_id: int | None = None,
    format_version: int = 4,
    template: bytes | bytearray | None = None,
    signatures: tuple[bytes, bytes, bytes] | None = None,
) -> bytes:
    type_ids: dict[str, int] = {}
    if template is not None and signatures is not None:
        raise ValueError("SLDPRT signatures cannot be given alongside a template")
    if template is None and signatures is not None:
        if len(signatures) != 3 or any(len(value) != 4 for value in signatures):
            raise ValueError("SLDPRT signatures must be three four byte values")
        if file_id is None:
            raise ValueError("SLDPRT signatures require the paired file id")
        signatures = tuple(bytes(value) for value in signatures)
    elif template is None:
        if file_id is None:
            file_id = DEFAULT_FILE_ID
        signatures = signature_triplet(file_id)
        if signatures is None:
            raise ValueError(
                "SLDPRT file id has no known container signatures; "
                "a native template with matching signatures is required"
            )
    else:
        template_data = bytes(template)
        archive = SldprtArchive.from_bytes(template_data)
        if file_id is None:
            file_id = archive.file_id
        elif file_id != archive.file_id:
            raise ValueError(
                "SLDPRT template file id does not match the requested file id"
            )
        signatures, type_ids = _template_fields(template_data, archive)
    if not 0 <= file_id <= 0xFFFFFFFF:
        raise ValueError("SLDPRT file id must fit in 32 bits")
    if format_version not in CONTAINER_VERSIONS:
        raise ValueError("SLDPRT container version must be 3 or 4")
    items = list(streams.items() if isinstance(streams, Mapping) else streams)
    names = [name for name, _ in items]
    if len(names) != len(set(names)):
        raise ValueError("SLDPRT stream names must be unique")
    if len(items) > _MAX_DIRECTORY_STREAM_COUNT:
        raise ValueError("SLDPRT stream count must fit in the native directory")
    local_signature, central_signature, end_signature = signatures
    output = bytearray(struct.pack(">II", file_id, format_version))
    encoded: list[tuple[int, str, int, int, int, int]] = []
    for name, payload in items:
        type_id = type_ids.get(name, _TYPE_IDS_BY_NAME.get(name, _DEFAULT_TYPE_ID))
        data = bytes(payload)
        local_offset = len(output) - _ARCHIVE_OFFSET
        record, crc32_value, compressed_size = _encode_record(name, data, type_id)
        output.extend(local_signature)
        output.extend(record)
        encoded.append(
            (
                type_id,
                name,
                crc32_value,
                compressed_size,
                len(data),
                local_offset,
            )
        )
    central_offset = len(output) - _ARCHIVE_OFFSET
    if central_offset > _MAX_ARCHIVE_OFFSET:
        raise ValueError("SLDPRT local records exceed the native offset range")
    for record in encoded:
        output.extend(_encode_directory_entry(*record, central_signature))
    central_size = len(output) - _ARCHIVE_OFFSET - central_offset
    if central_size > _MAX_ARCHIVE_OFFSET:
        raise ValueError("SLDPRT directory exceeds the native size range")
    output.extend(end_signature)
    output.extend(
        struct.pack(
            "<HHHHIIH",
            0,
            0,
            len(encoded),
            len(encoded),
            central_size,
            central_offset,
            0,
        )
    )
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


def _encode_record(name: str, data: bytes, type_id: int) -> tuple[bytes, int, int]:
    if len(data) > _MAX_UNCOMPRESSED_STREAM:
        raise ValueError("SLDPRT stream is too large")
    compressor = zlib.compressobj(level=1, wbits=-15)
    compressed = compressor.compress(data) + compressor.flush()
    encoded_name = _encoded_name(name)
    crc32_value = zlib.crc32(data) & 0xFFFFFFFF
    record = b"".join(
        (
            _LOCAL_SIGNATURE_PREFIX,
            struct.pack("<I", type_id),
            struct.pack(
                "<IIIHH", crc32_value, len(compressed), len(data), len(encoded_name), 0
            ),
            encoded_name,
            compressed,
        )
    )
    return record, crc32_value, len(compressed)


def _encode_directory_entry(
    type_id: int,
    name: str,
    crc32_value: int,
    compressed_size: int,
    size: int,
    local_offset: int,
    signature: bytes,
) -> bytes:
    encoded_name = _encoded_name(name)
    package_section = int(
        name == CONTENT_TYPES_STREAM
        or name == RELATIONSHIPS_STREAM
        or name.startswith("docProps/")
        or name.startswith("swXmlContents/")
    )
    return b"".join(
        (
            signature,
            struct.pack("<H", 0),
            _LOCAL_SIGNATURE_PREFIX,
            struct.pack("<I", type_id),
            struct.pack(
                "<IIIHH", crc32_value, compressed_size, size, len(encoded_name), 0
            ),
            struct.pack("<HHHII", 0, 0, package_section, 0, local_offset),
            encoded_name,
        )
    )


def _template_fields(
    blob: bytes, archive: SldprtArchive
) -> tuple[tuple[bytes, bytes, bytes], dict[str, int]]:
    records = tuple(sorted(archive.records, key=lambda item: item.offset))
    local_signatures = {blob[item.offset - 4 : item.offset] for item in records}
    if len(local_signatures) != 1 or any(len(value) != 4 for value in local_signatures):
        raise ValueError("SLDPRT template has inconsistent local signatures")
    expected = {
        (item.name, item.crc32, item.compressed_size, item.uncompressed_size)
        for item in records
    }
    central_markers: list[int] = []
    cursor = max(item.payload_offset + item.compressed_size for item in records)
    while True:
        marker = blob.find(_LOCAL_SIGNATURE_PREFIX, cursor)
        if marker < 0:
            break
        cursor = marker + 1
        if marker + 40 > len(blob):
            continue
        crc32_value, compressed_size, size, name_size = struct.unpack_from(
            "<IIII", blob, marker + 10
        )
        if not 0 < name_size <= _MAX_NAME_BYTES:
            continue
        name_start = marker + 40
        name_end = name_start + name_size
        if name_end > len(blob):
            continue
        try:
            name = _nibble_swap(blob[name_start:name_end]).decode("utf-8")
        except UnicodeDecodeError:
            continue
        if (name, crc32_value, compressed_size, size) in expected:
            central_markers.append(marker)
    if len(central_markers) != len(records):
        raise ValueError("SLDPRT template central directory is incomplete")
    central_signatures = {
        blob[marker - 6 : marker - 2]
        for marker in central_markers
        if blob[marker - 2 : marker] == b"\0\0"
    }
    if len(central_signatures) != 1:
        raise ValueError("SLDPRT template has inconsistent central signatures")
    central_start = central_markers[0] - 6
    end_signature = _end_signature(blob, central_start, len(records))
    type_ids = {
        item.name: struct.unpack_from("<I", item.signature, 6)[0] for item in records
    }
    return (
        (
            next(iter(local_signatures)),
            next(iter(central_signatures)),
            end_signature,
        ),
        type_ids,
    )


def _end_signature(blob: bytes, central_start: int, count: int) -> bytes:
    central_offset = central_start - _ARCHIVE_OFFSET
    for offset in range(central_start, len(blob) - 21):
        (
            disk_number,
            directory_disk,
            disk_entries,
            total_entries,
            directory_size,
            directory_offset,
            comment_size,
        ) = struct.unpack_from("<HHHHIIH", blob, offset + 4)
        if (
            disk_number == 0
            and directory_disk == 0
            and disk_entries == count
            and total_entries == count
            and directory_offset == central_offset
            and _ARCHIVE_OFFSET + directory_offset + directory_size == offset
            and offset + 22 + comment_size <= len(blob)
        ):
            return blob[offset : offset + 4]
    raise ValueError("SLDPRT template end directory is missing")
