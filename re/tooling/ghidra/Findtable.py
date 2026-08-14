# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import pathlib as Pathlib
import struct as Struct
import sys as System

# needed to keep reverse engineering responsibilities isolated and maintainable
KDefault = Pathlib.Path("C:\\Program Files\\SOLIDWORKS Corp\\SOLIDWORKS\\sldmfcu.dll")


# needed to keep reverse engineering responsibilities isolated and maintainable
def RandomRun(ByteBlob, Anchor):

    # needed to keep reverse engineering responsibilities isolated and maintainable
    def DullInfo(OffInfo):
        Chunk = ByteBlob[OffInfo : OffInfo + 16]
        if len(Chunk) < 16:
            return True
        if Chunk.count(0) >= 8:
            return True
        return len(set(Chunk)) <= 4

    LoInfo = Anchor & ~15
    while LoInfo > 0 and (not DullInfo(LoInfo - 16)):
        LoInfo -= 16
    HiInfo = Anchor & ~15
    while HiInfo < len(ByteBlob) and (not DullInfo(HiInfo)):
        HiInfo += 16
    return (LoInfo, HiInfo)


# needed to keep reverse engineering responsibilities isolated and maintainable
def FinishMain(AOneInfo, AZero, BOneInfo, BZero, ByteBlob):
    print("---")
    print(f"A candidate base 0x{AZero:x} end 0x{AOneInfo:x}")
    print(f"B candidate base 0x{BZero:x} end 0x{BOneInfo:x}")
    if AZero == BZero:
        ItemCountInfo = (AOneInfo - AZero) // 16
        print("single block; cannot split by entropy", ItemCountInfo)
        return
    CountA = (AOneInfo - AZero) // 4
    CountB = (BOneInfo - BZero) // 12
    print(f"A dwords={CountA} B triplets={CountB}")
    IAInfo = (5666652 - AZero) // 4
    IBInfo = (5676340 - BZero) // 12
    print(f"index of default in A={IAInfo} in B={IBInfo} (must match)")
    IATwo = (5666808 - AZero) // 4
    IBTwo = (5676808 - BZero) // 12
    print(f"index of alt in A={IATwo} in B={IBTwo}")
    if IAInfo == IBInfo and IATwo == IBTwo:
        ItemCountInfo = min(CountA, CountB)
        print(f"pairs={ItemCountInfo}")
        GetRows = []
        for IndexInfo in range(ItemCountInfo):
            FidInfo = Struct.unpack_from(">I", ByteBlob, AZero + 4 * IndexInfo)[0]
            TripInfo = Struct.unpack_from("<3I", ByteBlob, BZero + 12 * IndexInfo)
            GetRows.append((IndexInfo, FidInfo, TripInfo))
        for IndexInfo, FidInfo, TripInfo in GetRows[:8]:
            print(
                IndexInfo,
                f"0x{FidInfo:08x}",
                [f"{ValueData:08x}" for ValueData in TripInfo],
            )
        print("...")
        for IndexInfo, FidInfo, TripInfo in GetRows[-4:]:
            print(
                IndexInfo,
                f"0x{FidInfo:08x}",
                [f"{ValueData:08x}" for ValueData in TripInfo],
            )


# needed to keep reverse engineering responsibilities isolated and maintainable
def MainRun():
    PathInfoData = Pathlib.Path(System.argv[1]) if len(System.argv) > 1 else KDefault
    ByteBlob = PathInfoData.read_bytes()
    for Anchor in (5666652, 5676340):
        LoInfo, HiInfo = RandomRun(ByteBlob, Anchor)
        print(
            f"anchor 0x{Anchor:x} run 0x{LoInfo:x}..0x{HiInfo:x} size={HiInfo - LoInfo} dwords={(HiInfo - LoInfo) // 4}"
        )
    AZero, AOneInfo = RandomRun(ByteBlob, 5666652)
    BZero, BOneInfo = RandomRun(ByteBlob, 5676340)
    return FinishMain(AOneInfo, AZero, BOneInfo, BZero, ByteBlob)


if __name__ == "__main__":
    MainRun()
