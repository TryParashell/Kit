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
import Model as Modellib
import Segment as Segmentlib
import Streamlib as Streamlib
from convert.adapters.solidworks import resolved as Resolvedlib


# needed to keep reverse engineering responsibilities isolated and maintainable
def Anchors(ByteBlob: bytes) -> dict[int, str]:
    Marks: dict[int, str] = {}
    for NodeInfoInfo in Resolvedlib.tree_nodes(ByteBlob):
        Marks[NodeInfoInfo.text_end] = (
            f"tree:{NodeInfoInfo.name}:flags@{NodeInfoInfo.text_end + 4}"
        )
    for IndexData, Layout in enumerate(Resolvedlib.locate_features(ByteBlob)):
        Marks[Layout.depth_offset] = f"depth[{IndexData}]"
    for IndexData, Entry in enumerate(Streamlib.CompFeatEntries(ByteBlob)):
        Marks[Entry[0]] = f"comp_entry[{IndexData}] id={Entry[2]}"
    return Marks


# needed to keep reverse engineering responsibilities isolated and maintainable
def MainRun() -> int:
    PartInfoInfo = PathInfo(System.argv[1]).resolve()
    LogInfo = PathInfo(System.argv[2]).resolve()
    LowValue = int(System.argv[3]) if len(System.argv) > 3 else 0
    HighValue = int(System.argv[4]) if len(System.argv) > 4 else 0
    ByteBlob, ModelInfo, SegmentsInfo = Modellib.LoadData(PartInfoInfo, LogInfo)
    Offsets = Modellib.NodeOffsets(ModelInfo)
    Marks = Anchors(ByteBlob)
    StopInfo = HighValue if HighValue else len(SegmentsInfo)
    print(
        f"{PartInfoInfo.name} stream={len(ByteBlob)} nodes={len(SegmentsInfo)} base={ModelInfo.base}"
    )
    print(
        f"{'node':>5} {'offset':>7} {'len':>5} {'tag':>6} {'kind':>10} {'map':>5} {'d':>2} {'parent':>6} class"
    )
    for PosInfoInfo in range(LowValue, StopInfo):
        ItemData = SegmentsInfo[PosInfoInfo]
        NoteInfo = ""
        for Offset, LabelInfo in Marks.items():
            if ItemData.offset <= Offset < ItemData.end:
                NoteInfo += f"  <{LabelInfo}>"
        print(
            f"{PosInfoInfo:>5} {ItemData.offset:>7} {ItemData.length:>5} {ItemData.tag:>6x} {ItemData.kind:>10} {ItemData.map_index:>5} {ItemData.depth:>2} {ItemData.parent:>6} {ItemData.class_name}{NoteInfo}"
        )
    SpareValue = Offsets
    return 0


if __name__ == "__main__":
    raise SystemExit(MainRun())
