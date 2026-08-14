import json
import pathlib
import re
import struct
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from convert.adapters.solidworks.container.Container import SldprtArchive

TRACE = ROOT / "re/data/segments"
STREAM = "Contents/Config-0-ResolvedFeatures"

WIDTHS = {
    "u8": 1,
    "i8": 1,
    "u16": 2,
    "i16": 2,
    "u32": 4,
    "i32": 4,
    "f32": 4,
    "u64": 8,
    "i64": 8,
    "f64": 8,
}


def load(label):
    doc = json.loads((TRACE / f"segments_{label}.json").read_text())
    part = pathlib.Path(doc["part"])
    if not part.exists():
        for base in (
            ROOT / ".rescratch/corpus/parts",
            ROOT / ".rescratch/corpus2",
            ROOT / ".rescratch/trace/parts",
            ROOT / "examples",
            ROOT / ".rescratch",
        ):
            hits = list(base.rglob(part.name))
            if hits:
                part = hits[0]
                break
    blob = SldprtArchive.open(part).require(STREAM)
    return doc, doc["segments"], blob, part


def resolve_name(segs, seg):
    name = seg["class_name"]
    m = re.match(r"backref->(\d+)$", name)
    if m:
        return segs[int(m.group(1))]["class_name"]
    return name


def children(segs, index):
    return [s for s in segs if s["parent"] == index]


def gaps(segs, index):
    parent = segs[index]
    kids = children(segs, index)
    cursor = parent["offset"] + parent["header"]
    out = []
    for kid in kids:
        if kid["offset"] > cursor:
            out.append(("scalars", cursor, kid["offset"] - cursor))
        name = resolve_name(segs, kid)
        if kid["kind"] in ("definition", "classref"):
            out.append(("object", kid["index"], name, kid["kind"], kid["tag"]))
            cursor = kid["scope_end"]
        else:
            out.append(("object", kid["index"], name, kid["kind"], kid["tag"]))
            cursor = kid["offset"] + 2
            if kid["scope_end"] > cursor:
                out.append(("scalars", cursor, kid["scope_end"] - cursor))
                cursor = kid["scope_end"]
    if parent["scope_end"] > cursor:
        out.append(("scalars", cursor, parent["scope_end"] - cursor))
    return out


def find(segs, name, kind=None):
    hits = []
    for seg in segs:
        if resolve_name(segs, seg) != name:
            continue
        if kind and seg["kind"] != kind:
            continue
        hits.append(seg["index"])
    return hits


def show(label, name, kind="definition"):
    doc, segs, blob, part = load(label)
    for index in find(segs, name, kind):
        parent = segs[index]
        print(
            f"--- {label} {part.name} {name} node={index} "
            f"span={parent['offset']}..{parent['scope_end']}"
        )
        for item in gaps(segs, index):
            if item[0] == "scalars":
                _, off, size = item
                if size == 0:
                    continue
                raw = blob[off : off + size]
                print(f"    scalars off={off:6d} n={size:4d} {raw.hex(' ')}")
                decode(raw)
            else:
                kid, kname, kkind, ktag = item[1], item[2], item[3], item[4]
                seg = segs[kid]
                span = (
                    seg["scope_end"] - seg["offset"]
                    if kkind in ("definition", "classref")
                    else 2
                )
                print(
                    f"    OBJECT  off={seg['offset']:6d} "
                    f"span={span:5d} tag=0x{ktag:04x} {kkind:10s} {kname}"
                )


def decode(raw):
    if len(raw) >= 8:
        for pos in range(0, len(raw) - 7):
            value = struct.unpack_from("<d", raw, pos)[0]
            if value != 0.0 and (1e-7 < abs(value) < 1e7):
                print(f"        f64@{pos}: {value!r}")
    for pos in range(0, len(raw) - 3, 1):
        value = struct.unpack_from("<I", raw, pos)[0]
        if 0 < value < 1 << 20 and pos % 2 == 0:
            print(f"        u32@{pos}: {value}")


def check(label, name, spec, kind="definition"):
    doc, segs, blob, part = load(label)
    results = []
    for index in find(segs, name, kind):
        items = gaps(segs, index)
        cursor = 0
        ok = True
        detail = []
        for item in items:
            if item[0] == "object":
                if cursor >= len(spec) or spec[cursor][0] != "obj":
                    ok = False
                    detail.append(
                        f"expected obj at spec[{cursor}] got {spec[cursor:cursor + 1]}"
                    )
                    break
                detail.append(f"obj {spec[cursor][1]} <- {item[2]} ({item[3]})")
                cursor += 1
                continue
            _, off, size = item
            used = 0
            while used < size and cursor < len(spec) and spec[cursor][0] != "obj":
                kind_name, field = spec[cursor][0], spec[cursor][1]
                width = WIDTHS[kind_name]
                if used + width > size:
                    break
                detail.append(f"{kind_name} {field} @{off + used}")
                used += width
                cursor += 1
            if used != size:
                ok = False
                detail.append(f"gap mismatch at off={off}: gap={size} consumed={used}")
                break
        if ok and cursor != len(spec):
            ok = False
            detail.append(f"spec has {len(spec) - cursor} unconsumed items")
        results.append((index, ok, detail))
    return results


def main():
    if len(sys.argv) < 3:
        print("Layout.py <label> <ClassName> [kind]")
        return
    kind = sys.argv[3] if len(sys.argv) > 3 else "definition"
    show(sys.argv[1], sys.argv[2], kind)


if __name__ == "__main__":
    main()
