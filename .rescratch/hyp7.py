from __future__ import annotations

import json
import struct
from pathlib import Path

HERE = Path(__file__).resolve().parent
rows = json.loads((HERE / "scan.json").read_text(encoding="utf-8"))


def bswap(v):
    return struct.unpack("<I", struct.pack(">I", v))[0]


samples = []
seen = set()
for r in rows:
    k = (r["file_id"], r["local_sigs"][0])
    if k in seen:
        continue
    seen.add(k)
    Lb = struct.unpack(">I", bytes.fromhex(r["local_sigs"][0]))[0]
    Cb = struct.unpack(">I", bytes.fromhex(r["central_sigs"][0]))[0]
    Eb = struct.unpack(">I", bytes.fromhex(r["end_sig"]))[0]
    samples.append(
        {
            "fid": r["file_id"],
            "fid_sw": bswap(r["file_id"]),
            "Lb": Lb, "Cb": Cb, "Eb": Eb,
            "Ll": bswap(Lb), "Cl": bswap(Cb), "El": bswap(Eb),
        }
    )
N = len(samples)


def bit_consistency(xs, ys):
    n = 33
    base = [([(x >> i) & 1 for i in range(32)] + [1], y) for x, y in zip(xs, ys)]
    out = []
    for ob in range(32):
        mat = [b + [(y >> ob) & 1] for b, y in base]
        r = 0
        for col in range(n):
            piv = next((i for i in range(r, len(mat)) if mat[i][col]), None)
            if piv is None:
                continue
            mat[r], mat[piv] = mat[piv], mat[r]
            for i in range(len(mat)):
                if i != r and mat[i][col]:
                    mat[i] = [a ^ b for a, b in zip(mat[i], mat[r])]
            r += 1
        consistent = not any(mat[i][n] for i in range(r, len(mat)))
        out.append(consistent)
    return out


print(f"samples={N}; per-output-bit GF(2)-affine consistency (33 unknowns, {N} eqs)")
print("bit index 0 (LSB) .. 31; '.'=inconsistent, 'A'=affine-consistent")
for src in ("fid", "fid_sw"):
    for tgt in ("Lb", "Ll", "Cb", "Cl", "Eb", "El"):
        res = bit_consistency([s[src] for s in samples], [s[tgt] for s in samples])
        line = "".join("A" if c else "." for c in res)
        print(f"  {src:6} -> {tgt:3}: {line}  ({sum(res)}/32 affine)")

print("\nsignature-to-signature:")
for a, b in (("Lb", "Cb"), ("Cb", "Eb"), ("Lb", "Eb"), ("Ll", "Cl"), ("Ll", "El")):
    res = bit_consistency([s[a] for s in samples], [s[b] for s in samples])
    print(f"  {a} -> {b}: {''.join('A' if c else '.' for c in res)} ({sum(res)}/32)")

print("\nsanity control: fid -> fid (must be all affine)")
res = bit_consistency([s["fid"] for s in samples], [s["fid"] for s in samples])
print(f"  {''.join('A' if c else '.' for c in res)} ({sum(res)}/32)")

print("\nsanity control: fid -> murmur3_fmix(fid) (nonlinear mixer, expect few affine)")


def fmix(h):
    h ^= h >> 16
    h = (h * 0x85EBCA6B) & 0xFFFFFFFF
    h ^= h >> 13
    h = (h * 0xC2B2AE35) & 0xFFFFFFFF
    h ^= h >> 16
    return h


res = bit_consistency([s["fid"] for s in samples], [fmix(s["fid"]) for s in samples])
print(f"  {''.join('A' if c else '.' for c in res)} ({sum(res)}/32)")

print("\nsanity control: fid -> random-but-fixed permutation (expect ~0 affine)")
import random as _r

_r.seed(7)
tbl = {s["fid"]: _r.getrandbits(32) for s in samples}
res = bit_consistency([s["fid"] for s in samples], [tbl[s["fid"]] for s in samples])
print(f"  {''.join('A' if c else '.' for c in res)} ({sum(res)}/32)")
