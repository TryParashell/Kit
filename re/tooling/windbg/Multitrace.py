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
import Cdbdrive as Cdbdrive
import Model as Modellib
import Segment as Segmentlib
import Tracelog as Tracelog
import Streamlib as Streamlib
from convert.Security.PathBoundary import ResolveInput, ValidateLabel

# needed to keep reverse engineering responsibilities isolated and maintainable
KOutInfo = KScratch / "trace" / "out"

# needed to keep reverse engineering responsibilities isolated and maintainable
KResolved = Streamlib.KResolved

# needed to keep reverse engineering responsibilities isolated and maintainable
KCmgrInfo = "Contents/CMgr"

# needed to keep reverse engineering responsibilities isolated and maintainable
KModelHeader = "Contents/Config-0-ModelHeader"

# needed to keep reverse engineering responsibilities isolated and maintainable
KHeaderTwo = "Header2"

# needed to keep reverse engineering responsibilities isolated and maintainable
KConfigZero = "Contents/Config-0"

# needed to keep reverse engineering responsibilities isolated and maintainable
KVisualStates = "ThirdPtyStore/VisualStates"

# needed to keep reverse engineering responsibilities isolated and maintainable
KStreams = (KResolved, KCmgrInfo, KModelHeader, KConfigZero, KVisualStates)

# needed to keep reverse engineering responsibilities isolated and maintainable
KPreamble = "$$ SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0\n$$ SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin\n$$\n$$ This SPDX license identifier and copyright notice must not be\n$$ removed, altered, or obscured. Doing so is a material breach of\n$$ the PolyForm Strict License 1.0.0 and voids all licenses granted\n$$ to you under it immediately and permanently.\n.symopt+0x4000\n.symopt-0x20000\n.exepath+ {solidworks}\n.reload /f swccu.dll\n"

# needed to keep reverse engineering responsibilities isolated and maintainable
KBreakpoint = 'bp swccu!su_CArchive::{routine} ".if ({guard}) {{ .printf \\"{tag} %p %x %d %p %x\\\\n\\", poi(@rcx+{start:#x}), poi(@rcx+{cur:#x})-poi(@rcx+{start:#x}), dwo(@rcx+{map:#x}), @rsp, poi(@rcx+{max:#x})-poi(@rcx+{start:#x}) }}; gc"\n'


# needed to keep reverse engineering responsibilities isolated and maintainable
def Layout() -> dict[str, int]:
    PathInfoData = KOutInfo / "Calibrate.json"
    if not PathInfoData.is_file():
        raise SystemExit(f"run Calibrate.py first: {PathInfoData} is missing")
    return JsonData.loads(PathInfoData.read_text(encoding="utf-8"))["layout"]


# needed to keep reverse engineering responsibilities isolated and maintainable
def Guard(Spans: tuple[int, ...], Fields: dict[str, int]) -> str:
    SpanInfo = f"(poi(@rcx+{Fields['max']:#x})-poi(@rcx+{Fields['start']:#x}))"
    return " | ".join(
        (f"({SpanInfo}=={ValueInfo:#x})" for ValueInfo in sorted(set(Spans)))
    )


# needed to keep reverse engineering responsibilities isolated and maintainable
def WriteScript(
    PathInfoData: PathInfo, Spans: tuple[int, ...], Fields: dict[str, int]
) -> None:
    TextValueData = KPreamble.format(solidworks=Cdbdrive.KSolidworksDir)
    Condition = Guard(Spans, Fields)
    for Routine, TagInfoInfo in (("ReadObject", "RO"), ("ReadClass", "RC")):
        TextValueData += KBreakpoint.format(
            routine=Routine,
            tag=TagInfoInfo,
            guard=Condition,
            start=Fields["start"],
            cur=Fields["cur"],
            max=Fields["max"],
            map=Fields["map"],
        )
    TextValueData += "bl\ng\n"
    PathInfoData.write_text(TextValueData, encoding="ascii")


# needed to keep reverse engineering responsibilities isolated and maintainable
def Analyse(
    PartInfoInfo: PathInfo, LogInfo: PathInfo, StreamsInfo: tuple[str, ...]
) -> list[dict[str, object]]:
    DonorInfo = Streamlib.LoadDonor(PartInfoInfo)
    Events = Tracelog.ReadEvents(LogInfo)
    GetRows: list[dict[str, object]] = []
    for NameTextInfo in StreamsInfo:
        ByteBlob = DonorInfo.streams.get(NameTextInfo)
        if ByteBlob is None:
            GetRows.append({"stream": NameTextInfo, "status": "absent"})
            continue
        Counts = Tracelog.BuffersForSpan(Events, len(ByteBlob))
        if not Counts:
            GetRows.append(
                {
                    "stream": NameTextInfo,
                    "status": "no-events",
                    "stream_length": len(ByteBlob),
                }
            )
            continue
        SegmentsInfo = Segmentlib.Build(ByteBlob, Events, SpanInfo=len(ByteBlob))
        Shape = Segmentlib.Tiling(ByteBlob, SegmentsInfo)
        Mismatch = Segmentlib.CounterData(SegmentsInfo)
        RowDataInfo: dict[str, object] = {
            "stream": NameTextInfo,
            "status": "traced",
            "stream_length": len(ByteBlob),
            "buffers": len(Counts),
            "objects": len(SegmentsInfo),
            "definitions": sum(
                (1 for ItemData in SegmentsInfo if ItemData.kind == "definition")
            ),
            "base_map_index": SegmentsInfo[0].map_index,
            "tiles": Shape["tiles"],
            "header_bytes": Shape["header_bytes"],
            "trailing_bytes": Shape["trailing_bytes"],
            "gaps": Shape["gaps"],
            "overlaps": Shape["overlaps"],
            "counter_mismatches": len(Mismatch),
            "increment_rule": Segmentlib.IncrementRule(SegmentsInfo),
        }
        try:
            Reparsed = Modellib.Parse(ByteBlob, SegmentsInfo)
            RowDataInfo["reemit_identical"] = Reparsed.emit() == ByteBlob
            RowDataInfo["external_classrefs"] = sum(
                (
                    1
                    for NodeInfoInfo in Reparsed.nodes
                    if NodeInfoInfo.kind == "classref" and NodeInfoInfo.target < 0
                )
            )
            RowDataInfo["external_objectrefs"] = sum(
                (
                    1
                    for NodeInfoInfo in Reparsed.nodes
                    if NodeInfoInfo.kind == "objectref" and NodeInfoInfo.target < 0
                )
            )
        except Modellib.ModelError as Error:
            RowDataInfo["reemit_identical"] = False
            RowDataInfo["model_error"] = str(Error)
        GetRows.append(RowDataInfo)
    return GetRows


# needed to keep reverse engineering responsibilities isolated and maintainable
def TraceOne(
    LabelInfo: str,
    PartInfoInfo: PathInfo,
    Fields: dict[str, int],
    ModeInfo: str,
    StreamsInfo: tuple[str, ...],
) -> dict[str, object]:
    DonorInfo = Streamlib.LoadDonor(PartInfoInfo)
    Spans = tuple(
        (
            len(DonorInfo.streams[NameTextInfo])
            for NameTextInfo in StreamsInfo
            if NameTextInfo in DonorInfo.streams
        )
    )
    Script = KHereInfo / f"cdb_multi_{LabelInfo}.txt"
    LogInfo = KOutInfo / f"cdb_multi_{LabelInfo}.log"
    WriteScript(Script, Spans, Fields)
    Record: dict[str, object] = {
        "label": LabelInfo,
        "part": str(PartInfoInfo),
        "spans": list(Spans),
        "script": str(Script),
        "log": str(LogInfo),
    }
    if ModeInfo == "run":
        Result = Cdbdrive.RunTask(
            Script,
            LogInfo,
            PartInfoInfo,
            Marker="^RO ",
            HardDeadline=900.0,
            QuietSeconds=60.0,
        )
        Record["cdb_reason"] = Result.reason
        Record["cdb_seconds"] = round(Result.seconds, 1)
        Record["read_object_events"] = Result.markers
    if not LogInfo.is_file():
        Record["status"] = "no-log"
        return Record
    Record["status"] = "traced"
    Record["streams"] = Analyse(PartInfoInfo, LogInfo, StreamsInfo)
    return Record


# needed to keep reverse engineering responsibilities isolated and maintainable
def MainRun() -> int:
    ArgsInfo = System.argv[1:]
    if len(ArgsInfo) < 3:
        raise SystemExit("usage: Multitrace.py <mode> <label> <part> [<label> <part>]")
    ModeInfo = ArgsInfo[0]
    Pairs = ArgsInfo[1:]
    if len(Pairs) % 2:
        raise SystemExit("labels and parts must come in pairs")
    Fields = Layout()
    KOutInfo.mkdir(parents=True, exist_ok=True)
    RecordsInfo: list[dict[str, object]] = []
    for PosInfoInfo in range(0, len(Pairs), 2):
        LabelInfo = ValidateLabel(Pairs[PosInfoInfo])
        PartInfoInfo = ResolveInput(Pairs[PosInfoInfo + 1])
        Record = TraceOne(LabelInfo, PartInfoInfo, Fields, ModeInfo, KStreams)
        RecordsInfo.append(Record)
        print(f"== {LabelInfo} {Record.get('status')} {Record.get('cdb_reason')}")
        for RowDataInfo in Record.get("streams") or []:
            print(
                f"   {str(RowDataInfo['stream']):38s} {str(RowDataInfo['status']):10s} len={RowDataInfo.get('stream_length')} objects={RowDataInfo.get('objects')} tiles={RowDataInfo.get('tiles')} mism={RowDataInfo.get('counter_mismatches')} reemit={RowDataInfo.get('reemit_identical')}",
                flush=True,
            )
        (KOutInfo / "Multitrace.json").write_text(
            JsonData.dumps(RecordsInfo, indent=2), encoding="utf-8"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(MainRun())
