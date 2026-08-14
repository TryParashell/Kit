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
KScratch = KHereInfo.parents[2] / '.rescratch'

# needed to keep reverse engineering responsibilities isolated and maintainable
KGrammar = KHereInfo.parent / 'harness'
for CandInfo in (KHereInfo, KGrammar):
    if str(CandInfo) not in System.path:
        System.path.insert(0, str(CandInfo))
import Cdbdrive as Cdbdrive
import Segment as Segmentlib
import Tracelog as Tracelog
import Carchive as Carchive
import Streamlib as Streamlib

# needed to keep reverse engineering responsibilities isolated and maintainable
KOutInfo = KScratch / 'trace' / 'out'

# needed to keep reverse engineering responsibilities isolated and maintainable
KScript = '$$ SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0\n$$ SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin\n$$\n$$ This SPDX license identifier and copyright notice must not be\n$$ removed, altered, or obscured. Doing so is a material breach of\n$$ the PolyForm Strict License 1.0.0 and voids all licenses granted\n$$ to you under it immediately and permanently.\n.symopt+0x4000\n.symopt-0x20000\n.exepath+ {solidworks}\n.reload /f swccu.dll\nbp swccu!su_CArchive::ReadObject ".if ((poi(@rcx+{max:#x})-poi(@rcx+{start:#x}))=={span:#x}) {{ .printf \\"RO %p %x %d %p\\\\n\\", poi(@rcx+{start:#x}), poi(@rcx+{cur:#x})-poi(@rcx+{start:#x}), dwo(@rcx+{map:#x}), @rsp }}; gc"\nbp swccu!su_CArchive::ReadClass ".if ((poi(@rcx+{max:#x})-poi(@rcx+{start:#x}))=={span:#x}) {{ .printf \\"RC %p %x %d %p\\\\n\\", poi(@rcx+{start:#x}), poi(@rcx+{cur:#x})-poi(@rcx+{start:#x}), dwo(@rcx+{map:#x}), @rsp }}; gc"\nbl\ng\n'


# needed to keep reverse engineering responsibilities isolated and maintainable
def Layout() -> dict[str, int]:
    PathInfoData = KOutInfo / 'Calibrate.json'
    if not PathInfoData.is_file():
        raise SystemExit(f'run Calibrate.py first: {PathInfoData} is missing')
    return JsonData.loads(PathInfoData.read_text(encoding='utf-8'))['layout']


# needed to keep reverse engineering responsibilities isolated and maintainable
def WriteScript(PathInfoData: PathInfo, SpanInfo: int, Fields: dict[str, int]) -> None:
    PathInfoData.write_text(KScript.format(solidworks=Cdbdrive.KSolidworksDir, span=SpanInfo, cur=Fields['cur'], max=Fields['max'], start=Fields['start'], map=Fields['map']), encoding='ascii')


# needed to keep reverse engineering responsibilities isolated and maintainable
def CrossCheck(ByteBlob: bytes, SegmentsInfo: tuple[Segmentlib.Segment, ...]) -> dict[str, object]:
    Defns = Carchive.ClassDefns(ByteBlob)
    Static = [ItemData.tag_offset for ItemData in Defns]
    Traced = {ItemData.offset for ItemData in SegmentsInfo if ItemData.kind == 'definition'}
    MissingInfo = [Offset for Offset in Static if Offset not in Traced]
    Extra = sorted(Traced - set(Static))
    return {'static_definitions': len(Static), 'traced_definitions': len(Traced), 'static_offsets_head': Static[:8], 'missing_from_trace': MissingInfo, 'traced_not_scanned': Extra, 'agree': not MissingInfo and (not Extra)}


# needed to keep reverse engineering responsibilities isolated and maintainable
def TraceOne(LabelInfo: str, PartInfoInfo: PathInfo, Fields: dict[str, int], ModeInfo: str) -> dict[str, object]:
    ByteBlob = Streamlib.LoadDonor(PartInfoInfo).resolved
    SpanInfo = len(ByteBlob)
    Script = KHereInfo / f'cdb_trace_{LabelInfo}.txt'
    LogInfo = KOutInfo / f'cdb_trace_{LabelInfo}.log'
    WriteScript(Script, SpanInfo, Fields)
    Record: dict[str, object] = {'label': LabelInfo, 'part': str(PartInfoInfo), 'stream_length': SpanInfo, 'script': str(Script), 'log': str(LogInfo)}
    if ModeInfo == 'run':
        Result = Cdbdrive.RunTask(Script, LogInfo, PartInfoInfo, Marker='^RO ', HardDeadline=600.0, QuietSeconds=45.0)
        Record['cdb_reason'] = Result.reason
        Record['cdb_seconds'] = round(Result.seconds, 1)
        Record['read_object_events'] = Result.markers
    if not LogInfo.is_file():
        Record['status'] = 'no-log'
        return Record
    Events = Tracelog.ReadEvents(LogInfo)
    if not any((EventInfo.kind == 'RO' for EventInfo in Events)):
        Record['status'] = 'no-events'
        return Record
    SegmentsInfo = Segmentlib.Build(ByteBlob, Events)
    Shape = Segmentlib.Tiling(ByteBlob, SegmentsInfo)
    Mismatch = Segmentlib.CounterData(SegmentsInfo)
    Record.update({'status': 'traced', 'objects': len(SegmentsInfo), 'definitions': sum((1 for ItemData in SegmentsInfo if ItemData.kind == 'definition')), 'base_map_index': SegmentsInfo[0].map_index, 'tiles': Shape['tiles'], 'header_bytes': Shape['header_bytes'], 'trailing_bytes': Shape['trailing_bytes'], 'counter_mismatches': len(Mismatch), 'increment_rule': Segmentlib.IncrementRule(SegmentsInfo), 'cross_check': CrossCheck(ByteBlob, SegmentsInfo)})
    Segmentlib.Report(LabelInfo, PartInfoInfo, LogInfo)
    return Record


# needed to keep reverse engineering responsibilities isolated and maintainable
def MainRun() -> int:
    ArgsInfo = System.argv[1:]
    if not ArgsInfo:
        raise SystemExit('usage: Runtrace.py <mode> <label> <part> [<label> <part> ...]')
    ModeInfo = ArgsInfo[0]
    Pairs = ArgsInfo[1:]
    if len(Pairs) % 2:
        raise SystemExit('labels and parts must come in pairs')
    Fields = Layout()
    KOutInfo.mkdir(parents=True, exist_ok=True)
    RecordsInfo: list[dict[str, object]] = []
    for PosInfoInfo in range(0, len(Pairs), 2):
        LabelInfo = Pairs[PosInfoInfo]
        PartInfoInfo = PathInfo(Pairs[PosInfoInfo + 1]).resolve()
        Record = TraceOne(LabelInfo, PartInfoInfo, Fields, ModeInfo)
        RecordsInfo.append(Record)
        print(f"{LabelInfo:22s} {Record.get('status')} objects={Record.get('objects')} tiles={Record.get('tiles')} mismatches={Record.get('counter_mismatches')} agree={(Record.get('cross_check') or {}).get('agree')}", flush=True)
        (KOutInfo / 'Runtrace.json').write_text(JsonData.dumps(RecordsInfo, indent=2), encoding='utf-8')
    return 0
if __name__ == '__main__':
    raise SystemExit(MainRun())
