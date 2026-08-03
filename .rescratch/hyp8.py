from __future__ import annotations

import json
import struct
from pathlib import Path

HERE = Path(__file__).resolve().parent
rows = json.loads((HERE / "scan.json").read_text(encoding="utf-8"))
MASK = 0xFFFFFFFF
ZIP = (0x04034B50, 0x02014B50, 0x06054B50)

trip = []
seen = set()
for r in rows:
    k = (r["file_id"], r["local_sigs"][0])
    if k in seen:
        continue
    seen.add(k)
    trip.append(
        (
            r["file_id"],
            bytes.fromhex(r["local_sigs"][0]),
            bytes.fromhex(r["central_sigs"][0]),
            bytes.fromhex(r["end_sig"]),
            Path(r["path"]).name,
        )
    )


def rotl(v, n):
    n %= 32
    return ((v << n) | (v >> (32 - n))) & MASK if n else v


def bitrev(v):
    return int(format(v, "032b")[::-1], 2)


def bswap(v):
    return struct.unpack("<I", struct.pack(">I", v))[0]


def nibswap(v):
    b = struct.pack("<I", v)
    return struct.unpack("<I", bytes(((x >> 4) | ((x & 0xF) << 4)) for x in b))[0]


PERMS = {"id": lambda v: v, "bswap": bswap, "bitrev": bitrev, "nibswap": nibswap}
for i in range(1, 32):
    PERMS[f"rotl{i}"] = (lambda i: lambda v: rotl(v, i))(i)
    PERMS[f"bswap.rotl{i}"] = (lambda i: lambda v: bswap(rotl(v, i)))(i)

print("=== single-key XOR under a magic-side permutation (per-file solve) ===")
best = {}
for pname, perm in PERMS.items():
    for read in ("be", "le"):
        hits = 0
        for fid, L, C, E, nm in trip:
            fmt = ">I" if read == "be" else "<I"
            l, c, e = (struct.unpack(fmt, x)[0] for x in (L, C, E))
            k1 = l ^ perm(ZIP[0])
            k2 = c ^ perm(ZIP[1])
            k3 = e ^ perm(ZIP[2])
            if k1 == k2 == k3:
                hits += 1
        if hits:
            best[f"{pname}/{read}"] = hits
print(f"  permutations giving a consistent single XOR key: {best or 'NONE'}")

print("\n=== single-key ADD/SUB under permutation ===")
addhits = {}
for pname, perm in PERMS.items():
    for read in ("be", "le"):
        hits = 0
        for fid, L, C, E, nm in trip:
            fmt = ">I" if read == "be" else "<I"
            l, c, e = (struct.unpack(fmt, x)[0] for x in (L, C, E))
            k1 = (l - perm(ZIP[0])) & MASK
            k2 = (c - perm(ZIP[1])) & MASK
            k3 = (e - perm(ZIP[2])) & MASK
            if k1 == k2 == k3:
                hits += 1
        if hits:
            addhits[f"{pname}/{read}"] = hits
print(f"  permutations giving a consistent single ADD key: {addhits or 'NONE'}")

print("\n=== per-file: does ANY rotation r make the three XOR keys agree? ===")
agree = 0
for fid, L, C, E, nm in trip:
    for read in ("be", "le"):
        fmt = ">I" if read == "be" else "<I"
        l, c, e = (struct.unpack(fmt, x)[0] for x in (L, C, E))
        for r in range(32):
            if (
                l ^ rotl(ZIP[0], r)
                == c ^ rotl(ZIP[1], r)
                == e ^ rotl(ZIP[2], r)
            ):
                agree += 1
                print(f"  HIT {nm} read={read} r={r}")
print(f"  files with any rotation making keys agree: {agree}/{len(trip)}")

print("\n=== structural: do the three signatures preserve the zip magics' own relations? ===")
print("  zip: C = L - 0x02020000, E = L + 0x02020000 (LE ints); L^C=0x06020000, L^E=0x02060000")
d1 = set()
d2 = set()
x1 = set()
for fid, L, C, E, nm in trip:
    l, c, e = (struct.unpack("<I", x)[0] for x in (L, C, E))
    d1.add((l - c) & MASK)
    d2.add((e - l) & MASK)
    x1.add(l ^ c)
print(f"  observed distinct (L-C)={len(d1)}, (E-L)={len(d2)}, (L^C)={len(x1)} over {len(trip)} files")

print("\n=== do the two hardcoded ids' triplets match their corpus files? ===")
for fid, L, C, E, nm in trip:
    if fid in (0xEC6E2386, 0x715BE98F):
        print(f"  {nm}: fid={fid:#010x} L={L.hex()} C={C.hex()} E={E.hex()}")

print("\n=== front/tail region: 4 bytes preceding each stale local-header fragment ===")
PREFIX = bytes.fromhex("140006000800")
for r in rows[:3]:
    blob = Path(r["path"]).read_bytes()
    first = min(s["offset"] for s in r["streams"]) - 4
    pre = []
    cur = 0
    while True:
        m = blob.find(PREFIX, cur)
        if m < 0 or m >= first:
            break
        cur = m + 1
        pre.append(blob[m - 4 : m].hex())
    print(f"  {Path(r['path']).name}: live_sig={r['local_sigs'][0]} "
          f"front fragments preceded by {pre}")
