import pathlib
import struct
import sys

DEFAULT = pathlib.Path(r"C:\Program Files\SOLIDWORKS Corp\SOLIDWORKS\sldmfcu.dll")


def random_run(blob, anchor):
    def dull(off):
        chunk = blob[off : off + 16]
        if len(chunk) < 16:
            return True
        if chunk.count(0) >= 8:
            return True
        return len(set(chunk)) <= 4

    lo = anchor & ~0xF
    while lo > 0 and not dull(lo - 16):
        lo -= 16
    hi = anchor & ~0xF
    while hi < len(blob) and not dull(hi):
        hi += 16
    return lo, hi


def main():
    path = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT
    blob = path.read_bytes()
    for anchor in (0x56775C, 0x569D34):
        lo, hi = random_run(blob, anchor)
        print(
            f"anchor 0x{anchor:x} run 0x{lo:x}..0x{hi:x} size={hi - lo} dwords={(hi - lo) // 4}"
        )
    a0, a1 = random_run(blob, 0x56775C)
    b0, b1 = random_run(blob, 0x569D34)
    print("---")
    print(f"A candidate base 0x{a0:x} end 0x{a1:x}")
    print(f"B candidate base 0x{b0:x} end 0x{b1:x}")
    if a0 == b0:
        n = (a1 - a0) // 16
        print("single block; cannot split by entropy", n)
        return
    countA = (a1 - a0) // 4
    countB = (b1 - b0) // 12
    print(f"A dwords={countA} B triplets={countB}")
    iA = (0x56775C - a0) // 4
    iB = (0x569D34 - b0) // 12
    print(f"index of default in A={iA} in B={iB} (must match)")
    iA2 = (0x5677F8 - a0) // 4
    iB2 = (0x569F08 - b0) // 12
    print(f"index of alt in A={iA2} in B={iB2}")
    if iA == iB and iA2 == iB2:
        n = min(countA, countB)
        print(f"pairs={n}")
        rows = []
        for i in range(n):
            fid = struct.unpack_from(">I", blob, a0 + 4 * i)[0]
            trip = struct.unpack_from("<3I", blob, b0 + 12 * i)
            rows.append((i, fid, trip))
        for i, fid, trip in rows[:8]:
            print(i, f"0x{fid:08x}", [f"{v:08x}" for v in trip])
        print("...")
        for i, fid, trip in rows[-4:]:
            print(i, f"0x{fid:08x}", [f"{v:08x}" for v in trip])


if __name__ == "__main__":
    main()
