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
from pathlib import Path as PathInfo
import sys as System
from typing import Dict as DictInfo, List as ListInfo, Mapping, Sequence, Tuple

# needed to keep reverse engineering responsibilities isolated and maintainable
KHereInfo = PathInfo(__file__).resolve().parent
if str(KHereInfo) not in System.path:
    System.path.insert(0, str(KHereInfo))
import SolveRuns


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
KRootInfo = KHereInfo.parents[3]

# needed to keep reverse engineering responsibilities isolated and maintainable
KDefaultValue = KRootInfo / "re" / "data" / "segments"

# needed to keep reverse engineering responsibilities isolated and maintainable
KDefaultInfo = KRootInfo / "re" / "data" / "Layouts" / "ClassLayoutsDecompiled.json"

# needed to keep reverse engineering responsibilities isolated and maintainable
KDefaultExtern = KRootInfo / "re" / "data" / "Layouts" / "ExternalClasses.json"

# needed to keep reverse engineering responsibilities isolated and maintainable
KDefaultEntry = KRootInfo / "re" / "data" / "Layouts" / "ClassLayoutsVersioned.json"

# needed to keep reverse engineering responsibilities isolated and maintainable
KDefaultOut = KRootInfo / "re" / "data" / "Layouts" / "ClassLayouts.json"

# needed to keep reverse engineering responsibilities isolated and maintainable
KExternSource = "re/data/Layouts/ExternalClasses.json"

# needed to keep reverse engineering responsibilities isolated and maintainable
KExternPrefix = "external#"

# needed to keep reverse engineering responsibilities isolated and maintainable
KPinnedSlots = ("component", "object_list", "pmark_record")

# needed to keep reverse engineering responsibilities isolated and maintainable
KNoBodyKinds = SolveRuns.KNoBodyKinds

# needed to keep reverse engineering responsibilities isolated and maintainable
KLeadRun = "lead"

# needed to keep reverse engineering responsibilities isolated and maintainable
KLeafRun = "leaf"

# needed to keep reverse engineering responsibilities isolated and maintainable
KLoopTailRun = "tail"

# needed to keep reverse engineering responsibilities isolated and maintainable
KRepeatedSlot = "..."

# needed to keep reverse engineering responsibilities isolated and maintainable
KPolymorphic = "*"

# needed to keep reverse engineering responsibilities isolated and maintainable
KSolvedSource = "re/data/segments"

# needed to keep reverse engineering responsibilities isolated and maintainable
KDecompiled = "re/data/Layouts/ClassLayoutsDecompiled.json"

# needed to keep reverse engineering responsibilities isolated and maintainable
KVersioned = "re/data/Layouts/ClassLayoutsVersioned.json"


# needed to keep reverse engineering responsibilities isolated and maintainable
def Reparented(
    SegmentsInfo: Sequence[Mapping[str, object]],
) -> Tuple[ListInfo[ListInfo[int]], ListInfo[int]]:
    KidsInfo = SolveRuns.ChildrenOf(SegmentsInfo)
    Parents = [int(ItemData["parent"]) for ItemData in SegmentsInfo]
    for NodeInfoInfo in range(len(SegmentsInfo) - 1, -1, -1):
        if (
            SegmentsInfo[NodeInfoInfo]["kind"] not in KNoBodyKinds
            or not KidsInfo[NodeInfoInfo]
        ):
            continue
        Owner = Parents[NodeInfoInfo]
        Moved = KidsInfo[NodeInfoInfo]
        KidsInfo[NodeInfoInfo] = []
        for IsChild in Moved:
            Parents[IsChild] = Owner
        if Owner >= 0:
            KidsInfo[Owner] = sorted(KidsInfo[Owner] + Moved)
    return (KidsInfo, Parents)


# needed to keep reverse engineering responsibilities isolated and maintainable
def RecordEnds(TraceInfo: Mapping[str, object]) -> ListInfo[int]:
    SegmentsInfo = list(TraceInfo["segments"])
    Total = int(TraceInfo["stream_length"])
    CountInfo = len(SegmentsInfo)
    Children = Reparented(SegmentsInfo)[0]
    LastInfo = list(range(CountInfo))
    for NodeInfoInfo in range(CountInfo - 1, -1, -1):
        Bound = NodeInfoInfo
        for IsChild in Children[NodeInfoInfo]:
            Bound = max(Bound, LastInfo[IsChild])
        LastInfo[NodeInfoInfo] = Bound
    EndsInfo: ListInfo[int] = []
    for NodeInfoInfo, ItemData in enumerate(SegmentsInfo):
        if ItemData["kind"] in KNoBodyKinds:
            EndsInfo.append(ItemData["offset"] + ItemData["header"])
            continue
        Follower = LastInfo[NodeInfoInfo] + 1
        EndsInfo.append(
            SegmentsInfo[Follower]["offset"] if Follower < CountInfo else Total
        )
    return EndsInfo


# needed to keep reverse engineering responsibilities isolated and maintainable
def IsContiguous(TraceInfo: Mapping[str, object]) -> bool:
    SegmentsInfo = list(TraceInfo["segments"])
    Children = Reparented(SegmentsInfo)[0]
    Reach: ListInfo[set] = [
        set(range(IndexInfo, IndexInfo)) for IndexInfo in range(len(SegmentsInfo))
    ]
    for NodeInfoInfo in range(len(SegmentsInfo) - 1, -1, -1):
        AccInfo: set = set()
        for IsChild in Children[NodeInfoInfo]:
            AccInfo.add(IsChild)
            AccInfo |= Reach[IsChild]
        Reach[NodeInfoInfo] = AccInfo
    for NodeInfoInfo, Descendants in enumerate(Reach):
        if not Descendants:
            continue
        if Descendants != set(range(NodeInfoInfo + 1, max(Descendants) + 1)):
            return False
    return True


# needed to keep reverse engineering responsibilities isolated and maintainable
class TilingSolver(SolveRuns.Solver):

    # needed to keep reverse engineering responsibilities isolated and maintainable
    def __init__(SelfRef, Traces: Sequence[Mapping[str, object]]) -> None:
        super().__init__(Traces)
        SelfRef.Exact: DictInfo[str, ListInfo[int]] = {}
        SelfRef.Parents: DictInfo[str, ListInfo[int]] = {}
        for TraceInfo in Traces:
            LabelInfo = str(TraceInfo["label"])
            if not IsContiguous(TraceInfo):
                raise ValueError(f"trace {LabelInfo} has interleaved object subtrees")
            KidsInfo, Parents = Reparented(list(TraceInfo["segments"]))
            SelfRef.KidsInfo[LabelInfo] = KidsInfo
            SelfRef.Parents[LabelInfo] = Parents
            SelfRef.Exact[LabelInfo] = RecordEnds(TraceInfo)

    # needed to keep reverse engineering responsibilities isolated and maintainable
    def SeedInfo(SelfRef) -> None:
        super().seed()
        for LabelInfo, EndsInfo in SelfRef.Exact.items():
            for NodeInfoInfo, ValueInfo in enumerate(EndsInfo):
                SelfRef.EndIndex[LabelInfo, NodeInfoInfo] = ValueInfo

    KAliasNames = {"seed": "SeedInfo"}


# needed to keep reverse engineering responsibilities isolated and maintainable
TilingSolver.__getattr__ = GetLegacyAttr

# needed to keep reverse engineering responsibilities isolated and maintainable
TilingSolver.__setattr__ = SetLegacyMut


# needed to keep reverse engineering responsibilities isolated and maintainable
def SlotNames(SolverInfo: SolveRuns.Solver) -> DictInfo[str, DictInfo[int, set]]:

    # needed to keep reverse engineering responsibilities isolated and maintainable
    Table: DictInfo[str, DictInfo[int, set]] = Collects.defaultdict(
        lambda: Collects.defaultdict(set)
    )
    for LabelInfo, SegmentsInfo in SolverInfo.segments.items():
        KidsInfo = SolverInfo.kids[LabelInfo]
        for NodeInfoInfo, ItemData in enumerate(SegmentsInfo):
            if ItemData["kind"] in KNoBodyKinds:
                continue
            for SlotIndex, IsChild in enumerate(KidsInfo[NodeInfoInfo]):
                Entry = SegmentsInfo[IsChild]
                if Entry["kind"] in KNoBodyKinds:
                    Table[ItemData["class_name"]][SlotIndex].add(KPolymorphic)
                else:
                    Table[ItemData["class_name"]][SlotIndex].add(Entry["class_name"])
    return Table


# needed to keep reverse engineering responsibilities isolated and maintainable
def ChildCounts(SolverInfo: SolveRuns.Solver) -> DictInfo[str, Collects.Counter]:
    Table: DictInfo[str, Collects.Counter] = Collects.defaultdict(Collects.Counter)
    for LabelInfo, SegmentsInfo in SolverInfo.segments.items():
        KidsInfo = SolverInfo.kids[LabelInfo]
        for NodeInfoInfo, ItemData in enumerate(SegmentsInfo):
            if ItemData["kind"] in KNoBodyKinds:
                continue
            Table[ItemData["class_name"]][len(KidsInfo[NodeInfoInfo])] += 1
    return Table


# needed to keep reverse engineering responsibilities isolated and maintainable
def ObservedLengths(SolverInfo: SolveRuns.Solver) -> DictInfo[str, Collects.Counter]:
    Table: DictInfo[str, Collects.Counter] = Collects.defaultdict(Collects.Counter)
    for LabelInfo, SegmentsInfo in SolverInfo.segments.items():
        KidsInfo = SolverInfo.kids[LabelInfo]
        EndsInfo = SolverInfo.end
        for NodeInfoInfo, ItemData in enumerate(SegmentsInfo):
            if ItemData["kind"] in KNoBodyKinds:
                continue
            NameTextInfo = ItemData["class_name"]
            HeadInfo = ItemData["offset"] + ItemData["header"]
            Slots = KidsInfo[NodeInfoInfo]
            OwnEnd = EndsInfo[LabelInfo, NodeInfoInfo]
            if not Slots:
                if OwnEnd is not None:
                    Table[f"{NameTextInfo}@{KLeafRun}"][OwnEnd - HeadInfo] += 1
                continue
            Table[f"{NameTextInfo}@{KLeadRun}"][
                SegmentsInfo[Slots[0]]["offset"] - HeadInfo
            ] += 1
            for SlotIndex, IsChild in enumerate(Slots):
                Bound = (
                    SegmentsInfo[Slots[SlotIndex + 1]]["offset"]
                    if SlotIndex + 1 < len(Slots)
                    else OwnEnd
                )
                ChildEndInfo = EndsInfo[LabelInfo, IsChild]
                if Bound is None or ChildEndInfo is None:
                    continue
                Table[f"{NameTextInfo}@{SlotIndex}"][Bound - ChildEndInfo] += 1
    return Table


# needed to keep reverse engineering responsibilities isolated and maintainable
def LeafInstances(SolverInfo: TilingSolver) -> DictInfo[str, ListInfo[dict]]:
    Table: DictInfo[str, ListInfo[dict]] = Collects.defaultdict(list)
    for LabelInfo, SegmentsInfo in SolverInfo.segments.items():
        KidsInfo = SolverInfo.kids[LabelInfo]
        for NodeInfoInfo, ItemData in enumerate(SegmentsInfo):
            if ItemData["kind"] in KNoBodyKinds or KidsInfo[NodeInfoInfo]:
                continue
            EndIndex = SolverInfo.end[LabelInfo, NodeInfoInfo]
            if EndIndex is None:
                continue
            Parent = SolverInfo.parents[LabelInfo][NodeInfoInfo]
            if Parent < 0:
                Context = ("<root>", -1)
            else:
                Context = (
                    SegmentsInfo[Parent]["class_name"],
                    KidsInfo[Parent].index(NodeInfoInfo),
                )
            Table[ItemData["class_name"]].append(
                {
                    "label": LabelInfo,
                    "node": NodeInfoInfo,
                    "head": ItemData["offset"] + ItemData["header"],
                    "span": EndIndex - ItemData["offset"] - ItemData["header"],
                    "context": Context,
                }
            )
    return Table


# needed to keep reverse engineering responsibilities isolated and maintainable
def StringLength(ByteBlob: bytes, Offset: int) -> int:
    if ByteBlob[Offset : Offset + 3] != b"\xff\xfe\xff":
        return -1
    Units = ByteBlob[Offset + 3]
    HeadInfo = 4
    if Units == 255:
        Units = int.from_bytes(ByteBlob[Offset + 4 : Offset + 6], "little")
        HeadInfo = 6
    EndIndex = Offset + HeadInfo + 2 * Units
    if EndIndex > len(ByteBlob):
        return -1
    return HeadInfo + 2 * Units


# leaf measurement stays isolated so string tail evidence has one validation boundary
def MeasureLeaf(
    SolverInfo: SolveRuns.Solver,
    StreamsInfo: Mapping[str, bytes],
    Owners: DictInfo[Tuple[str, int], set],
    NameTextInfo: str,
    GetRows: ListInfo[dict],
) -> tuple[int, DictInfo[Tuple[str, int], set]] | None:
    if any((RowDataInfo["label"] not in StreamsInfo for RowDataInfo in GetRows)):
        return None
    if len({RowDataInfo["span"] for RowDataInfo in GetRows}) < 2:
        return None
    Measured: ListInfo[Tuple[dict, int]] = []
    for RowDataInfo in GetRows:
        Length = StringLength(StreamsInfo[RowDataInfo["label"]], RowDataInfo["head"])
        if Length < 0 or Length > RowDataInfo["span"]:
            return None
        Measured.append((RowDataInfo, RowDataInfo["span"] - Length))
    Floor = min((TailInfo for SpareValue, TailInfo in Measured))
    Deltas: DictInfo[Tuple[str, int], set] = Collects.defaultdict(set)
    for RowDataInfo, TailInfo in Measured:
        Deltas[RowDataInfo["context"]].add(TailInfo - Floor)
    if any((len(Values) != 1 for Values in Deltas.values())):
        return None
    for Context, Values in Deltas.items():
        Delta = next(iter(Values))
        if Delta and (
            Context == ("<root>", -1) or Owners.get(Context) != {NameTextInfo}
        ):
            return None
    return Floor, Deltas


# leaf rebalancing aggregates validated measurements without owning their detection rules
def RebalanceLeaves(
    SolverInfo: SolveRuns.Solver, StreamsInfo: Mapping[str, bytes]
) -> Tuple[DictInfo[str, int], DictInfo[Tuple[str, int], int]]:
    Tails: DictInfo[str, int] = {}
    Shifts: DictInfo[Tuple[str, int], int] = {}
    Owners = SlotOwners(SolverInfo)
    for NameTextInfo, GetRows in sorted(LeafInstances(SolverInfo).items()):
        Measurement = MeasureLeaf(
            SolverInfo, StreamsInfo, Owners, NameTextInfo, GetRows
        )
        if Measurement is None:
            continue
        Floor, Deltas = Measurement
        Tails[NameTextInfo] = Floor
        for Context, Values in Deltas.items():
            Delta = next(iter(Values))
            if Delta:
                Shifts[Context] = Shifts.get(Context, 0) + Delta
    return (Tails, Shifts)


# needed to keep reverse engineering responsibilities isolated and maintainable
def SlotOwners(SolverInfo: SolveRuns.Solver) -> DictInfo[Tuple[str, int], set]:
    Table: DictInfo[Tuple[str, int], set] = Collects.defaultdict(set)
    for LabelInfo, SegmentsInfo in SolverInfo.segments.items():
        KidsInfo = SolverInfo.kids[LabelInfo]
        for NodeInfoInfo, ItemData in enumerate(SegmentsInfo):
            if ItemData["kind"] in KNoBodyKinds:
                continue
            for SlotIndex, IsChild in enumerate(KidsInfo[NodeInfoInfo]):
                Entry = SegmentsInfo[IsChild]
                Table[ItemData["class_name"], SlotIndex].add(
                    KPolymorphic
                    if Entry["kind"] in KNoBodyKinds
                    else Entry["class_name"]
                )
    return Table


# needed to keep reverse engineering responsibilities isolated and maintainable
def ParentInstances(SolverInfo: SolveRuns.Solver) -> DictInfo[str, ListInfo[dict]]:
    Table: DictInfo[str, ListInfo[dict]] = Collects.defaultdict(list)
    for LabelInfo, SegmentsInfo in SolverInfo.segments.items():
        KidsInfo = SolverInfo.kids[LabelInfo]
        for NodeInfoInfo, ItemData in enumerate(SegmentsInfo):
            if ItemData["kind"] in KNoBodyKinds or not KidsInfo[NodeInfoInfo]:
                continue
            OwnEnd = SolverInfo.end[LabelInfo, NodeInfoInfo]
            if OwnEnd is None:
                continue
            Slots = KidsInfo[NodeInfoInfo]
            ChildEnds = [SolverInfo.end[LabelInfo, IsChild] for IsChild in Slots]
            if any((ValueInfo is None for ValueInfo in ChildEnds)):
                continue
            Table[ItemData["class_name"]].append(
                {
                    "label": LabelInfo,
                    "head": ItemData["offset"] + ItemData["header"],
                    "offsets": [SegmentsInfo[IsChild]["offset"] for IsChild in Slots],
                    "ends": ChildEnds,
                    "names": [
                        (
                            KPolymorphic
                            if SegmentsInfo[IsChild]["kind"] in KNoBodyKinds
                            else SegmentsInfo[IsChild]["class_name"]
                        )
                        for IsChild in Slots
                    ],
                    "own_end": OwnEnd,
                }
            )
    return Table


# needed to keep reverse engineering responsibilities isolated and maintainable
def FinishRepeat(GetRows, StreamsInfo) -> dict | None:
    if len({len(RowDataInfo["names"]) for RowDataInfo in GetRows}) < 2:
        return None
    Smallest = min((len(RowDataInfo["names"]) for RowDataInfo in GetRows))
    for Template in range(Smallest + 1):
        Templates = {
            RowDataInfo["names"][SlotIndex]
            for RowDataInfo in GetRows
            for SlotIndex in range(Template, len(RowDataInfo["names"]))
        }
        if len(Templates) != 1 or KPolymorphic in Templates:
            continue
        Values = set()
        for RowDataInfo in GetRows:
            for SlotIndex in range(Template, len(RowDataInfo["names"])):
                Bound = (
                    RowDataInfo["offsets"][SlotIndex + 1]
                    if SlotIndex + 1 < len(RowDataInfo["names"])
                    else RowDataInfo["own_end"]
                )
                Values.add(Bound - RowDataInfo["ends"][SlotIndex])
        if len(Values) != 1:
            continue
        RunTask = KLeadRun if Template == 0 else str(Template - 1)
        if Template == 0:
            Starts = [RowDataInfo["head"] for RowDataInfo in GetRows]
        else:
            Starts = [RowDataInfo["ends"][Template - 1] for RowDataInfo in GetRows]
        Bounds = [
            (
                RowDataInfo["offsets"][Template]
                if Template < len(RowDataInfo["offsets"])
                else RowDataInfo["own_end"]
            )
            for RowDataInfo in GetRows
        ]
        SpanInfo = min((Bound - StartRun for Bound, StartRun in zip(Bounds, Starts)))
        if SpanInfo <= 0:
            continue
        for WidthInfo in (2, 4):
            for AtInfo in range(0, max(SpanInfo - WidthInfo + 1, 0)):
                if all(
                    (
                        int.from_bytes(
                            StreamsInfo[RowDataInfo["label"]][
                                StartRun + AtInfo : StartRun + AtInfo + WidthInfo
                            ],
                            "little",
                        )
                        == len(RowDataInfo["names"]) - Template
                        for RowDataInfo, StartRun in zip(GetRows, Starts)
                    )
                ):
                    return {
                        "template": Template,
                        "name": next(iter(Templates)),
                        "run": RunTask,
                        "at": AtInfo,
                        "width": WidthInfo,
                        "template_run": next(iter(Values)),
                    }
    return None


# needed to keep reverse engineering responsibilities isolated and maintainable
def RepeatShape(
    SolverInfo: SolveRuns.Solver, StreamsInfo: Mapping[str, bytes], NameTextInfo: str
) -> dict | None:
    GetRows = ParentInstances(SolverInfo).get(NameTextInfo, [])
    if not GetRows or any(
        (RowDataInfo["label"] not in StreamsInfo for RowDataInfo in GetRows)
    ):
        return None
    return FinishRepeat(GetRows, StreamsInfo)


# class shape recovery stays isolated so slot cardinality does not leak into run resolution
def GetClassShape(
    Names: DictInfo[str, DictInfo[int, set]],
    Counts: DictInfo[str, Collects.Counter],
    SolverInfo: SolveRuns.Solver,
    StreamsInfo: Mapping[str, bytes],
    NameTextInfo: str,
) -> tuple[
    Collects.Counter, ListInfo[int], ListInfo[str], bool, dict | None, ListInfo[str]
]:
    Observed = Counts[NameTextInfo]
    SeenInfo = sorted(Observed)
    Widest = SeenInfo[-1]
    Slots: ListInfo[str] = []
    for SlotIndex in range(Widest):
        Candidates = Names[NameTextInfo].get(SlotIndex, {KPolymorphic})
        Concrete = {ItemData for ItemData in Candidates if ItemData != KPolymorphic}
        Slots.append(Concrete.pop() if len(Concrete) == 1 else KPolymorphic)
    Varying = len(SeenInfo) > 1
    Shape = RepeatShape(SolverInfo, StreamsInfo, NameTextInfo) if Varying else None
    if Shape is not None:
        Slots = Slots[: Shape["template"]] + [Shape["name"], KRepeatedSlot]
        Needed = [KLeadRun] + [
            str(SlotIndex) for SlotIndex in range(Shape["template"] + 1)
        ]
    elif Widest == 0:
        Needed = [KLeafRun]
    else:
        if Varying:
            Slots.append(KRepeatedSlot)
        Needed = [KLeadRun] + [str(SlotIndex) for SlotIndex in range(Widest)]
    return Observed, SeenInfo, Slots, Varying, Shape, Needed


# run collection stays isolated because solved string and opaque evidence follow different rules
def CollectRunsMut(
    SolverInfo: SolveRuns.Solver,
    Lengths: DictInfo[str, Collects.Counter],
    StringTails: DictInfo[str, int],
    SlotShifts: DictInfo[Tuple[str, int], int],
    NameTextInfo: str,
    Needed: ListInfo[str],
    Shape: dict | None,
    Stats: dict,
) -> tuple[DictInfo[str, int], ListInfo[dict], int]:
    RunsInfo: DictInfo[str, int] = {}
    ValueValue: ListInfo[dict] = []
    Opaque = 0
    for KeyName in Needed:
        FullInfo = f"{NameTextInfo}@{KeyName}"
        if Shape is not None and KeyName == str(Shape["template"]):
            RunsInfo[KeyName] = Shape["template_run"]
        elif FullInfo in SolverInfo.runs:
            ValueInfo = SolverInfo.runs[FullInfo]
            if KeyName not in (KLeadRun, KLeafRun):
                ValueInfo += SlotShifts.get((NameTextInfo, int(KeyName)), 0)
            RunsInfo[KeyName] = ValueInfo
        elif KeyName == KLeafRun and NameTextInfo in StringTails:
            ValueValue.append(
                {
                    "slot": KLeafRun,
                    "rule": "string",
                    "at": 0,
                    "tail": StringTails[NameTextInfo],
                    "note": f"every traced instance opens with an ff fe ff string and closes with {StringTails[NameTextInfo]} constant bytes",
                }
            )
        else:
            NoteInfo = ", ".join(
                (
                    f"{Length}x{Tally}"
                    for Length, Tally in sorted(Lengths.get(FullInfo, {}).items())
                )
            )
            ValueValue.append(
                {
                    "slot": KeyName,
                    "rule": "opaque",
                    "note": (
                        f"observed run lengths {NoteInfo}"
                        if NoteInfo
                        else "no traced instance resolves this run"
                    ),
                }
            )
            Stats["opaque_runs"] += 1
            Opaque += 1
    return RunsInfo, ValueValue, Opaque


# repeat metadata stays isolated because partial shapes need conservative prefix truncation
def AddRepeatMut(
    Entry: DictInfo[str, object],
    ValueValue: ListInfo[dict],
    Lengths: DictInfo[str, Collects.Counter],
    NameTextInfo: str,
    Observed: Collects.Counter,
    SeenInfo: ListInfo[int],
    Shape: dict | None,
) -> None:
    if Shape is not None:
        Tally = ", ".join(
            (f"{CountInfo}x{Times}" for CountInfo, Times in sorted(Observed.items()))
        )
        Entry["repeat_count"] = {
            "run": Shape["run"],
            "at": Shape["at"],
            "width": Shape["width"],
        }
        Entry["repeat_note"] = (
            f"child count varies across instances: {Tally}; the count sits in run {Shape['run']} at offset {Shape['at']} as a {Shape['width']} byte value and the repeated slot holds {Shape['name']}"
        )
        return
    Entry["repeat_count"] = None
    Entry["repeat_note"] = "child count varies across instances: " + ", ".join(
        (f"{CountInfo}x{Times}" for CountInfo, Times in sorted(Observed.items()))
    )
    if SeenInfo[0] <= 0:
        return
    Prefix = SeenInfo[0]
    Entry["repeat_prefix"] = Prefix
    KeptInfo = {KLeadRun} | {str(SlotIndex) for SlotIndex in range(Prefix - 1)}
    ValueValue[:] = [
        ItemData for ItemData in ValueValue if ItemData["slot"] in KeptInfo
    ]
    ObservedTail = ", ".join(
        (
            f"{Length}x{Tally}"
            for Length, Tally in sorted(
                Lengths.get(f"{NameTextInfo}@{Prefix - 1}", {}).items()
            )
        )
    )
    ValueValue.append(
        {
            "slot": KLoopTailRun,
            "rule": "opaque",
            "note": (
                f"every traced instance carries at least {Prefix} children, so the segmenter walks those {Prefix} slots with the runs solved above and refuses the run that follows the last of them; the run after slot {Prefix - 1} takes the lengths {ObservedTail} across the traced instances because that slot closes the shortest instances and continues the longer ones"
                if ObservedTail
                else f"every traced instance carries at least {Prefix} children, so the segmenter walks those {Prefix} slots and refuses the run that follows the last of them"
            ),
        }
    )


# needed to keep reverse engineering responsibilities isolated and maintainable
def BuildClasses(
    SolverInfo: SolveRuns.Solver, StreamsInfo: Mapping[str, bytes]
) -> Tuple[DictInfo[str, dict], DictInfo[str, int]]:
    Names = SlotNames(SolverInfo)
    Counts = ChildCounts(SolverInfo)
    Lengths = ObservedLengths(SolverInfo)
    StringTails, SlotShifts = RebalanceLeaves(SolverInfo, StreamsInfo)
    Classes: DictInfo[str, dict] = {}
    Stats = {"confirmed": 0, "partial": 0, "opaque_runs": 0}
    for NameTextInfo in sorted(Counts):
        Observed, SeenInfo, Slots, Varying, Shape, Needed = GetClassShape(
            Names, Counts, SolverInfo, StreamsInfo, NameTextInfo
        )
        RunsInfo, ValueValue, Opaque = CollectRunsMut(
            SolverInfo,
            Lengths,
            StringTails,
            SlotShifts,
            NameTextInfo,
            Needed,
            Shape,
            Stats,
        )
        Confidence = (
            "confirmed"
            if not Opaque and (not Varying or Shape is not None)
            else "partial"
        )
        Stats[Confidence] += 1
        Entry: DictInfo[str, object] = {
            "confidence": Confidence,
            "source": KSolvedSource,
            "child_slots": Slots,
            "instances": sum(Observed.values()),
            "child_counts": [
                [CountInfo, Times] for CountInfo, Times in sorted(Observed.items())
            ],
            "runs": {
                KeyName: RunsInfo[KeyName] for KeyName in Needed if KeyName in RunsInfo
            },
        }
        if Varying:
            AddRepeatMut(
                Entry, ValueValue, Lengths, NameTextInfo, Observed, SeenInfo, Shape
            )
        if ValueValue:
            Entry["variable_runs"] = ValueValue
        Classes[NameTextInfo] = Entry
    return (Classes, Stats)


# needed to keep reverse engineering responsibilities isolated and maintainable
def MergeAuthored(
    Classes: DictInfo[str, dict], PathInfoData: PathInfo, Source: str
) -> Tuple[DictInfo[str, dict], int]:
    if not PathInfoData.is_file():
        return (Classes, 0)
    PayloadInfo = JsonData.loads(PathInfoData.read_text(encoding="utf-8"))
    Incoming = PayloadInfo.get("classes")
    if not isinstance(Incoming, dict):
        raise ValueError(f"{PathInfoData} has no classes mapping")
    Merged = dict(Classes)
    for NameTextInfo, Entry in Incoming.items():
        if not isinstance(Entry, dict):
            raise ValueError(
                f"{PathInfoData} entry for {NameTextInfo} is not an object"
            )
        Combined = dict(Entry)
        Combined["source"] = Source
        Merged[NameTextInfo] = Combined
    return (Merged, len(Incoming))


# needed to keep reverse engineering responsibilities isolated and maintainable
def MergeDecompiled(
    Classes: DictInfo[str, dict], PathInfoData: PathInfo
) -> Tuple[DictInfo[str, dict], int]:
    return MergeAuthored(Classes, PathInfoData, KDecompiled)


# needed to keep reverse engineering responsibilities isolated and maintainable
def MergeVersioned(
    Classes: DictInfo[str, dict], PathInfoData: PathInfo
) -> Tuple[DictInfo[str, dict], int]:
    return MergeAuthored(Classes, PathInfoData, KVersioned)


# needed to keep reverse engineering responsibilities isolated and maintainable
def ExternLayout(SlotIndex: str, Record: Mapping[str, object]) -> dict:
    NameTextInfo = str(Record["class_name"])
    Bodies = [int(ValueInfo) for ValueInfo in Record["own_body_lengths"]]
    if len(Bodies) != 1:
        raise ValueError(
            f"external slot {SlotIndex} has {len(Bodies)} own body lengths; a pinned slot must have exactly one"
        )
    BodyInfo = Bodies[0]
    Entry: DictInfo[str, object] = {
        "confidence": str(Record["confidence"]),
        "source": KExternSource,
        "external_class": NameTextInfo,
        "instances": sum(
            (int(ValueInfo) for ValueInfo in Record["occurrences_per_trace"].values())
        ),
        "note": f"resolved to {NameTextInfo}; own body is {BodyInfo} bytes by {Record['decompiled_serialize']}. The traced spans {Record['traced_span_lengths']} are longer because bytes an ancestor reads after this object returns are absorbed into its row, so they belong to the ancestor run and not to this class.",
    }
    if SlotIndex == "component":
        Entry["child_slots"] = [KPolymorphic]
        Entry["runs"] = {KLeadRun: BodyInfo, "0": 0}
        return Entry
    if SlotIndex == "pmark_record":
        Entry["child_slots"] = []
        Entry["runs"] = {KLeafRun: BodyInfo}
        return Entry
    if SlotIndex == "object_list":
        Entry["child_slots"] = [KPolymorphic, KRepeatedSlot]
        Entry["runs"] = {KLeadRun: BodyInfo, "0": 0}
        Entry["repeat_count"] = {"run": KLeadRun, "at": 0, "width": 2}
        Entry["repeat_note"] = (
            "u16 element count in the lead run followed by that many nested objects"
        )
        return Entry
    raise ValueError(f"external slot {SlotIndex} has no pinned layout rule")


# needed to keep reverse engineering responsibilities isolated and maintainable
def MergeExtern(
    Classes: DictInfo[str, dict], PathInfoData: PathInfo
) -> Tuple[DictInfo[str, dict], int, DictInfo[str, ListInfo[str]]]:
    if not PathInfoData.is_file():
        return (Classes, 0, {})
    PayloadInfo = JsonData.loads(PathInfoData.read_text(encoding="utf-8"))
    Slots = PayloadInfo.get("slots")
    if not isinstance(Slots, dict):
        raise ValueError(f"{PathInfoData} has no slots mapping")
    Merged = dict(Classes)
    Bindings: DictInfo[str, ListInfo[str]] = {}
    Pinned = 0
    for SlotIndex in KPinnedSlots:
        Record = Slots.get(SlotIndex)
        if not isinstance(Record, dict):
            raise ValueError(f"{PathInfoData} has no {SlotIndex} slot")
        Entry = ExternLayout(SlotIndex, Record)
        Indices = sorted(
            {int(ValueInfo) for ValueInfo in Record["class_index_per_trace"].values()}
        )
        Aliases = [f"{KExternPrefix}{IndexData}" for IndexData in Indices]
        Bindings[str(Record["class_name"])] = Aliases
        for Alias in Aliases:
            Merged[Alias] = dict(Entry)
            Pinned += 1
        Merged[str(Record["class_name"])] = dict(Entry)
    return (Merged, Pinned, Bindings)


# needed to keep reverse engineering responsibilities isolated and maintainable
def SlotClassesInfo(
    SolverInfo: SolveRuns.Solver, Aliases: Mapping[str, str]
) -> DictInfo[Tuple[str, int], str]:
    Table: DictInfo[Tuple[str, int], set] = Collects.defaultdict(set)
    for LabelInfo, SegmentsInfo in SolverInfo.segments.items():
        KidsInfo = SolverInfo.kids[LabelInfo]
        for NodeInfoInfo, ItemData in enumerate(SegmentsInfo):
            if ItemData["kind"] in KNoBodyKinds:
                continue
            for SlotIndex, IsChild in enumerate(KidsInfo[NodeInfoInfo]):
                Entry = SegmentsInfo[IsChild]
                if Entry["kind"] in KNoBodyKinds:
                    continue
                Resolved = Aliases.get(str(Entry["class_name"]))
                if Resolved is not None:
                    Table[str(ItemData["class_name"]), SlotIndex].add(Resolved)
    return {
        KeyName: next(iter(ValueInfo))
        for KeyName, ValueInfo in Table.items()
        if len(ValueInfo) == 1
    }


# needed to keep reverse engineering responsibilities isolated and maintainable
def BindExternSlots(
    Classes: DictInfo[str, dict],
    Table: Mapping[Tuple[str, int], str],
    Aliases: Mapping[str, str],
) -> Tuple[DictInfo[str, dict], ListInfo[dict]]:
    Merged = dict(Classes)
    Bound: ListInfo[dict] = []
    for (Parent, SlotIndex), Resolved in sorted(Table.items()):
        Entry = Merged.get(Parent)
        if Entry is None or Resolved not in Merged:
            continue
        Slots = list(Entry.get("child_slots", ()))
        if SlotIndex >= len(Slots):
            continue
        if KRepeatedSlot in Slots and SlotIndex >= len(Slots) - 2:
            continue
        Current = str(Slots[SlotIndex])
        if Current == Resolved:
            continue
        if Current != KPolymorphic and Current not in Aliases:
            continue
        Slots[SlotIndex] = Resolved
        Updated = dict(Entry)
        Updated["child_slots"] = Slots
        Merged[Parent] = Updated
        Bound.append(
            {"class": Parent, "slot": SlotIndex, "was": Current, "now": Resolved}
        )
    return (Merged, Bound)


# needed to keep reverse engineering responsibilities isolated and maintainable
def TracedStreams(Traces: Sequence[Mapping[str, object]]) -> DictInfo[str, bytes]:
    System.path.insert(0, str(KRootInfo / "src"))
    from convert.adapters.solidworks.container.Container import SldprtArchive
    from convert.adapters.solidworks.container.Format import (
        RESOLVED_FEATURES_STREAM as ResolvedStream,
    )

    StreamsInfo: DictInfo[str, bytes] = {}
    for TraceInfo in Traces:
        PartInfoInfo = PathInfo(str(TraceInfo["part"]))
        if not PartInfoInfo.is_file():
            continue
        ByteBlob = SldprtArchive.from_bytes(PartInfoInfo.read_bytes()).streams[
            ResolvedStream
        ]
        if len(ByteBlob) != int(TraceInfo["stream_length"]):
            continue
        StreamsInfo[str(TraceInfo["label"])] = ByteBlob
    return StreamsInfo


# needed to keep reverse engineering responsibilities isolated and maintainable
def Generate(
    SegmentsDir: PathInfo,
    Decompiled: PathInfo,
    Extern: PathInfo,
    Versioned: PathInfo,
    Labels: str,
) -> dict:
    Traces = SolveRuns.LoadTraces(str(SegmentsDir), Labels)
    if not Traces:
        raise ValueError(f"no segmentations found under {SegmentsDir}")
    SolverInfo = TilingSolver(Traces)
    SolverInfo.solve()
    StreamsInfo = TracedStreams(Traces)
    Classes, Stats = BuildClasses(SolverInfo, StreamsInfo)
    Classes, DecompiledCount = MergeDecompiled(Classes, Decompiled)
    Classes, VersionedCount = MergeVersioned(Classes, Versioned)
    Classes, ExternCount, ExternBindings = MergeExtern(Classes, Extern)
    Aliases = {
        Alias: NameTextInfo
        for NameTextInfo, Group in ExternBindings.items()
        for Alias in Group
    }
    Classes, BoundSlots = BindExternSlots(
        Classes, SlotClassesInfo(SolverInfo, Aliases), Aliases
    )
    Gated = sorted(
        (
            NameTextInfo
            for NameTextInfo, Entry in Classes.items()
            if "runs_by_version" in Entry
        )
    )
    Grouped = sorted(
        (NameTextInfo for NameTextInfo, Entry in Classes.items() if Entry.get("groups"))
    )
    for NameTextInfo in Grouped:
        Entry = Classes[NameTextInfo]
        if Entry.get("child_slots") or Entry.get("repeat_prefix"):
            raise ValueError(
                f"{NameTextInfo} carries run groups and slot based children; a grouped class drives its whole child list from the groups"
            )
        if KLeadRun not in Entry.get("runs", {}):
            raise ValueError(f"{NameTextInfo} carries run groups but no lead run")
        for Group in Entry["groups"]:
            if len(Group.get("slots", ())) != len(Group.get("element", ())):
                raise ValueError(
                    f"run group {NameTextInfo}@{Group.get('name')} names {len(Group.get('slots', ()))} slots for {len(Group.get('element', ()))} element runs"
                )
    return {
        "external_classes": ExternCount,
        "external_bindings": ExternBindings,
        "external_slot_bindings": BoundSlots,
        "external_slot_binding_contract": "a child slot whose traced occupant is one of the resolved external classes carries that class name rather than the document specific external#<index> alias, so the segmenter binds an unknown below base class index from the class the parent Serialize is recorded to read at that position instead of from the index; a slot is only bound when every traced occupant of it resolves to the same class, and a slot at or past a repeated template is left alone because rewriting it would move the template",
        "streams_read_for_string_rules": sorted(StreamsInfo),
        "version": 1,
        "source": " + ".join(
            [KSolvedSource]
            + ([KDecompiled] if DecompiledCount else [])
            + ([KVersioned] if VersionedCount else [])
            + ([KExternSource] if ExternCount else [])
        ),
        "traces": [str(TraceInfo["label"]) for TraceInfo in Traces],
        "run_keys": len(SolverInfo.runs),
        "conflicting_run_keys": sorted(SolverInfo.variable),
        "run_derivation": "solve_runs.Solver seeded with the exact record end of every traced object, taken from the contiguous preorder subtree of the recorded segmentation; a run is constant only when every traced instance agrees",
        "repeat_count_contract": "a trailing ... entry in child_slots means the child count is not constant across the traced instances; repeat_count is null because no field holding the count has been recovered, and the static segmenter never guesses the count. repeat_prefix carries the smallest child count any traced instance of the class holds, which is the number of leading child slots every instance is known to fill; the segmenter walks exactly that prefix with the runs solved for those slots and then refuses the tail run, so an unresolved child count costs the objects past the prefix instead of the whole class",
        "grouped_classes": Grouped,
        "group_contract": "a class whose body is a chain of counted loops rather than a fixed slot list carries groups instead of child_slots: each group reads a count of count.width bytes sitting count.back bytes ahead of its own first element, walks that many copies of element with one run per element child, and then consumes trailer bytes whether or not the count was zero, so the trailers of empty groups accumulate into the run that follows the last child actually read; repeat replaces the count for a group whose children are unconditional, and element_by_version overrides element per document version exactly as runs_by_version overrides runs",
        "class_count": len(Classes),
        "confirmed_classes": Stats["confirmed"],
        "partial_classes": Stats["partial"],
        "opaque_runs": Stats["opaque_runs"],
        "decompiled_classes": DecompiledCount,
        "versioned_classes": VersionedCount,
        "version_gated_classes": Gated,
        "version_gate_contract": "runs_by_version maps a run key to a mapping from document version to run length; the segmenter consults it before runs, falls back to runs when the version is unknown or absent from the mapping, and refuses the class when neither names the run",
        "classes": dict(sorted(Classes.items())),
    }


# needed to keep reverse engineering responsibilities isolated and maintainable
def MainRun() -> int:
    ParserInfo = Argparse.ArgumentParser()
    ParserInfo.add_argument("--segments", default=str(KDefaultValue))
    ParserInfo.add_argument("--decompiled", default=str(KDefaultInfo))
    ParserInfo.add_argument("--external", default=str(KDefaultExtern))
    ParserInfo.add_argument("--versioned", default=str(KDefaultEntry))
    ParserInfo.add_argument("--labels", default="")
    ParserInfo.add_argument("--out", default=str(KDefaultOut))
    ArgsInfo = ParserInfo.parse_args()
    PayloadInfo = Generate(
        PathInfo(ArgsInfo.segments),
        PathInfo(ArgsInfo.decompiled),
        PathInfo(ArgsInfo.external),
        PathInfo(ArgsInfo.versioned),
        ArgsInfo.labels,
    )
    Destination = PathInfo(ArgsInfo.out)
    Destination.parent.mkdir(parents=True, exist_ok=True)
    with Destination.open("w", encoding="utf-8") as Handle:
        JsonData.dump(PayloadInfo, Handle, indent=1)
        Handle.write("\n")
    print(
        "classes=%d confirmed=%d partial=%d opaque_runs=%d decompiled=%d versioned=%d version_gated=%d external=%d"
        % (
            PayloadInfo["class_count"],
            PayloadInfo["confirmed_classes"],
            PayloadInfo["partial_classes"],
            PayloadInfo["opaque_runs"],
            PayloadInfo["decompiled_classes"],
            PayloadInfo["versioned_classes"],
            len(PayloadInfo["version_gated_classes"]),
            PayloadInfo["external_classes"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(MainRun())
