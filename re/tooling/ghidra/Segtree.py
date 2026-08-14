import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
TRACE = ROOT / "re/data/segments"


def main():
    label = sys.argv[1]
    lo = int(sys.argv[2])
    hi = int(sys.argv[3])
    doc = json.loads((TRACE / f"segments_{label}.json").read_text())
    segs = doc["segments"]
    for seg in segs:
        if seg["offset"] < lo or seg["offset"] > hi:
            continue
        name = seg["class_name"]
        m = re.match(r"backref->(\d+)$", name)
        if m:
            name = segs[int(m.group(1))]["class_name"] + " (backref)"
        print(
            f"{seg['index']:5d} off={seg['offset']:6d} len={seg['length']:5d} "
            f"end={seg['end']:6d} d={seg['depth']:2d} p={seg['parent']:5d} "
            f"tag=0x{seg['tag']:04x} {seg['kind']:10s} hdr={seg['header']:3d} {name}"
        )


if __name__ == "__main__":
    main()
