import pathlib
import struct
import sys

from gen_signature_table import BLOCK_OFFSET, ENTRY_COUNT, host_dll
from gen_signature_table import extract as extract_rows

HOST = host_dll(None)
ROOT = pathlib.Path(__file__).resolve().parents[3]


def extract(path=None):
    rows = extract_rows(path or HOST)
    return [
        (index, file_id, (triplet[0:4], triplet[4:8], triplet[8:12]))
        for index, (file_id, triplet) in enumerate(rows)
    ]


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
    print("host", HOST, "block", hex(BLOCK_OFFSET), "count", ENTRY_COUNT)
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
