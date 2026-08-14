import pathlib
import struct
import sys

SW = pathlib.Path(r"C:\Program Files\SOLIDWORKS Corp\SOLIDWORKS")

VALUES = [
    ("file_id_default", 0xEC6E2386),
    ("file_id_alt", 0x715BE98F),
    ("local_1", 0x64D80045),
    ("central_1", 0xAE0D4EF6),
    ("end_1", 0x54CE179A),
    ("local_2", 0xA1909B1F),
    ("central_2", 0xA576970F),
    ("end_2", 0x7A004720),
]


def needles():
    out = []
    for name, value in VALUES:
        out.append((name + "_le", struct.pack("<I", value)))
        out.append((name + "_be", struct.pack(">I", value)))
    return out


def main():
    roots = [SW]
    if len(sys.argv) > 1:
        roots = [pathlib.Path(a) for a in sys.argv[1:]]
    pats = needles()
    for root in roots:
        files = sorted(root.rglob("*.dll")) + sorted(root.rglob("*.exe"))
        for path in files:
            try:
                blob = path.read_bytes()
            except OSError:
                continue
            hits = []
            for name, pat in pats:
                start = 0
                while True:
                    idx = blob.find(pat, start)
                    if idx < 0:
                        break
                    hits.append((name, idx))
                    start = idx + 1
                    if len(hits) > 40:
                        break
            if hits:
                print(path.name, len(blob))
                for name, idx in hits[:40]:
                    print(f"   {name} @ 0x{idx:x}")


if __name__ == "__main__":
    main()
