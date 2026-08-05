import argparse
import base64
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
OUT = ROOT / ".rescratch/ghidra/out"
VENDORED = ROOT / "re/binaries/sldmfcu.dll"
INSTALLED = pathlib.Path(
    r"C:\Program Files\SOLIDWORKS Corp\SOLIDWORKS\sldmfcu.dll",
)
BLOCK_OFFSET = 0x566C40
ENTRY_COUNT = 1000
ID_STRIDE = 4
SIG_STRIDE = 12
LINE_WIDTH = 76


def host_dll(explicit: str | None) -> pathlib.Path:
    if explicit:
        return pathlib.Path(explicit)
    if VENDORED.is_file():
        return VENDORED
    return INSTALLED


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


def source_fragment(blob: bytes) -> str:
    text = base64.b85encode(blob).decode("ascii")
    chunks = [
        text[start : start + LINE_WIDTH] for start in range(0, len(text), LINE_WIDTH)
    ]
    body = "\n".join(f'    "{chunk}"' for chunk in chunks)
    return f"_SIGNATURE_TABLE_B85 = (\n{body}\n)\n"


def shipped_blob() -> bytes | None:
    sys.path.insert(0, str(ROOT / "src"))
    try:
        from convert.adapters.solidworks import container
    except ImportError:
        return None
    text = getattr(container, "_SIGNATURE_TABLE_B85", None)
    if text is None:
        return None
    return base64.b85decode(text)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dll")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    path = host_dll(args.dll)
    rows = extract(path)
    blob = pack(rows)
    ids = [file_id for file_id, _ in rows]
    if len(set(ids)) != ENTRY_COUNT:
        raise SystemExit("signature table ids are not distinct")
    OUT.mkdir(parents=True, exist_ok=True)
    fragment = source_fragment(blob)
    if not args.check:
        (OUT / "signature_table_b85.py").write_text(fragment, encoding="utf-8")
        (OUT / "signature_table.json").write_text(
            json.dumps(
                {
                    "host": str(path),
                    "block_file_offset": BLOCK_OFFSET,
                    "entry_count": ENTRY_COUNT,
                    "id_array_file_offset": BLOCK_OFFSET,
                    "signature_array_file_offset": (
                        BLOCK_OFFSET + ENTRY_COUNT * ID_STRIDE
                    ),
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
                },
                indent=1,
            ),
            encoding="utf-8",
        )
    print(f"host {path}")
    print(f"entries {ENTRY_COUNT} distinct_ids {len(set(ids))} raw_bytes {len(blob)}")
    print(f"b85_chars {len(base64.b85encode(blob))} lines {fragment.count(chr(10))}")
    shipped = shipped_blob()
    if shipped is None:
        print("shipped container has no embedded table")
        return 1
    if shipped != blob:
        print("MISMATCH shipped embedded table differs from the DLL")
        return 1
    print("shipped embedded table matches the DLL byte for byte")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
