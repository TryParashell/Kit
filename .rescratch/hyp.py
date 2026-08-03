from __future__ import annotations

import json
import struct
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
rows = json.loads((HERE / "scan.json").read_text(encoding="utf-8"))

M = 1 << 32
ZIP_LOCAL = 0x04034B50
ZIP_CENTRAL = 0x02014B50
ZIP_END = 0x06054B50


def be(h: str) -> int:
    return struct.unpack(">I", bytes.fromhex(h))[0]


def le(h: str) -> int:
    return struct.unpack("<I", bytes.fromhex(h))[0]


samples = []
seen = set()
for r in rows:
    key = (r["file_id"], r["local_sigs"][0], r["central_sigs"][0], r["end_sig"])
    if key in seen:
        continue
    seen.add(key)
    samples.append(
        {
            "name": r["path"],
            "fid": r["file_id"],
            "L_be": be(r["local_sigs"][0]),
            "L_le": le(r["local_sigs"][0]),
            "C_be": be(r["central_sigs"][0]),
            "C_le": le(r["central_sigs"][0]),
            "E_be": be(r["end_sig"]),
            "E_le": le(r["end_sig"]),
        }
    )
print(f"unique samples: {len(samples)}")

print("\n=== H1: xor-with-zip-magic gives a single per-file key? ===")
for lab, kl, kc, ke in (
    ("LE sig ^ LE magic", "L_le", "C_le", "E_le"),
    ("BE sig ^ LE magic", "L_be", "C_be", "E_be"),
):
    agree = 0
    for s in samples:
        k1 = s[kl] ^ ZIP_LOCAL
        k2 = s[kc] ^ ZIP_CENTRAL
        k3 = s[ke] ^ ZIP_END
        if k1 == k2 == k3:
            agree += 1
    print(f"  {lab}: {agree}/{len(samples)} files where key_L==key_C==key_E")
s = samples[0]
print(f"  sample {Path(s['name']).name}: fid={s['fid']:#010x}")
for lab, v, magic in (
    ("L", s["L_be"], ZIP_LOCAL),
    ("C", s["C_be"], ZIP_CENTRAL),
    ("E", s["E_be"], ZIP_END),
):
    print(
        f"    {lab} be={v:#010x} ^magic={v ^ magic:#010x}   "
        f"le={struct.unpack('<I', struct.pack('>I', v))[0]:#010x} "
        f"^magic={struct.unpack('<I', struct.pack('>I', v))[0] ^ magic:#010x}"
    )

print("\n=== H2: fixed xor / delta between the three signatures? ===")
for a, b in (("L_be", "C_be"), ("L_be", "E_be"), ("C_be", "E_be")):
    xs = {samples[i][a] ^ samples[i][b] for i in range(len(samples))}
    ds = {(samples[i][a] - samples[i][b]) % M for i in range(len(samples))}
    print(f"  {a}^{b}: {len(xs)} distinct;  {a}-{b}: {len(ds)} distinct")

print("\n=== H3: direct equality / trivial transforms of file_id ===")


def rotl(v: int, n: int) -> int:
    return ((v << n) | (v >> (32 - n))) & 0xFFFFFFFF


def bswap(v: int) -> int:
    return struct.unpack("<I", struct.pack(">I", v))[0]


def bitrev(v: int) -> int:
    return int(format(v, "032b")[::-1], 2)


cands = {
    "fid": lambda f: f,
    "~fid": lambda f: f ^ 0xFFFFFFFF,
    "bswap(fid)": bswap,
    "bitrev(fid)": bitrev,
    "crc32(be4)": lambda f: zlib.crc32(struct.pack(">I", f)) & 0xFFFFFFFF,
    "crc32(le4)": lambda f: zlib.crc32(struct.pack("<I", f)) & 0xFFFFFFFF,
}
for n in range(1, 32):
    cands[f"rotl{n}(fid)"] = (lambda n: lambda f: rotl(f, n))(n)
for tgt in ("L_be", "L_le", "C_be", "C_le", "E_be", "E_le"):
    for cname, fn in cands.items():
        xs = {s[tgt] ^ fn(s["fid"]) for s in samples}
        ds = {(s[tgt] - fn(s["fid"])) % M for s in samples}
        if len(xs) == 1 or len(ds) == 1:
            print(f"  HIT {tgt} vs {cname}: xor-const={xs} delta-const={ds}")
print("  (no HIT lines above means every constant-offset/xor hypothesis failed)")

print("\n=== H4: GF(2)-affine map file_id -> signature ? ===")


def solve_gf2_affine(inputs: list[int], outputs: list[int]) -> list[int] | None:
    n = 33
    rowsm = []
    for x, y in zip(inputs, outputs):
        bits = [(x >> i) & 1 for i in range(32)] + [1]
        rowsm.append((bits, y))
    solution = []
    for obit in range(32):
        aug = [(list(b), (y >> obit) & 1) for b, y in rowsm]
        mat = [b + [t] for b, t in aug]
        pivots = {}
        r = 0
        for col in range(n):
            piv = next((i for i in range(r, len(mat)) if mat[i][col]), None)
            if piv is None:
                continue
            mat[r], mat[piv] = mat[piv], mat[r]
            for i in range(len(mat)):
                if i != r and mat[i][col]:
                    mat[i] = [a ^ b for a, b in zip(mat[i], mat[r])]
            pivots[col] = r
            r += 1
        for i in range(r, len(mat)):
            if mat[i][n]:
                return None
        coef = [0] * n
        for col, ri in pivots.items():
            coef[col] = mat[ri][n]
        solution.append(coef)
    return solution


fids = [s["fid"] for s in samples]
for tgt in ("L_be", "L_le", "C_be", "C_le", "E_be", "E_le"):
    outs = [s[tgt] for s in samples]
    sol = solve_gf2_affine(fids, outs)
    print(f"  {tgt}: {'CONSISTENT affine' if sol else 'inconsistent (ruled out)'}")

print("\n=== H5: LCG / affine mod 2^32:  y = a*x + c ===")


def solve_lcg(xs: list[int], ys: list[int]):
    for i in range(len(xs)):
        for j in range(i + 1, len(xs)):
            dx = (xs[i] - xs[j]) % M
            if dx % 2 == 0:
                continue
            a = ((ys[i] - ys[j]) * pow(dx, -1, M)) % M
            c = (ys[i] - a * xs[i]) % M
            if all((a * x + c) % M == y for x, y in zip(xs, ys)):
                return a, c
            break
    return None


pairs = [
    ("fid", "L_be"),
    ("fid", "L_le"),
    ("fid", "C_be"),
    ("fid", "E_be"),
    ("L_be", "C_be"),
    ("L_le", "C_le"),
    ("C_be", "E_be"),
    ("L_be", "E_be"),
]
for a, b in pairs:
    xs = [s[a] if a != "fid" else s["fid"] for s in samples]
    ys = [s[b] for s in samples]
    res = solve_lcg(xs, ys)
    print(f"  {a} -> {b}: {('a=%#010x c=%#010x' % res) if res else 'no affine fit'}")

print("\n=== H6: are signatures even injective in file_id? (collision check) ===")
byfid = {}
for s in samples:
    byfid.setdefault(s["fid"], set()).add((s["L_be"], s["C_be"], s["E_be"]))
multi = {k: v for k, v in byfid.items() if len(v) > 1}
print(f"  file_ids mapping to >1 triplet: {len(multi)}")
print(f"  distinct file_ids: {len(byfid)}  distinct triplets: {len(seen)}")

print("\n=== H7: bit-count / structure stats ===")
for tgt in ("fid", "L_be", "C_be", "E_be"):
    vals = [s[tgt] if tgt != "fid" else s["fid"] for s in samples]
    pop = [bin(v).count("1") for v in vals]
    print(f"  {tgt}: mean popcount {sum(pop)/len(pop):.2f}  min {min(pop)} max {max(pop)}")
