# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations
import ast as AstInfo
from pathlib import Path as FilePath
import struct as StructLib
import pytest as PytestLib
import convert.adapters.solidworks.core.Adapter as SolidworksAdapter
import convert.adapters.solidworks.assembly.Assembly as SolidworksAssembly
import convert.adapters.solidworks.core.Display as SolidworksDisplay
import convert.adapters.solidworks.core.Native as SolidworksNative
from convert.adapters.solidworks.core.Adapter import SldprtAdapter
from convert.adapters.solidworks.container.Container import SldprtArchive
from convert.adapters.solidworks.container.Format import ASSEMBLY_FORMAT_ID as IdInfo, ASSEMBLY_SUFFIX as Suffix, CANONICAL_PLANE_FEATURE_TYPE as TypeInfo, CLASS_MARKER as Marker, COMPONENT_TREE_STREAM as Stream, CONTAINER_VERSIONS as Versions, CONTENT_TYPES_STREAM as StreamA, DIMENSION_SCALAR_HEADERS as Headers, DISPLAY_LISTS_STREAM as StreamB, FEATURES_STREAM as StreamC, FORMAT_IDS as IdsInfo, FORMAT_ID_BY_SUFFIX as SuffixA, INFO as InfoInfo, KEYWORDS_STREAM as StreamD, KIT_DOCUMENT_STREAM as StreamE, MATES_STREAM_NAME as NameInfo, MATES_STREAM_SUFFIX as SuffixB, OFFICIAL_REFERENCE_PLANE_FEATURE_TYPES as Types, PARTITION_STREAM as StreamF, PART_FORMAT_ID as IdInfoA, PART_SUFFIX as SuffixC, PLANE_FEATURE_TYPES as TypesA, RELATIONSHIPS_STREAM as StreamG, RESOLVED_FEATURES_STREAM as StreamH, SERIALIZED_STRING_MARKER as MarkerA, SOLIDWORKS_STREAM as StreamI, SOLID_BODY_FEATURE_TYPES as TypesB, SUFFIX_BY_FORMAT_ID as IdInfoB, dimension_scalar_value_offset as DimensionSVO, is_cad_path as IsCadPath, is_component_path as IsComponentPath
from interchange import BooleanOperation, Capability, CircleGeometry, FeatureKind, LineGeometry

# centralizes shared evidence so every related assertion uses one value
SAMPLE = FilePath(__file__).parents[4] / 'examples' / '.SLDPRT' / 'example.SLDPRT'

# keeps this focused behavior isolated so regressions remain immediately visible
def TestFPVAEADFAI() -> None:
    assert SldprtAdapter().info is InfoInfo
    assert IdsInfo == (InfoInfo.format_id, *InfoInfo.aliases)
    assert tuple(SuffixA) == InfoInfo.extensions
    assert tuple(SuffixA.values()) == IdsInfo
    assert IdInfoB == {FormatId: SuffixD for SuffixD, FormatId in SuffixA.items()}
    assert (IdInfoA, IdInfo) == IdsInfo
    assert (SuffixC, Suffix) == InfoInfo.extensions
    assert Versions == frozenset({3, 4})
    assert (Stream, StreamB, StreamD, StreamC, StreamH, StreamF, StreamI, StreamE, StreamA, StreamG, NameInfo, SuffixB) == ('swXmlContents/COMPINSTANCETREE', 'Contents/DisplayLists', 'swXmlContents/KeyWords', 'swXmlContents/Features', 'Contents/Config-0-ResolvedFeatures', 'Contents/Config-0-Partition', 'Contents/SolidWorks', 'Kit/Interchange', '[Content_Types].xml', '_rels/.rels', 'MatesList', '-MatesList')
    assert Marker.hex() == 'ffff0100'
    assert MarkerA.hex() == 'fffeff'
    assert tuple((Header.hex() for Header in Headers)) == ('0000000000000040ffffffff00000000fffeff000000', '0000000000000040ffffffff000000000000')
    assert TypeInfo == 'plane'
    assert Types == frozenset({'refplane'})
    assert TypesA == frozenset({'plane', 'refplane'})
    assert TypesB == frozenset({'featsolidbodyfolder', 'solidbodyfolder'})
    assert all((SolidworksAdapter._FEATURE_KIND_BY_NATIVE[NativeType] == FeatureKind.REFERENCE for NativeType in (*TypesA, *TypesB)))

# keeps this focused behavior isolated so regressions remain immediately visible
def TestMLIRLACWUF() -> None:
    Expected = {142: 138, 146: 138, 152: 148, 154: 150, 156: 148, 158: 144, 162: 158, 166: 158, 167: 158}
    assert SolidworksNative.MARKER_LOCAL_ID_OFFSET_BY_LENGTH == Expected
    for Length, Relative in Expected.items():
        DataValue = bytearray(Length + 4)
        StructLib.pack_into('<I', DataValue, Relative, 42)
        assert SolidworksNative._marker_local_id(bytes(DataValue), 0, Length) == 42
    assert SolidworksNative._marker_local_id(bytes(2048), 0, 2048) is None

# keeps this focused behavior isolated so regressions remain immediately visible
@PytestLib.mark.parametrize('Header', Headers)
def TestDSHBASAE(Header: bytes) -> None:
    DataValue = b'x' + Header + StructLib.pack('<d', 2.0)
    Expected = 1 + len(Header)
    assert DimensionSVO(DataValue, 1, len(DataValue)) == Expected
    assert DimensionSVO(DataValue[:-1], 1, len(DataValue) - 1) is None
    assert DimensionSVO(DataValue, 1, len(DataValue), trailing_bytes=7) is None
    WithTrailer = DataValue + b'\x00' * 7
    assert DimensionSVO(WithTrailer, 1, len(WithTrailer), trailing_bytes=7) == Expected

# keeps this focused behavior isolated so regressions remain immediately visible
def TestPCSAO() -> None:
    assert SolidworksNative.dimension_scalar_value_offset is DimensionSVO
    assert SolidworksAssembly.dimension_scalar_value_offset is DimensionSVO
    assert SolidworksAssembly.COMPONENT_TREE_STREAM is Stream
    assert SolidworksAssembly.DISPLAY_LISTS_STREAM is StreamB
    assert SolidworksDisplay.DISPLAY_LISTS_STREAM is StreamB
    assert SolidworksDisplay.is_cad_path is IsCadPath
    assert SolidworksDisplay.is_component_path is IsComponentPath
    assert SolidworksAdapter.INFO is InfoInfo
    assert SolidworksAdapter.FORMAT_ID_BY_SUFFIX is SuffixA
    assert SolidworksAdapter.SUFFIX_BY_FORMAT_ID is IdInfoB

# keeps this focused behavior isolated so regressions remain immediately visible
def TestPLHOSD() -> None:
    ValueList = {'.sldprt', '.sldasm', 'swXmlContents/COMPINSTANCETREE', 'Contents/DisplayLists', 'swXmlContents/KeyWords', 'swXmlContents/Features', 'Contents/Config-0-ResolvedFeatures', 'Contents/Config-0-Partition', 'Contents/SolidWorks', 'Kit/Interchange', '[Content_Types].xml', '_rels/.rels', 'MatesList', 'ffff0100', 'fffeff', '0000000000000040ffffffff00000000fffeff000000', '0000000000000040ffffffff000000000000', 'refplane', 'featsolidbodyfolder', 'solidbodyfolder'}
    SourceRoot = FilePath(SolidworksAdapter.__file__).parent
    Occurrences = {ItemValue: [] for ItemValue in ValueList}
    for TargetPath in SourceRoot.glob('*.py'):
        if TargetPath.stem.startswith('assembly') and TargetPath.stem != 'assembly':
            continue
        TreeInfo = AstInfo.parse(TargetPath.read_text(encoding='utf-8'))
        for NodeInfo in AstInfo.walk(TreeInfo):
            if isinstance(NodeInfo, AstInfo.Constant) and NodeInfo.value in Occurrences:
                Occurrences[NodeInfo.value].append(TargetPath.name)
    assert Occurrences == {ItemValue: ['Format.py'] for ItemValue in ValueList}

# keeps this focused behavior isolated so regressions remain immediately visible
@PytestLib.mark.parametrize(('value', 'is_cad', 'is_component'), (('C:/parts/Part.SLDPRT', True, False), ('C:/parts/Assembly.SLDASM', True, False), ('C:/parts/Part.sldprtx', False, False), ('Rotor@Assembly', False, True), ('Top Plane@Rotor@Assembly', False, False)))
def TestPPCIE(ItemValue: str, IsCad: bool, IsComponent: bool) -> None:
    assert IsCadPath(ItemValue) is IsCad
    assert IsComponentPath(ItemValue) is IsComponent

# keeps this focused behavior isolated so regressions remain immediately visible
def TestCREICS() -> None:
    Archive = SldprtArchive.open(SAMPLE)
    assert Archive.format_version == 4
    assert len(Archive.records) == 44
    assert Archive.records[0].name == 'Contents/3DExperienceExchange2'
    assert Archive.records[-1].name == 'swXmlContents/KeyWords'
    assert {RecordInfo.name for RecordInfo in Archive.records} >= {'Contents/Config-0-ResolvedFeatures', 'Contents/Config-0-Partition', 'PreviewPNG', 'Header2', 'Preview'}

# keeps this focused behavior isolated so regressions remain immediately visible
def TestPHINAO() -> None:
    Document = SldprtAdapter().read(SAMPLE)
    Operations = [Feature for Feature in Document.feature_timeline if Feature.name in {'Boss-Extrude1', 'Cut-Extrude1', 'Boss-Extrude2', 'Cut-Extrude2', 'Boss-Extrude3', 'Fillet1'}]
    assert [Feature.name for Feature in Operations] == ['Boss-Extrude1', 'Cut-Extrude1', 'Boss-Extrude2', 'Cut-Extrude2', 'Boss-Extrude3', 'Fillet1']
    assert [Feature.operation for Feature in Operations[:-1]] == [BooleanOperation.JOIN, BooleanOperation.CUT, BooleanOperation.JOIN, BooleanOperation.CUT, BooleanOperation.JOIN]
    assert [Document.parameter(Feature.parameter_ids[0]).value.value for Feature in Operations] == [20.0, 0.25, 0.75, 9.0, 6.0, 0.25]
    assert Capability.PARAMETRIC_HISTORY in Document.capabilities
    assert Capability.EDITABLE_SKETCHES in Document.capabilities
    assert Document.validate() == ()

# keeps this focused behavior isolated so regressions remain immediately visible
def TestSPASPAE() -> None:
    Document = SldprtAdapter().read(SAMPLE)
    assert len(Document.sketches) == 5
    First = Document.sketch('sldprt:sketch:26')
    FirstEdges = [Entity.geometry for Entity in First.entities if Entity.id in First.closed_profile_entity_ids[0]]
    assert all((isinstance(EdgeInfo, LineGeometry) for EdgeInfo in FirstEdges))
    assert FirstEdges[0].start.x == -124.3
    assert FirstEdges[0].start.y == -89.75
    assert FirstEdges[2].start.x == 124.3
    assert FirstEdges[2].start.y == 89.75
    HoleInfo = Document.sketch('sldprt:sketch:88')
    HoleProfile = next((Entity.geometry for Entity in HoleInfo.entities if Entity.id == HoleInfo.closed_profile_entity_ids[0][0]))
    assert isinstance(HoleProfile, CircleGeometry)
    assert HoleProfile.center.x == 10.0
    assert HoleProfile.center.y == 81.631746131982
    assert HoleProfile.radius == 2.75
    assert Document.plane('sldprt:plane:62').transform.origin.x == 124.30000000000001
    assert Document.plane('sldprt:plane:104').transform.origin.x == -115.3

# keeps this focused behavior isolated so regressions remain immediately visible
def TestPBIPBFB() -> None:
    Document = SldprtAdapter().read(SAMPLE)
    assert [Payload.kind for Payload in Document.brep_payloads] == ['partition', 'partition', 'deltas']
    assert [len(Payload.data or b'') for Payload in Document.brep_payloads] == [1513, 30850, 23150]
    assert [Payload.sha256 for Payload in Document.brep_payloads] == ['8c57db227621a15a0a429cdd65dbe3f374e2c1145ef2f3edc3a25b745513bf3d', '3f3e3efbfbee0f41bda187579547881126cbf48101f006eecd759f491fc87ac6', '59d5eef7feb40d7a2ce52e20e50e14ca8eedaa1a1671b33a13fdc43720311cb7']
    assert all((Payload.data is not None and Payload.data.startswith(b'PS\x00\x00') for Payload in Document.brep_payloads))

# keeps this focused behavior isolated so regressions remain immediately visible
def TestNJRKHAB() -> None:
    SourceDoc = SldprtAdapter().read(SAMPLE)
    Restored = type(SourceDoc).from_json(SourceDoc.to_json())
    assert Restored == SourceDoc
