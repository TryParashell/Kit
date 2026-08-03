from __future__ import annotations

import json
import struct
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
rows = json.loads((HERE / "scan.json").read_text(encoding="utf-8"))
PREFIX = bytes.fromhex("140006000800")


def dump(b: bytes, base: int = 0) -> None:
    for i in range(0, len(b), 16):
        chunk = b[i : i + 16]
        txt = "".join(chr(c) if 32 <= c < 127 else "." for c in chunk)
        print(f"    {base+i:06x}  {chunk.hex(' '):<47}  {txt}")


def swap(data: bytes) -> bytes:
    return bytes(((v >> 4) | ((v & 0x0F) << 4)) for v in data)


for r in rows[:3]:
    p = Path(r["path"])
    blob = p.read_bytes()
    first = min(s["offset"] for s in r["streams"]) - 4
    print(f"\n### {p.name}  file_id={r['file_id']:#010x} local_sig={r['local_sigs'][0]} "
          f"first_local_record_sig_at={first}")
    dump(blob[: min(first + 16, 560)], 0)
    print("    -- all PREFIX occurrences before the first accepted record --")
    cur = 0
    while True:
        m = blob.find(PREFIX, cur)
        if m < 0 or m >= first:
            break
        cur = m + 1
        sig = blob[m - 4 : m].hex()
        tid, crc, csz, usz, nl, z = struct.unpack_from("<IIIIHH", blob, m + 6)
        nm = blob[m + 22 : m + 22 + nl]
        try:
            nmtxt = swap(nm).decode("utf-8", "replace")
        except Exception:
            nmtxt = "?"
        print(
            f"      at {m}: sig={sig} type_id={tid:#010x} crc={crc:#010x} "
            f"csz={csz} usz={usz} namelen={nl} pad={z} name={nmtxt!r}"
        )
        if 0 < csz < len(blob):
            seg = blob[m + 22 + nl : m + 22 + nl + csz]
            try:
                d = zlib.decompress(seg, wbits=-15)
                print(f"        inflates to {len(d)} bytes (usz says {usz}) "
                      f"crc_ok={zlib.crc32(d) & 0xFFFFFFFF == crc}")
            except zlib.error as exc:
                print(f"        inflate failed: {exc}")
