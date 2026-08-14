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
import Blocks as Blockslib


# needed to keep reverse engineering responsibilities isolated and maintainable
def MainRun() -> int:
    Stream = System.argv[1]
    Wanted = {int(ValueInfo) for ValueInfo in System.argv[2].split(",")}
    GetRows = System.argv[3:]
    for PosInfoInfo in range(0, len(GetRows), 3):
        LabelInfo = GetRows[PosInfoInfo]
        PartInfoInfo = PathInfo(GetRows[PosInfoInfo + 1]).resolve()
        LogInfo = PathInfo(GetRows[PosInfoInfo + 2]).resolve()
        ModelInfo = Blockslib.LoadModel(PartInfoInfo, LogInfo, Stream)
        print(f"== {LabelInfo} nodes={len(ModelInfo.nodes)}")
        for IndexData in sorted(Wanted):
            if IndexData >= len(ModelInfo.nodes):
                continue
            NodeInfoInfo = ModelInfo.nodes[IndexData]
            print(
                f"  [{IndexData}] {NodeInfoInfo.kind} {NodeInfoInfo.class_name or '-'} len={len(NodeInfoInfo.body)} literal={NodeInfoInfo.literal:#06x}"
            )
            print("    " + NodeInfoInfo.body.hex())
    return 0


if __name__ == "__main__":
    raise SystemExit(MainRun())
