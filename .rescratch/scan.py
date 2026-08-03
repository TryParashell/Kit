from __future__ import annotations

import json
import struct
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from convert.adapters.solidworks.container import (  # noqa: E402
    SldprtArchive,
    _ARCHIVE_OFFSET,
    _LOCAL_SIGNATURE_PREFIX,
    _MAX_NAME_BYTES,
    _nibble_swap,
)

WORKSPACE = ROOT.parent


def find_files() -> list[Path]:
    out: list[Path] = []
    for ext in ("*.SLDPRT", "*.SLDASM", "*.SLDDRW"):
        out.extend(p for p in WORKSPACE.rglob(ext) if p.is_file())
    return sorted(set(out))


def central_markers(blob: bytes, archive: SldprtArchive) -> list[int]:
    records = archive.records
    expected = {
        (r.name, r.crc32, r.compressed_size, r.uncompressed_size) for r in records
    }
    markers: list[int] = []
    cursor = max(r.payload_offset + r.compressed_size for r in records)
    while True:
        marker = blob.find(_LOCAL_SIGNATURE_PREFIX, cursor)
        if marker < 0:
            break
        cursor = marker + 1
        if marker + 40 > len(blob):
            continue
        crc, csize, size, nsize = struct.unpack_from("<IIII", blob, marker + 10)
        if not 0 < nsize <= _MAX_NAME_BYTES:
            continue
        ns, ne = marker + 40, marker + 40 + nsize
        if ne > len(blob):
            continue
        try:
            name = _nibble_swap(blob[ns:ne]).decode("utf-8")
        except UnicodeDecodeError:
            continue
        if (name, crc, csize, size) in expected:
            markers.append(marker)
    return markers


def end_record(blob: bytes, central_start: int, count: int):
    central_offset = central_start - _ARCHIVE_OFFSET
    for offset in range(central_start, len(blob) - 21):
        fields = struct.unpack_from("<HHHHIIH", blob, offset + 4)
        dn, dd, de, te, dsize, doff, csize = fields
        if (
            dn == 0
            and dd == 0
            and de == count
            and te == count
            and doff == central_offset
            and _ARCHIVE_OFFSET + doff + dsize == offset
            and offset + 22 + csize <= len(blob)
        ):
            return blob[offset : offset + 4], fields, offset
    return None, None, None


def analyse(path: Path) -> dict:
    blob = path.read_bytes()
    row: dict = {
        "path": str(path),
        "size": len(blob),
        "raw_head": blob[:16].hex(),
    }
    if len(blob) >= 8:
        fid, fver = struct.unpack_from(">II", blob, 0)
        row["file_id"] = fid
        row["format_version"] = fver
    try:
        archive = SldprtArchive.from_bytes(blob, path)
    except Exception as exc:  # noqa: BLE001
        row["error"] = f"{type(exc).__name__}: {exc}"
        return row
    row["file_id"] = archive.file_id
    row["format_version"] = archive.format_version
    recs = sorted(archive.records, key=lambda r: r.offset)
    row["stream_count"] = len(recs)
    locals_ = sorted({blob[r.offset - 4 : r.offset].hex() for r in recs})
    row["local_sigs"] = locals_
    row["streams"] = [
        {
            "name": r.name,
            "type_id": struct.unpack_from("<I", r.signature, 6)[0],
            "csize": r.compressed_size,
            "usize": r.uncompressed_size,
            "offset": r.offset,
        }
        for r in recs
    ]
    row["prefix_at_local"] = sorted(
        {blob[r.offset : r.offset + 6].hex() for r in recs}
    )
    markers = central_markers(blob, archive)
    row["central_marker_count"] = len(markers)
    csigs = sorted(
        {
            blob[m - 6 : m - 2].hex()
            for m in markers
            if blob[m - 2 : m] == b"\0\0"
        }
    )
    row["central_sigs"] = csigs
    row["central_prefix_at"] = sorted({blob[m : m + 6].hex() for m in markers})
    if markers:
        cstart = markers[0] - 6
        esig, fields, eoff = end_record(blob, cstart, len(recs))
        row["end_sig"] = esig.hex() if esig else None
        row["end_fields"] = list(fields) if fields else None
        row["end_offset"] = eoff
        row["tail"] = blob[-32:].hex()
    return row


def main() -> None:
    files = find_files()
    rows = [analyse(p) for p in files]
    out = Path(__file__).resolve().parent / "scan.json"
    out.write_text(json.dumps(rows, indent=1), encoding="utf-8")
    print(f"files: {len(rows)}")
    ok = [r for r in rows if "error" not in r]
    bad = [r for r in rows if "error" in r]
    print(f"parsed ok: {len(ok)}  failed: {len(bad)}")
    for r in bad:
        print("  FAIL", r["path"], r["error"], r.get("format_version"))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
