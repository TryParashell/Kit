import sys
from collections import Counter

from layout import load, resolve_name


def names(label):
    doc, segs, blob, part = load(label)
    counter = Counter()
    for seg in segs:
        name = resolve_name(segs, seg)
        if name == "null" or name.startswith("external#"):
            continue
        counter[name] += 1
    return part.name, counter


def main():
    left, right = sys.argv[1], sys.argv[2]
    lname, lc = names(left)
    rname, rc = names(right)
    print(f"{left} = {lname}")
    print(f"{right} = {rname}")
    keys = sorted(set(lc) | set(rc))
    for key in keys:
        a, b = lc.get(key, 0), rc.get(key, 0)
        if a != b:
            print(f"  {key:40s} {a:4d} {b:4d}")


if __name__ == "__main__":
    main()
