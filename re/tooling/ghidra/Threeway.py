import sys

from layout import gaps, load, resolve_name


def collect(label, names):
    doc, segs, blob, part = load(label)
    out = []
    for seg in segs:
        name = resolve_name(segs, seg)
        if name not in names:
            continue
        if seg["kind"] not in ("definition", "classref"):
            continue
        seq = []
        for item in gaps(segs, seg["index"]):
            if item[0] == "scalars":
                seq.append(("S", item[1], blob[item[1] : item[1] + item[2]]))
            else:
                seq.append(("O", item[2], item[3]))
        out.append((seg["index"], name, seg["kind"], seg["offset"], seq))
    return part.name, out


def shape(seq):
    return tuple((e[0], len(e[2]) if e[0] == "S" else 0) for e in seq)


def main():
    label = sys.argv[1]
    names = set(sys.argv[2:]) or {"moExtrusion_c", "moICE_c"}
    part, rows = collect(label, names)
    print(f"{label} = {part}")
    for index, name, kind, offset, seq in rows:
        print(f"  node={index:4d} {kind:10s} off={offset:6d} {name} shape={shape(seq)}")
    groups = {}
    for row in rows:
        groups.setdefault(shape(row[4]), []).append(row)
    for key, members in groups.items():
        if len(members) < 2:
            continue
        print(f"--- shape group with {len(members)} members")
        base = members[0]
        for other in members[1:]:
            print(f"    node {base[0]} vs {other[0]}")
            for pos, (a, b) in enumerate(zip(base[4], other[4])):
                if a[0] != "S" or a[2] == b[2]:
                    continue
                diffs = [k for k in range(len(a[2])) if a[2][k] != b[2][k]]
                print(f"      [{pos}] n={len(a[2])} ndiff={len(diffs)} at {diffs[:24]}")
                for k in diffs[:24]:
                    print(f"          +{k:4d} {a[2][k]:02x} -> {b[2][k]:02x}")


if __name__ == "__main__":
    main()
