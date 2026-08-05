import collections
import json
import pathlib
import struct
import sys

import layout

OUT = pathlib.Path(__file__).resolve().parents[3] / "re/data"

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

HANDLE_CLASSES = (
    "sgEntHandle",
    "sgLineHandle",
    "sgArcHandle",
    "sgPointHandle",
)


def scalar_runs(segs, index, blob):
    runs = []
    for item in layout.gaps(segs, index):
        if item[0] == "scalars" and item[2] > 0:
            runs.append((item[1], blob[item[1] : item[1] + item[2]]))
    return runs


def decode_handle(raw):
    if len(raw) < 2:
        return None
    ent = struct.unpack_from("<H", raw, 0)[0]
    cursor = 2
    if ent == 0x777F:
        if len(raw) < 6:
            return None
        ent = struct.unpack_from("<i", raw, 2)[0]
        cursor = 6
    if len(raw) < cursor + 8:
        return None
    ref_id = struct.unpack_from("<i", raw, cursor)[0]
    dim_on_cm = struct.unpack_from("<i", raw, cursor + 4)[0]
    return {
        "bytes": cursor + 8,
        "escaped": cursor == 6,
        "EntIndex": ent,
        "RefId": ref_id,
        "DimOnCM": dim_on_cm,
    }


def main():
    report = {}
    total = 0
    passed = 0
    tally = collections.Counter()
    ent_values = collections.Counter()
    ref_values = collections.Counter()
    dim_values = collections.Counter()
    for label in LABELS:
        doc, segs, blob, part = layout.load(label)
        rows = []
        for name in HANDLE_CLASSES:
            for kind in ("definition", "classref"):
                for index in layout.find(segs, name, kind):
                    runs = scalar_runs(segs, index, blob)
                    total += 1
                    if not runs:
                        rows.append(
                            {"node": index, "class": name, "kind": kind, "ok": False}
                        )
                        tally[(name, kind, "no-scalars")] += 1
                        continue
                    offset, raw = runs[0]
                    decoded = decode_handle(raw)
                    ok = decoded is not None and decoded["bytes"] == len(raw)
                    if ok:
                        passed += 1
                        ent_values[decoded["EntIndex"]] += 1
                        ref_values[decoded["RefId"]] += 1
                        dim_values[decoded["DimOnCM"]] += 1
                    tally[(name, kind, "ok" if ok else "mismatch")] += 1
                    rows.append(
                        {
                            "node": index,
                            "class": name,
                            "kind": kind,
                            "ok": ok,
                            "first_run_bytes": len(raw),
                            "extra_runs": len(runs) - 1,
                            "decoded": decoded,
                        }
                    )
        report[label] = {"part": part.name, "handles": rows}
    for key in sorted(tally):
        print(f"{key[0]:16s} {key[1]:11s} {key[2]:12s} {tally[key]}")
    print(f"sgEntHandle chain: {passed}/{total} traced handle records tile exactly")
    print(f"EntIndex distinct={len(ent_values)} escaped_sentinel_used=0x777f")
    print(f"RefId  values {dict(sorted(ref_values.items())[:8])}")
    print(f"DimOnCM values {dict(sorted(dim_values.items())[:8])}")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "verify_sketch.json").write_text(json.dumps(report, indent=1))
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
