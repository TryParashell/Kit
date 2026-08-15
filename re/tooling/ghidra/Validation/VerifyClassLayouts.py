# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations
import argparse as Argparse
import collections as Collects
import json as JsonData
import pathlib as Pathlib
import re as Regex
import sys as System
from typing import Dict as DictInfo, List as ListInfo, Optional, Tuple

from convert.Security.PathBoundary import (
    ResolveFolder,
    ResolveInput,
    ResolveOutput,
    ResolveWithin,
    UnsafePath,
)

# needed to keep reverse engineering responsibilities isolated and maintainable
KHereInfo = Pathlib.Path(__file__).resolve().parent

# repository root resolution accounts for the semantic validation subfolder
KRootInfo = KHereInfo.parents[3]

# generation tools provide the trace solver used for fallback layouts
KGeneration = KHereInfo.parent / "Generation"
System.path.insert(0, str(KRootInfo / "src"))
System.path.insert(0, str(KGeneration))
from convert.adapters.solidworks.container.Container import SldprtArchive
from SolveRuns import LoadTraces, Solver


# needed to keep reverse engineering responsibilities isolated and maintainable
def GetLegacyAttr(SelfRef, NameText):
    AliasName = SelfRef.KAliasNames.get(NameText)
    if AliasName is None:
        raise AttributeError(NameText)
    return getattr(SelfRef, AliasName)


# needed to keep reverse engineering responsibilities isolated and maintainable
def SetLegacyMut(SelfRef, NameText, ValueData):
    TargetName = SelfRef.KAliasNames.get(NameText, NameText)
    object.__setattr__(SelfRef, TargetName, ValueData)


# needed to keep reverse engineering responsibilities isolated and maintainable
KStream = "Contents/Config-0-ResolvedFeatures"

# needed to keep reverse engineering responsibilities isolated and maintainable
KNoBodyKinds = ("null", "objectref")

# needed to keep reverse engineering responsibilities isolated and maintainable
KBackref = Regex.compile("backref->(\\d+)$")


# needed to keep reverse engineering responsibilities isolated and maintainable
def PartPath(DocInfo: dict) -> Pathlib.Path:
    PartInfoInfo = Pathlib.Path(DocInfo["part"])
    try:
        return ResolveInput(PartInfoInfo)
    except (FileNotFoundError, UnsafePath):
        pass
    for BaseInfo in (
        KRootInfo / ".rescratch/corpus/parts",
        KRootInfo / ".rescratch/corpus2",
        KRootInfo / ".rescratch/trace/parts",
        KRootInfo / "examples",
        KRootInfo / ".rescratch",
    ):
        if not BaseInfo.is_dir():
            continue
        for HitPath in BaseInfo.rglob("*"):
            if HitPath.name == PartInfoInfo.name and HitPath.is_file():
                return ResolveWithin(HitPath, BaseInfo, True)
    raise SystemExit("cannot locate part " + str(PartInfoInfo))


# needed to keep reverse engineering responsibilities isolated and maintainable
def ClassOf(SegmentsInfo: ListInfo[dict], IndexData: int) -> str:
    NameTextInfo = SegmentsInfo[IndexData]["class_name"]
    Match = KBackref.match(NameTextInfo)
    if Match:
        return SegmentsInfo[int(Match.group(1))]["class_name"]
    return NameTextInfo


# needed to keep reverse engineering responsibilities isolated and maintainable
def FallbackRuns(Traces: ListInfo[dict]) -> DictInfo[str, DictInfo[str, int]]:
    SolverInfo = Solver(Traces)
    SolverInfo.Solve()
    Table: DictInfo[str, DictInfo[str, int]] = Collects.defaultdict(dict)
    for KeyName, ValueInfo in SolverInfo.RunsInfo.items():
        NameTextInfo, SlotIndex = KeyName.rsplit("@", 1)
        Table[NameTextInfo][SlotIndex] = ValueInfo
    return Table


# needed to keep reverse engineering responsibilities isolated and maintainable
def StringLength(ByteBlob: bytes, AtInfo: int) -> Optional[int]:
    if ByteBlob[AtInfo : AtInfo + 3] != b"\xff\xfe\xff":
        return None
    Marker = ByteBlob[AtInfo + 3]
    if Marker == 255:
        Units = int.from_bytes(ByteBlob[AtInfo + 4 : AtInfo + 6], "little")
        return 6 + 2 * Units
    return 4 + 2 * Marker


# needed to keep reverse engineering responsibilities isolated and maintainable
def FinishLength(ByteBlob, Entries, StartRun) -> Tuple[Optional[int], str]:
    if not Entries:
        return (None, "undeclared")
    Total = 0
    for Entry in Entries:
        RuleInfo = Entry["rule"]
        if RuleInfo == "opaque":
            return (None, "opaque")
        Total += Entry.get("at", 0)
        Cursor = StartRun + Total
        if RuleInfo == "string":
            ByteSize = StringLength(ByteBlob, Cursor)
            if ByteSize is None:
                return (None, "string marker absent at %d" % Cursor)
            Total += ByteSize
        elif RuleInfo == "count":
            WidthInfo = Entry["count_width"]
            CountInfo = int.from_bytes(ByteBlob[Cursor : Cursor + WidthInfo], "little")
            Total += WidthInfo + Entry["stride"] * CountInfo
        elif RuleInfo == "conditional":
            WidthInfo = Entry["predicate_width"]
            Offset = Cursor + Entry.get("predicate_at", 0)
            ValueInfo = int.from_bytes(ByteBlob[Offset : Offset + WidthInfo], "little")
            Total += WidthInfo
            if ValueInfo in Entry["values"]:
                Total += Entry["width"]
        else:
            return (None, "unknown rule " + RuleInfo)
        Total += Entry.get("tail", 0)
    return (Total, "rule")


# needed to keep reverse engineering responsibilities isolated and maintainable
def RunLength(
    Layout: dict, KeyName: str, ByteBlob: bytes, StartRun: int
) -> Tuple[Optional[int], str]:
    Constant = Layout.get("runs", {}).get(KeyName)
    if Constant is not None:
        return (Constant, "constant")
    Entries = [
        ErrorInfo
        for ErrorInfo in Layout.get("variable_runs", [])
        if ErrorInfo["slot"] == KeyName
    ]
    return FinishLength(ByteBlob, Entries, StartRun)


# layout lookup isolates declared and inferred class run policies
class WalkerLookup:
    __slots__ = ()

    # needed to keep reverse engineering responsibilities isolated and maintainable
    def LayoutFor(SelfRef, IndexData: int) -> Optional[dict]:
        NameTextInfo = ClassOf(SelfRef.SegmentsInfo, IndexData)
        if NameTextInfo in SelfRef.Declared:
            return SelfRef.Declared[NameTextInfo]
        RunsInfo = SelfRef.Fallback.get(NameTextInfo)
        if RunsInfo is None:
            return None
        return {"runs": RunsInfo, "variable_runs": [], "child_slots": None}


# body memoization isolates recursion control from layout arithmetic
class WalkerBody:
    __slots__ = ()

    # needed to keep reverse engineering responsibilities isolated and maintainable
    def BodyEnd(SelfRef, IndexData: int) -> Optional[int]:
        if IndexData in SelfRef.MemoInfo:
            return SelfRef.MemoInfo[IndexData]
        if IndexData in SelfRef.Active:
            return None
        SegInfo = SelfRef.SegmentsInfo[IndexData]
        if SegInfo["kind"] in KNoBodyKinds:
            SelfRef.MemoInfo[IndexData] = SegInfo["offset"] + SegInfo["header"]
            return SelfRef.MemoInfo[IndexData]
        SelfRef.Active.add(IndexData)
        Result = SelfRef.Compute(IndexData)
        SelfRef.Active.discard(IndexData)
        SelfRef.MemoInfo[IndexData] = Result
        return Result


# body computation tiles child bodies and recovered interstitial runs
class WalkerCompute:
    __slots__ = ()

    # needed to keep reverse engineering responsibilities isolated and maintainable
    def Compute(SelfRef, IndexData: int) -> Optional[int]:
        SegInfo = SelfRef.SegmentsInfo[IndexData]
        HeadInfo = SegInfo["offset"] + SegInfo["header"]
        Layout = SelfRef.LayoutFor(IndexData)
        if Layout is None:
            return None
        Slots = Layout.get("child_slots")
        KidsInfo = SelfRef.KidsInfo[IndexData]
        if Slots == [] or not KidsInfo:
            ByteSize, SpareValue = RunLength(Layout, "leaf", SelfRef.ByteBlob, HeadInfo)
            return None if ByteSize is None else HeadInfo + ByteSize
        Cursor = HeadInfo
        ByteSize, SpareValue = RunLength(Layout, "lead", SelfRef.ByteBlob, Cursor)
        if ByteSize is None:
            return None
        Cursor += ByteSize
        for SlotIndex, KidInfo in enumerate(KidsInfo):
            EndIndex = SelfRef.BodyEnd(KidInfo)
            if EndIndex is None:
                return None
            Cursor = EndIndex
            ByteSize, SpareValue = RunLength(
                Layout, str(SlotIndex), SelfRef.ByteBlob, Cursor
            )
            if ByteSize is None:
                return None
            Cursor += ByteSize
        return Cursor


# child offset prediction isolates recovered run checks from object traversal
class WalkerChildren:
    __slots__ = ()

    # needed to keep reverse engineering responsibilities isolated and maintainable
    def ChildOffsets(SelfRef, IndexData: int) -> ListInfo[Tuple[int, int, int]]:
        SegInfo = SelfRef.SegmentsInfo[IndexData]
        HeadInfo = SegInfo["offset"] + SegInfo["header"]
        Layout = SelfRef.LayoutFor(IndexData)
        OutputDataInfo: ListInfo[Tuple[int, int, int]] = []
        if Layout is None or Layout.get("child_slots") == []:
            return OutputDataInfo
        KidsInfo = SelfRef.KidsInfo[IndexData]
        if not KidsInfo:
            return OutputDataInfo
        ByteSize, SpareValue = RunLength(Layout, "lead", SelfRef.ByteBlob, HeadInfo)
        if ByteSize is not None:
            OutputDataInfo.append(
                (-1, HeadInfo + ByteSize, SelfRef.SegmentsInfo[KidsInfo[0]]["offset"])
            )
        for SlotIndex, KidInfo in enumerate(KidsInfo):
            EndIndex = SelfRef.BodyEnd(KidInfo)
            if EndIndex is None:
                continue
            ByteSize, SpareValue = RunLength(
                Layout, str(SlotIndex), SelfRef.ByteBlob, EndIndex
            )
            if ByteSize is None:
                continue
            if SlotIndex + 1 < len(KidsInfo):
                OutputDataInfo.append(
                    (
                        SlotIndex,
                        EndIndex + ByteSize,
                        SelfRef.SegmentsInfo[KidsInfo[SlotIndex + 1]]["offset"],
                    )
                )
            elif SegInfo["depth"] == 0:
                OutputDataInfo.append(
                    (SlotIndex, EndIndex + ByteSize, SegInfo["scope_end"])
                )
        return OutputDataInfo


# span bounds isolate observed containment limits from computed body lengths
class WalkerBounds:
    __slots__ = ()

    # needed to keep reverse engineering responsibilities isolated and maintainable
    def Bound(SelfRef, IndexData: int) -> int:
        SegInfo = SelfRef.SegmentsInfo[IndexData]
        HeadInfo = SegInfo["offset"] + SegInfo["header"]
        Layout = SelfRef.LayoutFor(IndexData)
        KidsInfo = SelfRef.KidsInfo[IndexData]
        LeafInfo = Layout is not None and Layout.get("child_slots") == []
        StartRun = HeadInfo
        if KidsInfo and (not LeafInfo):
            StartRun = max(HeadInfo, SelfRef.SegmentsInfo[KidsInfo[-1]]["scope_end"])
        Limit = SegInfo["scope_end"]
        for Other in SelfRef.Order:
            Offset = SelfRef.SegmentsInfo[Other]["offset"]
            if Offset >= StartRun:
                Limit = min(Limit, Offset)
                break
        return Limit - HeadInfo


# the public walker composes focused traversal policies around shared trace indexes
class Walker(WalkerLookup, WalkerBody, WalkerCompute, WalkerChildren, WalkerBounds):

    # needed to keep reverse engineering responsibilities isolated and maintainable
    def __init__(
        SelfRef,
        SegmentsInfo: ListInfo[dict],
        ByteBlob: bytes,
        Declared: DictInfo[str, dict],
        Fallback: DictInfo[str, DictInfo[str, int]],
    ) -> None:
        SelfRef.SegmentsInfo = SegmentsInfo
        SelfRef.ByteBlob = ByteBlob
        SelfRef.Declared = Declared
        SelfRef.Fallback = Fallback
        SelfRef.KidsInfo: DictInfo[int, ListInfo[int]] = Collects.defaultdict(list)
        for IndexData, SegInfo in enumerate(SegmentsInfo):
            if SegInfo["parent"] >= 0:
                SelfRef.KidsInfo[SegInfo["parent"]].append(IndexData)

        # needed to keep reverse engineering responsibilities isolated and maintainable
        SelfRef.Order = sorted(
            range(len(SegmentsInfo)),
            key=lambda IndexInfo: (SegmentsInfo[IndexInfo]["offset"], IndexInfo),
        )
        SelfRef.NextOffset: DictInfo[int, Optional[int]] = {}
        for PosInfoInfo, IndexData in enumerate(SelfRef.Order):
            HeadInfo = (
                SegmentsInfo[IndexData]["offset"] + SegmentsInfo[IndexData]["header"]
            )
            Found = None
            for Other in SelfRef.Order[PosInfoInfo + 1 :]:
                if SegmentsInfo[Other]["offset"] >= HeadInfo:
                    Found = SegmentsInfo[Other]["offset"]
                    break
            SelfRef.NextOffset[IndexData] = Found
        SelfRef.MemoInfo: DictInfo[int, Optional[int]] = {}
        SelfRef.Active: set = set()

    KAliasNames = {
        "segments": "SegmentsInfo",
        "data": "ByteBlob",
        "declared": "Declared",
        "fallback": "Fallback",
        "kids": "KidsInfo",
        "order": "Order",
        "next_offset": "NextOffset",
        "memo": "MemoInfo",
        "active": "Active",
        "layout_for": "LayoutFor",
        "body_end": "BodyEnd",
        "compute": "Compute",
        "predicted_child_offsets": "ChildOffsets",
        "bound": "Bound",
    }


# needed to keep reverse engineering responsibilities isolated and maintainable
Walker.__getattr__ = GetLegacyAttr

# needed to keep reverse engineering responsibilities isolated and maintainable
Walker.__setattr__ = SetLegacyMut


# report construction keeps every class counter initialized through one stable schema
def BuildReport(Declared: DictInfo[str, dict]) -> DictInfo[str, dict]:
    return {
        NameTextInfo: {
            "confidence": SpecInfo.get("confidence", "not found"),
            "instances": 0,
            "computed": 0,
            "exact_span": 0,
            "overruns": [],
            "run_checks": 0,
            "run_mismatches": [],
            "unresolved": 0,
            "traced_children_ignored": 0,
            "declared_leaf": SpecInfo.get("child_slots") == [],
        }
        for NameTextInfo, SpecInfo in Declared.items()
    }


# span accounting records computed body coverage against observed containment bounds
def RecordSpanMut(
    RowDataInfo: dict, SegInfo: dict, WalkerInfo: Walker, IndexData: int, LabelInfo: str
) -> None:
    HeadInfo = SegInfo["offset"] + SegInfo["header"]
    GapInfo = WalkerInfo.Bound(IndexData)
    if RowDataInfo["declared_leaf"] and WalkerInfo.KidsInfo[IndexData]:
        RowDataInfo["traced_children_ignored"] += 1
    EndIndex = WalkerInfo.BodyEnd(IndexData)
    if EndIndex is None:
        RowDataInfo["unresolved"] += 1
        return
    RowDataInfo["computed"] += 1
    Length = EndIndex - HeadInfo
    if Length > GapInfo:
        RowDataInfo["overruns"].append(
            {"label": LabelInfo, "node": IndexData, "computed": Length, "gap": GapInfo}
        )
    elif Length == GapInfo:
        RowDataInfo["exact_span"] += 1
    if SegInfo["depth"] == 0 and EndIndex != SegInfo["scope_end"]:
        RowDataInfo["overruns"].append(
            {
                "label": LabelInfo,
                "node": IndexData,
                "computed": Length,
                "gap": SegInfo["scope_end"] - HeadInfo,
                "reason": "top level object must tile exactly",
            }
        )


# run accounting compares every predicted child boundary with its observed trace offset
def RecordRunsMut(
    RowDataInfo: dict, WalkerInfo: Walker, IndexData: int, LabelInfo: str
) -> None:
    for SlotIndex, Predicted, Observed in WalkerInfo.ChildOffsets(IndexData):
        RowDataInfo["run_checks"] += 1
        if Predicted != Observed:
            RowDataInfo["run_mismatches"].append(
                {
                    "label": LabelInfo,
                    "node": IndexData,
                    "run": "lead" if SlotIndex < 0 else str(SlotIndex),
                    "expected": Observed,
                    "computed": Predicted,
                }
            )


# node auditing filters unsupported objects before delegating span and run evidence
def AuditNodeMut(
    Report: DictInfo[str, dict],
    Declared: DictInfo[str, dict],
    SegmentsInfo: ListInfo[dict],
    WalkerInfo: Walker,
    IndexData: int,
    LabelInfo: str,
) -> None:
    SegInfo = SegmentsInfo[IndexData]
    if SegInfo["kind"] in KNoBodyKinds:
        return
    NameTextInfo = ClassOf(SegmentsInfo, IndexData)
    if NameTextInfo not in Declared:
        return
    RowDataInfo = Report[NameTextInfo]
    RowDataInfo["instances"] += 1
    RecordSpanMut(RowDataInfo, SegInfo, WalkerInfo, IndexData, LabelInfo)
    RecordRunsMut(RowDataInfo, WalkerInfo, IndexData, LabelInfo)


# verification coordinates trace loading and delegates each class instance audit
def Verify(Layouts: dict, SegmentsDir: Pathlib.Path) -> dict:
    Traces = LoadTraces(str(SegmentsDir), "")
    Fallback = FallbackRuns(Traces)
    Declared = Layouts["classes"]
    Blobs = {
        TraceInfo["label"]: SldprtArchive.open(PartPath(TraceInfo)).require(KStream)
        for TraceInfo in Traces
    }
    Report = BuildReport(Declared)
    for TraceInfo in Traces:
        LabelInfo = TraceInfo["label"]
        SegmentsInfo = TraceInfo["segments"]
        WalkerInfo = Walker(SegmentsInfo, Blobs[LabelInfo], Declared, Fallback)
        for IndexData in range(len(SegmentsInfo)):
            AuditNodeMut(
                Report, Declared, SegmentsInfo, WalkerInfo, IndexData, LabelInfo
            )
    return Report


# needed to keep reverse engineering responsibilities isolated and maintainable
def MainRun() -> int:
    ParserInfo = Argparse.ArgumentParser()
    ParserInfo.add_argument(
        "--layouts",
        default=str(KRootInfo / "re/data/Layouts/ClassLayoutsDecompiled.json"),
    )
    ParserInfo.add_argument("--segments", default=str(KRootInfo / "re/data/segments"))
    ParserInfo.add_argument("--out", default="")
    ArgValues = ParserInfo.parse_args()
    Layouts = JsonData.loads(
        ResolveInput(ArgValues.layouts).read_text(encoding="utf-8")
    )
    Report = Verify(Layouts, ResolveFolder(ArgValues.segments))
    Failures = 0
    print(
        "%-24s %-9s %5s %5s %5s %5s %6s %5s %5s"
        % ("class", "claim", "inst", "comp", "exact", "unres", "runchk", "runX", "over")
    )
    for NameTextInfo in sorted(Report):
        RowDataInfo = Report[NameTextInfo]
        BadInfo = len(RowDataInfo["run_mismatches"]) + len(RowDataInfo["overruns"])
        if RowDataInfo["confidence"] == "confirmed" and BadInfo:
            Failures += BadInfo
        print(
            "%-24s %-9s %5d %5d %5d %5d %6d %5d %5d"
            % (
                NameTextInfo,
                RowDataInfo["confidence"],
                RowDataInfo["instances"],
                RowDataInfo["computed"],
                RowDataInfo["exact_span"],
                RowDataInfo["unresolved"],
                RowDataInfo["run_checks"],
                len(RowDataInfo["run_mismatches"]),
                len(RowDataInfo["overruns"]),
            )
        )
    for NameTextInfo in sorted(Report):
        RowDataInfo = Report[NameTextInfo]
        for ItemData in RowDataInfo["overruns"]:
            print(
                "OVERRUN  %-22s %-16s node=%-4d computed=%-6d gap=%-6d %s"
                % (
                    NameTextInfo,
                    ItemData["label"],
                    ItemData["node"],
                    ItemData["computed"],
                    ItemData["gap"],
                    ItemData.get("reason", ""),
                )
            )
        for ItemData in RowDataInfo["run_mismatches"]:
            print(
                "MISMATCH %-22s %-16s node=%-4d run=%-4s expected=%-6d computed=%-6d"
                % (
                    NameTextInfo,
                    ItemData["label"],
                    ItemData["node"],
                    ItemData["run"],
                    ItemData["expected"],
                    ItemData["computed"],
                )
            )
    for NameTextInfo in sorted(Report):
        RowDataInfo = Report[NameTextInfo]
        if RowDataInfo["traced_children_ignored"]:
            print(
                "NOTE     %-22s %d instances carry traced children that its Serialize does not read"
                % (NameTextInfo, RowDataInfo["traced_children_ignored"])
            )
    print(
        "classes=%d confirmed=%d failures=%d"
        % (
            len(Report),
            sum(
                (
                    1
                    for ResultData in Report.values()
                    if ResultData["confidence"] == "confirmed"
                )
            ),
            Failures,
        )
    )
    if ArgValues.out:
        ResolveOutput(ArgValues.out).write_text(
            JsonData.dumps(Report, indent=1), encoding="utf-8"
        )
    return 1 if Failures else 0


if __name__ == "__main__":
    raise SystemExit(MainRun())
