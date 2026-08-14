# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations as Annotations
from dataclasses import dataclass as Dataclass, field as Field
from enum import IntEnum
from pathlib import PureWindowsPath
import math as MathValue
import re as RegexLib
import struct as Struct
from types import MappingProxyType
from typing import Any as AnyValue, Iterable, Mapping, Sequence
import xml.etree.ElementTree as XmlTree
from interchange import AssemblyData as AsmData, ComponentDefinition, ComponentInstance, ComponentKind, Configuration as Config, MateAlignment, MateConstraint as MateRule, MateEntity, MateGroup, Matrix4 as MatrixFour, ValueKind
from convert.adapters.solidworks.container.Container import SldprtArchive, SldprtFormatError
from convert.adapters.solidworks.core.Display import NativeDisplayComponent, NativeTessellationFace as NativeTessellationFace, decode_display_lists as DecodeDisplayLists, decode_tessellation_faces as DecodeTessellationFaces
from convert.adapters.solidworks.container.Format import CLASS_MARKER as ClassMarker, COMPONENT_TREE_STREAM as ComponentTreeStream, DIMENSION_SCALAR_HEADERS as DimensionScalarHeaders, DISPLAY_LISTS_STREAM as DisplayListsStream, MATES_STREAM_NAME as MatesStreamName, MATES_STREAM_SUFFIX as MatesStreamSuffix, SERIALIZED_STRING_MARKER as SerializedStringMarker, dimension_scalar_value_offset as DimensionScalarValue, is_cad_path as IsCadPath, is_component_path as IsComponentPath

# this binding exists because shared behavior needs one stable value
KWideText = RegexLib.compile(b'(?:[ -~\\xa1-\\xff]\\x00){4,}')

# this binding exists because shared behavior needs one stable value
KMateAlignmentOffset = 159

# this binding exists because shared behavior needs one stable value
KMateEntityCountOffset = 164

# this binding exists because shared behavior needs one stable value
KMateRecordBodySize = 168

# this binding exists because shared behavior needs one stable value
KMateObjectPrefix = 32769

# this binding exists because shared behavior needs one stable value
KMateListNativeIdFlag = 65536

# this binding exists because shared behavior needs one stable value
KMateGroupEndSuffix = '___EndTag___'

# this binding exists because shared behavior needs one stable value
KMateLossExpression = 'expression_resolved_to_value'

# this binding exists because shared behavior needs one stable value
KMateLossEntityFrame = 'mate_entity_frame'

# this binding exists because shared behavior needs one stable value
KMateLossEntityRadius = 'mate_entity_radius'

# this binding exists because shared behavior needs one stable value
KMateLossValue = 'mate_value_unrepresentable'

# this binding exists because shared behavior needs one stable value
KMateLossValueMissing = 'mate_value_missing'

# this binding exists because shared behavior needs one stable value
KMateLossGroupNesting = 'mate_group_nesting'

# this binding exists because shared behavior needs one stable value
KMateLossGroupMembership = 'mate_group_membership'

# this binding exists because shared behavior needs one stable value
KMateLossOrphanEntity = 'unreferenced_mate_entity'

# this binding exists because shared behavior needs one stable value
KMateLossSuppressed = 'mate_suppressed_state'

# this binding exists because shared behavior needs one stable value
KMateLossNotDriving = 'mate_not_driving'

# this binding exists because shared behavior needs one stable value
KMateLossKind = 'mate_kind_has_no_native_class'

# this binding exists because shared behavior needs one stable value
KMateLossAlignment = 'mate_alignment_has_no_native_code'

# this binding exists because shared behavior needs one stable value
KMateLossEntityMissing = 'mate_entity_missing'

# this binding exists because shared behavior needs one stable value
KMateLossEntitySelection = 'mate_entity_carries_selection_id'

# this binding exists because shared behavior needs one stable value
KMateLossEntityRef = 'mate_entity_reference_is_not_a_persistent_token'

# this binding exists because shared behavior needs one stable value
KMateLossEntityComponent = 'mate_entity_component_path_unresolved'

# this binding exists because shared behavior needs one stable value
KMateLossName = 'mate_name_exceeds_native_string_limit'

# this binding exists because shared behavior needs one stable value
KMateLossRecord = 'mate_record_failed_redecode'

# this binding exists because shared behavior needs one stable value
KMateLossLaneCapacity = 'mate_lane_record_capacity'

# this binding exists because shared behavior needs one stable value
KMateBlockingLossReasons = frozenset({KMateLossValue, KMateLossValueMissing})

# this binding exists because shared behavior needs one stable value
KMateAdvisoryLossReasons = frozenset({KMateLossExpression, KMateLossEntityFrame, KMateLossEntityRadius, KMateLossGroupNesting, KMateLossGroupMembership, KMateLossOrphanEntity})

# this binding exists because shared behavior needs one stable value
KMateRejectionReasons = frozenset({KMateLossSuppressed, KMateLossNotDriving, KMateLossKind, KMateLossAlignment, KMateLossEntityMissing, KMateLossEntitySelection, KMateLossEntityRef, KMateLossEntityComponent, KMateLossName, KMateLossRecord, KMateLossLaneCapacity})

# this binding exists because shared behavior needs one stable value
KMateLossReasons = KMateBlockingLossReasons | KMateAdvisoryLossReasons | KMateRejectionReasons

# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class NativeMateType:
    locals().setdefault('__annotations__', {})
    __annotations__['code'] = 'int | None'
    __annotations__['api_name'] = 'str'
    __annotations__['kind'] = 'str'
    __annotations__['class_names'] = 'tuple[str, ...]'
    locals()['class_names'] = ()
    __annotations__['name_prefixes'] = 'tuple[str, ...]'
    locals()['name_prefixes'] = ()
    __annotations__['value_semantic'] = 'str'
    locals()['value_semantic'] = ''
    __annotations__['neutral_kind'] = 'str'
    locals()['neutral_kind'] = ''

# this definition exists because focused behavior needs one stable owner
class NativeMateCode(IntEnum):
    KAnyValue = 0
    KAligned = 1
    KAntiAligned = 2
    KClosest = 3
setattr(NativeMateCode, 'ANY', NativeMateCode.KAnyValue)
setattr(NativeMateCode, 'ALIGNED', NativeMateCode.KAligned)
setattr(NativeMateCode, 'ANTI_ALIGNED', NativeMateCode.KAntiAligned)
setattr(NativeMateCode, 'CLOSEST', NativeMateCode.KClosest)

# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class NativeMateA:
    locals().setdefault('__annotations__', {})
    __annotations__['code'] = 'NativeMateAlignmentCode'
    __annotations__['api_name'] = 'str'
    __annotations__['kind'] = 'str'

# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class NativeMateTypeA:
    locals().setdefault('__annotations__', {})
    __annotations__['code'] = 'int | None'
    __annotations__['api_name'] = 'str'
    __annotations__['kind'] = 'str'
    __annotations__['markers'] = 'tuple[str, ...]'
    locals()['markers'] = ()

# this binding exists because shared behavior needs one stable value
KNativeMateTypes = (NativeMateType(0, 'swMateCOINCIDENT', 'coincident', ('MateCoincident', 'moMateCoincident'), ('coincident',)), NativeMateType(1, 'swMateCONCENTRIC', 'concentric', ('MateConcentric', 'moMateConcentric'), ('concentric',)), NativeMateType(2, 'swMatePERPENDICULAR', 'perpendicular', ('MatePerpendicular', 'moMatePerpendicular'), ('perpendicular',)), NativeMateType(3, 'swMatePARALLEL', 'parallel', ('MateParallel', 'moMateParallel'), ('parallel',)), NativeMateType(4, 'swMateTANGENT', 'tangent', ('MateTangent', 'moMateTangent'), ('tangent',)), NativeMateType(5, 'swMateDISTANCE', 'distance', ('MateDistanceDim', 'MateLimitDistanceDim', 'moMateDistanceDim', 'moMateDistanceDim_c', 'moMateLimitDistanceDim', 'moMateLimitDistanceDim_c'), ('distance', 'limitdistance'), 'length'), NativeMateType(6, 'swMateANGLE', 'angle', ('MateLimitAngleDim', 'MatePlanarAngleDim', 'moMateAngleDim_c', 'moMateLimitAngleDim', 'moMateLimitAngleDim_c', 'moMatePlanarAngleDim', 'moMatePlanarAngleDim_c'), ('angle', 'limitangle'), 'angle'), NativeMateType(7, 'swMateUNKNOWN', 'native'), NativeMateType(8, 'swMateSYMMETRIC', 'symmetric', ('MateSymmetric', 'moMateSymmetric'), ('symmetric',)), NativeMateType(9, 'swMateCAMFOLLOWER', 'cam_tangent', ('MateCamTangent', 'moMateCamTangent'), ('cam', 'cammatetangent', 'camfollower'), neutral_kind='cam'), NativeMateType(10, 'swMateGEAR', 'gear', ('MateGearDim', 'moMateGearDim', 'moMateGearDim_c'), ('gear', 'gearmate'), 'ratio'), NativeMateType(11, 'swMateWIDTH', 'width', ('MateWidth', 'moMateWidth'), ('width', 'widthmate')), NativeMateType(12, 'swMateLOCKTOSKETCH', 'lock_to_sketch', ('moLockToSketchMate',), ('locktosketch', 'locktosketchmate'), neutral_kind='lock'), NativeMateType(13, 'swMateRACKPINION', 'rack_pinion', ('MateRackPinionDim', 'moMateRackPinionDim', 'moMateRackPinionDim_c'), ('rackpinion',), 'length'), NativeMateType(14, 'swMateMAXMATES', 'native'), NativeMateType(15, 'swMatePATH', 'path', ('MatePath', 'moMatePath'), ('path', 'pathmate')), NativeMateType(16, 'swMateLOCK', 'lock', ('MateInPlace', 'MateLock', 'moMateInPlace', 'moMateLock'), ('inplace', 'lock', 'lockmate')), NativeMateType(17, 'swMateSCREW', 'screw', ('MateScrew', 'moMateScrew', 'moMateScrewDim_c'), ('screw', 'screwmate'), 'length'), NativeMateType(18, 'swMateLINEARCOUPLER', 'linear_coupler', ('MateLinearCoupler', 'moMateLinearCoupler'), ('linearcoupler',), 'ratio'), NativeMateType(19, 'swMateUNIVERSALJOINT', 'universal_joint', ('MateUniversalJoint', 'moMateUniversalJoint'), ('universaljoint', 'universalmate')), NativeMateType(20, 'swMateCOORDINATE', 'coordinate', ('MateCoordinate', 'moMateCoordinate'), ('coordinate',)), NativeMateType(21, 'swMateSLOT', 'slot', ('MateSlot', 'moMateSlot'), ('slot', 'slotmate')), NativeMateType(22, 'swMateHINGE', 'hinge', ('MateHinge', 'moMateHinge'), ('hinge',)), NativeMateType(23, 'swMateSLIDER', 'slider', ('MateSlider', 'moMateSlider'), ('slider',)), NativeMateType(24, 'swMatePROFILECENTER', 'profile_center', ('MateProfileCenter', 'moMateProfileCenter'), ('profilecenter',)), NativeMateType(25, 'swMateMAGNETIC', 'magnetic', ('MateMagnetic', 'moMateMagnetic'), ('magnetic', 'magneticmate')))

# this binding exists because shared behavior needs one stable value
KNativeMateTypeExtensions = (NativeMateType(None, 'BELT', 'belt', ('moMateBeltDim_c',), ('beltmate',), 'ratio'), NativeMateType(None, 'BELT_GROUP', 'group', ('moBeltMateFolder_c',), ('beltmates',)), NativeMateType(None, 'MATE_REFERENCE_GROUP_FOLDER', 'group', ('MateReferenceGroupFolder',)))

# this binding exists because shared behavior needs one stable value
KNativeMateTypeRecords = (*KNativeMateTypes, *KNativeMateTypeExtensions)

# this definition exists because focused behavior needs one stable owner
def ClassifierMap(Records: Iterable[NativeMateType | NativeMateEntityType], AttrValue: str) -> Mapping[str, str]:
    Result: dict[str, str] = {}
    for Record in Records:
        for Value in getattr(Record, AttrValue):
            KeyValue = Value.casefold()
            Previous = Result.get(KeyValue)
            if Previous is not None and Previous != Record.kind:
                raise RuntimeError(f'conflicting classifier {Value!r}')
            Result[KeyValue] = Record.kind
    return MappingProxyType(Result)

# this binding exists because shared behavior needs one stable value
KMateKindByClass = ClassifierMap(KNativeMateTypeRecords, 'class_names')

# this binding exists because shared behavior needs one stable value
KMateKindByName = ClassifierMap(KNativeMateTypeRecords, 'name_prefixes')

# this binding exists because shared behavior needs one stable value
KMateValueSemantics = MappingProxyType({Record.kind: Record.value_semantic for Record in KNativeMateTypeRecords if Record.value_semantic})

# this binding exists because shared behavior needs one stable value
KNativeMateNeutralKind = MappingProxyType({Record.kind: Record.neutral_kind for Record in KNativeMateTypeRecords if Record.neutral_kind})

# this binding exists because shared behavior needs one stable value
KNativeMateAlignments = (NativeMateA(NativeMateCode.ANY, 'swMateReferenceAlignment_Any', 'unknown'), NativeMateA(NativeMateCode.ALIGNED, 'swMateReferenceAlignment_Aligned', 'aligned'), NativeMateA(NativeMateCode.ANTI_ALIGNED, 'swMateReferenceAlignment_AntiAligned', 'anti_aligned'), NativeMateA(NativeMateCode.CLOSEST, 'swMateReferenceAlignment_Closest', 'closest'))

# this binding exists because shared behavior needs one stable value
KNativeMateAlignmentByCoA = {int(Record.code): Record for Record in KNativeMateAlignments}

# this binding exists because shared behavior needs one stable value
KNativeMateEntityGeomTypA = (NativeMateTypeA(0, 'swMateUnsupported', 'native'), NativeMateTypeA(1, 'swMatePoint', 'point'), NativeMateTypeA(2, 'swMateLine', 'line'), NativeMateTypeA(3, 'swMatePlane', 'plane'), NativeMateTypeA(4, 'swMateCylinder', 'cylinder'), NativeMateTypeA(5, 'swMateCone', 'cone'), NativeMateTypeA(6, 'swMateSphere', 'sphere'), NativeMateTypeA(7, 'swMateCircle', 'circle'))

# this binding exists because shared behavior needs one stable value
KNativeMateEntityRefTypes = (NativeMateTypeA(0, 'swMateEntity2ReferenceType_Point', 'point', ('refpoint', 'point')), NativeMateTypeA(1, 'swMateEntity2ReferenceType_Line', 'line', ('line',)), NativeMateTypeA(2, 'swMateEntity2ReferenceType_Circle', 'circle', ('circle',)), NativeMateTypeA(3, 'swMateEntity2ReferenceType_Plane', 'plane', ('plane',)), NativeMateTypeA(4, 'swMateEntity2ReferenceType_Cylinder', 'cylinder', ('cylinder', 'wzdhole', 'sweepside')), NativeMateTypeA(5, 'swMateEntity2ReferenceType_Sphere', 'sphere', ('sphere',)), NativeMateTypeA(6, 'swMateEntity2ReferenceType_Set', 'native'), NativeMateTypeA(7, 'swMateEntity2ReferenceType_Cone', 'cone', ('cone',)), NativeMateTypeA(8, 'swMateEntity2ReferenceType_SweptSurface', 'surface', ('sweptsurface',)), NativeMateTypeA(9, 'swMateEntity2ReferenceType_MultipleSurface', 'surface', ('multiplesurface',)), NativeMateTypeA(10, 'swMateEntity2ReferenceType_GenSurface', 'surface', ('gensurface', 'generalsurface', 'surface')), NativeMateTypeA(11, 'swMateEntity2ReferenceType_Ellipse', 'curve', ('ellipse',)), NativeMateTypeA(12, 'swMateEntity2ReferenceType_GeneralCurve', 'curve', ('generalcurve', 'curve')), NativeMateTypeA(13, 'swMateEntity2ReferenceType_UNKNOWN', 'native'))

# this binding exists because shared behavior needs one stable value
KNativeMateEntityType = (NativeMateTypeA(None, 'SketchEntity', 'sketch_entity', ('^',)), NativeMateTypeA(None, 'CoordinateSystem', 'coordinate_system', ('coordinatesystem', 'coordsys')), NativeMateTypeA(None, 'Vertex', 'vertex', ('vertex',)), NativeMateTypeA(None, 'Axis', 'axis', ('axis',)), NativeMateTypeA(None, 'Edge', 'edge', ('edge',)), NativeMateTypeA(None, 'Face', 'face', ('face', 'surfidrep')))

# this binding exists because shared behavior needs one stable value
KNativeMateEntityTypeA = (KNativeMateEntityType[0], *KNativeMateEntityRefTypes, *KNativeMateEntityType[1:])

# this binding exists because shared behavior needs one stable value
KNativeMateEntityKindBy = ClassifierMap(KNativeMateEntityTypeA, 'markers')

# this binding exists because shared behavior needs one stable value
KNativeMateEntityMarkers = tuple(((Marker.casefold(), Record.kind) for Record in KNativeMateEntityTypeA for Marker in Record.markers))

# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class NativeAsmFile:
    locals().setdefault('__annotations__', {})
    __annotations__['object_id'] = 'int'
    __annotations__['document_type'] = 'str'
    __annotations__['creation_time'] = 'int'
    __annotations__['source_path'] = 'str'

# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class NativeAsmA:
    locals().setdefault('__annotations__', {})
    __annotations__['object_id'] = 'int'
    __annotations__['name'] = 'str'
    __annotations__['document_type'] = 'str'
    __annotations__['file_id'] = 'int'
    __annotations__['source_path'] = 'str'
    __annotations__['configuration_name'] = 'str'
    __annotations__['configuration_id'] = 'int'
    __annotations__['alternate_configuration_name'] = 'str'
    __annotations__['last_modified_stamp'] = 'int'
    __annotations__['configuration_flags'] = 'int'
    __annotations__['bounding_box_m'] = 'tuple[float, float, float, float, float, float] | None'
    __annotations__['child_occurrence_ids'] = 'tuple[int, ...]'
    __annotations__['attributes'] = 'tuple[tuple[str, str], ...]'

# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class NativeAsmItem:
    locals().setdefault('__annotations__', {})
    __annotations__['object_id'] = 'int'
    __annotations__['feature_id'] = 'int'
    __annotations__['owner_definition_id'] = 'int'
    __annotations__['definition_id'] = 'int'
    __annotations__['name'] = 'str'
    __annotations__['reference_number'] = 'int'
    __annotations__['component_reference'] = 'str'
    __annotations__['configuration_name'] = 'str'
    __annotations__['configuration_id'] = 'int'
    __annotations__['transform'] = 'tuple[float, ...]'
    __annotations__['transform_stamp'] = 'int'
    __annotations__['suppressed'] = 'bool'
    __annotations__['hidden'] = 'bool'
    __annotations__['flexible'] = 'bool'
    __annotations__['virtual'] = 'bool'
    __annotations__['exclude_from_bom'] = 'bool'
    __annotations__['zone'] = 'bool'
    __annotations__['display_mode'] = 'int'
    __annotations__['display_quality'] = 'int'
    __annotations__['edges_in_shaded_mode'] = 'bool'
    __annotations__['order'] = 'int'
    __annotations__['attributes'] = 'tuple[tuple[str, str], ...]'

# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class NativeAsmConfig:
    locals().setdefault('__annotations__', {})
    __annotations__['object_id'] = 'int'
    __annotations__['configuration_id'] = 'int'
    __annotations__['name'] = 'str'
    __annotations__['reference'] = 'str'
    __annotations__['model_id'] = 'int'
    __annotations__['most_recent'] = 'bool'
    __annotations__['needs_update'] = 'bool'
    __annotations__['attributes'] = 'tuple[tuple[str, str], ...]'

# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class NativeDisplay:
    locals().setdefault('__annotations__', {})
    __annotations__['object_id'] = 'int'
    __annotations__['name'] = 'str'
    __annotations__['configuration_id'] = 'int | None'
    __annotations__['attributes'] = 'tuple[tuple[str, str], ...]'

# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class NativeMateC:
    locals().setdefault('__annotations__', {})
    __annotations__['component_path'] = 'str'
    __annotations__['persistent_references'] = 'tuple[str, ...]'
    __annotations__['source_path'] = 'str'
    __annotations__['configuration_name'] = 'str'

# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class NativeMateB:
    locals().setdefault('__annotations__', {})
    __annotations__['name'] = 'str'
    __annotations__['value'] = 'float'
    __annotations__['value_offset'] = 'int'

# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class NativeMate:
    locals().setdefault('__annotations__', {})
    __annotations__['name'] = 'str'
    __annotations__['kind'] = 'str'
    __annotations__['owner_definition_id'] = 'int'
    __annotations__['order'] = 'int'
    __annotations__['entities'] = 'tuple[NativeMateEntity, ...]'
    __annotations__['record_offset'] = 'int'
    __annotations__['record_length'] = 'int'
    __annotations__['class_name'] = 'str'
    __annotations__['class_token'] = 'int | None'
    __annotations__['serialized_strings'] = 'tuple[str, ...]'
    __annotations__['alignment_code'] = 'int | None'
    __annotations__['dimensions'] = 'tuple[NativeMateDimension, ...]'

    # this definition exists because focused behavior needs one stable owner
    @property
    def ValueM(Instance) -> float | None:
        return Instance.dimensions[0].value if Instance.kind == 'distance' and Instance.dimensions else None

    # this definition exists because focused behavior needs one stable owner
    @property
    def ValueOffset(Instance) -> int | None:
        return Instance.dimensions[0].value_offset if Instance.kind == 'distance' and Instance.dimensions else None
    locals()['value_m'] = ValueM
    locals()['value_offset'] = ValueOffset

# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class NativeMateList:
    locals().setdefault('__annotations__', {})
    __annotations__['native_id'] = 'int'
    __annotations__['declared_count'] = 'int'
    __annotations__['owner_definition_id'] = 'int'
    __annotations__['mates'] = 'tuple[NativeMate, ...]'
    __annotations__['stream'] = 'str'

# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class MateRecord:
    locals().setdefault('__annotations__', {})
    __annotations__['name'] = 'str'
    __annotations__['name_end'] = 'int'
    __annotations__['start'] = 'int'
    __annotations__['end'] = 'int'
    __annotations__['class_name'] = 'str'
    __annotations__['class_token'] = 'int | None'
    __annotations__['strings'] = 'tuple[str, ...]'
    __annotations__['alignment_code'] = 'int | None'
    __annotations__['dimensions'] = 'tuple[NativeMateDimension, ...]'

# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class NativeItemPath:
    locals().setdefault('__annotations__', {})
    __annotations__['occurrence_id'] = 'int'
    __annotations__['definition_id'] = 'int'
    __annotations__['path'] = 'str'
    __annotations__['depth'] = 'int'

# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class NativeAsm:
    locals().setdefault('__annotations__', {})
    __annotations__['name'] = 'str'
    __annotations__['root_definition_id'] = 'int'
    __annotations__['files'] = 'tuple[NativeAssemblyFile, ...]'
    __annotations__['definitions'] = 'tuple[NativeAssemblyDefinition, ...]'
    __annotations__['occurrences'] = 'tuple[NativeAssemblyOccurrence, ...]'
    __annotations__['configurations'] = 'tuple[NativeAssemblyConfiguration, ...]'
    __annotations__['display_states'] = 'tuple[NativeDisplayState, ...]'
    __annotations__['occurrence_paths'] = 'tuple[NativeOccurrencePath, ...]'
    __annotations__['mate_lists'] = 'tuple[NativeMateList, ...]'
    __annotations__['display_components'] = 'tuple[NativeDisplayComponent, ...]'
    __annotations__['application_version'] = 'int'

# this definition exists because focused behavior needs one stable owner
def EmptyTupleMap() -> Mapping[str, tuple[str, ...]]:
    return MappingProxyType({})

# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class NativeMateD:
    locals().setdefault('__annotations__', {})
    __annotations__['streams'] = 'Mapping[str, bytes]'
    __annotations__['complete'] = 'bool'
    __annotations__['encoded_mate_ids'] = 'tuple[str, ...]'
    __annotations__['unsupported_mate_ids'] = 'tuple[str, ...]'
    __annotations__['losses'] = 'Mapping[str, tuple[str, ...]]'
    __annotations__['unsupported_reasons'] = 'Mapping[str, tuple[str, ...]]'
    locals()['unsupported_reasons'] = Field(default_factory=EmptyTupleMap)

# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class NativeAsmB:
    locals().setdefault('__annotations__', {})
    __annotations__['component_tree'] = 'bytes'
    __annotations__['mate_streams'] = 'Mapping[str, bytes]'
    __annotations__['definition_ids'] = 'Mapping[str, int]'
    __annotations__['occurrence_ids'] = 'Mapping[str, int]'
    __annotations__['structure_complete'] = 'bool'
    __annotations__['mates_complete'] = 'bool'
    __annotations__['unsupported_mate_ids'] = 'tuple[str, ...]'
    __annotations__['generated_mate_ids'] = 'tuple[str, ...]'
    locals()['generated_mate_ids'] = ()
    __annotations__['generated_mate_losses'] = 'Mapping[str, tuple[str, ...]]'
    locals()['generated_mate_losses'] = Field(default_factory=EmptyTupleMap)
    __annotations__['unsupported_mate_reasons'] = 'Mapping[str, tuple[str, ...]]'
    locals()['unsupported_mate_reasons'] = Field(default_factory=EmptyTupleMap)

# assembly encoding needs one immutable plan so xml phases share consistent identifiers
@Dataclass(frozen=True, slots=True)
class AsmEncodePlan:
    Definitions: tuple[ComponentDefinition, ...]
    Instances: tuple[ComponentInstance, ...]
    DefinitionById: Mapping[str, ComponentDefinition]
    SelectedConfigs: tuple[Configuration, ...]
    SourcePaths: Mapping[str, str]
    FileKeys: Mapping[str, tuple[str, str]]
    UniqueFileKeys: tuple[tuple[str, str], ...]
    DefinitionIds: Mapping[str, int]
    FileIds: Mapping[tuple[str, str], int]
    ItemIds: Mapping[str, int]
    ConfigIds: Mapping[str, int]


# native object allocation stays isolated so every xml phase consumes identical references
def BuildObjPrefs(
    Definitions: tuple[ComponentDefinition, ...],
    Instances: tuple[ComponentInstance, ...],
    Configs: tuple[Configuration, ...],
    FileKeys: Mapping[str, tuple[str, str]],
    UniqueKeys: tuple[tuple[str, str], ...],
) -> dict[tuple[str, str], int | None]:
    FilePrefs = {
        KeyValue: next(
            (
                PositiveInteger(Definition.attributes.get('native_file_id'))
                for Definition in Definitions
                if FileKeys[Definition.id] == KeyValue
                and PositiveInteger(Definition.attributes.get('native_file_id')) is not None
            ),
            None,
        )
        for KeyValue in UniqueKeys
    }
    ObjectPrefs: dict[tuple[str, str], int | None] = {}
    for Config in Configs:
        ObjectPrefs['configuration', Config.id] = PositiveInteger(Config.attributes.get('native_object_id'))
    for Definition in Definitions:
        ObjectPrefs['definition', Definition.id] = PreferredNative(Definition.id, 'sldasm:definition:', Definition.attributes.get('native_object_id'))
    for KeyValue in UniqueKeys:
        ObjectPrefs['file', repr(KeyValue)] = FilePrefs[KeyValue]
    for Instance in Instances:
        ObjectPrefs['occurrence', Instance.id] = PreferredNative(Instance.id, 'sldasm:instance:', Instance.attributes.get('native_object_id'))
    return ObjectPrefs


# assembly validation and allocation belong together so later phases only render trusted state
def BuildAsmPlan(
    AsmValue: AssemblyData,
    Configurations: Sequence[Configuration],
    ModelName: str,
    BundleNames: Mapping[str, str] | None,
) -> AsmEncodePlan:
    Definitions = tuple(AsmValue.definitions)
    Instances = tuple(AsmValue.instances)
    DefinitionById = {ItemValue.id: ItemValue for ItemValue in Definitions}
    if AsmValue.root_definition_id not in DefinitionById:
        raise SldprtFormatError('assembly root definition is missing')

    # active configuration ordering must remain deterministic across equivalent input sequences
    SelectedConfigs = tuple(sorted(Configurations, key=lambda ItemValue: (not ItemValue.active, Configurations.index(ItemValue))))
    if not SelectedConfigs:
        raise SldprtFormatError('assembly contains no configuration')
    Names = BundleNames or {}
    SourcePaths = {Definition.id: DefinitionPath(Definition, Definition.id == AsmValue.root_definition_id, ModelName, Names) for Definition in Definitions}
    FileKeys = {Definition.id: DefinitionFile(Definition, SourcePaths[Definition.id]) for Definition in Definitions}
    UniqueKeys = tuple(dict.fromkeys(FileKeys.values()))
    ObjectIds = AllocateObject(BuildObjPrefs(Definitions, Instances, SelectedConfigs, FileKeys, UniqueKeys))
    return AsmEncodePlan(
        Definitions,
        Instances,
        DefinitionById,
        SelectedConfigs,
        SourcePaths,
        FileKeys,
        UniqueKeys,
        {Definition.id: ObjectIds['definition', Definition.id] for Definition in Definitions},
        {KeyValue: ObjectIds['file', repr(KeyValue)] for KeyValue in UniqueKeys},
        {Instance.id: ObjectIds['occurrence', Instance.id] for Instance in Instances},
        {Config.id: ObjectIds['configuration', Config.id] for Config in SelectedConfigs},
    )


# file declarations remain separate because models may share one physical component source
def AddAsmHeader(RootValue: AnyValue, PlanValue: AsmEncodePlan) -> None:
    Header = XmlTree.SubElement(RootValue, 'swHeader', {'swObjCount': str(len(PlanValue.UniqueFileKeys))})
    for KeyValue in PlanValue.UniqueFileKeys:
        Definition = next((ItemValue for ItemValue in PlanValue.Definitions if PlanValue.FileKeys[ItemValue.id] == KeyValue))
        XmlTree.SubElement(Header, 'swFile', {'id': str(PlanValue.FileIds[KeyValue]), 'swDocType': DefinitionDoc(Definition), 'swCreationTime': str(IntegerAttr(Definition, 'native_creation_time', 0)), 'swPath': PlanValue.SourcePaths[Definition.id]})


# occurrence rendering stays focused so definition metadata cannot drift from child references
def AddAsmReference(
    ModelValue: AnyValue,
    Instance: ComponentInstance,
    Target: ComponentDefinition,
    ItemIndex: int,
    PlanValue: AsmEncodePlan,
) -> None:
    RefValue = RefNumber(Instance, ItemIndex + 1)
    XmlTree.SubElement(ModelValue, 'swReference', {'id': str(PlanValue.ItemIds[Instance.id]), 'swName': InstanceBase(Instance, RefValue), 'swReferenceNumber': str(RefValue), 'swComponentReference': str(Instance.attributes.get('component_reference', '')), 'swID': str(NativeFeatureId(Instance, ItemIndex)), 'swIsVirtualComponent': YesText(bool(Instance.attributes.get('virtual', False))), 'swConfigurationId': str(ConfigInteger(Instance.configuration_id)), 'swConfigurationName': Instance.configuration_name or Target.configuration_name or 'Default', 'swDisplayMode': str(IntegerAttr(Instance, 'display_mode', 6)), 'swHlrDisplayQuality': str(IntegerAttr(Instance, 'display_quality', 1)), 'swSuppressed': YesText(Instance.suppressed), 'swHidden': YesText(Instance.hidden), 'swEdgesInShadedMode': YesText(bool(Instance.attributes.get('edges_in_shaded_mode', False))), 'swFlexible': YesText(Instance.flexible), 'swExcludeFromBOM': YesText(Instance.exclude_from_bom), 'swZone': YesText(bool(Instance.attributes.get('zone', False))), 'swModelRef': str(PlanValue.DefinitionIds[Target.id]), 'swTransform': ' '.join((format(Value, '.17g') for Value in NativeMatrix(Instance.transform))), 'swTransformStamp': str(IntegerAttr(Instance, 'transform_stamp', 0))})


# one model renderer keeps optional metadata and owned occurrences under the same definition
def AddAsmModel(
    ModelList: AnyValue,
    Definition: ComponentDefinition,
    OwnedItems: list[tuple[int, ComponentInstance]],
    PlanValue: AsmEncodePlan,
    RootId: str,
) -> None:
    Attributes = {'id': str(PlanValue.DefinitionIds[Definition.id]), 'swName': Definition.name, 'swConfigurationName': Definition.configuration_name or 'Default', 'swConfigurationId': str(ConfigInteger(Definition.configuration_id)), 'swLastModifiedStamp': str(IntegerAttr(Definition, 'last_modified_stamp', 0)), 'swConfigurationFlags': str(IntegerAttr(Definition, 'configuration_flags', 0)), 'swFileRef': str(PlanValue.FileIds[PlanValue.FileKeys[Definition.id]])}
    Alternate = Definition.attributes.get('alternate_configuration_name')
    if isinstance(Alternate, str) and Alternate:
        Attributes['swConfigurationAlternateName'] = Alternate
    BoundingValue = NativeBounding(Definition)
    if BoundingValue:
        Attributes['swBoundingBox'] = BoundingValue
    if Definition.id == RootId:
        Attributes['swAssemblyFeatureEffectedComponents'] = ''
    ModelValue = XmlTree.SubElement(ModelList, 'swModel', Attributes)

    # occurrence order is part of the vendor tree identity and must remain stable
    SortedItems = sorted(OwnedItems, key=lambda ItemValue: (ItemValue[1].order, ItemValue[0]))
    for ItemIndex, Instance in SortedItems:
        Target = PlanValue.DefinitionById.get(Instance.definition_id)
        if Target is not None:
            AddAsmReference(ModelValue, Instance, Target, ItemIndex, PlanValue)


# model collection rendering stays independent because component ownership drives its own traversal
def AddAsmModels(RootValue: AnyValue, PlanValue: AsmEncodePlan, RootId: str) -> None:
    ModelList = XmlTree.SubElement(RootValue, 'swModelList', {'swObjCount': str(len(PlanValue.Definitions))})
    ChildItems: dict[str, list[tuple[int, ComponentInstance]]] = {}
    for ItemIndex, Instance in enumerate(PlanValue.Instances):
        ChildItems.setdefault(Instance.owner_definition_id, []).append((ItemIndex, Instance))
    for Definition in PlanValue.Definitions:
        AddAsmModel(ModelList, Definition, ChildItems.get(Definition.id, []), PlanValue, RootId)


# configuration rendering remains separate because active state does not affect component topology
def AddAsmConfigs(RootValue: AnyValue, PlanValue: AsmEncodePlan, RootId: str) -> None:
    ConfigList = XmlTree.SubElement(RootValue, 'swConfigurationList', {'swObjCount': str(len(PlanValue.SelectedConfigs))})
    for Config in PlanValue.SelectedConfigs:
        XmlTree.SubElement(ConfigList, 'swConfiguration', {'id': str(PlanValue.ConfigIds[Config.id]), 'swName': Config.name, 'swID': str(ConfigInteger(Config.attributes.get('native_configuration_id', 0))), 'swReference': PlanValue.DefinitionById[RootId].name, 'swMostRecentConfiguration': YesText(Config.active), 'swConfigurationNeedsUpdate': 'NO', 'swModelRef': str(PlanValue.DefinitionIds[RootId])})


# top level assembly encoding composes focused allocation xml and mate phases
def EncodeNativeAsm(AsmValue: AssemblyData, Configurations: Sequence[Configuration], ModelName: str, BundleNames: Mapping[str, str] | None=None) -> NativeAsmB:
    PlanValue = BuildAsmPlan(AsmValue, Configurations, ModelName, BundleNames)
    ObjectCount = max((*PlanValue.DefinitionIds.values(), *PlanValue.FileIds.values(), *PlanValue.ItemIds.values(), *PlanValue.ConfigIds.values()), default=0)
    RootValue = XmlTree.Element('swSolidWorks', {'xmlns': 'http://www.solidworks.com/sw2003/schema', 'swObjCount': str(ObjectCount), 'swVersion': '18000'})
    AddAsmHeader(RootValue, PlanValue)
    AddAsmModels(RootValue, PlanValue, AsmValue.root_definition_id)
    AddAsmConfigs(RootValue, PlanValue, AsmValue.root_definition_id)
    XmlTree.SubElement(RootValue, 'swExtFeatureList', {'swObjCount': '0'})
    Mates = EncodeMateA(AsmValue, PlanValue.Definitions, PlanValue.DefinitionById, PlanValue.DefinitionIds)
    ComponentTree = XmlTree.tostring(RootValue, encoding='utf-8', xml_declaration=True, short_empty_elements=True)
    StructureComplete = all((IsDefinition(Definition) for Definition in PlanValue.Definitions)) and all((Instance.definition_id in PlanValue.DefinitionById and Instance.owner_definition_id in PlanValue.DefinitionById for Instance in PlanValue.Instances)) and HasCoreState(AsmValue) and HasCoreBasis(AsmValue)
    return NativeAsmB(component_tree=ComponentTree, mate_streams=Mates.streams, definition_ids=MappingProxyType(PlanValue.DefinitionIds), occurrence_ids=MappingProxyType(PlanValue.ItemIds), structure_complete=StructureComplete, mates_complete=Mates.complete, unsupported_mate_ids=Mates.unsupported_mate_ids, generated_mate_ids=Mates.encoded_mate_ids, generated_mate_losses=Mates.losses, unsupported_mate_reasons=Mates.unsupported_reasons)

# this definition exists because focused behavior needs one stable owner
def HasCoreState(AsmValue: AssemblyData) -> bool:
    DirectItems = AsmValue.children(AsmValue.root_definition_id)
    return bool(DirectItems) and all((not InstanceItem.fixed and (not InstanceItem.suppressed) and (not InstanceItem.hidden) and (not InstanceItem.flexible) and (not InstanceItem.exclude_from_bom) and (not bool(InstanceItem.attributes.get('virtual', False))) and (not bool(InstanceItem.attributes.get('zone', False))) for InstanceItem in DirectItems))

# this definition exists because focused behavior needs one stable owner
def HasCoreBasis(AsmValue: AssemblyData) -> bool:
    DirectItems = AsmValue.children(AsmValue.root_definition_id)
    IdentityVals = (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)
    HasRotated = any(((MatrixValues[0], MatrixValues[4], MatrixValues[8], MatrixValues[1], MatrixValues[5], MatrixValues[9], MatrixValues[2], MatrixValues[6], MatrixValues[10]) != IdentityVals for MatrixValues in (InstanceItem.transform.values for InstanceItem in DirectItems)))
    if not HasRotated:
        return True
    UniqueDefs = {InstanceItem.definition_id for InstanceItem in DirectItems}
    return len(DirectItems) >= 4 or (len(DirectItems) >= 3 and len(UniqueDefs) > 1)

# this definition exists because focused behavior needs one stable owner
def IsDefinition(Definition: ComponentDefinition) -> bool:
    return str(Definition.kind) in {ComponentKind.PART.value, ComponentKind.ASSEMBLY.value}

# this definition exists because focused behavior needs one stable owner
def DefinitionDoc(Definition: ComponentDefinition) -> str:
    return 'ASSEMBLY' if str(Definition.kind) == ComponentKind.ASSEMBLY.value else 'PART'

# this definition exists because focused behavior needs one stable owner
def DefinitionPath(Definition: ComponentDefinition, RootValue: bool, ModelName: str, BundleNames: Mapping[str, str]) -> str:
    Suffix = '.SLDASM' if RootValue or DefinitionDoc(Definition) == 'ASSEMBLY' else '.SLDPRT'
    if RootValue:
        StemValue = PureWindowsPath(ModelName).stem or Definition.name or 'Assembly'
        return f'{FileStem(StemValue)}{Suffix}'
    Bundled = BundleNames.get(Definition.document_id) or BundleNames.get(Definition.id)
    if isinstance(Bundled, str) and Bundled:
        return Bundled
    for Choice in (Definition.attributes.get('native_source_path'), Definition.source_path):
        if not isinstance(Choice, str) or not Choice:
            continue
        if PureWindowsPath(Choice).suffix.casefold() == Suffix.casefold():
            return Choice
    return f'{FileStem(Definition.name or Definition.id)}{Suffix}'

# this definition exists because focused behavior needs one stable owner
def FileStem(Value: str) -> str:
    Result = ''.join(('_' if Character in '<>:"/\\|?*' else Character for Character in Value)).strip(' .')
    return Result or 'Component'

# this definition exists because focused behavior needs one stable owner
def DefinitionFile(Definition: ComponentDefinition, SourcePath: str) -> tuple[str, str | int, str]:
    NativeId = PositiveInteger(Definition.attributes.get('native_file_id'))
    if NativeId is not None:
        return ('native', NativeId, DefinitionDoc(Definition))
    return ('path', SourcePath.casefold(), DefinitionDoc(Definition))

# this definition exists because focused behavior needs one stable owner
def PreferredNative(Value: str, Prefix: str, AttrValue: Any) -> int | None:
    Native = PositiveInteger(AttrValue)
    if Native is not None:
        return Native
    if not Value.startswith(Prefix):
        return None
    return PositiveInteger(Value.removeprefix(Prefix).split(':', 1)[0])

# this definition exists because focused behavior needs one stable owner
def PositiveInteger(Value: Any) -> int | None:
    if isinstance(Value, bool):
        return None
    try:
        Result = int(Value)
    except (TypeError, ValueError):
        return None
    return Result if 0 < Result <= 2147483647 else None

# this definition exists because focused behavior needs one stable owner
def AllocateObject(Preferred: Mapping[tuple[str, str], int | None]) -> dict[tuple[str, str], int]:
    Counts: dict[int, int] = {}
    for Value in Preferred.values():
        if Value is not None:
            Counts[Value] = Counts.get(Value, 0) + 1
    Reserved = {Value for Value, Count in Counts.items() if Count == 1}
    Result: dict[tuple[str, str], int] = {}
    UsedValue: set[int] = set()
    Choice = 1
    for KeyValue, Value in Preferred.items():
        if Value in Reserved:
            Result[KeyValue] = Value
            UsedValue.add(Value)
            continue
        while Choice in UsedValue or Choice in Reserved:
            Choice += 1
        Result[KeyValue] = Choice
        UsedValue.add(Choice)
        Choice += 1
    return Result

# this definition exists because focused behavior needs one stable owner
def IntegerAttr(ItemValue: ComponentDefinition | ComponentInstance, NameValue: str, Default: int) -> int:
    Value = ItemValue.attributes.get(NameValue, Default)
    if isinstance(Value, bool):
        return Default
    try:
        return int(Value)
    except (TypeError, ValueError):
        return Default

# this definition exists because focused behavior needs one stable owner
def ConfigInteger(Value: Any) -> int:
    if isinstance(Value, bool):
        return 0
    try:
        return int(Value)
    except (TypeError, ValueError):
        return 0

# this definition exists because focused behavior needs one stable owner
def NativeBounding(Definition: ComponentDefinition) -> str:
    BoxValue = Definition.bounding_box
    if BoxValue is None:
        return ''
    Values = (BoxValue.minimum.x, BoxValue.minimum.y, BoxValue.minimum.z, BoxValue.maximum.x, BoxValue.maximum.y, BoxValue.maximum.z)
    if not all((MathValue.isfinite(Value) for Value in Values)):
        raise SldprtFormatError('component bounding box contains a non-finite value')
    return ' '.join((format(Value / 1000.0, '.17g') for Value in Values))

# this definition exists because focused behavior needs one stable owner
def RefNumber(Instance: ComponentInstance, Fallback: int) -> int:
    Value = PositiveInteger(Instance.reference_number)
    if Value is not None:
        return Value
    Match = RegexLib.search('-(\\d+)$', Instance.name)
    if Match is not None:
        Value = PositiveInteger(Match.group(1))
        if Value is not None:
            return Value
    Native = PositiveInteger(Instance.attributes.get('native_reference_number'))
    return Native or Fallback

# this definition exists because focused behavior needs one stable owner
def InstanceBase(Instance: ComponentInstance, RefNumber: int) -> str:
    Suffix = f'-{RefNumber}'
    return Instance.name[:-len(Suffix)] if Instance.name.endswith(Suffix) else Instance.name

# this definition exists because focused behavior needs one stable owner
def NativeFeatureId(Instance: ComponentInstance, Index: int) -> int:
    Value = PositiveInteger(Instance.attributes.get('native_feature_id'))
    if Value is not None:
        return Value
    return 24 + Index

# this definition exists because focused behavior needs one stable owner
def NativeMatrix(Matrix: Matrix4) -> tuple[float, ...]:
    Values = Matrix.values
    if len(Values) != 16 or not all((MathValue.isfinite(Value) for Value in Values)):
        raise SldprtFormatError('component transform contains a non-finite value')
    return (Values[0], Values[4], Values[8], Values[12], Values[1], Values[5], Values[9], Values[13], Values[2], Values[6], Values[10], Values[14], Values[3] / 1000.0, Values[7] / 1000.0, Values[11] / 1000.0, Values[15])

# this definition exists because focused behavior needs one stable owner
def YesText(Value: bool) -> str:
    return 'YES' if Value else 'NO'

# mate encoding state keeps lane failures and successful records synchronized across phases
@Dataclass(slots=True)
class MateEncodeState:
    Entities: Mapping[str, MateEntity]
    Losses: dict[str, tuple[str, ...]]
    Rejections: dict[str, tuple[str, ...]]
    Streams: dict[str, bytes]
    Encoded: list[str]
    Unsupported: list[str]


# orphan detection belongs at state creation so every lane observes the same loss inventory
def BuildMateState(AsmValue: AssemblyData) -> MateEncodeState:
    Entities = {Entity.id: Entity for Entity in AsmValue.mate_entities}
    Losses: dict[str, tuple[str, ...]] = {}
    Referenced = {EntityId for MateValue in AsmValue.mates for EntityId in MateValue.entity_ids}
    for EntityId in sorted(set(Entities) - Referenced):
        Losses[EntityId] = (KMateLossOrphanEntity,)
    return MateEncodeState(Entities, Losses, {}, {}, [], [])


# each planned item updates one lane so group and mate failures remain locally attributable
def AppendMateMut(
    StateValue: MateEncodeState,
    ItemValue: MateRule | MateGroup,
    RecordList: list[bytes],
    LayoutList: list[tuple[str, MateRule | MateGroup]],
    AsmValue: AssemblyData,
    Definitions: Mapping[str, ComponentDefinition],
) -> None:
    if isinstance(ItemValue, MateGroup):
        PairValue = EncodeGroup(ItemValue)
        if PairValue is None:
            StateValue.Losses[ItemValue.id] = WithReason(StateValue.Losses.get(ItemValue.id, ()), KMateLossGroupMembership)
            return
        RecordList.extend(PairValue)
        LayoutList.extend((('group_start', ItemValue), ('group_end', ItemValue)))
        return
    Record, Reasons = EncodeMate(ItemValue, StateValue.Entities, AsmValue, Definitions)
    if Record is None:
        StateValue.Unsupported.append(ItemValue.id)
        StateValue.Rejections[ItemValue.id] = Reasons
        return
    RecordList.append(Record)
    LayoutList.append(('mate', ItemValue))
    if Reasons:
        StateValue.Losses[ItemValue.id] = MergedReasons(StateValue.Losses.get(ItemValue.id, ()), Reasons)


# lane completion centralizes capacity and roundtrip checks before publishing any generated bytes
def FinishLaneMut(
    StateValue: MateEncodeState,
    OwnerId: str,
    LaneValue: int,
    RecordList: list[bytes],
    LayoutList: list[tuple[str, MateRule | MateGroup]],
    DefinitionIds: Mapping[str, int],
    AsmValue: AssemblyData,
    Definitions: Mapping[str, ComponentDefinition],
) -> None:
    Planned = tuple((ItemValue.id for RoleValue, ItemValue in LayoutList if RoleValue == 'mate'))
    if not Planned or len(RecordList) > 65535:
        StateValue.Unsupported.extend(Planned)
        for MateId in Planned:
            StateValue.Rejections[MateId] = (KMateLossLaneCapacity,)
        return
    StreamName = f'Contents/Config-{LaneValue}-MatesList'
    NativeId = (DefinitionIds[OwnerId] | KMateListNativeIdFlag) & 4294967295
    StreamData = Struct.pack('<IH', NativeId, len(RecordList)) + b''.join(RecordList)
    if not IsVerifyMateMut(StreamData, StreamName, DefinitionIds[OwnerId], LayoutList, StateValue.Entities, AsmValue, Definitions, StateValue.Losses):
        StateValue.Unsupported.extend(Planned)
        for MateId in Planned:
            StateValue.Rejections[MateId] = (KMateLossRecord,)
        return
    StateValue.Streams[StreamName] = StreamData
    StateValue.Encoded.extend(Planned)


# one lane coordinator prevents record planning from leaking into aggregate completion logic
def EncodeLaneMut(
    StateValue: MateEncodeState,
    AsmValue: AssemblyData,
    OwnerId: str,
    LaneValue: int,
    Definitions: Mapping[str, ComponentDefinition],
    DefinitionIds: Mapping[str, int],
) -> None:
    RecordList: list[bytes] = []
    LayoutList: list[tuple[str, MateRule | MateGroup]] = []
    for ItemValue in MateOwnerPlaMut(AsmValue, OwnerId, StateValue.Losses):
        AppendMateMut(StateValue, ItemValue, RecordList, LayoutList, AsmValue, Definitions)
    FinishLaneMut(StateValue, OwnerId, LaneValue, RecordList, LayoutList, DefinitionIds, AsmValue, Definitions)


# aggregate encoding composes independent lanes and derives one explicit completeness attestation
def EncodeMateA(AsmValue: AssemblyData, OrderedDefinitions: Sequence[ComponentDefinition], Definitions: Mapping[str, ComponentDefinition], DefinitionIds: Mapping[str, int]) -> NativeMateD:
    if not AsmValue.mates and (not AsmValue.mate_entities) and (not AsmValue.mate_groups):
        return NativeMateD(MappingProxyType({}), True, (), (), MappingProxyType({}))
    StateValue = BuildMateState(AsmValue)
    LaneValues = MateStreamLanes(AsmValue, OrderedDefinitions, Definitions)
    for OwnerId, LaneValue in LaneValues.items():
        EncodeLaneMut(StateValue, AsmValue, OwnerId, LaneValue, Definitions, DefinitionIds)
    Blocking = any((Reason in KMateBlockingLossReasons for Reasons in StateValue.Losses.values() for Reason in Reasons))
    Complete = not StateValue.Unsupported and (not Blocking) and (len(StateValue.Encoded) == len(AsmValue.mates)) and (bool(AsmValue.mates) == bool(StateValue.Streams))
    return NativeMateD(MappingProxyType(StateValue.Streams), Complete, tuple(StateValue.Encoded), tuple(dict.fromkeys(StateValue.Unsupported)), MappingProxyType(dict(sorted(StateValue.Losses.items()))), MappingProxyType(dict(sorted(StateValue.Rejections.items()))))

# this definition exists because focused behavior needs one stable owner
def WithReason(Reasons: tuple[str, ...], Reason: str) -> tuple[str, ...]:
    return tuple(dict.fromkeys((*Reasons, Reason)))

# this definition exists because focused behavior needs one stable owner
def MergedReasons(Reasons: tuple[str, ...], Added: Iterable[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys((*Reasons, *Added)))

# this definition exists because focused behavior needs one stable owner
def MateStreamLanes(AsmValue: AssemblyData, OrderedDefinitions: Sequence[ComponentDefinition], Definitions: Mapping[str, ComponentDefinition]) -> dict[str, int]:
    Owners = [Owner for Owner in dict.fromkeys((AsmValue.root_definition_id, *(MateValue.owner_definition_id for MateValue in AsmValue.mates), *(Group.owner_definition_id for Group in AsmValue.mate_groups))) if Owner in Definitions]
    Order = {Definition.id: Index for Index, Definition in enumerate(OrderedDefinitions)}

    # this callback exists because local behavior needs one focused transformation
    Remaining = sorted((Owner for Owner in Owners if Owner != AsmValue.root_definition_id), key=lambda Value: (Order.get(Value, len(Order)), Value))
    Result = {AsmValue.root_definition_id: 0}
    for LaneValue, Owner in enumerate(Remaining, start=1):
        Result[Owner] = LaneValue
    return Result

# this definition exists because focused behavior needs one stable owner
def MateOwnerPlaMut(AsmValue: AssemblyData, OwnerId: str, Losses: dict[str, tuple[str, ...]]) -> tuple[MateRule | MateGroup, ...]:
    Mates = {MateValue.id: MateValue for MateValue in AsmValue.mates if MateValue.owner_definition_id == OwnerId}

    # this callback exists because local behavior needs one focused transformation
    OrderedMates = tuple((ItemValue[1] for ItemValue in sorted(enumerate(Mates.values()), key=lambda ItemValue: (ItemValue[1].order, ItemValue[0]))))

    # this callback exists because local behavior needs one focused transformation
    Groups = tuple((ItemValue[1] for ItemValue in sorted(enumerate((Group for Group in AsmValue.mate_groups if Group.owner_definition_id == OwnerId)), key=lambda ItemValue: (ItemValue[1].order, ItemValue[0]))))
    Assigned: dict[str, list[str]] = {}
    Claimed: set[str] = set()
    for Group in Groups:
        if Group.parent_group_id:
            Losses[Group.id] = WithReason(Losses.get(Group.id, ()), KMateLossGroupNesting)
        Members: list[str] = []
        for MateId in Group.mate_ids:
            if MateId not in Mates or MateId in Claimed:
                Losses[Group.id] = WithReason(Losses.get(Group.id, ()), KMateLossGroupMembership)
                continue
            Claimed.add(MateId)
            Members.append(MateId)
        Assigned[Group.id] = Members
    PlanValue: list[MateRule | MateGroup] = [MateValue for MateValue in OrderedMates if MateValue.id not in Claimed]
    for Group in Groups:
        PlanValue.append(Group)
        PlanValue.extend((Mates[MateId] for MateId in Assigned[Group.id]))
    return tuple(PlanValue)

# this definition exists because focused behavior needs one stable owner
def IsVerifyMateMut(Stream: bytes, StreamName: str, OwnerNativeId: int, Layout: Sequence[tuple[str, MateConstraint | MateGroup]], Entities: Mapping[str, MateEntity], AsmValue: AssemblyData, Definitions: Mapping[str, ComponentDefinition], Losses: dict[str, tuple[str, ...]]) -> bool:
    try:
        Decoded = DecodeMateList(Stream, StreamName, OwnerNativeId)
    except SldprtFormatError:
        return False
    if len(Decoded.mates) != len(Layout):
        return False
    for (RoleValue, Source), Target in zip(Layout, Decoded.mates):
        if RoleValue == 'mate':
            if not isinstance(Source, MateRule) or not IsEncodedMate(Source, Target, Entities, AsmValue, Definitions):
                return False
            continue
        ExpectedName = Source.name if RoleValue == 'group_start' else f'{Source.name}{KMateGroupEndSuffix}'
        if Target.kind != 'group' or Target.name != ExpectedName:
            return False
    Expected = ExpectedGroup(Layout)
    Actual = DecodedGroup(Decoded)
    for Order, Group in Expected.items():
        if Actual.get(Order, ()) != Group[1]:
            Losses[Group[0].id] = WithReason(Losses.get(Group[0].id, ()), KMateLossGroupMembership)
    return True

# this definition exists because focused behavior needs one stable owner
def ExpectedGroup(Layout: Sequence[tuple[str, MateConstraint | MateGroup]]) -> dict[int, tuple[MateGroup, tuple[int, ...]]]:
    Result: dict[int, tuple[MateGroup, tuple[int, ...]]] = {}
    Starts = [Index for Index, (RoleValue, Ignored) in enumerate(Layout) if RoleValue == 'group_start']
    for Position, Index in enumerate(Starts):
        Group = Layout[Index][1]
        if not isinstance(Group, MateGroup):
            continue
        Limit = Starts[Position + 1] if Position + 1 < len(Starts) else len(Layout)
        Result[Index] = (Group, tuple(range(Index + 2, Limit)))
    return Result

# this definition exists because focused behavior needs one stable owner
def DecodedGroup(Decoded: NativeMateList) -> dict[int, tuple[int, ...]]:
    Records = Decoded.mates
    Markers = tuple((Record for Record in Records if Record.kind == 'group'))
    Result: dict[int, tuple[int, ...]] = {}
    for PairIndex in range(0, len(Markers) - 1, 2):
        Marker = Markers[PairIndex]
        EndValue = Markers[PairIndex + 1]
        Limit = Markers[PairIndex + 2].order if PairIndex + 2 < len(Markers) else len(Records)
        Members: list[int] = []
        for Choice in Records:
            if Choice.order <= EndValue.order or Choice.order >= Limit or Choice.kind == 'group':
                continue
            Members.append(Choice.order)
            if Choice.kind == 'lock_to_sketch':
                break
        Result[Marker.order] = tuple(Members)
    return Result

# this definition exists because focused behavior needs one stable owner
def EncodeGroup(Group: MateGroup) -> tuple[bytes, bytes] | None:
    ClassName = NativeGroup(Group)
    Start = EncodeRecord(Group.name, ClassName, 0)
    EndValue = EncodeRecord(f'{Group.name}{KMateGroupEndSuffix}', ClassName, 0)
    if Start is None or EndValue is None:
        return None
    return (Start, EndValue)

# this definition exists because focused behavior needs one stable owner
def NativeGroup(Group: MateGroup) -> str:
    Candidates = tuple((Record for Record in KNativeMateTypeRecords if Record.kind == 'group' and Record.class_names))
    Requested = Group.attributes.get('native_class_name')
    if isinstance(Requested, str):
        for Record in Candidates:
            if Requested in Record.class_names:
                return Requested
    Lowered = Group.name.casefold()
    for Record in Candidates:
        if any((Lowered.startswith(Prefix) for Prefix in Record.name_prefixes)):
            return Record.class_names[0]
    return Candidates[0].class_names[0]

# this definition exists because focused behavior needs one stable owner
def EncodeRecord(NameValue: str, ClassName: str, EntityCount: int) -> bytes | None:
    SerializedName = Serialized(NameValue)
    if SerializedName is None:
        return None
    try:
        EncodedClass = ClassName.encode('ascii')
    except UnicodeEncodeError:
        return None
    Record = bytearray(ClassMarker + Struct.pack('<H', len(EncodedClass)) + EncodedClass + Struct.pack('<H', KMateObjectPrefix) + SerializedName)
    BodyValue = bytearray(KMateRecordBodySize)
    Struct.pack_into('<I', BodyValue, KMateEntityCountOffset, EntityCount)
    Record.extend(BodyValue)
    return bytes(Record)

# this definition exists because focused behavior needs one stable owner
def EncodeMate(MateValue: MateConstraint, Entities: Mapping[str, MateEntity], AsmValue: AssemblyData, Definitions: Mapping[str, ComponentDefinition]) -> tuple[bytes | None, tuple[str, ...]]:
    if MateValue.suppressed:
        return (None, (KMateLossSuppressed,))
    if not MateValue.driving:
        return (None, (KMateLossNotDriving,))
    NativeKind, ClassName = NativeMateClass(MateValue)
    if not ClassName:
        return (None, (KMateLossKind,))
    Reasons: list[str] = [KMateLossExpression] if MateValue.parameter_ids else []
    EntityValues: list[str] = []
    for EntityId in MateValue.entity_ids:
        Entity = Entities.get(EntityId)
        if Entity is None or Entity.owner_definition_id != MateValue.owner_definition_id:
            return (None, (KMateLossEntityMissing,))
        Values, EntityReasons = MateEntityA(Entity, AsmValue, Definitions)
        if Values is None:
            return (None, EntityReasons)
        EntityValues.extend(Values)
        Reasons.extend(EntityReasons)
    AlignmentCode = MateAlignmentB(MateValue.alignment)
    if AlignmentCode is None:
        return (None, (KMateLossAlignment,))
    Dimensions, ValueReasons = MateDimension(MateValue, NativeKind)
    Reasons.extend(ValueReasons)
    Record = bytearray(EncodeRecord(MateValue.name, ClassName, len(MateValue.entity_ids)) or b'')
    if not Record:
        return (None, (KMateLossName,))
    Struct.pack_into('<H', Record, len(Record) - KMateRecordBodySize + KMateAlignmentOffset, AlignmentCode)
    for Value in EntityValues:
        Serialized = Serialized(Value)
        if Serialized is None:
            return (None, (KMateLossEntityRef,))
        Record.extend(Serialized)
    for NameValue, Value in Dimensions:
        Serialized = Serialized(NameValue)
        if Serialized is None:
            return (None, (KMateLossName,))
        Record.extend(Serialized)
        Record.extend(DimensionScalarHeaders[0])
        Record.extend(Struct.pack('<d', Value))
    return (bytes(Record), tuple(dict.fromkeys(Reasons)))

# this definition exists because focused behavior needs one stable owner
def NativeMateClass(MateValue: MateConstraint) -> tuple[str, str]:
    Neutral = str(MateValue.kind)
    Requested = MateValue.attributes.get('native_kind')
    Candidates = tuple((Record for Record in KNativeMateTypeRecords if Record.class_names and (Record.neutral_kind or Record.kind) == Neutral))
    if isinstance(Requested, str):
        Selected = next((Record for Record in Candidates if Record.kind == Requested), None)
        if Selected is not None:
            ClassName = MateValue.attributes.get('native_class_name')
            if isinstance(ClassName, str) and ClassName in Selected.class_names:
                return (Selected.kind, ClassName)
            return (Selected.kind, Selected.class_names[0])
    if not Candidates:
        return ('', '')
    return (Candidates[0].kind, Candidates[0].class_names[0])

# this definition exists because focused behavior needs one stable owner
def MateEntityA(Entity: MateEntity, AsmValue: AssemblyData, Definitions: Mapping[str, ComponentDefinition]) -> tuple[tuple[str, ...] | None, tuple[str, ...]]:
    if Entity.selection_id:
        return (None, (KMateLossEntitySelection,))
    Reasons: list[str] = []
    if Entity.frame is not None and (not IsIdentity(Entity.frame)):
        Reasons.append(KMateLossEntityFrame)
    if Entity.radius is not None:
        Reasons.append(KMateLossEntityRadius)
    Persistent = Entity.attributes.get('persistent_references')
    if isinstance(Persistent, tuple) and all((isinstance(Value, str) for Value in Persistent)):
        References = Persistent
    elif Entity.source_entity_id:
        References = (Entity.source_entity_id,)
    else:
        return (None, (KMateLossEntityRef,))
    if not References or References[-1] != Entity.source_entity_id:
        return (None, (KMateLossEntityRef,))
    ComponentPath = NativeComponent(Entity.instance_path, AsmValue, Definitions, Entity.owner_definition_id)
    if ComponentPath is None:
        return (None, (KMateLossEntityComponent,))
    Values: list[str] = []
    if ComponentPath:
        if all((Value.casefold().startswith('mo') for Value in References)):
            Values.extend(References)
            Values.append(ComponentPath)
        elif all(('@' in Value and '^' not in Value for Value in References)):
            Values.append(ComponentPath)
            Values.extend(References)
        else:
            return (None, (KMateLossEntityRef,))
    else:
        if not all((Value.casefold().startswith('mo') or ('^' in Value and '@' in Value) for Value in References)):
            return (None, (KMateLossEntityRef,))
        Values.extend(References)
    SourcePath = Entity.attributes.get('source_path')
    if isinstance(SourcePath, str) and SourcePath:
        Values.append(SourcePath)
    return (tuple(Values), tuple(dict.fromkeys(Reasons)))

# this definition exists because focused behavior needs one stable owner
def IsIdentity(Matrix: Matrix4) -> bool:
    return Matrix.values == MatrixFour().values

# this definition exists because focused behavior needs one stable owner
def NativeComponent(PathValue: Sequence[str], AsmValue: AssemblyData, Definitions: Mapping[str, ComponentDefinition], OwnerDefinitionId: str='') -> str | None:
    if not PathValue:
        return ''
    Instances = {Instance.id: Instance for Instance in AsmValue.instances}
    Result: list[str] = []
    OwnerId = OwnerDefinitionId or AsmValue.root_definition_id
    for Index, InstanceId in enumerate(PathValue):
        Instance = Instances.get(InstanceId)
        Owner = Definitions.get(OwnerId)
        if Instance is None or Owner is None or Instance.owner_definition_id != OwnerId:
            return None
        RefNumber = RefNumber(Instance, Index + 1)
        Result.append(f'{InstanceBase(Instance, RefNumber)}-{RefNumber}@{Owner.name}')
        OwnerId = Instance.definition_id
    return '/'.join(Result)

# this definition exists because focused behavior needs one stable owner
def MateAlignmentB(Value: MateAlignment | str) -> int | None:
    KindValue = str(Value)
    return next((int(Record.code) for Record in KNativeMateAlignments if Record.kind == KindValue), None)

# this definition exists because focused behavior needs one stable owner
def MateDimension(MateValue: MateConstraint, NativeKind: str) -> tuple[tuple[tuple[str, float], ...], tuple[str, ...]]:
    if KMateValueSemantics.get(NativeKind) is not None and MateValue.value is None:
        return ((), (KMateLossValueMissing,))
    Resolved = ResolvedMate(MateValue, NativeKind)
    if Resolved is None:
        return ((), (KMateLossValue,))
    return (Resolved, ())

# this definition exists because focused behavior needs one stable owner
def ResolvedMate(MateValue: MateConstraint, NativeKind: str) -> tuple[tuple[str, float], ...] | None:
    Semantic = KMateValueSemantics.get(NativeKind)
    if Semantic is None:
        return () if MateValue.value is None else None
    Value = MateValue.value
    if Value is None or isinstance(Value.value, bool) or (not isinstance(Value.value, (int, float))):
        return None
    Number = float(Value.value)
    if not MathValue.isfinite(Number):
        return None
    Dimensions = MateValue.attributes.get('native_dimensions')
    Names = tuple((ItemValue.get('name', '') for ItemValue in Dimensions if isinstance(ItemValue, Mapping) and isinstance(ItemValue.get('name', ''), str))) if isinstance(Dimensions, tuple) else ()
    FirstName = Names[0] if Names and Names[0] else 'D1'
    if Semantic == 'length' and Value.kind is ValueKind.LENGTH:
        Factor = {'': 1.0, 'mm': 1.0, 'cm': 10.0, 'm': 1000.0, 'in': 25.4}.get(Value.unit.casefold())
        return ((FirstName, Number * Factor / 1000.0),) if Factor is not None else None
    if Semantic == 'angle' and Value.kind is ValueKind.ANGLE:
        Factor = {'': 1.0, 'rad': 1.0, 'deg': MathValue.pi / 180.0}.get(Value.unit.casefold())
        return ((FirstName, Number * Factor),) if Factor is not None else None
    if Semantic == 'ratio' and Value.kind is ValueKind.NUMBER:
        Denominator = 1.0
        if isinstance(Dimensions, tuple) and len(Dimensions) >= 2:
            Choice = Dimensions[1]
            if isinstance(Choice, Mapping) and isinstance(Choice.get('value'), (int, float)):
                Denominator = float(Choice['value'])
        if not MathValue.isfinite(Denominator) or Denominator == 0.0:
            return None
        SecondName = Names[1] if len(Names) > 1 and Names[1] else 'D2'
        return ((FirstName, Number * Denominator), (SecondName, Denominator))
    return None

# this definition exists because focused behavior needs one stable owner
def Serialized(Value: str) -> bytes | None:
    Encoded = Value.encode('utf-16le')
    Units = len(Encoded) // 2
    if Units > 254:
        return None
    return SerializedStringMarker + bytes((Units,)) + Encoded

# this definition exists because focused behavior needs one stable owner
def IsEncodedMate(Source: MateConstraint, Target: NativeMate, Entities: Mapping[str, MateEntity], AsmValue: AssemblyData, Definitions: Mapping[str, ComponentDefinition]) -> bool:
    NativeKind, Ignored = NativeMateClass(Source)
    if Target.name != Source.name or Target.kind != NativeKind:
        return False
    ExpectedEntities: list[tuple[str, str]] = []
    for EntityId in Source.entity_ids:
        Entity = Entities.get(EntityId)
        if Entity is None:
            return False
        ComponentPath = NativeComponent(Entity.instance_path, AsmValue, Definitions, Entity.owner_definition_id)
        ExpectedEntities.append((ComponentPath or '', Entity.source_entity_id))
    ActualEntities = [(Entity.component_path, Entity.persistent_references[-1] if Entity.persistent_references else '') for Entity in Target.entities]
    if ActualEntities != ExpectedEntities:
        return False
    ExpectedAlignment = MateAlignmentB(Source.alignment)
    if len(Source.entity_ids) == 2 and Target.alignment_code != ExpectedAlignment:
        return False
    Dimensions, Ignored = MateDimension(Source, NativeKind)
    if len(Dimensions) != len(Target.dimensions):
        return False
    return all((ExpectedName == Actual.name and MathValue.isclose(ExpectedValue, Actual.value, rel_tol=1e-12, abs_tol=1e-12) for (ExpectedName, ExpectedValue), Actual in zip(Dimensions, Target.dimensions)))

# this definition exists because focused behavior needs one stable owner
def DecodeNativeAsm(Archive: SldprtArchive, *, IncludeTessellation: bool=False) -> NativeAsm:
    RootValue = XmlRoot(Archive.require(ComponentTreeStream))
    Files = Files(RootValue)
    FileById = {ItemValue.object_id: ItemValue for ItemValue in Files}
    Definitions, Occurrences = Models(RootValue, FileById)
    Configurations = Configurations(RootValue)
    if not Configurations:
        raise SldprtFormatError('assembly contains no configuration')
    RootDefinitionId = Configurations[0].model_id
    DefinitionById = {ItemValue.object_id: ItemValue for ItemValue in Definitions}
    if RootDefinitionId not in DefinitionById:
        raise SldprtFormatError('assembly configuration references a missing model')
    ItemPaths = ExpandItemPaths(RootDefinitionId, Definitions, Occurrences)
    MateLists = MateLists(Archive, RootDefinitionId)
    DisplayComponents: tuple[NativeDisplayComponent, ...] = ()
    Display = Archive.get(DisplayListsStream)
    if IncludeTessellation and Display:
        DisplayComponents = DecodeDisplayLists(Display)
    return NativeAsm(name=DefinitionById[RootDefinitionId].name, root_definition_id=RootDefinitionId, files=Files, definitions=Definitions, occurrences=Occurrences, configurations=Configurations, display_states=DisplayStates(RootValue), occurrence_paths=ItemPaths, mate_lists=MateLists, display_components=DisplayComponents, application_version=Integer(RootValue.attrib.get('swVersion')))

# this definition exists because focused behavior needs one stable owner
def DecodeMateList(DataValue: bytes, Stream: str='', OwnerDefinitionId: int=0) -> NativeMateList:
    if len(DataValue) < 6:
        raise SldprtFormatError(f'mate stream is truncated: {Stream}')
    NativeId, DeclaredCount = Struct.unpack_from('<IH', DataValue, 0)
    if DeclaredCount == 0 and len(DataValue) == 6:
        return NativeMateList(native_id=NativeId, declared_count=0, owner_definition_id=OwnerDefinitionId, mates=(), stream=Stream)
    ClassOffset = DataValue.find(ClassMarker, 6)
    if ClassOffset < 0 or ClassOffset + 6 > len(DataValue):
        raise SldprtFormatError(f'mate stream has no class table: {Stream}')
    ClassSize = Struct.unpack_from('<H', DataValue, ClassOffset + 4)[0]
    ClassEnd = ClassOffset + 6 + ClassSize
    if ClassEnd + 5 > len(DataValue):
        raise SldprtFormatError(f'mate class record is truncated: {Stream}')
    ObjectPrefix = DataValue[ClassEnd:ClassEnd + 2]
    NamePrefix = ObjectPrefix + SerializedStringMarker
    Serialized = PrefixedStrings(DataValue, NamePrefix)
    ScalarTokens = {Token for Offset, Ignored, NameEnd in Serialized if DimensionScalarValue(DataValue, NameEnd, len(DataValue)) is not None for Token in (ClassRefToken(DataValue, Offset - 2),) if Token is not None}
    Candidates = [ItemValue for ItemValue in Serialized if DimensionScalarValue(DataValue, ItemValue[2], len(DataValue)) is None and ClassRefToken(DataValue, ItemValue[0] - 2) not in ScalarTokens]
    if len(Candidates) != DeclaredCount:
        raise SldprtFormatError(f'mate count mismatch in {Stream}: expected {DeclaredCount}, decoded {len(Candidates)}')
    Starts = [MateRecordStart(DataValue, Offset) for Offset, Ignored, Ignored in Candidates]
    Records: list[MateRecord] = []
    for Order, ((Ignored, NameValue, NameEnd), Start) in enumerate(zip(Candidates, Starts)):
        EndValue = Starts[Order + 1] if Order + 1 < len(Starts) else len(DataValue)
        Strings = RecordStrings(DataValue, Start, EndValue)
        ClassName = InlineClassName(DataValue, Start)
        Records.append(MateRecord(name=NameValue, name_end=NameEnd, start=Start, end=EndValue, class_name=ClassName, class_token=None if ClassName else ClassRefToken(DataValue, Start), strings=Strings, alignment_code=MateAlignmentA(DataValue, EndValue, NameEnd), dimensions=MateDimensions(DataValue, Start, EndValue)))
    TokenKinds = MateTokenKinds(Records)
    ClassesByKind: dict[str, set[str]] = {}
    for Record in Records:
        if not Record.class_name:
            continue
        KindValue = MateKind(Record.name, Record.class_name)
        if KindValue != 'native':
            ClassesByKind.setdefault(KindValue, set()).add(Record.class_name)
    Mates: list[NativeMate] = []
    for Order, Record in enumerate(Records):
        if Record.class_name:
            KindValue = MateKind(Record.name, Record.class_name)
            ClassName = Record.class_name
        else:
            KindValue = TokenKinds.get(Record.class_token, MateKind(Record.name))
            InferredClasses = ClassesByKind.get(KindValue, set())
            ClassName = next(iter(InferredClasses)) if len(InferredClasses) == 1 else ''
        Mates.append(NativeMate(name=Record.name, kind=KindValue, owner_definition_id=OwnerDefinitionId, order=Order, entities=MateEntities(Record.strings), record_offset=Record.start, record_length=Record.end - Record.start, class_name=ClassName, class_token=Record.class_token, serialized_strings=Record.strings, alignment_code=Record.alignment_code, dimensions=Record.dimensions))
    return NativeMateList(native_id=NativeId, declared_count=DeclaredCount, owner_definition_id=OwnerDefinitionId, mates=tuple(Mates), stream=Stream)

# this definition exists because focused behavior needs one stable owner
def MateLists(Archive: SldprtArchive, OwnerDefinitionId: int) -> tuple[NativeMateList, ...]:
    Result: list[NativeMateList] = []
    for Record in Archive.records:
        Named = IsMateStreamNam(Record.name)
        if not Named and (not IsMateStream(Record.data)):
            continue
        try:
            Decoded = DecodeMateList(Record.data, Record.name, OwnerDefinitionId)
        except SldprtFormatError:
            if Named:
                raise
            continue
        Result.append(Decoded)
    return tuple(Result)

# this definition exists because focused behavior needs one stable owner
def IsMateStreamNam(NameValue: str) -> bool:
    LeafValue = NameValue.replace('\\', '/').rsplit('/', 1)[-1].casefold()
    return LeafValue == MatesStreamName.casefold() or LeafValue.endswith(MatesStreamSuffix.casefold())

# this definition exists because focused behavior needs one stable owner
def IsMateStream(DataValue: bytes) -> bool:
    if len(DataValue) < 12 or DataValue[6:10] != ClassMarker:
        return False
    ClassSize = Struct.unpack_from('<H', DataValue, 10)[0]
    ClassEnd = 12 + ClassSize
    if not 1 <= ClassSize <= 128 or ClassEnd + 5 > len(DataValue):
        return False
    ObjectPrefix = Struct.unpack_from('<H', DataValue, ClassEnd)[0]
    return ObjectPrefix & 32768 != 0 and DataValue[ClassEnd + 2:ClassEnd + 5] == SerializedStringMarker

# this definition exists because focused behavior needs one stable owner
def ExpandItemPaths(RootDefinitionId: int, Definitions: Iterable[NativeAssemblyDefinition], Occurrences: Iterable[NativeAssemblyOccurrence]) -> tuple[NativeItemPath, ...]:
    DefinitionById = {ItemValue.object_id: ItemValue for ItemValue in Definitions}
    Children: dict[int, list[NativeAsmItem]] = {}
    for ItemValue in Occurrences:
        Children.setdefault(ItemValue.owner_definition_id, []).append(ItemValue)
    Result: list[NativeItemPath] = []

    # this definition exists because focused behavior needs one stable owner
    def Visit(DefinitionId: int, Prefix: str, Depth: int, Stack: frozenset[int]) -> None:
        if DefinitionId in Stack:
            raise SldprtFormatError('cyclic assembly definition hierarchy')
        Owner = DefinitionById[DefinitionId]
        for ItemValue in Children.get(DefinitionId, []):
            Segment = f'{ItemValue.name}-{ItemValue.reference_number}@{Owner.name}'
            PathValue = f'{Prefix}/{Segment}' if Prefix else Segment
            Result.append(NativeItemPath(occurrence_id=ItemValue.object_id, definition_id=ItemValue.definition_id, path=PathValue, depth=Depth))
            Target = DefinitionById[ItemValue.definition_id]
            if Target.document_type == 'ASSEMBLY':
                Visit(Target.object_id, PathValue, Depth + 1, Stack | {DefinitionId})
    Visit(RootDefinitionId, '', 0, frozenset())
    return tuple(Result)

# this definition exists because focused behavior needs one stable owner
def XmlRoot(DataValue: bytes) -> XmlTree.Element:
    Marker = DataValue.find(b'<?xml')
    if Marker >= 0:
        DataValue = DataValue[Marker:]
    try:
        return XmlTree.fromstring(DataValue)
    except XmlTree.ParseError as ErrorInfo:
        raise SldprtFormatError(f'invalid assembly component XML: {ErrorInfo}') from ErrorInfo

# this definition exists because focused behavior needs one stable owner
def LocalName(ElemValue: ET.Element) -> str:
    return ElemValue.tag.rsplit('}', 1)[-1]

# this definition exists because focused behavior needs one stable owner
def Elements(RootValue: ET.Element, NameValue: str) -> tuple[XmlTree.Element, ...]:
    return tuple((ItemValue for ItemValue in RootValue.iter() if LocalName(ItemValue) == NameValue))

# this definition exists because focused behavior needs one stable owner
def Files(RootValue: ET.Element) -> tuple[NativeAsmFile, ...]:
    return tuple((NativeAsmFile(object_id=Integer(ItemValue.attrib.get('id')), document_type=ItemValue.attrib.get('swDocType', ''), creation_time=Integer(ItemValue.attrib.get('swCreationTime')), source_path=ItemValue.attrib.get('swPath', '')) for ItemValue in Elements(RootValue, 'swFile')))

# this definition exists because focused behavior needs one stable owner
def Models(RootValue: ET.Element, Files: dict[int, NativeAssemblyFile]) -> tuple[tuple[NativeAsmA, ...], tuple[NativeAsmItem, ...]]:
    Definitions: list[NativeAsmA] = []
    Occurrences: list[NativeAsmItem] = []
    Order = 0
    for ItemValue in Elements(RootValue, 'swModel'):
        FileId = Integer(ItemValue.attrib.get('swFileRef'))
        Source = Files.get(FileId)
        if Source is None:
            raise SldprtFormatError(f'assembly model references missing file {FileId}')
        ChildElements = tuple((Child for Child in ItemValue if LocalName(Child) == 'swReference'))
        DefinitionId = Integer(ItemValue.attrib.get('id'))
        Definitions.append(NativeAsmA(object_id=DefinitionId, name=ItemValue.attrib.get('swName', ''), document_type=Source.document_type, file_id=FileId, source_path=Source.source_path, configuration_name=ItemValue.attrib.get('swConfigurationName', ''), configuration_id=Integer(ItemValue.attrib.get('swConfigurationId')), alternate_configuration_name=ItemValue.attrib.get('swConfigurationAlternateName', ''), last_modified_stamp=Integer(ItemValue.attrib.get('swLastModifiedStamp')), configuration_flags=Integer(ItemValue.attrib.get('swConfigurationFlags')), bounding_box_m=BoundingBox(ItemValue.attrib.get('swBoundingBox')), child_occurrence_ids=tuple((Integer(Child.attrib.get('id')) for Child in ChildElements)), attributes=tuple(sorted(ItemValue.attrib.items()))))
        for Child in ChildElements:
            Transform = FloatTuple(Child.attrib.get('swTransform'), 16)
            Occurrences.append(NativeAsmItem(object_id=Integer(Child.attrib.get('id')), feature_id=Integer(Child.attrib.get('swID')), owner_definition_id=DefinitionId, definition_id=Integer(Child.attrib.get('swModelRef')), name=Child.attrib.get('swName', ''), reference_number=Integer(Child.attrib.get('swReferenceNumber'), 1), component_reference=Child.attrib.get('swComponentReference', ''), configuration_name=Child.attrib.get('swConfigurationName', ''), configuration_id=Integer(Child.attrib.get('swConfigurationId')), transform=Transform, transform_stamp=Integer(Child.attrib.get('swTransformStamp')), suppressed=IsYesAction(Child.attrib.get('swSuppressed')), hidden=IsYesAction(Child.attrib.get('swHidden')), flexible=IsYesAction(Child.attrib.get('swFlexible')), virtual=IsYesAction(Child.attrib.get('swIsVirtualComponent')), exclude_from_bom=IsYesAction(Child.attrib.get('swExcludeFromBOM')), zone=IsYesAction(Child.attrib.get('swZone')), display_mode=Integer(Child.attrib.get('swDisplayMode')), display_quality=Integer(Child.attrib.get('swHlrDisplayQuality')), edges_in_shaded_mode=IsYesAction(Child.attrib.get('swEdgesInShadedMode')), order=Order, attributes=tuple(sorted(Child.attrib.items()))))
            Order += 1
    DefinitionIds = {ItemValue.object_id for ItemValue in Definitions}
    for ItemValueA in Occurrences:
        if ItemValueA.definition_id not in DefinitionIds:
            raise SldprtFormatError(f'component {ItemValueA.object_id} references missing model {ItemValueA.definition_id}')
    return (tuple(Definitions), tuple(Occurrences))

# this definition exists because focused behavior needs one stable owner
def Configurations(RootValue: ET.Element) -> tuple[NativeAsmConfig, ...]:
    return tuple((NativeAsmConfig(object_id=Integer(ItemValue.attrib.get('id')), configuration_id=Integer(ItemValue.attrib.get('swID')), name=ItemValue.attrib.get('swName', ''), reference=ItemValue.attrib.get('swReference', ''), model_id=Integer(ItemValue.attrib.get('swModelRef')), most_recent=IsYesAction(ItemValue.attrib.get('swMostRecentConfiguration')), needs_update=IsYesAction(ItemValue.attrib.get('swConfigurationNeedsUpdate')), attributes=tuple(sorted(ItemValue.attrib.items()))) for ItemValue in Elements(RootValue, 'swConfiguration')))

# this definition exists because focused behavior needs one stable owner
def DisplayStates(RootValue: ET.Element) -> tuple[NativeDisplay, ...]:
    return tuple((NativeDisplay(object_id=Integer(ItemValue.attrib.get('id')), name=ItemValue.attrib.get('swName', ''), configuration_id=Integer(ItemValue.attrib.get('swConfigurationId')) if 'swConfigurationId' in ItemValue.attrib else None, attributes=tuple(sorted(ItemValue.attrib.items()))) for ItemValue in Elements(RootValue, 'swDisplayState')))

# this definition exists because focused behavior needs one stable owner
def PrefixedStrings(DataValue: bytes, Prefix: bytes) -> tuple[tuple[int, str, int], ...]:
    Result: list[tuple[int, str, int]] = []
    Cursor = 0
    while True:
        Offset = DataValue.find(Prefix, Cursor)
        if Offset < 0:
            break
        Cursor = Offset + 1
        LengthOffset = Offset + len(Prefix)
        Decoded = UtfOneSixString(DataValue, LengthOffset)
        if Decoded is not None:
            Value, EndValue = Decoded
            Result.append((Offset, Value, EndValue))
    return tuple(Result)

# this definition exists because focused behavior needs one stable owner
def SerializedA(DataValue: bytes, Start: int=0, EndValue: int | None=None) -> tuple[tuple[int, str, int], ...]:
    Limit = len(DataValue) if EndValue is None else min(EndValue, len(DataValue))
    Result: list[tuple[int, str, int]] = []
    Cursor = max(Start, 0)
    while True:
        Offset = DataValue.find(SerializedStringMarker, Cursor, Limit)
        if Offset < 0:
            break
        Cursor = Offset + 1
        Decoded = UtfOneSixString(DataValue, Offset + len(SerializedStringMarker), Limit)
        if Decoded is not None:
            Value, StringEnd = Decoded
            Result.append((Offset, Value, StringEnd))
    return tuple(Result)

# this definition exists because focused behavior needs one stable owner
def UtfOneSixString(DataValue: bytes, LengthOffset: int, EndValue: int | None=None) -> tuple[str, int] | None:
    Limit = len(DataValue) if EndValue is None else EndValue
    if LengthOffset >= Limit:
        return None
    Length = DataValue[LengthOffset]
    if Length == 255:
        return None
    StringStart = LengthOffset + 1
    StringEnd = StringStart + Length * 2
    if StringEnd > Limit:
        return None
    try:
        Value = DataValue[StringStart:StringEnd].decode('utf-16le')
    except UnicodeDecodeError:
        return None
    if any((ord(Character) < 32 for Character in Value)):
        return None
    return (Value, StringEnd)

# this definition exists because focused behavior needs one stable owner
def MateRecordStart(DataValue: bytes, NamePrefixOffset: int) -> int:
    Inline = DataValue.rfind(ClassMarker, 0, NamePrefixOffset)
    if Inline >= 0 and Inline + 6 <= NamePrefixOffset:
        SizeValue = Struct.unpack_from('<H', DataValue, Inline + 4)[0]
        if Inline + 6 + SizeValue == NamePrefixOffset:
            return Inline
    return max(6, NamePrefixOffset - 2)

# this definition exists because focused behavior needs one stable owner
def InlineClassName(DataValue: bytes, Start: int) -> str:
    if DataValue[Start:Start + 4] != ClassMarker:
        return ''
    if Start + 6 > len(DataValue):
        return ''
    SizeValue = Struct.unpack_from('<H', DataValue, Start + 4)[0]
    try:
        return DataValue[Start + 6:Start + 6 + SizeValue].decode('ascii')
    except UnicodeDecodeError:
        return ''

# this definition exists because focused behavior needs one stable owner
def ClassRefToken(DataValue: bytes, Offset: int) -> int | None:
    if Offset < 0 or Offset + 2 > len(DataValue):
        return None
    Token = Struct.unpack_from('<H', DataValue, Offset)[0]
    return Token if Token & 32768 and Token != 65535 else None

# this definition exists because focused behavior needs one stable owner
def MateTokenKinds(Records: list[_MateRecord]) -> dict[int | None, str]:
    Candidates: dict[int, set[str]] = {}
    for Record in Records:
        if Record.class_name or Record.class_token is None:
            continue
        KindValue = MateKind(Record.name)
        if KindValue != 'native':
            Candidates.setdefault(Record.class_token, set()).add(KindValue)
    return {Token: next(iter(Kinds)) for Token, Kinds in Candidates.items() if len(Kinds) == 1}

# this definition exists because focused behavior needs one stable owner
def MateEntities(Strings: tuple[str, ...]) -> tuple[NativeMateC, ...]:
    SourcePaths = tuple((Value for Value in Strings if IsCadPath(Value)))
    EntityValues: list[tuple[str, list[str]]] = []
    Persistent: list[str] = []
    for Value in Strings:
        if '^' in Value and '@' in Value:
            continue
        if Value.casefold().startswith('mo'):
            Persistent.append(Value)
            continue
        if IsComponentPath(Value):
            EntityValues.append((Value, Persistent))
            Persistent = []
            continue
        if '@' in Value and EntityValues:
            EntityValues[-1][1].append(Value)
            continue
        if '@' in Value:
            Persistent.append(Value)
    Entities: list[NativeMateC] = []
    for ComponentPath, References in EntityValues:
        LeafValue = ComponentPath.rsplit('/', 1)[-1].split('@', 1)[0]
        SourceName = RegexLib.sub('-\\d+$', '', LeafValue).casefold()
        SourcePath = next((Value for Value in SourcePaths if PureWindowsPath(Value).stem.casefold() == SourceName), '')
        Entities.append(NativeMateC(component_path=ComponentPath, persistent_references=tuple(References), source_path=SourcePath, configuration_name=''))
    Synthetic = tuple((Value for Value in Strings if '^' in Value and '@' in Value))
    Entities.extend((NativeMateC(component_path='', persistent_references=(Value,), source_path='', configuration_name='') for Value in Synthetic))
    if Persistent:
        Entities.append(NativeMateC('', tuple(Persistent), '', ''))
    return tuple(Entities)

# this definition exists because focused behavior needs one stable owner
def MateKind(NameValue: str, ClassName: str='') -> str:
    NormalizedClass = ClassName.casefold().strip()
    if NormalizedClass:
        return KMateKindByClass.get(NormalizedClass, 'native')
    Lowered = NameValue.casefold().strip()
    Match = RegexLib.fullmatch('([a-z]+)(\\d+)(?:___endtag___)?', Lowered)
    return KMateKindByName.get(Match.group(1), 'native') if Match else 'native'

# this definition exists because focused behavior needs one stable owner
def MateAlignmentA(DataValue: bytes, EndValue: int, NameEnd: int) -> int | None:
    AlignmentOffset = NameEnd + KMateAlignmentOffset
    EntityCountOffset = NameEnd + KMateEntityCountOffset
    if EntityCountOffset + 4 > EndValue:
        return None
    EntityCount = Struct.unpack_from('<I', DataValue, EntityCountOffset)[0]
    if EntityCount != 2:
        return None
    try:
        AlignmentCode = Struct.unpack_from('<H', DataValue, AlignmentOffset)[0]
    except Struct.error:
        return None
    return AlignmentCode if AlignmentCode in KNativeMateAlignmentByCoA else None

# this definition exists because focused behavior needs one stable owner
def MateDimensions(DataValue: bytes, Start: int, EndValue: int) -> tuple[NativeMateB, ...]:
    Result: list[NativeMateB] = []
    for Ignored, NameValue, StringEnd in SerializedA(DataValue, Start, EndValue):
        ValueOffset = DimensionScalarValue(DataValue, StringEnd, EndValue)
        if ValueOffset is None:
            continue
        Value = Struct.unpack_from('<d', DataValue, ValueOffset)[0]
        if MathValue.isfinite(Value):
            Result.append(NativeMateB(NameValue, Value, ValueOffset))
    return tuple(Result)

# this definition exists because focused behavior needs one stable owner
def RecordStrings(DataValue: bytes, Start: int, EndValue: int) -> tuple[str, ...]:
    Values = [(Offset, Value) for Offset, Value, Ignored in SerializedA(DataValue, Start, EndValue) if Value]
    for Match in KWideText.finditer(DataValue, Start, EndValue):
        Values.append((Match.start(), Match.group().decode('utf-16le')))

    # this callback exists because local behavior needs one focused transformation
    Values.sort(key=lambda ItemValue: ItemValue[0])
    Result: list[str] = []
    for Ignored, Value in Values:
        if not Result or Result[-1] != Value:
            Result.append(Value)
    return tuple(Result)

# this definition exists because focused behavior needs one stable owner
def BoundingBox(Value: str | None) -> tuple[float, float, float, float, float, float] | None:
    if not Value:
        return None
    return FloatTuple(Value, 6)

# this definition exists because focused behavior needs one stable owner
def FloatTuple(Value: str | None, Count: int) -> tuple[float, ...]:
    if Value is None:
        raise SldprtFormatError('required floating-point tuple is missing')
    Result = tuple((float(ItemValue) for ItemValue in Value.split()))
    if len(Result) != Count or not all((MathValue.isfinite(ItemValue) for ItemValue in Result)):
        raise SldprtFormatError(f'expected {Count} finite floating-point values, found {len(Result)}')
    return Result

# this definition exists because focused behavior needs one stable owner
def Integer(Value: str | None, Default: int=0) -> int:
    try:
        return int(Value) if Value is not None else Default
    except ValueError as ErrorInfo:
        raise SldprtFormatError(f'invalid integer value {Value!r}') from ErrorInfo

# this definition exists because focused behavior needs one stable owner
def IsYesAction(Value: str | None) -> bool:
    return Value == 'YES'

# this binding exists because shared behavior needs one stable value
globals()['Any'] = AnyValue

# this binding exists because shared behavior needs one stable value
globals()['AssemblyData'] = AsmData

# this binding exists because shared behavior needs one stable value
globals()['CLASS_MARKER'] = ClassMarker

# this binding exists because shared behavior needs one stable value
globals()['COMPONENT_TREE_STREAM'] = ComponentTreeStream

# this binding exists because shared behavior needs one stable value
globals()['Configuration'] = Config

# this binding exists because shared behavior needs one stable value
globals()['DIMENSION_SCALAR_HEADERS'] = DimensionScalarHeaders

# this binding exists because shared behavior needs one stable value
globals()['DISPLAY_LISTS_STREAM'] = DisplayListsStream

# this binding exists because shared behavior needs one stable value
globals()['ET'] = XmlTree

# this binding exists because shared behavior needs one stable value
globals()['MATES_STREAM_NAME'] = MatesStreamName

# this binding exists because shared behavior needs one stable value
globals()['MATES_STREAM_SUFFIX'] = MatesStreamSuffix

# this binding exists because shared behavior needs one stable value
globals()['MATE_ADVISORY_LOSS_REASONS'] = KMateAdvisoryLossReasons

# this binding exists because shared behavior needs one stable value
globals()['MATE_BLOCKING_LOSS_REASONS'] = KMateBlockingLossReasons

# this binding exists because shared behavior needs one stable value
globals()['MATE_LOSS_ALIGNMENT'] = KMateLossAlignment

# this binding exists because shared behavior needs one stable value
globals()['MATE_LOSS_ENTITY_COMPONENT_PATH'] = KMateLossEntityComponent

# this binding exists because shared behavior needs one stable value
globals()['MATE_LOSS_ENTITY_FRAME'] = KMateLossEntityFrame

# this binding exists because shared behavior needs one stable value
globals()['MATE_LOSS_ENTITY_MISSING'] = KMateLossEntityMissing

# this binding exists because shared behavior needs one stable value
globals()['MATE_LOSS_ENTITY_RADIUS'] = KMateLossEntityRadius

# this binding exists because shared behavior needs one stable value
globals()['MATE_LOSS_ENTITY_REFERENCE'] = KMateLossEntityRef

# this binding exists because shared behavior needs one stable value
globals()['MATE_LOSS_ENTITY_SELECTION'] = KMateLossEntitySelection

# this binding exists because shared behavior needs one stable value
globals()['MATE_LOSS_EXPRESSION'] = KMateLossExpression

# this binding exists because shared behavior needs one stable value
globals()['MATE_LOSS_GROUP_MEMBERSHIP'] = KMateLossGroupMembership

# this binding exists because shared behavior needs one stable value
globals()['MATE_LOSS_GROUP_NESTING'] = KMateLossGroupNesting

# this binding exists because shared behavior needs one stable value
globals()['MATE_LOSS_KIND'] = KMateLossKind

# this binding exists because shared behavior needs one stable value
globals()['MATE_LOSS_LANE_CAPACITY'] = KMateLossLaneCapacity

# this binding exists because shared behavior needs one stable value
globals()['MATE_LOSS_NAME'] = KMateLossName

# this binding exists because shared behavior needs one stable value
globals()['MATE_LOSS_NOT_DRIVING'] = KMateLossNotDriving

# this binding exists because shared behavior needs one stable value
globals()['MATE_LOSS_ORPHAN_ENTITY'] = KMateLossOrphanEntity

# this binding exists because shared behavior needs one stable value
globals()['MATE_LOSS_REASONS'] = KMateLossReasons

# this binding exists because shared behavior needs one stable value
globals()['MATE_LOSS_RECORD_VERIFICATION'] = KMateLossRecord

# this binding exists because shared behavior needs one stable value
globals()['MATE_LOSS_SUPPRESSED'] = KMateLossSuppressed

# this binding exists because shared behavior needs one stable value
globals()['MATE_LOSS_VALUE'] = KMateLossValue

# this binding exists because shared behavior needs one stable value
globals()['MATE_LOSS_VALUE_MISSING'] = KMateLossValueMissing

# this binding exists because shared behavior needs one stable value
globals()['MATE_REJECTION_REASONS'] = KMateRejectionReasons

# this binding exists because shared behavior needs one stable value
globals()['MATE_VALUE_SEMANTICS'] = KMateValueSemantics

# this binding exists because shared behavior needs one stable value
globals()['MateConstraint'] = MateRule

# this binding exists because shared behavior needs one stable value
globals()['Matrix4'] = MatrixFour

# this binding exists because shared behavior needs one stable value
globals()['NATIVE_MATE_ALIGNMENTS'] = KNativeMateAlignments

# this binding exists because shared behavior needs one stable value
globals()['NATIVE_MATE_ALIGNMENT_BY_CODE'] = KNativeMateAlignmentByCoA

# this binding exists because shared behavior needs one stable value
globals()['NATIVE_MATE_ENTITY_GEOMETRY_TYPES'] = KNativeMateEntityGeomTypA

# this binding exists because shared behavior needs one stable value
globals()['NATIVE_MATE_ENTITY_KIND_BY_MARKER'] = KNativeMateEntityKindBy

# this binding exists because shared behavior needs one stable value
globals()['NATIVE_MATE_ENTITY_MARKERS'] = KNativeMateEntityMarkers

# this binding exists because shared behavior needs one stable value
globals()['NATIVE_MATE_ENTITY_REFERENCE_TYPES'] = KNativeMateEntityRefTypes

# this binding exists because shared behavior needs one stable value
globals()['NATIVE_MATE_ENTITY_TYPE_EXTENSIONS'] = KNativeMateEntityType

# this binding exists because shared behavior needs one stable value
globals()['NATIVE_MATE_ENTITY_TYPE_RECORDS'] = KNativeMateEntityTypeA

# this binding exists because shared behavior needs one stable value
globals()['NATIVE_MATE_NEUTRAL_KIND_ALIASES'] = KNativeMateNeutralKind

# this binding exists because shared behavior needs one stable value
globals()['NATIVE_MATE_TYPES'] = KNativeMateTypes

# this binding exists because shared behavior needs one stable value
globals()['NATIVE_MATE_TYPE_EXTENSIONS'] = KNativeMateTypeExtensions

# this binding exists because shared behavior needs one stable value
globals()['NATIVE_MATE_TYPE_RECORDS'] = KNativeMateTypeRecords

# this binding exists because shared behavior needs one stable value
globals()['NativeAssembly'] = NativeAsm

# this binding exists because shared behavior needs one stable value
globals()['NativeAssemblyConfiguration'] = NativeAsmConfig

# this binding exists because shared behavior needs one stable value
globals()['NativeAssemblyDefinition'] = NativeAsmA

# this binding exists because shared behavior needs one stable value
globals()['NativeAssemblyEncoding'] = NativeAsmB

# this binding exists because shared behavior needs one stable value
globals()['NativeAssemblyFile'] = NativeAsmFile

# this binding exists because shared behavior needs one stable value
globals()['NativeAssemblyOccurrence'] = NativeAsmItem

# this binding exists because shared behavior needs one stable value
globals()['NativeDisplayState'] = NativeDisplay

# this binding exists because shared behavior needs one stable value
globals()['NativeMateAlignment'] = NativeMateA

# this binding exists because shared behavior needs one stable value
globals()['NativeMateAlignmentCode'] = NativeMateCode

# this binding exists because shared behavior needs one stable value
globals()['NativeMateDimension'] = NativeMateB

# this binding exists because shared behavior needs one stable value
globals()['NativeMateEntity'] = NativeMateC

# this binding exists because shared behavior needs one stable value
globals()['NativeMateEntityType'] = NativeMateTypeA

# this binding exists because shared behavior needs one stable value
globals()['NativeMateStreamReport'] = NativeMateD

# this binding exists because shared behavior needs one stable value
globals()['NativeOccurrencePath'] = NativeItemPath

# this binding exists because shared behavior needs one stable value
globals()['SERIALIZED_STRING_MARKER'] = SerializedStringMarker

# this binding exists because shared behavior needs one stable value
globals()['_MATE_ALIGNMENT_OFFSET'] = KMateAlignmentOffset

# this binding exists because shared behavior needs one stable value
globals()['_MATE_ENTITY_COUNT_OFFSET'] = KMateEntityCountOffset

# this binding exists because shared behavior needs one stable value
globals()['_MATE_GROUP_END_SUFFIX'] = KMateGroupEndSuffix

# this binding exists because shared behavior needs one stable value
globals()['_MATE_KIND_BY_CLASS'] = KMateKindByClass

# this binding exists because shared behavior needs one stable value
globals()['_MATE_KIND_BY_NAME'] = KMateKindByName

# this binding exists because shared behavior needs one stable value
globals()['_MATE_LIST_NATIVE_ID_FLAG'] = KMateListNativeIdFlag

# this binding exists because shared behavior needs one stable value
globals()['_MATE_OBJECT_PREFIX'] = KMateObjectPrefix

# this binding exists because shared behavior needs one stable value
globals()['_MATE_RECORD_BODY_SIZE'] = KMateRecordBodySize

# this binding exists because shared behavior needs one stable value
globals()['_MateRecord'] = MateRecord

# this binding exists because shared behavior needs one stable value
globals()['_WIDE_TEXT'] = KWideText

# this binding exists because shared behavior needs one stable value
globals()['_allocate_object_ids'] = AllocateObject

# this binding exists because shared behavior needs one stable value
globals()['_bounding_box'] = BoundingBox

# this binding exists because shared behavior needs one stable value
globals()['_class_reference_token'] = ClassRefToken

# this binding exists because shared behavior needs one stable value
globals()['_classifier_map'] = ClassifierMap

# this binding exists because shared behavior needs one stable value
globals()['_configuration_integer'] = ConfigInteger

# this binding exists because shared behavior needs one stable value
globals()['_configurations'] = Configurations

# this binding exists because shared behavior needs one stable value
globals()['_decoded_group_members'] = DecodedGroup

# this binding exists because shared behavior needs one stable value
globals()['_definition_document_type'] = DefinitionDoc

# this binding exists because shared behavior needs one stable value
globals()['_definition_file_key'] = DefinitionFile

# this binding exists because shared behavior needs one stable value
globals()['_definition_source_path'] = DefinitionPath

# this binding exists because shared behavior needs one stable value
globals()['_definition_supported'] = IsDefinition

# this binding exists because shared behavior needs one stable value
globals()['_display_states'] = DisplayStates

# this binding exists because shared behavior needs one stable value
globals()['_elements'] = Elements

# this binding exists because shared behavior needs one stable value
globals()['_encode_group_records'] = EncodeGroup

# this binding exists because shared behavior needs one stable value
globals()['_encode_mate_record'] = EncodeMate

# this binding exists because shared behavior needs one stable value
globals()['_encode_mate_streams'] = EncodeMateA

# this binding exists because shared behavior needs one stable value
globals()['_encode_record_body'] = EncodeRecord

# this binding exists because shared behavior needs one stable value
globals()['_encoded_mate_matches'] = IsEncodedMate

# this binding exists because shared behavior needs one stable value
globals()['_expected_group_members'] = ExpectedGroup

# this binding exists because shared behavior needs one stable value
globals()['_file_stem'] = FileStem

# this binding exists because shared behavior needs one stable value
globals()['_files'] = Files

# this binding exists because shared behavior needs one stable value
globals()['_float_tuple'] = FloatTuple

# this binding exists because shared behavior needs one stable value
globals()['_inline_class_name'] = InlineClassName

# this binding exists because shared behavior needs one stable value
globals()['_instance_base_name'] = InstanceBase

# this binding exists because shared behavior needs one stable value
globals()['_integer'] = Integer

# this binding exists because shared behavior needs one stable value
globals()['_integer_attribute'] = IntegerAttr

# this binding exists because shared behavior needs one stable value
globals()['_is_identity_matrix'] = IsIdentity

# this binding exists because shared behavior needs one stable value
globals()['_local_name'] = LocalName

# this binding exists because shared behavior needs one stable value
globals()['_mate_alignment'] = MateAlignmentA

# this binding exists because shared behavior needs one stable value
globals()['_mate_alignment_code'] = MateAlignmentB

# this binding exists because shared behavior needs one stable value
globals()['_mate_dimension_values'] = MateDimension

# this binding exists because shared behavior needs one stable value
globals()['_mate_dimensions'] = MateDimensions

# this binding exists because shared behavior needs one stable value
globals()['_mate_entities'] = MateEntities

# this binding exists because shared behavior needs one stable value
globals()['_mate_entity_strings'] = MateEntityA

# this binding exists because shared behavior needs one stable value
globals()['_mate_kind'] = MateKind

# this binding exists because shared behavior needs one stable value
globals()['_mate_lists'] = MateLists

# this binding exists because shared behavior needs one stable value
globals()['_mate_owner_plan'] = MateOwnerPlaMut

# this binding exists because shared behavior needs one stable value
globals()['_mate_record_start'] = MateRecordStart

# this binding exists because shared behavior needs one stable value
globals()['_mate_stream_lanes'] = MateStreamLanes

# this binding exists because shared behavior needs one stable value
globals()['_mate_stream_name'] = IsMateStreamNam

# this binding exists because shared behavior needs one stable value
globals()['_mate_stream_structure'] = IsMateStream

# this binding exists because shared behavior needs one stable value
globals()['_mate_token_kinds'] = MateTokenKinds

# this binding exists because shared behavior needs one stable value
globals()['_merged_reasons'] = MergedReasons

# this binding exists because shared behavior needs one stable value
globals()['_models'] = Models

# this binding exists because shared behavior needs one stable value
globals()['_native_bounding_box'] = NativeBounding

# this binding exists because shared behavior needs one stable value
globals()['_native_component_path'] = NativeComponent

# this binding exists because shared behavior needs one stable value
globals()['_native_feature_id'] = NativeFeatureId

# this binding exists because shared behavior needs one stable value
globals()['_native_group_class'] = NativeGroup

# this binding exists because shared behavior needs one stable value
globals()['_native_mate_class'] = NativeMateClass

# this binding exists because shared behavior needs one stable value
globals()['_native_matrix'] = NativeMatrix

# this binding exists because shared behavior needs one stable value
globals()['_positive_integer'] = PositiveInteger

# this binding exists because shared behavior needs one stable value
globals()['_preferred_native_id'] = PreferredNative

# this binding exists because shared behavior needs one stable value
globals()['_prefixed_strings'] = PrefixedStrings

# this binding exists because shared behavior needs one stable value
globals()['_record_strings'] = RecordStrings

# this binding exists because shared behavior needs one stable value
globals()['_reference_number'] = RefNumber

# this binding exists because shared behavior needs one stable value
globals()['_resolved_mate_dimensions'] = ResolvedMate

# this binding exists because shared behavior needs one stable value
globals()['_serialized_string'] = Serialized

# this binding exists because shared behavior needs one stable value
globals()['_serialized_strings'] = SerializedA

# this binding exists because shared behavior needs one stable value
globals()['_utf16_string'] = UtfOneSixString

# this binding exists because shared behavior needs one stable value
globals()['_verify_mate_stream'] = IsVerifyMateMut

# this binding exists because shared behavior needs one stable value
globals()['_with_reason'] = WithReason

# this binding exists because shared behavior needs one stable value
globals()['_xml_root'] = XmlRoot

# this binding exists because shared behavior needs one stable value
globals()['_yes'] = IsYesAction

# this binding exists because shared behavior needs one stable value
globals()['_yes_text'] = YesText

# this binding exists because shared behavior needs one stable value
globals()['annotations'] = Annotations

# this binding exists because shared behavior needs one stable value
globals()['dataclass'] = Dataclass

# this binding exists because shared behavior needs one stable value
globals()['decode_display_lists'] = DecodeDisplayLists

# this binding exists because shared behavior needs one stable value
globals()['decode_mate_list'] = DecodeMateList

# this binding exists because shared behavior needs one stable value
globals()['decode_native_assembly'] = DecodeNativeAsm

# this binding exists because shared behavior needs one stable value
globals()['decode_tessellation_faces'] = DecodeTessellationFaces

# this binding exists because shared behavior needs one stable value
globals()['dimension_scalar_value_offset'] = DimensionScalarValue

# this binding exists because shared behavior needs one stable value
globals()['encode_native_assembly'] = EncodeNativeAsm

# this binding exists because shared behavior needs one stable value
globals()['expand_occurrence_paths'] = ExpandItemPaths

# this binding exists because shared behavior needs one stable value
globals()['field'] = Field

# this binding exists because shared behavior needs one stable value
globals()['is_cad_path'] = IsCadPath

# this binding exists because shared behavior needs one stable value
globals()['is_component_path'] = IsComponentPath

# this binding exists because shared behavior needs one stable value
globals()['math'] = MathValue

# this binding exists because shared behavior needs one stable value
globals()['re'] = RegexLib

# this binding exists because shared behavior needs one stable value
globals()['struct'] = Struct

# this binding exists because shared behavior needs one stable value
globals()['Definition'] = IsDefinition

# this binding exists because shared behavior needs one stable value
globals()['EncodedMate'] = IsEncodedMate

# this binding exists because shared behavior needs one stable value
globals()['MateOwnerPlan'] = MateOwnerPlaMut

# this binding exists because shared behavior needs one stable value
globals()['MateStream'] = IsMateStream

# this binding exists because shared behavior needs one stable value
globals()['MateStreamName'] = IsMateStreamNam

# this binding exists because shared behavior needs one stable value
globals()['VerifyMate'] = IsVerifyMateMut

# this binding exists because shared behavior needs one stable value
globals()['YesAction'] = IsYesAction
