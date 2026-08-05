import sys

from layout import find, gaps, load


def runs(label, name, kind):
    doc, segs, blob, part = load(label)
    out = []
    for index in find(segs, name, kind):
        seq = []
        for item in gaps(segs, index):
            if item[0] == "scalars":
                seq.append(("S", item[1], blob[item[1] : item[1] + item[2]]))
            else:
                seq.append(("O", item[2], item[3]))
        out.append((part.name, index, seq))
    return out


def main():
    name = sys.argv[1]
    left, right = sys.argv[2], sys.argv[3]
    kind = sys.argv[4] if len(sys.argv) > 4 else "definition"
    lrows = runs(left, name, kind)
    rrows = runs(right, name, kind)
    for (lp, li, lseq), (rp, ri, rseq) in zip(lrows, rrows):
        print(f"--- {name}: {lp} node={li}   vs   {rp} node={ri}")
        if len(lseq) != len(rseq):
            print(f"    SHAPE DIFFERS {len(lseq)} vs {len(rseq)}")
        for pos, (a, b) in enumerate(zip(lseq, rseq)):
            if a[0] != b[0]:
                print(f"    [{pos}] kind differs {a[0]} vs {b[0]}")
                continue
            if a[0] == "O":
                if a[1] != b[1]:
                    print(f"    [{pos}] object class {a[1]} vs {b[1]}")
                continue
            if a[2] == b[2]:
                continue
            print(f"    [{pos}] scalars n={len(a[2])}/{len(b[2])} at {a[1]}/{b[1]}")
            for k in range(min(len(a[2]), len(b[2]))):
                if a[2][k] != b[2][k]:
                    print(f"        +{k:4d}  {a[2][k]:02x} -> {b[2][k]:02x}")


if __name__ == "__main__":
    main()
