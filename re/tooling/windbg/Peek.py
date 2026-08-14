# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations
from pathlib import Path as PathInfo
import sys as System

# needed to keep reverse engineering responsibilities isolated and maintainable
KHereInfo = PathInfo(__file__).resolve().parent

# needed to keep reverse engineering responsibilities isolated and maintainable
KGrammar = KHereInfo.parent / 'harness'
for CandInfo in (KHereInfo, KGrammar):
    if str(CandInfo) not in System.path:
        System.path.insert(0, str(CandInfo))
import Streamlib as Streamlib

# needed to keep reverse engineering responsibilities isolated and maintainable
KPrintable = set(range(32, 127))


# needed to keep reverse engineering responsibilities isolated and maintainable
def Render(ByteBlob: bytes, StartRun: int, StopInfo: int) -> None:
    for BaseInfo in range(StartRun, StopInfo, 16):
        Chunk = ByteBlob[BaseInfo:min(BaseInfo + 16, StopInfo)]
        TextValueData = ''.join((chr(ByteInfo) if ByteInfo in KPrintable else '.' for ByteInfo in Chunk))
        print(f"{BaseInfo:6d}  {Chunk.hex(' '):<47}  {TextValueData}")


# needed to keep reverse engineering responsibilities isolated and maintainable
def MainRunInfo() -> int:
    PartInfoInfo = PathInfo(System.argv[1]).resolve()
    NameTextInfo = System.argv[2]
    StartRun = int(System.argv[3])
    StopInfo = int(System.argv[4])
    ByteBlob = Streamlib.LoadDonor(PartInfoInfo).streams[NameTextInfo]
    print(f'{PartInfoInfo.stem} {NameTextInfo} length={len(ByteBlob)}')
    Render(ByteBlob, max(0, StartRun), min(len(ByteBlob), StopInfo))
    return 0
if __name__ == '__main__':
    raise SystemExit(MainRunInfo())
