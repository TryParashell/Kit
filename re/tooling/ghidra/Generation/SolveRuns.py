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
import glob as GlobInfo
import json as JsonData
import os as OsLayer
from typing import Dict as DictInfo, List as ListInfo, Optional, Sequence, Tuple

from convert.Security.PathBoundary import ResolveFolder, ResolveOutput


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
KNoBodyKinds = ("null", "objectref")


# needed to keep reverse engineering responsibilities isolated and maintainable
def LoadTraces(SegmentsDir: str, Labels: str) -> ListInfo[dict]:
    Traces = []
    SegmentsDir = str(ResolveFolder(SegmentsDir))
    for PathInfoData in sorted(
        GlobInfo.glob(OsLayer.path.join(SegmentsDir, "segments_*.json"))
    ):
        with open(PathInfoData, encoding="utf-8") as TraceHandle:
            Traces.append(JsonData.load(TraceHandle))
    if Labels:
        Wanted = set(Labels.split(","))
        Traces = [TextData for TextData in Traces if TextData["label"] in Wanted]
    return Traces


# needed to keep reverse engineering responsibilities isolated and maintainable
def ChildrenOf(SegmentsInfo: Sequence[dict]) -> ListInfo[ListInfo[int]]:
    Children: ListInfo[ListInfo[int]] = [
        list(range(IndexInfo, IndexInfo)) for IndexInfo in range(len(SegmentsInfo))
    ]
    for IndexInfo, SegInfo in enumerate(SegmentsInfo):
        if SegInfo["parent"] >= 0:
            Children[SegInfo["parent"]].append(IndexInfo)
    return Children


# leaf solving stays independent because leaf runs do not participate in child boundary propagation
def SolveLeaf(SelfRef, LabelInfo: str, NodeInfoInfo: int, SegInfo: dict) -> int:
    HeadInfo = SegInfo["offset"] + SegInfo["header"]
    KeyName = SelfRef.KeyName(LabelInfo, NodeInfoInfo, -2)
    Known = SelfRef.EndIndex[LabelInfo, NodeInfoInfo]
    if Known is not None:
        return int(SelfRef.IsSetRun(KeyName, Known - HeadInfo, LabelInfo, NodeInfoInfo))
    if KeyName in SelfRef.RunsInfo:
        return int(
            SelfRef.IsSetEnd(
                LabelInfo, NodeInfoInfo, HeadInfo + SelfRef.RunsInfo[KeyName]
            )
        )
    return 0


# child solving stays independent because adjacent slot boundaries share one propagation contract
def SolveSlots(
    SelfRef,
    LabelInfo: str,
    NodeInfoInfo: int,
    SegInfo: dict,
    SegmentsInfo: Sequence[dict],
    KidsInfo: ListInfo[int],
) -> int:
    HeadInfo = SegInfo["offset"] + SegInfo["header"]
    Progress = int(
        SelfRef.IsSetRun(
            SelfRef.KeyName(LabelInfo, NodeInfoInfo, -1),
            SegmentsInfo[KidsInfo[0]]["offset"] - HeadInfo,
            LabelInfo,
            NodeInfoInfo,
        )
    )
    for SlotIndex, IsChild in enumerate(KidsInfo):
        KeyName = SelfRef.KeyName(LabelInfo, NodeInfoInfo, SlotIndex)
        Bound = (
            SegmentsInfo[KidsInfo[SlotIndex + 1]]["offset"]
            if SlotIndex + 1 < len(KidsInfo)
            else SelfRef.EndIndex[LabelInfo, NodeInfoInfo]
        )
        ChildEndInfo = SelfRef.EndIndex[LabelInfo, IsChild]
        if Bound is None and ChildEndInfo is None:
            continue
        if Bound is not None and ChildEndInfo is not None:
            Progress += int(
                SelfRef.IsSetRun(KeyName, Bound - ChildEndInfo, LabelInfo, NodeInfoInfo)
            )
        elif Bound is not None and KeyName in SelfRef.RunsInfo:
            Progress += int(
                SelfRef.IsSetEnd(LabelInfo, IsChild, Bound - SelfRef.RunsInfo[KeyName])
            )
        elif ChildEndInfo is not None and KeyName in SelfRef.RunsInfo:
            Progress += int(
                SelfRef.IsSetEnd(
                    LabelInfo, NodeInfoInfo, ChildEndInfo + SelfRef.RunsInfo[KeyName]
                )
            )
    return Progress


# key behavior remains isolated so run naming and seed state evolve together
class SolverKeys:

    # stable run keys let every trace contribute to the same recovered grammar
    def KeyName(SelfRef, LabelInfo: str, NodeInfoInfo: int, SlotIndex: int) -> str:
        NameTextInfo = SelfRef.SegmentsInfo[LabelInfo][NodeInfoInfo]["class_name"]
        if SlotIndex == -2:
            return NameTextInfo + "@leaf"
        if SlotIndex == -1:
            return NameTextInfo + "@lead"
        return "%s@%d" % (NameTextInfo, SlotIndex)

    # fresh seed state is needed before each conflict refinement round
    def SeedInfo(SelfRef) -> None:
        SelfRef.RunsInfo = {}
        SelfRef.Witness = Collects.defaultdict(list)
        SelfRef.EndIndex = {}
        for LabelInfo, SegmentsInfo in SelfRef.SegmentsInfo.items():
            for IndexInfo, SegInfo in enumerate(SegmentsInfo):
                if SegInfo["kind"] in KNoBodyKinds:
                    SelfRef.EndIndex[LabelInfo, IndexInfo] = (
                        SegInfo["offset"] + SegInfo["header"]
                    )
                elif SegInfo["depth"] == 0:
                    SelfRef.EndIndex[LabelInfo, IndexInfo] = SegInfo["scope_end"]
                else:
                    SelfRef.EndIndex[LabelInfo, IndexInfo] = None


# run reconciliation remains isolated because conflicting scalar evidence has one owner
class SolverRuns:

    # repeated run observations need one conflict aware reconciliation boundary
    def IsSetRun(
        SelfRef, KeyName: str, ValueInfo: int, LabelInfo: str, NodeInfoInfo: int
    ) -> bool:
        if KeyName in SelfRef.ValueValue:
            return False
        if ValueInfo < 0:
            SelfRef.Conflicts.append(
                {
                    "key": KeyName,
                    "reason": "negative",
                    "observed": ValueInfo,
                    "label": LabelInfo,
                    "node": NodeInfoInfo,
                }
            )
            SelfRef.ValueValue.add(KeyName)
            SelfRef.RunsInfo.pop(KeyName, None)
            return False
        Previous = SelfRef.RunsInfo.get(KeyName)
        if Previous is None:
            SelfRef.RunsInfo[KeyName] = ValueInfo
            SelfRef.Witness[KeyName].append("%s:%d" % (LabelInfo, NodeInfoInfo))
            return True
        if Previous != ValueInfo:
            SelfRef.Conflicts.append(
                {
                    "key": KeyName,
                    "reason": "mismatch",
                    "existing": Previous,
                    "observed": ValueInfo,
                    "label": LabelInfo,
                    "node": NodeInfoInfo,
                }
            )
            SelfRef.ValueValue.add(KeyName)
            SelfRef.RunsInfo.pop(KeyName, None)
            return False
        SelfRef.Witness[KeyName].append("%s:%d" % (LabelInfo, NodeInfoInfo))
        return False


# end reconciliation remains isolated because object bounds use a distinct validity contract
class SolverEnds:

    # recovered ends must stay inside the owning serialized object scope
    def IsSetEnd(SelfRef, LabelInfo: str, NodeInfoInfo: int, ValueInfo: int) -> bool:
        SegInfo = SelfRef.SegmentsInfo[LabelInfo][NodeInfoInfo]
        LowValue = SegInfo["offset"] + SegInfo["header"]
        HighValue = SegInfo["scope_end"]
        if ValueInfo < LowValue or ValueInfo > HighValue:
            SelfRef.Conflicts.append(
                {
                    "key": SegInfo["class_name"] + "@end",
                    "reason": "out_of_range",
                    "observed": ValueInfo,
                    "low": LowValue,
                    "high": HighValue,
                    "label": LabelInfo,
                    "node": NodeInfoInfo,
                }
            )
            return False
        Current = SelfRef.EndIndex[LabelInfo, NodeInfoInfo]
        if Current is None:
            SelfRef.EndIndex[LabelInfo, NodeInfoInfo] = ValueInfo
            return True
        return False


# propagation remains isolated because fixed point iteration is an independent solver strategy
class SolverPass:

    # one pass propagates every currently known boundary across all traces
    def PassOnce(SelfRef) -> int:
        Progress = 0
        for LabelInfo, SegmentsInfo in SelfRef.SegmentsInfo.items():
            KidsAll = SelfRef.KidsInfo[LabelInfo]
            for NodeInfoInfo, SegInfo in enumerate(SegmentsInfo):
                if SegInfo["kind"] in KNoBodyKinds:
                    continue
                KidsInfo = KidsAll[NodeInfoInfo]
                if not KidsInfo:
                    Progress += SolveLeaf(SelfRef, LabelInfo, NodeInfoInfo, SegInfo)
                    continue
                Progress += SolveSlots(
                    SelfRef, LabelInfo, NodeInfoInfo, SegInfo, SegmentsInfo, KidsInfo
                )
        return Progress


# result behavior remains isolated because iteration and body reporting form the public solver surface
class SolverResult:

    # bounded refinement prevents contradictory traces from causing endless retries
    def Solve(SelfRef, Rounds: int = 400) -> None:
        Attempts = 0
        while Attempts < 40:
            Attempts += 1
            Before = len(SelfRef.ValueValue)
            SelfRef.SeedInfo()
            RoundIndex = 0
            while RoundIndex < Rounds:
                RoundIndex += 1
                if SelfRef.PassOnce() == 0:
                    break
            if len(SelfRef.ValueValue) == Before:
                break

    # body summaries expose recovered lengths without leaking solver state mutations
    def Bodies(SelfRef) -> DictInfo[str, ListInfo[dict]]:
        Result: DictInfo[str, ListInfo[dict]] = Collects.defaultdict(list)
        for LabelInfo, SegmentsInfo in SelfRef.SegmentsInfo.items():
            for IndexInfo, SegInfo in enumerate(SegmentsInfo):
                if SegInfo["kind"] in KNoBodyKinds:
                    continue
                EndIndex = SelfRef.EndIndex[LabelInfo, IndexInfo]
                Result[SegInfo["class_name"]].append(
                    {
                        "label": LabelInfo,
                        "node": IndexInfo,
                        "kind": SegInfo["kind"],
                        "depth": SegInfo["depth"],
                        "children": len(SelfRef.KidsInfo[LabelInfo][IndexInfo]),
                        "span": SegInfo["scope_end"]
                        - SegInfo["offset"]
                        - SegInfo["header"],
                        "body": (
                            None
                            if EndIndex is None
                            else EndIndex - SegInfo["offset"] - SegInfo["header"]
                        ),
                    }
                )
        return Result


# composition keeps solver responsibilities independently extensible behind one stable public type
class Solver(SolverKeys, SolverRuns, SolverEnds, SolverPass, SolverResult):

    # construction owns trace indexing while every solving strategy remains replaceable
    def __init__(SelfRef, Traces: Sequence[dict]) -> None:
        SelfRef.Traces = list(Traces)
        SelfRef.SegmentsInfo: DictInfo[str, ListInfo[dict]] = {}
        SelfRef.KidsInfo: DictInfo[str, ListInfo[ListInfo[int]]] = {}
        for TraceInfo in SelfRef.Traces:
            LabelInfo = TraceInfo["label"]
            SelfRef.SegmentsInfo[LabelInfo] = TraceInfo["segments"]
            SelfRef.KidsInfo[LabelInfo] = ChildrenOf(TraceInfo["segments"])
        SelfRef.ValueValue: set = set()
        SelfRef.Conflicts: ListInfo[dict] = []
        SelfRef.RunsInfo: DictInfo[str, int] = {}
        SelfRef.EndIndex: DictInfo[Tuple[str, int], Optional[int]] = {}
        SelfRef.Witness: DictInfo[str, ListInfo[str]] = Collects.defaultdict(list)

    KAliasNames = {
        "traces": "Traces",
        "segments": "SegmentsInfo",
        "kids": "KidsInfo",
        "variable": "ValueValue",
        "conflicts": "Conflicts",
        "runs": "RunsInfo",
        "end": "EndIndex",
        "witness": "Witness",
        "key": "KeyName",
        "seed": "SeedInfo",
        "set_run": "IsSetRun",
        "set_end": "IsSetEnd",
        "pass_once": "PassOnce",
        "solve": "Solve",
        "bodies": "Bodies",
    }


# needed to keep reverse engineering responsibilities isolated and maintainable
Solver.__getattr__ = GetLegacyAttr

# needed to keep reverse engineering responsibilities isolated and maintainable
Solver.__setattr__ = SetLegacyMut


# needed to keep reverse engineering responsibilities isolated and maintainable
def Summarise(Bodies: DictInfo[str, ListInfo[dict]], SolverInfo: Solver) -> dict:
    Summary: DictInfo[str, dict] = {}
    for NameTextInfo, GetRows in sorted(Bodies.items()):
        Resolved = [
            ResultData["body"]
            for ResultData in GetRows
            if ResultData["body"] is not None
        ]
        CounterInfo = Collects.Counter(Resolved)
        OwnInfo = {
            KeyName: ValueInfo
            for KeyName, ValueInfo in SolverInfo.runs.items()
            if KeyName.rsplit("@", 1)[0] == NameTextInfo
        }
        ValueValue = sorted(
            (
                KeyIndex
                for KeyIndex in SolverInfo.variable
                if KeyIndex.rsplit("@", 1)[0] == NameTextInfo
            )
        )
        ChildCounts = sorted(
            Collects.Counter((ResultData["children"] for ResultData in GetRows)).items()
        )
        ScalarTotal = None
        if len(ChildCounts) == 1 and (not ValueValue):
            Slots = ChildCounts[0][0]
            if Slots == 0:
                if NameTextInfo + "@leaf" in OwnInfo:
                    ScalarTotal = OwnInfo[NameTextInfo + "@leaf"]
            else:
                Needed = [NameTextInfo + "@lead"] + [
                    "%s@%d" % (NameTextInfo, InnerIndex) for InnerIndex in range(Slots)
                ]
                if all((KeyIndex in OwnInfo for KeyIndex in Needed)):
                    ScalarTotal = sum((OwnInfo[KeyIndex] for KeyIndex in Needed))
        Summary[NameTextInfo] = {
            "instances": len(GetRows),
            "resolved": len(Resolved),
            "body_lengths": sorted(CounterInfo.items()),
            "child_counts": ChildCounts,
            "runs": dict(sorted(OwnInfo.items())),
            "variable_runs": ValueValue,
            "own_scalar_total": ScalarTotal,
        }
    return Summary


# needed to keep reverse engineering responsibilities isolated and maintainable
def MainRun() -> int:
    ParserInfo = Argparse.ArgumentParser()
    ParserInfo.add_argument("--segments", default="re/data/segments")
    ParserInfo.add_argument("--labels", default="")
    ParserInfo.add_argument("--out", required=True)
    ArgValues = ParserInfo.parse_args()
    Traces = LoadTraces(ArgValues.segments, ArgValues.labels)
    SolverInfo = Solver(Traces)
    SolverInfo.solve()
    Bodies = SolverInfo.bodies()
    PayloadInfo = {
        "traces": [TextData["label"] for TextData in Traces],
        "run_keys": dict(sorted(SolverInfo.runs.items())),
        "variable_runs": sorted(SolverInfo.variable),
        "conflicts": SolverInfo.conflicts,
        "witnesses": {
            KeyIndex: len(ValueData)
            for KeyIndex, ValueData in sorted(SolverInfo.witness.items())
        },
        "classes": Summarise(Bodies, SolverInfo),
    }
    with ResolveOutput(ArgValues.out).open("w", encoding="utf-8") as Handle:
        JsonData.dump(PayloadInfo, Handle, indent=1)
        Handle.write("\n")
    Total = sum((len(ValueData) for ValueData in Bodies.values()))
    Resolved = sum(
        (
            1
            for ValueData in Bodies.values()
            for ResultData in ValueData
            if ResultData["body"] is not None
        )
    )
    print(
        "objects=%d resolved=%d runkeys=%d variable=%d conflicts=%d"
        % (
            Total,
            Resolved,
            len(SolverInfo.runs),
            len(SolverInfo.variable),
            len(SolverInfo.conflicts),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(MainRun())
