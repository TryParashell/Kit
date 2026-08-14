# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations
from pathlib import Path as PathInfo
import json as JsonData
import sys as System

from convert.Security.PathBoundary import ResolveInput

# needed to keep reverse engineering responsibilities isolated and maintainable
KHereInfo = PathInfo(__file__).resolve().parent

# needed to keep reverse engineering responsibilities isolated and maintainable
KGrammar = KHereInfo.parent / "grammar"
for CandInfo in (KHereInfo, KGrammar):
    if str(CandInfo) not in System.path:
        System.path.insert(0, str(CandInfo))
import Carchive as Carchive
import Streamlib as Streamlib


# needed to keep reverse engineering responsibilities isolated and maintainable
def FinishMain(BaseInfo, ByteBlob, Extra, ItemData, Items, MissingInfo) -> None:
    print(f"static-only={MissingInfo} traced-only={Extra}")
    SlotOfClass: dict[int, str] = {}
    CounterInfo = BaseInfo
    for ItemData in Items:
        if ItemData["kind"] == "definition":
            SlotOfClass[CounterInfo] = ItemData["name"]
            CounterInfo += 2
        elif ItemData["kind"] in {"classref", "big"}:
            CounterInfo += 1
    print(f"final counter={CounterInfo} classes in stream={len(SlotOfClass)}")
    Extern = sorted(
        {
            ItemData["index"]
            for ItemData in Items
            if ItemData["kind"] == "classref" and ItemData["index"] < BaseInfo
        }
    )
    Intern = sorted(
        {
            ItemData["index"]
            for ItemData in Items
            if ItemData["kind"] == "classref" and ItemData["index"] >= BaseInfo
        }
    )
    print(f"classref indices below base (external)={Extern}")
    Unresolved = [IndexData for IndexData in Intern if IndexData not in SlotOfClass]
    print(f"classref indices at/above base={len(Intern)} unresolved={Unresolved}")
    ObjExtern = sorted(
        {
            ItemData["index"]
            for ItemData in Items
            if ItemData["kind"] == "objectref" and ItemData["index"] < BaseInfo
        }
    )
    print(f"objectref indices below base={ObjExtern}")
    FindGaps: list[tuple[int, int, int]] = []
    for PosInfoInfo, ItemData in enumerate(Items):
        StartRun = ItemData["offset"] + ItemData["header"]
        EndIndex = (
            Items[PosInfoInfo + 1]["offset"]
            if PosInfoInfo + 1 < len(Items)
            else len(ByteBlob)
        )
        FindGaps.append((ItemData["offset"], StartRun, EndIndex - StartRun))
    ZeroInfo = sum(
        (1 for SpareValue, SpareValue, ByteSize in FindGaps if ByteSize == 0)
    )
    print(f"gaps={len(FindGaps)} zero-length={ZeroInfo} tail={FindGaps[-1]}")
    print()
    print(f"{'off':>6} {'ctr':>5} {'kind':>10} {'tok':>6} {'idx':>5} {'gap':>6} name")
    for ItemData, (SpareValue, SpareValue, ByteSize) in zip(Items, FindGaps):
        LabelInfo = ItemData["name"] or SlotOfClass.get(ItemData["index"], "")
        print(
            f"{ItemData['offset']:>6} {ItemData['counter']:>5} {ItemData['kind']:>10} {ItemData['token']:#06x} {ItemData['index']:>5} {ByteSize:>6} {LabelInfo}"
        )


# needed to keep reverse engineering responsibilities isolated and maintainable
def MainRun() -> None:
    PartInfoInfo = ResolveInput(System.argv[1])
    Report = JsonData.loads(ResolveInput(System.argv[2]).read_text(encoding="utf-8"))
    ByteBlob = Streamlib.LoadDonor(PartInfoInfo).resolved
    Items = Report["items"]
    BaseInfo = Report["base_counter"]
    Static = Carchive.ClassDefns(ByteBlob)
    StaticOffsets = [DefnInfo.tag_offset for DefnInfo in Static]
    TracedDefs = [
        ItemData["offset"] for ItemData in Items if ItemData["kind"] == "definition"
    ]
    print(f"static definitions={len(StaticOffsets)} traced={len(TracedDefs)}")
    print(f"definition offsets identical={StaticOffsets == TracedDefs}")
    MissingInfo = sorted(set(StaticOffsets) - set(TracedDefs))
    Extra = sorted(set(TracedDefs) - set(StaticOffsets))
    return FinishMain(BaseInfo, ByteBlob, Extra, ItemData, Items, MissingInfo)


if __name__ == "__main__":
    MainRun()
