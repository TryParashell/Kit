from __future__ import annotations

import json
import struct
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
rows = json.loads((HERE / "scan.json").read_text(encoding="utf-8"))
AO = 8

diffs = Counter()
detail = []
for r in rows:
    blob = Path(r["path"]).read_bytes()
    _, _, de, te, dsize, doff, _ = r["end_fields"]
    cur = AO + doff
    total = 0
    names = []
    for _ in range(te):
        nl, el, cl2 = struct.unpack_from("<HHH", blob, cur + 28)
        nm = bytes(((v >> 4) | ((v & 0xF) << 4)) for v in blob[cur + 46 : cur + 46 + nl])
        names.append(nm.decode("utf-8", "replace"))
        step = 46 + nl + el + cl2
        total += step
        cur += step
    diffs[cur - r["end_offset"]] += 1
    detail.append((Path(r["path"]).name, total, dsize, cur - r["end_offset"], names))

print("=== central-dir walk: (cursor_after_walk - eocd_offset) ===")
print(f"  {dict(diffs)}")
n, total, dsize, d, names = detail[0]
print(f"\n  {n}: walked {total} bytes, eocd says dsize={dsize}, diff={d}")
print(f"  central names == live stream names: ", end="")
live = sorted(s["name"] for s in rows[0]["streams"])
print(sorted(names) == live)
print(f"  first/last central name: {names[0]!r} .. {names[-1]!r}")

print("\n=== does dsize count the 4-byte signatures? ===")
for n, total, dsize, d, names in detail[:8]:
    te = len(names)
    print(f"  {n:32} walked={total:6} dsize={dsize:6} diff={d:6} "
          f"entries={te} walked-4*te={total - 4*te}")

print("\n=== corrected walk: treat entry size as 42+nl (sig counted separately) ===")
ok = 0
for r in rows:
    blob = Path(r["path"]).read_bytes()
    _, _, de, te, dsize, doff, _ = r["end_fields"]
    cur = AO + doff
    sigs = set()
    offs = []
    for _ in range(te):
        sigs.add(blob[cur : cur + 4])
        nl, el, cl2 = struct.unpack_from("<HHH", blob, cur + 28)
        offs.append(struct.unpack_from("<I", blob, cur + 42)[0])
        cur += 46 + nl + el + cl2
    live_sigpos = sorted(s["offset"] - 4 - AO for s in r["streams"])
    good = (
        len(sigs) == 1
        and sorted(offs) == live_sigpos
        and all(
            blob[AO + o + 4 : AO + o + 10] == bytes.fromhex("140006000800")
            for o in offs
        )
    )
    if good:
        ok += 1
print(f"  files where all central local_offsets resolve to real local records "
      f"and central sig is unique: {ok}/{len(rows)}")
