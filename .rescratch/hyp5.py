from __future__ import annotations

import json
import struct
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
rows = json.loads((HERE / "scan.json").read_text(encoding="utf-8"))
AO = 8

print("=== trailing bytes after the end-of-directory record ===")
tails = Counter()
for r in rows:
    n = Path(r["path"]).stat().st_size
    tails[n - (r["end_offset"] + 22)] += 1
print(f"  len(file) - (eocd_offset + 22): {dict(tails)}")
r0 = rows[0]
blob0 = Path(r0["path"]).read_bytes()
print(f"  {Path(r0['path']).name} last 48 bytes: {blob0[-48:].hex(' ')}")
print(f"  eocd at {r0['end_offset']}, file size {len(blob0)}")
print(f"  bytes from eocd: {blob0[r0['end_offset']:].hex(' ')}")

print("\n=== central directory walk, first file, first 4 entries ===")
dn, dd, de, te, dsize, doff, clen = r0["end_fields"]
cur = AO + doff
print(f"  eocd fields disk={dn} dd={dd} de={de} te={te} dsize={dsize} doff={doff} clen={clen}")
print(f"  central dir starts at file offset {cur}")
live = sorted(r0["streams"], key=lambda s: s["offset"])
for i in range(min(4, te)):
    sig = blob0[cur : cur + 4].hex()
    vmb, vn, fl, me = struct.unpack_from("<HHHH", blob0, cur + 4)
    crc, cs, us = struct.unpack_from("<III", blob0, cur + 16)
    nl, el, cl2, ds, ia = struct.unpack_from("<HHHHH", blob0, cur + 28)
    ea, lo = struct.unpack_from("<II", blob0, cur + 38)
    nm = bytes(((v >> 4) | ((v & 0xF) << 4)) for v in blob0[cur + 46 : cur + 46 + nl])
    print(
        f"    [{i}] sig={sig} vmb={vmb} vneed={vn} flags={fl:#06x} method={me} "
        f"crc={crc:#010x} cs={cs} us={us} nl={nl} el={el} cl={cl2} disk={ds} "
        f"iattr={ia:#06x} eattr={ea:#010x} local_off={lo}"
    )
    print(f"        name={nm.decode('utf-8', 'replace')!r}  "
          f"points to file offset {AO + lo}, sig there={blob0[AO+lo:AO+lo+4].hex()}")
    cur += 46 + nl + el + cl2
print(f"  cursor after {min(4, te)} entries: {cur}")

print("\n=== full verification across all files ===")
allok = 0
probs = Counter()
for r in rows:
    blob = Path(r["path"]).read_bytes()
    dn, dd, de, te, dsize, doff, clen = r["end_fields"]
    cur = AO + doff
    sigset = set()
    offs = []
    ok = True
    for _ in range(te):
        sigset.add(blob[cur : cur + 4])
        nl, el, cl2 = struct.unpack_from("<HHH", blob, cur + 28)
        lo = struct.unpack_from("<I", blob, cur + 42)[0]
        offs.append(lo)
        cur += 46 + nl + el + cl2
    if cur != r["end_offset"]:
        probs["central_walk_does_not_end_at_eocd"] += 1
        ok = False
    if len(sigset) != 1:
        probs["central_sig_not_unique"] += 1
        ok = False
    want = sorted(s["offset"] - 4 - AO for s in r["streams"])
    if sorted(offs) != want:
        probs["local_offsets_mismatch"] += 1
        ok = False
    for lo in offs:
        if blob[AO + lo + 4 : AO + lo + 10] != bytes.fromhex("140006000800"):
            probs["local_offset_not_on_record"] += 1
            ok = False
            break
    if ok:
        allok += 1
print(f"  fully ZIP-navigable files: {allok}/{len(rows)}")
print(f"  problems: {dict(probs)}")

print("\n=== live vs front-region descriptor comparison (example.SLDPRT) ===")
for s in live:
    if s["name"] in {
        "Contents/Config-0-Partition",
        "swXmlContents/Features",
        "PreviewPNG",
        "Contents/Config-0-ResolvedFeatures",
    }:
        print(f"  live {s['name']:38} csize={s['csize']:6} usize={s['usize']:6}")
