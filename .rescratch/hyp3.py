from __future__ import annotations

import json
import struct
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
rows = json.loads((HERE / "scan.json").read_text(encoding="utf-8"))
M32 = 0xFFFFFFFF

samples = []
seen = set()
for r in rows:
    key = (r["file_id"], r["local_sigs"][0])
    if key in seen:
        continue
    seen.add(key)
    blob = Path(r["path"]).read_bytes()
    first = min(s["offset"] for s in r["streams"]) - 4
    samples.append(
        {
            "name": Path(r["path"]).name,
            "fid": r["file_id"],
            "L": struct.unpack(">I", bytes.fromhex(r["local_sigs"][0]))[0],
            "C": struct.unpack(">I", bytes.fromhex(r["central_sigs"][0]))[0],
            "E": struct.unpack(">I", bytes.fromhex(r["end_sig"]))[0],
            "hdr": blob[8:first],
            "hdr_len": first - 8,
            "n": r["stream_count"],
        }
    )

print("=== front-region (offset 8 .. first accepted local signature) ===")
lens = sorted(s["hdr_len"] for s in samples)
print(f"  lengths: min={lens[0]} max={lens[-1]} distinct={len(set(lens))}")
for s in samples[:10]:
    print(f"  {s['name']:34} len={s['hdr_len']:6} first16={s['hdr'][:16].hex()}")
inflatable = 0
for s in samples:
    try:
        zlib.decompress(s["hdr"], wbits=-15)
        inflatable += 1
    except zlib.error:
        pass
print(f"  raw-deflate-inflatable front regions: {inflatable}/{len(samples)}")

print("\n=== known 32-bit mixers: fid -> L / C / E ===")


def rotl(v, n):
    return ((v << n) | (v >> (32 - n))) & M32


def rotr(v, n):
    return ((v >> n) | (v << (32 - n))) & M32


def murmur3_fmix(h):
    h ^= h >> 16
    h = (h * 0x85EBCA6B) & M32
    h ^= h >> 13
    h = (h * 0xC2B2AE35) & M32
    h ^= h >> 16
    return h


def splitmix32(z):
    z = (z + 0x9E3779B9) & M32
    z ^= z >> 16
    z = (z * 0x21F0AAAD) & M32
    z ^= z >> 15
    z = (z * 0x735A2D97) & M32
    z ^= z >> 15
    return z


def wang(k):
    k = (~k + (k << 15)) & M32
    k ^= k >> 12
    k = (k + (k << 2)) & M32
    k ^= k >> 4
    k = (k * 2057) & M32
    k ^= k >> 16
    return k


def xorshift32(x):
    x ^= (x << 13) & M32
    x ^= x >> 17
    x ^= (x << 5) & M32
    return x & M32


def fnv1a(v):
    h = 0x811C9DC5
    for b in struct.pack("<I", v):
        h = ((h ^ b) * 0x01000193) & M32
    return h


def fnv1a_be(v):
    h = 0x811C9DC5
    for b in struct.pack(">I", v):
        h = ((h ^ b) * 0x01000193) & M32
    return h


def jenkins(a):
    a = (a + 0x7ED55D16 + (a << 12)) & M32
    a = (a ^ 0xC761C23C ^ (a >> 19)) & M32
    a = (a + 0x165667B1 + (a << 5)) & M32
    a = ((a + 0xD3A2646C) ^ (a << 9)) & M32
    a = (a + 0xFD7046C5 + (a << 3)) & M32
    a = (a ^ 0xB55A4F09 ^ (a >> 16)) & M32
    return a


MIXERS = {
    "murmur3_fmix": murmur3_fmix,
    "splitmix32": splitmix32,
    "wang": wang,
    "xorshift32": xorshift32,
    "fnv1a_le": fnv1a,
    "fnv1a_be": fnv1a_be,
    "jenkins32": jenkins,
    "knuth_mul": lambda v: (v * 2654435761) & M32,
    "lcg_msvc": lambda v: (v * 214013 + 2531011) & M32,
    "lcg_glibc": lambda v: (v * 1103515245 + 12345) & M32,
    "lcg_numrec": lambda v: (v * 1664525 + 1013904223) & M32,
    "crc32": lambda v: zlib.crc32(struct.pack("<I", v)) & M32,
    "adler32": lambda v: zlib.adler32(struct.pack("<I", v)) & M32,
}
for i in range(1, 32):
    MIXERS[f"rotl{i}"] = (lambda i: lambda v: rotl(v, i))(i)


def bswap(v):
    return struct.unpack("<I", struct.pack(">I", v))[0]


hits = []
for tgt in ("L", "C", "E"):
    for src_name, src in (("fid", lambda s: s["fid"]), ("bswap(fid)", lambda s: bswap(s["fid"]))):
        for mname, fn in MIXERS.items():
            for post_name, post in (("", lambda v: v), ("bswap", bswap)):
                if all(post(fn(src(s))) == s[tgt] for s in samples):
                    hits.append(f"{tgt} = {post_name}({mname}({src_name}))")
                for depth in (2, 3):
                    pass
print(f"  direct mixer hits: {hits if hits else 'NONE'}")

print("\n=== 48-bit LCG (java.util.Random / drand48) consecutive-output test ===")


def test_lcg48(a, c, outs, shift=16, width=32):
    for low in range(1 << shift):
        seed = ((outs[0] & M32) << shift) | low
        ok = True
        st = seed
        for want in outs[1:]:
            st = (a * st + c) & ((1 << 48) - 1)
            got = (st >> (48 - width)) & M32
            if got != want:
                ok = False
                break
        if ok:
            return seed
    return None


found = 0
for s in samples[:6]:
    r1 = test_lcg48(0x5DEECE66D, 0xB, [s["fid"], s["L"], s["C"], s["E"]])
    if r1:
        found += 1
        print(f"  HIT java48 {s['name']} seed={r1:#014x}")
print(f"  java48 chained fid->L->C->E hits: {found}/6")

print("\n=== python/C++ mt19937 seeded with file_id ===")
import random

mt_hits = 0
for s in samples[:8]:
    rnd = random.Random(s["fid"])
    seq = [rnd.getrandbits(32) for _ in range(6)]
    if s["L"] in seq or s["C"] in seq or s["E"] in seq:
        mt_hits += 1
print(f"  python Random(fid) first-6 32-bit draws containing any signature: {mt_hits}/8")

print("\n=== relation to record/stream counts and offsets? ===")
print(
    "  end_sig vs stream_count correlation check:",
    len({(s["E"], s["n"]) for s in samples}),
    "pairs for",
    len({s["n"] for s in samples}),
    "distinct counts",
)

print("\n=== byte-level: any byte of L equal to any byte of fid consistently? ===")
for tgt in ("L", "C", "E"):
    tab = []
    for i in range(4):
        for j in range(4):
            if all(
                ((s[tgt] >> (8 * i)) & 0xFF) == ((s["fid"] >> (8 * j)) & 0xFF)
                for s in samples
            ):
                tab.append((i, j))
    print(f"  {tgt}: matching byte positions {tab}")

print("\n=== do L/C/E look uniformly random? (chi-square on bytes) ===")
for tgt in ("fid", "L", "C", "E"):
    buckets = [0] * 16
    for s in samples:
        v = s[tgt] if tgt != "fid" else s["fid"]
        for k in range(8):
            buckets[(v >> (4 * k)) & 0xF] += 1
    exp = len(samples) * 8 / 16
    chi = sum((b - exp) ** 2 / exp for b in buckets)
    print(f"  {tgt}: nibble chi2={chi:.1f} (df=15, ~<25 is plausible-uniform)")
