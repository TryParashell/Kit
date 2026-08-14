# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations
import json as JsonData
from pathlib import Path as PathInfo
import struct as Struct
import sys as System

# needed to keep reverse engineering responsibilities isolated and maintainable
KHereInfo = PathInfo(__file__).resolve().parent

# needed to keep reverse engineering responsibilities isolated and maintainable
KScratch = KHereInfo.parents[2] / ".rescratch"

# needed to keep reverse engineering responsibilities isolated and maintainable
KGrammar = KHereInfo.parent / "harness"
for CandInfo in (KHereInfo, KGrammar):
    if str(CandInfo) not in System.path:
        System.path.insert(0, str(CandInfo))
import Streamlib as Streamlib

# needed to keep reverse engineering responsibilities isolated and maintainable
KOutInfo = KScratch / "trace" / "out"

# needed to keep reverse engineering responsibilities isolated and maintainable
KFormulas = {
    "n": lambda ItemCountInfo: ItemCountInfo,
    "2n": lambda ItemCountInfo: 2 * ItemCountInfo,
    "24+2n": lambda ItemCountInfo: 24 + 2 * ItemCountInfo,
    "25+2n": lambda ItemCountInfo: 25 + 2 * ItemCountInfo,
    "18+2n": lambda ItemCountInfo: 18 + 2 * ItemCountInfo,
    "n-1": lambda ItemCountInfo: ItemCountInfo - 1,
    "n+1": lambda ItemCountInfo: ItemCountInfo + 1,
    "2n-1": lambda ItemCountInfo: 2 * ItemCountInfo - 1,
    "2n+1": lambda ItemCountInfo: 2 * ItemCountInfo + 1,
    "2n+2": lambda ItemCountInfo: 2 * ItemCountInfo + 2,
    "3n": lambda ItemCountInfo: 3 * ItemCountInfo,
    "4n": lambda ItemCountInfo: 4 * ItemCountInfo,
    "19+2n": lambda ItemCountInfo: 19 + 2 * ItemCountInfo,
    "23+2n": lambda ItemCountInfo: 23 + 2 * ItemCountInfo,
    "26+2n": lambda ItemCountInfo: 26 + 2 * ItemCountInfo,
    "40+2n": lambda ItemCountInfo: 40 + 2 * ItemCountInfo,
}


# needed to keep reverse engineering responsibilities isolated and maintainable
def Matches(ByteBlob: bytes, ValueInfo: int) -> set[tuple[int, int]]:
    Found: set[tuple[int, int]] = set()
    Limit = len(ByteBlob)
    for Offset in range(Limit - 1):
        if Struct.unpack_from("<H", ByteBlob, Offset)[0] == ValueInfo:
            Found.add((Offset, 2))
        if (
            Offset + 4 <= Limit
            and Struct.unpack_from("<I", ByteBlob, Offset)[0] == ValueInfo
        ):
            Found.add((Offset, 4))
    return Found


# needed to keep reverse engineering responsibilities isolated and maintainable
def FinishMain(Formula, RuleInfo) -> int:
    Parts = [PathInfo(ItemData).resolve() for ItemData in System.argv[2:]]
    if len(Parts) < 2:
        raise SystemExit("usage: Fieldscan.py <formula> <part> <part> [...]")
    PerStream: dict[str, list[set[tuple[int, int]]]] = {}
    Counts: list[int] = []
    for PartInfoInfo in Parts:
        DonorInfo = Streamlib.LoadDonor(PartInfoInfo)
        FeatInfoInfo = len(Streamlib.CompFeatEntries(DonorInfo.resolved)) // 2
        Counts.append(FeatInfoInfo)
        ValueInfo = RuleInfo(FeatInfoInfo)
        for NameTextInfo, PayloadInfo in DonorInfo.streams.items():
            PerStream.setdefault(NameTextInfo, []).append(
                Matches(PayloadInfo, ValueInfo)
            )
    Distinct = sorted(set(Counts))
    print(f"parts={len(Parts)} feature counts observed={Distinct} formula={Formula}")
    if len(Distinct) < 2:
        raise SystemExit("the part set must contain at least two feature counts")
    Report: dict[str, list[list[int]]] = {}
    for NameTextInfo in sorted(PerStream):
        SetsInfo = PerStream[NameTextInfo]
        if len(SetsInfo) != len(Parts):
            continue
        Shared = set.intersection(*SetsInfo)
        if not Shared:
            continue
        Report[NameTextInfo] = sorted([list(ItemData) for ItemData in Shared])
        print(f"{NameTextInfo}: {sorted(Shared)}")
    KOutInfo.mkdir(parents=True, exist_ok=True)
    (KOutInfo / f"fieldscan_{Formula}.json").write_text(
        JsonData.dumps(
            {
                "formula": Formula,
                "parts": [str(PartInfoInfo) for PartInfoInfo in Parts],
                "feature_counts": Counts,
                "shared": Report,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return 0


# needed to keep reverse engineering responsibilities isolated and maintainable
def MainRun() -> int:
    Formula = System.argv[1]
    if Formula not in KFormulas:
        raise SystemExit(f"formula must be one of {sorted(KFormulas)}")
    RuleInfo = KFormulas[Formula]
    return FinishMain(Formula, RuleInfo)


if __name__ == "__main__":
    raise SystemExit(MainRun())
