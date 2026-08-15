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
KSwInfo = Pathlib.Path("C:\\Program Files\\SOLIDWORKS Corp\\SOLIDWORKS")

# needed to keep reverse engineering responsibilities isolated and maintainable
KValues = [
    ("file_id_default", 3966641030),
    ("file_id_alt", 1901848975),
    ("local_1", 1691877445),
    ("central_1", 2920107766),
    ("end_1", 1422792602),
    ("local_2", 2710608671),
    ("central_2", 2776012559),
    ("end_2", 2046838560),
]


# needed to keep reverse engineering responsibilities isolated and maintainable
def Needles():
    OutputDataInfo = []
    for NameTextInfo, ValueInfo in KValues:
        OutputDataInfo.append((NameTextInfo + "_le", Struct.pack("<I", ValueInfo)))
        OutputDataInfo.append((NameTextInfo + "_be", Struct.pack(">I", ValueInfo)))
    return OutputDataInfo


# needed to keep reverse engineering responsibilities isolated and maintainable
def MainRun():
    Roots = [KSwInfo]
    if len(System.argv) > 1:
        Roots = [Pathlib.Path(FirstValue) for FirstValue in System.argv[1:]]
    PatsInfo = Needles()
    for RootPath in Roots:
        Files = sorted(RootPath.rglob("*.dll")) + sorted(RootPath.rglob("*.exe"))
        for PathInfoData in Files:
            try:
                ByteBlob = PathInfoData.read_bytes()
            except OSError:
                continue
            HitsInfo = []
            for NameTextInfo, PatInfo in PatsInfo:
                StartRun = 0
                while True:
                    IdxInfo = ByteBlob.find(PatInfo, StartRun)
                    if IdxInfo < 0:
                        break
                    HitsInfo.append((NameTextInfo, IdxInfo))
                    StartRun = IdxInfo + 1
                    if len(HitsInfo) > 40:
                        break
            if HitsInfo:
                print(PathInfoData.name, len(ByteBlob))
                for NameTextInfo, IdxInfo in HitsInfo[:40]:
                    print(f"   {NameTextInfo} @ 0x{IdxInfo:x}")


if __name__ == "__main__":
    MainRun()
