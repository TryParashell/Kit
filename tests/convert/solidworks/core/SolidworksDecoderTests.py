# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations
import math as MathInfo
from pathlib import Path as FilePath
import pytest as PytestLib
from convert.adapters.solidworks.container.Container import SldprtArchive
from convert.adapters.solidworks.container.Format import KEYWORDS_STREAM as Stream, RESOLVED_FEATURES_STREAM as StreamA
from convert.adapters.solidworks.core.Native import DERIVED_SUPPORT_KIND as KindInfo, FACE_SUPPORT_KIND as KindInfoA, PLANE_SUPPORT_KIND as KindInfoB, NativeModel, NativeProfile, NativeSketch, decode_native_model as DecodeNativeModel
from convert.adapters.solidworks.resolved.Core import CIRCLE_POINT_ANGLE_DEGREES as Degrees, DEPTH_COPY_DELTAS as Deltas, DEPTH_COPY_SIGNS as Signs, FROM_END_SPEC_CLASS as Class, FROM_REVERSE_RELATIVE as Relative, class_records as ClassRecords, first_class_offset as FirstClassOffset

# centralizes shared evidence so every related assertion uses one value
KRootInfo = FilePath(__file__).resolve().parents[4]

# centralizes shared evidence so every related assertion uses one value
KParts = KRootInfo / '.rescratch' / 'corpus' / 'parts'

# centralizes shared evidence so every related assertion uses one value
KCorpusTwoParts = KRootInfo / '.rescratch' / 'corpus2' / 'parts'

# centralizes shared evidence so every related assertion uses one value
KCorpusParts = PytestLib.mark.skipif(not KParts.is_dir(), reason='the SOLIDWORKS single-feature corpus is not present in this checkout')

# centralizes shared evidence so every related assertion uses one value
KCorpusTwoPartsA = PytestLib.mark.skipif(not KCorpusTwoParts.is_dir(), reason='the SOLIDWORKS multi-feature corpus is not present in this checkout')

# centralizes shared evidence so every related assertion uses one value
KIdInfo = 2

# centralizes shared evidence so every related assertion uses one value
KIdInfoB = 3

# centralizes shared evidence so every related assertion uses one value
KIdInfoA = 4

# centralizes shared evidence so every related assertion uses one value
KBasis = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))

# centralizes shared evidence so every related assertion uses one value
KBasisB = ((1.0, 0.0, 0.0), (0.0, 0.0, -1.0), (0.0, 1.0, 0.0))

# centralizes shared evidence so every related assertion uses one value
KBasisA = ((0.0, 0.0, -1.0), (0.0, 1.0, 0.0), (1.0, 0.0, 0.0))

# centralizes shared evidence so every related assertion uses one value
KSupports = (('PLANE_FRONT', KIdInfo, 3, KBasis), ('PLANE_TOP', KIdInfoB, 2, KBasisB), ('PLANE_RIGHT', KIdInfoA, 1, KBasisA))

# centralizes shared evidence so every related assertion uses one value
KRadiiA = (('CIRCLE_r10', 10.0), ('CIRCLE_r11', 11.0), ('CIRCLE_r20', 20.0))

# centralizes shared evidence so every related assertion uses one value
KRadii = (('CIRCLECUT_r4', 4.0), ('CIRCLECUT_r6', 6.0))

# centralizes shared evidence so every related assertion uses one value
KPartsA = (('BASELINE_40x20x10', 10.0), ('DEPTH_d11', 11.0), ('DEPTH_d20', 20.0), ('DEPTH_d50', 50.0))

# centralizes shared evidence so every related assertion uses one value
KBoxes = (('BASELINE_40x20x10', (0.0, 0.0, 5.0), 45.82575694955841), ('OFFSET_x10_y7', (10.0, 7.0, 5.0), 45.82575694955841), ('DEPTH_d50', (0.0, 0.0, 25.0), 67.08203932499369), ('MIDPLANE_d10', (0.0, 0.0, 0.0), 45.82575694955841), ('REVERSED_d10', (0.0, 0.0, -5.0), 45.82575694955841), ('PLANE_TOP', (0.0, 5.0, 0.0), 45.82575694955841), ('PLANE_RIGHT', (5.0, 0.0, 0.0), 45.82575694955841), ('CIRCLE_r10', (0.0, 0.0, 5.0), 30.0))

# centralizes shared evidence so every related assertion uses one value
KSketches = (('TWOFEATURES_pad_pad', 'Sketch2', KParts), ('TWOPAD_d5', 'Sketch2', KCorpusTwoParts), ('CUTFACE_d5', 'Sketch2', KCorpusTwoParts), ('THREEFEATURE_pad_cut_pad', 'Sketch3', KCorpusTwoParts))

# centralizes shared evidence so every related assertion uses one value
KSketchesA = (('CUTBASE_cd5', 'Sketch2'), ('CUTMID_d5', 'Sketch2'), ('PADPLANE_rev_d5', 'Sketch2'), ('CIRCLECUT_r4', 'Sketch2'), ('THREEFEATURE_pad_cut_pad', 'Sketch2'))

# keeps this focused behavior isolated so regressions remain immediately visible
def Decode(Directory: FilePath, NameText: str) -> tuple[NativeModel, bytes]:
    Archive = SldprtArchive.from_bytes((Directory / f'{NameText}.SLDPRT').read_bytes())
    Resolved = Archive.require(StreamA)
    return (DecodeNativeModel(Archive.require(Stream), Resolved), Resolved)

# keeps this focused behavior isolated so regressions remain immediately visible
def Sketch(ModelDoc: NativeModel, NameText: str) -> NativeSketch:
    return next((SketchA for SketchA in ModelDoc.sketches if SketchA.name == NameText))

# keeps this focused behavior isolated so regressions remain immediately visible
def Circles(SketchA: NativeSketch) -> tuple[NativeProfile, ...]:
    return tuple((Profile for Profile in SketchA.profiles if Profile.kind == 'circle'))

# keeps this focused behavior isolated so regressions remain immediately visible
@KCorpusParts
@PytestLib.mark.parametrize(('NameText', 'PlaneId', 'AxisCode', 'Basis'), KSupports)
def TestPPSRTSSP(NameText: str, PlaneId: int, AxisCode: int, Basis: tuple[tuple[float, float, float], ...]) -> None:
    ModelDoc, IgnoredValue = Decode(KParts, NameText)
    SketchA = Sketch(ModelDoc, 'Sketch1')
    assert SketchA.support_plane_id == PlaneId
    assert SketchA.support_kind == KindInfoB
    Reference = SketchA.support_plane
    assert Reference is not None
    assert Reference.plane_object_id == PlaneId
    assert Reference.axis_code == AxisCode
    assert (Reference.u_axis, Reference.v_axis, Reference.normal) == Basis
    assert {Plane.object_id for Plane in ModelDoc.planes} >= {PlaneId}

# keeps this focused behavior isolated so regressions remain immediately visible
@KCorpusParts
def NamedTTARPSNLCO() -> None:
    Reported = {}
    for NameText, PlaneId, IgnoredValue, IgnoredValue in KSupports:
        ModelDoc, IgnoredValue = Decode(KParts, NameText)
        Reported[NameText] = Sketch(ModelDoc, 'Sketch1').support_plane_id
        assert Reported[NameText] == PlaneId
    assert len(set(Reported.values())) == len(KSupports)

# keeps this focused behavior isolated so regressions remain immediately visible
@KCorpusParts
def TestTSPRIRFTSCR() -> None:
    ModelDoc, Resolved = Decode(KParts, 'PLANE_TOP')
    Reference = Sketch(ModelDoc, 'Sketch1').support_plane
    assert Reference is not None
    Chain = FirstClassOffset(ClassRecords(Resolved), 'moSketchChain_c')
    assert Chain is not None
    assert Reference.offset == Chain + 209
    assert Reference.basis_offset == Chain + 224

# keeps this focused behavior isolated so regressions remain immediately visible
@KCorpusParts
@PytestLib.mark.parametrize(('NameText', 'RadiusMm'), KRadiiA)
def TestCRARFTSCP(NameText: str, RadiusMm: float) -> None:
    ModelDoc, IgnoredValue = Decode(KParts, NameText)
    CirclesA = Circles(Sketch(ModelDoc, 'Sketch1'))
    assert len(CirclesA) == 1
    CenterX, CenterY, Decoded = CirclesA[0].coordinates
    assert (CenterX, CenterY) == (0.0, 0.0)
    assert abs(Decoded - RadiusMm) <= 1.8e-15
    assert CirclesA[0].start_angle_degrees is not None
    assert CirclesA[0].start_angle_degrees == PytestLib.approx(Degrees, abs=1e-12)

# keeps this focused behavior isolated so regressions remain immediately visible
@KCorpusTwoPartsA
@PytestLib.mark.parametrize(('NameText', 'RadiusMm'), KRadii)
def TestSFCRAE(NameText: str, RadiusMm: float) -> None:
    ModelDoc, IgnoredValue = Decode(KCorpusTwoParts, NameText)
    CirclesA = Circles(Sketch(ModelDoc, 'Sketch2'))
    assert len(CirclesA) == 1
    assert abs(CirclesA[0].coordinates[2] - RadiusMm) <= 1.8e-15
    assert CirclesA[0].start_angle_degrees == PytestLib.approx(Degrees, abs=1e-12)

# keeps this focused behavior isolated so regressions remain immediately visible
@KCorpusParts
def TestRPCNASA() -> None:
    ModelDoc, IgnoredValue = Decode(KParts, 'BASELINE_40x20x10')
    Profiles = Sketch(ModelDoc, 'Sketch1').profiles
    assert [Profile.kind for Profile in Profiles] == ['rectangle']
    assert Profiles[0].start_angle_degrees is None

# keeps this focused behavior isolated so regressions remain immediately visible
@KCorpusParts
@PytestLib.mark.parametrize(('NameText', 'DepthMm'), KPartsA)
def TestASDCAM(NameText: str, DepthMm: float) -> None:
    ModelDoc, IgnoredValue = Decode(KParts, NameText)
    Operation = ModelDoc.operations[0]
    assert Operation.length_mm == PytestLib.approx(DepthMm)
    Copies = Operation.depth_copies
    assert len(Copies) == len(Deltas)
    Anchor = Copies[0].offset
    assert tuple((CopyInfo.offset - Anchor for CopyInfo in Copies)) == Deltas
    assert tuple((CopyInfo.sign for CopyInfo in Copies)) == Signs
    for CopyInfo in Copies:
        assert CopyInfo.value_mm == PytestLib.approx(CopyInfo.sign * DepthMm, abs=1e-09)

# keeps this focused behavior isolated so regressions remain immediately visible
@KCorpusTwoPartsA
def TestTSFDCUTSL() -> None:
    ModelDoc, IgnoredValue = Decode(KCorpusTwoParts, 'CUTBASE_cd7')
    Second = ModelDoc.operations[1]
    assert Second.length_mm == PytestLib.approx(7.0)
    Copies = Second.depth_copies
    Anchor = Copies[0].offset
    assert tuple((CopyInfo.offset - Anchor for CopyInfo in Copies)) == Deltas
    assert tuple((CopyInfo.sign for CopyInfo in Copies)) == Signs
    for CopyInfo in Copies:
        assert CopyInfo.value_mm == PytestLib.approx(CopyInfo.sign * 7.0, abs=1e-09)

# keeps this focused behavior isolated so regressions remain immediately visible
@KCorpusTwoPartsA
def TestAFSSFSTAEPC() -> None:
    ModelDoc, IgnoredValue = Decode(KCorpusTwoParts, 'TWOPAD_d8')
    Second = ModelDoc.operations[1]
    Anchor = Second.depth_copies[0].offset
    ByDelta = {CopyInfo.offset - Anchor: CopyInfo for CopyInfo in Second.depth_copies}
    assert set(ByDelta) == set(Deltas)
    assert ByDelta[0].value_mm == PytestLib.approx(8.0, abs=1e-09)
    assert ByDelta[72].value_mm == PytestLib.approx(18.0, abs=1e-09)

# keeps this focused behavior isolated so regressions remain immediately visible
@KCorpusParts
@PytestLib.mark.parametrize(('NameText', 'CenterMm', 'DiameterMm'), KBoxes)
def TestTBBCID(NameText: str, CenterMm: tuple[float, float, float], DiameterMm: float) -> None:
    ModelDoc, Resolved = Decode(KParts, NameText)
    BoxInfo = ModelDoc.bounding_box
    assert BoxInfo is not None
    Offset = FirstClassOffset(ClassRecords(Resolved), 'moBBoxCenterData_c')
    assert Offset is not None
    assert BoxInfo.offset == Offset + 28
    assert BoxInfo.center_mm == PytestLib.approx(CenterMm, abs=1e-09)
    assert BoxInfo.diameter_mm == PytestLib.approx(DiameterMm, abs=1e-06)

# keeps this focused behavior isolated so regressions remain immediately visible
@KCorpusParts
def TestTBSDMTBHE() -> None:
    ModelDoc, IgnoredValue = Decode(KParts, 'WIDTH_w100')
    BoxInfo = ModelDoc.bounding_box
    assert BoxInfo is not None
    assert BoxInfo.diameter_mm == PytestLib.approx(2.0 * MathInfo.sqrt(50.0 ** 2 + 10.0 ** 2 + 5.0 ** 2), abs=1e-09)

# keeps this focused behavior isolated so regressions remain immediately visible
@KCorpusParts
@PytestLib.mark.parametrize(('NameText', 'Mirrored'), (('BASELINE_40x20x10', 0), ('REVERSED_d10', 1), ('MIDPLANE_d10', 0)))
def TestTMDFIR(NameText: str, Mirrored: int) -> None:
    ModelDoc, Resolved = Decode(KParts, NameText)
    Operation = ModelDoc.operations[0]
    Offset = FirstClassOffset(ClassRecords(Resolved), Class)
    assert Offset is not None
    assert Operation.mirrored_direction_offset == Offset + Relative
    assert Operation.mirrored_direction_code == Mirrored
    assert Operation.mirrored_direction_code == Operation.direction_code

# keeps this focused behavior isolated so regressions remain immediately visible
@KCorpusParts
@PytestLib.mark.parametrize(('NameText', 'RecordEnd'), (('BASELINE_40x20x10', 8280), ('PLANE_TOP', 8352), ('PLANE_RIGHT', 8352), ('CIRCLE_r10', 7881)))
def TestTEORTRE(NameText: str, RecordEnd: int) -> None:
    ModelDoc, Resolved = Decode(KParts, NameText)
    Operation = ModelDoc.operations[0]
    assert Operation.native_end == RecordEnd
    assert Operation.native_end < len(Resolved)
    assert Operation.native_offset < Operation.native_end

# keeps this focused behavior isolated so regressions remain immediately visible
@KCorpusParts
def TestTEREITNCM() -> None:
    ModelDoc, Resolved = Decode(KParts, 'BASELINE_40x20x10')
    Operation = ModelDoc.operations[0]
    RecordList = ClassRecords(Resolved)
    Extrusion = next((RecordInfo for RecordInfo in RecordList if RecordInfo.name == 'moExtrusion_c'))
    Following = min((RecordInfo.offset for RecordInfo in RecordList if RecordInfo.offset > Extrusion.offset))
    assert Operation.native_offset == Extrusion.data_offset
    assert Operation.native_end == Following

# keeps this focused behavior isolated so regressions remain immediately visible
@KCorpusTwoPartsA
@PytestLib.mark.parametrize(('NameText', 'SketchName'), KSketchesA)
def TestPSSSRAPS(NameText: str, SketchName: str) -> None:
    ModelDoc, IgnoredValue = Decode(KCorpusTwoParts, NameText)
    SketchA = Sketch(ModelDoc, SketchName)
    assert SketchA.support_kind == KindInfoB
    assert SketchA.support_plane_id == KIdInfo
    Reference = SketchA.support_plane
    assert Reference is not None
    assert Reference.plane_object_id == KIdInfo
    assert Reference.axis_code == 3
    assert Reference.basis_offset is None
    assert SketchA.native_offset < Reference.offset < SketchA.native_end

# keeps this focused behavior isolated so regressions remain immediately visible
@PytestLib.mark.parametrize(('NameText', 'SketchName', 'Directory'), KSketches)
def TestFSSANRAPS(NameText: str, SketchName: str, Directory: FilePath) -> None:
    if not Directory.is_dir():
        PytestLib.skip('the SOLIDWORKS corpus is not present in this checkout')
    ModelDoc, IgnoredValue = Decode(Directory, NameText)
    SketchA = Sketch(ModelDoc, SketchName)
    assert SketchA.support_kind == KindInfoA
    assert SketchA.support_plane is None

# keeps this focused behavior isolated so regressions remain immediately visible
@KCorpusParts
def TestECPDWD() -> None:
    for TargetPath in sorted(KParts.glob('*.SLDPRT')):
        if TargetPath.name.startswith('~$'):
            continue
        Archive = SldprtArchive.from_bytes(TargetPath.read_bytes())
        ModelDoc = DecodeNativeModel(Archive.require(Stream), Archive.require(StreamA))
        assert ModelDoc.diagnostics == ()
        assert ModelDoc.bounding_box is not None
        assert ModelDoc.sketches
        for SketchA in ModelDoc.sketches:
            assert SketchA.support_kind in {KindInfoB, KindInfoA, KindInfo}
