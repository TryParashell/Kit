from __future__ import annotations

import hashlib
import json
import struct
import zlib
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
rows = json.loads((HERE / "scan.json").read_text(encoding="utf-8"))
M = 1 << 32
M32 = M - 1
ARCHIVE_OFFSET = 8
PREFIX = bytes.fromhex("140006000800")

print("=== A. ZIP structural equivalence ===")
bad = []
for r in rows:
    blob = Path(r["path"]).read_bytes()
    eoff = r["end_offset"]
    dn, dd, de, te, dsize, doff, clen = r["end_fields"]
    checks = {
        "eocd_at_eof_minus_22": eoff == len(blob) - 22,
        "comment_len_zero": clen == 0,
        "entries_match_streams": de == te == r["stream_count"],
        "central_offset_consistent": ARCHIVE_OFFSET + doff + dsize == eoff,
    }
    ver_flags_method = set()
    for s in r["streams"]:
        ver_flags_method.add(blob[s["offset"] : s["offset"] + 6].hex())
    checks["local_vfm_constant"] = ver_flags_method == {"140006000800"}
    if not all(checks.values()):
        bad.append((r["path"], checks))
print(f"  files satisfying all ZIP structure checks: {len(rows) - len(bad)}/{len(rows)}")
for p, c in bad[:5]:
    print(f"    {p}: {c}")

print("\n=== B. central-directory local_offset -> does it point at the signature? ===")
mismatch = 0
front_from_cd = []
for r in rows:
    blob = Path(r["path"]).read_bytes()
    dn, dd, de, te, dsize, doff, clen = r["end_fields"]
    cur = ARCHIVE_OFFSET + doff
    offsets = []
    for _ in range(te):
        namelen = struct.unpack_from("<H", blob, cur + 28)[0]
        extralen = struct.unpack_from("<H", blob, cur + 30)[0]
        commentlen = struct.unpack_from("<H", blob, cur + 32)[0]
        local_off = struct.unpack_from("<I", blob, cur + 42)[0]
        offsets.append(local_off)
        cur += 46 + namelen + extralen + commentlen
    ends_at_eocd = cur == r["end_offset"]
    actual = sorted(s["offset"] - 4 - ARCHIVE_OFFSET for s in r["streams"])
    ok = sorted(offsets) == actual
    if not (ok and ends_at_eocd):
        mismatch += 1
    front_from_cd.append(min(offsets))
print(f"  files where every central local_offset lands on a local signature: "
      f"{len(rows) - mismatch}/{len(rows)}")
print(f"  min local_offset (i.e. prepended-junk length) range: "
      f"{min(front_from_cd)}..{max(front_from_cd)}")

print("\n=== C. what is the 4-byte field after 14 00 06 00 08 00 ? (ZIP modtime+moddate) ===")
cnt = Counter(s["type_id"] for r in rows for s in r["streams"])
for v, n in cnt.most_common(12):
    t = v & 0xFFFF
    d = (v >> 16) & 0xFFFF
    y, mo, da = 1980 + (d >> 9), (d >> 5) & 0xF, d & 0x1F
    h, mi, se = t >> 11, (t >> 5) & 0x3F, (t & 0x1F) * 2
    valid = 1 <= mo <= 12 and 1 <= da <= 31 and h < 24 and mi < 60 and se < 60
    print(f"  {v:#010x} x{n:<5} time={t:#06x} date={d:#06x} -> "
          f"{y:04d}-{mo:02d}-{da:02d} {h:02d}:{mi:02d}:{se:02d}  dos_valid={valid}")

print("\n=== D. signature keys K = sig XOR zip magic: pairwise relations ===")
ZL, ZC, ZE = 0x04034B50, 0x02014B50, 0x06054B50


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
            "Lb": Lb,
            "Cb": Cb,
            "Eb": Eb,
            "Ll": bswap(Lb),
            "Cl": bswap(Cb),
            "El": bswap(Eb),
            "K1b": Lb ^ ZL,
            "K2b": Cb ^ ZC,
            "K3b": Eb ^ ZE,
            "K1l": bswap(Lb) ^ ZL,
            "K2l": bswap(Cb) ^ ZC,
            "K3l": bswap(Eb) ^ ZE,
        }
    )


def solve_lcg(xs, ys):
    for i in range(len(xs)):
        for j in range(i + 1, len(xs)):
            dx = (xs[i] - xs[j]) % M
            if dx % 2 == 0:
                continue
            a = ((ys[i] - ys[j]) * pow(dx, -1, M)) % M
            c = (ys[i] - a * xs[i]) % M
            if all((a * x + c) % M == y for x, y in zip(xs, ys)):
                return a, c
            return None
    return None


def gf2_affine(xs, ys):
    n = 33
    base = [([(x >> i) & 1 for i in range(32)] + [1], y) for x, y in zip(xs, ys)]
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
        if any(mat[i][n] for i in range(r, len(mat))):
            return False
    return True


pairs = [
    ("fid", "K1b"), ("fid", "K1l"), ("K1b", "K2b"), ("K2b", "K3b"),
    ("K1l", "K2l"), ("K2l", "K3l"), ("K1b", "K3b"), ("fid", "K2b"), ("fid", "K3b"),
]
for a, b in pairs:
    xs = [s[a] for s in samples]
    ys = [s[b] for s in samples]
    print(
        f"  {a:5} -> {b:5}: mod2^32-affine="
        f"{('a=%#010x c=%#010x' % solve_lcg(xs, ys)) if solve_lcg(xs, ys) else 'NO':30} "
        f"gf2-affine={'YES' if gf2_affine(xs, ys) else 'NO'}"
    )

print("\n=== E. ratio / product invariants among sig and fid ===")
for a in ("Lb", "Cb", "Eb", "Ll", "Cl", "El"):
    prods = {(s[a] * s["fid"]) % M for s in samples}
    sums = {(s[a] + s["fid"]) % M for s in samples}
    xors = {s[a] ^ s["fid"] for s in samples}
    print(f"  {a}: distinct fid*sig={len(prods)} fid+sig={len(sums)} fid^sig={len(xors)}")

print("\n=== F. per-bit balance (constant bits would reveal construction) ===")
for tgt in ("fid", "Lb", "Cb", "Eb"):
    ones = [sum((s[tgt] >> b) & 1 for s in samples) for b in range(32)]
    const = [b for b in range(32) if ones[b] in (0, len(samples))]
    print(f"  {tgt}: ones-per-bit min={min(ones)} max={max(ones)} of {len(samples)}; "
          f"constant bits={const}")

print("\n=== G. duplicate files / determinism evidence ===")
h = {}
for r in rows:
    d = hashlib.sha256(Path(r["path"]).read_bytes()).hexdigest()[:16]
    h.setdefault(d, []).append(r["path"])
for d, ps in h.items():
    if len(ps) > 1:
        print(f"  identical content {d}: {ps}")
print(f"  distinct file contents: {len(h)} / {len(rows)}")

print("\n=== H. front region: inflatable one, and stale-record check ===")
for r in rows:
    blob = Path(r["path"]).read_bytes()
    first = min(s["offset"] for s in r["streams"]) - 4
    front = blob[8:first]
    try:
        d = zlib.decompress(front, wbits=-15)
        print(f"  {Path(r['path']).name}: front region inflates to {len(d)} bytes; "
              f"head={d[:60]!r}")
    except zlib.error:
        pass
r = rows[0]
blob = Path(r["path"]).read_bytes()
first = min(s["offset"] for s in r["streams"]) - 4
names_accepted = {s["name"] for s in r["streams"]}
cur, stale = 0, []
while True:
    m = blob.find(PREFIX, cur)
    if m < 0 or m >= first:
        break
    cur = m + 1
    nl = struct.unpack_from("<H", blob, m + 22)[0]
    nm = bytes(((v >> 4) | ((v & 0xF) << 4)) for v in blob[m + 26 : m + 26 + nl])
    try:
        s = nm.decode("utf-8")
    except UnicodeDecodeError:
        continue
    crc, cs, us = struct.unpack_from("<III", blob, m + 10)
    stale.append((m, s, crc, cs, us, s in names_accepted))
print(f"  {Path(r['path']).name} front-region pseudo-records: {len(stale)}")
for m, s, crc, cs, us, dup in stale:
    print(f"    at {m}: {s!r} crc={crc:#010x} csize={cs} usize={us} "
          f"also_a_live_stream={dup}")
