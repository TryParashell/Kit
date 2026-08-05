import collections
import json
import pathlib
import struct
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from convert.adapters.solidworks.container import SldprtArchive
from scan_endspec import NAMES, marker, parts

STREAM = "Contents/Config-0-ResolvedFeatures"
OUT = pathlib.Path(__file__).resolve().parents[3] / "re/data"
KLASS = "moRevEndSpec_c"


def decode(blob, data):
    tags = [struct.unpack_from("<H", blob, data + 20 + 2 * k)[0] for k in range(4)]
    if any(tag != 0 for tag in tags):
        return None
    return {
        "data": data,
        "singleEnd": struct.unpack_from("<i", blob, data)[0],
        "f138": struct.unpack_from("<i", blob, data + 4)[0],
        "f13c": struct.unpack_from("<i", blob, data + 8)[0],
        "type0": struct.unpack_from("<i", blob, data + 12)[0],
        "type1": struct.unpack_from("<i", blob, data + 16)[0],
        "d38": struct.unpack_from("<d", blob, data + 28)[0],
        "d40": struct.unpack_from("<d", blob, data + 36)[0],
        "offsetReverse0": struct.unpack_from("<i", blob, data + 44)[0],
        "offsetReverse1": struct.unpack_from("<i", blob, data + 48)[0],
    }


def main():
    roots = sys.argv[1:] or [
        ".rescratch/corpus/parts",
        ".rescratch/corpus2",
        "examples",
    ]
    needle = marker(KLASS)
    histogram = collections.Counter()
    rows = []
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
        record = decode(blob, pos + 6 + len(KLASS))
        if record is None:
            continue
        histogram[
            (
                record["type0"],
                record["type1"],
                record["singleEnd"],
                record["d38"],
                record["d40"],
            )
        ] += 1
        rows.append(
            {"part": path.name.encode("ascii", "replace").decode("ascii"), **record}
        )
    print(f"parts with a {KLASS} definition: {len(rows)}")
    for key, count in sorted(histogram.items(), key=lambda kv: -kv[1]):
        t0, t1, single, d38, d40 = key
        print(
            f"  type0={t0} ({NAMES.get(t0, '?')}) type1={t1} singleEnd={single} "
            f"d@0x38={d38!r} d@0x40={d40!r} n={count}"
        )
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "scan_revendspec.json").write_text(json.dumps(rows, indent=1))


if __name__ == "__main__":
    main()
