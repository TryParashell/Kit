import sys

from layout import find, gaps, load, resolve_name

LABELS = [
    "baseline",
    "circle",
    "planetop",
    "twopad",
    "padplane",
    "cutbase",
    "three",
    "vendor_ring",
    "vendor_cojinete",
]


def rows(label, name, kind):
    doc, segs, blob, part = load(label)
    out = []
    for index in find(segs, name, kind):
        seq = []
        for item in gaps(segs, index):
            if item[0] == "scalars":
                seq.append(("S", item[2], blob[item[1] : item[1] + item[2]]))
            else:
                seq.append(("O", item[2], item[3]))
        out.append((part.name, index, seq))
    return out


def main():
    name = sys.argv[1]
    kind = sys.argv[2] if len(sys.argv) > 2 else "definition"
    for label in LABELS:
        try:
            data = rows(label, name, kind)
        except Exception as problem:
            print(label, "ERROR", problem)
            continue
        for part, index, seq in data:
            if "-bytes" in sys.argv:
                print(f"{label:16s} {part[:30]:30s} node={index:4d}")
                for entry in seq:
                    if entry[0] == "S":
                        print(f"    S{entry[1]:<5d} {entry[2].hex(' ')}")
                    else:
                        print(f"    O     {entry[1]} ({entry[2]})")
                continue
            sig = " ".join(f"{k}{v}" if k == "S" else f"O:{v}" for k, v, *_ in seq)
            print(f"{label:16s} {part[:26]:26s} node={index:4d} {sig}")


if __name__ == "__main__":
    main()
