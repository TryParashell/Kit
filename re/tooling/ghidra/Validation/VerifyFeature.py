import collections
import json
import pathlib
import struct
import sys

import layout

OUT = pathlib.Path(__file__).resolve().parents[4] / "re/data"

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

STRING_MARKER = bytes.fromhex("fffeff")


def read_string(blob, cursor):
    if blob[cursor : cursor + 3] != STRING_MARKER:
        return None
    count = blob[cursor + 3]
    if count == 0xFF:
        count = struct.unpack_from("<H", blob, cursor + 4)[0]
        head = cursor + 6
    else:
        head = cursor + 4
    end = head + 2 * count
    if end > len(blob):
        return None
    try:
        text = blob[head:end].decode("utf-16-le")
    except UnicodeDecodeError:
        return None
    return text, end


def decode_node(blob, cursor, limit):
    name = read_string(blob, cursor)
    if name is None:
        return None
    text, cursor = name
    if cursor + 16 > limit:
        return None
    word_0c = struct.unpack_from("<I", blob, cursor)[0]
    flags = struct.unpack_from("<I", blob, cursor + 4)[0]
    node_id = struct.unpack_from("<i", blob, cursor + 8)[0]
    word_2c = struct.unpack_from("<I", blob, cursor + 12)[0]
    cursor += 16
    trailer = read_string(blob, cursor)
    if trailer is None:
        return None
    trailer_text, cursor = trailer
    return {
        "name": text,
        "word@0x0c": word_0c,
        "flags@0x28": flags,
        "id@0x08": node_id,
        "word@0x2c": word_2c,
        "trailer@0x20": trailer_text,
        "end": cursor,
    }


def node_records(segs, blob, index):
    parent = segs[index]
    kids = [seg for seg in segs if seg["parent"] == index]
    if not kids:
        return None
    first = kids[0]
    if first["offset"] != parent["offset"] + parent["header"]:
        return None
    body = first["offset"] + (2 if first["kind"] in ("classref", "objectref") else 0)
    if first["kind"] not in ("classref", "objectref"):
        return None
    return decode_node(blob, body, parent["scope_end"])


def main():
    report = {}
    total = 0
    decoded = 0
    flags_seen = collections.Counter()
    by_class = collections.Counter()
    for label in LABELS:
        doc, segs, blob, part = layout.load(label)
        rows = []
        for seg in segs:
            if seg["kind"] != "definition" and seg["kind"] != "classref":
                continue
            name = layout.resolve_name(segs, seg)
            if not name.startswith("mo"):
                continue
            record = node_records(segs, blob, seg["index"])
            if record is None:
                continue
            total += 1
            decoded += 1
            flags_seen[record["flags@0x28"]] += 1
            by_class[name] += 1
            rows.append({"node": seg["index"], "class": name, **record})
        report[label] = {"part": part.name, "nodes": rows}
        for row in rows:
            print(
                f"{label:16s} {row['class'][:26]:26s} node={row['node']:4d} "
                f"name={row['name'][:26]:26s} "
                f"flags=0x{row['flags@0x28']:08x} id={row['id@0x08']:6d} "
                f"w0c=0x{row['word@0x0c']:08x} w2c=0x{row['word@0x2c']:08x}"
            )
    print(f"moNode_c prefix decoded on {decoded}/{total} candidate objects")
    print("distinct tree-flags words:")
    for value, count in sorted(flags_seen.items()):
        print(f"  0x{value:08x} n={count}")
    print(f"classes covered: {len(by_class)}")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "VerifyFeature.json").write_text(json.dumps(report, indent=1))
    return 0 if decoded == total and decoded else 1


if __name__ == "__main__":
    sys.exit(main())
