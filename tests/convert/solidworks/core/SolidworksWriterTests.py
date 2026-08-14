# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations
from dataclasses import replace as ReplaceData
from io import BytesIO, StringIO
import hashlib as Hashlib
import json as JsonLib
from pathlib import Path as FilePath, PureWindowsPath
import struct as StructLib
import xml.etree.ElementTree as EtInfo
import pytest as PytestLib
from convert import ApplicationUsabilityError, convert as Convert, open_document as OpenDocument, registry as Registry, write_document as WriteDocument
from convert.adapters import WriteOptions
from convert.adapters.catia import read_catia as ReadCatia, write_catia as WriteCatia
from convert.adapters.freecad import read_freecad as ReadFreecad, write_freecad as WriteFreecad
from convert.adapters.solidworks import SldprtArchive, SldprtFormatError, build_sldprt as BuildSldprt, decode_native_assembly as DecodeNativeAssembly, decode_native_model as DecodeNativeModel, decode_brep_model as DecodeBrepModel, decode_partition_stream as DecodePartitionStream, encode_blank_partition_stream as EncodeBPS, encode_brep_model as EncodeBrepModel, read_sldprt as ReadSldprt, write_sldprt as WriteSldprt
from convert.adapters.solidworks.container.Archive import encode_class_definition as EncodeClassDefinition
from convert.adapters.solidworks.container.Container import container_signatures as ContainerSignatures
from convert.adapters.solidworks.core.Adapter import _ASSEMBLY_DONOR_CARRIED_STREAMS as Streams, _document_without_source as DocumentWithoutSource, _native_stream_sha256 as NativeStreamShaTwoFiveSix, _semantic_sha256 as SemanticShaTwoFiveSix
from convert.adapters.solidworks.container.Cmgr import CONFIGURATION_MANAGER_STREAM as StreamA
from convert.adapters.solidworks.container.Format import COMPONENT_TREE_STREAM as Stream, CONFIGURATION_STREAM as StreamB, CONTENT_TYPES_STREAM as StreamC, FEATURES_STREAM as StreamD, KEYWORDS_STREAM as StreamE, KIT_DOCUMENT_STREAM as StreamF, KIT_NATIVE_STREAM as StreamG, KIT_RESOLVED_STREAM as StreamH, PARTITION_STREAM as StreamI, RELATIONSHIPS_STREAM as StreamJ, RESOLVED_FEATURES_STREAM as StreamK
from convert.adapters.solidworks.core.Native import HasVendorPartEncoding, VENDOR_UNLOADABLE_NOTES as Notes, decode_native_model_header as DecodeNativeModelHeader, encode_native_part as EncodeNativePart, native_axis_bindings as NativeAxisBindings
from convert.adapters.solidworks.resolved.Core import BLIND_END_CONDITION as Condition, locate_features as LocateFeatures
from convert.adapters.solidworks.programs.resolved.revolve.pin.default.Program import EncodeProgram as EncodeRevolvePinProgram, FieldOwners as RevolvePinOwners, ResolvedOps as RevolvePinOps
from convert.adapters.solidworks.envelopes.revolve.pin.default.Envelope import BuildEnvelope as BuildRevolvePinEnvelope, KPinPointsMm
from convert.geometry.Parasolid import _parasolid_header as ParasolidHeader, _scan_partition_records as ScanPartitionRecords
from interchange import BooleanOperation, BrepPayload, CadDocument, Capability, CircleGeometry, Configuration, Diagnostic, ExtrusionEndCondition, ExtrusionFeature, FeatureKind, GeometryKind, LineGeometry, MateAlignment, Matrix4 as MatrixFour, NativeFeatureDefinition, NativeSurface, Parameter, ParameterValue, PayloadRole, Provenance, Selection, SelectionPathElement, Severity, Sketch, SketchEntity, Transform, ValueKind, Vector2 as VectorTwo, Vector3 as VectorThree, frozen_mapping as FrozenMapping
from tests.interchange.assembly.AssemblyTests import assembly_document as AssemblyDocument
from tests.interchange.brep.BrepTests import triangle_brep as TriangleBrep
from tests.interchange.document.DocumentTests import document as Document

# centralizes shared evidence so every related assertion uses one value
KSample = FilePath(__file__).parents[4] / 'examples' / '.SLDPRT' / 'example.SLDPRT'

# centralizes shared evidence so every related assertion uses one value
KAssembly = FilePath(__file__).parents[4] / 'examples' / 'Random' / 'Pistons' / 'Piston.SLDASM'

# centralizes shared evidence so every related assertion uses one value
KConrod = FilePath(__file__).parents[4] / 'examples' / 'Random' / 'Pistons' / 'Conrod.SLDASM'

# centralizes shared evidence so every related assertion uses one value
KRingInfo = FilePath(__file__).parents[4] / 'examples' / 'Random' / 'Pistons' / 'Piston_ring.SLDPRT'

# centralizes shared evidence so every related assertion uses one value
KCatproduct = FilePath(__file__).parents[4] / 'examples' / '.CATProduct' / 'Tilton_Set.CATProduct'

# centralizes shared evidence so every related assertion uses one value
KFreeCadBoxCorpus = FilePath(__file__).parents[4] / '.rescratch' / 'freecad' / 'FreeCAD_1.1.3-Windows-x86_64-py311' / 'Mod' / 'Fem' / 'femtest' / 'data' / 'calculix' / 'box.FCStd'

# centralizes shared evidence so every related assertion uses one value
KFreeCadCylCorpus = FilePath(__file__).parents[4] / '.rescratch' / 'fcstd' / 'cylinder_r5_h10.FCStd'

# centralizes shared evidence so every related assertion uses one value
KFreeCadRevPin = FilePath(__file__).parents[4] / '.rescratch' / 'sw' / 'fcstd' / 'kit_revolve_pin_top.FCStd'

# keeps this focused behavior isolated so regressions remain immediately visible
def FreecadRPD(Bounds: tuple[float, float, float, float]=(-30.0, -15.0, 30.0, 15.0), Depth: float=12.0) -> CadDocument:
    SourceDoc = Document()
    MinimumX, MinimumY, MaximumX, MaximumY = Bounds
    Points = (VectorTwo(MinimumX, MinimumY), VectorTwo(MaximumX, MinimumY), VectorTwo(MaximumX, MaximumY), VectorTwo(MinimumX, MaximumY))
    Entities = tuple((SketchEntity(f'freecad:edge:{Index}', GeometryKind.LINE, LineGeometry(Points[Index], Points[(Index + 1) % 4])) for Index in range(4)))
    SketchA = Sketch(SourceDoc.sketches[0].id, 'Sketch', SourceDoc.sketches[0].support_plane_id, Entities, closed_profile_entity_ids=(tuple((ItemValue.id for ItemValue in Entities)),), attributes=FrozenMapping({'freecad': {'type_id': 'Sketcher::SketchObject'}}))
    Feature = ReplaceData(SourceDoc.feature_timeline[0], name='Pad', operation=BooleanOperation.CREATE, definition=ExtrusionFeature(ParameterValue(Depth, ValueKind.LENGTH, 'mm'), direction=VectorThree(0.0, 0.0, 1.0), second_length=ParameterValue(10.0, ValueKind.LENGTH, 'mm'), offset=ParameterValue(0.0, ValueKind.LENGTH, 'mm'), second_offset=ParameterValue(0.0, ValueKind.LENGTH, 'mm'), draft_angle=ParameterValue(0.0, ValueKind.ANGLE, 'deg'), second_draft_angle=ParameterValue(0.0, ValueKind.ANGLE, 'deg')), attributes=FrozenMapping({'freecad': {'type_id': 'PartDesign::Pad'}}))
    ValueList = (('AllowMultiFace', True, ValueKind.BOOLEAN, ''), ('AlongSketchNormal', True, ValueKind.BOOLEAN, ''), ('FuzzyTolerance', 0.0, ValueKind.NUMBER, ''), ('Label', 'Pad', ValueKind.STRING, ''), ('Label2', '', ValueKind.STRING, ''), ('Length', Depth, ValueKind.LENGTH, 'mm'), ('Length2', 10.0, ValueKind.LENGTH, 'mm'), ('Midplane', False, ValueKind.BOOLEAN, ''), ('Offset', 0.0, ValueKind.LENGTH, 'mm'), ('Offset2', 0.0, ValueKind.LENGTH, 'mm'), ('Refine', True, ValueKind.BOOLEAN, ''), ('Reversed', False, ValueKind.BOOLEAN, ''), ('SideType', 0, ValueKind.INTEGER, ''), ('Suppressed', False, ValueKind.BOOLEAN, ''), ('TaperAngle', 0.0, ValueKind.ANGLE, 'deg'), ('TaperAngle2', 0.0, ValueKind.ANGLE, 'deg'), ('Type', 0, ValueKind.INTEGER, ''), ('Type2', 0, ValueKind.INTEGER, ''), ('UseCustomVector', False, ValueKind.BOOLEAN, ''), ('Visibility', True, ValueKind.BOOLEAN, ''))
    Parameters = tuple((Parameter(f'freecad:parameter:Pad:{TargetPathA}', f'Pad.{TargetPathA}', ParameterValue(ItemValueA, KindInfo, UnitInfo), owner_id=Feature.id, attributes=FrozenMapping({'freecad_path': TargetPathA})) for TargetPathA, ItemValueA, KindInfo, UnitInfo in ValueList))
    Feature = ReplaceData(Feature, parameter_ids=tuple((ItemValue.id for ItemValue in Parameters)))
    return ReplaceData(SourceDoc, source=ReplaceData(SourceDoc.source, format_id='freecad.fcstd', path='FreeCADRectanglePad.FCStd'), parameters=Parameters, sketches=(SketchA,), feature_timeline=(Feature,), bodies=(ReplaceData(SourceDoc.bodies[0], final_feature_id=Feature.id),), capabilities=frozenset({Capability.PARAMETERS, Capability.PARAMETRIC_HISTORY, Capability.SUPPORT_PLANES, Capability.EDITABLE_SKETCHES, Capability.BODY_STRUCTURE, Capability.CONFIGURATIONS, Capability.BREP, Capability.NATIVE_PAYLOADS, Capability.PROVENANCE, Capability.ROUNDTRIP_METADATA}))

# keeps this focused behavior isolated so regressions remain immediately visible
def FreeCPPD(*, ThroughAll: bool=False, JoinInfo: bool=False) -> CadDocument:
    SourceData = FreecadRPD(bounds=(-30.0, -20.0, 30.0, 20.0), depth=15.0)
    FeatureOne = SourceData.feature_timeline[0]
    SketchTemplate = SourceData.sketches[0]
    PocketPoints = (VectorTwo(-10.0, -8.0), VectorTwo(10.0, -8.0), VectorTwo(10.0, 8.0), VectorTwo(-10.0, 8.0))
    PocketEntities = tuple((SketchEntity(f'freecad:pocket-edge:{IndexValue}', GeometryKind.LINE, LineGeometry(PocketPoints[IndexValue], PocketPoints[(IndexValue + 1) % 4])) for IndexValue in range(4)))
    SketchTwo = ReplaceData(SketchTemplate, id='freecad:sketch:Sketch001', name='Sketch001', entities=PocketEntities, parameter_ids=(), closed_profile_entity_ids=(tuple((ItemData.id for ItemData in PocketEntities)),))
    SecondName = 'Pad001' if JoinInfo else 'Pocket'
    FeatureTwo = ReplaceData(FeatureOne, id=f'freecad:feature:{SecondName}', name=SecondName, order=1, operation=BooleanOperation.JOIN if JoinInfo else BooleanOperation.CUT, sketch_id=SketchTwo.id, input_feature_ids=(FeatureOne.id,), definition=ExtrusionFeature(ParameterValue(25.0 if JoinInfo else 5.0 if ThroughAll else 6.0, ValueKind.LENGTH, 'mm'), end_condition=ExtrusionEndCondition.THROUGH_ALL if ThroughAll else ExtrusionEndCondition.BLIND, reversed=not JoinInfo, direction=VectorThree(0.0, 0.0, 1.0 if JoinInfo else -1.0), second_length=ParameterValue(10.0 if JoinInfo else 5.0, ValueKind.LENGTH, 'mm'), offset=ParameterValue(0.0, ValueKind.LENGTH, 'mm'), second_offset=ParameterValue(0.0, ValueKind.LENGTH, 'mm'), draft_angle=ParameterValue(0.0, ValueKind.ANGLE, 'deg'), second_draft_angle=ParameterValue(0.0, ValueKind.ANGLE, 'deg')), attributes=FrozenMapping({'freecad': {'type_id': 'PartDesign::Pad' if JoinInfo else 'PartDesign::Pocket'}}))
    FirstParameters = tuple((ReplaceData(ItemData, value=ParameterValue(False, ValueKind.BOOLEAN) if ItemData.attributes.get('freecad_path') == 'Visibility' else ItemData.value) for ItemData in SourceData.parameters))
    PocketValues = {'Label': ParameterValue(SecondName, ValueKind.STRING), 'Length': ParameterValue(25.0 if JoinInfo else 5.0 if ThroughAll else 6.0, ValueKind.LENGTH, 'mm'), 'Length2': ParameterValue(10.0 if JoinInfo else 5.0, ValueKind.LENGTH, 'mm'), 'Reversed': ParameterValue(not JoinInfo, ValueKind.BOOLEAN), 'Type': ParameterValue(1 if ThroughAll else 0, ValueKind.INTEGER), 'Visibility': ParameterValue(True, ValueKind.BOOLEAN)}
    SecondParameters = tuple((ReplaceData(ItemData, id=f"freecad:parameter:{SecondName}:{ItemData.attributes['freecad_path']}", name=f"{SecondName}.{ItemData.attributes['freecad_path']}", value=PocketValues.get(str(ItemData.attributes['freecad_path']), ItemData.value), owner_id=FeatureTwo.id) for ItemData in SourceData.parameters))
    FeatureTwo = ReplaceData(FeatureTwo, parameter_ids=tuple((ItemData.id for ItemData in SecondParameters)))
    return ReplaceData(SourceData, parameters=(*FirstParameters, *SecondParameters), sketches=(SketchTemplate, SketchTwo), feature_timeline=(FeatureOne, FeatureTwo), bodies=(ReplaceData(SourceData.bodies[0], final_feature_id=FeatureTwo.id),))

# keeps this focused behavior isolated so regressions remain immediately visible
def FreeCPTPDA() -> CadDocument:
    SourceData = FreeCPPD()
    FeatureTwo = SourceData.feature_timeline[1]
    SketchTemplate = SourceData.sketches[1]
    PocketPoints = (VectorTwo(15.0, -5.0), VectorTwo(25.0, -5.0), VectorTwo(25.0, 5.0), VectorTwo(15.0, 5.0))
    PocketEntities = tuple((SketchEntity(f'freecad:pocket-two-edge:{IndexValue}', GeometryKind.LINE, LineGeometry(PocketPoints[IndexValue], PocketPoints[(IndexValue + 1) % 4])) for IndexValue in range(4)))
    SketchThree = ReplaceData(SketchTemplate, id='freecad:sketch:Sketch002', name='Sketch002', entities=PocketEntities, parameter_ids=(), closed_profile_entity_ids=(tuple((ItemData.id for ItemData in PocketEntities)),))
    assert isinstance(FeatureTwo.definition, ExtrusionFeature)
    FeatureThree = ReplaceData(FeatureTwo, id='freecad:feature:Pocket001', name='Pocket001', order=2, sketch_id=SketchThree.id, input_feature_ids=(FeatureTwo.id,), definition=ReplaceData(FeatureTwo.definition, length=ParameterValue(5.0, ValueKind.LENGTH, 'mm')))
    ParametersOneTwo = tuple((ReplaceData(ItemData, value=ParameterValue(False, ValueKind.BOOLEAN) if ItemData.owner_id == FeatureTwo.id and ItemData.attributes.get('freecad_path') == 'Visibility' else ItemData.value) for ItemData in SourceData.parameters))
    PocketValues = {'Label': ParameterValue('Pocket001', ValueKind.STRING), 'Length': ParameterValue(5.0, ValueKind.LENGTH, 'mm'), 'Visibility': ParameterValue(True, ValueKind.BOOLEAN)}
    ParametersThree = tuple((ReplaceData(ItemData, id=f"freecad:parameter:Pocket001:{ItemData.attributes['freecad_path']}", name=f"Pocket001.{ItemData.attributes['freecad_path']}", value=PocketValues.get(str(ItemData.attributes['freecad_path']), ItemData.value), owner_id=FeatureThree.id) for ItemData in SourceData.parameters if ItemData.owner_id == FeatureTwo.id))
    FeatureThree = ReplaceData(FeatureThree, parameter_ids=tuple((ItemData.id for ItemData in ParametersThree)))
    return ReplaceData(SourceData, parameters=(*ParametersOneTwo, *ParametersThree), sketches=(*SourceData.sketches, SketchThree), feature_timeline=(*SourceData.feature_timeline, FeatureThree), bodies=(ReplaceData(SourceData.bodies[0], final_feature_id=FeatureThree.id),))

# keeps this focused behavior isolated so regressions remain immediately visible
def FreeCPTPD() -> CadDocument:
    SourceData = FreeCPTPDA()
    FeatureThree = SourceData.feature_timeline[2]
    SketchTemplate = SourceData.sketches[2]
    PocketPoints = (VectorTwo(-25.0, -4.0), VectorTwo(-17.0, -4.0), VectorTwo(-17.0, 4.0), VectorTwo(-25.0, 4.0))
    PocketEntities = tuple((SketchEntity(f'freecad:pocket-three-edge:{IndexValue}', GeometryKind.LINE, LineGeometry(PocketPoints[IndexValue], PocketPoints[(IndexValue + 1) % 4])) for IndexValue in range(4)))
    SketchFour = ReplaceData(SketchTemplate, id='freecad:sketch:Sketch003', name='Sketch003', entities=PocketEntities, parameter_ids=(), closed_profile_entity_ids=(tuple((ItemData.id for ItemData in PocketEntities)),))
    assert isinstance(FeatureThree.definition, ExtrusionFeature)
    FeatureFour = ReplaceData(FeatureThree, id='freecad:feature:Pocket002', name='Pocket002', order=3, sketch_id=SketchFour.id, input_feature_ids=(FeatureThree.id,), definition=ReplaceData(FeatureThree.definition, length=ParameterValue(4.0, ValueKind.LENGTH, 'mm')))
    ParametersFirstThree = tuple((ReplaceData(ItemData, value=ParameterValue(False, ValueKind.BOOLEAN) if ItemData.owner_id == FeatureThree.id and ItemData.attributes.get('freecad_path') == 'Visibility' else ItemData.value) for ItemData in SourceData.parameters))
    PocketValues = {'Label': ParameterValue('Pocket002', ValueKind.STRING), 'Length': ParameterValue(4.0, ValueKind.LENGTH, 'mm'), 'Visibility': ParameterValue(True, ValueKind.BOOLEAN)}
    ParametersFour = tuple((ReplaceData(ItemData, id=f"freecad:parameter:Pocket002:{ItemData.attributes['freecad_path']}", name=f"Pocket002.{ItemData.attributes['freecad_path']}", value=PocketValues.get(str(ItemData.attributes['freecad_path']), ItemData.value), owner_id=FeatureFour.id) for ItemData in SourceData.parameters if ItemData.owner_id == FeatureThree.id))
    FeatureFour = ReplaceData(FeatureFour, parameter_ids=tuple((ItemData.id for ItemData in ParametersFour)))
    return ReplaceData(SourceData, parameters=(*ParametersFirstThree, *ParametersFour), sketches=(*SourceData.sketches, SketchFour), feature_timeline=(*SourceData.feature_timeline, FeatureFour), bodies=(ReplaceData(SourceData.bodies[0], final_feature_id=FeatureFour.id),))

# keeps this focused behavior isolated so regressions remain immediately visible
def FreeCRRD() -> CadDocument:
    SourceData = FreecadRPD(bounds=(6.0, -9.0, 18.0, 9.0))
    SourceFeature = SourceData.feature_timeline[0]
    SelectionData = Selection('freecad:selection:Revolution:ReferenceAxis:0', 'Revolution.ReferenceAxis.V_Axis', (SelectionPathElement('native', SourceData.sketches[0].name, 'V_Axis'),), provenance=Provenance('freecad.fcstd', 'Revolution.ReferenceAxis.V_Axis'), attributes=FrozenMapping({'freecad_object': 'Revolution', 'freecad_property': 'ReferenceAxis', 'freecad_target': SourceData.sketches[0].name, 'freecad_subelement': 'V_Axis'}))
    FeatureData = ReplaceData(SourceFeature, name='Revolution', kind=FeatureKind.REVOLUTION, operation=BooleanOperation.CREATE, definition=NativeFeatureDefinition('freecad.fcstd', 'PartDesign::Revolution'), selection_ids=(SelectionData.id,), provenance=Provenance('freecad.fcstd', 'Revolution'), attributes=FrozenMapping({'freecad': {'type_id': 'PartDesign::Revolution'}}))
    ValuesData = (('AllowMultiFace', True, ValueKind.BOOLEAN, ''), ('Angle', 360.0, ValueKind.ANGLE, 'deg'), ('Angle2', 0.0, ValueKind.ANGLE, 'deg'), ('FuseOrder', 0, ValueKind.INTEGER, ''), ('FuzzyTolerance', -1.0, ValueKind.NUMBER, ''), ('Label', 'Revolution', ValueKind.STRING, ''), ('Label2', '', ValueKind.STRING, ''), ('Midplane', False, ValueKind.BOOLEAN, ''), ('Refine', True, ValueKind.BOOLEAN, ''), ('Reversed', False, ValueKind.BOOLEAN, ''), ('Suppressed', False, ValueKind.BOOLEAN, ''), ('Type', 0, ValueKind.INTEGER, ''), ('Visibility', True, ValueKind.BOOLEAN, ''))
    ParametersData = tuple((Parameter(f'freecad:parameter:Revolution:{PathValue}', f'Revolution.{PathValue}', ParameterValue(ValueData, KindData, UnitData), owner_id=FeatureData.id, attributes=FrozenMapping({'freecad_path': PathValue})) for PathValue, ValueData, KindData, UnitData in ValuesData))
    FeatureData = ReplaceData(FeatureData, parameter_ids=tuple((ItemData.id for ItemData in ParametersData)))
    return ReplaceData(SourceData, parameters=ParametersData, selections=(SelectionData,), feature_timeline=(FeatureData,), bodies=(ReplaceData(SourceData.bodies[0], final_feature_id=FeatureData.id),), capabilities=SourceData.capabilities | {Capability.SELECTIONS})

# keeps this focused behavior isolated so regressions remain immediately visible
def FreeCPGD() -> CadDocument:
    SourceData = FreeCPPD()
    PadFeature, PocketFeature = SourceData.feature_timeline
    SketchOne, SketchTwo = SourceData.sketches
    GroovePoints = (VectorTwo(-25.0, 0.0), VectorTwo(25.0, 0.0), VectorTwo(25.0, 3.0), VectorTwo(-25.0, 3.0))
    GrooveEntities = tuple((SketchEntity(f'freecad:groove-edge:{IndexValue}', GeometryKind.LINE, LineGeometry(GroovePoints[IndexValue], GroovePoints[(IndexValue + 1) % 4])) for IndexValue in range(4)))
    SketchTwo = ReplaceData(SketchTwo, entities=GrooveEntities, closed_profile_entity_ids=(tuple((ItemData.id for ItemData in GrooveEntities)),))
    SelectionData = Selection('freecad:selection:Groove:ReferenceAxis:0', 'Groove.ReferenceAxis.H_Axis', (SelectionPathElement('native', SketchTwo.name, 'H_Axis'),), provenance=Provenance('freecad.fcstd', 'Groove.ReferenceAxis.H_Axis'), attributes=FrozenMapping({'freecad_object': 'Groove', 'freecad_property': 'ReferenceAxis', 'freecad_target': SketchTwo.name, 'freecad_subelement': 'H_Axis'}))
    GrooveFeature = ReplaceData(PocketFeature, id='freecad:feature:Groove', name='Groove', kind=FeatureKind.REVOLUTION, operation=BooleanOperation.CUT, definition=NativeFeatureDefinition('freecad.fcstd', 'PartDesign::Groove'), selection_ids=(SelectionData.id,), provenance=Provenance('freecad.fcstd', 'Groove'), attributes=FrozenMapping({'freecad': {'type_id': 'PartDesign::Groove'}}))
    ValuesData = (('AllowMultiFace', True, ValueKind.BOOLEAN, ''), ('Angle', 360.0, ValueKind.ANGLE, 'deg'), ('Angle2', 0.0, ValueKind.ANGLE, 'deg'), ('FuzzyTolerance', -1.0, ValueKind.NUMBER, ''), ('Label', 'Groove', ValueKind.STRING, ''), ('Label2', '', ValueKind.STRING, ''), ('Midplane', False, ValueKind.BOOLEAN, ''), ('Refine', True, ValueKind.BOOLEAN, ''), ('Reversed', False, ValueKind.BOOLEAN, ''), ('Suppressed', False, ValueKind.BOOLEAN, ''), ('Type', 0, ValueKind.INTEGER, ''), ('Visibility', True, ValueKind.BOOLEAN, ''))
    GrooveParameters = tuple((Parameter(f'freecad:parameter:Groove:{PathValue}', f'Groove.{PathValue}', ParameterValue(ValueData, KindData, UnitData), owner_id=GrooveFeature.id, attributes=FrozenMapping({'freecad_path': PathValue})) for PathValue, ValueData, KindData, UnitData in ValuesData))
    GrooveFeature = ReplaceData(GrooveFeature, parameter_ids=tuple((ItemData.id for ItemData in GrooveParameters)))
    PadParameters = tuple((ItemData for ItemData in SourceData.parameters if ItemData.owner_id != PocketFeature.id))
    return ReplaceData(SourceData, parameters=(*PadParameters, *GrooveParameters), sketches=(SketchOne, SketchTwo), selections=(SelectionData,), feature_timeline=(PadFeature, GrooveFeature), bodies=(ReplaceData(SourceData.bodies[0], final_feature_id=GrooveFeature.id),), capabilities=SourceData.capabilities | {Capability.SELECTIONS})

# keeps this focused behavior isolated so regressions remain immediately visible
def TestPPFSCRPS() -> None:
    NativeDocument = b'legacy CATProduct'
    NativeDigest = Hashlib.sha256(NativeDocument).digest()
    SourceDoc = ReplaceData(Document(), brep_payloads=(BrepPayload('legacy-brep', 'parasolid', 'binary', 'SCH_3500040', Hashlib.sha256(b'PS\x00\x00legacy').hexdigest(), data=b'PS\x00\x00legacy', source_stream='Contents/Bodies/Partition', role=PayloadRole.BREP, file_extension='.x_b'), BrepPayload('legacy-mates', 'solidworks.mates', 'mate-list', 'solidworks.serialized-object-stream', Hashlib.sha256(b'legacy mates').hexdigest(), data=b'legacy mates', source_stream='Contents/Mates', role=PayloadRole.ASSEMBLY_STRUCTURE, file_extension='.bin'), BrepPayload('legacy-document', 'catia.v5.cfv2', 'native_document', 'CATProduct', Hashlib.sha256(NativeDocument).hexdigest(), data=NativeDocument, source_stream='V5_CFV2', role=PayloadRole.DOCUMENT, file_extension='.catproduct'), BrepPayload('legacy-binding', 'catia.v5.sha256', 'native_document_binding', 'sha256', Hashlib.sha256(NativeDigest).hexdigest(), data=NativeDigest, source_stream='V5_CFV2', role=PayloadRole.VERIFICATION, file_extension='.sha256')))
    Generated = BytesIO()
    WriteSldprt(SourceDoc, Generated)
    Archive = SldprtArchive.from_bytes(Generated.getvalue())
    Manifest = JsonLib.loads(Archive.require(StreamF))
    for Payload in Manifest['brep_payloads']['$tuple']:
        Payload.pop('role')
        Payload.pop('file_extension')
    StreamsA = Archive.streams
    StreamsA[StreamF] = JsonLib.dumps(Manifest).encode('utf-8')
    Legacy = BuildSldprt(StreamsA, file_id=Archive.file_id, format_version=Archive.format_version, signatures=ContainerSignatures(Generated.getvalue()))
    Restored = ReadSldprt(Legacy)
    Fields = {Payload.id: (Payload.role, Payload.file_extension, Payload.data) for Payload in Restored.brep_payloads}
    assert Fields == {'legacy-brep': (PayloadRole.BREP, '.x_b', b'PS\x00\x00legacy'), 'legacy-mates': (PayloadRole.ASSEMBLY_STRUCTURE, '.bin', b'legacy mates'), 'legacy-document': (PayloadRole.DOCUMENT, '.catproduct', NativeDocument), 'legacy-binding': (PayloadRole.VERIFICATION, '.sha256', NativeDigest)}
    Filtered = ReadSldprt(Legacy, include_brep=False)
    assert {Payload.id for Payload in Filtered.brep_payloads} == {'legacy-mates', 'legacy-document', 'legacy-binding'}

# keeps this focused behavior isolated so regressions remain immediately visible
def TestSSREAFR(TmpPath) -> None:
    SourceDoc = ReadSldprt(KSample)
    Fcstd = TmpPath / 'source.FCStd'
    Output = TmpPath / 'source.SLDPRT'
    WriteFreecad(SourceDoc, Fcstd)
    Restored = ReadFreecad(Fcstd)
    ResultInfo = WriteSldprt(Restored, Output)
    assert Output.read_bytes() == KSample.read_bytes()
    assert ResultInfo.metadata['mode'] == 'exact'
    assert ResultInfo.metadata['native_content'] == 'exact'
    assert ResultInfo.metadata['compatibility'] == 'native-exact'
    assert ResultInfo.metadata['neutral_edits_are_native'] is True
    assert ResultInfo.metadata['native_self_contained'] is True
    assert ResultInfo.metadata['referenced_files_written'] == 0

# keeps this focused behavior isolated so regressions remain immediately visible
def TestSSREACC(TmpPath) -> None:
    SourceDoc = ReadSldprt(KSample)
    Catpart = TmpPath / 'source.CATPart'
    Output = TmpPath / 'source.SLDPRT'
    WriteCatia(SourceDoc, Catpart, allow_non_native=True)
    Restored = ReadCatia(Catpart)
    ResultInfo = WriteSldprt(Restored, Output)
    assert Output.read_bytes() == KSample.read_bytes()
    assert ResultInfo.metadata['mode'] == 'exact'
    assert ResultInfo.metadata['compatibility'] == 'native-exact'

# keeps this focused behavior isolated so regressions remain immediately visible
def TestPSADACCE(TmpPath) -> None:
    SourceDoc = ReadSldprt(KAssembly)
    Catproduct = TmpPath / 'source.CATProduct'
    Output = TmpPath / 'source.SLDASM'
    WriteCatia(SourceDoc, Catproduct, allow_non_native=True)
    Restored = OpenDocument(Catproduct)
    WriteDocument(Restored, Output, allow_carrier=True)
    ReversedDocument = ReadSldprt(Output)
    assert ReversedDocument.brep_payloads == SourceDoc.brep_payloads
    assert ReversedDocument.assembly == SourceDoc.assembly

# keeps this focused behavior isolated so regressions remain immediately visible
@PytestLib.mark.parametrize('Change', ('capabilities', 'metadata', 'diagnostics'))
def TestSEDESR(Change: str) -> None:
    Document = ReadSldprt(KSample)
    if Change == 'capabilities':
        Changed = ReplaceData(Document, capabilities=Document.capabilities | {Capability.MATERIALS})
    elif Change == 'metadata':
        Changed = ReplaceData(Document, metadata=FrozenMapping({**Document.metadata, 'user.tag': 'changed'}))
    else:
        Changed = ReplaceData(Document, diagnostics=(*Document.diagnostics, Diagnostic('user.changed', 'changed', Severity.INFO)))
    Output = BytesIO()
    ResultInfo = WriteSldprt(Changed, Output)
    assert ResultInfo.metadata['mode'] != 'exact'
    assert Output.getvalue() != KSample.read_bytes()
    Restored = ReadSldprt(Output.getvalue())
    if Change == 'capabilities':
        assert Capability.MATERIALS in Restored.capabilities
    elif Change == 'metadata':
        assert Restored.metadata['user.tag'] == 'changed'
    else:
        assert Restored.diagnostics[-1].code == 'user.changed'

# keeps this focused behavior isolated so regressions remain immediately visible
def TestRSSDCFNER() -> None:
    Document = ReadSldprt(KSample)
    Feature = Document.feature_timeline[0]
    Changed = ReplaceData(Document, feature_timeline=(ReplaceData(Feature, name='Forged metadata cannot certify native semantics'), *Document.feature_timeline[1:]))
    Changed = ReplaceData(Changed, metadata=FrozenMapping({**Changed.metadata, 'solidworks_source_semantic_sha256': SemanticShaTwoFiveSix(Changed)}))
    Output = BytesIO()
    ResultInfo = WriteSldprt(Changed, Output)
    assert ResultInfo.metadata['mode'] == 'template'
    assert ResultInfo.metadata['compatibility'] == 'native-source-with-kit-neutral'
    assert Output.getvalue() != KSample.read_bytes()
    assert ReadSldprt(Output.getvalue()).feature_timeline[0].name == 'Forged metadata cannot certify native semantics'

# keeps this focused behavior isolated so regressions remain immediately visible
def CheckNeutral(Archive) -> None:
    assert Archive.format_version == 4
    assert Archive.require('Kit/Interchange')
    assert StreamK not in Archive.streams
    assert Archive.require(StreamA)
    assert Archive.require(StreamB)
    assert 'Contents/DisplayLists' not in Archive.streams
    assert 'Contents/Config-0-LWDATA' not in Archive.streams
    assert Archive.require('Contents/Config-0-ModelHeader') == Archive.require('Header2')
    assert Archive.require(StreamE).startswith(b'\x86<?xml')
    assert Archive.require(StreamD).startswith(b'<?xml')

# keeps this focused behavior isolated so regressions remain immediately visible
def CheckNeutralDoc(SourceDoc, Output, ResultInfo) -> None:
    Reread = ReadSldprt(Output)
    assert Reread.configurations == SourceDoc.configurations
    assert Reread.support_planes == SourceDoc.support_planes
    assert Reread.sketches == SourceDoc.sketches
    assert Reread.feature_timeline == SourceDoc.feature_timeline
    assert Reread.bodies == SourceDoc.bodies
    assert ResultInfo.metadata['mode'] == 'generated'
    assert ResultInfo.metadata['native_content'] == 'native-metadata'
    assert ResultInfo.metadata['compatibility'] == 'native-metadata-with-kit-neutral'
    for MetaKey in ('neutral_edits_are_native', 'vendor_loadable', 'native_geometry', 'native_history', 'native_assembly', 'native_self_contained'):
        assert ResultInfo.metadata[MetaKey] is False
    assert ResultInfo.metadata['referenced_files_written'] == 0
    assert [ItemValue.code for ItemValue in ResultInfo.diagnostics] == ['sldprt.neutral_write', 'sldprt.donor_declined']
    assert [ItemValue.severity for ItemValue in ResultInfo.diagnostics if ItemValue.code == 'sldprt.donor_declined'] == [Severity.WARNING]
    Replay = BytesIO()
    ReplayResult = WriteSldprt(Reread, Replay)
    assert Replay.getvalue() == Output.read_bytes()
    assert ReplayResult.metadata['compatibility'] == 'native-metadata-with-kit-neutral'
    assert ReplayResult.metadata['vendor_loadable'] is False

# keeps this focused behavior isolated so regressions remain immediately visible
def TestFDWSSC(TmpPath) -> None:
    SourceDoc = Document()
    Fcstd = TmpPath / 'neutral.FCStd'
    Output = TmpPath / 'neutral.SLDPRT'
    WriteFreecad(SourceDoc, Fcstd)
    Restored = ReadFreecad(Fcstd)
    with PytestLib.raises(SldprtFormatError, match='allow_non_native'):
        WriteSldprt(Restored, Output, allow_non_native=False)
    ResultInfo = WriteSldprt(Restored, Output)
    Archive = SldprtArchive.open(Output)
    CheckNeutral(Archive)
    Native = DecodeNativeModel(Archive.require(StreamE), Archive.require(StreamH), resolved_stream=StreamH)
    assert Native.diagnostics == ()
    assert [(ItemValue.name, ItemValue.configuration_id) for ItemValue in Native.configurations] == [('Default', 0)]
    assert [ItemValue.name for ItemValue in Native.features[-2:]] == ['Sketch1', 'Boss1']
    assert [(ItemValue.name, ItemValue.support_plane_id) for ItemValue in Native.sketches] == [('Sketch1', 2)]
    assert [(ItemValue.name, ItemValue.profile_id) for ItemValue in Native.operations] == [('Boss1', Native.sketches[0].object_id)]
    assert Output.read_bytes()[:1] not in {b'{', b'['}
    assert Output.read_bytes()[:4] != b'PK\x03\x04'
    CheckNeutralDoc(SourceDoc, Output, ResultInfo)

# keeps this focused behavior isolated so regressions remain immediately visible
def BuildStablePart():
    First = BytesIO()
    Second = BytesIO()
    WriteSldprt(Document(), First)
    WriteSldprt(Document(), Second)
    assert First.getvalue() == Second.getvalue()
    return SldprtArchive.from_bytes(First.getvalue())

# keeps this focused behavior isolated so regressions remain immediately visible
def CheckPartRels(Archive) -> None:
    ContentTypes = Archive.require(StreamC)
    Relationships = Archive.require(StreamJ)
    assert len(ContentTypes) == 556
    assert len(Relationships) == 597
    assert EtInfo.fromstring(ContentTypes).tag.endswith('Types')
    Targets = {ItemValue.attrib['Target'] for ItemValue in EtInfo.fromstring(Relationships) if ItemValue.tag.endswith('Relationship')}
    assert Targets == {'docProps/app.xml', 'docProps/core.xml', 'docProps/custom.xml'}
    assert Targets <= set(Archive.streams)
    assert len(Archive.require('docProps/app.xml')) == 570
    assert b'<dc:lastModifiedBy>Kit</dc:lastModifiedBy>' in Archive.require('docProps/core.xml')
    assert len(Archive.require('docProps/custom.xml')) == 853

# keeps this focused behavior isolated so regressions remain immediately visible
def CheckPartXml(Archive) -> None:
    Keywords = Archive.require(StreamE)
    Features = Archive.require(StreamD)
    assert Keywords.startswith(b'\x86<?xml version="1.0" encoding="UTF-8"?>\r\n<Keywords ')
    assert Keywords.endswith(b'</Keywords>\r\n')
    assert Features.startswith(b'<?xml version="1.0" encoding="UTF-8"?>\r\n<swSolidWorks ')
    assert Features.endswith(b'</swSolidWorks>\r\n')
    assert b' />' not in Keywords
    assert b' />' not in Features
    KeywordRoot = EtInfo.fromstring(Keywords[Keywords.find(b'<'):])
    FeaturesRoot = EtInfo.fromstring(Features)
    NativeElements = {ItemValue.tag.rsplit('}', 1)[-1]: ItemValue for ItemValue in FeaturesRoot.iter()}
    assert (KeywordRoot.tag, KeywordRoot.attrib['Name']) == ('Keywords', 'Part1')
    assert FeaturesRoot.tag.rsplit('}', 1)[-1] == 'swSolidWorks'
    assert FeaturesRoot.attrib == {'swObjCount': '3', 'swVersion': '18000'}
    assert KeywordRoot.attrib['id'] == NativeElements['swFile'].attrib['swCreationTime']
    assert NativeElements['swFile'].attrib['swPath'] == 'memory.sldprt'
    assert NativeElements['swModel'].attrib['swName'] == 'memory'
    assert NativeElements['swModel'].attrib['swConfigurationFlags'] == '-2143288960'
    assert NativeElements['swConfiguration'].attrib['swReference'] == 'Part1'
    assert NativeElements['swConfiguration'].attrib['swConfigurationNeedsUpdate'] == 'NO'
    ModelStamps = StructLib.unpack('<III', Archive.require('ModelStamps'))
    assert ModelStamps == (int(KeywordRoot.attrib['id']), int(NativeElements['swModel'].attrib['swLastModifiedStamp']), 101)

# keeps this focused behavior isolated so regressions remain immediately visible
def CheckDefaults(Archive) -> None:
    assert Archive.require('Contents/CnfgObjs') == bytes.fromhex('00000000fffeff00fffeff00')
    assert Archive.require('Contents/OleItems') == b'\x00' * 4
    assert Archive.require('Contents/eModelLic') == b'\x00' * 4
    assert len(Archive.require('Contents/CusProps')) == 102
    assert len(Archive.require('Contents/CMgrHdr2')) == 137
    assert len(Archive.require('_MO_VERSION_18000/History')) == 101
    assert Archive.require('_MO_VERSION_18000/Biography')

# keeps this focused behavior isolated so regressions remain immediately visible
def TestSLNPSAD() -> None:
    Archive = BuildStablePart()
    CheckPartRels(Archive)
    CheckPartXml(Archive)
    CheckDefaults(Archive)

# keeps this focused behavior isolated so regressions remain immediately visible
def TestSLBPWNBP() -> None:
    Marker = b'blank-part'
    SourceDoc = ReplaceData(DocumentWithoutSource(Document()), sketches=(), feature_timeline=(), bodies=(), brep_payloads=(BrepPayload('blank-part', 'kit', 'blank', '1', Hashlib.sha256(Marker).hexdigest(), data=Marker, role=PayloadRole.AUXILIARY),), capabilities=frozenset())
    Output = BytesIO()
    WriteSldprt(SourceDoc, Output)
    Archive = SldprtArchive.from_bytes(Output.getvalue())
    assert Archive.require(StreamI) == EncodeBPS()

# keeps this focused behavior isolated so regressions remain immediately visible
def TestSLNSFAEO() -> None:
    SourceDoc = DocumentWithoutSource(ReadSldprt(KRingInfo, include_brep=False))
    Output = BytesIO()
    WriteSldprt(SourceDoc, Output)
    Archive = SldprtArchive.from_bytes(Output.getvalue())
    assert StreamK not in Archive.streams
    Native = DecodeNativeModel(Archive.require(StreamE), Archive.require(StreamH), resolved_stream=StreamH)
    SystemIds = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 21, 22, 23, 24, 25}
    assert {ItemValue.object_id for ItemValue in Native.features if ItemValue.object_id <= 25} == SystemIds
    assert all((sum((ItemValue.object_id == ObjectId for ItemValue in Native.features)) == 1 for ObjectId in SystemIds))
    assert [(ItemValue.object_id, ItemValue.name) for ItemValue in Native.features if ItemValue.object_id > 25] == [(26, 'Sketch1'), (36, 'Boss-Extrude1')]
    SketchA = next((ItemValue for ItemValue in Native.features if ItemValue.object_id == 26))
    Extrusion = next((ItemValue for ItemValue in Native.features if ItemValue.object_id == 36))
    assert SketchA.properties == {'id': '26', 'Name': 'Sketch1', 'Dissectable': 'true'}
    assert [(ItemValue.name, ItemValue.source_text) for ItemValue in SketchA.dimensions] == [('D1', '<MOD-DIAM>90'), ('D2', '<MOD-DIAM>89')]
    assert Extrusion.properties == {'id': '36', 'Name': 'Boss-Extrude1', 'Type': 'Boss-Extrude'}
    assert [(ItemValue.name, ItemValue.source_text) for ItemValue in Extrusion.dimensions] == [('D1', '1')]
    Configurations = EtInfo.fromstring(Archive.require(StreamE)[Archive.require(StreamE).find(b'<'):])
    ConfigurationA = next((ItemValue for ItemValue in Configurations if ItemValue.tag == 'Configuration'))
    assert ConfigurationA.attrib['Material'] == 'Rubber'

# keeps this focused behavior isolated so regressions remain immediately visible
def TestSLNDSR() -> None:
    SourceDoc = Document()
    Feature = SourceDoc.feature_timeline[0]
    ItemValueA = ParameterValue(12.5, ValueKind.LENGTH, 'mm')
    ParameterA = Parameter('length', 'D1', ItemValueA, owner_id=Feature.id)
    Feature = ReplaceData(Feature, parameter_ids=(ParameterA.id,), operation=BooleanOperation.JOIN, definition=ExtrusionFeature(ItemValueA))
    SourceDoc = ReplaceData(SourceDoc, parameters=(ParameterA,), feature_timeline=(Feature,))
    Output = BytesIO()
    ResultInfo = WriteSldprt(SourceDoc, Output)
    Archive = SldprtArchive.from_bytes(Output.getvalue())
    Native = DecodeNativeModel(Archive.require(StreamE), Archive.require(StreamH), resolved_stream=StreamH)
    Operation = next((ItemValue for ItemValue in Native.operations if ItemValue.name == Feature.name))
    Dimension = next((Dimension for NativeFeature in Native.features if NativeFeature.object_id == Operation.object_id for Dimension in NativeFeature.dimensions if Dimension.name == 'D1'))
    assert Operation.length_mm == PytestLib.approx(12.5)
    assert Operation.operation_code == 0
    assert Operation.termination_code == 0
    assert Dimension.native_value == PytestLib.approx(0.0125)
    assert Dimension.native_role == 'driving'
    assert Capability.PARAMETERS in ResultInfo.native_capabilities
    assert ResultInfo.vendor_loadable is False

# keeps this focused behavior isolated so regressions remain immediately visible
def TestSLNCLAA() -> None:
    SourceDoc = ReplaceData(Document(), configurations=(Configuration('config:default', 'Default'), Configuration('config:machined', 'Machined', True)))
    Output = BytesIO()
    ResultInfo = WriteSldprt(SourceDoc, Output)
    Archive = SldprtArchive.from_bytes(Output.getvalue())
    assert [NameText for NameText in Archive.streams if NameText.startswith('Contents/Config-') and NameText.endswith('-ResolvedFeatures')] == []
    assert EncodeNativePart(DocumentWithoutSource(SourceDoc), 'memory').configuration_lanes == ()
    assert Archive.require(StreamH)
    Features = EtInfo.fromstring(Archive.require(StreamD))
    Configurations = [ItemValue for ItemValue in Features.iter() if ItemValue.tag.rsplit('}', 1)[-1] == 'swConfiguration']
    assert [ItemValue.attrib['swName'] for ItemValue in Configurations] == ['Default', 'Machined']
    assert [ItemValue.attrib['swMostRecentConfiguration'] for ItemValue in Configurations] == ['NO', 'YES']
    assert {ItemValue.attrib['swConfigurationNeedsUpdate'] for ItemValue in Configurations} == {'NO'}
    assert Capability.CONFIGURATIONS in ResultInfo.native_capabilities

# keeps this focused behavior isolated so regressions remain immediately visible
def TestSLNRMR() -> None:
    SourceDoc = Document()
    Points = (VectorTwo(0.0, 0.0), VectorTwo(20.0, 0.0), VectorTwo(20.0, 10.0), VectorTwo(0.0, 10.0))
    Entities = tuple((SketchEntity(f'edge:{Index}', GeometryKind.LINE, LineGeometry(Points[Index], Points[(Index + 1) % len(Points)])) for Index in range(len(Points))))
    SketchA = Sketch(SourceDoc.sketches[0].id, SourceDoc.sketches[0].name, SourceDoc.sketches[0].support_plane_id, Entities, closed_profile_entity_ids=(tuple((ItemValue.id for ItemValue in Entities)),))
    SourceDoc = ReplaceData(SourceDoc, sketches=(SketchA,))
    Output = BytesIO()
    WriteSldprt(SourceDoc, Output)
    Archive = SldprtArchive.from_bytes(Output.getvalue())
    Native = DecodeNativeModel(Archive.require(StreamE), Archive.require(StreamH), resolved_stream=StreamH)
    Decoded = next((ItemValue for ItemValue in Native.sketches if ItemValue.name == SketchA.name))
    assert len(Decoded.markers) == 8
    assert [(ItemValue.kind, ItemValue.coordinates) for ItemValue in Decoded.profiles] == [('rectangle', (0.0, 0.0, 20.0, 10.0))]

# keeps this focused behavior isolated so regressions remain immediately visible
def TestSLNRBRAP() -> None:
    SourceDoc = Document()
    Points = (VectorTwo(-30.0, -15.0), VectorTwo(30.0, -15.0), VectorTwo(30.0, 15.0), VectorTwo(-30.0, 15.0))
    Entities = tuple((SketchEntity(f'edge:{Index}', GeometryKind.LINE, LineGeometry(Points[Index], Points[(Index + 1) % len(Points)])) for Index in range(len(Points))))
    SketchA = Sketch(SourceDoc.sketches[0].id, SourceDoc.sketches[0].name, SourceDoc.sketches[0].support_plane_id, Entities, closed_profile_entity_ids=(tuple((ItemValue.id for ItemValue in Entities)),))
    Length = ParameterValue(12.0, ValueKind.LENGTH, 'mm')
    Feature = ReplaceData(SourceDoc.feature_timeline[0], name='Boss-Extrude1', operation=BooleanOperation.JOIN, definition=ExtrusionFeature(Length))
    SourceDoc = ReplaceData(SourceDoc, sketches=(SketchA,), feature_timeline=(Feature,))
    Output = BytesIO()
    WriteSldprt(SourceDoc, Output)
    Archive = SldprtArchive.from_bytes(Output.getvalue())
    assert StreamK in Archive.streams
    assert StreamH not in Archive.streams
    assert Archive.require(StreamA)
    assert Archive.require(StreamB)
    Resolved = Archive.require(StreamK)
    Native = DecodeNativeModel(Archive.require(StreamE), Resolved, resolved_stream=StreamK)
    assert Native.diagnostics == ()
    assert Native.sketches[0].object_id == 26
    assert Native.sketches[0].name == 'Sketch1'
    assert Native.sketches[0].profiles[0].coordinates == (-30.0, -15.0, 30.0, 15.0)
    assert Native.operations[0].object_id == 32
    assert Native.operations[0].name == 'Boss-Extrude1'
    assert Native.operations[0].profile_id == Native.sketches[0].object_id
    assert Native.operations[0].length_mm == PytestLib.approx(12.0)
    assert Native.operations[0].termination_code == Condition
    assert Native.operations[0].native_stream == StreamK
    Restored = ReadSldprt(Output.getvalue())
    assert Restored.sketches[0].entities == SketchA.entities
    assert Restored.feature_timeline[0].definition == Feature.definition

# keeps this focused behavior isolated so regressions remain immediately visible
def CheckRectNative(Archive, ResultInfo) -> None:
    assert StreamK in Archive.streams
    assert StreamH not in Archive.streams
    assert Archive.require(StreamA)
    assert Archive.require(StreamB)
    assert StreamI not in Archive.streams
    Native = DecodeNativeModel(Archive.require(StreamE), Archive.require(StreamK), resolved_stream=StreamK)
    Transfers = {ItemValue.capability: ItemValue for ItemValue in ResultInfo.transfers}
    assert ResultInfo.application_usable is True
    assert ResultInfo.vendor_loadable is True
    assert ResultInfo.near_lossless is True
    assert ResultInfo.requirements == ()
    assert Native.sketches[0].object_id == 26
    assert Native.sketches[0].profiles[0].coordinates == PytestLib.approx((-30.0, -15.0, 30.0, 15.0))
    assert Native.operations[0].object_id == 32
    assert Native.operations[0].length_mm == PytestLib.approx(12.0)
    assert Native.operations[0].termination_code == Condition
    for CapabilityA in (Capability.PARAMETERS, Capability.PARAMETRIC_HISTORY, Capability.EDITABLE_SKETCHES, Capability.BREP):
        assert Transfers[CapabilityA].mode.value == 'native'
    for CapabilityA in (Capability.NATIVE_PAYLOADS, Capability.PROVENANCE, Capability.ROUNDTRIP_METADATA):
        assert Transfers[CapabilityA].mode.value == 'carrier'
        assert Transfers[CapabilityA].carrier_reason.value == 'target_unsupported'

# keeps this focused behavior isolated so regressions remain immediately visible
def TestFRPWNPSP(TmpPath: FilePath) -> None:
    SourceDoc = FreecadRPD()
    TargetDoc = TmpPath / 'FreeCADRectanglePad.SLDPRT'
    ResultInfo = WriteDocument(SourceDoc, TargetDoc, allow_carrier=False)
    DataValue = TargetDoc.read_bytes()
    CheckRectNative(SldprtArchive.from_bytes(DataValue), ResultInfo)
    Restored = ReadSldprt(DataValue)
    assert Restored.feature_timeline[0].definition == SourceDoc.feature_timeline[0].definition
    Replay = BytesIO()
    ReplayResult = WriteSldprt(Restored, Replay)
    assert Replay.getvalue() == DataValue
    assert ReplayResult.application_usable is True
    assert ReplayResult.vendor_loadable is True

# keeps this focused behavior isolated so regressions remain immediately visible
@PytestLib.mark.skipif(not KFreeCadBoxCorpus.is_file(), reason='box corpus unavailable')
def TestFCBWNPSWP(TmpPath: FilePath) -> None:
    SourceData = ReadFreecad(KFreeCadBoxCorpus)
    TargetPath = TmpPath / 'FreeCadBox.SLDPRT'
    ResultData = WriteDocument(SourceData, TargetPath, allow_carrier=True)
    ArchiveData = SldprtArchive.from_bytes(TargetPath.read_bytes())
    NativeData = DecodeNativeModel(ArchiveData.require(StreamE), ArchiveData.require(StreamK), ArchiveData.require(StreamB), resolved_stream=StreamK)
    assert ResultData.application_usable is True
    assert ResultData.vendor_loadable is True
    assert ResultData.near_lossless is True
    assert ResultData.requirements == ()
    assert len(NativeData.sketches) == 1
    assert NativeData.sketches[0].object_id == 26
    assert NativeData.sketches[0].profiles[0].coordinates == PytestLib.approx((0.0, 0.0, 10.0, 10.0))
    assert [(ItemData.name, ItemData.value_mm) for ItemData in NativeData.sketches[0].dimensions] == [('D1', 10.0), ('D2', 10.0)]
    assert len(NativeData.operations) == 1
    assert NativeData.operations[0].object_id == 34
    assert NativeData.operations[0].name == 'Boss-Extrude1'
    assert NativeData.operations[0].profile_id == 26
    assert NativeData.operations[0].length_mm == PytestLib.approx(10.0)
    assert NativeData.operations[0].termination_code == Condition
    LengthParameter = next((ItemData for ItemData in SourceData.parameters if ItemData.attributes.get('freecad_path') == 'Length'))
    MismatchedSource = ReplaceData(SourceData, parameters=tuple((ReplaceData(ItemData, value=ParameterValue(12.0, ValueKind.LENGTH, 'mm')) if ItemData.id == LengthParameter.id else ItemData for ItemData in SourceData.parameters)))
    assert not HasVendorPartEncoding(MismatchedSource)

# keeps this focused behavior isolated so regressions remain immediately visible
@PytestLib.mark.skipif(not KFreeCadCylCorpus.is_file(), reason='cylinder corpus unavailable')
def TestFCCWNPSWP(TmpPath: FilePath) -> None:
    SourceData = ReadFreecad(KFreeCadCylCorpus)
    TargetPath = TmpPath / 'FreeCadCylinder.SLDPRT'
    ResultData = WriteDocument(SourceData, TargetPath, allow_carrier=True)
    ArchiveData = SldprtArchive.from_bytes(TargetPath.read_bytes())
    NativeData = DecodeNativeModel(ArchiveData.require(StreamE), ArchiveData.require(StreamK), ArchiveData.require(StreamB), resolved_stream=StreamK)
    assert ResultData.application_usable is True
    assert ResultData.vendor_loadable is True
    assert ResultData.near_lossless is True
    assert ResultData.requirements == ()
    assert len(NativeData.sketches) == 1
    assert NativeData.sketches[0].object_id == 26
    assert NativeData.sketches[0].profiles[0].coordinates == PytestLib.approx((0.0, 0.0, 5.0))
    assert tuple(((ItemData.name, ItemData.value_mm, ItemData.kind, ItemData.native_role) for ItemData in NativeData.sketches[0].dimensions)) == (('D1', 10.0, 'diameter', 'driving'),)
    assert tuple((ItemData.kind for ItemData in NativeData.sketches[0].constraints)) == ('diameter',)
    assert len(NativeData.operations) == 1
    assert NativeData.operations[0].object_id == 33
    assert NativeData.operations[0].name == 'Boss-Extrude1'
    assert NativeData.operations[0].profile_id == 26
    assert NativeData.operations[0].length_mm == PytestLib.approx(10.0)
    assert NativeData.operations[0].termination_code == Condition

# keeps this focused behavior isolated so regressions remain immediately visible
def TestVPPRAUFF() -> None:
    SourceData = FreecadRPD()
    assert HasVendorPartEncoding(SourceData)
    UnsupportedFeature = ReplaceData(SourceData.feature_timeline[0], kind=FeatureKind.LOFT, definition=NativeFeatureDefinition('freecad.fcstd', 'PartDesign::Loft', {}))
    UnsupportedData = ReplaceData(SourceData, feature_timeline=(UnsupportedFeature,))
    assert not HasVendorPartEncoding(UnsupportedData)

# keeps this focused behavior isolated so regressions remain immediately visible
def FreeCDV(SourceData: CadDocument, VariantName: str) -> CadDocument:
    FeatureData = SourceData.feature_timeline[0]
    DefinitionData = ReplaceData(FeatureData.definition, reversed=VariantName == 'reversed', symmetric=VariantName == 'midplane')
    ParametersData = tuple((ReplaceData(ItemData, value=ParameterValue(2 if ItemData.attributes.get('freecad_path') == 'SideType' and VariantName == 'midplane' else 0 if ItemData.attributes.get('freecad_path') == 'SideType' else VariantName == ItemData.attributes.get('freecad_path', '').casefold(), ValueKind.INTEGER if ItemData.attributes.get('freecad_path') == 'SideType' else ValueKind.BOOLEAN)) if ItemData.attributes.get('freecad_path') in {'Midplane', 'Reversed', 'SideType'} else ItemData for ItemData in SourceData.parameters))
    return ReplaceData(SourceData, parameters=ParametersData, feature_timeline=(ReplaceData(FeatureData, definition=DefinitionData),))

# keeps this focused behavior isolated so regressions remain immediately visible
@PytestLib.mark.parametrize(('VariantName', 'DirectionCode', 'TerminationCode'), (('reversed', 1, 0), ('midplane', 0, 6)))
def TestFRPWNDV(VariantName: str, DirectionCode: int, TerminationCode: int) -> None:
    SourceData = FreeCDV(FreecadRPD(depth=18.0), VariantName)
    OutputData = BytesIO()
    ResultData = WriteSldprt(SourceData, OutputData)
    ArchiveData = SldprtArchive.from_bytes(OutputData.getvalue())
    NativeData = DecodeNativeModel(ArchiveData.require(StreamE), ArchiveData.require(StreamK), resolved_stream=StreamK)
    OperationData = NativeData.operations[0]
    assert ResultData.vendor_loadable is True
    assert OperationData.direction_code == DirectionCode
    assert OperationData.termination_code == TerminationCode
    assert OperationData.length_mm == PytestLib.approx(18.0)
    assert OperationData.depth_copies[0].value_mm == PytestLib.approx(18.0)

# keeps this focused behavior isolated so regressions remain immediately visible
def TestFPPWTENF() -> None:
    SourceData = FreeCPPD()
    OutputData = BytesIO()
    ResultData = WriteSldprt(SourceData, OutputData)
    ArchiveData = SldprtArchive.from_bytes(OutputData.getvalue())
    FeatureData = LocateFeatures(ArchiveData.require(StreamK))
    assert ResultData.vendor_loadable is True
    assert StreamH not in ArchiveData.streams
    ConfigurationData = ArchiveData.require(StreamB)
    assert len(ConfigurationData) == 25300
    AtomDefinition = b'\xff\xff\x01\x00\x08\x00moAtom_c'
    AtomPos = ConfigurationData.index(AtomDefinition)
    assert StructLib.unpack_from('<II', ConfigurationData, AtomPos - 8) == (102, 2)
    HeaderData = ArchiveData.require('Contents/Config-0-ModelHeader')
    CStringName = b'moCStringHandle_c'
    CStringEnd = HeaderData.index(CStringName) + len(CStringName)
    assert HeaderData[CStringEnd + 4:CStringEnd + 6] == StructLib.pack('<H', 32843)
    assert bytes.fromhex('f65a1a69') + StructLib.pack('<IHI', 41, 0, 110) in HeaderData
    assert [(ItemData.feature_id, ItemData.name, ItemData.kind, ItemData.sketch_id, ItemData.reversed, ItemData.depth_mm, ItemData.bounds_mm) for ItemData in FeatureData] == [(32, 'Boss-Extrude1', 'boss', 26, False, PytestLib.approx(15.0), PytestLib.approx((-30.0, -20.0, 30.0, 20.0))), (40, 'Cut-Extrude1', 'cut', 33, True, PytestLib.approx(6.0), PytestLib.approx((-10.0, -8.0, 10.0, 8.0)))]
    assert ResultData.application_usable is True
    assert ResultData.metadata['native_brep'] == 'feature-rebuilt'
    assert ResultData.metadata['native_geometry'] is True
    TransferData = {ItemData.capability: ItemData.mode.value for ItemData in ResultData.transfers}
    for CapabilityValue in (Capability.PARAMETERS, Capability.PARAMETRIC_HISTORY, Capability.EDITABLE_SKETCHES, Capability.BODY_STRUCTURE):
        assert TransferData[CapabilityValue] == 'native'

# keeps this focused behavior isolated so regressions remain immediately visible
def TestFPPWTENB() -> None:
    SourceData = FreeCPPD(Join=True)
    OutputData = BytesIO()
    ResultData = WriteSldprt(SourceData, OutputData)
    ArchiveData = SldprtArchive.from_bytes(OutputData.getvalue())
    ResolvedData = ArchiveData.require(StreamK)
    FeatureData = LocateFeatures(ResolvedData)
    NativeData = DecodeNativeModel(ArchiveData.require(StreamE), ResolvedData, ArchiveData.require(StreamB), resolved_stream=StreamK)
    assert ResultData.vendor_loadable is True
    assert ResultData.application_usable is True
    assert ResultData.metadata['native_brep'] == 'feature-rebuilt'
    assert StreamH not in ArchiveData.streams
    assert len(ResolvedData) == 16474
    assert [(ItemData.feature_id, ItemData.name, ItemData.kind, ItemData.sketch_id, ItemData.depth_mm, ItemData.bounds_mm) for ItemData in FeatureData] == [(32, 'Boss-Extrude1', 'boss', 26, PytestLib.approx(15.0), PytestLib.approx((-30.0, -20.0, 30.0, 20.0))), (40, 'Boss-Extrude2', 'boss', 33, PytestLib.approx(25.0), PytestLib.approx((-10.0, -8.0, 10.0, 8.0)))]
    assert [ItemData.kind for ItemData in NativeData.operations] == ['join', 'join']
    assert [ItemData.object_id for ItemData in NativeData.operations] == [32, 40]
    TransferData = {ItemData.capability: ItemData.mode.value for ItemData in ResultData.transfers}
    for CapabilityValue in (Capability.BREP, Capability.PARAMETERS, Capability.PARAMETRIC_HISTORY, Capability.EDITABLE_SKETCHES, Capability.BODY_STRUCTURE):
        assert TransferData[CapabilityValue] == 'native'

# keeps this focused behavior isolated so regressions remain immediately visible
def TestFPGWENRC() -> None:
    SourceData = FreeCPGD()
    OutputData = BytesIO()
    ResultData = WriteSldprt(SourceData, OutputData)
    ArchiveData = SldprtArchive.from_bytes(OutputData.getvalue())
    ResolvedData = ArchiveData.require(StreamK)
    FeatureData = LocateFeatures(ResolvedData)
    NativeData = DecodeNativeModel(ArchiveData.require(StreamE), ResolvedData, ArchiveData.require(StreamB), resolved_stream=StreamK)
    assert ResultData.vendor_loadable is True
    assert ResultData.application_usable is True
    assert ResultData.metadata['native_brep'] == 'feature-rebuilt'
    assert StreamH not in ArchiveData.streams
    assert len(ResolvedData) == 17713
    assert [(ItemData.feature_id, ItemData.name, ItemData.kind, ItemData.sketch_id, ItemData.depth_mm, ItemData.angle_radians, ItemData.bounds_mm) for ItemData in FeatureData] == [(32, 'Boss-Extrude1', 'boss', 26, PytestLib.approx(15.0), None, PytestLib.approx((-30.0, -20.0, 30.0, 20.0))), (39, 'Cut-Revolve1', 'revolve-cut', 33, None, PytestLib.approx(2.0 * 3.141592653589793), PytestLib.approx((-25.0, 0.0, 25.0, 3.0)))]
    assert [ItemData.kind for ItemData in NativeData.operations] == ['join', 'revolve_cut']
    assert [ItemData.object_id for ItemData in NativeData.operations] == [32, 39]
    ConfigurationData = ArchiveData.require(StreamB)
    AnnotationTag = EncodeClassDefinition('moAnnotationView_c', 1)
    AnnotationStart = ConfigurationData.index(AnnotationTag)
    assert StructLib.unpack_from('<H', ConfigurationData, AnnotationStart - 2)[0] == 2
    assert '*Top'.encode('utf-16-le') in ConfigurationData
    assert '*Right'.encode('utf-16-le') in ConfigurationData
    TransferData = {ItemData.capability: ItemData.mode.value for ItemData in ResultData.transfers}
    for CapabilityValue in (Capability.BREP, Capability.PARAMETERS, Capability.PARAMETRIC_HISTORY, Capability.EDITABLE_SKETCHES, Capability.BODY_STRUCTURE, Capability.SELECTIONS):
        assert TransferData[CapabilityValue] == 'native'

# keeps this focused behavior isolated so regressions remain immediately visible
def TestFPTAPWDNC() -> None:
    SourceData = FreeCPPD(ThroughAll=True)
    OutputData = BytesIO()
    ResultData = WriteSldprt(SourceData, OutputData)
    ArchiveData = SldprtArchive.from_bytes(OutputData.getvalue())
    FeatureData = LocateFeatures(ArchiveData.require(StreamK))
    NativeData = DecodeNativeModel(ArchiveData.require(StreamE), ArchiveData.require(StreamK), resolved_stream=StreamK)
    assert ResultData.vendor_loadable is True
    assert ResultData.application_usable is True
    assert ResultData.metadata['native_brep'] == 'feature-rebuilt'
    assert ResultData.metadata['native_geometry'] is True
    assert len(ArchiveData.require(StreamK)) == 14693
    assert [ItemData.depth_mm for ItemData in FeatureData] == [PytestLib.approx(15.0), None]
    assert [ItemData.termination_code for ItemData in NativeData.operations] == [0, 1]
    assert [ItemData.direction_code for ItemData in NativeData.operations] == [0, 1]
    assert [ItemData.length_mm for ItemData in NativeData.operations] == [PytestLib.approx(15.0), None]
    TransferData = {ItemData.capability: ItemData.mode.value for ItemData in ResultData.transfers}
    for CapabilityValue in (Capability.PARAMETERS, Capability.PARAMETRIC_HISTORY, Capability.EDITABLE_SKETCHES, Capability.BODY_STRUCTURE):
        assert TransferData[CapabilityValue] == 'native'

# keeps this focused behavior isolated so regressions remain immediately visible
def TestFPTPWTENF() -> None:
    SourceData = FreeCPTPDA()
    OutputData = BytesIO()
    ResultData = WriteSldprt(SourceData, OutputData)
    ArchiveData = SldprtArchive.from_bytes(OutputData.getvalue())
    FeatureData = LocateFeatures(ArchiveData.require(StreamK))
    NativeData = DecodeNativeModel(ArchiveData.require(StreamE), ArchiveData.require(StreamK), ArchiveData.require(StreamB), resolved_stream=StreamK)
    assert ResultData.vendor_loadable is True
    assert ResultData.application_usable is True
    assert ResultData.metadata['native_brep'] == 'feature-rebuilt'
    assert StreamH not in ArchiveData.streams
    assert len(ArchiveData.require(StreamK)) == 21780
    assert [(ItemData.feature_id, ItemData.name, ItemData.kind, ItemData.sketch_id, ItemData.depth_mm, ItemData.bounds_mm) for ItemData in FeatureData] == [(32, 'Boss-Extrude1', 'boss', 26, PytestLib.approx(15.0), PytestLib.approx((-30.0, -20.0, 30.0, 20.0))), (40, 'Cut-Extrude1', 'cut', 33, PytestLib.approx(6.0), PytestLib.approx((-10.0, -8.0, 10.0, 8.0))), (47, 'Cut-Extrude2', 'cut', 41, PytestLib.approx(5.0), PytestLib.approx((15.0, -5.0, 25.0, 5.0)))]
    assert [ItemData.object_id for ItemData in NativeData.operations] == [32, 40, 47]
    assert [ItemData.length_mm for ItemData in NativeData.operations] == [PytestLib.approx(15.0), PytestLib.approx(6.0), PytestLib.approx(5.0)]
    ManagerData = ArchiveData.require(StreamA)
    assert StructLib.pack('<IIIII', 2, 103, 102, 102, 101) in ManagerData
    ConfigurationData = ArchiveData.require(StreamB)
    AtomDefinition = b'\xff\xff\x01\x00\x08\x00moAtom_c'
    AtomPos = ConfigurationData.index(AtomDefinition)
    assert StructLib.unpack_from('<II', ConfigurationData, AtomPos - 8) == (103, 3)
    TransferData = {ItemData.capability: ItemData.mode.value for ItemData in ResultData.transfers}
    for CapabilityValue in (Capability.BREP, Capability.PARAMETERS, Capability.PARAMETRIC_HISTORY, Capability.EDITABLE_SKETCHES, Capability.BODY_STRUCTURE):
        assert TransferData[CapabilityValue] == 'native'

# keeps this focused behavior isolated so regressions remain immediately visible
def TestFPTPWFENF() -> None:
    SourceData = FreeCPTPD()
    OutputData = BytesIO()
    ResultData = WriteSldprt(SourceData, OutputData)
    ArchiveData = SldprtArchive.from_bytes(OutputData.getvalue())
    FeatureData = LocateFeatures(ArchiveData.require(StreamK))
    NativeData = DecodeNativeModel(ArchiveData.require(StreamE), ArchiveData.require(StreamK), ArchiveData.require(StreamB), resolved_stream=StreamK)
    assert ResultData.vendor_loadable is True
    assert ResultData.application_usable is True
    assert ResultData.metadata['native_brep'] == 'feature-rebuilt'
    assert StreamH not in ArchiveData.streams
    assert len(ArchiveData.require(StreamK)) == 27092
    assert [(ItemData.feature_id, ItemData.name, ItemData.kind, ItemData.sketch_id, ItemData.depth_mm, ItemData.bounds_mm) for ItemData in FeatureData] == [(32, 'Boss-Extrude1', 'boss', 26, PytestLib.approx(15.0), PytestLib.approx((-30.0, -20.0, 30.0, 20.0))), (40, 'Cut-Extrude1', 'cut', 33, PytestLib.approx(6.0), PytestLib.approx((-10.0, -8.0, 10.0, 8.0))), (47, 'Cut-Extrude2', 'cut', 41, PytestLib.approx(5.0), PytestLib.approx((15.0, -5.0, 25.0, 5.0))), (54, 'Cut-Extrude3', 'cut', 48, PytestLib.approx(4.0), PytestLib.approx((-25.0, -4.0, -17.0, 4.0)))]
    assert [ItemData.object_id for ItemData in NativeData.operations] == [32, 40, 47, 54]
    assert [ItemData.length_mm for ItemData in NativeData.operations] == [PytestLib.approx(15.0), PytestLib.approx(6.0), PytestLib.approx(5.0), PytestLib.approx(4.0)]
    ManagerData = ArchiveData.require(StreamA)
    assert StructLib.pack('<IIIIIII', 3, 104, 103, 103, 102, 102, 101) in ManagerData
    ConfigurationData = ArchiveData.require(StreamB)
    AtomDefinition = b'\xff\xff\x01\x00\x08\x00moAtom_c'
    AtomPos = ConfigurationData.index(AtomDefinition)
    assert StructLib.unpack_from('<II', ConfigurationData, AtomPos - 8) == (104, 4)
    TransferData = {ItemData.capability: ItemData.mode.value for ItemData in ResultData.transfers}
    for CapabilityValue in (Capability.BREP, Capability.PARAMETERS, Capability.PARAMETRIC_HISTORY, Capability.EDITABLE_SKETCHES, Capability.BODY_STRUCTURE):
        assert TransferData[CapabilityValue] == 'native'

# keeps this focused behavior isolated so regressions remain immediately visible
def CheckRevCore(ResultData, ArchiveData, FeatureData, NativeData) -> None:
    assert ResultData.vendor_loadable is True
    assert ResultData.application_usable is True
    assert ResultData.metadata['native_brep'] == 'feature-rebuilt'
    assert StreamH not in ArchiveData.streams
    assert len(ArchiveData.require(StreamK)) == 12135
    assert len(FeatureData) == 1
    assert (FeatureData[0].feature_id, FeatureData[0].name, FeatureData[0].kind, FeatureData[0].sketch_id) == (31, 'Revolve1', 'revolve', 26)
    assert FeatureData[0].angle_radians == PytestLib.approx(2.0 * 3.141592653589793)
    assert FeatureData[0].bounds_mm == PytestLib.approx((6.0, -9.0, 18.0, 9.0))
    assert len(NativeData.operations) == 1
    assert NativeData.operations[0].object_id == 31
    assert NativeData.operations[0].kind == 'revolve_join'
    assert NativeData.operations[0].angle_degrees == PytestLib.approx(360.0)
    assert NativeAxisBindings(NativeData) == frozenset({(31, 26, 'V_Axis')})

# keeps this focused behavior isolated so regressions remain immediately visible
def CheckRevHead(ArchiveData, NativeData) -> None:
    HeaderData = ArchiveData.require('Contents/Config-0-ModelHeader')
    assert DecodeNativeModelHeader(HeaderData).objects[-2:] == ((26, 'Sketch1'), (31, 'Revolve1'))
    ResolvedData = ArchiveData.require(StreamK)
    SketchCreatedStamp = StructLib.unpack_from('<I', ResolvedData, 767)[0]
    SketchModifiedStamp = StructLib.unpack_from('<I', ResolvedData, 886)[0]
    assert (SketchCreatedStamp, SketchModifiedStamp) == (1785797027, 1785797028)
    SerializedCreated = b'\xff\xfe\xff\x07' + 'Created'.encode('utf-16le')
    SerializedModified = b'\xff\xfe\xff\x08' + 'Modified'.encode('utf-16le')
    SerializedSketch = b'\xff\xfe\xff\x07' + 'Sketch1'.encode('utf-16le')
    SerializedRevolve = b'\xff\xfe\xff\x08' + 'Revolve1'.encode('utf-16le')
    assert bytes.fromhex('088002000a80') + StructLib.pack('<I', 0) + b'\x00\x00' + StructLib.pack('<I', SketchCreatedStamp) + SerializedCreated + bytes.fromhex('0a80') + StructLib.pack('<I', 1) + b'\x00\x00' + StructLib.pack('<I', SketchModifiedStamp) + SerializedModified + StructLib.pack('<I', 26) + SerializedSketch in HeaderData
    assert bytes.fromhex('088001000a80') + StructLib.pack('<I', 0) + b'\x00\x00' + StructLib.pack('<I', SketchModifiedStamp) + SerializedCreated + StructLib.pack('<I', 31) + SerializedRevolve in HeaderData

# keeps this focused behavior isolated so regressions remain immediately visible
def CheckRevolveCfg(ArchiveData, ResultData) -> None:
    ConfigurationData = ArchiveData.require(StreamB)
    AtomDefinition = b'\xff\xff\x01\x00\x08\x00moAtom_c'
    AtomPos = ConfigurationData.index(AtomDefinition)
    assert StructLib.unpack_from('<II', ConfigurationData, AtomPos - 8) == (101, 1)
    TransferData = {ItemData.capability: ItemData.mode.value for ItemData in ResultData.transfers}
    for CapabilityValue in (Capability.BREP, Capability.PARAMETERS, Capability.PARAMETRIC_HISTORY, Capability.EDITABLE_SKETCHES, Capability.BODY_STRUCTURE, Capability.SELECTIONS):
        assert TransferData[CapabilityValue] == 'native'

# keeps this focused behavior isolated so regressions remain immediately visible
def TestFFRWENRB() -> None:
    SourceData = FreeCRRD()
    OutputData = BytesIO()
    ResultData = WriteSldprt(SourceData, OutputData)
    ArchiveData = SldprtArchive.from_bytes(OutputData.getvalue())
    FeatureData = LocateFeatures(ArchiveData.require(StreamK))
    NativeData = DecodeNativeModel(ArchiveData.require(StreamE), ArchiveData.require(StreamK), ArchiveData.require(StreamB), resolved_stream=StreamK)
    CheckRevCore(ResultData, ArchiveData, FeatureData, NativeData)
    CheckRevHead(ArchiveData, NativeData)
    CheckRevolveCfg(ArchiveData, ResultData)

# keeps this focused behavior isolated so regressions remain immediately visible
def CheckPinProgram(SourceData, ResultData, ArchiveData, ProgramData, EnvelopeData) -> None:
    assert len(ProgramData) == 12337
    assert Hashlib.sha256(ProgramData).hexdigest() == 'e8a72dfd4796bda2a408ab8b629e9f12dc4ae225c8a1e0cc08f3c09b02ff68bf'
    assert len(RevolvePinOps) == 3014
    assert len(RevolvePinOwners) == 503
    assert sum((ItemData[1] for ItemData in RevolvePinOps)) == len(ProgramData)
    assert HasVendorPartEncoding(SourceData)
    assert ResultData.application_usable is True
    assert ResultData.vendor_loadable is True
    assert ResultData.near_lossless is True
    assert StreamH not in ArchiveData.streams
    assert ArchiveData.require(StreamK) == ProgramData
    assert ArchiveData.require(StreamB) == EnvelopeData.Config0Payload
    assert ArchiveData.require('Contents/Config-0-ModelHeader') == EnvelopeData.HeaderPayload
    assert ArchiveData.require('Header2') == EnvelopeData.HeaderPayload

# keeps this focused behavior isolated so regressions remain immediately visible
def CheckPinNative(ArchiveData, ProgramData, EnvelopeData) -> None:
    NativeData = DecodeNativeModel(ArchiveData.require(StreamE), ProgramData, EnvelopeData.Config0Payload, resolved_stream=StreamK)
    assert len(NativeData.sketches) == 1
    assert NativeData.sketches[0].support_plane_id == 3
    assert len(NativeData.sketches[0].profiles) == 1
    assert NativeData.sketches[0].profiles[0].kind == 'polyline'
    assert NativeData.sketches[0].profiles[0].coordinates == PytestLib.approx(tuple((ValueData for PointData in KPinPointsMm for ValueData in PointData)))
    assert len(NativeData.operations) == 1
    assert NativeData.operations[0].object_id == 31
    assert NativeData.operations[0].kind == 'revolve_join'
    assert NativeData.operations[0].angle_degrees == PytestLib.approx(360.0)
    assert NativeAxisBindings(NativeData) == frozenset({(31, 26, 'V_Axis')})

# keeps this focused behavior isolated so regressions remain immediately visible
def CheckPinModes(ResultData) -> None:
    TransferData = {ItemData.capability: ItemData.mode.value for ItemData in ResultData.transfers}
    for CapabilityValue in (Capability.BREP, Capability.PARAMETERS, Capability.PARAMETRIC_HISTORY, Capability.EDITABLE_SKETCHES, Capability.BODY_STRUCTURE, Capability.SELECTIONS):
        assert TransferData[CapabilityValue] == 'native'

# keeps this focused behavior isolated so regressions remain immediately visible
def TestFCPRWRCE(TmpPath: FilePath) -> None:
    SourceData = ReadFreecad(KFreeCadRevPin)
    TargetPath = TmpPath / 'FreeCadPinRevolution.SLDPRT'
    ResultData = WriteDocument(SourceData, TargetPath, allow_carrier=True)
    ArchiveData = SldprtArchive.from_bytes(TargetPath.read_bytes())
    ProgramData = EncodeRevolvePinProgram()
    EnvelopeData = BuildRevolvePinEnvelope()
    CheckPinProgram(SourceData, ResultData, ArchiveData, ProgramData, EnvelopeData)
    CheckPinNative(ArchiveData, ProgramData, EnvelopeData)
    CheckPinModes(ResultData)

# keeps this focused behavior isolated so regressions remain immediately visible
def TestFCPWNEF() -> None:
    CenterData = VectorTwo(0.0, 0.0)
    SourceData = FreecadRPD(depth=14.0)
    SourceSketch = SourceData.sketches[0]
    CircleEntity = SketchEntity('freecad:circle:0', GeometryKind.CIRCLE, CircleGeometry(CenterData, 18.0))
    CircleSketch = ReplaceData(SourceSketch, entities=(CircleEntity,), closed_profile_entity_ids=((CircleEntity.id,),))
    SourceData = ReplaceData(SourceData, sketches=(CircleSketch,))
    OutputData = BytesIO()
    ResultData = WriteSldprt(SourceData, OutputData)
    ArchiveData = SldprtArchive.from_bytes(OutputData.getvalue())
    NativeData = DecodeNativeModel(ArchiveData.require(StreamE), ArchiveData.require(StreamK), resolved_stream=StreamK)
    assert ResultData.application_usable is True
    assert ResultData.vendor_loadable is True
    assert ResultData.near_lossless is True
    assert len(NativeData.sketches) == 1
    assert NativeData.sketches[0].object_id == 26
    assert len(NativeData.sketches[0].profiles) == 1
    assert NativeData.sketches[0].profiles[0].kind == 'circle'
    assert NativeData.sketches[0].profiles[0].coordinates == PytestLib.approx((CenterData.x, CenterData.y, 18.0))
    assert tuple(((ItemData.name, ItemData.value_mm, ItemData.kind, ItemData.native_role) for ItemData in NativeData.sketches[0].dimensions)) == (('D1', 36.0, 'diameter', 'driving'),)
    assert tuple((ItemData.kind for ItemData in NativeData.sketches[0].constraints)) == ('diameter',)
    assert NativeData.operations[0].object_id == 33
    assert NativeData.operations[0].length_mm == PytestLib.approx(14.0)
    OffsetEntity = ReplaceData(CircleEntity, geometry=CircleGeometry(VectorTwo(3.0, -2.0), 18.0))
    OffsetSource = ReplaceData(SourceData, sketches=(ReplaceData(CircleSketch, entities=(OffsetEntity,), closed_profile_entity_ids=((OffsetEntity.id,),)),))
    OffsetResult = WriteSldprt(OffsetSource, BytesIO())
    assert OffsetResult.application_usable is False
    assert OffsetResult.vendor_loadable is False

# keeps this focused behavior isolated so regressions remain immediately visible
def TestFCRCPWNEF() -> None:
    CenterData = VectorTwo(0.0, 0.0)
    SourceData = FreecadRPD(depth=10.0)
    SourceSketch = SourceData.sketches[0]
    CircleEntity = SketchEntity('freecad:circle:reverse', GeometryKind.CIRCLE, CircleGeometry(CenterData, 5.0))
    CircleSketch = ReplaceData(SourceSketch, entities=(CircleEntity,), closed_profile_entity_ids=((CircleEntity.id,),))
    SourceData = FreeCDV(ReplaceData(SourceData, sketches=(CircleSketch,)), 'reversed')
    OutputData = BytesIO()
    ResultData = WriteSldprt(SourceData, OutputData)
    ArchiveData = SldprtArchive.from_bytes(OutputData.getvalue())
    ResolvedData = ArchiveData.require(StreamK)
    ConfigurationData = ArchiveData.require(StreamB)
    NativeData = DecodeNativeModel(ArchiveData.require(StreamE), ResolvedData, ConfigurationData, resolved_stream=StreamK)
    assert HasVendorPartEncoding(SourceData)
    assert ResultData.application_usable is True
    assert ResultData.vendor_loadable is True
    assert ResultData.near_lossless is True
    assert len(ResolvedData) == 12514
    assert Hashlib.sha256(ResolvedData).hexdigest() == 'b9735d3134c944dc8e66e64d62aa84c117edcf06a17e5d69601e552b9150655d'
    assert len(ConfigurationData) == 25158
    assert Hashlib.sha256(ConfigurationData).hexdigest() == 'fc1cb072c15c9f334bab288234353e3dc27db5aa83abd61c6fdd95364ac276a8'
    assert NativeData.sketches[0].profiles[0].coordinates == PytestLib.approx((0.0, 0.0, 5.0))
    assert NativeData.operations[0].object_id == 33
    assert NativeData.operations[0].direction_code == 1
    assert NativeData.operations[0].termination_code == 0
    assert NativeData.operations[0].length_mm == PytestLib.approx(10.0)

# keeps this focused behavior isolated so regressions remain immediately visible
def TestCircleVar() -> None:
    CenterData = VectorTwo(0.0, 0.0)
    VariableSource = FreecadRPD(depth=12.0)
    VariableSketch = VariableSource.sketches[0]
    VariableCircle = SketchEntity('freecad:circle:reverse:variable', GeometryKind.CIRCLE, CircleGeometry(CenterData, 8.0))
    VariableSource = FreeCDV(ReplaceData(VariableSource, sketches=(ReplaceData(VariableSketch, entities=(VariableCircle,), closed_profile_entity_ids=((VariableCircle.id,),)),)), 'reversed')
    VariableOutput = BytesIO()
    VariableResult = WriteSldprt(VariableSource, VariableOutput)
    VariableArchive = SldprtArchive.from_bytes(VariableOutput.getvalue())
    VariableNative = DecodeNativeModel(VariableArchive.require(StreamE), VariableArchive.require(StreamK), VariableArchive.require(StreamB), resolved_stream=StreamK)
    assert VariableResult.vendor_loadable is True
    assert VariableResult.near_lossless is True
    assert VariableNative.sketches[0].profiles[0].coordinates == PytestLib.approx((0.0, 0.0, 8.0))
    assert VariableNative.operations[0].direction_code == 1
    assert VariableNative.operations[0].length_mm == PytestLib.approx(12.0)

# keeps this focused behavior isolated so regressions remain immediately visible
def TestFTPPWNEF() -> None:
    SourceData = FreecadRPD(bounds=(-17.0, -8.0, 29.0, 12.0), depth=13.0)
    SourcePlane = ReplaceData(SourceData.support_planes[0], transform=Transform(x_axis=VectorThree(1.0, 0.0, 0.0), y_axis=VectorThree(0.0, 0.0, 1.0), z_axis=VectorThree(0.0, -1.0, 0.0)))
    SourceFeature = SourceData.feature_timeline[0]
    assert isinstance(SourceFeature.definition, ExtrusionFeature)
    SourceFeature = ReplaceData(SourceFeature, definition=ReplaceData(SourceFeature.definition, direction=VectorThree(0.0, -1.0, 0.0)))
    SourceData = ReplaceData(SourceData, support_planes=(SourcePlane,), feature_timeline=(SourceFeature,))
    OutputData = BytesIO()
    ResultData = WriteSldprt(SourceData, OutputData)
    ArchiveData = SldprtArchive.from_bytes(OutputData.getvalue())
    NativeData = DecodeNativeModel(ArchiveData.require(StreamE), ArchiveData.require(StreamK), resolved_stream=StreamK)
    assert ResultData.vendor_loadable is True
    assert NativeData.sketches[0].support_plane_id == 3
    assert NativeData.sketches[0].profiles[0].coordinates == PytestLib.approx((-17.0, -12.0, 29.0, 8.0))
    assert NativeData.operations[0].direction_code == 1
    assert NativeData.operations[0].length_mm == PytestLib.approx(13.0)

# keeps this focused behavior isolated so regressions remain immediately visible
def TestFRPPWNEF() -> None:
    SourceData = FreecadRPD(bounds=(-17.0, -8.0, 29.0, 12.0), depth=7.0)
    SourcePlane = ReplaceData(SourceData.support_planes[0], transform=Transform(x_axis=VectorThree(0.0, 1.0, 0.0), y_axis=VectorThree(0.0, 0.0, 1.0), z_axis=VectorThree(1.0, 0.0, 0.0)))
    SourceFeature = SourceData.feature_timeline[0]
    assert isinstance(SourceFeature.definition, ExtrusionFeature)
    SourceFeature = ReplaceData(SourceFeature, definition=ReplaceData(SourceFeature.definition, direction=VectorThree(1.0, 0.0, 0.0)))
    SourceData = ReplaceData(SourceData, support_planes=(SourcePlane,), feature_timeline=(SourceFeature,))
    OutputData = BytesIO()
    ResultData = WriteSldprt(SourceData, OutputData)
    ArchiveData = SldprtArchive.from_bytes(OutputData.getvalue())
    NativeData = DecodeNativeModel(ArchiveData.require(StreamE), ArchiveData.require(StreamK), resolved_stream=StreamK)
    assert ResultData.vendor_loadable is True
    assert NativeData.sketches[0].support_plane_id == 4
    assert NativeData.sketches[0].profiles[0].coordinates == PytestLib.approx((-12.0, -17.0, 8.0, 29.0))
    assert NativeData.operations[0].direction_code == 0
    assert NativeData.operations[0].length_mm == PytestLib.approx(7.0)

# keeps this focused behavior isolated so regressions remain immediately visible
@PytestLib.mark.parametrize('Variant', ('foreign', 'construction', 'open', 'taper'))
def TestFRPNGRNEM(Variant: str) -> None:
    SourceDoc = FreecadRPD()
    Feature = SourceDoc.feature_timeline[0]
    SketchA = SourceDoc.sketches[0]
    if Variant == 'foreign':
        SourceDoc = ReplaceData(SourceDoc, source=ReplaceData(SourceDoc.source, format_id='test'))
    elif Variant == 'construction':
        Entities = (ReplaceData(SketchA.entities[0], construction=True), *SketchA.entities[1:])
        SourceDoc = ReplaceData(SourceDoc, sketches=(ReplaceData(SketchA, entities=Entities),))
    elif Variant == 'open':
        SourceDoc = ReplaceData(SourceDoc, sketches=(ReplaceData(SketchA, entities=SketchA.entities[:-1], closed_profile_entity_ids=()),))
    else:
        SourceDoc = ReplaceData(SourceDoc, feature_timeline=(ReplaceData(Feature, definition=ReplaceData(Feature.definition, draft_angle=ParameterValue(1.0, ValueKind.ANGLE, 'deg'))),))
    Output = BytesIO()
    ResultInfo = WriteSldprt(SourceDoc, Output)
    Archive = SldprtArchive.from_bytes(Output.getvalue())
    assert ResultInfo.application_usable is False
    assert ResultInfo.vendor_loadable is False
    assert 'Contents/DisplayLists' not in Archive.streams
    assert Hashlib.sha256(Archive.require(StreamI)).hexdigest() != '56df5b4e4ccac3158b60ea75dd57959b991660d6d9c7bc05cbff795e56f44439'

# keeps this focused behavior isolated so regressions remain immediately visible
def TestSLNRBPPCN() -> None:
    SourceDoc = Document()
    Points = (VectorTwo(-20.0, -10.0), VectorTwo(20.0, -10.0), VectorTwo(20.0, 10.0), VectorTwo(-20.0, 10.0))
    Entities = tuple((SketchEntity(f'edge:{Index}', GeometryKind.LINE, LineGeometry(Points[Index], Points[(Index + 1) % len(Points)])) for Index in range(len(Points))))
    SketchA = Sketch(SourceDoc.sketches[0].id, 'CustomSketch', SourceDoc.sketches[0].support_plane_id, Entities, closed_profile_entity_ids=(tuple((ItemValue.id for ItemValue in Entities)),))
    Feature = ReplaceData(SourceDoc.feature_timeline[0], name='CustomBoss', operation=BooleanOperation.JOIN, definition=ExtrusionFeature(ParameterValue(10.0, ValueKind.LENGTH, 'mm')))
    SourceDoc = ReplaceData(SourceDoc, sketches=(SketchA,), feature_timeline=(Feature,))
    Output = BytesIO()
    WriteSldprt(SourceDoc, Output)
    Archive = SldprtArchive.from_bytes(Output.getvalue())
    Native = DecodeNativeModel(Archive.require(StreamE), Archive.require(StreamH), resolved_stream=StreamH)
    assert Native.sketches[0].name == 'CustomSketch'
    assert Native.operations[0].name == 'CustomBoss'
    assert 'Contents/DisplayLists' not in Archive.streams

# keeps this focused behavior isolated so regressions remain immediately visible
def NonNRBD() -> CadDocument:
    SourceDoc = Document()
    Points = (VectorTwo(-20.0, -10.0), VectorTwo(20.0, -10.0), VectorTwo(20.0, 10.0), VectorTwo(-20.0, 10.0))
    Entities = tuple((SketchEntity(f'edge:{Index}', GeometryKind.LINE, LineGeometry(Points[Index], Points[(Index + 1) % len(Points)])) for Index in range(len(Points))))
    SketchA = Sketch(SourceDoc.sketches[0].id, 'CustomSketch', SourceDoc.sketches[0].support_plane_id, Entities, closed_profile_entity_ids=(tuple((ItemValue.id for ItemValue in Entities)),))
    Feature = ReplaceData(SourceDoc.feature_timeline[0], name='CustomBoss', operation=BooleanOperation.JOIN, definition=ExtrusionFeature(ParameterValue(10.0, ValueKind.LENGTH, 'mm')))
    return ReplaceData(SourceDoc, sketches=(SketchA,), feature_timeline=(Feature,), configurations=(Configuration('config:default', 'Default', True), Configuration('config:machined', 'Machined')))

# keeps this focused behavior isolated so regressions remain immediately visible
def TestNNDWNVRFL() -> None:
    SourceDoc = NonNRBD()
    Output = BytesIO()
    ResultInfo = WriteSldprt(SourceDoc, Output)
    Archive = SldprtArchive.from_bytes(Output.getvalue())
    Lanes = sorted((NameText for NameText in Archive.streams if NameText.startswith('Contents/Config-') and NameText.endswith('-ResolvedFeatures')))
    assert Lanes == []
    PartDoc = EncodeNativePart(DocumentWithoutSource(SourceDoc), 'memory')
    assert PartDoc.configuration_lanes == ()
    assert PartDoc.donor_notes == Notes
    assert Archive.require(StreamA)
    assert Archive.require(StreamB)
    RecordList = Archive.require(StreamH)
    assert RecordList == PartDoc.kit_resolved_features
    assert ResultInfo.application_usable is False
    assert ResultInfo.vendor_loadable is False
    assert ResultInfo.metadata['compatibility'] == 'native-metadata-with-kit-neutral'
    assert ResultInfo.metadata['native_content'] == 'native-metadata'
    DonorDeclined = next((ItemValue for ItemValue in ResultInfo.diagnostics if ItemValue.code == 'sldprt.donor_declined'))
    assert DonorDeclined.severity is Severity.WARNING
    assert all((NoteInfo in DonorDeclined.message for NoteInfo in Notes))

# keeps this focused behavior isolated so regressions remain immediately visible
def TestNNKRSPDR() -> None:
    SourceDoc = NonNRBD()
    Output = BytesIO()
    WriteSldprt(SourceDoc, Output)
    Archive = SldprtArchive.from_bytes(Output.getvalue())
    Keywords = Archive.require(StreamE)
    Native = DecodeNativeModel(Keywords, Archive.require(StreamH), resolved_stream=StreamH)
    assert [ItemValue.name for ItemValue in Native.sketches] == ['CustomSketch']
    assert Native.sketches[0].object_id == 26
    assert Native.sketches[0].support_plane_id == 2
    assert [(ItemValue.kind, ItemValue.coordinates) for ItemValue in Native.sketches[0].profiles] == [('rectangle', (-20.0, -10.0, 20.0, 10.0))]
    assert [(ItemValue.name, ItemValue.object_id) for ItemValue in Native.operations] == [('CustomBoss', 27)]
    assert Native.operations[0].length_mm == PytestLib.approx(10.0)
    assert Native.operations[0].profile_id == 26
    assert [(ItemValue.object_id, ItemValue.name) for ItemValue in Native.planes] == [(2, 'Front Plane'), (3, 'Top Plane'), (4, 'Right Plane')]
    assert {ItemValue.native_stream for ItemValue in Native.planes} == {StreamH}
    assert {ItemValue.native_stream for ItemValue in Native.sketches} == {StreamH}
    assert {ItemValue.native_stream for ItemValue in Native.operations} == {StreamH}
    assert StreamK not in Archive.streams
    assert Archive.require(StreamA)
    assert Archive.require(StreamB)
    Restored = ReadSldprt(Output.getvalue())
    assert [ItemValue.name for ItemValue in Restored.sketches] == ['CustomSketch']
    assert [ItemValue.name for ItemValue in Restored.feature_timeline] == ['CustomBoss']
    assert Restored.sketches[0].entities == SourceDoc.sketches[0].entities
    assert Restored.feature_timeline[0].definition == SourceDoc.feature_timeline[0].definition

# keeps this focused behavior isolated so regressions remain immediately visible
def TestNBWNPP() -> None:
    BaseInfo = Document()
    SourceDoc = ReplaceData(BaseInfo, brep=TriangleBrep(), capabilities=BaseInfo.capabilities | {Capability.BREP})
    Output = BytesIO()
    ResultInfo = WriteSldprt(SourceDoc, Output)
    Archive = SldprtArchive.from_bytes(Output.getvalue())
    Partition = Archive.require(StreamI)
    Native = DecodePartitionStream(Partition)[0]
    Restored = ReadSldprt(Output.getvalue())
    PartInfo = EncodeNativePart(SourceDoc, 'Part1')
    FeatureId = PartInfo.object_ids[f'feature:{SourceDoc.bodies[0].final_feature_id}']
    assert Native.schema == 'SCH_1200000_12006'
    assert Native.data == EncodeBrepModel(SourceDoc.brep, solidworks_feature_ids={SourceDoc.brep.bodies[0].id: FeatureId})
    assert b'LAST_BODY_MODIFYING_FEATURE_ID' in Native.data
    assert Partition != Native.data
    assert Restored.brep == SourceDoc.brep
    assert ResultInfo.metadata['mode'] == 'generated'
    assert ResultInfo.metadata['native_content'] == 'native-metadata-and-neutral-brep'
    assert ResultInfo.metadata['compatibility'] == 'native-brep-with-kit-neutral'
    assert ResultInfo.metadata['native_brep'] == 'generated'
    assert ResultInfo.metadata['native_geometry'] is True
    assert ResultInfo.metadata['native_history'] is False
    assert ResultInfo.metadata['native_assembly'] is False
    assert ResultInfo.metadata['vendor_loadable'] is False

# keeps this focused behavior isolated so regressions remain immediately visible
def TestSLBOWNIFM() -> None:
    BaseInfo = Document()
    Feature = ReplaceData(BaseInfo.feature_timeline[0], name='Imported1', kind='imported', sketch_id=None, attributes=FrozenMapping({'native_object_id': 26, 'native_type': 'Imported'}))
    BodyInfo = ReplaceData(BaseInfo.bodies[0], final_feature_id=Feature.id)
    SourceDoc = ReplaceData(BaseInfo, support_planes=(), sketches=(), feature_timeline=(Feature,), bodies=(BodyInfo,), brep=TriangleBrep(), capabilities=frozenset({Capability.BREP}))
    Output = BytesIO()
    WriteSldprt(SourceDoc, Output)
    Archive = SldprtArchive.from_bytes(Output.getvalue())
    assert StreamK not in Archive.streams
    assert Archive.require(StreamA)
    assert Archive.require(StreamB)
    Resolved = Archive.require(StreamH)
    Native = DecodeNativeModel(Archive.require(StreamE), Resolved, resolved_stream=StreamH)
    Imported = next((ItemValue for ItemValue in Native.features if ItemValue.object_id == 26))
    Classes = {ItemValue.offset: ItemValue.name for ItemValue in Native.classes}
    assert Imported.name == 'Imported1'
    assert Imported.kind == 'Imported'
    assert Classes[Imported.native_offset - 18] == 'moBaseBody_c'
    assert Native.diagnostics == ()
    assert Imported.native_end == len(Resolved)
    assert Resolved[Imported.native_offset:Imported.native_end] == Imported.data

# keeps this focused behavior isolated so regressions remain immediately visible
def TestGPPINB(TmpPath) -> None:
    BaseInfo = Document()
    SourceDoc = ReplaceData(BaseInfo, brep=TriangleBrep(), capabilities=BaseInfo.capabilities | {Capability.BREP})
    Blocked = TmpPath / 'blocked.SLDPRT'
    with PytestLib.raises(ApplicationUsabilityError) as Captured:
        WriteDocument(SourceDoc, Blocked, allow_carrier=False)
    assert Capability.BREP not in Captured.value.unimplemented_capabilities
    assert Captured.value.unimplemented_capabilities == frozenset({Capability.BODY_STRUCTURE, Capability.EDITABLE_SKETCHES, Capability.PARAMETRIC_HISTORY})
    assert not Blocked.exists()
    Explicit = TmpPath / 'explicit.SLDPRT'
    ResultInfo = WriteDocument(SourceDoc, Explicit, allow_carrier=True)
    assert ResultInfo.metadata['native_brep'] == 'generated'
    assert next((ItemValue for ItemValue in ResultInfo.transfers if ItemValue.capability is Capability.BREP)).mode.value == 'native'
    assert ResultInfo.vendor_loadable is False
    assert ResultInfo.near_lossless is False
    assert OpenDocument(Explicit).brep == SourceDoc.brep

# keeps this focused behavior isolated so regressions remain immediately visible
def TestPPDTKNB() -> None:
    Encoded = EncodeBrepModel(TriangleBrep())
    Decoded = DecodeBrepModel(Encoded)
    assert Decoded is not None
    assert Decoded.validate() == ()
    assert len(Decoded.bodies) == 1
    assert len(Decoded.faces) == 1
    assert len(Decoded.edges) == 3
    assert len(Decoded.vertices) == 3
    assert {Vertex.point for Vertex in Decoded.vertices} == {Vertex.point for Vertex in TriangleBrep().vertices}

# keeps this focused behavior isolated so regressions remain immediately visible
def TestNSRPPAATB() -> None:
    Encoded = EncodeBrepModel(TriangleBrep())
    SourceDoc = SldprtArchive.open(KSample)
    StreamsA = SourceDoc.streams
    StreamsA[StreamI] = Encoded
    StreamsA.pop('Contents/Config-0-GhostPartition', None)
    Native = BuildSldprt(StreamsA, file_id=SourceDoc.file_id, format_version=SourceDoc.format_version, signatures=ContainerSignatures(KSample.read_bytes()))
    Decoded = ReadSldprt(Native)
    assert Decoded.brep is not None
    assert Decoded.brep.validate() == ()
    assert len(Decoded.brep_payloads) == 1
    assert Decoded.brep_payloads[0].data == Encoded

# keeps this focused behavior isolated so regressions remain immediately visible
def TestPDROTAD() -> None:
    Encoded = EncodeBrepModel(TriangleBrep())
    Broken = bytearray(Encoded)
    Header = ParasolidHeader(Encoded)
    assert Header is not None
    Tables = ScanPartitionRecords(Encoded[Header.body_offset:])
    assert Tables is not None
    LoopInfo = next(iter(Tables.loops.values()))
    StructLib.pack_into('>H', Broken, Header.body_offset + LoopInfo.offset + 10, 1)
    assert DecodeBrepModel(Broken) is None
    Deltas = Encoded.replace(b'partition', b'deltasxxx', 1)
    assert DecodeBrepModel(Deltas) is None

# keeps this focused behavior isolated so regressions remain immediately visible
def TestNSIBFOTARG() -> None:
    Encoded = EncodeBrepModel(TriangleBrep())
    SourceDoc = SldprtArchive.open(KSample)
    StreamsA = SourceDoc.streams
    StreamsA[StreamI] = Encoded
    StreamsA.pop('Contents/Config-0-GhostPartition', None)
    Native = BuildSldprt(StreamsA, file_id=SourceDoc.file_id, format_version=SourceDoc.format_version, signatures=ContainerSignatures(KSample.read_bytes()))
    Decoded = ReadSldprt(Native, include_brep=False)
    assert Decoded.brep is None
    assert Decoded.brep_payloads == ()

# keeps this focused behavior isolated so regressions remain immediately visible
def TestUNBRAHC() -> None:
    BaseInfo = Document()
    BrepInfo = TriangleBrep()
    Unsupported = ReplaceData(BrepInfo, surfaces=(NativeSurface('surface:0', 'future.cad', 'future-surface'),))
    SourceDoc = ReplaceData(BaseInfo, brep=Unsupported, capabilities=BaseInfo.capabilities | {Capability.BREP})
    Output = BytesIO()
    ResultInfo = WriteSldprt(SourceDoc, Output)
    Archive = SldprtArchive.from_bytes(Output.getvalue())
    Restored = ReadSldprt(Output.getvalue())
    assert Archive.get(StreamI) is None
    assert Restored.brep == SourceDoc.brep
    assert ResultInfo.metadata['native_content'] == 'native-metadata'
    assert ResultInfo.metadata['native_brep'].startswith('unsupported:')
    assert ResultInfo.metadata['native_geometry'] is False
    assert ResultInfo.metadata['vendor_loadable'] is False
    assert ResultInfo.diagnostics[-1].code == 'sldprt.native_brep_unsupported'

# keeps this focused behavior isolated so regressions remain immediately visible
def TestGCIBFRNGP(TmpPath) -> None:
    BaseInfo = Document()
    SourceDoc = ReplaceData(BaseInfo, brep_payloads=(BrepPayload('geometry', 'future.kernel', 'body', '1', '', data=b'geometry', role=PayloadRole.BREP, file_extension='.geo'), BrepPayload('history', 'future.cad', 'feature-records', '1', '', data=b'history', role=PayloadRole.FEATURE_HISTORY)), capabilities=BaseInfo.capabilities | frozenset({Capability.BREP, Capability.NATIVE_PAYLOADS}))
    TargetDoc = TmpPath / 'payloads.SLDPRT'
    WriteSldprt(SourceDoc, TargetDoc)
    WithoutBrep = ReadSldprt(TargetDoc, include_brep=False)
    assert [Payload.id for Payload in WithoutBrep.brep_payloads] == ['history']
    assert WithoutBrep.brep_payloads[0].data == b'history'
    assert WithoutBrep.capabilities == SourceDoc.capabilities - {Capability.BREP}
    WithBrep = ReadSldprt(TargetDoc, include_brep=True)
    assert [Payload.id for Payload in WithBrep.brep_payloads] == ['geometry', 'history']
    assert WithBrep.capabilities == SourceDoc.capabilities

# keeps this focused behavior isolated so regressions remain immediately visible
@PytestLib.mark.parametrize('SourceDoc', (Document(), AssemblyDocument()))
def TestGCPDSC(SourceDoc) -> None:
    Output = BytesIO()
    WriteSldprt(SourceDoc, Output)
    Restored = ReadSldprt(Output.getvalue())
    assert Restored.capabilities == SourceDoc.capabilities
    if SourceDoc.assembly is not None:
        assert Restored.assembly is not None
        assert tuple((ItemValue.document.capabilities for ItemValue in Restored.assembly.documents if ItemValue.document is not None)) == tuple((ItemValue.document.capabilities for ItemValue in SourceDoc.assembly.documents if ItemValue.document is not None))

# keeps this focused behavior isolated so regressions remain immediately visible
@PytestLib.mark.parametrize(('payload_index', 'changes'), ((0, {'data': b'changed document'}), (1, {'data': b'changed binding'}), (0, {'id': 'changed-document'}), (1, {'id': 'changed-binding'})))
def TestFDPMIOR(PayloadIndex: int, Changes: dict[str, bytes | str]) -> None:
    SourceDoc = ReplaceData(Document(), brep_payloads=(BrepPayload('foreign-document', 'future.cad.document', 'native_document', 'v1', '', data=b'original document', role=PayloadRole.DOCUMENT, file_extension='.cad'), BrepPayload('foreign-binding', 'future.cad.sha256', 'native_document_binding', 'sha256', '', data=b'original binding', role=PayloadRole.VERIFICATION, file_extension='.sha256')))
    Carrier = BytesIO()
    WriteSldprt(SourceDoc, Carrier)
    Original = Carrier.getvalue()
    Restored = ReadSldprt(Original)
    Payloads = list(Restored.brep_payloads)
    Payloads[PayloadIndex] = ReplaceData(Payloads[PayloadIndex], **Changes)
    Mutated = ReplaceData(Restored, brep_payloads=tuple(Payloads))
    Output = BytesIO()
    ResultInfo = WriteSldprt(Mutated, Output)
    assert ResultInfo.metadata['mode'] == 'template'
    assert Output.getvalue() != Original
    Reread = ReadSldprt(Output.getvalue())
    Changed = Reread.brep_payloads[PayloadIndex]
    for LookupKey, ItemValueA in Changes.items():
        assert getattr(Changed, LookupKey) == ItemValueA

# keeps this focused behavior isolated so regressions remain immediately visible
def TestSEUNTWCNE(TmpPath) -> None:
    SourceDoc = ReadSldprt(KSample)
    EditedFeature = ReplaceData(SourceDoc.feature_timeline[0], name='Edited in Kit')
    Edited = ReplaceData(SourceDoc, feature_timeline=(EditedFeature, *SourceDoc.feature_timeline[1:]))
    Output = TmpPath / 'edited.SLDPRT'
    with PytestLib.raises(SldprtFormatError, match='allow_non_native'):
        WriteSldprt(Edited, Output, allow_non_native=False)
    ResultInfo = WriteSldprt(Edited, Output)
    OriginalArchive = SldprtArchive.open(KSample)
    EditedArchive = SldprtArchive.open(Output)
    assert Output.read_bytes() != KSample.read_bytes()
    assert set(OriginalArchive.streams) <= set(EditedArchive.streams)
    assert EditedArchive.require('Kit/Interchange')
    assert ReadSldprt(Output).feature_timeline[0].name == 'Edited in Kit'
    assert ResultInfo.metadata['mode'] == 'template'
    assert ResultInfo.metadata['native_content'] == 'source-preserved'
    assert ResultInfo.metadata['compatibility'] == 'native-source-with-kit-neutral'
    assert ResultInfo.metadata['neutral_edits_are_native'] is False
    assert ResultInfo.diagnostics[-1].code == 'sldprt.neutral_write'

# keeps this focused behavior isolated so regressions remain immediately visible
def TestNTPDDWCOI(TmpPath) -> None:
    SourceDoc = ReadSldprt(KSample)
    ParameterA = SourceDoc.parameters[0]
    TargetValue = float(ParameterA.value.value) + 1.25
    Edited = ReplaceData(SourceDoc, parameters=(ReplaceData(ParameterA, value=ReplaceData(ParameterA.value, value=TargetValue)), *SourceDoc.parameters[1:]))
    Output = TmpPath / 'dimension.SLDPRT'
    ResultInfo = WriteDocument(Edited, Output)
    assert ResultInfo.application_usable is True
    assert ResultInfo.vendor_loadable is True
    assert ResultInfo.near_lossless is True
    assert ResultInfo.metadata['compatibility'] == 'native-template'
    assert {Capability.PARAMETERS, Capability.PARAMETRIC_HISTORY, Capability.EDITABLE_SKETCHES} <= ResultInfo.native_capabilities
    Archive = SldprtArchive.open(Output)
    StreamsA = Archive.streams
    StreamsA.pop(StreamF)
    StreamsA.pop(StreamG)
    Native = ReadSldprt(BuildSldprt(StreamsA, file_id=Archive.file_id, format_version=Archive.format_version, signatures=ContainerSignatures(Output.read_bytes())))
    NativeParameter = next((ItemValue for ItemValue in Native.parameters if ItemValue.id == ParameterA.id))
    assert NativeParameter.value.value == PytestLib.approx(TargetValue)

# keeps this focused behavior isolated so regressions remain immediately visible
def ForgeAttest(TmpPath) -> tuple[bytes, float]:
    SourceDoc = ReadSldprt(KSample)
    ParameterA = SourceDoc.parameters[0]
    NativeValue = float(ParameterA.value.value) + 1.25
    NativeDocument = ReplaceData(SourceDoc, parameters=(ReplaceData(ParameterA, value=ReplaceData(ParameterA.value, value=NativeValue)), *SourceDoc.parameters[1:]))
    Trusted = TmpPath / 'trusted.SLDPRT'
    assert WriteDocument(NativeDocument, Trusted).metadata['compatibility'] == 'native-template'
    Archive = SldprtArchive.open(Trusted)
    StreamsA = Archive.streams
    Embedded = CadDocument.from_json(StreamsA[StreamF].decode('utf-8'))
    EmbeddedParameter = Embedded.parameters[0]
    ForgedValue = NativeValue + 7.5
    ForgedDocument = ReplaceData(Embedded, parameters=(ReplaceData(EmbeddedParameter, value=ReplaceData(EmbeddedParameter.value, value=ForgedValue)), *Embedded.parameters[1:]))
    ForgedManifest = ForgedDocument.to_json(indent=None).encode('utf-8')
    StreamsA[StreamF] = ForgedManifest
    Attestation = JsonLib.loads(StreamsA[StreamG].decode('utf-8'))
    Attestation['embedded_sha256'] = Hashlib.sha256(ForgedManifest).hexdigest()
    Attestation['semantic_sha256'] = SemanticShaTwoFiveSix(ForgedDocument)
    Attestation['native_stream_sha256'] = NativeStreamShaTwoFiveSix(StreamsA)
    StreamsA[StreamG] = JsonLib.dumps(Attestation, sort_keys=True, separators=(',', ':')).encode('utf-8')
    Forged = BuildSldprt(StreamsA, file_id=Archive.file_id, format_version=Archive.format_version, signatures=ContainerSignatures(Trusted.read_bytes()))
    return (Forged, ForgedValue)

# keeps this focused behavior isolated so regressions remain immediately visible
def TestRACFNTC(TmpPath) -> None:
    Forged, ForgedValue = ForgeAttest(TmpPath)
    Restored = ReadSldprt(Forged)
    assert Restored.parameters[0].value.value == PytestLib.approx(ForgedValue)
    Blocked = TmpPath / 'blocked.SLDPRT'
    with PytestLib.raises(ApplicationUsabilityError):
        WriteDocument(Restored, Blocked, allow_carrier=False)
    assert not Blocked.exists()
    Output = TmpPath / 'carrier.SLDPRT'
    ResultInfo = WriteDocument(Restored, Output)
    assert ResultInfo.application_usable is False
    assert ResultInfo.vendor_loadable is False
    assert ResultInfo.metadata['compatibility'] == 'kit-neutral-only'
    assert ResultInfo.near_lossless is False
    assert Output.read_bytes() == Forged

# keeps this focused behavior isolated so regressions remain immediately visible
def TestACPKSTNE(TmpPath) -> None:
    SourceDoc = ReadSldprt(KSample)
    ParameterA = SourceDoc.parameters[0]
    Edited = ReplaceData(SourceDoc, parameters=(ReplaceData(ParameterA, value=ReplaceData(ParameterA.value, value=float(ParameterA.value.value) + 1.25)), *SourceDoc.parameters[1:]))
    Trusted = TmpPath / 'trusted.SLDPRT'
    WriteDocument(Edited, Trusted)
    Archive = SldprtArchive.open(Trusted)
    StreamsA = Archive.streams
    Attestation = JsonLib.loads(StreamsA[StreamG].decode('utf-8'))
    Attestation['compatibility'] = 'native-exact'
    Attestation['application_usable'] = False
    Attestation['vendor_loadable'] = False
    StreamsA[StreamG] = JsonLib.dumps(Attestation, sort_keys=True, separators=(',', ':')).encode('utf-8')
    Forged = BuildSldprt(StreamsA, file_id=Archive.file_id, format_version=Archive.format_version, signatures=ContainerSignatures(Trusted.read_bytes()))
    Restored = ReadSldprt(Forged)
    Blocked = TmpPath / 'blocked.SLDPRT'
    with PytestLib.raises(ApplicationUsabilityError):
        WriteDocument(Restored, Blocked, allow_carrier=False)
    assert not Blocked.exists()
    Output = TmpPath / 'carrier.SLDPRT'
    ResultInfo = WriteDocument(Restored, Output)
    assert ResultInfo.application_usable is False
    assert ResultInfo.vendor_loadable is False
    assert ResultInfo.metadata['compatibility'] == 'kit-neutral-only'
    assert ResultInfo.carrier_capabilities == ResultInfo.transferred_capabilities

# keeps this focused behavior isolated so regressions remain immediately visible
def TestNTPSWFN(TmpPath) -> None:
    SourceDoc = ReadSldprt(KSample)
    Feature = SourceDoc.feature_timeline[0]
    TargetName = 'X' * len(Feature.name)
    Edited = ReplaceData(SourceDoc, feature_timeline=(ReplaceData(Feature, name=TargetName), *SourceDoc.feature_timeline[1:]))
    Output = TmpPath / 'feature-name.SLDPRT'
    ResultInfo = WriteDocument(Edited, Output)
    assert ResultInfo.near_lossless is True
    Archive = SldprtArchive.open(Output)
    StreamsA = Archive.streams
    StreamsA.pop(StreamF)
    StreamsA.pop(StreamG)
    Native = ReadSldprt(BuildSldprt(StreamsA, file_id=Archive.file_id, format_version=Archive.format_version, signatures=ContainerSignatures(Output.read_bytes())))
    assert Native.feature_timeline[0].name == TargetName

# keeps this focused behavior isolated so regressions remain immediately visible
def TestSAEDK(TmpPath) -> None:
    Adapter = Registry.writer('solidworks.sldprt')
    assert Registry.reader('solidworks.sldasm') is Registry.reader('solidworks.sldprt')
    assert Registry.writer('solidworks.sldasm') is Adapter
    assert 'solidworks.sldasm' in Registry.format_ids()
    PartDoc = Document()
    Assembly = AssemblyDocument()
    assert Adapter.supports(PartDoc, TmpPath / 'part.SLDPRT')
    assert not Adapter.supports(PartDoc, TmpPath / 'part.SLDASM')
    assert Adapter.supports(Assembly, TmpPath / 'assembly.SLDASM')
    assert not Adapter.supports(Assembly, TmpPath / 'assembly.SLDPRT')
    assert Adapter.supports(PartDoc, BytesIO())
    assert not Adapter.supports(PartDoc, StringIO())
    with PytestLib.raises(ValueError, match='\\.SLDPRT'):
        WriteSldprt(PartDoc, TmpPath / 'part.SLDASM')
    with PytestLib.raises(ValueError, match='\\.SLDASM'):
        WriteSldprt(Assembly, TmpPath / 'assembly.SLDPRT')
    ResultInfo = WriteSldprt(Assembly, TmpPath / 'assembly.SLDASM', allow_non_native=True)
    assert ResultInfo.adapter == 'solidworks.sldasm'
    assert ResultInfo.metadata['format_id'] == 'solidworks.sldasm'
    AssemblyJson = Assembly.write_json(TmpPath / 'assembly.json')
    PartJson = PartDoc.write_json(TmpPath / 'part.json')
    with PytestLib.raises(ValueError, match='does not support this document kind'):
        Convert(PartJson, BytesIO(), destination_format='solidworks.sldasm')
    with PytestLib.raises(ValueError, match='does not support this document kind'):
        Convert(AssemblyJson, BytesIO(), destination_format='solidworks.sldprt')
    with PytestLib.raises(ValueError, match='does not support this document kind'):
        Convert(PartJson, TmpPath / 'explicit.SLDPRT', destination_format='solidworks.sldasm')
    Conversion = Convert(AssemblyJson, TmpPath / 'converted.SLDASM', destination_format='solidworks.sldasm', allow_carrier=True)
    assert Conversion.destination_format == 'solidworks.sldasm'

# keeps this focused behavior isolated so regressions remain immediately visible
@PytestLib.mark.parametrize(('source', 'wrong_suffix'), ((KSample, '.SLDASM'), (KAssembly, '.SLDPRT')))
def TestSRRNSKM(SourceDoc, WrongSuffix, TmpPath) -> None:
    Renamed = TmpPath / f'renamed{WrongSuffix}'
    Renamed.write_bytes(SourceDoc.read_bytes())
    with PytestLib.raises(SldprtFormatError, match='content requires'):
        ReadSldprt(Renamed)

# keeps this focused behavior isolated so regressions remain immediately visible
def TestSRRCSKM(TmpPath) -> None:
    Valid = TmpPath / 'valid.SLDPRT'
    WriteSldprt(Document(), Valid)
    Renamed = TmpPath / 'renamed.SLDASM'
    Renamed.write_bytes(Valid.read_bytes())
    with PytestLib.raises(SldprtFormatError, match='content requires'):
        ReadSldprt(Renamed)

# keeps this focused behavior isolated so regressions remain immediately visible
def TestGSSRAI() -> None:
    SourceDoc = AssemblyDocument()
    Output = BytesIO()
    ResultInfo = WriteSldprt(SourceDoc, Output)
    Restored = ReadSldprt(Output.getvalue())
    assert ResultInfo.adapter == 'solidworks.sldasm'
    assert Restored.source.format_id == 'solidworks.sldasm'
    assert Restored.assembly == SourceDoc.assembly

# keeps this focused behavior isolated so regressions remain immediately visible
def TestSLAERNCG() -> None:
    SourceDoc = AssemblyDocument()
    Output = BytesIO()
    ResultInfo = WriteSldprt(SourceDoc, Output)
    Archive = SldprtArchive.from_bytes(Output.getvalue())
    Native = DecodeNativeAssembly(Archive)
    Transfers = {ItemValue.capability: ItemValue.mode.value for ItemValue in ResultInfo.transfers}
    assert Stream in Archive.streams
    assert Transfers[Capability.ASSEMBLIES] == 'native'
    assert Transfers[Capability.ASSEMBLY_MATES] == 'carrier'
    assert ResultInfo.application_usable is False
    assert ResultInfo.vendor_loadable is True
    assert Native.name == 'Engine'
    assert tuple((ItemValue.name for ItemValue in Native.definitions)) == ('Engine', 'Piston', 'Piston')
    assert tuple((ItemValue.document_type for ItemValue in Native.definitions)) == ('ASSEMBLY', 'ASSEMBLY', 'PART')
    assert Native.occurrences[0].transform[12:15] == (0.1, 0.02, 0.03)

# keeps this focused behavior isolated so regressions remain immediately visible
def TestSLAEOERM() -> None:
    SourceDoc = AssemblyDocument()
    Assembly = SourceDoc.assembly
    ComponentEntity, RootEntity = Assembly.mate_entities
    ComponentEntity = ReplaceData(ComponentEntity, id='mate-entity:component', instance_path=('instance:subassembly', 'instance:part'), source_entity_id='moPlaneSurfIdRep_c,1,2, ', attributes=FrozenMapping({'persistent_references': ('moPlaneSurfIdRep_c,1,2, ',)}))
    RootEntity = ReplaceData(RootEntity, id='mate-entity:root', instance_path=(), source_entity_id='moPlaneSurfIdRep_c,3,4, ', attributes=FrozenMapping({'persistent_references': ('moPlaneSurfIdRep_c,3,4, ',)}))
    MateInfo = ReplaceData(Assembly.mates[0], entity_ids=(ComponentEntity.id, RootEntity.id), alignment=MateAlignment.ALIGNED)
    SourceDoc = ReplaceData(SourceDoc, assembly=ReplaceData(Assembly, mate_entities=(ComponentEntity, RootEntity), mates=(MateInfo,)))
    Output = BytesIO()
    ResultInfo = WriteSldprt(SourceDoc, Output)
    Native = DecodeNativeAssembly(SldprtArchive.from_bytes(Output.getvalue()))
    Transfers = {ItemValue.capability: ItemValue.mode.value for ItemValue in ResultInfo.transfers}
    assert Transfers[Capability.ASSEMBLY_MATES] == 'native'
    assert len(Native.mate_lists) == 1
    assert Native.mate_lists[0].declared_count == 1
    Restored = Native.mate_lists[0].mates[0]
    assert Restored.name == 'Coincident1'
    assert Restored.kind == 'coincident'
    assert Restored.alignment_code == 1
    assert tuple(((Entity.component_path, Entity.persistent_references[-1]) for Entity in Restored.entities)) == (('Piston-1@Engine/Piston-1@Piston', 'moPlaneSurfIdRep_c,1,2, '), ('', 'moPlaneSurfIdRep_c,3,4, '))

# keeps this focused behavior isolated so regressions remain immediately visible
def TestSLNMPIRWT() -> None:
    SourceDoc = DocumentWithoutSource(ReadSldprt(KConrod))
    Output = BytesIO()
    ResultInfo = WriteSldprt(SourceDoc, Output)
    Native = DecodeNativeAssembly(SldprtArchive.from_bytes(Output.getvalue()))
    Transfers = {ItemValue.capability: ItemValue.mode.value for ItemValue in ResultInfo.transfers}
    assert Transfers[Capability.ASSEMBLY_MATES] == 'native'
    assert sum((len(ItemValue.mates) for ItemValue in Native.mate_lists)) == len(SourceDoc.assembly.mates)
    assert tuple((MateInfo.name for ItemValue in Native.mate_lists for MateInfo in ItemValue.mates)) == tuple((MateInfo.name for MateInfo in SourceDoc.assembly.mates))

# keeps this focused behavior isolated so regressions remain immediately visible
def TestPSRECOI(TmpPath) -> None:
    SourceDoc = Document()
    Direct = TmpPath / 'direct.SLDPRT'
    Blocked = TmpPath / 'blocked.SLDPRT'
    with PytestLib.raises(ApplicationUsabilityError):
        WriteDocument(SourceDoc, Blocked, allow_carrier=False)
    assert not Blocked.exists()
    Written = WriteDocument(SourceDoc, Direct, allow_carrier=True)
    assert Written.metadata['compatibility'] == 'native-metadata-with-kit-neutral'
    Fcstd = TmpPath / 'source.FCStd'
    Converted = TmpPath / 'converted.SLDPRT'
    WriteFreecad(SourceDoc, Fcstd)
    BlockedConversion = TmpPath / 'blocked_conversion.SLDPRT'
    with PytestLib.raises(ApplicationUsabilityError):
        Convert(Fcstd, BlockedConversion, allow_carrier=False)
    assert not BlockedConversion.exists()
    ResultInfo = Convert(Fcstd, Converted, allow_carrier=True)
    assert ResultInfo.destination_format == 'solidworks.sldprt'
    assert ResultInfo.output.metadata['compatibility'] == 'native-metadata-with-kit-neutral'

# keeps this focused behavior isolated so regressions remain immediately visible
def TestANTSWMR(TmpPath) -> None:
    Original = OpenDocument(KSample)
    Changed = ReplaceData(Original, metadata=FrozenMapping({**Original.metadata, 'audit_change': True}))
    Carrier = TmpPath / 'carrier.SLDPRT'
    First = WriteDocument(Changed, Carrier)
    assert First.vendor_loadable is True
    assert First.near_lossless is True
    assert First.metadata['mode'] == 'template'
    Restored = OpenDocument(Carrier)
    Metadata = dict(Restored.metadata)
    assert Metadata.pop('solidworks.container_compatibility') == 'native-template'
    Stripped = ReplaceData(Restored, metadata=FrozenMapping(Metadata))
    Replay = TmpPath / 'replay.SLDPRT'
    ResultInfo = WriteDocument(Stripped, Replay)
    assert ResultInfo.vendor_loadable is True
    assert ResultInfo.near_lossless is True
    assert Replay.read_bytes() == Carrier.read_bytes()
    assert OpenDocument(Replay).feature_timeline == Restored.feature_timeline

# keeps this focused behavior isolated so regressions remain immediately visible
def TestPSDTPAW(TmpPath) -> None:
    SourceDoc = ReadSldprt(KAssembly)
    Portable = TmpPath / 'portable.SLDASM'
    PortableResult = WriteDocument(SourceDoc, Portable)
    assert PortableResult.metadata['compatibility'] == 'native-template'
    assert PortableResult.metadata['native_self_contained'] is True
    assert PortableResult.metadata['referenced_files_written'] == len(SourceDoc.assembly.documents)
    assert PortableResult.requirements == ()
    assert PortableResult.near_lossless is True
    assert ReadSldprt(Portable).assembly == SourceDoc.assembly
    Exact = TmpPath / 'exact.SLDASM'
    ExactResult = Registry.write(SourceDoc, Exact, options=WriteOptions(values={'portable': False, 'allow_carrier': True, 'require_self_contained': False}))
    assert ExactResult.metadata['compatibility'] == 'native-exact'
    assert ExactResult.metadata['native_self_contained'] is False
    assert ExactResult.requirements == ('referenced SOLIDWORKS component files',)
    assert ExactResult.near_lossless is False
    assert Exact.read_bytes() == KAssembly.read_bytes()

# keeps this focused behavior isolated so regressions remain immediately visible
def TestIPADTRC(TmpPath) -> None:
    Isolated = TmpPath / 'isolated' / KAssembly.name
    Isolated.parent.mkdir()
    Isolated.write_bytes(KAssembly.read_bytes())
    SourceDoc = ReadSldprt(Isolated)
    assert SourceDoc.assembly is not None
    assert SourceDoc.assembly.documents == ()
    assert SourceDoc.meshes
    Output = TmpPath / 'portable' / KAssembly.name
    ResultInfo = WriteDocument(SourceDoc, Output)
    assert ResultInfo.application_usable is False
    assert ResultInfo.vendor_loadable is False
    assert ResultInfo.metadata['native_self_contained'] is False
    assert ResultInfo.metadata['referenced_files_written'] == 0
    assert ResultInfo.requirements == ()
    assert tuple(Output.parent.iterdir()) == (Output,)
    Attestation = JsonLib.loads(SldprtArchive.open(Output).require(StreamG).decode('utf-8'))
    assert Attestation['compatibility'] == ResultInfo.metadata['compatibility']
    assert Attestation['application_usable'] is False
    assert Attestation['vendor_loadable'] is False
    Restored = ReadSldprt(Output)
    assert Restored.assembly == SourceDoc.assembly
    assert Restored.meshes == SourceDoc.meshes
    Blocked = TmpPath / 'blocked' / KAssembly.name
    with PytestLib.raises(ApplicationUsabilityError) as Captured:
        WriteDocument(SourceDoc, Blocked, allow_carrier=False)
    assert Captured.value.requirements == ('referenced SOLIDWORKS component files',)
    assert not Blocked.exists()

# keeps this focused behavior isolated so regressions remain immediately visible
def TestCDTRSRC(TmpPath) -> None:
    SourceDoc = OpenDocument(KCatproduct)
    Output = TmpPath / 'converted' / 'Tilton_Set.SLDASM'
    ResultInfo = Convert(KCatproduct, Output)
    assert ResultInfo.requirements == ()
    assert ResultInfo.application_usable is False
    assert ResultInfo.vendor_loadable is False
    assert ResultInfo.output.metadata['native_self_contained'] is False
    assert ResultInfo.output.metadata['referenced_files_written'] == len(SourceDoc.assembly.documents)
    Native = DecodeNativeAssembly(SldprtArchive.open(Output))
    Referenced = tuple((Output.parent / PureWindowsPath(Definition.source_path).name for Definition in Native.definitions if Definition.object_id != Native.root_definition_id))
    assert Referenced
    assert all((TargetPathA.is_file() for TargetPathA in Referenced))
    assert all((SldprtArchive.open(TargetPathA).records for TargetPathA in Referenced))
    Relocated = TmpPath / 'relocated' / Output.name
    Relocated.parent.mkdir()
    Relocated.write_bytes(Output.read_bytes())
    Restored = OpenDocument(Relocated)
    assert Restored.assembly == SourceDoc.assembly
    assert Restored.meshes == SourceDoc.meshes

# keeps this focused behavior isolated so regressions remain immediately visible
def TestPAPTMALP(TmpPath) -> None:
    SourceDoc = ReadSldprt(KAssembly)
    Assembly = SourceDoc.assembly
    Instance = Assembly.instances[0]
    TransformA = list(Instance.transform.values)
    TransformA[3] += 12.5
    MateInfo = Assembly.mates[0]
    Alignment = MateAlignment.ANTI_ALIGNED if MateInfo.alignment is MateAlignment.ALIGNED else MateAlignment.ALIGNED
    Component = Assembly.documents[0]
    PartDoc = Component.document
    ParameterA = PartDoc.parameters[0]
    TargetValue = float(ParameterA.value.value) + 0.5
    PartDoc = ReplaceData(PartDoc, parameters=(ReplaceData(ParameterA, value=ReplaceData(ParameterA.value, value=TargetValue)), *PartDoc.parameters[1:]))
    Edited = ReplaceData(SourceDoc, assembly=ReplaceData(Assembly, instances=(ReplaceData(Instance, transform=MatrixFour(tuple(TransformA))), *Assembly.instances[1:]), mates=(ReplaceData(MateInfo, alignment=Alignment), *Assembly.mates[1:]), documents=(ReplaceData(Component, document=PartDoc), *Assembly.documents[1:])))
    Output = TmpPath / 'edited.SLDASM'
    ResultInfo = WriteDocument(Edited, Output)
    assert ResultInfo.near_lossless is False
    assert ResultInfo.vendor_loadable is False
    assert ResultInfo.application_usable is False
    Rejection = next((ItemValue.message for ItemValue in ResultInfo.diagnostics if ItemValue.code == 'sldasm.vendor_reader_rejects'))
    assert f'donor_instance_diverged:{Instance.id}' in Rejection
    assert f'donor_mate_diverged:{MateInfo.id}' in Rejection
    assert ResultInfo.requirements == ()
    assert ResultInfo.metadata['referenced_files_written'] == len(Assembly.documents)
    Restored = ReadSldprt(Output)
    assert Restored.assembly.instances[0].transform == MatrixFour(tuple(TransformA))
    assert Restored.assembly.mates[0].alignment is Alignment
    assert Restored.assembly.documents[0].document.parameters[0].value.value == PytestLib.approx(TargetValue)

# keeps this focused behavior isolated so regressions remain immediately visible
def TestPACTLCDS(TmpPath) -> None:
    SourceDoc = ReadSldprt(KAssembly)
    Output = TmpPath / 'carried.SLDASM'
    ResultInfo = WriteDocument(SourceDoc, Output)
    assert ResultInfo.vendor_loadable is True
    assert ResultInfo.application_usable is True
    assert ResultInfo.metadata['compatibility'] == 'native-template'
    assert not [ItemValue for ItemValue in ResultInfo.diagnostics if ItemValue.code == 'sldasm.vendor_reader_rejects']
    Donor = SldprtArchive.open(KAssembly).streams
    Written = SldprtArchive.open(Output).streams
    for NameText in Streams:
        assert Written[NameText] == Donor[NameText]

# keeps this focused behavior isolated so regressions remain immediately visible
def TestPADWACIR(TmpPath) -> None:
    SourceDoc = ReadSldprt(KAssembly)
    Assembly = SourceDoc.assembly
    Removed = Assembly.instances[-1]
    Entities = tuple((Entity for Entity in Assembly.mate_entities if Removed.id not in Entity.instance_path))
    EntityIds = {Entity.id for Entity in Entities}
    Mates = tuple((MateInfo for MateInfo in Assembly.mates if set(MateInfo.entity_ids) <= EntityIds))
    MateIds = {MateInfo.id for MateInfo in Mates}
    Edited = ReplaceData(SourceDoc, assembly=ReplaceData(Assembly, instances=Assembly.instances[:-1], mate_entities=Entities, mates=Mates, mate_groups=tuple((ReplaceData(Group, mate_ids=tuple((ItemValue for ItemValue in Group.mate_ids if ItemValue in MateIds))) for Group in Assembly.mate_groups))))
    Output = TmpPath / 'shrunk.SLDASM'
    ResultInfo = Registry.write(Edited, Output, options=WriteOptions(validate=False, values={'portable': True, 'allow_carrier': True}))
    assert ResultInfo.vendor_loadable is False
    assert ResultInfo.application_usable is False
    Rejection = next((ItemValue.message for ItemValue in ResultInfo.diagnostics if ItemValue.code == 'sldasm.vendor_reader_rejects'))
    assert f'donor_instance_diverged:{Removed.id}' in Rejection
    Donor = SldprtArchive.open(KAssembly).streams
    Written = SldprtArchive.open(Output).streams
    for NameText in Streams:
        assert Written[NameText] == Donor[NameText]
