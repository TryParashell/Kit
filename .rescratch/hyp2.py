from __future__ import annotations

import json
import struct
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "src"))
from convert.adapters.solidworks.container import SldprtArchive  # noqa: E402

rows = json.loads((HERE / "scan.json").read_text(encoding="utf-8"))
M = 1 << 32


def bswap(v: int) -> int:
    return struct.unpack("<I", struct.pack(">I", v))[0]


print("=== header region: bytes 0..first_local_record ===")
for r in rows[:6]:
    p = Path(r["path"])
    blob = p.read_bytes()
    first = min(s["offset"] for s in r["streams"]) - 4
    print(f"  {p.name:34} first_local_sig_at={first}  head={blob[:24].hex()}")

print("\n=== do signature bytes appear anywhere else in the file/streams? ===")
for r in rows[:8]:
    p = Path(r["path"])
    blob = p.read_bytes()
    arch = SldprtArchive.from_bytes(blob, p)
    lsig = bytes.fromhex(r["local_sigs"][0])
    csig = bytes.fromhex(r["central_sigs"][0])
    esig = bytes.fromhex(r["end_sig"])
    fidb = struct.pack(">I", r["file_id"])
    fidl = struct.pack("<I", r["file_id"])
    counts = {n: blob.count(v) for n, v in (("L", lsig), ("C", csig), ("E", esig))}
    instream = {}
    for name, tag in (("L", lsig), ("C", csig), ("E", esig), ("fidBE", fidb), ("fidLE", fidl)):
        hits = [rec.name for rec in arch.records if tag in rec.data]
        instream[name] = hits[:4]
    print(f"  {p.name}")
    print(f"    raw occurrences: {counts} (expect n_streams for L/C, 1 for E)")
    for k, v in instream.items():
        print(f"    {k:6} found in streams: {v}")

print("\n=== GF(2)-affine between signatures themselves ===")
samples = []
seen = set()
for r in rows:
    k = (r["file_id"], r["local_sigs"][0])
    if k in seen:
        continue
    seen.add(k)
    samples.append(
        {
            "fid": r["file_id"],
            "L": struct.unpack(">I", bytes.fromhex(r["local_sigs"][0]))[0],
            "C": struct.unpack(">I", bytes.fromhex(r["central_sigs"][0]))[0],
            "E": struct.unpack(">I", bytes.fromhex(r["end_sig"]))[0],
        }
    )


def solve_gf2_affine(inputs, outputs):
    n = 33
    base = [([(x >> i) & 1 for i in range(32)] + [1], y) for x, y in zip(inputs, outputs)]
    for obit in range(32):
        mat = [b + [(y >> obit) & 1] for b, y in base]
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
        for i in range(r, len(mat)):
            if mat[i][n]:
                return False
    return True


for a, b in (("L", "C"), ("L", "E"), ("C", "E"), ("C", "L"), ("E", "L")):
    xs = [s[a] for s in samples]
    ys = [s[b] for s in samples]
    print(f"  {a} -> {b}: {'CONSISTENT' if solve_gf2_affine(xs, ys) else 'inconsistent'}")
for a in ("L", "C", "E"):
    xs = [bswap(s["fid"]) for s in samples]
    print(
        f"  bswap(fid) -> {a}: "
        f"{'CONSISTENT' if solve_gf2_affine(xs, [s[a] for s in samples]) else 'inconsistent'}"
    )

print("\n=== multiplicative: is sig * inv(fid) constant? ===")
for a in ("L", "C", "E"):
    ks = set()
    for s in samples:
        if s["fid"] % 2 == 1:
            ks.add((s[a] * pow(s["fid"], -1, M)) % M)
    print(f"  {a}/fid distinct ratios (odd fids): {len(ks)}")

print("\n=== per-byte independence: does byte k of L depend only on byte k of fid? ===")
for a in ("L", "C", "E"):
    ok = []
    for bytepos in range(4):
        mapping = {}
        good = True
        for s in samples:
            fb = (s["fid"] >> (8 * bytepos)) & 0xFF
            sb = (s[a] >> (8 * bytepos)) & 0xFF
            if mapping.setdefault(fb, sb) != sb:
                good = False
                break
        ok.append(good)
    print(f"  {a}: bytewise-consistent per position = {ok}")
