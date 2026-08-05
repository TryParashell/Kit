import collections
import json
import pathlib
import struct
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from convert.adapters.solidworks.container import SldprtArchive

STREAM = "Contents/Config-0-ResolvedFeatures"
OUT = pathlib.Path(__file__).resolve().parents[3] / "re/data"

NAMES = {
    0: "Blind",
    1: "ThroughAll",
    2: "ThroughNext",
    3: "UpToVertex",
    4: "UpToSurface",
    5: "OffsetFromSurface",
    6: "MidPlane",
    7: "UpToBody",
    9: "ThroughAllBoth",
    10: "UpToSelection",
    11: "UpToNext",
}


def marker(name):
    body = name.encode("ascii")
    return b"\xff\xff\x01\x00" + struct.pack("<H", len(body)) + body


def parts(roots):
    for root in roots:
        for path in sorted((ROOT / root).rglob("*")):
            if path.suffix.upper() not in (".SLDPRT",):
                continue
            yield path


def decode(blob, pos, klass):
    data = pos + 6 + len(klass)
    if struct.unpack_from("<H", blob, data)[0] != 0:
        return None
    if struct.unpack_from("<H", blob, data + 14)[0] != 0:
        return None
    return {
        "data": data,
        "singleEnd": struct.unpack_from("<i", blob, data + 2)[0],
        "reverse1": struct.unpack_from("<i", blob, data + 6)[0],
        "reverse0": struct.unpack_from("<i", blob, data + 10)[0],
        "type0": struct.unpack_from("<i", blob, data + 16)[0],
        "type1": struct.unpack_from("<i", blob, data + 20)[0],
    }


def main():
    roots = sys.argv[1:] or [
        ".rescratch/corpus/parts",
        ".rescratch/corpus2",
        ".rescratch/trace/parts",
        "examples",
    ]
    klass = "moEndSpec_c"
    needle = marker(klass)
    histogram = collections.Counter()
    rows = []
    seen = 0
    skipped = 0
    for path in parts(roots):
        try:
            archive = SldprtArchive.open(path)
            blob = archive.get(STREAM)
        except Exception:
            continue
        if not blob:
            continue
        pos = blob.find(needle)
        if pos < 0:
            continue
        seen += 1
        record = decode(blob, pos, klass)
        if record is None:
            skipped += 1
            continue
        histogram[(record["type0"], record["type1"], record["reverse0"])] += 1
        rows.append(
            {
                "part": path.name.encode("ascii", "replace").decode("ascii"),
                "marker": pos,
                **record,
            }
        )
    print(
        f"parts with a moEndSpec_c definition: {seen}, decoded: {len(rows)}, rejected: {skipped}"
    )
    for key, count in sorted(histogram.items(), key=lambda kv: -kv[1]):
        t0, t1, rev = key
        print(
            f"  type0={t0:3d} ({NAMES.get(t0, '?'):18s}) type1={t1:3d} "
            f"({NAMES.get(t1, '?'):18s}) reverse={rev} n={count}"
        )
    for row in rows:
        if row["type0"] not in (0, 1, 6) or row["type1"] != 0:
            print(
                f"  NOTABLE {row['part']:44s} type0={row['type0']} type1={row['type1']}"
            )
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "scan_endspec.json").write_text(json.dumps(rows, indent=1))


if __name__ == "__main__":
    main()
