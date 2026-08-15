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
from convert.Security.PathBoundary import ResolveInput


# needed to keep reverse engineering responsibilities isolated and maintainable
def MainRun() -> int:
    Parts = [ResolveInput(ItemData) for ItemData in System.argv[1:]]
    if not Parts:
        raise SystemExit("usage: Streamgrowth.py <part> <part> [...]")
    Table: dict[str, list[int]] = {}
    for PartInfoInfo in Parts:
        DonorInfo = Streamlib.LoadDonor(PartInfoInfo)
        for NameTextInfo, PayloadInfo in DonorInfo.streams.items():
            Table.setdefault(NameTextInfo, []).append(len(PayloadInfo))
    WidthInfo = max((len(NameTextInfo) for NameTextInfo in Table))
    print(
        "stream sizes across "
        + ", ".join((PartInfoInfo.stem for PartInfoInfo in Parts))
    )
    for NameTextInfo in sorted(Table):
        Sizes = Table[NameTextInfo]
        if len(Sizes) != len(Parts):
            print(f"{NameTextInfo:<{WidthInfo}}  {Sizes} (missing from some parts)")
            continue
        Trend = "grows" if Sizes == sorted(Sizes) and Sizes[0] != Sizes[-1] else "flat"
        print(f"{NameTextInfo:<{WidthInfo}}  {Sizes} {Trend}")
    return 0


if __name__ == "__main__":
    raise SystemExit(MainRun())
