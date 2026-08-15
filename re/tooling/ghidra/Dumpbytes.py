# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import sys as System

from convert.Security.PathBoundary import ResolveInput


# needed to keep reverse engineering responsibilities isolated and maintainable
def MainRun():
    PathInfoData = ResolveInput(System.argv[1])
    StartRun = int(System.argv[2], 0)
    Length = int(System.argv[3], 0)
    ByteBlob = PathInfoData.read_bytes()
    LoInfo = max(0, StartRun)
    HiInfo = min(len(ByteBlob), StartRun + Length)
    for OffInfo in range(LoInfo, HiInfo, 16):
        Chunk = ByteBlob[OffInfo : OffInfo + 16]
        Hexpart = " ".join((f"{SecondValue:02x}" for SecondValue in Chunk))
        TextValueData = "".join(
            (
                chr(SecondValue) if 32 <= SecondValue < 127 else "."
                for SecondValue in Chunk
            )
        )
        print(f"{OffInfo:08x}  {Hexpart:<47s}  {TextValueData}")


if __name__ == "__main__":
    MainRun()
