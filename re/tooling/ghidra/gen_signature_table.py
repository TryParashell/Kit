import argparse
import hashlib
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[3]
VENDORED = ROOT / "re/binaries/sldmfcu.dll"
MANIFEST = ROOT / "re/binaries/manifest.json"
INSTALLED = pathlib.Path(
    r"C:\Program Files\SOLIDWORKS Corp\SOLIDWORKS\sldmfcu.dll",
)
SHIPPED = ROOT / "src/convert/adapters/solidworks/data/sldprt_signature_table.bin"
RECORD = ROOT / "re/data/signature_table.json"
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
        "shipped_resource": str(SHIPPED.relative_to(ROOT)).replace("\\", "/"),
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
        if not SHIPPED.is_file():
            print(f"shipped resource {SHIPPED} is missing")
            return 1
        shipped = SHIPPED.read_bytes()
        if shipped != table:
            print("MISMATCH shipped resource differs from the DLL")
            return 1
        print("shipped resource matches the DLL byte for byte")
        return 0
    SHIPPED.parent.mkdir(parents=True, exist_ok=True)
    SHIPPED.write_bytes(table)
    RECORD.parent.mkdir(parents=True, exist_ok=True)
    RECORD.write_text(
        json.dumps(provenance(path, rows, digest), indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"wrote {SHIPPED.relative_to(ROOT)} and {RECORD.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
