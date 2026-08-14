# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import argparse
import hashlib
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
VENDORED = ROOT / "re/binaries/sldmfcu.dll"
MANIFEST = ROOT / "re/binaries/Manifest.json"
INSTALLED = pathlib.Path(
    r"C:\Program Files\SOLIDWORKS Corp\SOLIDWORKS\sldmfcu.dll",
)
RECORD = ROOT / "re/data/Serialization/SignatureTable.json"
HOST_NAME = "sldmfcu.dll"
BLOCK_OFFSET = 0x566C40
ENTRY_COUNT = 1000
ID_STRIDE = 4
SIG_STRIDE = 12


def host_dll(explicit: str | None) -> pathlib.Path:
    if explicit:
        return pathlib.Path(explicit)
    if VENDORED.is_file():
        return VENDORED
    return INSTALLED


def recorded_digest() -> str | None:
    if not MANIFEST.is_file():
        return None
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    entries = payload if isinstance(payload, list) else payload.get("binaries", ())
    for entry in entries:
        if isinstance(entry, dict) and entry.get("name") == HOST_NAME:
            digest = entry.get("sha256")
            return str(digest) if digest else None
    return None


def extract(path: pathlib.Path) -> list[tuple[int, bytes]]:
    blob = path.read_bytes()
    ids_base = BLOCK_OFFSET
    sig_base = BLOCK_OFFSET + ENTRY_COUNT * ID_STRIDE
    end = sig_base + ENTRY_COUNT * SIG_STRIDE
    if end > len(blob):
        raise SystemExit(f"{path} is too small to hold the signature table")
    rows: list[tuple[int, bytes]] = []
    for index in range(ENTRY_COUNT):
        head = ids_base + ID_STRIDE * index
        file_id = int.from_bytes(blob[head : head + ID_STRIDE], "big")
        triplet = bytearray()
        for slot in range(3):
            start = sig_base + SIG_STRIDE * index + 4 * slot
            triplet.extend(reversed(blob[start : start + 4]))
        rows.append((file_id, bytes(triplet)))
    return rows


def pack(rows: list[tuple[int, bytes]]) -> bytes:
    return b"".join(
        file_id.to_bytes(ID_STRIDE, "big") + triplet for file_id, triplet in rows
    )


def provenance(
    path: pathlib.Path, rows: list[tuple[int, bytes]], digest: str
) -> dict[str, object]:
    return {
        "host": HOST_NAME,
        "host_sha256": digest,
        "host_bytes": path.stat().st_size,
        "block_file_offset": BLOCK_OFFSET,
        "entry_count": ENTRY_COUNT,
        "id_array_file_offset": BLOCK_OFFSET,
        "signature_array_file_offset": BLOCK_OFFSET + ENTRY_COUNT * ID_STRIDE,
        "id_encoding": "big-endian u32",
        "signature_encoding": "little-endian u32 stored big-endian",
        "reader": "FUN_3cc4d270 keys on file_id, caches the row magics at +0x88/+0x8c/+0x90",
        "comparison_sites": {
            "local": "FUN_3cc528b0 unz+0xc8",
            "central": "FUN_3cc52ac0 unz+0xcc",
            "end": "FUN_3cc51900 backward scan on unz+0xd0",
        },
        "writer": "FUN_3cc4a8c0 draws a random index in [0,1000) and emits that row",
        "shipped_rows": 1,
        "entries": [
            {
                "index": index,
                "file_id": f"{file_id:08x}",
                "local": triplet[0:4].hex(),
                "central": triplet[4:8].hex(),
                "end": triplet[8:12].hex(),
            }
            for index, (file_id, triplet) in enumerate(rows)
        ],
    }


def shipped_row() -> tuple[int, bytes] | None:
    sys.path.insert(0, str(ROOT / "src"))
    try:
        from convert.adapters.solidworks import container
    except ImportError:
        return None
    file_id = getattr(container, "DEFAULT_FILE_ID", None)
    triplet = getattr(container, "DEFAULT_SIGNATURES", None)
    if file_id is None or triplet is None:
        return None
    return int(file_id), b"".join(triplet)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dll")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    path = host_dll(args.dll)
    if not path.is_file():
        print(f"host dll {path} is not present")
        return 1
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    expected = recorded_digest()
    rows = extract(path)
    ids = [file_id for file_id, _ in rows]
    if len(set(ids)) != ENTRY_COUNT:
        print("signature table ids are not distinct")
        return 1
    table = pack(rows)
    print(f"host {path}")
    print(f"host_sha256 {digest}")
    print(f"entries {ENTRY_COUNT} distinct_ids {len(set(ids))} raw_bytes {len(table)}")
    if expected is not None and expected != digest:
        print(f"MISMATCH host digest differs from {MANIFEST.name} {expected}")
        return 1
    if args.check:
        shipped = shipped_row()
        if shipped is None:
            print("Container.py exposes no default signature row")
            return 1
        file_id, triplet = shipped
        index = next(
            (
                position
                for position, (candidate, payload) in enumerate(rows)
                if candidate == file_id and payload == triplet
            ),
            None,
        )
        if index is None:
            print(f"MISMATCH 0x{file_id:08x} {triplet.hex()} is not a row of the DLL")
            return 1
        print(f"shipped row 0x{file_id:08x} is DLL table index {index}")
        print(f"shipped vendor bytes {4 + len(triplet)} of {len(table)}")
        return 0
    RECORD.parent.mkdir(parents=True, exist_ok=True)
    RECORD.write_text(
        json.dumps(provenance(path, rows, digest), indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"wrote {RECORD.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
