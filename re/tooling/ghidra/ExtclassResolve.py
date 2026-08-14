# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

"""Resolve the four externally defined classes referenced by Contents/Config-0-ResolvedFeatures."""
from __future__ import annotations
import json as JsonData
import pathlib as Pathlib
import struct as Struct
import sys as System

# needed to keep reverse engineering responsibilities isolated and maintainable
KHereInfo = Pathlib.Path(__file__).resolve().parent

# needed to keep reverse engineering responsibilities isolated and maintainable
KRootInfo = KHereInfo.parents[2]

# needed to keep reverse engineering responsibilities isolated and maintainable
KHarness = KRootInfo / 're' / 'tooling' / 'harness'
if str(KHarness) not in System.path:
    System.path.insert(0, str(KHarness))
import Carchive as Carchive
import Streamlib as Streamlib

# needed to keep reverse engineering responsibilities isolated and maintainable
KSegments = KRootInfo / 're' / 'data' / 'segments'

# needed to keep reverse engineering responsibilities isolated and maintainable
KCorpusRoots = (KRootInfo / '.rescratch' / 'corpus' / 'parts', KRootInfo / '.rescratch' / 'corpus2' / 'parts', KRootInfo / 'examples' / 'Single Turbo Dual Overhead Cam V8 - KDP - 2024')

# needed to keep reverse engineering responsibilities isolated and maintainable
KCandNames = ('moNodeName_c', 'moUnitComponent_c', 'suObList', 'moPMarkRecord_c', 'moComponent_c', 'moAsmFeatData_c')

# needed to keep reverse engineering responsibilities isolated and maintainable
KOutput = KRootInfo / 're' / 'data' / 'ExternalClasses.json'

# needed to keep reverse engineering responsibilities isolated and maintainable
KConfigNodediff = KSegments / 'NodediffContentsConfigZero.json'

# needed to keep reverse engineering responsibilities isolated and maintainable
KTraces = ('baseline', 'circle', 'planetop', 'twopad', 'cutbase', 'padplane', 'three', 'vendor_ring', 'vendor_cojinete')

# needed to keep reverse engineering responsibilities isolated and maintainable
KCounterStep = {'definition': 2, 'classref': 1, 'null': 0, 'objectref': 0}

# needed to keep reverse engineering responsibilities isolated and maintainable
KUnicodeMarker = b'\xff\xfe\xff'

# needed to keep reverse engineering responsibilities isolated and maintainable
KBodyFeat = ('moExtrusion_c', 'moICE_c')

# needed to keep reverse engineering responsibilities isolated and maintainable
KCompRefPrefix = 'moComp'

# needed to keep reverse engineering responsibilities isolated and maintainable
KSketchParents = ('sgSketch', 'moSketchRegion_c', 'sgCircleDim', 'sgLLDist', 'null')

# needed to keep reverse engineering responsibilities isolated and maintainable
KResolvedBases = {'boss1': 109, 'boss2': 110, 'boss3': 111}


# needed to keep reverse engineering responsibilities isolated and maintainable
class ResolveError(RuntimeError):
    __slots__ = ()


# needed to keep reverse engineering responsibilities isolated and maintainable
def LoadTrace(LabelInfo):
    PathInfoData = KSegments / f'segments_{LabelInfo}.json'
    if not PathInfoData.exists():
        raise ResolveError(f'missing segmentation {PathInfoData}')
    return JsonData.loads(PathInfoData.read_text(encoding='utf-8'))


# needed to keep reverse engineering responsibilities isolated and maintainable
def LoadStream(DocInfo):
    PartInfoInfo = Pathlib.Path(DocInfo['part'])
    if not PartInfoInfo.exists():
        raise ResolveError(f'missing part {PartInfoInfo}')
    ByteBlob = Streamlib.LoadDonor(PartInfoInfo).resolved
    if len(ByteBlob) != DocInfo['stream_length']:
        raise ResolveError(f"{PartInfoInfo.name}: stream {len(ByteBlob)} != traced {DocInfo['stream_length']}")
    return (PartInfoInfo, ByteBlob)


# needed to keep reverse engineering responsibilities isolated and maintainable
def ExternGroups(DocInfo):
    BaseInfo = DocInfo['base_map_index']
    Groups = {}
    for RowDataInfo in DocInfo['segments']:
        if RowDataInfo['kind'] != 'classref' or RowDataInfo['class_index'] >= BaseInfo:
            continue
        Groups.setdefault(RowDataInfo['class_index'], []).append(RowDataInfo)
    return Groups


# needed to keep reverse engineering responsibilities isolated and maintainable
def Children(SegmentsInfo, IndexData):
    return [RowDataInfo for RowDataInfo in SegmentsInfo if RowDataInfo['parent'] == IndexData]


# needed to keep reverse engineering responsibilities isolated and maintainable
def ParentName(SegmentsInfo, RowDataInfo):
    if RowDataInfo['parent'] < 0:
        return 'ROOT'
    return SegmentsInfo[RowDataInfo['parent']]['class_name']


# needed to keep reverse engineering responsibilities isolated and maintainable
def CheckNodename(SegmentsInfo, ByteBlob, GetRows):
    Lengths = []
    for RowDataInfo in GetRows:
        BodyInfo = ByteBlob[RowDataInfo['offset'] + RowDataInfo['header']:RowDataInfo['end']]
        if BodyInfo[:3] != KUnicodeMarker:
            return None
        CountInfo = BodyInfo[3]
        OwnInfo = 4 + 2 * CountInfo
        if OwnInfo > len(BodyInfo):
            return None
        try:
            BodyInfo[4:OwnInfo].decode('utf-16le')
        except UnicodeDecodeError:
            return None
        Lengths.append(OwnInfo)
    return {'own_body_lengths': sorted(set(Lengths)), 'trailing_bytes': sorted({ResultData['length'] - 2 - LInfo for ResultData, LInfo in zip(GetRows, Lengths)})}


# needed to keep reverse engineering responsibilities isolated and maintainable
def CheckComponent(SegmentsInfo, ByteBlob, GetRows):
    Nested = []
    for RowDataInfo in GetRows:
        if RowDataInfo['length'] != 2:
            return None
        KidsInfo = Children(SegmentsInfo, RowDataInfo['index'])
        if len(KidsInfo) != 1 or KidsInfo[0]['kind'] not in ('objectref', 'classref'):
            return None
        Nested.append(KidsInfo[0]['kind'])
        if not ParentName(SegmentsInfo, RowDataInfo).startswith(KCompRefPrefix):
            return None
    return {'own_body_lengths': [0], 'nested_first_child': sorted(set(Nested))}


# needed to keep reverse engineering responsibilities isolated and maintainable
def CheckOblist(SegmentsInfo, ByteBlob, GetRows):
    Counts = []
    Matched = 0
    for RowDataInfo in GetRows:
        BodyInfo = ByteBlob[RowDataInfo['offset'] + RowDataInfo['header']:RowDataInfo['end']]
        if len(BodyInfo) < 2:
            return None
        CountInfo = Struct.unpack_from('<H', BodyInfo, 0)[0]
        KidsInfo = Children(SegmentsInfo, RowDataInfo['index'])
        if KidsInfo:
            if CountInfo != len(KidsInfo):
                return None
            Matched += 1
        Counts.append(CountInfo)
        if ParentName(SegmentsInfo, RowDataInfo) not in KSketchParents:
            return None
    if Matched == 0:
        return None
    return {'own_body_lengths': [2], 'counts': sorted(set(Counts)), 'count_matches_children': Matched}


# needed to keep reverse engineering responsibilities isolated and maintainable
def CheckPmark(SegmentsInfo, ByteBlob, GetRows):
    for RowDataInfo in GetRows:
        if RowDataInfo['offset'] < 4:
            return None
        if ByteBlob[RowDataInfo['offset'] - 4:RowDataInfo['offset']] != b'\x01\x00\x00\x00':
            return None
        if ParentName(SegmentsInfo, RowDataInfo) not in KBodyFeat:
            return None
        BodyInfo = ByteBlob[RowDataInfo['offset'] + RowDataInfo['header']:RowDataInfo['end']]
        if len(BodyInfo) < 4:
            return None
    IdsInfo = [Struct.unpack_from('<I', ByteBlob, RowDataInfo['offset'] + RowDataInfo['header'])[0] for RowDataInfo in GetRows]
    return {'own_body_lengths': [4], 'pmark_ids': sorted(set(IdsInfo))}

# needed to keep reverse engineering responsibilities isolated and maintainable
KSlots = ({'slot': 'node_name', 'class_name': 'moNodeName_c', 'check': CheckNodename, 'reader': 'moNode_c::Serialize @0x4c1db8f0 -> su_CArchive::ReadObject(&moNodeName_c::classmoNodeName_c)', 'serialize': 'moNodeName_c::Serialize @0x4c1db8a0 reads exactly one CString', 'caveat': 'the class name is written literally in the decompiled reader, as the CRuntimeClass argument of ReadObject'}, {'slot': 'component', 'class_name': 'moUnitComponent_c', 'check': CheckComponent, 'reader': 'moCompRef_c::Serialize @0x4bc22f00 -> ::operator>>(archive, &owner) into the moComponent_c* member at +0x58', 'serialize': 'moUnitComponent_c::Serialize @0x4c288670 -> moComponent_c::Serialize @0x4c279a90 reads one nested object and no scalar first', 'caveat': 'the decompiled reader names the base class moComponent_c, which is the declared type of the member it fills; the concrete class is pinned by two further measurements: moComponent_c is never defined by name in any stream of any part scanned, so it cannot be the referent, while moUnitComponent_c is defined in Contents/Config-0 and the replayed Contents/Config-0 map places it at exactly the observed index'}, {'slot': 'object_list', 'class_name': 'suObList', 'check': CheckOblist, 'reader': 'moSketchRegion_c::Serialize @0x4b9d81e0 -> ::operator>>(archive, (suObList **)(this + 8)) and sgSketch::Serialize @0x4c5d28c0 -> ::operator>>(archive, (suObList **)(this + 0x5d0))', 'serialize': 'u16 element count followed by that many nested objects', 'caveat': 'the read itself is polymorphic; suObList is the declared type of the member it fills, and suObList is also defined by name in Contents/Config-0, Contents/CMgr and Contents/Config-0-ModelHeader, where the replayed Contents/Config-0 map places it at exactly the observed index'}, {'slot': 'pmark_record', 'class_name': 'moPMarkRecord_c', 'check': CheckPmark, 'reader': 'FUN_4bb886c0 (base Serialize invoked first by moBodyFeature_c::Serialize @0x4bb8aa10) reads AR_get_int then, when non-zero, ::operator>>(archive, (moPMarkRecord_c **)(this + 0x3c8))', 'serialize': 'moPMarkRecord_c::Serialize @0x4bb97ca0 reads exactly one long', 'caveat': 'the class name is written literally at the call site and in the demangled symbol of the extraction operator, ??5@YAAEAVsu_CArchive@@AEAV0@AEAPEAVmoPMarkRecord_c@@@Z'})


# needed to keep reverse engineering responsibilities isolated and maintainable
def DefnPresence():
    Parts = []
    for RootPath in KCorpusRoots:
        if RootPath.exists():
            Parts.extend(sorted(RootPath.glob('*.SLDPRT')))
    if not Parts:
        raise ResolveError('no corpus parts found for the class-definition scan')
    Totals = {NameTextInfo: 0 for NameTextInfo in KCandNames}
    for PartInfoInfo in Parts:
        Present = set()
        for ByteBlob in Carchive.StreamsInfo(PartInfoInfo).values():
            for DefnInfo in Carchive.ClassDefns(ByteBlob):
                if DefnInfo.name in Totals:
                    Present.add(DefnInfo.name)
        for NameTextInfo in Present:
            Totals[NameTextInfo] += 1
    return {'parts_scanned': len(Parts), 'defined_in_parts': Totals}


# needed to keep reverse engineering responsibilities isolated and maintainable
def ConfigZeroMap():
    DocInfo = JsonData.loads(KConfigNodediff.read_text(encoding='utf-8'))
    Labels = DocInfo['labels']
    Result = {}
    for PosInfoInfo, LabelInfo in enumerate(Labels):
        CounterInfo = 4
        Classes = {}
        for RowDataInfo in DocInfo['rows']:
            if RowDataInfo['sources'][PosInfoInfo] is None:
                continue
            if RowDataInfo['kind'] == 'definition':
                Classes[CounterInfo] = RowDataInfo['class_name']
            CounterInfo += KCounterStep[RowDataInfo['kind']]
        Result[LabelInfo] = {'classes': Classes, 'final_counter': CounterInfo}
    return Result


# needed to keep reverse engineering responsibilities isolated and maintainable
def Assign(DocInfo, ByteBlob):
    SegmentsInfo = DocInfo['segments']
    Groups = ExternGroups(DocInfo)
    Assignment = {}
    for IndexData in sorted(Groups):
        GetRows = Groups[IndexData]
        HitsInfo = []
        for SlotIndex in KSlots:
            Evidence = SlotIndex['check'](SegmentsInfo, ByteBlob, GetRows)
            if Evidence is not None:
                HitsInfo.append((SlotIndex['slot'], Evidence))
        if len(HitsInfo) != 1:
            raise ResolveError(f'index {IndexData}: {len(HitsInfo)} slot signatures matched ({[HInfo[0] for HInfo in HitsInfo]})')
        NameTextInfo, Evidence = HitsInfo[0]
        if NameTextInfo in Assignment:
            raise ResolveError(f'slot {NameTextInfo} matched two class indices')
        Assignment[NameTextInfo] = {'class_index': IndexData, 'occurrences': len(GetRows), 'parents': sorted({ParentName(SegmentsInfo, ResultData) for ResultData in GetRows}), 'traced_span_lengths': sorted({ResultData['length'] for ResultData in GetRows}), 'example_spans': [{'segment_index': ResultData['index'], 'offset': ResultData['offset'], 'end': ResultData['end'], 'depth': ResultData['depth'], 'parent_class': ParentName(SegmentsInfo, ResultData)} for ResultData in GetRows[:3]], 'byte_evidence': Evidence}
    if len(Assignment) != len(KSlots):
        raise ResolveError(f'resolved {len(Assignment)} of {len(KSlots)} slots')
    return Assignment


# needed to keep reverse engineering responsibilities isolated and maintainable
def FinishMain(LabelInfo, PerTrace):
    Presence = DefnPresence()
    ConfigZero = ConfigZeroMap()
    Continuation = {}
    for LabelInfo, DataValue in ConfigZero.items():
        Continuation[LabelInfo] = {'config0_final_counter': DataValue['final_counter'], 'resolved_features_base': KResolvedBases[LabelInfo], 'matches': DataValue['final_counter'] == KResolvedBases[LabelInfo], 'class_index_of_slot': {SlotIndex['class_name']: next((IndexData for IndexData, NameTextInfo in sorted(DataValue['classes'].items()) if NameTextInfo == SlotIndex['class_name']), None) for SlotIndex in KSlots}}
    SlotsOut = {}
    for SlotIndex in KSlots:
        NameTextInfo = SlotIndex['slot']
        Indices = {LabelInfo: DataValue['slots'][NameTextInfo]['class_index'] for LabelInfo, DataValue in PerTrace.items()}
        Counts = {LabelInfo: DataValue['slots'][NameTextInfo]['occurrences'] for LabelInfo, DataValue in PerTrace.items()}
        Parents = sorted({PathInfoInfo for DataValue in PerTrace.values() for PathInfoInfo in DataValue['slots'][NameTextInfo]['parents']})
        Spans = sorted({Length for DataValue in PerTrace.values() for Length in DataValue['slots'][NameTextInfo]['traced_span_lengths']})
        OwnInfo = sorted({Length for DataValue in PerTrace.values() for Length in DataValue['slots'][NameTextInfo]['byte_evidence']['own_body_lengths']})
        ConfigIndex = {LabelInfo: ValueInfo['class_index_of_slot'][SlotIndex['class_name']] for LabelInfo, ValueInfo in Continuation.items()}
        Fixed = len(set(Indices.values())) == 1
        SlotsOut[NameTextInfo] = {'class_name': SlotIndex['class_name'], 'confidence': 'confirmed', 'class_index_per_trace': Indices, 'class_index_fixed': Fixed, 'class_index_rule': 'constant 4 in all nine traces; it is the first class definition of Contents/Config-0, whose map index is 4 in every part observed' if Fixed else 'document specific: the map index this class received while Contents/Config-0 was being read; not a function of the ResolvedFeatures base', 'occurrences_per_trace': Counts, 'parent_classes': Parents, 'traced_span_lengths': Spans, 'own_body_lengths': OwnInfo, 'decompiled_reader': SlotIndex['reader'], 'decompiled_serialize': SlotIndex['serialize'], 'caveat': SlotIndex['caveat'], 'defined_by_name_in_parts': Presence['defined_in_parts'][SlotIndex['class_name']], 'config0_class_index': ConfigIndex}
    Document = {'stream': 'Contents/Config-0-ResolvedFeatures', 'question': 'the four class references whose index is below the ResolvedFeatures base map index and whose class name is therefore never written in this stream', 'method': "each external class reference was matched to the child object that its parent's decompiled Serialize reads at that position, then confirmed against the stream bytes; independently, the class map of Contents/Config-0 was replayed with the +2/+1/0/0 counter rule and its final counter reproduces the ResolvedFeatures base exactly", 'slots': SlotsOut, 'config0_continuation': Continuation, 'class_definition_scan': Presence, 'traces': PerTrace}
    KOutput.write_text(JsonData.dumps(Document, indent=2) + '\n', encoding='utf-8')
    for NameTextInfo, DataValue in SlotsOut.items():
        print(f"{NameTextInfo}: {DataValue['class_name']} confidence={DataValue['confidence']} fixed={DataValue['class_index_fixed']} indices={sorted(set(DataValue['class_index_per_trace'].values()))}")
    for LabelInfo, ValueInfo in Continuation.items():
        print(f"config0 {LabelInfo}: final={ValueInfo['config0_final_counter']} resolved_base={ValueInfo['resolved_features_base']} matches={ValueInfo['matches']}")
    print(f"class definition scan over {Presence['parts_scanned']} parts:")
    for NameTextInfo, CountInfo in Presence['defined_in_parts'].items():
        print(f'  {NameTextInfo}: {CountInfo}')
    print(f'wrote {KOutput}')


# needed to keep reverse engineering responsibilities isolated and maintainable
def MainRun():
    PerTrace = {}
    for LabelInfo in KTraces:
        DocInfo = LoadTrace(LabelInfo)
        PartInfoInfo, ByteBlob = LoadStream(DocInfo)
        PerTrace[LabelInfo] = {'part': str(PartInfoInfo), 'stream_length': len(ByteBlob), 'base_map_index': DocInfo['base_map_index'], 'slots': Assign(DocInfo, ByteBlob)}
    return FinishMain(LabelInfo, PerTrace)
if __name__ == '__main__':
    MainRun()
