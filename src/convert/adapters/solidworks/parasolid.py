from __future__ import annotations

from dataclasses import dataclass
import hashlib
import re
import struct
import zlib

from .container import SldprtFormatError


_WRAPPER_MAGIC = bytes.fromhex("231dd571da8148a2a85898b21b89ef99")


@dataclass(frozen=True, slots=True)
class ParasolidPayload:
    stream: str
    kind: str
    schema: str
    description: str
    data: bytes
    sha256: str
    wrapper_offset: int
    magic_offset: int
    compressed_offset: int
    compressed_size: int
    uncompressed_size: int


def decode_partition_stream(
    data: bytes, stream: str = ""
) -> tuple[ParasolidPayload, ...]:
    results: list[ParasolidPayload] = []
    cursor = 0
    while True:
        magic_offset = data.find(_WRAPPER_MAGIC, cursor)
        if magic_offset < 0:
            break
        cursor = magic_offset + 1
        header_offset = magic_offset + len(_WRAPPER_MAGIC)
        if header_offset + 8 > len(data):
            continue
        uncompressed_size, compressed_size = struct.unpack_from(
            "<II", data, header_offset
        )
        compressed_offset = header_offset + 8
        compressed_end = compressed_offset + compressed_size
        if compressed_end > len(data):
            continue
        try:
            payload = zlib.decompress(data[compressed_offset:compressed_end])
        except zlib.error:
            continue
        if len(payload) != uncompressed_size or not payload.startswith(b"PS\x00\x00"):
            continue
        results.append(
            _payload(
                stream,
                payload,
                magic_offset - 4 if magic_offset >= 4 else magic_offset,
                magic_offset,
                compressed_offset,
                compressed_size,
                uncompressed_size,
            )
        )
        cursor = compressed_end
    if not results and data.startswith(b"PS\x00\x00"):
        results.append(_payload(stream, data, 0, 0, 0, len(data), len(data)))
    if not results:
        raise SldprtFormatError(f"no Parasolid payload found in {stream or 'stream'}")
    return tuple(results)


def _payload(
    stream: str,
    data: bytes,
    wrapper_offset: int,
    magic_offset: int,
    compressed_offset: int,
    compressed_size: int,
    uncompressed_size: int,
) -> ParasolidPayload:
    header = data[:8192]
    kind_match = re.search(rb"TRANSMIT FILE \(([^)]+)\)", header)
    schema_match = re.search(rb"SCH_[0-9_]+", header)
    description_match = re.search(rb": ([\x20-\x7e]{1,512})", header)
    return ParasolidPayload(
        stream=stream,
        kind=(
            kind_match.group(1).decode("ascii", "replace") if kind_match else "unknown"
        ),
        schema=(schema_match.group(0).decode("ascii") if schema_match else "unknown"),
        description=(
            description_match.group(1).decode("ascii", "replace").strip()
            if description_match
            else ""
        ),
        data=data,
        sha256=hashlib.sha256(data).hexdigest(),
        wrapper_offset=wrapper_offset,
        magic_offset=magic_offset,
        compressed_offset=compressed_offset,
        compressed_size=compressed_size,
        uncompressed_size=uncompressed_size,
    )
