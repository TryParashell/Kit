from __future__ import annotations

from pathlib import Path
import struct
import sys
import zlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from convert.adapters.solidworks.container import (  # noqa: E402
    SldprtArchive,
    _template_fields,
)
from convert.adapters.solidworks.format import (  # noqa: E402
    CONTENT_TYPES_STREAM,
    RELATIONSHIPS_STREAM,
)
from tests.oracle import SolidWorksSession  # noqa: E402

PREFIX = bytes.fromhex("140006000800")
ARCHIVE_OFFSET = 8
SAMPLE = ROOT / "examples" / ".SLDPRT" / "example.SLDPRT"
OUTPUT = ROOT / ".rescratch" / "variants"

ZIP_LOCAL = bytes.fromhex("504b0304")
ZIP_CENTRAL = bytes.fromhex("504b0102")
ZIP_END = bytes.fromhex("504b0506")


def nibble_swap(data: bytes) -> bytes:
    return bytes(((value >> 4) | ((value & 0x0F) << 4)) for value in data)


def build_container(
    streams: list[tuple[str, bytes]],
    file_id: int,
    signatures: tuple[bytes, bytes, bytes],
    type_ids: dict[str, int],
    default_type_id: int,
    format_version: int = 4,
) -> bytes:
    local_signature, central_signature, end_signature = signatures
    output = bytearray(struct.pack(">II", file_id, format_version))
    encoded: list[tuple[int, str, int, int, int, int]] = []
    for name, payload in streams:
        type_id = type_ids.get(name, default_type_id)
        local_offset = len(output) - ARCHIVE_OFFSET
        compressor = zlib.compressobj(level=1, wbits=-15)
        compressed = compressor.compress(payload) + compressor.flush()
        encoded_name = nibble_swap(name.encode("utf-8"))
        crc = zlib.crc32(payload) & 0xFFFFFFFF
        output.extend(local_signature)
        output.extend(PREFIX)
        output.extend(struct.pack("<I", type_id))
        output.extend(
            struct.pack(
                "<IIIHH", crc, len(compressed), len(payload), len(encoded_name), 0
            )
        )
        output.extend(encoded_name)
        output.extend(compressed)
        encoded.append(
            (type_id, name, crc, len(compressed), len(payload), local_offset)
        )
    central_offset = len(output) - ARCHIVE_OFFSET
    for type_id, name, crc, csize, size, local_offset in encoded:
        encoded_name = nibble_swap(name.encode("utf-8"))
        package_section = int(
            name == CONTENT_TYPES_STREAM
            or name == RELATIONSHIPS_STREAM
            or name.startswith("docProps/")
            or name.startswith("swXmlContents/")
        )
        output.extend(central_signature)
        output.extend(struct.pack("<H", 0))
        output.extend(PREFIX)
        output.extend(struct.pack("<I", type_id))
        output.extend(struct.pack("<IIIHH", crc, csize, size, len(encoded_name), 0))
        output.extend(struct.pack("<HHHII", 0, 0, package_section, 0, local_offset))
        output.extend(encoded_name)
    central_size = len(output) - ARCHIVE_OFFSET - central_offset
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


def main() -> int:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    original = SAMPLE.read_bytes()
    archive = SldprtArchive.from_bytes(original)
    signatures, type_ids = _template_fields(original, archive)
    streams = [(record.name, record.data) for record in archive.records]
    default_type_id = max(
        set(type_ids.values()), key=lambda value: list(type_ids.values()).count(value)
    )
    print(f"file_id=0x{archive.file_id:08x} streams={len(streams)}", flush=True)
    print(
        "signatures:",
        " ".join(item.hex() for item in signatures),
        flush=True,
    )

    variants: dict[str, bytes] = {}
    variants["a_faithful"] = build_container(
        streams, archive.file_id, signatures, type_ids, default_type_id
    )
    variants["b_foreign_signatures"] = build_container(
        streams,
        archive.file_id,
        (
            bytes.fromhex("64d80045"),
            bytes.fromhex("ae0d4ef6"),
            bytes.fromhex("54ce179a"),
        ),
        type_ids,
        default_type_id,
    )
    variants["c_arbitrary"] = build_container(
        streams,
        0x1234ABCD,
        (
            bytes.fromhex("deadbe01"),
            bytes.fromhex("deadbe02"),
            bytes.fromhex("deadbe03"),
        ),
        type_ids,
        default_type_id,
    )
    variants["d_real_zip_magics"] = build_container(
        streams,
        0x1234ABCD,
        (ZIP_LOCAL, ZIP_CENTRAL, ZIP_END),
        type_ids,
        default_type_id,
    )
    variants["e_uniform_type_id"] = build_container(
        streams, archive.file_id, signatures, {}, default_type_id
    )
    variants["f_zero_type_id"] = build_container(
        streams, archive.file_id, signatures, {}, 0
    )

    paths: list[Path] = []
    for label, payload in variants.items():
        target = OUTPUT / f"{label}.SLDPRT"
        target.write_bytes(payload)
        paths.append(target)
        reread = SldprtArchive.from_bytes(payload)
        print(
            f"{label}: bytes={len(payload)} kit_reread_streams={len(reread.records)}",
            flush=True,
        )

    for target in (SAMPLE, *paths):
        describe(target)
    return 0


def describe(target: Path) -> None:
    session: SolidWorksSession | None = None
    try:
        session = SolidWorksSession()
        result = session.inspect_part(target)
        print(
            f"{target.stem}: opened={result.opened} errors={result.load_errors} "
            f"warnings={result.load_warnings} rebuilt={result.rebuilt} "
            f"bodies={result.body_count} features={len(result.features)} "
            f"volume={None if result.solid is None else result.solid.volume_mm3}",
            flush=True,
        )
    except Exception as exc:
        print(f"{target.stem}: CRASHED {type(exc).__name__} {exc}", flush=True)
    finally:
        if session is not None:
            try:
                session.close()
            except Exception:
                pass


if __name__ == "__main__":
    raise SystemExit(main())
