# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations
import argparse as Argparse
from fractions import Fraction
import glob as GlobInfo
import json as JsonData
import os as OsLayer
from typing import Dict as DictInfo, List as ListInfo, Sequence, Tuple

# needed to keep reverse engineering responsibilities isolated and maintainable
KNoBodyKinds = ("null", "objectref")


# needed to keep reverse engineering responsibilities isolated and maintainable
def LoadTraces(SegmentsDir: str) -> ListInfo[dict]:
    Traces = []
    for PathInfoData in sorted(
        GlobInfo.glob(OsLayer.path.join(SegmentsDir, "segments_*.json"))
    ):
        with open(PathInfoData, encoding="utf-8") as TraceHandle:
            Traces.append(JsonData.load(TraceHandle))
    return Traces


# needed to keep reverse engineering responsibilities isolated and maintainable
def BuildTree(
    SegmentsInfo: Sequence[dict],
) -> Tuple[ListInfo[ListInfo[int]], ListInfo[int]]:
    Children: ListInfo[ListInfo[int]] = [
        list(range(IndexInfo, IndexInfo)) for IndexInfo in range(len(SegmentsInfo))
    ]
    for IndexInfo, SegInfo in enumerate(SegmentsInfo):
        Parent = SegInfo["parent"]
        if Parent >= 0:
            Children[Parent].append(IndexInfo)
    SubtreeOrder: ListInfo[int] = []
    for IndexInfo in range(len(SegmentsInfo) - 1, -1, -1):
        SubtreeOrder.append(IndexInfo)
    return (Children, SubtreeOrder)


# needed to keep reverse engineering responsibilities isolated and maintainable
def SubtreeStats(
    SegmentsInfo: Sequence[dict], Children: Sequence[Sequence[int]]
) -> Tuple[ListInfo[DictInfo[str, int]], ListInfo[int]]:
    Counts: ListInfo[DictInfo[str, int]] = [dict()] * len(SegmentsInfo)
    Headers: ListInfo[int] = [0] * len(SegmentsInfo)
    for IndexInfo in range(len(SegmentsInfo) - 1, -1, -1):
        SegInfo = SegmentsInfo[IndexInfo]
        AccInfo: DictInfo[str, int] = {}
        HdrInfo = 0
        if SegInfo["kind"] not in KNoBodyKinds:
            AccInfo[SegInfo["class_name"]] = 1
        for ThirdValue in Children[IndexInfo]:
            HdrInfo += SegmentsInfo[ThirdValue]["header"] + Headers[ThirdValue]
            for KeyName, ValueInfo in Counts[ThirdValue].items():
                AccInfo[KeyName] = AccInfo.get(KeyName, 0) + ValueInfo
        Counts[IndexInfo] = AccInfo
        Headers[IndexInfo] = HdrInfo
    return (Counts, Headers)


# needed to keep reverse engineering responsibilities isolated and maintainable
def TailChain(
    SegmentsInfo: Sequence[dict], Children: Sequence[Sequence[int]], IndexData: int
) -> Tuple[DictInfo[str, int], bool]:
    Chain: DictInfo[str, int] = {}
    Cursor = IndexData
    while True:
        SegInfo = SegmentsInfo[Cursor]
        Parent = SegInfo["parent"]
        if Parent < 0:
            return (Chain, True)
        Siblings = Children[Parent]
        if Siblings[-1] != Cursor:
            return (Chain, False)
        NameTextInfo = SegmentsInfo[Parent]["class_name"]
        if SegmentsInfo[Parent]["kind"] in KNoBodyKinds:
            return (Chain, False)
        Chain[NameTextInfo] = Chain.get(NameTextInfo, 0) + 1
        Cursor = Parent


# needed to keep reverse engineering responsibilities isolated and maintainable
def BuildEquations(Traces: Sequence[dict]) -> Tuple[ListInfo[dict], ListInfo[str]]:
    Equations: ListInfo[dict] = []
    ValuesInfo: DictInfo[str, None] = {}
    for TraceInfo in Traces:
        SegmentsInfo = TraceInfo["segments"]
        Children = BuildTree(SegmentsInfo)[0]
        Counts, Headers = SubtreeStats(SegmentsInfo, Children)
        for IndexInfo, SegInfo in enumerate(SegmentsInfo):
            if SegInfo["kind"] in KNoBodyKinds:
                continue
            Chain, Usable = TailChain(SegmentsInfo, Children, IndexInfo)
            if not Usable:
                continue
            RowDataInfo: DictInfo[str, int] = {}
            for KeyName, ValueInfo in Counts[IndexInfo].items():
                RowDataInfo["S:" + KeyName] = (
                    RowDataInfo.get("S:" + KeyName, 0) + ValueInfo
                )
            for KeyName, ValueInfo in Chain.items():
                RowDataInfo["T:" + KeyName] = (
                    RowDataInfo.get("T:" + KeyName, 0) + ValueInfo
                )
            SpanInfo = SegInfo["scope_end"] - SegInfo["offset"] - SegInfo["header"]
            RhsInfo = SpanInfo - Headers[IndexInfo]
            for KeyName in RowDataInfo:
                ValuesInfo[KeyName] = None
            Equations.append(
                {
                    "label": TraceInfo["label"],
                    "node": IndexInfo,
                    "class_name": SegInfo["class_name"],
                    "row": RowDataInfo,
                    "rhs": RhsInfo,
                    "span": SpanInfo,
                    "depth": SegInfo["depth"],
                }
            )
    return (Equations, sorted(ValuesInfo))


# needed to keep reverse engineering responsibilities isolated and maintainable
def RrefInfoMut(
    GetRows: ListInfo[ListInfo[Fraction]], WidthInfo: int
) -> Tuple[ListInfo[ListInfo[Fraction]], ListInfo[int], bool]:
    Pivots: ListInfo[int] = []
    ResultData = 0
    for ThirdValue in range(WidthInfo):
        PickInfo = -1
        for KeyIndex in range(ResultData, len(GetRows)):
            if GetRows[KeyIndex][ThirdValue] != 0:
                PickInfo = KeyIndex
                break
        if PickInfo < 0:
            continue
        GetRows[ResultData], GetRows[PickInfo] = (
            GetRows[PickInfo],
            GetRows[ResultData],
        )
        LeadInfo = GetRows[ResultData][ThirdValue]
        GetRows[ResultData] = [
            ValueInfo / LeadInfo for ValueInfo in GetRows[ResultData]
        ]
        for KeyIndex in range(len(GetRows)):
            if KeyIndex != ResultData and GetRows[KeyIndex][ThirdValue] != 0:
                Factor = GetRows[KeyIndex][ThirdValue]
                GetRows[KeyIndex] = [
                    FirstValue - Factor * SecondValue
                    for FirstValue, SecondValue in zip(
                        GetRows[KeyIndex], GetRows[ResultData]
                    )
                ]
        Pivots.append(ThirdValue)
        ResultData += 1
        if ResultData == len(GetRows):
            break
    Consistent = True
    for KeyIndex in range(ResultData, len(GetRows)):
        if (
            all((ValueInfo == 0 for ValueInfo in GetRows[KeyIndex][:WidthInfo]))
            and GetRows[KeyIndex][WidthInfo] != 0
        ):
            Consistent = False
    return (GetRows, Pivots, Consistent)


# needed to keep reverse engineering responsibilities isolated and maintainable
def Solve(Equations: Sequence[dict], ValuesInfo: Sequence[str]) -> dict:
    IndexData = {
        NameTextInfo: IndexInfo for IndexInfo, NameTextInfo in enumerate(ValuesInfo)
    }
    WidthInfo = len(ValuesInfo)
    GetRows: ListInfo[ListInfo[Fraction]] = []
    for EqInfo in Equations:
        RowDataInfo = [Fraction(0)] * (WidthInfo + 1)
        for KeyName, ValueInfo in EqInfo["row"].items():
            RowDataInfo[IndexData[KeyName]] = Fraction(ValueInfo)
        RowDataInfo[WidthInfo] = Fraction(EqInfo["rhs"])
        GetRows.append(RowDataInfo)
    Reduced, Pivots, Consistent = RrefInfoMut(GetRows, WidthInfo)
    FreeInfo = [
        ThirdValue for ThirdValue in range(WidthInfo) if ThirdValue not in set(Pivots)
    ]
    Freeset = set(FreeInfo)
    Determined: DictInfo[str, int] = {}
    for ResultData, ThirdValue in enumerate(Pivots):
        if all((Reduced[ResultData][FileData] == 0 for FileData in Freeset)):
            ValueInfo = Reduced[ResultData][WidthInfo]
            Determined[ValuesInfo[ThirdValue]] = ValueInfo
    return {
        "consistent": Consistent,
        "rank": len(Pivots),
        "variables": len(ValuesInfo),
        "determined": Determined,
        "free": [ValuesInfo[FileData] for FileData in FreeInfo],
    }


# needed to keep reverse engineering responsibilities isolated and maintainable
def ResidualCheck(
    Equations: Sequence[dict], Determined: DictInfo[str, Fraction]
) -> ListInfo[dict]:
    Failures: ListInfo[dict] = []
    for EqInfo in Equations:
        Total = Fraction(0)
        Complete = True
        for KeyName, ValueInfo in EqInfo["row"].items():
            if KeyName in Determined:
                Total += Determined[KeyName] * ValueInfo
            else:
                Complete = False
                break
        if not Complete:
            continue
        if Total != Fraction(EqInfo["rhs"]):
            Failures.append(
                {
                    "label": EqInfo["label"],
                    "node": EqInfo["node"],
                    "class_name": EqInfo["class_name"],
                    "predicted": str(Total),
                    "observed": EqInfo["rhs"],
                }
            )
    return Failures


# needed to keep reverse engineering responsibilities isolated and maintainable
def MainRun() -> int:
    ParserInfo = Argparse.ArgumentParser()
    ParserInfo.add_argument("--segments", default="re/data/segments")
    ParserInfo.add_argument("--out", default="re/data/body_scalars.json")
    ParserInfo.add_argument("--labels", default="")
    ArgValues = ParserInfo.parse_args()
    Traces = LoadTraces(ArgValues.segments)
    if ArgValues.labels:
        Wanted = set(ArgValues.labels.split(","))
        Traces = [TextData for TextData in Traces if TextData["label"] in Wanted]
    Equations, ValuesInfo = BuildEquations(Traces)
    Result = Solve(Equations, ValuesInfo)
    Determined = Result["determined"]
    Failures = ResidualCheck(Equations, Determined)
    PayloadInfo = {
        "traces": [TextData["label"] for TextData in Traces],
        "equations": len(Equations),
        "variables": Result["variables"],
        "rank": Result["rank"],
        "consistent": Result["consistent"],
        "determined": {
            KeyName: int(ValueInfo) if ValueInfo.denominator == 1 else str(ValueInfo)
            for KeyName, ValueInfo in sorted(Determined.items())
        },
        "free": Result["free"],
        "residual_failures": Failures,
    }
    with open(ArgValues.out, "w", encoding="utf-8") as Handle:
        JsonData.dump(PayloadInfo, Handle, indent=1)
        Handle.write("\n")
    print(
        f"equations={len(Equations)} variables={Result['variables']} rank={Result['rank']} consistent={Result['consistent']} determined={len(Determined)} residual_failures={len(Failures)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(MainRun())
