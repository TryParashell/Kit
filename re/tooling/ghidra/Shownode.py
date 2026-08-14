import struct
import sys

import layout


def dump(label, name, kind, limit):
    doc, segs, blob, part = layout.load(label)
    print(f"=== {label} {part.name} {name} {kind}")
    hits = layout.find(segs, name, kind)
    for index in hits[:limit]:
        parent = segs[index]
        print(
            f"--- node={index} kind={parent['kind']} "
            f"span={parent['offset']}..{parent['scope_end']} hdr={parent['header']}"
        )
        for item in layout.gaps(segs, index):
            if item[0] == "scalars":
                off, size = item[1], item[2]
                raw = blob[off : off + size]
                head = raw[:96].hex(" ")
                print(f"  scalars off={off} n={size} {head}")
                for pos in range(0, min(size, 96) - 3, 4):
                    value = struct.unpack_from("<I", raw, pos)[0]
                    print(f"      u32@{pos}=0x{value:08x} {value}")
            else:
                kid = segs[item[1]]
                span = (
                    kid["scope_end"] - kid["offset"]
                    if item[3] in ("definition", "classref")
                    else 2
                )
                print(
                    f"  OBJ off={kid['offset']} span={span} "
                    f"tag=0x{item[4]:04x} {item[3]} {item[2]}"
                )


def main():
    label = sys.argv[1]
    name = sys.argv[2]
    kind = sys.argv[3] if len(sys.argv) > 3 else "definition"
    limit = int(sys.argv[4]) if len(sys.argv) > 4 else 2
    dump(label, name, kind, limit)


if __name__ == "__main__":
    main()
