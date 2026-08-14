import json
import pathlib
import re
import sys
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parents[3]
TRACE = ROOT / "re/data/segments"


def load():
    out = {}
    for path in sorted(TRACE.glob("segments_*.json")):
        out[path.stem[len("segments_") :]] = json.loads(path.read_text())
    return out


def resolve(doc):
    segs = doc["segments"]
    by_obj = {}
    for seg in segs:
        if seg["kind"] in ("definition", "classref"):
            by_obj[seg["object_index"]] = seg
    names = []
    for seg in segs:
        name = seg["class_name"]
        m = re.match(r"backref->(\d+)$", name)
        if m:
            tgt = segs[int(m.group(1))]
            name = tgt["class_name"]
        names.append(name)
    return segs, names


def main():
    want = [a for a in sys.argv[1:]]
    docs = load()
    table = defaultdict(lambda: defaultdict(list))
    for label, doc in docs.items():
        segs, names = resolve(doc)
        for seg, name in zip(segs, names):
            if want and not any(w.lower() in name.lower() for w in want):
                continue
            table[name][label].append(
                (seg["offset"], seg["length"], seg["depth"], seg["kind"])
            )
    for name in sorted(table):
        print("=" * 70)
        print(name)
        for label in sorted(table[name]):
            rows = table[name][label]
            lens = sorted({r[1] for r in rows})
            print(f"  {label:18s} n={len(rows):4d} lengths={lens}")
            for off, ln, depth, kind in rows[:12]:
                print(f"      off={off:6d} len={ln:5d} depth={depth} kind={kind}")


if __name__ == "__main__":
    main()
