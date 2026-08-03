from __future__ import annotations

import json
import struct
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
rows = json.loads((HERE / "scan.json").read_text(encoding="utf-8"))
PREFIX = bytes.fromhex("140006000800")

ratio = Counter()
total = 0
name_live = Counter()
sizes_match = Counter()
frag_counts = []
for r in rows:
    blob = Path(r["path"]).read_bytes()
    first = min(s["offset"] for s in r["streams"]) - 4
    live = {s["name"]: (s["csize"], s["usize"]) for s in r["streams"]}
    cur, n = 0, 0
    while True:
        m = blob.find(PREFIX, cur)
        if m < 0 or m >= first:
            break
        cur = m + 1
        crc, cs, us = struct.unpack_from("<III", blob, m + 10)
        nl = struct.unpack_from("<H", blob, m + 22)[0]
        raw = blob[m + 26 : m + 26 + nl]
        nm = bytes(((v >> 4) | ((v & 0xF) << 4)) for v in raw)
        try:
            name = nm.decode("utf-8")
        except UnicodeDecodeError:
            continue
        n += 1
        total += 1
        ratio[(crc == 4 * cs, us == 2 * cs)] += 1
        name_live[name in live] += 1
        if name in live:
            sizes_match[live[name] == (cs, us)] += 1
    frag_counts.append(n)

print(f"front-region local-header-shaped fragments across all files: {total}")
print(f"  per-file fragment count: min={min(frag_counts)} max={max(frag_counts)}")
print(f"  (crc==4*csize, usize==2*csize) pattern counts: {dict(ratio)}")
print(f"  fragment name is also a live stream name: {dict(name_live)}")
print(f"  fragment (csize,usize) equals the live stream's: {dict(sizes_match)}")

print("\ntail region after the live end-of-directory record:")
for r in rows[:3]:
    blob = Path(r["path"]).read_bytes()
    eo = r["end_offset"]
    tail = blob[eo + 22 :]
    hits = []
    for i in range(len(tail) - 22):
        dn, dd, de, te, ds, do, cl = struct.unpack_from("<HHHHIIH", tail, i + 4)
        if dn == 0 and dd == 0 and de == te == r["stream_count"] and cl == 0:
            hits.append((eo + 22 + i, tail[i : i + 4].hex(), ds, do))
    print(f"  {Path(r['path']).name}: tail={len(tail)}B, eocd-shaped records={len(hits)}")
    for off, sig, ds, do in hits[:6]:
        print(f"    at {off} sig={sig} dsize={ds} doff={do}")
