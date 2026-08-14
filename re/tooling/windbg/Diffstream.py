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
KGrammar = KHereInfo.parent / "harness"
for CandInfo in (KHereInfo, KGrammar):
    if str(CandInfo) not in System.path:
        System.path.insert(0, str(CandInfo))
import Streamlib as Streamlib


# needed to keep reverse engineering responsibilities isolated and maintainable
def MainRun() -> int:
    NameTextInfo = System.argv[3] if len(System.argv) > 3 else Streamlib.KResolved
    LeftInfo = Streamlib.LoadDonor(PathInfo(System.argv[1]).resolve()).streams[
        NameTextInfo
    ]
    Right = Streamlib.LoadDonor(PathInfo(System.argv[2]).resolve()).streams[
        NameTextInfo
    ]
    print(f"left={len(LeftInfo)} right={len(Right)}")
    if len(LeftInfo) != len(Right):
        print("lengths differ; byte comparison covers the common prefix")
    RunsInfo: list[tuple[int, int]] = []
    StartRun = -1
    for Offset in range(min(len(LeftInfo), len(Right))):
        if LeftInfo[Offset] != Right[Offset]:
            if StartRun < 0:
                StartRun = Offset
        elif StartRun >= 0:
            RunsInfo.append((StartRun, Offset))
            StartRun = -1
    if StartRun >= 0:
        RunsInfo.append((StartRun, min(len(LeftInfo), len(Right))))
    print(
        f"differing runs={len(RunsInfo)} differing bytes={sum((SecondValue - FirstValue for FirstValue, SecondValue in RunsInfo))}"
    )
    for Begin, EndIndex in RunsInfo[:40]:
        print(
            f"  [{Begin}, {EndIndex}) left={LeftInfo[Begin:EndIndex].hex(' ')} right={Right[Begin:EndIndex].hex(' ')}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(MainRun())
