import json
import pathlib
import struct
import sys

SW = pathlib.Path(r"C:\Program Files\SOLIDWORKS Corp\SOLIDWORKS")
VENDORED = pathlib.Path(__file__).resolve().parents[2] / "binaries" / "sldmfcu.dll"
HOST = VENDORED if VENDORED.exists() else SW / "sldmfcu.dll"
BLOCK_OFFSET = 0x566C40
ENTRY_COUNT = 1000
ID_BYTES = ENTRY_COUNT * 4
ROOT = pathlib.Path(__file__).resolve().parents[3]
OUT = ROOT / "re/data"


def extract(path=HOST, block=BLOCK_OFFSET, count=ENTRY_COUNT):
    blob = path.read_bytes()
    ids_base = block
    sig_base = block + count * 4
    rows = []
    for i in range(count):
        raw_id = blob[ids_base + 4 * i : ids_base + 4 * i + 4]
        file_id = int.from_bytes(raw_id, "big")
        trip = []
        for k in range(3):
            raw = blob[sig_base + 12 * i + 4 * k : sig_base + 12 * i + 4 * k + 4]
            trip.append(bytes(reversed(raw)))
        rows.append((i, file_id, tuple(trip)))
    return rows


def locate(path=HOST):
    blob = path.read_bytes()
    a = blob.find(struct.pack(">I", 0xEC6E2386))
    b = blob.find(struct.pack("<I", 0x64D80045))
    return a, b


def scan_parts(roots):
    sys.path.insert(0, str(ROOT / "src"))
    from convert.adapters.solidworks.container import SldprtArchive, _template_fields

    found = []
    for root in roots:
        for path in sorted((ROOT / root).rglob("*")):
            if path.suffix.upper() not in (".SLDPRT", ".SLDASM", ".SLDDRW"):
                continue
            try:
                blob = path.read_bytes()
            except OSError:
                continue
            if len(blob) < 32:
                continue
            try:
                archive = SldprtArchive.from_bytes(blob, path)
                signatures, _ = _template_fields(blob, archive)
            except Exception as problem:
                found.append((path, -1, 0, repr(problem)))
                continue
            found.append((path, archive.file_id, archive.format_version, signatures))
    return found


def main():
    rows = extract()
    table = {}
    for i, file_id, trip in rows:
        table.setdefault(file_id, (i, trip))
    OUT.mkdir(parents=True, exist_ok=True)
    dump = {
        "host": HOST.name,
        "block_file_offset": BLOCK_OFFSET,
        "entry_count": ENTRY_COUNT,
        "id_array_file_offset": BLOCK_OFFSET,
        "signature_array_file_offset": BLOCK_OFFSET + ID_BYTES,
        "entries": [
            {
                "index": i,
                "file_id": f"{file_id:08x}",
                "local": trip[0].hex(),
                "central": trip[1].hex(),
                "end": trip[2].hex(),
            }
            for i, file_id, trip in rows
        ],
    }
    (OUT / "signature_table.json").write_text(json.dumps(dump, indent=1))
    print("anchors", [hex(v) for v in locate()])
    print("distinct file_ids", len(table), "of", ENTRY_COUNT)
    for i, file_id, trip in rows[709:714] + rows[748:753]:
        print(i, f"0x{file_id:08x}", [t.hex() for t in trip])
    roots = sys.argv[1:] or [
        "examples",
        ".rescratch/corpus/parts",
        ".rescratch/corpus2",
        ".rescratch/trace/parts",
        ".rescratch/re/parts",
    ]
    parts = scan_parts(roots)
    ok = 0
    bad = 0
    unknown = 0
    broken = 0
    for path, file_id, version, signatures in parts:
        name = path.name.encode("ascii", "replace").decode("ascii")
        if file_id < 0:
            broken += 1
            print("UNREADABLE", name, signatures)
            continue
        hit = table.get(file_id)
        if hit is None:
            unknown += 1
            print("NO TABLE ENTRY", name, f"0x{file_id:08x}")
            continue
        if tuple(hit[1]) == tuple(signatures):
            ok += 1
        else:
            bad += 1
            print(
                "MISMATCH",
                name,
                f"0x{file_id:08x}",
                f"index={hit[0]}",
                [s.hex() for s in signatures],
                [t.hex() for t in hit[1]],
            )
    print(
        f"parts={len(parts)} match={ok} mismatch={bad} unknown={unknown} unreadable={broken}"
    )


if __name__ == "__main__":
    main()
