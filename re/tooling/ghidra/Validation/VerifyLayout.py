import json
import pathlib
import struct
import sys

from layout import find, gaps, load

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

MO_END_SPEC = [
    ("obj", "dirSpec@0x138"),
    ("i32", "singleEnd@0x08"),
    ("i32", "reverse1@0x88"),
    ("i32", "reverse0@0x8c"),
    ("obj", "keepPiece@0x90"),
    ("i32", "type0@0x0c"),
    ("i32", "type1@0x10"),
    ("obj", "distanceDim0@0x18"),
    ("obj", "distanceDim1@0x20"),
    ("u8", "surfArrayPresent0"),
    ("u16", "surfArray0@0x28"),
    ("u8", "surfArrayPresent1"),
    ("u16", "surfArray1@0x48"),
    ("f64", "f64@0xa0"),
    ("i32", "draftCheck0@0xb8"),
    ("i32", "draftCheck1@0xbc"),
    ("i32", "draftDir0@0xc0"),
    ("i32", "draftDir1@0xc4"),
    ("i32", "translateSurf0@0xb0"),
    ("i32", "translateSurf1@0xb4"),
    ("obj", "angleDim0@0xc8"),
    ("obj", "angleDim1@0xd0"),
    ("i32", "f@0xa8"),
    ("i32", "f@0xac"),
    ("i32", "f@0xd8"),
    ("i32", "f@0xdc"),
    ("u16", "sub@0xe0"),
    ("u16", "sub@0x100"),
    ("i32", "f@0x128"),
    ("i32", "f@0x12c"),
    ("i32", "f@0x130"),
    ("obj", "fromEndSpec@0x140"),
]

MO_REV_END_SPEC = [
    ("i32", "singleEnd@0x08"),
    ("i32", "f@0x138"),
    ("i32", "f@0x13c"),
    ("i32", "type0@0x0c"),
    ("i32", "type1@0x10"),
    ("obj", "iSurfRef0@0x118"),
    ("obj", "iSurfRef1@0x120"),
    ("obj", "upToPointRef0@0x128"),
    ("obj", "upToPointRef1@0x130"),
    ("f64", "f64@0x38"),
    ("f64", "f64@0x40"),
    ("i32", "offsetReverse0@0x140"),
    ("i32", "offsetReverse1@0x144"),
    ("obj", "angleDim0@0x18"),
    ("obj", "angleDim1@0x20"),
    ("obj", "offsetDim0@0x28"),
    ("obj", "offsetDim1@0x30"),
]

WIDTHS = {"u8": 1, "i8": 1, "u16": 2, "i16": 2, "u32": 4, "i32": 4, "f32": 4, "f64": 8}


def walk(segs, blob, index, spec):
    items = gaps(segs, index)
    cursor = 0
    values = []
    for item in items:
        if item[0] == "object":
            if cursor >= len(spec) or spec[cursor][0] != "obj":
                return (
                    False,
                    f"expected obj, spec[{cursor}]={spec[cursor:cursor + 1]}",
                    values,
                )
            values.append((spec[cursor][1], "obj:" + item[2]))
            cursor += 1
            continue
        _, off, size = item
        used = 0
        while used < size:
            if cursor >= len(spec):
                return (
                    False,
                    f"spec exhausted with {size - used} bytes left at {off + used}",
                    values,
                )
            kind, name = spec[cursor]
            if kind == "obj":
                return (
                    False,
                    f"expected scalar at {off + used}, spec says obj {name}",
                    values,
                )
            width = WIDTHS[kind]
            if used + width > size:
                return (
                    False,
                    f"field {name} ({kind}) overruns gap at {off + used}",
                    values,
                )
            raw = blob[off + used : off + used + width]
            if kind == "f64":
                value = struct.unpack("<d", raw)[0]
            elif kind in ("i32", "u32"):
                value = struct.unpack("<i" if kind == "i32" else "<I", raw)[0]
            elif kind in ("u16", "i16"):
                value = struct.unpack("<H", raw)[0]
            else:
                value = raw[0]
            values.append((name, value))
            used += width
            cursor += 1
        if used != size:
            return False, f"gap mismatch at {off}", values
    if cursor != len(spec):
        return False, f"{len(spec) - cursor} spec items unconsumed", values
    return True, "ok", values


def tail(segs, blob, index):
    kids = [s for s in segs if s["parent"] == index]
    if not kids:
        return None
    last = kids[-1]
    start = last["offset"] + last["header"]
    size = last["scope_end"] - start
    raw = blob[start : start + size]
    candidates = []
    for end_spec_bytes in (20, 16):
        need = 4 + end_spec_bytes + 12
        if size not in (need, need + 4):
            continue
        cursor = 0
        out = {
            "run_size": size,
            "end_spec_tail_bytes": end_spec_bytes,
            "driver_trailer": size - need,
            "fromEndSpec_type": struct.unpack_from("<i", raw, 0)[0],
        }
        cursor = 4
        labels = [
            "capEnd0@0x148",
            "capEnd1@0x14c",
            "delInitFace@0x150",
            "knitRes@0x154",
        ]
        if end_spec_bytes == 20:
            labels.append("createSolid@0x158")
        for label in labels:
            out[label] = struct.unpack_from("<I", raw, cursor)[0]
            cursor += 4
        value = struct.unpack_from("<d", raw, cursor)[0]
        out["extrusion_f64@0x7d0"] = value
        cursor += 8
        out["extrusion_long@0x7a8"] = struct.unpack_from("<I", raw, cursor)[0]
        out["plausible"] = value == value and abs(value) < 1e6
        candidates.append(out)
    for out in candidates:
        if out["plausible"]:
            return out
    if candidates:
        return candidates[0]
    return {"run_size": size, "error": "no budget fits"}


def main():
    report = {}
    total = 0
    passed = 0
    for label in LABELS:
        doc, segs, blob, part = load(label)
        rows = []
        indices = find(segs, "moEndSpec_c", "definition") + find(
            segs, "moEndSpec_c", "classref"
        )
        for index in indices:
            ok, message, values = walk(segs, blob, index, MO_END_SPEC)
            total += 1
            passed += 1 if ok else 0
            named = {k: v for k, v in values}
            rows.append(
                {
                    "node": index,
                    "offset": segs[index]["offset"],
                    "ok": ok,
                    "message": message,
                    "type0": named.get("type0@0x0c"),
                    "type1": named.get("type1@0x10"),
                    "reverse0": named.get("reverse0@0x8c"),
                    "singleEnd": named.get("singleEnd@0x08"),
                    "fields": [[k, v] for k, v in values],
                }
            )
            print(
                f"{label:16s} {part.name[:28]:28s} moEndSpec_c node={index:4d} "
                f"{'PASS' if ok else 'FAIL'} {message} "
                f"type0={named.get('type0@0x0c')} type1={named.get('type1@0x10')} "
                f"rev={named.get('reverse0@0x8c')} single={named.get('singleEnd@0x08')}"
            )
        tails = []
        for index in find(segs, "moEndSpec_c", "definition"):
            info = tail(segs, blob, index)
            tails.append({"node": index, **(info or {})})
            print(f"{label:16s} tail node={index:4d} {info}")
        report[label] = {"part": part.name, "moEndSpec_c": rows, "tails": tails}
    print(f"moEndSpec_c: {passed}/{total} objects reproduce the traced spans exactly")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "VerifyLayout.json").write_text(json.dumps(report, indent=1))
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
