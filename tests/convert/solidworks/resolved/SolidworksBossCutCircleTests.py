# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations
import hashlib as Hashlib
from pathlib import Path as FilePath
import struct as StructLib
import pytest as PytestLib
from convert import write_document as WriteDocument
from convert.adapters.freecad import read_freecad as ReadFreecad
from convert.adapters.solidworks.container.Container import SldprtArchive, SldprtFormatError
from convert.adapters.solidworks.container.Format import KIT_RESOLVED_STREAM as Stream, RESOLVED_FEATURES_STREAM as StreamA
from convert.adapters.solidworks.resolved.Core import BOSS_KIND as KindInfo, CUT_KIND as KindInfoA, FeatureEdit, locate_features as LocateFeatures, patch_features as PatchFeatures, rectangle_corners_mm as RectangleCornersMm
from convert.adapters.solidworks.programs.resolved.boss.cut.circle.Program import EncodeProgram, KFieldOwners, KResolvedOps

# centralizes shared evidence so every related assertion uses one value
KRepoRoot = FilePath(__file__).resolve().parents[4]

# centralizes shared evidence so every related assertion uses one value
KOracleStream = KRepoRoot / 'tests' / 'fixtures' / 'solidworks' / 'donors' / 'boss_cut_cut_blind' / 'resolved.bin'

# centralizes shared evidence so every related assertion uses one value
KSourcePath = KRepoRoot / '.rescratch' / 'gates' / 'fcstd' / 'gate_boss_cut_circle.FCStd'

# centralizes shared evidence so every related assertion uses one value
KProgramDigest = 'ea2e72fee693b357d6ccea3aac0f9a64a428f5b851aff0d77faf422491d939a6'

# keeps this focused behavior isolated so regressions remain immediately visible
@PytestLib.mark.skipif(not KSourcePath.is_file(), reason='boss plus rectangular and circular blind-cut corpus unavailable')
def TestBCCPWSTP(TmpPath: FilePath) -> None:
    SourceData = ReadFreecad(KSourcePath)
    TargetPath = TmpPath / 'BossCutCirclePublic.SLDPRT'
    ResultData = WriteDocument(SourceData, TargetPath, allow_carrier=False)
    ArchiveData = SldprtArchive.open(TargetPath)
    FeatureData = LocateFeatures(ArchiveData.require(StreamA))
    assert ResultData.vendor_loadable is True
    assert ResultData.application_usable is True
    assert ResultData.near_lossless is True
    assert ResultData.metadata['runtime'] == 'python-stdlib'
    assert Stream not in ArchiveData.streams
    assert tuple((ItemData.name for ItemData in FeatureData)) == ('Boss-Extrude1', 'Cut-Extrude1', 'Cut-Extrude2')
    assert tuple((ItemData.depth_mm for ItemData in FeatureData)) == PytestLib.approx((15.0, 5.0, 9.0))
    assert tuple((ItemData.reversed for ItemData in FeatureData)) == (True, False, False)
    assert FeatureData[0].bounds_mm == PytestLib.approx((-30.0, -20.0, 30.0, 20.0))
    assert FeatureData[1].bounds_mm == PytestLib.approx((-24.0, -4.0, 24.0, 4.0))
    assert FeatureData[2].arcs[0].centre_mm == PytestLib.approx((0.0, 12.0))
    assert FeatureData[2].arcs[0].radius_mm == PytestLib.approx(6.0)

# keeps this focused behavior isolated so regressions remain immediately visible
def TestBCCPCETF() -> None:
    PayloadData = EncodeProgram()
    assert len(PayloadData) == 21021
    assert Hashlib.sha256(PayloadData).hexdigest() == KProgramDigest
    assert PayloadData == KOracleStream.read_bytes()
    assert len(KResolvedOps) == 5302
    assert len(KFieldOwners) == 520
    CursorPos = 0
    ObjectCount = 0
    DefineCount = 0
    for StartPos, FieldWidth, OwnerIndex, KindName, IgnoredValue in KResolvedOps:
        assert StartPos == CursorPos
        assert FieldWidth > 0
        assert 0 <= OwnerIndex < len(KFieldOwners)
        assert KindName in {'definition', 'classref', 'objectref', 'null', 'string'} or KindName.startswith(('primitive:', 'direct:'))
        ObjectCount += KindName in {'definition', 'classref', 'objectref', 'null'}
        DefineCount += KindName == 'definition'
        CursorPos += FieldWidth
    assert CursorPos == len(PayloadData)
    assert ObjectCount == 734
    assert DefineCount == 46

# keeps this focused behavior isolated so regressions remain immediately visible
def TestBCCPECFT() -> None:
    FeatureData = LocateFeatures(EncodeProgram())
    assert tuple((ItemData.kind for ItemData in FeatureData)) == (KindInfo, KindInfoA, KindInfoA)
    assert tuple((ItemData.feature_id for ItemData in FeatureData)) == (32, 40, 47)
    assert tuple((ItemData.sketch_id for ItemData in FeatureData)) == (26, 33, 41)
    assert tuple((ItemData.name for ItemData in FeatureData)) == ('Boss-Extrude1', 'Cut-Extrude1', 'Cut-Extrude2')
    assert tuple((len(ItemData.points) for ItemData in FeatureData)) == (4, 4, 0)
    assert tuple((len(ItemData.arcs) for ItemData in FeatureData)) == (0, 0, 1)
    assert tuple((ItemData.depth_mm for ItemData in FeatureData)) == PytestLib.approx((40.0, 15.0, 50.0))
    CircleData = FeatureData[2].arcs[0]
    assert CircleData.centre_mm == PytestLib.approx((40.0, 15.0))
    assert CircleData.radius_mm == PytestLib.approx(25.0)
    assert CircleData.sweep_angle_degrees == PytestLib.approx(360.0)

# keeps this focused behavior isolated so regressions remain immediately visible
def TestBCCPASFE() -> None:
    PatchedData = PatchFeatures(EncodeProgram(), {0: FeatureEdit(corners_mm=RectangleCornersMm(-30.0, -20.0, 30.0, 20.0), depth_mm=15.0, reversed=True, end_condition_code=0, update_depth_copies=True), 1: FeatureEdit(corners_mm=RectangleCornersMm(-24.0, -4.0, 24.0, 4.0), depth_mm=5.0, reversed=False, end_condition_code=0, update_depth_copies=True), 2: FeatureEdit(depth_mm=9.0, reversed=False, end_condition_code=0, update_depth_copies=True, radii_mm=(6.0,), arc_centres_mm=((0.0, 12.0),))})
    FeatureData = LocateFeatures(PatchedData)
    assert FeatureData[0].bounds_mm == PytestLib.approx((-30.0, -20.0, 30.0, 20.0))
    assert FeatureData[1].bounds_mm == PytestLib.approx((-24.0, -4.0, 24.0, 4.0))
    assert tuple((ItemData.depth_mm for ItemData in FeatureData)) == PytestLib.approx((15.0, 5.0, 9.0))
    assert tuple((ItemData.reversed for ItemData in FeatureData)) == (True, False, False)
    assert all((ItemData.end_condition_code == 0 for ItemData in FeatureData))
    CircleData = FeatureData[2].arcs[0]
    assert CircleData.centre_mm == PytestLib.approx((0.0, 12.0))
    assert CircleData.radius_mm == PytestLib.approx(6.0)
    for ItemData in FeatureData:
        CopyValues = tuple((StructLib.unpack_from('<d', PatchedData, OffsetPos)[0] for OffsetPos in ItemData.depth_copy_offsets))
        ExpectedDepth = ItemData.depth_mm / 1000.0
        assert CopyValues == PytestLib.approx((ExpectedDepth, ExpectedDepth, -ExpectedDepth, -ExpectedDepth, ExpectedDepth, ExpectedDepth))

# keeps this focused behavior isolated so regressions remain immediately visible
def TestBCCPRVWO() -> None:
    StringField = next((ItemData for ItemData in KResolvedOps if ItemData[3] == 'string'))
    with PytestLib.raises(SldprtFormatError, match='field width changed'):
        EncodeProgram({StringField[0]: 'variable width metadata is unsupported'})

# keeps this focused behavior isolated so regressions remain immediately visible
def TestBCCPCNVB() -> None:
    ProgramPath = KRepoRoot / 'src' / 'convert' / 'adapters' / 'solidworks' / 'Program.py'
    SourceText = ProgramPath.read_text(encoding='utf-8')
    assert 'bytes.fromhex' not in SourceText
    assert 'base64' not in SourceText
    assert 'b85decode' not in SourceText
    assert 'opaque' not in SourceText.casefold()
    assert '.rescratch' not in SourceText
    assert 'tests/fixtures' not in SourceText
