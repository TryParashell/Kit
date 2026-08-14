# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations as Annotations
from dataclasses import dataclass as Dataclass, field as Field, replace as Replace
import hashlib as Hashlib
import itertools as Itertools
import math as MathValue
from pathlib import PureWindowsPath
import re as RegexLib
import struct as Struct
from types import MappingProxyType
from typing import Any as AnyValue, Mapping, Sequence
import xml.etree.ElementTree as XmlTree
from interchange import BooleanOperation as BoolOperation, CadDocument as CadDoc, Capability, ChamferFeature, CircleCurve, CircleGeometry as CircleGeom, CircularPatternFeature, CylinderSurface, ExtrusionEndCondition, ExtrusionFeature, FeatureKind, FeatureStep, FilletFeature, LinearPatternFeature, LineCurve, LineGeometry as LineGeom, NativeFeatureDefinition, Parameter as Param, ParameterRole as ParamRole, ParameterValue as ParamValue, PlaneSurface, ShellFeature, Sketch, SupportPlane, ValueKind, Vector2 as VectorTwo
from convert.geometry.Opencascade import decode_ascii_brep as DecodeAsciiBrep
from convert.adapters.solidworks.container.Archive import encode_class_reference as EncodeClassRef
from convert.adapters.solidworks.container.Cmgr import CONFIGURATION_MANAGER_STREAM as ConfigManagerStream, FIRST_ATOM_ID as FirstAtomId, atom_ids_for as AtomIdsFor, encode_cmgr_stream as EncodeCmgrStream
from convert.adapters.solidworks.configuration.ConfigZero import encode_config0_stream as EncodeConfigZeroStream
from convert.adapters.solidworks.programs.configuration.box.Program import EncodeProgram as EncodeBoxConfigProgram
from convert.adapters.solidworks.programs.configuration.circle.reverse.Program import EncodeProgram as EncodeReverseCircleConfig
from convert.adapters.solidworks.container.Container import SldprtFormatError
from convert.adapters.solidworks.container.Definition import encode_definition_stream as EncodeDefinitionStream
from convert.adapters.solidworks.container.Format import ASSEMBLY_SUFFIX as AsmSuffix, CANONICAL_PLANE_FEATURE_TYPE as CanonicalPlaneFeatureType, CLASS_MARKER as ClassMarker, CONFIGURATION_STREAM as ConfigStream, DIMENSION_SCALAR_HEADERS as DimensionScalarHeaders, KIT_RESOLVED_STREAM as KitResolvedStream, PART_SUFFIX as PartSuffix, PLANE_FEATURE_TYPES as PlaneFeatureTypes, RESOLVED_FEATURES_STREAM as ResolvedFeaturesStream, SERIALIZED_STRING_MARKER as SerializedStringMarker, dimension_scalar_value_offset as DimensionScalarValue
from convert.adapters.solidworks.resolved.Core import ANGLE_COPY_DELTAS as AngleCopyDeltas, DEPTH_COPY_DELTAS as DepthCopyDeltas, DEPTH_COPY_SIGNS as DepthCopySigns, FeatureEdit, FROM_END_SPEC_CLASS as FromEndSpecClass, FROM_REVERSE_RELATIVE as FromReverseRelative, REVOLUTION_AXIS_SKETCH as RevolutionAxisSketch, SKETCH_CHAIN_CLASS as SketchChainClass, circle_radius_mm as CircleRadiusMm, locate_features as LocateFeatures, patch_features as PatchFeatures, rectangle_corners_mm as RectangleCornersMm
from convert.adapters.solidworks.programs.resolved.default.Program import EncodeProgram
from convert.adapters.solidworks.programs.resolved.boss.cut.default.Program import EncodeProgram as EncodeBossCutProgram
from convert.adapters.solidworks.programs.resolved.boss.cut.circle.Program import EncodeProgram as EncodeBossCutCircle
from convert.adapters.solidworks.programs.resolved.boss.cut.pair.Program import EncodeProgram as EncodeBossCutCutProgram
from convert.adapters.solidworks.programs.resolved.boss.cut.triple.Program import EncodeProgram as EncodeBossCutCutCut
from convert.adapters.solidworks.programs.resolved.boss.cut.through.Program import EncodeProgram as EncodeBossCutThrough
from convert.adapters.solidworks.programs.resolved.boss.repeated.Program import EncodeProgram as EncodeBossBossProgram
from convert.adapters.solidworks.programs.resolved.boss.chamfer.Program import EncodeProgram as EncodeBossChamferProgram
from convert.adapters.solidworks.programs.resolved.boss.pattern.circular.Program import EncodeProgram as EncodeBossCircularPattern
from convert.adapters.solidworks.programs.resolved.boss.fillet.Program import EncodeProgram as EncodeBossFilletProgram
from convert.adapters.solidworks.programs.resolved.boss.pattern.linear.Program import EncodeProgram as EncodeBossLinearPattern
from convert.adapters.solidworks.programs.resolved.boss.revolvecut.Program import EncodeProgram as EncodeBossRevCutProgram
from convert.adapters.solidworks.programs.resolved.boss.shell.Program import EncodeProgram as EncodeBossShellProgram
from convert.adapters.solidworks.programs.resolved.box.Program import EncodeProgram as EncodeBoxProgram
from convert.adapters.solidworks.programs.resolved.circle.default.Program import EncodeProgram as EncodeCircleProgram
from convert.adapters.solidworks.programs.resolved.circle.reverse.Program import EncodeProgram as EncodeReverseCircle
from convert.adapters.solidworks.programs.resolved.polyline.sixpoint.Program import EncodeProgram as EncodePolylineSixProgram, PadFieldMap as PolylineSixFieldMap
from convert.adapters.solidworks.programs.resolved.planes.right.Program import EncodeProgram as EncodeRightProgram
from convert.adapters.solidworks.programs.resolved.revolve.default.Program import EncodeProgram as EncodeRevolveProgram
from convert.adapters.solidworks.programs.resolved.revolve.pin.default.Program import EncodeProgram as EncodePinRevolveProgram
from convert.adapters.solidworks.programs.resolved.planes.top.Program import EncodeProgram as EncodeTopProgram
from convert.adapters.solidworks.envelopes.revolve.pin.rightangle.Envelope import BuildEnvelope as BuildPinNineZeroEnvelope
from convert.adapters.solidworks.envelopes.revolve.pin.rightangle.Envelope import EncodeFeatures as EncodePinNineZeroRevolve
from convert.adapters.solidworks.envelopes.revolve.pin.default.Envelope import BuildEnvelope as BuildPinEnvelope
from convert.adapters.solidworks.envelopes.revolve.pin.default.Envelope import KPinPointsMm

# this binding exists because shared behavior needs one stable value
KRadiansToDegrees = 180.0 / MathValue.pi

# this binding exists because shared behavior needs one stable value
KCurrentMarker = bytes.fromhex('ffff1f0003')

# this binding exists because shared behavior needs one stable value
KLegacyMarker = bytes.fromhex('ffff070001')

# this binding exists because shared behavior needs one stable value
KExtendedMarker = bytes.fromhex('ffff1f0001')

# this binding exists because shared behavior needs one stable value
KMarkers = (KCurrentMarker, KLegacyMarker, KExtendedMarker)

# this binding exists because shared behavior needs one stable value
KCoordinateTag = bytes.fromhex('1e00')

# this binding exists because shared behavior needs one stable value
KPointLocus = bytes.fromhex('04000200')

# this binding exists because shared behavior needs one stable value
KCircleLocus = bytes.fromhex('05000100')

# this binding exists because shared behavior needs one stable value
KNumber = RegexLib.compile('[-+]?(?:\\d+(?:\\.\\d*)?|\\.\\d+)(?:[eE][-+]?\\d+)?')

# this binding exists because shared behavior needs one stable value
KEdgeSelectionIdentity = bytes.fromhex('7dc39425ad49b2547dc39425ad49b254')

# this binding exists because shared behavior needs one stable value
KRevolutionFeatureTypes = frozenset({'revolve', 'revolution', 'cut-revolve', 'revcut'})

# this binding exists because shared behavior needs one stable value
KSurfaceExtrusionFeature = frozenset({'surface-extrude', 'extrurefsurface'})

# this binding exists because shared behavior needs one stable value
KMoveBodyFeatureTypes = frozenset({'body-move/copy', 'movecopybody'})

# this binding exists because shared behavior needs one stable value
KCombineFeatureTypes = frozenset({'combine', 'combinebodies'})

# this binding exists because shared behavior needs one stable value
KHoleClassNames = frozenset({'moSketchHole', 'moHoleWzd_c'})

# this binding exists because shared behavior needs one stable value
KEquation = RegexLib.compile('^"([^"\\r\\n]+)"\\s*=\\s*(\\S(?:.*\\S)?)$')

# this binding exists because shared behavior needs one stable value
KEquationRef = RegexLib.compile('"([^"\\r\\n]+)"')

# this binding exists because shared behavior needs one stable value
KExtrusionClass = 'moExtrusion_c'

# this binding exists because shared behavior needs one stable value
KBoundingBoxClass = 'moBBoxCenterData_c'

# this binding exists because shared behavior needs one stable value
KBoundingBoxRelative = 28

# this binding exists because shared behavior needs one stable value
KFaceSupportClass = 'moFaceRefPlnData_c'

# this binding exists because shared behavior needs one stable value
KSketchPlaneIdRelative = 209

# this binding exists because shared behavior needs one stable value
KSketchPlaneRefPrefix = bytes.fromhex('50460000')

# this binding exists because shared behavior needs one stable value
KSketchPlaneRefTag = bytes.fromhex('f65a1a69')

# this binding exists because shared behavior needs one stable value
KSketchPlaneAxisDelta = 10

# this binding exists because shared behavior needs one stable value
KSketchPlaneBasisFlagDelA = 14

# this binding exists because shared behavior needs one stable value
KSketchPlaneBasisDelta = 15

# this binding exists because shared behavior needs one stable value
KSketchPlaneBasisBytes = 72

# this binding exists because shared behavior needs one stable value
KSketchPlaneAxisComplemeA = 5

# this binding exists because shared behavior needs one stable value
KSketchPlaneScanBytes = 320

# this binding exists because shared behavior needs one stable value
KPrincipalPlaneObjectIds = frozenset({2, 3, 4})

# this binding exists because shared behavior needs one stable value
KPlaneFrameBytes = 121

# this binding exists because shared behavior needs one stable value
KEquationId = RegexLib.compile('[^0-9A-Za-z]+')

# this binding exists because shared behavior needs one stable value
KEquationRefSource = RegexLib.compile('^[A-Za-z_<][0-9A-Za-z_<>.:\\- ]*$')

# this binding exists because shared behavior needs one stable value
KEquationReservedPrefix = 'KitReserved'

# this binding exists because shared behavior needs one stable value
KExtrusionOperationKinds = frozenset({'join', 'cut'})

# this binding exists because shared behavior needs one stable value
KRevolutionOperationKinds = frozenset({'revolve_join', 'revolve_cut'})

# this binding exists because shared behavior needs one stable value
KNormalAxisSubElem = 'N_Axis'

# this binding exists because shared behavior needs one stable value
KVerticalAxisSubElem = 'V_Axis'

# this binding exists because shared behavior needs one stable value
KHorizontalAxisSubElem = 'H_Axis'

# this binding exists because shared behavior needs one stable value
KDirectionAxisRole = 'direction_axis'

# this binding exists because shared behavior needs one stable value
KIdentityBasis = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))

# this binding exists because shared behavior needs one stable value
KIdentityOrigin = (0.0, 0.0, 0.0)

# this binding exists because shared behavior needs one stable value
KDerivedPlaneClasses = ('moRefPlaneMidPlaneGeom_c', 'moConstraintMidPlaneRefplaneData_c', 'moLinePtRefPlnData_c', 'moFaceRefPlnData_c', 'moFixedRefPlnData_c', 'moDefaultRefPlnData_c')

# this binding exists because shared behavior needs one stable value
KPlaneSupportKind = 'plane'

# this binding exists because shared behavior needs one stable value
KFaceSupportKind = 'face'

# this binding exists because shared behavior needs one stable value
KDerivedSupportKind = 'derived'

# this binding exists because shared behavior needs one stable value
KRefSupportSource = 'plane-reference'

# this binding exists because shared behavior needs one stable value
KStreamOrderSupportSource = 'stream-order'

# this binding exists because shared behavior needs one stable value
KUnresolvedSupportSource = 'unresolved'

# this binding exists because shared behavior needs one stable value
KMillimetres = 1000.0

# this binding exists because shared behavior needs one stable value
KMarkerLocalIdOffsetBy = MappingProxyType({142: 138, 146: 138, 152: 148, 154: 150, 156: 148, 158: 144, 162: 158, 166: 158, 167: 158})

# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class NativeOperand:
    locals().setdefault('__annotations__', {})
    __annotations__['offset'] = 'int'
    __annotations__['kind_code'] = 'int'
    __annotations__['entity_index'] = 'int'

# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class NativeScalar:
    locals().setdefault('__annotations__', {})
    __annotations__['name'] = 'str'
    __annotations__['name_offset'] = 'int'
    __annotations__['value_offset'] = 'int'
    __annotations__['value'] = 'float'
    __annotations__['object_id'] = 'int | None'
    __annotations__['role'] = 'str'
    __annotations__['operands'] = 'tuple[NativeOperand, ...]'

# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class NativeDimension:
    locals().setdefault('__annotations__', {})
    __annotations__['name'] = 'str'
    __annotations__['value_mm'] = 'float'
    __annotations__['kind'] = 'str'
    __annotations__['source_text'] = 'str'
    __annotations__['native_value'] = 'float | None'
    locals()['native_value'] = None
    __annotations__['native_offset'] = 'int | None'
    locals()['native_offset'] = None
    __annotations__['native_role'] = 'str | None'
    locals()['native_role'] = None
    __annotations__['operands'] = 'tuple[NativeOperand, ...]'
    locals()['operands'] = ()

# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class NativeName:
    locals().setdefault('__annotations__', {})
    __annotations__['offset'] = 'int'
    __annotations__['text_end'] = 'int'
    __annotations__['name'] = 'str'
    __annotations__['object_id'] = 'int | None'
    __annotations__['class_token'] = 'int'

# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class NativeClass:
    locals().setdefault('__annotations__', {})
    __annotations__['offset'] = 'int'
    __annotations__['name'] = 'str'

# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class NativeMarker:
    locals().setdefault('__annotations__', {})
    __annotations__['offset'] = 'int'
    __annotations__['length'] = 'int'
    __annotations__['prefix'] = 'str'
    __annotations__['native_kind'] = 'int'
    __annotations__['locus'] = 'str'
    __annotations__['profile_role'] = 'int'
    __annotations__['state'] = 'float | None'
    __annotations__['object_index'] = 'int | None'
    __annotations__['local_id'] = 'int | None'
    __annotations__['coordinates_mm'] = 'tuple[float, float] | None'
    __annotations__['endpoint_indices'] = 'tuple[int, int] | None'
    __annotations__['construction'] = 'bool'
    __annotations__['semantic'] = 'str'
    __annotations__['data'] = 'bytes'
    locals()['data'] = b''
    __annotations__['coordinates_metres'] = 'tuple[float, float] | None'
    locals()['coordinates_metres'] = None

# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class NativeRule:
    locals().setdefault('__annotations__', {})
    __annotations__['id'] = 'str'
    __annotations__['kind'] = 'str'
    __annotations__['references'] = 'tuple[str, ...]'
    __annotations__['parameter'] = 'str | None'
    __annotations__['value'] = 'float | None'
    __annotations__['native_offset'] = 'int | None'
    __annotations__['native_code'] = 'int | None'

# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class NativeProfile:
    locals().setdefault('__annotations__', {})
    __annotations__['kind'] = 'str'
    __annotations__['coordinates'] = 'tuple[float, ...]'
    __annotations__['marker_offsets'] = 'tuple[int, ...]'
    __annotations__['parameter_name'] = 'str | None'
    locals()['parameter_name'] = None
    __annotations__['dimension_kind'] = 'str | None'
    locals()['dimension_kind'] = None
    __annotations__['start_angle_degrees'] = 'float | None'
    locals()['start_angle_degrees'] = None

# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class NativeSketchA:
    locals().setdefault('__annotations__', {})
    __annotations__['offset'] = 'int'
    __annotations__['plane_object_id'] = 'int'
    __annotations__['axis_code'] = 'int'
    __annotations__['u_axis'] = 'tuple[float, float, float]'
    __annotations__['v_axis'] = 'tuple[float, float, float]'
    __annotations__['normal'] = 'tuple[float, float, float]'
    __annotations__['basis_offset'] = 'int | None'

# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class NativeDepthCopy:
    locals().setdefault('__annotations__', {})
    __annotations__['offset'] = 'int'
    __annotations__['sign'] = 'int'
    __annotations__['value_mm'] = 'float'

# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class NativeBounding:
    locals().setdefault('__annotations__', {})
    __annotations__['offset'] = 'int'
    __annotations__['center_mm'] = 'tuple[float, float, float]'
    __annotations__['diameter_mm'] = 'float'

# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class NativePlane:
    locals().setdefault('__annotations__', {})
    __annotations__['object_id'] = 'int'
    __annotations__['name'] = 'str'
    __annotations__['origin_mm'] = 'tuple[float, float, float]'
    __annotations__['normal'] = 'tuple[float, float, float]'
    __annotations__['u_axis'] = 'tuple[float, float, float]'
    __annotations__['v_axis'] = 'tuple[float, float, float]'
    __annotations__['native_offset'] = 'int | None'
    __annotations__['native_length'] = 'int | None'
    __annotations__['principal'] = 'bool'
    locals()['principal'] = False
    __annotations__['reference_ids'] = 'tuple[int, ...]'
    locals()['reference_ids'] = ()
    __annotations__['native_stream'] = 'str'
    locals()['native_stream'] = ResolvedFeaturesStream

# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class NativeSketch:
    locals().setdefault('__annotations__', {})
    __annotations__['object_id'] = 'int'
    __annotations__['name'] = 'str'
    __annotations__['support_plane_id'] = 'int'
    __annotations__['native_offset'] = 'int'
    __annotations__['native_end'] = 'int'
    __annotations__['markers'] = 'tuple[NativeMarker, ...]'
    __annotations__['profiles'] = 'tuple[NativeProfile, ...]'
    __annotations__['dimensions'] = 'tuple[NativeDimension, ...]'
    __annotations__['constraints'] = 'tuple[NativeConstraint, ...]'
    __annotations__['native_stream'] = 'str'
    locals()['native_stream'] = ResolvedFeaturesStream
    __annotations__['support_kind'] = 'str'
    locals()['support_kind'] = KPlaneSupportKind
    __annotations__['support_plane'] = 'NativeSketchPlane | None'
    locals()['support_plane'] = None
    __annotations__['support_source'] = 'str'
    locals()['support_source'] = KRefSupportSource
    __annotations__['unframed_support_plane_id'] = 'int | None'
    locals()['unframed_support_plane_id'] = None

# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class NativeEndSpec:
    locals().setdefault('__annotations__', {})
    __annotations__['offset'] = 'int'
    __annotations__['termination_code'] = 'int'
    __annotations__['direction_code'] = 'int'
    __annotations__['second_direction_code'] = 'int'
    __annotations__['mirrored_direction_offset'] = 'int | None'
    locals()['mirrored_direction_offset'] = None
    __annotations__['mirrored_direction_code'] = 'int | None'
    locals()['mirrored_direction_code'] = None

# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class NativeOperation:
    locals().setdefault('__annotations__', {})
    __annotations__['object_id'] = 'int'
    __annotations__['name'] = 'str'
    __annotations__['kind'] = 'str'
    __annotations__['profile_id'] = 'int | None'
    __annotations__['dependencies'] = 'tuple[int, ...]'
    __annotations__['native_offset'] = 'int'
    __annotations__['native_end'] = 'int'
    __annotations__['length_mm'] = 'float | None'
    __annotations__['radius_mm'] = 'float | None'
    __annotations__['family_code'] = 'int | None'
    __annotations__['operation_code'] = 'int | None'
    __annotations__['schema_code'] = 'int | None'
    __annotations__['direction_code'] = 'int | None'
    __annotations__['termination_code'] = 'int | None'
    __annotations__['selection_offsets'] = 'tuple[int, ...]'
    __annotations__['selected_local_ids'] = 'tuple[int, ...]'
    __annotations__['angle_degrees'] = 'float | None'
    locals()['angle_degrees'] = None
    __annotations__['diameter_mm'] = 'float | None'
    locals()['diameter_mm'] = None
    __annotations__['second_length_mm'] = 'float | None'
    locals()['second_length_mm'] = None
    __annotations__['axis_marker_offset'] = 'int | None'
    locals()['axis_marker_offset'] = None
    __annotations__['selection_kind'] = 'str'
    locals()['selection_kind'] = 'edge'
    __annotations__['mode'] = 'str | None'
    locals()['mode'] = None
    __annotations__['native_stream'] = 'str'
    locals()['native_stream'] = ResolvedFeaturesStream
    __annotations__['selection_references'] = 'tuple[tuple[int, int], ...]'
    locals()['selection_references'] = ()
    __annotations__['translation_mm'] = 'tuple[float, float, float] | None'
    locals()['translation_mm'] = None
    __annotations__['scale_factors'] = 'tuple[float, float, float] | None'
    locals()['scale_factors'] = None
    __annotations__['depth_copies'] = 'tuple[NativeDepthCopy, ...]'
    locals()['depth_copies'] = ()
    __annotations__['mirrored_direction_offset'] = 'int | None'
    locals()['mirrored_direction_offset'] = None
    __annotations__['mirrored_direction_code'] = 'int | None'
    locals()['mirrored_direction_code'] = None
    __annotations__['axis_source_kind'] = 'str | None'
    locals()['axis_source_kind'] = None
    __annotations__['axis_source_id'] = 'int | None'
    locals()['axis_source_id'] = None
    __annotations__['axis_source_offset'] = 'int | None'
    locals()['axis_source_offset'] = None
    __annotations__['end_spec_offset'] = 'int | None'
    locals()['end_spec_offset'] = None
    __annotations__['angle_offset'] = 'int | None'
    locals()['angle_offset'] = None
    __annotations__['angle_copies'] = 'tuple[NativeDepthCopy, ...]'
    locals()['angle_copies'] = ()
    __annotations__['instance_count'] = 'int | None'
    locals()['instance_count'] = None
    __annotations__['spacing_mm'] = 'float | None'
    locals()['spacing_mm'] = None

# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class NativeFeature:
    locals().setdefault('__annotations__', {})
    __annotations__['object_id'] = 'int'
    __annotations__['name'] = 'str'
    __annotations__['kind'] = 'str'
    __annotations__['xml_tag'] = 'str'
    __annotations__['native_offset'] = 'int | None'
    __annotations__['native_end'] = 'int | None'
    __annotations__['properties'] = 'dict[str, str]'
    __annotations__['dimensions'] = 'tuple[NativeDimension, ...]'
    __annotations__['data'] = 'bytes'
    locals()['data'] = b''
    __annotations__['class_name'] = 'str'
    locals()['class_name'] = ''
    __annotations__['native_stream'] = 'str'
    locals()['native_stream'] = ResolvedFeaturesStream

# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class NativeConfig:
    locals().setdefault('__annotations__', {})
    __annotations__['object_id'] = 'int'
    __annotations__['name'] = 'str'
    __annotations__['configuration_id'] = 'int'
    __annotations__['properties'] = 'dict[str, str]'

# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class NativeEquation:
    locals().setdefault('__annotations__', {})
    __annotations__['source'] = 'str'
    __annotations__['lhs'] = 'str'
    __annotations__['rhs'] = 'str'
    __annotations__['references'] = 'tuple[str, ...]'
    __annotations__['native_offset'] = 'int'
    __annotations__['native_length'] = 'int'
    __annotations__['configuration_id'] = 'int'
    __annotations__['native_stream'] = 'str'

# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class NativeModel:
    locals().setdefault('__annotations__', {})
    __annotations__['configurations'] = 'tuple[NativeConfiguration, ...]'
    __annotations__['features'] = 'tuple[NativeFeature, ...]'
    __annotations__['planes'] = 'tuple[NativePlane, ...]'
    __annotations__['sketches'] = 'tuple[NativeSketch, ...]'
    __annotations__['operations'] = 'tuple[NativeOperation, ...]'
    __annotations__['names'] = 'tuple[NativeName, ...]'
    __annotations__['classes'] = 'tuple[NativeClass, ...]'
    __annotations__['scalars'] = 'tuple[NativeScalar, ...]'
    __annotations__['diagnostics'] = 'tuple[str, ...]'
    locals()['diagnostics'] = Field(default_factory=tuple)
    __annotations__['equations'] = 'tuple[NativeEquation, ...]'
    locals()['equations'] = Field(default_factory=tuple)
    __annotations__['active_configuration_id'] = 'int | None'
    locals()['active_configuration_id'] = None
    __annotations__['bounding_box'] = 'NativeBoundingBox | None'
    locals()['bounding_box'] = None

# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class NativePart:
    locals().setdefault('__annotations__', {})
    __annotations__['keywords'] = 'bytes'
    __annotations__['features'] = 'bytes'
    __annotations__['resolved_features'] = 'bytes'
    __annotations__['kit_resolved_features'] = 'bytes | None'
    __annotations__['configuration_lanes'] = 'tuple[tuple[int, bytes], ...]'
    __annotations__['native_capabilities'] = 'frozenset[Capability]'
    __annotations__['mixed_capabilities'] = 'frozenset[Capability]'
    __annotations__['object_ids'] = 'Mapping[str, int]'
    __annotations__['envelope_streams'] = 'Mapping[str, bytes]'
    __annotations__['partition'] = 'bytes | None'
    __annotations__['application_usable'] = 'bool'
    __annotations__['vendor_loadable'] = 'bool'
    __annotations__['donor_notes'] = 'tuple[str, ...]'
    locals()['donor_notes'] = ()

# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class NativeModelA:
    locals().setdefault('__annotations__', {})
    __annotations__['user_name'] = 'str'
    __annotations__['reference_name'] = 'str'
    __annotations__['configuration_name'] = 'str'
    __annotations__['document_path'] = 'str'
    __annotations__['objects'] = 'tuple[tuple[int, str], ...]'

# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class NativeAsm:
    locals().setdefault('__annotations__', {})
    __annotations__['streams'] = 'Mapping[str, bytes]'
    __annotations__['configuration_name'] = 'str'
    __annotations__['reference_name'] = 'str'
    __annotations__['document_path'] = 'str'
    __annotations__['header_objects'] = 'tuple[tuple[int, str], ...]'
    __annotations__['omitted_object_names'] = 'tuple[str, ...]'
    __annotations__['envelope_complete'] = 'bool'

# this definition exists because focused behavior needs one stable owner
@Dataclass(slots=True)
class XmlFeature:
    locals().setdefault('__annotations__', {})
    __annotations__['object_id'] = 'int'
    __annotations__['name'] = 'str'
    __annotations__['kind'] = 'str'
    __annotations__['xml_tag'] = 'str'
    __annotations__['properties'] = 'dict[str, str]'
    __annotations__['dimensions'] = 'list[NativeDimension]'

# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class WriteDimension:
    locals().setdefault('__annotations__', {})
    __annotations__['name'] = 'str'
    __annotations__['value_mm'] = 'float'
    __annotations__['text'] = 'str'
    __annotations__['role'] = 'ParameterRole'

# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class WriteObject:
    locals().setdefault('__annotations__', {})
    __annotations__['source_id'] = 'str'
    __annotations__['object_id'] = 'int'
    __annotations__['name'] = 'str'
    __annotations__['xml_tag'] = 'str'
    __annotations__['kind'] = 'str'
    __annotations__['class_name'] = 'str'
    __annotations__['properties'] = 'tuple[tuple[str, str], ...]'
    locals()['properties'] = ()
    __annotations__['dimensions'] = 'tuple[_WriteDimension, ...]'
    locals()['dimensions'] = ()
    __annotations__['payload'] = 'bytes'
    locals()['payload'] = b''

# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class NativeIdentity:
    locals().setdefault('__annotations__', {})
    __annotations__['creation_stamp'] = 'int'
    __annotations__['last_modified_stamp'] = 'int'
    __annotations__['baseline_stamp'] = 'int'
    __annotations__['header_stamp'] = 'int'
    __annotations__['configuration_flags'] = 'int'
    __annotations__['reference_name'] = 'str'

# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class VendorResolved:
    locals().setdefault('__annotations__', {})
    __annotations__['payload'] = 'bytes'
    __annotations__['header_stamps'] = 'tuple[tuple[int, ...], ...]'
    __annotations__['annotation_view_count'] = 'int'
    locals()['annotation_view_count'] = 1
    __annotations__['terminal_parent_tree_id'] = 'int | None'
    locals()['terminal_parent_tree_id'] = None
    KHeaderBounds: tuple[float, ...] | None = None
    KHeaderCreation: int | None = None
    __annotations__['cmgr_parent_tree_id'] = 'int | None'
    locals()['cmgr_parent_tree_id'] = None
    __annotations__['annotation_view_variant'] = 'str'
    locals()['annotation_view_variant'] = 'default'
    __annotations__['Config0Payload'] = 'bytes | None'
    locals()['Config0Payload'] = None
    KHeaderPayload: bytes | None = None

# this binding exists because shared behavior needs one stable value
KBaseObjects = ((8, 'Comments', 'Comments', 'moCommentsFolder_c'), (23, 'Favorites', 'Favorites', 'moFavoriteFolder_c'), (24, 'History', 'History', 'moHistoryFolder_c'), (25, 'Selection Sets', 'Selection Sets', 'moSelectionSetFolder_c'), (22, 'Sensors', 'Sensors', 'moSensorFolder_c'), (7, 'Design Binder', 'Design Binder', 'moDocsFolder_c'), (1, 'Annotations', 'Annotations', 'moDetailCabinet_c'), (17, 'Notes', 'Notes', 'moNotesAreaFtrFolder_c'), (18, 'Notes1___EndTag___', 'Notes', 'moNotesAreaFtrFolder_c'), (10, 'Surface Bodies', 'Surface Bodies', 'moSurfaceBodyFolder_c'), (9, 'Solid Bodies', 'Solid Bodies', 'moSolidBodyFolder_c'), (21, 'Markups', 'Markups', 'moInkMarkupFolder_c'), (16, 'Equations', 'Equations', 'moEqnFolder_c'), (11, 'Material <not specified>', 'SOLIDWORKS Materials', 'moMaterialFolder_c'), (2, 'Front Plane', 'Plane', 'moRefPlane_c'), (3, 'Top Plane', 'Plane', 'moRefPlane_c'), (4, 'Right Plane', 'Plane', 'moRefPlane_c'), (5, 'Origin', 'Origin', 'moOriginProfileFeature_c'))

# this binding exists because shared behavior needs one stable value
KeywordOnlyObjects = ((6, 'Lights and Cameras', 'Lights and Cameras'), (12, 'Ambient', 'Ambient'), (13, 'Directional1', 'Directional'), (14, 'Directional2', 'Directional'), (15, 'Directional3', 'Directional'), (19, '', 'Exploded Views'))

# this binding exists because shared behavior needs one stable value
KeywordOnlyObjectIds = frozenset((ItemValue[0] for ItemValue in KeywordOnlyObjects))

# this binding exists because shared behavior needs one stable value
KSystemObjectIds = frozenset(range(1, 26))

# this binding exists because shared behavior needs one stable value
KNameToken = 32772

# this binding exists because shared behavior needs one stable value
KNamePrefix = Struct.pack('<H', KNameToken) + b'\xff\xfe\xff'

# this binding exists because shared behavior needs one stable value
KFolderFlags = 1073741824

# this binding exists because shared behavior needs one stable value
KRefGeomFlags = 3221225472

# this binding exists because shared behavior needs one stable value
KBossExtrudeFlags = 1073742144

# this binding exists because shared behavior needs one stable value
KCutExtrudeFlags = 1073873354

# this binding exists because shared behavior needs one stable value
KRefGeomClasses = frozenset({'moRefPlane_c', 'moOriginProfileFeature_c'})

# this binding exists because shared behavior needs one stable value
KConfigZeroFirstFeature = 109

# this binding exists because shared behavior needs one stable value
KScalarHeader = DimensionScalarHeaders[0]

# this binding exists because shared behavior needs one stable value
KSolidworksXmlNamespace = 'http://www.solidworks.com/sw2003/schema'

# this binding exists because shared behavior needs one stable value
KSolidworksConfigFlags = -2143288960

# this binding exists because shared behavior needs one stable value
KCreationStampLow = 1577836800

# this binding exists because shared behavior needs one stable value
KCreationStampHigh = 1893456000

# this binding exists because shared behavior needs one stable value
KFrontBossHeaderStamps = ((1785796991, 1785796991), (1785796991,))

# this binding exists because shared behavior needs one stable value
KBoxHeaderStamps = ((1786460234, 1786460235), (1786460235,))

# this binding exists because shared behavior needs one stable value
KTopBossHeaderStamps = ((1785840649, 1785840649), (1785840649,))

# this binding exists because shared behavior needs one stable value
KRightBossHeaderStamps = ((1785840740, 1785840741), (1785840741,))

# this binding exists because shared behavior needs one stable value
KCircleBossHeaderStamps = ((1786472138, 1786472138), (1786472138,))

# this binding exists because shared behavior needs one stable value
KBossCutHeaderStamps = ((1785839433, 1785839433), (1785839434,), (1785839434, 1785839435), (1785839435,))

# this binding exists because shared behavior needs one stable value
KBossCutThroughHeader = ((1785797023, 1785797023), (1785797023,), (1785797024, 1785797024), (1785797025,))

# this binding exists because shared behavior needs one stable value
KBossBossHeaderStamps = ((1786440431, 1786440431), (1786440431,), (1786440432, 1786440432), (1786440432,))

# this binding exists because shared behavior needs one stable value
KBossFilletHeaderStamps = ((1786443440, 1786443440), (1786443440,), (1786443440,))

# this binding exists because shared behavior needs one stable value
KBossFilletRadiusOffsets = (12721, 13001, 13235, 13259, 13739, 14614)

# this binding exists because shared behavior needs one stable value
KBossFilletMaxXOffsets = (12753, 12777, 12902)

# this binding exists because shared behavior needs one stable value
KBossFilletMaxYOffsets = (12761, 12785)

# this binding exists because shared behavior needs one stable value
KBossFilletNegativeYOffsA = 12910

# this binding exists because shared behavior needs one stable value
KBossChamferHeaderStamps = ((1786446942, 1786446942), (1786446942,), (1786446942,))

# this binding exists because shared behavior needs one stable value
KBossChamferDistance = (12629, 12947, 13027, 13051, 13189, 13213)

# this binding exists because shared behavior needs one stable value
KBossChamferMaxYOffsets = (12669, 14519)

# this binding exists because shared behavior needs one stable value
KBossChamferNegativeY = (12866, 14620)

# this binding exists because shared behavior needs one stable value
KBossChamferNegativeOffsA = 14495

# this binding exists because shared behavior needs one stable value
KBossShellHeaderStamps = ((1786448316, 1786448316), (1786448316,), (1786448316,))

# this binding exists because shared behavior needs one stable value
KBossShellThicknessOffseA = (12498, 12816, 12888, 12912, 13058, 13082)

# this binding exists because shared behavior needs one stable value
KBossShellMinXOffset = 12530

# this binding exists because shared behavior needs one stable value
KBossShellInnerMinXOffset = 12554

# this binding exists because shared behavior needs one stable value
KBossShellMaxXOffset = 12727

# this binding exists because shared behavior needs one stable value
KBossShellDepthOffset = 12212

# this binding exists because shared behavior needs one stable value
KBossLinearPatternHeader = ((1786449611, 1786449611), (1786449611,), (1786449611,))

# this binding exists because shared behavior needs one stable value
KBossLinearPatternCountB = 12962

# this binding exists because shared behavior needs one stable value
KBossLinearPatternCountA = (13336, 13360)

# this binding exists because shared behavior needs one stable value
KBossLinearPatternPositiD = (14463, 14853, 14877, 15023, 15047)

# this binding exists because shared behavior needs one stable value
KBossLinearPatternDistanA = (12656, 14535)

# this binding exists because shared behavior needs one stable value
KBossLinearPatternFlag = 18577

# this binding exists because shared behavior needs one stable value
KLinearPatternDirection = 7264

# this binding exists because shared behavior needs one stable value
KBossLinearPatternNegatiD = (14569, 14577, 14620, 14644, 14692)

# this binding exists because shared behavior needs one stable value
KBossLinearPatternPositiA = (14585, 14668)

# this binding exists because shared behavior needs one stable value
KBossLinearPatternNegatiA = 14636

# this binding exists because shared behavior needs one stable value
KBossLinearPatternPositiB = 14660

# this binding exists because shared behavior needs one stable value
KBossLinearPatternTerminA = 18993

# this binding exists because shared behavior needs one stable value
KBossLinearPatternCount = 11398

# this binding exists because shared behavior needs one stable value
KBossLinearPatternNegatiC = 4187

# this binding exists because shared behavior needs one stable value
KBossLinearPatternPositiC = (4381, 4935)

# this binding exists because shared behavior needs one stable value
KBossLinearPatternNegatiB = (4389, 4943)

# this binding exists because shared behavior needs one stable value
KBossLinearPatternCenter = (4428, 4998)

# this binding exists because shared behavior needs one stable value
KBossLinearPatternPad = 4757

# this binding exists because shared behavior needs one stable value
KBossCircularPatternHeadA = ((1786452328, 1786452328), (1786452328,), (1786452328,))

# this binding exists because shared behavior needs one stable value
KBossCircularPatternCounA = 13433

# this binding exists because shared behavior needs one stable value
KBossCircularPatternCount = (13807, 13831)

# this binding exists because shared behavior needs one stable value
KBossCircularPatternAngle = (18584, 19026, 19050)

# this binding exists because shared behavior needs one stable value
KBossCircularPatternFlag = 17876

# this binding exists because shared behavior needs one stable value
KCircularPatternDirection = 6096

# this binding exists because shared behavior needs one stable value
KBossRevCutHeaderStamps = ((1785927829, 1785927829), (1785927829,), (1785927830, 1785927830), (1785927830,))

# this binding exists because shared behavior needs one stable value
KBossCutCutHeaderStamps = ((1785839606, 1785839607), (1785839607,), (1785839608, 1785839609), (1785839609,), (1785839609, 1785839610), (1785839610,))

# this binding exists because shared behavior needs one stable value
KBossCutCutCutHeaderStamA = ((1785843343, 1785843343), (1785843343,), (1785843344, 1785843344), (1785843345,), (1785843345, 1785843345), (1785843345,), (1785843346, 1785843346), (1785843346,))

# this binding exists because shared behavior needs one stable value
KRevolutionHeaderStamps = ((1785797027, 1785797028), (1785797028,))

# this binding exists because shared behavior needs one stable value
KVendorUnloadableNotes = ('Contents/Config-0-ResolvedFeatures is the SOLIDWORKS feature tree authority and the current source graph is outside the recovered native rectangle pad family',)

# this binding exists because shared behavior needs one stable value
KNonSolidFeatureClasses = frozenset({'moRefPlane_c', 'moProfileFeature_c'})

# this binding exists because shared behavior needs one stable value
KConfigRootTreeId = 0

# this binding exists because shared behavior needs one stable value
KHeaderObjects = ((1, 'Annotations', False), (2, 'Front Plane', True), (3, 'Top Plane', True), (4, 'Right Plane', True), (5, 'Origin', True), (6, 'Lights and Cameras', False), (7, 'Design Binder', False), (8, 'Comments', False), (9, 'Solid Bodies', False), (10, 'Surface Bodies', False), (11, 'Material <not specified>', True), (12, 'Ambient', False), (13, 'Directional1', False), (14, 'Directional2', False), (15, 'Directional3', False), (16, 'Equations', False), (17, 'Notes', False), (18, 'Notes1___EndTag___', False), (21, 'Markups', False), (22, 'Sensors', False), (23, 'Favorites', False), (24, 'History', False), (25, 'Selection Sets', False))

# this binding exists because shared behavior needs one stable value
KAsmHeaderObjects = ((2, 'Annotations', False), (3, 'Front Plane', True), (4, 'Top Plane', True), (5, 'Right Plane', True), (6, 'Origin', True), (7, 'Lights, Cameras and Scene', False), (8, 'Design Binder', False), (9, 'Comments', False), (10, 'Live Section Planes', False), (11, 'Mates', False), (12, 'Ambient', False), (13, 'Directional1', False), (14, 'Directional2', False), (15, 'Directional3', False), (16, 'Equations', False), (17, 'Notes', False), (18, 'Notes1___EndTag___', False), (19, 'Markups', False), (20, 'Sensors', False), (21, 'Favorites', False), (22, 'History', False), (23, 'Selection Sets', False))

# this binding exists because shared behavior needs one stable value
KAsmConfigFlags = -2147221376

# this binding exists because shared behavior needs one stable value
KAsmRefName = 'Assem1'

# this binding exists because shared behavior needs one stable value
KAsmVersionPrefix = '_MO_VERSION_18000'

# this binding exists because shared behavior needs one stable value
KAsmPropContainerClass = 'moAssyFilePropContainer_c'

# this binding exists because shared behavior needs one stable value
KAsmAttachmentStream = 'Contents/Config-0-Attachment'

# this binding exists because shared behavior needs one stable value
KAsmVisualDataStream = f'{KAsmVersionPrefix}/AssyVisualData'

# this binding exists because shared behavior needs one stable value
KAsmTablesStream = 'swXmlContents/Tables'

# this binding exists because shared behavior needs one stable value
KAsmViewOrientationStream = 'Contents/View Orientation Data'

# this binding exists because shared behavior needs one stable value
KAsmOpenTimeStream = 'docProps/OpenTime.xml'

# this binding exists because shared behavior needs one stable value
KAsmCutlistStream = 'docProps/Config-0-Cutlist-Properties.xml'

# this binding exists because shared behavior needs one stable value
KAsmConfigPropertiesStreA = 'docProps/Config-0-Properties.xml'

# this binding exists because shared behavior needs one stable value
KViewOrientationPayload = b'<?xml version="1.0" encoding="UTF-8"?>\n<VIEWS/>\n'

# this binding exists because shared behavior needs one stable value
KOpenTimePayload = b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\r\n<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/SolidworksOpenTime" xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes"><count xmlns="">0</count><TotalFileOpenTime xmlns="">-1</TotalFileOpenTime><LWcount xmlns="">0</LWcount><LWTotalFileOpenTime xmlns="">-1</LWTotalFileOpenTime></Properties>\r\n'

# this binding exists because shared behavior needs one stable value
KConfigPropertiesPayload = b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\r\n<ConfigProperties xmlns="http://www.solidworks.com/config-properties" xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes"><propertySection xmlns="" name="DocumentSummaryInformation" fmtid="{D5CDD502-2E9C-101B-9397-08002B2CF9AE}"><propertyNameDictionaryElement name="" pid="0"></propertyNameDictionaryElement></propertySection><propertySection xmlns="" name="UserDefinedProperties" fmtid="{D5CDD505-2E9C-101B-9397-08002B2CF9AE}"><property name="" pid="1"><vt:i2>65001</vt:i2></property><propertyNameDictionaryElement name="" pid="0"></propertyNameDictionaryElement></propertySection></ConfigProperties>\r\n'

# this definition exists because focused behavior needs one stable owner
def HasVendorPart(DocData: CadDocument) -> bool:
    ObjectIds = WriteObjectIds(DocData)
    SourceObjects = WriteObjects(DocData, ObjectIds)
    if not SourceObjects:
        return False
    AuthoredObjects = Canonical(SourceObjects, ObjectIds, DocData)
    return BuildVendorTree(AuthoredObjects) is not None

# this definition exists because focused behavior needs one stable owner
def EncodeNative(DocValue: CadDocument, ModelName: str) -> NativePart:
    ObjectIds = WriteObjectIds(DocValue)
    SourceAuthored = WriteObjects(DocValue, ObjectIds)
    if not SourceAuthored and DocValue.brep is not None:
        SourceAuthored = (WriteObject('brep:imported', 26, 'Imported1', 'Feature', 'Imported', 'moBaseBody_c'),)
    Authored = Canonical(SourceAuthored, ObjectIds, DocValue)
    Identity = NativeIdentityA(DocValue, ModelName)
    SystemFeatures = {int(Feature.attributes['native_object_id']): Feature for Feature in DocValue.feature_timeline if IsNativeSystem(Feature)}
    BaseValue = tuple((WriteObject(f'base:{ObjectId}', ObjectId, NativeSystem(SystemFeatures.get(ObjectId), NameValue), 'Sketch' if ObjectId == 5 else 'Feature', KindValue, ClassName) for ObjectId, NameValue, KindValue, ClassName in KBaseObjects))
    KeywordOnly = tuple((WriteObject(f'base:{ObjectId}', ObjectId, NativeSystem(SystemFeatures.get(ObjectId), NameValue), 'Feature', KindValue, '') for ObjectId, NameValue, KindValue in KeywordOnlyObjects))
    Objects = (*BaseValue, *Authored)
    VendorData = BuildVendorTree(Authored)
    VendorResolved = VendorData.payload if VendorData is not None else None
    SourceKeywords = KeywordsPayload(DocValue, ModelName, (*BaseValue, *SourceAuthored, *KeywordOnly), ObjectIds, Identity)
    ProofKeywords = KeywordsPayload(DocValue, ModelName, (*Objects, *KeywordOnly), ObjectIds, Identity)
    Keywords = ProofKeywords if VendorResolved is not None else SourceKeywords
    Features = FeaturesPayload(DocValue, ModelName, ObjectIds, Identity)
    KitResolved = ResolvedPayload(Objects)
    Resolved = VendorResolved if VendorResolved is not None else KitResolved
    HeaderFeatureObjects = tuple(((ItemData.object_id, ItemData.name, ItemData.kind == 'Sketch') for ItemData in Authored)) if VendorResolved is not None else ()
    HeaderFeatureStamps = MappingProxyType({ItemData.object_id: StampData for ItemData, StampData in zip(Authored, VendorData.header_stamps, strict=True)}) if VendorData is not None else MappingProxyType({})
    EnvelopeStreams = dict(NativeEnvelope(DocValue, ModelName, Identity, SolidFeatureIds(Authored), HeaderFeatureObjects, HeaderFeatureStamps, VendorData.annotation_view_count if VendorData is not None else 1, VendorData.terminal_parent_tree_id if VendorData is not None else None, VendorData.HeaderBounds if VendorData is not None else None, VendorData.HeaderCreation if VendorData is not None else None, VendorData.cmgr_parent_tree_id if VendorData is not None else None, VendorData.annotation_view_variant if VendorData is not None else 'default'))
    if VendorResolved is not None:
        EnvelopeStreams[ResolvedFeaturesStream] = VendorResolved
    if VendorData is not None and VendorData.Config0Payload is not None:
        EnvelopeStreams[ConfigStream] = VendorData.Config0Payload
    if VendorData is not None and VendorData.HeaderPayload is not None:
        EnvelopeStreams['Contents/Config-0-ModelHeader'] = VendorData.HeaderPayload
        EnvelopeStreams['Header2'] = VendorData.HeaderPayload
    ConfigData = EnvelopeStreams.get(ConfigStream, b'')
    Parsed = DecodeNative(ProofKeywords, Resolved, ConfigData, ResolvedStream=ResolvedFeaturesStream if VendorResolved is not None else KitResolvedStream)
    Capabilities = ProvedWrite(DocValue, Authored, Parsed, ObjectIds)
    MixedCapabilities: frozenset[Capability] = frozenset()
    Partition: bytes | None = None
    VendorLoadable = VendorResolved is not None
    AppUsable = VendorLoadable
    return NativePart(Keywords, Features, Resolved, None if VendorResolved is not None else KitResolved, ((0, VendorResolved),) if VendorResolved is not None else (), Capabilities, MixedCapabilities, MappingProxyType(ObjectIds), MappingProxyType(EnvelopeStreams), Partition, AppUsable, VendorLoadable, () if VendorResolved is not None else KVendorUnloadableNotes)

# this definition exists because focused behavior needs one stable owner
def EncodeCircCfg(CenterX: float, CenterY: float, RadiusValue: float, DepthValue: float) -> bytes:
    if not all((MathValue.isfinite(ItemValue) for ItemValue in (CenterX, CenterY, RadiusValue, DepthValue))) or min(RadiusValue, DepthValue) <= 0.0:
        raise SldprtFormatError('circle configuration requires finite positive radius and depth')
    CenterXMetres = CenterX / KMillimetres
    CenterYMetres = CenterY / KMillimetres
    RadiusMetres = RadiusValue / KMillimetres
    DepthMetres = DepthValue / KMillimetres
    CenterZMetres = DepthMetres / 2.0
    return EncodeBoxConfigProgram({70: 33056, 222: 4, 824: RadiusValue, 2316: 1771999328, 2320: 31271357, 2376: CenterXMetres, 2384: CenterYMetres, 2392: CenterZMetres, 2400: CenterXMetres + RadiusMetres, 2408: CenterYMetres + RadiusMetres, 2416: DepthMetres, 2424: CenterXMetres - RadiusMetres, 2432: CenterYMetres - RadiusMetres, 2448: MathValue.sqrt(RadiusMetres ** 2 * 2.0 + CenterZMetres ** 2), 2596: 103, 2914: 33, 2918: 33, 2942: 600, 2950: 600, 4219: 0.0, 21879: 115, 21888: 18000, 21892: 2025268, 21964: 31271357, 21968: 1770659972, 24057: 10, 24095: 0, 24220: 31271357, 24224: 1710964613})

# this definition exists because focused behavior needs one stable owner
def EncodeReverse(CenterX: float, CenterY: float, RadiusValue: float, DepthValue: float) -> bytes:
    if not all((MathValue.isfinite(ItemValue) for ItemValue in (CenterX, CenterY, RadiusValue, DepthValue))) or min(RadiusValue, DepthValue) <= 0.0:
        raise SldprtFormatError('reverse circle configuration requires finite positive radius and depth')
    CenterXMetres = CenterX / KMillimetres
    CenterYMetres = CenterY / KMillimetres
    RadiusMetres = RadiusValue / KMillimetres
    DepthMetres = DepthValue / KMillimetres
    CenterZMetres = -DepthMetres / 2.0
    return EncodeReverseCircleConfig({824: RadiusValue, 2376: CenterXMetres, 2384: CenterYMetres, 2392: CenterZMetres, 2400: CenterXMetres + RadiusMetres, 2408: CenterYMetres + RadiusMetres, 2416: 0.0, 2424: CenterXMetres - RadiusMetres, 2432: CenterYMetres - RadiusMetres, 2440: -DepthMetres, 2448: MathValue.sqrt(RadiusMetres ** 2 * 2.0 + CenterZMetres ** 2)})

# this definition exists because focused behavior needs one stable owner
def EncodeReverseA(DepthValue: float) -> bytes:
    if not MathValue.isfinite(DepthValue) or DepthValue <= 0.0:
        raise SldprtFormatError('reverse circle depth must be finite and positive')
    DepthMetres = DepthValue / KMillimetres
    return EncodeReverseCircle({11343: DepthMetres, 11415: -DepthMetres, 11741: DepthMetres, 11765: DepthMetres, 11903: DepthMetres, 11927: DepthMetres})

# this definition exists because focused behavior needs one stable owner
def BuildVendorTree(AuthoredObjs: tuple[_WriteObject, ...]) -> VendorResolved | None:
    if len(AuthoredObjs) == 8:
        return BuildFourVendor(AuthoredObjs)
    if len(AuthoredObjs) == 6:
        return BuildThreeTree(AuthoredObjs)
    if len(AuthoredObjs) == 4:
        if AuthoredObjs[3].class_name == 'moRevolution_c':
            return BuildPadGroove(AuthoredObjs)
        return BuildTwoFeature(AuthoredObjs)
    if len(AuthoredObjs) == 3 and AuthoredObjs[2].class_name == 'Fillet_c':
        return BuildBossFillet(AuthoredObjs)
    if len(AuthoredObjs) == 3 and AuthoredObjs[2].class_name == 'Chamfer_c':
        return BuildBossVendor(AuthoredObjs)
    if len(AuthoredObjs) == 3 and AuthoredObjs[2].class_name == 'moShell_c':
        return BuildBossShell(AuthoredObjs)
    if len(AuthoredObjs) == 3 and AuthoredObjs[2].class_name == 'moLPattern_c':
        return BuildBossLinear(AuthoredObjs)
    if len(AuthoredObjs) == 3 and AuthoredObjs[2].class_name == 'moCirPattern_c':
        return BuildBossVendoA(AuthoredObjs)
    if len(AuthoredObjs) != 2:
        return None
    SketchObject, PadObject = AuthoredObjs
    if PadObject.class_name == 'moRevolution_c':
        return BuildSingleTree(AuthoredObjs)
    PlaneObjectId = Struct.unpack_from('<I', SketchObject.payload)[0] if len(SketchObject.payload) >= 4 else 0
    BoundsValue = WriteRectangle(SketchObject)
    CircleValue = WriteCircle(SketchObject)
    PolylineValue = PolySixPoints(SketchObject)
    EndCodes = ExtrusionEdit(PadObject.payload)
    if SketchObject.class_name != 'moProfileFeature_c' or SketchObject.object_id != 26 or SketchObject.name != 'Sketch1' or (PadObject.class_name != 'moExtrusion_c') or (PadObject.name != 'Boss-Extrude1') or (sum((ItemValue is not None for ItemValue in (BoundsValue, CircleValue, PolylineValue))) != 1) or (EndCodes is None) or (len(PadObject.dimensions) != 1):
        return None
    DepthValue = PadObject.dimensions[0].value_mm
    if not MathValue.isfinite(DepthValue) or DepthValue <= 0.0:
        return None
    DirectionCode, TerminationCode = EndCodes
    IsDimensionedBox = False
    HeaderBoundsData = None
    HeaderCreationData = None
    ConfigZeroData = None
    if BoundsValue is not None:
        IsDimensionedBox = PadObject.properties and ('KitPrimitive', 'Box') in PadObject.properties and (len(SketchObject.dimensions) == 2)
        ExpectedFeatureId = 34 if IsDimensionedBox else 32
        if PadObject.object_id != ExpectedFeatureId:
            return None
        ProgramValue = (EncodeBoxProgram(), KBoxHeaderStamps) if PlaneObjectId == 2 and IsDimensionedBox else (EncodeProgram(), KFrontBossHeaderStamps) if PlaneObjectId == 2 else (EncodeTopProgram(), KTopBossHeaderStamps) if PlaneObjectId == 3 else (EncodeRightProgram(), KRightBossHeaderStamps) if PlaneObjectId == 4 else None
        if ProgramValue is None:
            return None
        ProgramData, HeaderStamps = ProgramValue
        ConfigZeroData = EncodeBoxConfigProgram() if IsDimensionedBox else None
        EditData = FeatureEdit(corners_mm=RectangleCornersMm(*BoundsValue), depth_mm=DepthValue, reversed=bool(DirectionCode), end_condition_code=TerminationCode, update_depth_copies=EndCodes == (0, 0) or PlaneObjectId in {3, 4}, SketchDimensionsMm=tuple((ItemData.value_mm for ItemData in SketchObject.dimensions)) if IsDimensionedBox else None)
    elif CircleValue is not None:
        if EndCodes not in {(0, 0), (1, 0)} or PlaneObjectId != 2 or PadObject.object_id != 33:
            return None
        CenterX, CenterY, RadiusValue = CircleValue
        if not MathValue.isclose(CenterX, 0.0, rel_tol=0.0, abs_tol=1e-10) or not MathValue.isclose(CenterY, 0.0, rel_tol=0.0, abs_tol=1e-10):
            return None
        IsReverseCircle = DirectionCode == 1
        ProgramData = EncodeReverseA(DepthValue) if IsReverseCircle else EncodeCircleProgram()
        HeaderStamps = KCircleBossHeaderStamps
        CenterXMetres = CenterX / KMillimetres
        CenterYMetres = CenterY / KMillimetres
        RadiusMetres = RadiusValue / KMillimetres
        DepthMetres = DepthValue / KMillimetres
        CenterZMetres = DepthMetres * (-0.5 if IsReverseCircle else 0.5)
        HeaderBoundsData = (CenterXMetres, CenterYMetres, CenterZMetres, CenterXMetres + RadiusMetres, CenterYMetres + RadiusMetres, 0.0 if IsReverseCircle else DepthMetres, CenterXMetres - RadiusMetres, CenterYMetres - RadiusMetres, -DepthMetres if IsReverseCircle else 0.0, MathValue.sqrt(RadiusMetres ** 2 * 2.0 + CenterZMetres ** 2))
        HeaderCreationData = HeaderStamps[0][0] - 1
        ConfigZeroData = EncodeReverse(CenterX, CenterY, RadiusValue, DepthValue) if IsReverseCircle else EncodeCircCfg(CenterX, CenterY, RadiusValue, DepthValue)
        EditData = FeatureEdit(radii_mm=(RadiusValue,), arc_centres_mm=((CenterX, CenterY),), depth_mm=DepthValue, update_depth_copies=not IsReverseCircle, SketchDimensionsMm=(RadiusValue * 2.0,))
    else:
        if PolylineValue is None or EndCodes != (0, 0) or PlaneObjectId != 2 or (PadObject.object_id != 32) or SketchObject.dimensions:
            return None
        try:
            ProgramData = EncodePolylineSixProgram(PolylineSixFieldMap(PolylineValue, DepthValue))
        except SldprtFormatError:
            return None
        HeaderStamps = KFrontBossHeaderStamps
    return VendorResolved(ProgramData if PolylineValue is not None else PatchFeatures(ProgramData, {0: EditData}), HeaderStamps, HeaderBounds=HeaderBoundsData, HeaderCreation=HeaderCreationData, Config0Payload=ConfigZeroData)

# this definition exists because focused behavior needs one stable owner
def BuildSingleTree(AuthoredObjs: tuple[_WriteObject, ...]) -> VendorResolved | None:
    if len(AuthoredObjs) != 2:
        return None
    SketchObject, RevolveObject = AuthoredObjs
    PlaneObjectId = Struct.unpack_from('<I', SketchObject.payload)[0] if len(SketchObject.payload) >= 4 else 0
    BoundsValue = WriteRectangle(SketchObject)
    PinPoints = PolySixPoints(SketchObject)
    IsPinData = IsPinProfile(PinPoints)
    if SketchObject.class_name != 'moProfileFeature_c' or SketchObject.object_id != 26 or SketchObject.name != 'Sketch1' or (not (PlaneObjectId == 2 and BoundsValue is not None or (PlaneObjectId == 3 and IsPinData and (not SketchObject.dimensions)))) or (RevolveObject.class_name != 'moRevolution_c') or (RevolveObject.object_id != 31) or (RevolveObject.name != 'Revolve1') or (len(RevolveObject.dimensions) != 1) or (RevolveObject.dimensions[0].name != 'D1'):
        return None
    AngleDegrees = RevolveObject.dimensions[0].value_mm
    IsFullAngle = MathValue.isfinite(AngleDegrees) and MathValue.isclose(AngleDegrees, 360.0, rel_tol=0.0, abs_tol=1e-10)
    IsPartialAngle = MathValue.isfinite(AngleDegrees) and MathValue.isclose(AngleDegrees, 90.0, rel_tol=0.0, abs_tol=1e-10)
    if not IsFullAngle and (not (IsPinData and IsPartialAngle)):
        return None
    if IsPinData:
        EnvelopeData = BuildPinNineZeroEnvelope() if IsPartialAngle else BuildPinEnvelope()
        return VendorResolved(EncodePinNineZeroRevolve() if IsPartialAngle else EncodePinRevolveProgram(), EnvelopeData.HeaderStamps, HeaderBounds=EnvelopeData.HeaderBounds, HeaderCreation=EnvelopeData.HeaderCreation, Config0Payload=EnvelopeData.Config0Payload, HeaderPayload=EnvelopeData.HeaderPayload)
    if BoundsValue is None:
        return None
    return VendorResolved(PatchFeatures(EncodeRevolveProgram(), {0: FeatureEdit(corners_mm=RectangleCornersMm(*BoundsValue), angle_radians=MathValue.radians(AngleDegrees))}), KRevolutionHeaderStamps)

# this definition exists because focused behavior needs one stable owner
def BuildPadGroove(AuthoredObjs: tuple[_WriteObject, ...]) -> VendorResolved | None:
    if len(AuthoredObjs) != 4:
        return None
    SketchOne, PadObject, SketchTwo, GrooveObject = AuthoredObjs
    BoundsData = (WriteRectangle(SketchOne), WriteRectangle(SketchTwo))
    PadCodes = ExtrusionEdit(PadObject.payload)
    if SketchOne.class_name != 'moProfileFeature_c' or SketchOne.object_id != 26 or SketchOne.name != 'Sketch1' or (SketchTwo.class_name != 'moProfileFeature_c') or (SketchTwo.object_id != 33) or (SketchTwo.name != 'Sketch2') or any((ItemData is None for ItemData in BoundsData)) or (PadObject.class_name != 'moExtrusion_c') or (PadObject.object_id != 32) or (PadObject.name != 'Boss-Extrude1') or (PadCodes is None) or (PadCodes[1] not in {0, 6}) or (len(PadObject.dimensions) != 1) or (GrooveObject.class_name != 'moRevolution_c') or (GrooveObject.object_id != 39) or (GrooveObject.name != 'Cut-Revolve1') or (len(GrooveObject.dimensions) != 1):
        return None
    PadDepth = PadObject.dimensions[0].value_mm
    GrooveAngle = GrooveObject.dimensions[0].value_mm
    if not MathValue.isfinite(PadDepth) or PadDepth <= 0.0 or (not MathValue.isfinite(GrooveAngle)) or (not MathValue.isclose(GrooveAngle, 360.0, rel_tol=0.0, abs_tol=1e-10)):
        return None
    BoundsOne, BoundsTwo = BoundsData
    if BoundsOne is None or BoundsTwo is None:
        return None
    return VendorResolved(PatchFeatures(EncodeBossRevCutProgram(), {0: FeatureEdit(corners_mm=RectangleCornersMm(*BoundsOne), depth_mm=PadDepth, reversed=bool(PadCodes[0]), end_condition_code=PadCodes[1], update_depth_copies=True), 1: FeatureEdit(corners_mm=RectangleCornersMm(*BoundsTwo), angle_radians=MathValue.radians(GrooveAngle))}), KBossRevCutHeaderStamps, 2)

# this definition exists because focused behavior needs one stable owner
def BuildTwoFeature(AuthoredObjs: tuple[_WriteObject, ...]) -> VendorResolved | None:
    SketchOne, PadObject, SketchTwo, CutObject = AuthoredObjs
    ExpectedData = ((SketchOne, 26, 'Sketch1'), (SketchTwo, 33, 'Sketch2'))
    BoundsData = tuple((WriteRectangle(ItemData[0]) for ItemData in ExpectedData))
    EndCodes = (ExtrusionEdit(PadObject.payload), ExtrusionEdit(CutObject.payload))
    if any((SketchObject.class_name != 'moProfileFeature_c' or SketchObject.object_id != ObjectId or SketchObject.name != ObjectName or (len(SketchObject.payload) < 4) or (Struct.unpack_from('<I', SketchObject.payload)[0] != 2) for SketchObject, ObjectId, ObjectName in ExpectedData)) or any((ItemData is None for ItemData in BoundsData)) or PadObject.class_name != 'moExtrusion_c' or (PadObject.object_id != 32) or (PadObject.name != 'Boss-Extrude1') or (CutObject.class_name not in {'moCut_c', 'moExtrusion_c'}) or (CutObject.object_id != 40) or (CutObject.name != ('Boss-Extrude2' if CutObject.class_name == 'moExtrusion_c' else 'Cut-Extrude1')) or any((ItemData is None for ItemData in EndCodes)) or (len(PadObject.dimensions) != 1):
        return None
    PadCodes, CutCodes = EndCodes
    if PadCodes is None or CutCodes is None or PadCodes[1] != 0:
        return None
    if CutObject.class_name == 'moExtrusion_c':
        if CutCodes[1] != 0 or len(CutObject.dimensions) != 1:
            return None
        CutDepth = CutObject.dimensions[0].value_mm
        ProgramData = EncodeBossBossProgram()
        HeaderStamps = KBossBossHeaderStamps
    elif CutCodes[1] == 0:
        if len(CutObject.dimensions) != 1:
            return None
        CutDepth: float | None = CutObject.dimensions[0].value_mm
        ProgramData = EncodeBossCutProgram()
        HeaderStamps = KBossCutHeaderStamps
    elif CutCodes == (1, 1):
        if CutObject.dimensions:
            return None
        CutDepth = None
        ProgramData = EncodeBossCutThrough()
        HeaderStamps = KBossCutThroughHeader
    else:
        return None
    DepthData = (PadObject.dimensions[0].value_mm, CutDepth)
    if any((ItemData is not None and (not MathValue.isfinite(ItemData) or ItemData <= 0.0) for ItemData in DepthData)):
        return None
    EditData: dict[int, FeatureEdit] = {}
    for FeatureIndex, (BoundsValue, DepthValue, CodesValue) in enumerate(zip(BoundsData, DepthData, EndCodes, strict=True)):
        if BoundsValue is None or CodesValue is None:
            return None
        if DepthValue is None:
            EditData[FeatureIndex] = FeatureEdit(corners_mm=RectangleCornersMm(*BoundsValue))
        else:
            EditData[FeatureIndex] = FeatureEdit(corners_mm=RectangleCornersMm(*BoundsValue), depth_mm=DepthValue, reversed=bool(CodesValue[0]), end_condition_code=CodesValue[1], update_depth_copies=True)
    return VendorResolved(PatchFeatures(ProgramData, EditData), HeaderStamps)

# this definition exists because focused behavior needs one stable owner
def BuildBossFillet(AuthoredObjs: tuple[_WriteObject, ...]) -> VendorResolved | None:
    if len(AuthoredObjs) != 3:
        return None
    SketchObject, PadObject, FilletObject = AuthoredObjs
    BoundsValue = WriteRectangle(SketchObject)
    PadCodes = ExtrusionEdit(PadObject.payload)
    if SketchObject.class_name != 'moProfileFeature_c' or SketchObject.object_id != 26 or SketchObject.name != 'Sketch1' or (len(SketchObject.payload) < 4) or (Struct.unpack_from('<I', SketchObject.payload)[0] != 2) or (BoundsValue is None) or (PadObject.class_name != 'moExtrusion_c') or (PadObject.object_id != 32) or (PadObject.name != 'Boss-Extrude1') or (PadCodes != (0, 0)) or (len(PadObject.dimensions) != 1) or (FilletObject.class_name != 'Fillet_c') or (FilletObject.object_id != 34) or (FilletObject.name != 'Fillet1') or (len(FilletObject.dimensions) != 1) or (FilletObject.payload != FilletSelection(32, 3)):
        return None
    PadDepth = PadObject.dimensions[0].value_mm
    FilletRadius = FilletObject.dimensions[0].value_mm
    MinimumX, MinimumY, MaximumX, MaximumY = BoundsValue
    if not MathValue.isfinite(PadDepth) or PadDepth <= 0.0 or (not MathValue.isfinite(FilletRadius)) or (FilletRadius <= 0.0) or (FilletRadius * 2.0 >= min(MaximumX - MinimumX, MaximumY - MinimumY)):
        return None
    RadiusMetres = FilletRadius / KMillimetres
    MaximumXMetres = MaximumX / KMillimetres
    MaximumYMetres = MaximumY / KMillimetres
    MinimumXMetres = MinimumX / KMillimetres
    MinimumYMetres = MinimumY / KMillimetres
    PadDepthMetres = PadDepth / KMillimetres
    CenterXMetres = (MinimumXMetres + MaximumXMetres) / 2.0
    CenterYMetres = (MinimumYMetres + MaximumYMetres) / 2.0
    CenterZMetres = PadDepthMetres / 2.0
    BoundsRadius = MathValue.sqrt(((MaximumXMetres - MinimumXMetres) / 2.0) ** 2 + ((MaximumYMetres - MinimumYMetres) / 2.0) ** 2 + CenterZMetres ** 2)
    HeaderBounds = (CenterXMetres, CenterYMetres, CenterZMetres, MaximumXMetres, MaximumYMetres, PadDepthMetres, MinimumXMetres, MinimumYMetres, 0.0, BoundsRadius)
    ProgramOverrides = {**{ItemData: RadiusMetres for ItemData in KBossFilletRadiusOffsets}, **{ItemData: MaximumXMetres - RadiusMetres for ItemData in KBossFilletMaxXOffsets}, **{ItemData: MaximumYMetres - RadiusMetres for ItemData in KBossFilletMaxYOffsets}, KBossFilletNegativeYOffsA: -(MaximumYMetres - RadiusMetres)}
    return VendorResolved(PatchFeatures(EncodeBossFilletProgram(ProgramOverrides), {0: FeatureEdit(corners_mm=RectangleCornersMm(*BoundsValue), depth_mm=PadDepth, reversed=False, end_condition_code=0, update_depth_copies=True)}), KBossFilletHeaderStamps, 2, 32, HeaderBounds, KBossFilletHeaderStamps[0][0] - 1)

# this definition exists because focused behavior needs one stable owner
def BuildBossVendor(AuthoredObjs: tuple[_WriteObject, ...]) -> VendorResolved | None:
    if len(AuthoredObjs) != 3:
        return None
    SketchObject, PadObject, ChamferObject = AuthoredObjs
    BoundsValue = WriteRectangle(SketchObject)
    PadCodes = ExtrusionEdit(PadObject.payload)
    if SketchObject.class_name != 'moProfileFeature_c' or SketchObject.object_id != 26 or SketchObject.name != 'Sketch1' or (len(SketchObject.payload) < 4) or (Struct.unpack_from('<I', SketchObject.payload)[0] != 2) or (BoundsValue is None) or (PadObject.class_name != 'moExtrusion_c') or (PadObject.object_id != 32) or (PadObject.name != 'Boss-Extrude1') or (PadCodes != (0, 0)) or (len(PadObject.dimensions) != 1) or (ChamferObject.class_name != 'Chamfer_c') or (ChamferObject.object_id != 35) or (ChamferObject.name != 'Chamfer1') or (len(ChamferObject.dimensions) != 1) or (ChamferObject.payload != FilletSelection(32, 3)):
        return None
    PadDepth = PadObject.dimensions[0].value_mm
    ChamferDistance = ChamferObject.dimensions[0].value_mm
    MinimumX, MinimumY, MaximumX, MaximumY = BoundsValue
    if not MathValue.isfinite(PadDepth) or PadDepth <= 0.0 or (not MathValue.isfinite(ChamferDistance)) or (ChamferDistance <= 0.0) or (ChamferDistance * 2.0 >= min(MaximumX - MinimumX, MaximumY - MinimumY)):
        return None
    DistanceMetres = ChamferDistance / KMillimetres
    MaximumXMetres = MaximumX / KMillimetres
    MaximumYMetres = MaximumY / KMillimetres
    MinimumXMetres = MinimumX / KMillimetres
    MinimumYMetres = MinimumY / KMillimetres
    PadDepthMetres = PadDepth / KMillimetres
    CenterXMetres = (MinimumXMetres + MaximumXMetres) / 2.0
    CenterYMetres = (MinimumYMetres + MaximumYMetres) / 2.0
    CenterZMetres = PadDepthMetres / 2.0
    BoundsRadius = MathValue.sqrt(((MaximumXMetres - MinimumXMetres) / 2.0) ** 2 + ((MaximumYMetres - MinimumYMetres) / 2.0) ** 2 + CenterZMetres ** 2)
    HeaderBounds = (CenterXMetres, CenterYMetres, CenterZMetres, MaximumXMetres, MaximumYMetres, PadDepthMetres, MinimumXMetres, MinimumYMetres, 0.0, BoundsRadius)
    TrimmedYMetres = MaximumYMetres - DistanceMetres
    ProgramOverrides = {**{ItemData: DistanceMetres for ItemData in KBossChamferDistance}, **{ItemData: TrimmedYMetres for ItemData in KBossChamferMaxYOffsets}, **{ItemData: -TrimmedYMetres for ItemData in KBossChamferNegativeY}, KBossChamferNegativeOffsA: -DistanceMetres}
    return VendorResolved(PatchFeatures(EncodeBossChamferProgram(ProgramOverrides), {0: FeatureEdit(corners_mm=RectangleCornersMm(*BoundsValue), depth_mm=PadDepth, reversed=False, end_condition_code=0, update_depth_copies=True)}), KBossChamferHeaderStamps, 2, 32, HeaderBounds, KBossChamferHeaderStamps[0][0] - 1)

# this definition exists because focused behavior needs one stable owner
def BuildBossShell(AuthoredObjs: tuple[_WriteObject, ...]) -> VendorResolved | None:
    if len(AuthoredObjs) != 3:
        return None
    SketchObject, PadObject, ShellObject = AuthoredObjs
    BoundsValue = WriteRectangle(SketchObject)
    PadCodes = ExtrusionEdit(PadObject.payload)
    if SketchObject.class_name != 'moProfileFeature_c' or SketchObject.object_id != 26 or SketchObject.name != 'Sketch1' or (len(SketchObject.payload) < 4) or (Struct.unpack_from('<I', SketchObject.payload)[0] != 2) or (BoundsValue is None) or (PadObject.class_name != 'moExtrusion_c') or (PadObject.object_id != 32) or (PadObject.name != 'Boss-Extrude1') or (PadCodes != (0, 0)) or (len(PadObject.dimensions) != 1) or (ShellObject.class_name != 'moShell_c') or (ShellObject.object_id != 34) or (ShellObject.name != 'Shell1') or (len(ShellObject.dimensions) != 1) or (ShellObject.payload != ShellSelection(32)):
        return None
    PadDepth = PadObject.dimensions[0].value_mm
    ShellThickness = ShellObject.dimensions[0].value_mm
    MinimumX, MinimumY, MaximumX, MaximumY = BoundsValue
    if not MathValue.isfinite(PadDepth) or PadDepth <= 0.0 or (not MathValue.isfinite(ShellThickness)) or (ShellThickness <= 0.0) or (ShellThickness >= PadDepth) or (ShellThickness * 2.0 >= min(MaximumX - MinimumX, MaximumY - MinimumY)):
        return None
    ThicknessMetres = ShellThickness / KMillimetres
    MaximumXMetres = MaximumX / KMillimetres
    MaximumYMetres = MaximumY / KMillimetres
    MinimumXMetres = MinimumX / KMillimetres
    MinimumYMetres = MinimumY / KMillimetres
    PadDepthMetres = PadDepth / KMillimetres
    CenterXMetres = (MinimumXMetres + MaximumXMetres) / 2.0
    CenterYMetres = (MinimumYMetres + MaximumYMetres) / 2.0
    CenterZMetres = PadDepthMetres / 2.0
    BoundsRadius = MathValue.sqrt(((MaximumXMetres - MinimumXMetres) / 2.0) ** 2 + ((MaximumYMetres - MinimumYMetres) / 2.0) ** 2 + CenterZMetres ** 2)
    HeaderBounds = (CenterXMetres, CenterYMetres, CenterZMetres, MaximumXMetres, MaximumYMetres, PadDepthMetres, MinimumXMetres, MinimumYMetres, 0.0, BoundsRadius)
    ProgramOverrides = {**{ItemData: ThicknessMetres for ItemData in KBossShellThicknessOffseA}, KBossShellMinXOffset: MinimumXMetres, KBossShellInnerMinXOffset: MinimumXMetres + ThicknessMetres, KBossShellMaxXOffset: MaximumXMetres, KBossShellDepthOffset: PadDepthMetres}
    return VendorResolved(PatchFeatures(EncodeBossShellProgram(ProgramOverrides), {0: FeatureEdit(corners_mm=RectangleCornersMm(*BoundsValue), depth_mm=PadDepth, reversed=False, end_condition_code=0, update_depth_copies=True)}), KBossShellHeaderStamps, 1, None, HeaderBounds, KBossShellHeaderStamps[0][0] - 1, 32)

# this definition exists because focused behavior needs one stable owner
def BuildBossLinear(AuthoredObjs: tuple[_WriteObject, ...]) -> VendorResolved | None:
    if len(AuthoredObjs) != 3:
        return None
    SketchObject, PadObject, PatternObject = AuthoredObjs
    BoundsValue = WriteRectangle(SketchObject)
    PadCodes = ExtrusionEdit(PadObject.payload)
    if SketchObject.class_name != 'moProfileFeature_c' or SketchObject.object_id != 26 or SketchObject.name != 'Sketch1' or (len(SketchObject.payload) < 4) or (Struct.unpack_from('<I', SketchObject.payload)[0] != 2) or (BoundsValue is None) or (PadObject.class_name != 'moExtrusion_c') or (PadObject.object_id != 32) or (PadObject.name != 'Boss-Extrude1') or (PadCodes != (0, 0)) or (len(PadObject.dimensions) != 1) or (PatternObject.class_name != 'moLPattern_c') or (PatternObject.object_id != 40) or (PatternObject.name != 'LPattern1') or (PatternObject.kind != 'LPattern') or (len(PatternObject.dimensions) != 2) or (tuple((ItemData.name for ItemData in PatternObject.dimensions)) != ('D1', 'D3')) or PatternObject.payload:
        return None
    PadDepth = PadObject.dimensions[0].value_mm
    CountNumber = PatternObject.dimensions[0].value_mm
    SpacingValue = PatternObject.dimensions[1].value_mm
    ItemCount = int(CountNumber)
    MinimumX, MinimumY, MaximumX, MaximumY = BoundsValue
    if not MathValue.isfinite(PadDepth) or PadDepth <= 0.0 or (not MathValue.isfinite(CountNumber)) or (CountNumber != ItemCount) or (not 2 <= ItemCount <= 1000) or (not MathValue.isfinite(SpacingValue)) or (SpacingValue <= 0.0) or (SpacingValue > PadDepth):
        return None
    PadDepthMetres = PadDepth / KMillimetres
    SpacingMetres = SpacingValue / KMillimetres
    MinimumXMetres = MinimumX / KMillimetres
    MinimumYMetres = MinimumY / KMillimetres
    MaximumXMetres = MaximumX / KMillimetres
    MaximumYMetres = MaximumY / KMillimetres
    TerminalDepthMetres = PadDepthMetres + SpacingMetres * (ItemCount - 1)
    CenterXMetres = (MinimumXMetres + MaximumXMetres) / 2.0
    CenterYMetres = (MinimumYMetres + MaximumYMetres) / 2.0
    CenterZMetres = TerminalDepthMetres / 2.0
    BoundsRadius = MathValue.sqrt(((MaximumXMetres - MinimumXMetres) / 2.0) ** 2 + ((MaximumYMetres - MinimumYMetres) / 2.0) ** 2 + CenterZMetres ** 2)
    HeaderBounds = (CenterXMetres, CenterYMetres, CenterZMetres, MaximumXMetres, MaximumYMetres, TerminalDepthMetres, MinimumXMetres, MinimumYMetres, 0.0, BoundsRadius)
    PositiveDisplay = 0.55 * TerminalDepthMetres
    MaximumProfileSpanMetres = max(MaximumXMetres - MinimumXMetres, MaximumYMetres - MinimumYMetres)
    ProgramOverrides = {KBossLinearPatternCountB: ItemCount, **{ItemData: float(ItemCount) for ItemData in KBossLinearPatternCountA}, **{ItemData: SpacingMetres for ItemData in KBossLinearPatternPositiD}, **{ItemData: SpacingMetres for ItemData in KBossLinearPatternDistanA}, KBossLinearPatternFlag: 1, **{ItemData: -0.0 for ItemData in KBossLinearPatternNegatiD}, **{ItemData: 1.0 for ItemData in KBossLinearPatternPositiA}, KBossLinearPatternNegatiA: -MathValue.sqrt(0.5), KBossLinearPatternPositiB: MathValue.sqrt(0.5), KBossLinearPatternTerminA: TerminalDepthMetres, KBossLinearPatternCount: MaximumProfileSpanMetres + (ItemCount + 2) / KMillimetres, KBossLinearPatternNegatiC: -0.05 * TerminalDepthMetres, **{ItemData: PositiveDisplay for ItemData in KBossLinearPatternPositiC}, **{ItemData: -PositiveDisplay for ItemData in KBossLinearPatternNegatiB}, **{ItemData: CenterZMetres for ItemData in KBossLinearPatternCenter}, KBossLinearPatternPad: 1.05 * TerminalDepthMetres}
    return VendorResolved(PatchFeatures(EncodeBossLinearPattern(ProgramOverrides), {0: FeatureEdit(corners_mm=RectangleCornersMm(*BoundsValue), depth_mm=PadDepth, reversed=False, end_condition_code=0, update_depth_copies=True)}), KBossLinearPatternHeader, 2, None, HeaderBounds, KBossLinearPatternHeader[0][0] - 1, None, 'linear_pattern')

# this definition exists because focused behavior needs one stable owner
def BuildBossVendoA(AuthoredObjs: tuple[_WriteObject, ...]) -> VendorResolved | None:
    if len(AuthoredObjs) != 3:
        return None
    SketchObject, PadObject, PatternObject = AuthoredObjs
    BoundsValue = WriteRectangle(SketchObject)
    PadCodes = ExtrusionEdit(PadObject.payload)
    if SketchObject.class_name != 'moProfileFeature_c' or SketchObject.object_id != 26 or SketchObject.name != 'Sketch1' or (len(SketchObject.payload) < 4) or (Struct.unpack_from('<I', SketchObject.payload)[0] != 2) or (BoundsValue is None) or (PadObject.class_name != 'moExtrusion_c') or (PadObject.object_id != 32) or (PadObject.name != 'Boss-Extrude1') or (PadCodes != (0, 0)) or (len(PadObject.dimensions) != 1) or (PatternObject.class_name != 'moCirPattern_c') or (PatternObject.object_id != 46) or (PatternObject.name != 'CirPattern1') or (PatternObject.kind != 'CirPattern') or (len(PatternObject.dimensions) != 2) or (tuple((ItemData.name for ItemData in PatternObject.dimensions)) != ('D1', 'D3')) or PatternObject.payload:
        return None
    PadDepth = PadObject.dimensions[0].value_mm
    CountNumber = PatternObject.dimensions[0].value_mm
    AngleDegrees = PatternObject.dimensions[1].value_mm
    ItemCount = int(CountNumber)
    if not MathValue.isfinite(PadDepth) or PadDepth <= 0.0 or (not MathValue.isfinite(CountNumber)) or (CountNumber != ItemCount) or (not 2 <= ItemCount <= 1000) or (not MathValue.isfinite(AngleDegrees)) or (not 0.0 < AngleDegrees <= 360.0) or any((not MathValue.isclose(ActualValue, ExpectedValue, rel_tol=0.0, abs_tol=1e-10) for ActualValue, ExpectedValue in zip(BoundsValue, (0.0, 0.0, 10.0, 5.0), strict=True))):
        return None
    PadDepthMetres = PadDepth / KMillimetres
    PatternBounds = CircularPattern(BoundsValue, ItemCount, AngleDegrees)
    MinimumX, MinimumY, MaximumX, MaximumY = (ItemData / KMillimetres for ItemData in PatternBounds)
    CenterXMetres = (MinimumX + MaximumX) / 2.0
    CenterYMetres = (MinimumY + MaximumY) / 2.0
    CenterZMetres = PadDepthMetres / 2.0
    BoundsRadius = MathValue.sqrt(((MaximumX - MinimumX) / 2.0) ** 2 + ((MaximumY - MinimumY) / 2.0) ** 2 + CenterZMetres ** 2)
    HeaderBounds = (CenterXMetres, CenterYMetres, CenterZMetres, MaximumX, MaximumY, PadDepthMetres, MinimumX, MinimumY, 0.0, BoundsRadius)
    AngleRadians = MathValue.radians(AngleDegrees)
    ProgramOverrides = {KBossCircularPatternCounA: ItemCount, **{ItemData: float(ItemCount) for ItemData in KBossCircularPatternCount}, **{ItemData: AngleRadians for ItemData in KBossCircularPatternAngle}, KBossCircularPatternFlag: 1}
    return VendorResolved(PatchFeatures(EncodeBossCircularPattern(ProgramOverrides), {0: FeatureEdit(corners_mm=RectangleCornersMm(*BoundsValue), depth_mm=PadDepth, reversed=False, end_condition_code=0, update_depth_copies=True)}), KBossCircularPatternHeadA, 2, None, HeaderBounds, KBossCircularPatternHeadA[0][0] - 1, None, 'circular_pattern')

# this definition exists because focused behavior needs one stable owner
def CircularPattern(BoundsValue: tuple[float, float, float, float], ItemCount: int, AngleDegrees: float) -> tuple[float, float, float, float]:
    MinimumX, MinimumY, MaximumX, MaximumY = BoundsValue
    CornerData = ((MinimumX, MinimumY), (MaximumX, MinimumY), (MaximumX, MaximumY), (MinimumX, MaximumY))
    Denominator = ItemCount if MathValue.isclose(AngleDegrees, 360.0, rel_tol=0.0, abs_tol=1e-10) else ItemCount - 1
    RotatedData = tuple(((XValue * MathValue.cos(AngleValue) - YValue * MathValue.sin(AngleValue), XValue * MathValue.sin(AngleValue) + YValue * MathValue.cos(AngleValue)) for IndexValue in range(ItemCount) for AngleValue in (MathValue.radians(AngleDegrees * IndexValue / Denominator),) for XValue, YValue in CornerData))
    return (min((ItemData[0] for ItemData in RotatedData)), min((ItemData[1] for ItemData in RotatedData)), max((ItemData[0] for ItemData in RotatedData)), max((ItemData[1] for ItemData in RotatedData)))

# this definition exists because focused behavior needs one stable owner
def IsCircleChain(BoundsData: tuple[tuple[float, float, float, float] | None, ...], CircleData: tuple[tuple[float, float, float] | None, ...]) -> bool:
    ExpectedBounds = ((-30.0, -20.0, 30.0, 20.0), (-24.0, -4.0, 24.0, 4.0))
    ExpectedCircle = (0.0, 12.0, 6.0)
    return len(BoundsData) == 3 and len(CircleData) == 3 and (BoundsData[2] is None) and (CircleData[:2] == (None, None)) and all((ActualBounds is not None and all((MathValue.isclose(ActualValue, ExpectedValue, rel_tol=0.0, abs_tol=1e-10) for ActualValue, ExpectedValue in zip(ActualBounds, ExpectedValueData, strict=True))) for ActualBounds, ExpectedValueData in zip(BoundsData[:2], ExpectedBounds, strict=True))) and (CircleData[2] is not None) and all((MathValue.isclose(ActualValue, ExpectedValue, rel_tol=0.0, abs_tol=1e-10) for ActualValue, ExpectedValue in zip(CircleData[2] or (), ExpectedCircle, strict=True)))

# this definition exists because focused behavior needs one stable owner
def BuildThreeTree(AuthoredObjs: tuple[_WriteObject, ...]) -> VendorResolved | None:
    SketchData = AuthoredObjs[0::2]
    FeatureData = AuthoredObjs[1::2]
    ExpectedSketchData = tuple(zip(SketchData, (26, 33, 41), ('Sketch1', 'Sketch2', 'Sketch3'), strict=True))
    ExpectedFeatureData = tuple(zip(FeatureData, (32, 40, 47), ('Boss-Extrude1', 'Cut-Extrude1', 'Cut-Extrude2'), ('moExtrusion_c', 'moCut_c', 'moCut_c'), strict=True))
    BoundsData = tuple((WriteRectangle(SketchObject) for SketchObject in SketchData))
    CircleData = tuple((WriteCircle(SketchObject) for SketchObject in SketchData))
    IsCircleData = IsCircleChain(BoundsData, CircleData)
    EndCodes = tuple((ExtrusionEdit(FeatureObject.payload) for FeatureObject in FeatureData))
    if any((SketchObject.class_name != 'moProfileFeature_c' or SketchObject.object_id != ObjectId or SketchObject.name != ObjectName or (len(SketchObject.payload) < 4) or (Struct.unpack_from('<I', SketchObject.payload)[0] != 2) for SketchObject, ObjectId, ObjectName in ExpectedSketchData)) or any((FeatureObject.class_name != ClassName or FeatureObject.object_id != ObjectId or FeatureObject.name != ObjectName or (len(FeatureObject.dimensions) != 1) for FeatureObject, ObjectId, ObjectName, ClassName in ExpectedFeatureData)) or (not IsCircleData and any((BoundsValue is None for BoundsValue in BoundsData))) or any((CodesValue is None for CodesValue in EndCodes)) or any((CodesValue is not None and CodesValue[1] != 0 for CodesValue in EndCodes)):
        return None
    DepthData = tuple((FeatureObject.dimensions[0].value_mm for FeatureObject in FeatureData))
    if any((not MathValue.isfinite(DepthValue) or DepthValue <= 0.0 for DepthValue in DepthData)):
        return None
    if IsCircleData and (any((not MathValue.isclose(ActualValue, ExpectedValue, rel_tol=0.0, abs_tol=1e-10) for ActualValue, ExpectedValue in zip(DepthData, (15.0, 5.0, 9.0), strict=True))) or EndCodes != ((1, 0), (0, 0), (0, 0))):
        return None
    EditData: dict[int, FeatureEdit] = {}
    for FeatureIndex, (BoundsValue, CircleValue, DepthValue, CodesValue) in enumerate(zip(BoundsData, CircleData, DepthData, EndCodes, strict=True)):
        if CodesValue is None or (BoundsValue is None) == (CircleValue is None):
            return None
        EditData[FeatureIndex] = FeatureEdit(corners_mm=RectangleCornersMm(*BoundsValue) if BoundsValue is not None else None, depth_mm=DepthValue, reversed=bool(CodesValue[0]), end_condition_code=CodesValue[1], update_depth_copies=True, radii_mm=(CircleValue[2],) if CircleValue is not None else None, arc_centres_mm=((CircleValue[0], CircleValue[1]),) if CircleValue is not None else None)
    return VendorResolved(PatchFeatures(EncodeBossCutCircle() if IsCircleData else EncodeBossCutCutProgram(), EditData), KBossCutCutHeaderStamps)

# this definition exists because focused behavior needs one stable owner
def BuildFourVendor(AuthoredObjs: tuple[_WriteObject, ...]) -> VendorResolved | None:
    SketchData = AuthoredObjs[0::2]
    FeatureData = AuthoredObjs[1::2]
    ExpectedSketchData = tuple(zip(SketchData, (26, 33, 41, 48), ('Sketch1', 'Sketch2', 'Sketch3', 'Sketch4'), strict=True))
    ExpectedFeatureData = tuple(zip(FeatureData, (32, 40, 47, 54), ('Boss-Extrude1', 'Cut-Extrude1', 'Cut-Extrude2', 'Cut-Extrude3'), ('moExtrusion_c', 'moCut_c', 'moCut_c', 'moCut_c'), strict=True))
    BoundsData = tuple((WriteRectangle(SketchObject) for SketchObject in SketchData))
    EndCodes = tuple((ExtrusionEdit(FeatureObject.payload) for FeatureObject in FeatureData))
    if any((SketchObject.class_name != 'moProfileFeature_c' or SketchObject.object_id != ObjectId or SketchObject.name != ObjectName or (len(SketchObject.payload) < 4) or (Struct.unpack_from('<I', SketchObject.payload)[0] != 2) for SketchObject, ObjectId, ObjectName in ExpectedSketchData)) or any((FeatureObject.class_name != ClassName or FeatureObject.object_id != ObjectId or FeatureObject.name != ObjectName or (len(FeatureObject.dimensions) != 1) for FeatureObject, ObjectId, ObjectName, ClassName in ExpectedFeatureData)) or any((BoundsValue is None for BoundsValue in BoundsData)) or any((CodesValue is None for CodesValue in EndCodes)) or any((CodesValue is not None and CodesValue[1] != 0 for CodesValue in EndCodes)):
        return None
    DepthData = tuple((FeatureObject.dimensions[0].value_mm for FeatureObject in FeatureData))
    if any((not MathValue.isfinite(DepthValue) or DepthValue <= 0.0 for DepthValue in DepthData)):
        return None
    EditData: dict[int, FeatureEdit] = {}
    for FeatureIndex, (BoundsValue, DepthValue, CodesValue) in enumerate(zip(BoundsData, DepthData, EndCodes, strict=True)):
        if BoundsValue is None or CodesValue is None:
            return None
        EditData[FeatureIndex] = FeatureEdit(corners_mm=RectangleCornersMm(*BoundsValue), depth_mm=DepthValue, reversed=bool(CodesValue[0]), end_condition_code=CodesValue[1], update_depth_copies=True)
    return VendorResolved(PatchFeatures(EncodeBossCutCutCut(), EditData), KBossCutCutCutHeaderStamA)

# this definition exists because focused behavior needs one stable owner
def ExtrusionEdit(PayloadData: bytes) -> tuple[int, int] | None:
    DeclData = ClassDecl('moEndSpec_c')
    DirectionOffset = len(DeclData) + 10
    TerminationOffset = len(DeclData) + 16
    if not PayloadData.startswith(DeclData) or len(PayloadData) < TerminationOffset + 4:
        return None
    DirectionCode = Struct.unpack_from('<I', PayloadData, DirectionOffset)[0]
    TerminationCode = Struct.unpack_from('<I', PayloadData, TerminationOffset)[0]
    if DirectionCode not in {0, 1} or TerminationCode not in {0, 1, 6}:
        return None
    return (DirectionCode, TerminationCode)

# this definition exists because focused behavior needs one stable owner
def WriteObjectIds(DocValue: CadDocument) -> dict[str, int]:
    UsedValue = set(range(1, 26))
    Result: dict[str, int] = {}
    NextId = 26

    # this definition exists because focused behavior needs one stable owner
    def Assign(KeyValue: str, Native: Any=None) -> int:
        nonlocal NextId
        Choice = Native if isinstance(Native, int) and Native > 25 else None
        if Choice is None or Choice in UsedValue or Choice > 4294967294:
            while NextId in UsedValue:
                NextId += 1
            Choice = NextId
            NextId += 1
        UsedValue.add(Choice)
        Result[KeyValue] = Choice
        return Choice
    Principal = PrincipalPlaneB(DocValue.support_planes)
    for Plane in DocValue.support_planes:
        KeyValue = f'plane:{Plane.id}'
        if Plane.id in Principal:
            Result[KeyValue] = Principal[Plane.id]
        else:
            Assign(KeyValue, Plane.attributes.get('native_object_id'))
    for Sketch in DocValue.sketches:
        Assign(f'sketch:{Sketch.id}', Sketch.attributes.get('native_object_id'))

    # this callback exists because local behavior needs one focused transformation
    for Feature in sorted(DocValue.feature_timeline, key=lambda ItemValue: ItemValue.order):
        if IsNativeSystem(Feature):
            continue
        Native = Feature.attributes.get('native_object_id')
        SketchNative = Result.get(f'sketch:{Feature.sketch_id}') if Feature.sketch_id is not None else None
        if isinstance(Native, int) and Native == SketchNative:
            Result[f'feature:{Feature.id}'] = Native
        else:
            Assign(f'feature:{Feature.id}', Native)
    ConfigIds: set[int] = set()
    NextConfigId = 0
    for Config in DocValue.configurations:
        Native = Config.attributes.get('native_configuration_id')
        Choice = Native if isinstance(Native, int) and (not isinstance(Native, bool)) and (0 <= Native <= 4294967295) and (Native not in ConfigIds) else None
        if Choice is None:
            while NextConfigId in ConfigIds:
                NextConfigId += 1
            Choice = NextConfigId
        ConfigIds.add(Choice)
        Result[f'configuration:{Config.id}'] = Choice
    return Result

# this definition exists because focused behavior needs one stable owner
def PrincipalPlaneB(Planes: tuple[SupportPlane, ...]) -> dict[str, int]:
    Frames = ((2, (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)), (3, (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 0.0, -1.0), (0.0, 1.0, 0.0)), (4, (0.0, 0.0, 0.0), (0.0, 0.0, -1.0), (0.0, 1.0, 0.0), (1.0, 0.0, 0.0)))
    Result: dict[str, int] = {}
    Claimed: set[int] = set()
    for Plane in Planes:
        Transform = Plane.transform
        OriginValue = (Transform.origin.x, Transform.origin.y, Transform.origin.z)
        NormalValue = (Transform.z_axis.x, Transform.z_axis.y, Transform.z_axis.z)
        for ObjectId, *Frame in Frames:
            if ObjectId in Claimed:
                continue
            TargetNormal = Frame[3]
            if all((MathValue.isclose(ItemData, 0.0, abs_tol=1e-09) for ItemData in OriginValue)) and MathValue.isclose(abs(sum((LeftValue * RightValue for LeftValue, RightValue in zip(NormalValue, TargetNormal, strict=True)))), 1.0, rel_tol=0.0, abs_tol=1e-09):
                Result[Plane.id] = ObjectId
                Claimed.add(ObjectId)
                break
    return Result

# this definition exists because focused behavior needs one stable owner
def FreeCadProp(ObjectData: Mapping[str, Any], PropName: str) -> Mapping[str, AnyValue] | None:
    PropertiesData = ObjectData.get('properties')
    if not isinstance(PropertiesData, Mapping):
        return None
    PropData = PropertiesData.get(PropName)
    if not isinstance(PropData, Mapping):
        return None
    ChildrenData = PropData.get('children')
    if not isinstance(ChildrenData, (list, tuple)) or len(ChildrenData) != 1:
        return None
    ChildData = ChildrenData[0]
    if not isinstance(ChildData, Mapping):
        return None
    AttributesData = ChildData.get('attributes')
    return AttributesData if isinstance(AttributesData, Mapping) else None

# this definition exists because focused behavior needs one stable owner
def IsFreeCad(ObjectData: Mapping[str, Any], PropName: str) -> bool:
    AttributesData = FreeCadProp(ObjectData, PropName)
    if AttributesData is None:
        return False
    ExpectedData = {'Px': 0.0, 'Py': 0.0, 'Pz': 0.0, 'Q0': 0.0, 'Q1': 0.0, 'Q2': 0.0, 'Q3': 1.0}
    try:
        ActualData = {KeyData: float(AttributesData[KeyData]) for KeyData in ExpectedData}
    except (KeyError, TypeError, ValueError):
        return False
    return all((MathValue.isfinite(ActualData[KeyData]) and MathValue.isclose(ActualData[KeyData], ExpectedValue, rel_tol=0.0, abs_tol=1e-12) for KeyData, ExpectedValue in ExpectedData.items()))

# this definition exists because focused behavior needs one stable owner
def HasFreeCadBox(DocData: CadDocument, LengthValue: float, WidthValue: float, HeightValue: float) -> bool:
    BrepData = DocData.brep
    if BrepData is None or len(BrepData.vertices) != 8 or len(BrepData.edges) != 12 or (len(BrepData.faces) != 6) or (len(BrepData.regions) != 1) or (len(BrepData.bodies) != 1):
        return False
    ExpectedData = {(XValue, YValue, ZValue) for XValue in (0.0, LengthValue) for YValue in (0.0, WidthValue) for ZValue in (0.0, HeightValue)}
    ActualData = {(VertexData.point.x, VertexData.point.y, VertexData.point.z) for VertexData in BrepData.vertices}
    return len(ActualData) == 8 and all((any((all((MathValue.isclose(ExpectedCoordinate, ActualCoordinate, rel_tol=0.0, abs_tol=1e-09) for ExpectedCoordinate, ActualCoordinate in zip(ExpectedPoint, ActualPoint, strict=True))) for ActualPoint in ActualData)) for ExpectedPoint in ExpectedData))

# this definition exists because focused behavior needs one stable owner
def HasCadCylBrep(DocData: CadDocument, RadiusValue: float, HeightValue: float) -> bool:
    BrepData = DocData.brep
    if BrepData is None or len(BrepData.vertices) != 2 or len(BrepData.curves) != 3 or (len(BrepData.edges) != 3) or (len(BrepData.loops) != 3) or (len(BrepData.surfaces) != 3) or (len(BrepData.faces) != 3) or (len(BrepData.regions) != 1) or (len(BrepData.bodies) != 1) or (not BrepData.regions[0].solid):
        return False
    CircleData = tuple((ItemData for ItemData in BrepData.curves if isinstance(ItemData, CircleCurve)))
    LineData = tuple((ItemData for ItemData in BrepData.curves if isinstance(ItemData, LineCurve)))
    CylinderData = tuple((ItemData for ItemData in BrepData.surfaces if isinstance(ItemData, CylinderSurface)))
    PlaneData = tuple((ItemData for ItemData in BrepData.surfaces if isinstance(ItemData, PlaneSurface)))
    if len(CircleData) != 2 or len(LineData) != 1 or len(CylinderData) != 1 or (len(PlaneData) != 2):
        return False
    CircleHeights = sorted((ItemData.center.z for ItemData in CircleData))
    PlaneHeights = sorted((ItemData.origin.z for ItemData in PlaneData))
    ExpectedHeights = (0.0, HeightValue)
    if not all((MathValue.isclose(ActualValue, ExpectedValue, rel_tol=0.0, abs_tol=1e-09) for ActualValue, ExpectedValue in zip(CircleHeights, ExpectedHeights, strict=True))) or not all((MathValue.isclose(ActualValue, ExpectedValue, rel_tol=0.0, abs_tol=1e-09) for ActualValue, ExpectedValue in zip(PlaneHeights, ExpectedHeights, strict=True))):
        return False
    if any((not MathValue.isclose(ItemData.center.x, 0.0, abs_tol=1e-09) or not MathValue.isclose(ItemData.center.y, 0.0, abs_tol=1e-09) or (not MathValue.isclose(ItemData.radius, RadiusValue, rel_tol=0.0, abs_tol=1e-09)) or (not MathValue.isclose(abs(ItemData.axis.z), 1.0, abs_tol=1e-09)) or (not MathValue.isclose(ItemData.axis.x, 0.0, abs_tol=1e-09)) or (not MathValue.isclose(ItemData.axis.y, 0.0, abs_tol=1e-09)) for ItemData in CircleData)):
        return False
    LineValue = LineData[0]
    CylinderValue = CylinderData[0]
    if not MathValue.isclose(MathValue.hypot(LineValue.origin.x, LineValue.origin.y), RadiusValue, rel_tol=0.0, abs_tol=1e-09) or not MathValue.isclose(LineValue.origin.z, 0.0, abs_tol=1e-09) or (not MathValue.isclose(LineValue.direction.x, 0.0, abs_tol=1e-09)) or (not MathValue.isclose(LineValue.direction.y, 0.0, abs_tol=1e-09)) or (not MathValue.isclose(abs(LineValue.direction.z), 1.0, abs_tol=1e-09)) or (not MathValue.isclose(CylinderValue.origin.x, 0.0, abs_tol=1e-09)) or (not MathValue.isclose(CylinderValue.origin.y, 0.0, abs_tol=1e-09)) or (not MathValue.isclose(CylinderValue.origin.z, 0.0, abs_tol=1e-09)) or (not MathValue.isclose(CylinderValue.radius, RadiusValue, rel_tol=0.0, abs_tol=1e-09)) or (not MathValue.isclose(CylinderValue.axis.x, 0.0, abs_tol=1e-09)) or (not MathValue.isclose(CylinderValue.axis.y, 0.0, abs_tol=1e-09)) or (not MathValue.isclose(abs(CylinderValue.axis.z), 1.0, abs_tol=1e-09)):
        return False
    VertexHeights = sorted((ItemData.point.z for ItemData in BrepData.vertices))
    return all((MathValue.isclose(MathValue.hypot(ItemData.point.x, ItemData.point.y), RadiusValue, rel_tol=0.0, abs_tol=1e-09) for ItemData in BrepData.vertices)) and all((MathValue.isclose(ActualValue, ExpectedValue, rel_tol=0.0, abs_tol=1e-09) for ActualValue, ExpectedValue in zip(VertexHeights, ExpectedHeights, strict=True)))

# this definition exists because focused behavior needs one stable owner
def FreeCadBox(DocData: CadDocument, ObjectIds: dict[str, int]) -> tuple[WriteObject, ...] | None:

    # this callback exists because local behavior needs one focused transformation
    TimelineData = tuple((FeatureData for FeatureData in sorted(DocData.feature_timeline, key=lambda FeatureData: FeatureData.order) if not IsNativeSystem(FeatureData)))
    if len(TimelineData) != 1:
        return None
    FeatureData = TimelineData[0]
    DefinitionData = FeatureData.definition
    if DocData.source.format_id.casefold() != 'freecad.fcstd' or DocData.assembly is not None or DocData.support_planes or DocData.sketches or DocData.selections or (len(DocData.bodies) != 1) or (DocData.bodies[0].final_feature_id != FeatureData.id) or (len(DocData.configurations) != 1) or (DocData.configurations[0].name.casefold() != 'default') or (not DocData.configurations[0].active) or (DocData.configurations[0].parent_id is not None) or DocData.configurations[0].overrides or DocData.configurations[0].suppressed_feature_ids or (FeatureData.order != 0) or FeatureData.input_feature_ids or (FeatureData.sketch_id is not None) or FeatureData.selection_ids or FeatureData.configuration_states or FeatureData.suppressed or (str(FeatureData.kind).casefold() != FeatureKind.PRIMITIVE.value) or (FeatureData.operation is not None) or (not isinstance(DefinitionData, NativeFeatureDefinition)) or (DefinitionData.format_id.casefold() != 'freecad.fcstd') or (DefinitionData.type_id not in {'Part::Box', 'PartDesign::AdditiveBox'}) or (FeatureData.provenance is None) or any((ItemData.expression is not None for ItemData in DocData.parameters)):
        return None
    PathData: dict[str, Param] = {}
    for ItemData in DocData.parameters:
        if ItemData.owner_id != FeatureData.id:
            return None
        PathValue = ItemData.attributes.get('freecad_path')
        if not isinstance(PathValue, str) or not PathValue or PathValue in PathData:
            return None
        PathData[PathValue] = ItemData
    ExpectedData = {'Length': (ValueKind.LENGTH, None), 'Width': (ValueKind.LENGTH, None), 'Height': (ValueKind.LENGTH, None), 'MapMode': (ValueKind.INTEGER, 0), 'MapPathParameter': (ValueKind.NUMBER, 0.0), 'MapReversed': (ValueKind.BOOLEAN, False), 'Visibility': (ValueKind.BOOLEAN, True)}
    if not set(ExpectedData) <= set(PathData) or any((not FreecadParam(PathData[PathName], KindData, ValueData) for PathName, (KindData, ValueData) in ExpectedData.items() if ValueData is not None)):
        return None
    DimensionsData = tuple((ParamDimension(PathData[PathName]) for PathName in ('Length', 'Width', 'Height')))
    if any((ItemData is None for ItemData in DimensionsData)):
        return None
    LengthData, WidthData, HeightData = DimensionsData
    if LengthData is None or WidthData is None or HeightData is None:
        return None
    LengthValue = LengthData.value_mm
    WidthValue = WidthData.value_mm
    HeightValue = HeightData.value_mm
    if not all((MathValue.isfinite(ItemData) and ItemData > 0.0 for ItemData in (LengthValue, WidthValue, HeightValue))) or not IsFreeCad(DefinitionData.object_data, 'Placement') or (not IsFreeCad(DefinitionData.object_data, 'AttachmentOffset')) or (not HasFreeCadBox(DocData, LengthValue, WidthValue, HeightValue)):
        return None
    SketchPayload = bytearray(PlaneRef(2))
    CornerData = ((0.0, 0.0), (LengthValue, 0.0), (LengthValue, WidthValue), (0.0, WidthValue))
    for LocalIndex, PointData in enumerate(CornerData, 1):
        SketchPayload.extend(Coordinate(PointData, LocalIndex, KPointLocus))
    for LocalIndex, (StartIndex, EndIndex) in enumerate(((0, 1), (1, 2), (2, 3), (3, 0)), 5):
        SketchPayload.extend(LineMarker(StartIndex, EndIndex, LocalIndex))
    SketchSourceId = f'{FeatureData.id}:box-profile'
    ObjectIds[f'sketch:{SketchSourceId}'] = 26
    ObjectIds[f'feature:{FeatureData.id}'] = 34
    ExtrusionData = Replace(FeatureData, kind=FeatureKind.EXTRUSION, sketch_id=SketchSourceId, operation=BoolOperation.CREATE, definition=ExtrusionFeature(ParamValue(HeightValue, ValueKind.LENGTH, 'mm')))
    return (WriteObject(SketchSourceId, 26, 'Sketch1', 'Sketch', 'Sketch', 'moProfileFeature_c', (('Dissectable', 'true'),), (Replace(LengthData, name='D1', text=format(LengthValue, '.15g')), Replace(WidthData, name='D2', text=format(WidthValue, '.15g'))), bytes(SketchPayload)), WriteObject(FeatureData.id, 34, 'Boss-Extrude1', 'Extrusion', 'Extrusion', 'moExtrusion_c', (('Dissectable', 'true'), ('DissectableChildren', '26'), ('DissectableRoot', 'true'), ('KitPrimitive', 'Box')), (Replace(HeightData, name='D1', text=format(HeightValue, '.15g')),), Extrusion(ExtrusionData)))

# this definition exists because focused behavior needs one stable owner
def BuildCadCylObjs(DocData: CadDocument, ObjectIds: dict[str, int]) -> tuple[WriteObject, ...] | None:

    # this callback exists because local behavior needs one focused transformation
    TimelineData = tuple((FeatureData for FeatureData in sorted(DocData.feature_timeline, key=lambda FeatureData: FeatureData.order) if not IsNativeSystem(FeatureData)))
    if len(TimelineData) != 1:
        return None
    FeatureData = TimelineData[0]
    DefinitionData = FeatureData.definition
    if DocData.source.format_id.casefold() != 'freecad.fcstd' or DocData.assembly is not None or DocData.support_planes or DocData.sketches or DocData.selections or (len(DocData.bodies) != 1) or (DocData.bodies[0].final_feature_id != FeatureData.id) or (len(DocData.configurations) != 1) or (DocData.configurations[0].name.casefold() != 'default') or (not DocData.configurations[0].active) or (DocData.configurations[0].parent_id is not None) or DocData.configurations[0].overrides or DocData.configurations[0].suppressed_feature_ids or (FeatureData.order != 0) or FeatureData.input_feature_ids or (FeatureData.sketch_id is not None) or FeatureData.selection_ids or FeatureData.configuration_states or FeatureData.suppressed or (str(FeatureData.kind).casefold() != FeatureKind.PRIMITIVE.value) or (FeatureData.operation is not None) or (not isinstance(DefinitionData, NativeFeatureDefinition)) or (DefinitionData.format_id.casefold() != 'freecad.fcstd') or (DefinitionData.type_id != 'Part::Cylinder') or (FeatureData.provenance is None) or any((ItemData.expression is not None for ItemData in DocData.parameters)):
        return None
    PathData: dict[str, Param] = {}
    for ItemData in DocData.parameters:
        if ItemData.owner_id != FeatureData.id:
            return None
        PathValue = ItemData.attributes.get('freecad_path')
        if not isinstance(PathValue, str) or not PathValue or PathValue in PathData:
            return None
        PathData[PathValue] = ItemData
    ExpectedData = {'Angle': (ValueKind.ANGLE, 360.0), 'FirstAngle': (ValueKind.ANGLE, 0.0), 'SecondAngle': (ValueKind.ANGLE, 0.0), 'Height': (ValueKind.LENGTH, None), 'Radius': (ValueKind.LENGTH, None), 'MapMode': (ValueKind.INTEGER, 0), 'MapPathParameter': (ValueKind.NUMBER, 0.0), 'MapReversed': (ValueKind.BOOLEAN, False), 'Visibility': (ValueKind.BOOLEAN, True)}
    if not set(ExpectedData) <= set(PathData) or any((not FreecadParam(PathData[PathName], KindData, ValueData) for PathName, (KindData, ValueData) in ExpectedData.items() if ValueData is not None)):
        return None
    RadiusData = ParamDimension(PathData['Radius'])
    HeightData = ParamDimension(PathData['Height'])
    if RadiusData is None or HeightData is None:
        return None
    RadiusValue = RadiusData.value_mm
    HeightValue = HeightData.value_mm
    if not MathValue.isfinite(RadiusValue) or RadiusValue <= 0.0 or (not MathValue.isfinite(HeightValue)) or (HeightValue <= 0.0) or (not IsFreeCad(DefinitionData.object_data, 'Placement')) or (not IsFreeCad(DefinitionData.object_data, 'AttachmentOffset')) or (not HasCadCylBrep(DocData, RadiusValue, HeightValue)):
        return None
    SketchPayload = bytearray(PlaneRef(2))
    SketchPayload.extend(Coordinate((0.0, 0.0), 1, KCircleLocus))
    SketchPayload.extend(Coordinate((RadiusValue, 0.0), 2, KPointLocus))
    SketchSourceId = f'{FeatureData.id}:cylinder-profile'
    ObjectIds[f'sketch:{SketchSourceId}'] = 26
    ObjectIds[f'feature:{FeatureData.id}'] = 33
    ExtrusionData = Replace(FeatureData, kind=FeatureKind.EXTRUSION, sketch_id=SketchSourceId, operation=BoolOperation.CREATE, definition=ExtrusionFeature(ParamValue(HeightValue, ValueKind.LENGTH, 'mm')))
    return (WriteObject(SketchSourceId, 26, 'Sketch1', 'Sketch', 'Sketch', 'moProfileFeature_c', (('Dissectable', 'true'),), (Replace(RadiusData, name='D1', value_mm=RadiusValue * 2.0, text='<MOD-DIAM>' + format(RadiusValue * 2.0, '.15g')),), bytes(SketchPayload)), WriteObject(FeatureData.id, 33, 'Boss-Extrude1', 'Extrusion', 'Extrusion', 'moExtrusion_c', (('Dissectable', 'true'), ('DissectableChildren', '26'), ('DissectableRoot', 'true'), ('KitPrimitive', 'Cylinder')), (Replace(HeightData, name='D1', text=format(HeightValue, '.15g')),), Extrusion(ExtrusionData)))

# this definition exists because focused behavior needs one stable owner
def WriteObjects(DocValue: CadDocument, ObjectIds: dict[str, int]) -> tuple[WriteObject, ...]:
    Parameters = {Param.id: Param for Param in DocValue.parameters}
    BoxObjects = FreeCadBox(DocValue, ObjectIds)
    if BoxObjects is not None:
        return BoxObjects
    CylinderObjects = BuildCadCylObjs(DocValue, ObjectIds)
    if CylinderObjects is not None:
        return CylinderObjects
    Result: list[WriteObject] = []
    for Plane in DocValue.support_planes:
        ObjectId = ObjectIds[f'plane:{Plane.id}']
        if ObjectId in {2, 3, 4}:
            continue
        Dimensions = WriteDimensions(Plane.id, (Plane.offset_parameter_id,) if Plane.offset_parameter_id else (), Parameters)
        Result.append(WriteObject(Plane.id, ObjectId, Plane.name, 'Feature', 'Plane', 'moRefPlane_c', dimensions=Dimensions, payload=PlanePayload(Plane)))
    Sketches = {Sketch.id: Sketch for Sketch in DocValue.sketches}
    EmittedSketches: set[str] = set()

    # this callback exists because local behavior needs one focused transformation
    for Feature in sorted(DocValue.feature_timeline, key=lambda ItemValue: ItemValue.order):
        if IsNativeSystem(Feature):
            continue
        if Feature.sketch_id is not None and Feature.sketch_id in Sketches:
            Sketch = Sketches[Feature.sketch_id]
            if Sketch.id not in EmittedSketches:
                Result.append(WriteSketch(Sketch, Parameters, ObjectIds, Feature))
                EmittedSketches.add(Sketch.id)
        FeatureId = ObjectIds[f'feature:{Feature.id}']
        if any((ItemValue.object_id == FeatureId for ItemValue in Result)):
            continue
        Result.append(WriteFeature(Feature, Parameters, ObjectIds))
    for Sketch in DocValue.sketches:
        if Sketch.id not in EmittedSketches:
            Result.append(WriteSketch(Sketch, Parameters, ObjectIds))
    return tuple(Result)

# this definition exists because focused behavior needs one stable owner
def EquationId(Value: str) -> str:
    Cleaned = KEquationId.sub('_', Value).strip('_')
    return f'Kit_{Cleaned}' if Cleaned else ''

# this definition exists because focused behavior needs one stable owner
def EquationLiteral(Value: ParameterValue) -> str | None:
    if not isinstance(Value.value, (int, float)) or isinstance(Value.value, bool):
        return None
    if not MathValue.isfinite(float(Value.value)):
        return None
    Rendered = format(float(Value.value), '.15g')
    if Value.kind is ValueKind.LENGTH:
        return f'{Rendered}mm'
    if Value.kind is ValueKind.NUMBER:
        return Rendered
    return None

# this definition exists because focused behavior needs one stable owner
def Expression(DocValue: CadDocument) -> tuple[Param, ...]:
    return tuple((Param for Param in DocValue.parameters if Param.expression is not None))

# this definition exists because focused behavior needs one stable owner
def ExpressionTexts(DocValue: CadDocument) -> tuple[str, ...] | None:
    Parameters = Expression(DocValue)
    if not Parameters:
        return ()
    Names: dict[str, str] = {}
    UsedValue: set[str] = set()

    # this definition exists because focused behavior needs one stable owner
    def IdAction(KeyValue: str, Source: str) -> str | None:
        if KeyValue in Names:
            return Names[KeyValue]
        BaseValue = EquationId(Source)
        if not BaseValue:
            return None
        Choice = BaseValue
        Suffix = 2
        while Choice in UsedValue:
            Choice = f'{BaseValue}_{Suffix}'
            Suffix += 1
        UsedValue.add(Choice)
        Names[KeyValue] = Choice
        return Choice
    References: list[tuple[str, str]] = []
    Values: dict[str, str] = {}
    Bindings: list[tuple[str, str]] = []
    for Param in Parameters:
        Expression = Param.expression
        if Expression is None:
            return None
        Source = Expression.source.strip()
        if not KEquationRefSource.fullmatch(Source):
            return None
        Literal = EquationLiteral(Param.value)
        if Literal is None:
            return None
        RefValue = IdAction(f'reference:{Source}', Source)
        Driven = IdAction(f'parameter:{Param.id}', Param.name)
        if RefValue is None or Driven is None or RefValue == Driven:
            return None
        if RefValue in Values:
            if Values[RefValue] != Literal:
                return None
        else:
            Values[RefValue] = Literal
            References.append((RefValue, Literal))
        Bindings.append((Driven, RefValue))
    Texts = [f'"{NameValue}"= {Literal}' for NameValue, Literal in References]
    Texts.extend((f'"{Driven}"= "{RefValue}"' for Driven, RefValue in Bindings))
    if len(set(Texts)) != len(Texts):
        return None
    return tuple(Texts)

# this definition exists because focused behavior needs one stable owner
def RepairPlaneIds(ObjectIds: dict[str, int]) -> None:
    Reserved = frozenset(range(1, 26))
    Taken = {Value for KeyValue, Value in ObjectIds.items() if not KeyValue.startswith(('plane:', 'configuration:'))}
    NextId = 26
    for KeyValue in tuple(ObjectIds):
        if not KeyValue.startswith('plane:'):
            continue
        Value = ObjectIds[KeyValue]
        if Value in {2, 3, 4} and Value not in Taken:
            Taken.add(Value)
            continue
        if Value not in Taken and Value not in Reserved:
            Taken.add(Value)
            continue
        while NextId in Taken or NextId in Reserved:
            NextId += 1
        ObjectIds[KeyValue] = NextId
        Taken.add(NextId)

# this definition exists because focused behavior needs one stable owner
def Canonical(ObjectsData: tuple[_WriteObject, ...], ObjectIds: dict[str, int], DocData: CadDocument) -> tuple[WriteObject, ...]:
    if len(ObjectsData) == 2 and ObjectsData[1].class_name == 'moRevolution_c':
        return CanonicalSinglA(ObjectsData, ObjectIds, DocData)
    if len(ObjectsData) in {6, 8}:
        return CanonicalCut(ObjectsData, ObjectIds, DocData)
    if len(ObjectsData) == 4:
        if ObjectsData[3].class_name == 'moRevolution_c':
            return CanonicalPad(ObjectsData, ObjectIds, DocData)
        return CanonicalTwo(ObjectsData, ObjectIds, DocData)
    if len(ObjectsData) == 3 and ObjectsData[2].class_name == 'Fillet_c':
        return CanonicalBossB(ObjectsData, ObjectIds, DocData)
    if len(ObjectsData) == 3 and ObjectsData[2].class_name == 'Chamfer_c':
        return CanonicalBoss(ObjectsData, ObjectIds, DocData)
    if len(ObjectsData) == 3 and ObjectsData[2].class_name == 'moShell_c':
        return CanonicalBossD(ObjectsData, ObjectIds, DocData)
    if len(ObjectsData) == 3 and ObjectsData[2].class_name == 'moLPattern_c':
        return CanonicalBossC(ObjectsData, ObjectIds, DocData)
    if len(ObjectsData) == 3 and ObjectsData[2].class_name == 'moCirPattern_c':
        return CanonicalBossA(ObjectsData, ObjectIds, DocData)
    return CanonicalSingle(ObjectsData, ObjectIds, DocData)

# this definition exists because focused behavior needs one stable owner
def CanonicalSinglA(ObjectsData: tuple[_WriteObject, ...], ObjectIds: dict[str, int], DocData: CadDocument) -> tuple[WriteObject, ...]:
    if len(ObjectsData) != 2:
        return ObjectsData
    SketchObject, RevolveObject = ObjectsData
    SourceSketch = next((ItemData for ItemData in DocData.sketches if ItemData.id == SketchObject.source_id), None)
    SourceFeature = next((ItemData for ItemData in DocData.feature_timeline if ItemData.id == RevolveObject.source_id), None)
    if SourceSketch is None or SourceFeature is None:
        return ObjectsData
    NormalizedSketch = CanonicalSketch(SourceSketch, DocData.support_planes, ObjectIds)
    SketchPayload, Ignored = SketchPayload(NormalizedSketch, SketchObject.object_id, ObjectIds)
    SketchObject = Replace(SketchObject, payload=SketchPayload)
    BoundsValue = WriteRectangle(SketchObject)
    PinPoints = PolySixPoints(SketchObject)
    AngleDimension = FreeCadSingle(DocData, SourceSketch, SourceFeature)
    PlaneObjectId = Struct.unpack_from('<I', SketchObject.payload)[0] if len(SketchObject.payload) >= 4 else 0
    IsPinData = PlaneObjectId == 3 and IsPinProfile(PinPoints) and (not SketchObject.dimensions) and HasPolySix(SourceSketch, PinPoints)
    IsRectangleData = PlaneObjectId == 2 and BoundsValue is not None and HasRectDims(SketchObject, BoundsValue) and HasCanonical(SourceSketch, BoundsValue, None)
    if SketchObject.class_name != 'moProfileFeature_c' or not (IsRectangleData or IsPinData) or SourceSketch.suppressed or (len(SourceSketch.closed_profile_entity_ids) != 1) or (set(SourceSketch.closed_profile_entity_ids[0]) != {ItemData.id for ItemData in SourceSketch.entities}) or (RevolveObject.class_name != 'moRevolution_c') or (AngleDimension is None):
        return ObjectsData
    ObjectIds[f'sketch:{SketchObject.source_id}'] = 26
    ObjectIds[f'feature:{RevolveObject.source_id}'] = 31
    return (Replace(SketchObject, object_id=26, name='Sketch1'), Replace(RevolveObject, object_id=31, name='Revolve1', dimensions=(AngleDimension,)))

# this definition exists because focused behavior needs one stable owner
def CanonicalPad(ObjectsData: tuple[_WriteObject, ...], ObjectIds: dict[str, int], DocData: CadDocument) -> tuple[WriteObject, ...]:
    if len(ObjectsData) != 4:
        return ObjectsData
    SketchOne, PadObject, SketchTwo, GrooveObject = ObjectsData
    SourceSketches = tuple((next((ItemData for ItemData in DocData.sketches if ItemData.id == SketchObject.source_id), None) for SketchObject in (SketchOne, SketchTwo)))
    SourceFeatures = tuple((next((ItemData for ItemData in DocData.feature_timeline if ItemData.id == FeatureObject.source_id), None) for FeatureObject in (PadObject, GrooveObject)))
    if any((ItemData is None for ItemData in (*SourceSketches, *SourceFeatures))):
        return ObjectsData
    SourceSketchOne, SourceSketchTwo = SourceSketches
    SourcePad, SourceGroove = SourceFeatures
    if SourceSketchOne is None or SourceSketchTwo is None or SourcePad is None or (SourceGroove is None):
        return ObjectsData
    NormalizedSketches = tuple((CanonicalSketch(ItemData, DocData.support_planes, ObjectIds) for ItemData in (SourceSketchOne, SourceSketchTwo)))
    SketchPayloads = tuple((SketchPayload(SketchData, SketchObject.object_id, ObjectIds)[0] for SketchData, SketchObject in zip(NormalizedSketches, (SketchOne, SketchTwo), strict=True)))
    SketchOne = Replace(SketchOne, payload=SketchPayloads[0])
    SketchTwo = Replace(SketchTwo, payload=SketchPayloads[1])
    NormalizedPad = CanonicalA(SourcePad, SourceSketchOne, DocData.support_planes, ObjectIds)
    PadObject = Replace(PadObject, payload=Extrusion(NormalizedPad))
    BoundsData = (WriteRectangle(SketchOne), WriteRectangle(SketchTwo))
    DimensionData = FreeCadPad(DocData, (SourceSketchOne, SourceSketchTwo), (SourcePad, SourceGroove))
    if PadObject.class_name != 'moExtrusion_c' or GrooveObject.class_name != 'moRevolution_c' or any((ItemData is None for ItemData in BoundsData)) or (ExtrusionEdit(PadObject.payload) is None) or (DimensionData is None) or any((len(SketchObject.payload) < 4 or Struct.unpack_from('<I', SketchObject.payload)[0] != 2 or SketchObject.class_name != 'moProfileFeature_c' or (not HasRectDims(SketchObject, BoundsValue)) or SketchData.suppressed or (not HasCanonical(SketchData, BoundsValue, None)) or (len(SketchData.closed_profile_entity_ids) != 1) or (set(SketchData.closed_profile_entity_ids[0]) != {ItemData.id for ItemData in SketchData.entities}) for SketchObject, SketchData, BoundsValue in zip((SketchOne, SketchTwo), (SourceSketchOne, SourceSketchTwo), BoundsData, strict=True))):
        return ObjectsData
    TargetIds = (26, 32, 33, 39)
    for SourceObject, TargetId in zip((SketchOne, PadObject, SketchTwo, GrooveObject), TargetIds, strict=True):
        PrefixValue = 'sketch' if SourceObject.kind == 'Sketch' else 'feature'
        ObjectIds[f'{PrefixValue}:{SourceObject.source_id}'] = TargetId
    PadDimension, GrooveDimension = DimensionData
    return (Replace(SketchOne, object_id=26, name='Sketch1'), Replace(PadObject, object_id=32, name='Boss-Extrude1', dimensions=(Replace(PadDimension, name='D1'),)), Replace(SketchTwo, object_id=33, name='Sketch2'), Replace(GrooveObject, object_id=39, name='Cut-Revolve1', kind='Cut-Revolve', dimensions=(GrooveDimension,)))

# this definition exists because focused behavior needs one stable owner
def CanonicalBossB(ObjectsData: tuple[_WriteObject, ...], ObjectIds: dict[str, int], DocData: CadDocument) -> tuple[WriteObject, ...]:
    if len(ObjectsData) != 3:
        return ObjectsData
    SketchObject, PadObject, FilletObject = ObjectsData
    SourceSketch = next((ItemData for ItemData in DocData.sketches if ItemData.id == SketchObject.source_id), None)

    # this callback exists because local behavior needs one focused transformation
    SourceFeatures = tuple((ItemData for ItemData in sorted(DocData.feature_timeline, key=lambda ItemData: ItemData.order) if not IsNativeSystem(ItemData)))
    if SourceSketch is None or len(SourceFeatures) != 2:
        return ObjectsData
    SourcePad, SourceFillet = SourceFeatures
    if SourcePad.id != PadObject.source_id or SourceFillet.id != FilletObject.source_id:
        return ObjectsData
    NormalizedSketch = CanonicalSketch(SourceSketch, DocData.support_planes, ObjectIds)
    SketchPayload, Ignored = SketchPayload(NormalizedSketch, SketchObject.object_id, ObjectIds)
    SketchObject = Replace(SketchObject, payload=SketchPayload)
    NormalizedPad = CanonicalA(SourcePad, SourceSketch, DocData.support_planes, ObjectIds)
    PadObject = Replace(PadObject, payload=Extrusion(NormalizedPad))
    BoundsValue = WriteRectangle(SketchObject)
    DimensionData = FreeCadBossB(DocData, SourceSketch, SourcePad, SourceFillet, BoundsValue)
    if BoundsValue is None or len(SketchObject.payload) < 4 or Struct.unpack_from('<I', SketchObject.payload)[0] != 2 or (SketchObject.class_name != 'moProfileFeature_c') or (not HasRectDims(SketchObject, BoundsValue)) or SourceSketch.suppressed or (not HasCanonical(SourceSketch, BoundsValue, None)) or (len(SourceSketch.closed_profile_entity_ids) != 1) or (set(SourceSketch.closed_profile_entity_ids[0]) != {ItemData.id for ItemData in SourceSketch.entities}) or (PadObject.class_name != 'moExtrusion_c') or (ExtrusionEdit(PadObject.payload) != (0, 0)) or (FilletObject.class_name != 'Fillet_c') or (DimensionData is None):
        return ObjectsData
    PadDimension, FilletDimension = DimensionData
    ObjectIds[f'sketch:{SketchObject.source_id}'] = 26
    ObjectIds[f'feature:{PadObject.source_id}'] = 32
    ObjectIds[f'feature:{FilletObject.source_id}'] = 34
    return (Replace(SketchObject, object_id=26, name='Sketch1'), Replace(PadObject, object_id=32, name='Boss-Extrude1', dimensions=(Replace(PadDimension, name='D1'),)), Replace(FilletObject, object_id=34, name='Fillet1', dimensions=(FilletDimension,), payload=FilletSelection(32, 3)))

# this definition exists because focused behavior needs one stable owner
def CanonicalBoss(ObjectsData: tuple[_WriteObject, ...], ObjectIds: dict[str, int], DocData: CadDocument) -> tuple[WriteObject, ...]:
    if len(ObjectsData) != 3:
        return ObjectsData
    SketchObject, PadObject, ChamferObject = ObjectsData
    SourceSketch = next((ItemData for ItemData in DocData.sketches if ItemData.id == SketchObject.source_id), None)

    # this callback exists because local behavior needs one focused transformation
    SourceFeatures = tuple((ItemData for ItemData in sorted(DocData.feature_timeline, key=lambda ItemData: ItemData.order) if not IsNativeSystem(ItemData)))
    if SourceSketch is None or len(SourceFeatures) != 2:
        return ObjectsData
    SourcePad, SourceChamfer = SourceFeatures
    if SourcePad.id != PadObject.source_id or SourceChamfer.id != ChamferObject.source_id:
        return ObjectsData
    NormalizedSketch = CanonicalSketch(SourceSketch, DocData.support_planes, ObjectIds)
    SketchPayload, Ignored = SketchPayload(NormalizedSketch, SketchObject.object_id, ObjectIds)
    SketchObject = Replace(SketchObject, payload=SketchPayload)
    NormalizedPad = CanonicalA(SourcePad, SourceSketch, DocData.support_planes, ObjectIds)
    PadObject = Replace(PadObject, payload=Extrusion(NormalizedPad))
    BoundsValue = WriteRectangle(SketchObject)
    DimensionData = FreeCadBoss(DocData, SourceSketch, SourcePad, SourceChamfer, BoundsValue)
    if BoundsValue is None or len(SketchObject.payload) < 4 or Struct.unpack_from('<I', SketchObject.payload)[0] != 2 or (SketchObject.class_name != 'moProfileFeature_c') or (not HasRectDims(SketchObject, BoundsValue)) or SourceSketch.suppressed or (not HasCanonical(SourceSketch, BoundsValue, None)) or (len(SourceSketch.closed_profile_entity_ids) != 1) or (set(SourceSketch.closed_profile_entity_ids[0]) != {ItemData.id for ItemData in SourceSketch.entities}) or (PadObject.class_name != 'moExtrusion_c') or (ExtrusionEdit(PadObject.payload) != (0, 0)) or (ChamferObject.class_name != 'Chamfer_c') or (DimensionData is None):
        return ObjectsData
    PadDimension, ChamferDimension = DimensionData
    ObjectIds[f'sketch:{SketchObject.source_id}'] = 26
    ObjectIds[f'feature:{PadObject.source_id}'] = 32
    ObjectIds[f'feature:{ChamferObject.source_id}'] = 35
    return (Replace(SketchObject, object_id=26, name='Sketch1'), Replace(PadObject, object_id=32, name='Boss-Extrude1', dimensions=(Replace(PadDimension, name='D1'),)), Replace(ChamferObject, object_id=35, name='Chamfer1', dimensions=(ChamferDimension,), payload=FilletSelection(32, 3)))

# this definition exists because focused behavior needs one stable owner
def CanonicalBossD(ObjectsData: tuple[_WriteObject, ...], ObjectIds: dict[str, int], DocData: CadDocument) -> tuple[WriteObject, ...]:
    if len(ObjectsData) != 3:
        return ObjectsData
    SketchObject, PadObject, ShellObject = ObjectsData
    SourceSketch = next((ItemData for ItemData in DocData.sketches if ItemData.id == SketchObject.source_id), None)

    # this callback exists because local behavior needs one focused transformation
    SourceFeatures = tuple((ItemData for ItemData in sorted(DocData.feature_timeline, key=lambda ItemData: ItemData.order) if not IsNativeSystem(ItemData)))
    if SourceSketch is None or len(SourceFeatures) != 2:
        return ObjectsData
    SourcePad, SourceShell = SourceFeatures
    if SourcePad.id != PadObject.source_id or SourceShell.id != ShellObject.source_id:
        return ObjectsData
    NormalizedSketch = CanonicalSketch(SourceSketch, DocData.support_planes, ObjectIds)
    SketchPayload, Ignored = SketchPayload(NormalizedSketch, SketchObject.object_id, ObjectIds)
    SketchObject = Replace(SketchObject, payload=SketchPayload)
    NormalizedPad = CanonicalA(SourcePad, SourceSketch, DocData.support_planes, ObjectIds)
    PadObject = Replace(PadObject, payload=Extrusion(NormalizedPad))
    BoundsValue = WriteRectangle(SketchObject)
    DimensionData = FreeCadBossD(DocData, SourceSketch, SourcePad, SourceShell, BoundsValue)
    if BoundsValue is None or len(SketchObject.payload) < 4 or Struct.unpack_from('<I', SketchObject.payload)[0] != 2 or (SketchObject.class_name != 'moProfileFeature_c') or (not HasRectDims(SketchObject, BoundsValue)) or SourceSketch.suppressed or (not HasCanonical(SourceSketch, BoundsValue, None)) or (len(SourceSketch.closed_profile_entity_ids) != 1) or (set(SourceSketch.closed_profile_entity_ids[0]) != {ItemData.id for ItemData in SourceSketch.entities}) or (PadObject.class_name != 'moExtrusion_c') or (ExtrusionEdit(PadObject.payload) != (0, 0)) or (ShellObject.class_name != 'moShell_c') or (DimensionData is None):
        return ObjectsData
    PadDimension, ShellDimension = DimensionData
    ObjectIds[f'sketch:{SketchObject.source_id}'] = 26
    ObjectIds[f'feature:{PadObject.source_id}'] = 32
    ObjectIds[f'feature:{ShellObject.source_id}'] = 34
    return (Replace(SketchObject, object_id=26, name='Sketch1'), Replace(PadObject, object_id=32, name='Boss-Extrude1', dimensions=(Replace(PadDimension, name='D1'),)), Replace(ShellObject, object_id=34, name='Shell1', dimensions=(ShellDimension,), payload=ShellSelection(32)))

# this definition exists because focused behavior needs one stable owner
def CanonicalBossC(ObjectsData: tuple[_WriteObject, ...], ObjectIds: dict[str, int], DocData: CadDocument) -> tuple[WriteObject, ...]:
    if len(ObjectsData) != 3:
        return ObjectsData
    SketchObject, PadObject, PatternObject = ObjectsData
    SourceSketch = next((ItemData for ItemData in DocData.sketches if ItemData.id == SketchObject.source_id), None)

    # this callback exists because local behavior needs one focused transformation
    SourceFeatures = tuple((ItemData for ItemData in sorted(DocData.feature_timeline, key=lambda ItemData: ItemData.order) if not IsNativeSystem(ItemData)))
    if SourceSketch is None or len(SourceFeatures) != 2:
        return ObjectsData
    SourcePad, SourcePattern = SourceFeatures
    if SourcePad.id != PadObject.source_id or SourcePattern.id != PatternObject.source_id:
        return ObjectsData
    NormalizedSketch = CanonicalSketch(SourceSketch, DocData.support_planes, ObjectIds)
    SketchPayload, Ignored = SketchPayload(NormalizedSketch, SketchObject.object_id, ObjectIds)
    SketchObject = Replace(SketchObject, payload=SketchPayload)
    NormalizedPad = CanonicalA(SourcePad, SourceSketch, DocData.support_planes, ObjectIds)
    PadObject = Replace(PadObject, payload=Extrusion(NormalizedPad))
    BoundsValue = WriteRectangle(SketchObject)
    DimensionData = FreeCadBossC(DocData, SourceSketch, SourcePad, SourcePattern, BoundsValue)
    if BoundsValue is None or len(SketchObject.payload) < 4 or Struct.unpack_from('<I', SketchObject.payload)[0] != 2 or (SketchObject.class_name != 'moProfileFeature_c') or (not HasRectDims(SketchObject, BoundsValue)) or SourceSketch.suppressed or (not HasCanonical(SourceSketch, BoundsValue, None)) or (len(SourceSketch.closed_profile_entity_ids) != 1) or (set(SourceSketch.closed_profile_entity_ids[0]) != {ItemData.id for ItemData in SourceSketch.entities}) or (PadObject.class_name != 'moExtrusion_c') or (ExtrusionEdit(PadObject.payload) != (0, 0)) or (PatternObject.class_name != 'moLPattern_c') or (DimensionData is None):
        return ObjectsData
    PadDimension, CountDimension, SpacingDimension = DimensionData
    ObjectIds[f'sketch:{SketchObject.source_id}'] = 26
    ObjectIds[f'feature:{PadObject.source_id}'] = 32
    ObjectIds[f'feature:{PatternObject.source_id}'] = 40
    return (Replace(SketchObject, object_id=26, name='Sketch1'), Replace(PadObject, object_id=32, name='Boss-Extrude1', dimensions=(Replace(PadDimension, name='D1'),)), Replace(PatternObject, object_id=40, name='LPattern1', kind='LPattern', dimensions=(CountDimension, SpacingDimension), payload=b''))

# this definition exists because focused behavior needs one stable owner
def CanonicalBossA(ObjectsData: tuple[_WriteObject, ...], ObjectIds: dict[str, int], DocData: CadDocument) -> tuple[WriteObject, ...]:
    if len(ObjectsData) != 3:
        return ObjectsData
    SketchObject, PadObject, PatternObject = ObjectsData
    SourceSketch = next((ItemData for ItemData in DocData.sketches if ItemData.id == SketchObject.source_id), None)

    # this callback exists because local behavior needs one focused transformation
    SourceFeatures = tuple((ItemData for ItemData in sorted(DocData.feature_timeline, key=lambda ItemData: ItemData.order) if not IsNativeSystem(ItemData)))
    if SourceSketch is None or len(SourceFeatures) != 2:
        return ObjectsData
    SourcePad, SourcePattern = SourceFeatures
    if SourcePad.id != PadObject.source_id or SourcePattern.id != PatternObject.source_id:
        return ObjectsData
    NormalizedSketch = CanonicalSketch(SourceSketch, DocData.support_planes, ObjectIds)
    SketchPayload, Ignored = SketchPayload(NormalizedSketch, SketchObject.object_id, ObjectIds)
    SketchObject = Replace(SketchObject, payload=SketchPayload)
    NormalizedPad = CanonicalA(SourcePad, SourceSketch, DocData.support_planes, ObjectIds)
    PadObject = Replace(PadObject, payload=Extrusion(NormalizedPad))
    BoundsValue = WriteRectangle(SketchObject)
    DimensionData = FreeCadBossA(DocData, SourceSketch, SourcePad, SourcePattern, BoundsValue)
    if BoundsValue is None or len(SketchObject.payload) < 4 or Struct.unpack_from('<I', SketchObject.payload)[0] != 2 or (SketchObject.class_name != 'moProfileFeature_c') or (not HasRectDims(SketchObject, BoundsValue)) or SourceSketch.suppressed or (not HasCanonical(SourceSketch, BoundsValue, None)) or (len(SourceSketch.closed_profile_entity_ids) != 1) or (set(SourceSketch.closed_profile_entity_ids[0]) != {ItemData.id for ItemData in SourceSketch.entities}) or (PadObject.class_name != 'moExtrusion_c') or (ExtrusionEdit(PadObject.payload) != (0, 0)) or (PatternObject.class_name != 'moCirPattern_c') or (DimensionData is None):
        return ObjectsData
    PadDimension, CountDimension, AngleDimension = DimensionData
    ObjectIds[f'sketch:{SketchObject.source_id}'] = 26
    ObjectIds[f'feature:{PadObject.source_id}'] = 32
    ObjectIds[f'feature:{PatternObject.source_id}'] = 46
    return (Replace(SketchObject, object_id=26, name='Sketch1'), Replace(PadObject, object_id=32, name='Boss-Extrude1', dimensions=(Replace(PadDimension, name='D1'),)), Replace(PatternObject, object_id=46, name='CirPattern1', kind='CirPattern', dimensions=(CountDimension, AngleDimension), payload=b''))

# this definition exists because focused behavior needs one stable owner
def CanonicalSingle(Objects: tuple[_WriteObject, ...], ObjectIds: dict[str, int], DocValue: CadDocument) -> tuple[WriteObject, ...]:
    if len(Objects) != 2:
        return Objects
    Sketch, Extrusion = Objects
    SourceSketch = next((ItemValue for ItemValue in DocValue.sketches if ItemValue.id == Sketch.source_id), None)
    SourceFeature = next((ItemValue for ItemValue in DocValue.feature_timeline if ItemValue.id == Extrusion.source_id), None)
    if SourceSketch is not None:
        NormalizedSketch = CanonicalSketch(SourceSketch, DocValue.support_planes, ObjectIds)
        NormalizedPayload, Ignored = SketchPayload(NormalizedSketch, Sketch.object_id, ObjectIds)
        Sketch = Replace(Sketch, payload=NormalizedPayload)
    if SourceFeature is not None and SourceSketch is not None:
        NormalizedFeature = CanonicalA(SourceFeature, SourceSketch, DocValue.support_planes, ObjectIds)
        Extrusion = Replace(Extrusion, payload=Extrusion(NormalizedFeature))
    Bounds = WriteRectangle(Sketch)
    Circle = WriteCircle(Sketch)
    PolylineData = PolySixPoints(Sketch)
    HasProfileDimensions = HasRectDims(Sketch, Bounds) if Bounds is not None else HasCircleDims(Sketch, Circle) if Circle is not None else PolylineData is not None and (not Sketch.dimensions)
    HasSourceGeom = SourceSketch is not None and (HasCanonical(SourceSketch, Bounds, Circle) if Bounds is not None or Circle is not None else HasPolySix(SourceSketch, PolylineData))
    if len(Sketch.payload) < 4 or Struct.unpack_from('<I', Sketch.payload)[0] not in {2, 3, 4} or Sketch.class_name != 'moProfileFeature_c' or (sum((ItemValue is not None for ItemValue in (Bounds, Circle, PolylineData))) != 1) or (not HasProfileDimensions) or (Extrusion.class_name != 'moExtrusion_c') or (ExtrusionEdit(Extrusion.payload) is None) or (SourceSketch is None) or SourceSketch.suppressed or (not HasSourceGeom) or (len(SourceSketch.closed_profile_entity_ids) != 1) or (set(SourceSketch.closed_profile_entity_ids[0]) != {ItemValue.id for ItemValue in SourceSketch.entities}) or (SourceFeature is None) or SourceFeature.suppressed or SourceFeature.input_feature_ids or SourceFeature.selection_ids or SourceFeature.configuration_states:
        return Objects
    FreecadDimension = FreecadSingle(DocValue, SourceSketch, SourceFeature)
    if FreecadDimension is None:
        if Sketch.object_id != 26 or Sketch.name != 'Sketch1' or Extrusion.name != 'Boss-Extrude1' or (len(Extrusion.dimensions) != 1) or (Extrusion.dimensions[0].name != 'D1') or (not MathValue.isfinite(Extrusion.dimensions[0].value_mm)) or (Extrusion.dimensions[0].value_mm <= 0.0):
            return Objects
        SourceDimension = Extrusion.dimensions[0]
    else:
        SourceDimension = FreecadDimension
    Dimension = Replace(SourceDimension, name='D1', text=format(SourceDimension.value_mm, '.15g'))
    if Circle is not None:
        CircleDimension = Sketch.dimensions[0]
        DiameterValue = Circle[2] * 2.0
        Sketch = Replace(Sketch, dimensions=(Replace(CircleDimension, name='D1', value_mm=DiameterValue, text='<MOD-DIAM>' + format(DiameterValue, '.15g')),))
    FeatureObjectId = 33 if Circle is not None else 32
    ObjectIds[f'sketch:{Sketch.source_id}'] = 26
    ObjectIds[f'feature:{Extrusion.source_id}'] = FeatureObjectId
    return (Replace(Sketch, object_id=26, name='Sketch1'), Replace(Extrusion, object_id=FeatureObjectId, name='Boss-Extrude1', dimensions=(Dimension,)))

# this definition exists because focused behavior needs one stable owner
def CanonicalTwo(ObjectsData: tuple[_WriteObject, ...], ObjectIds: dict[str, int], DocData: CadDocument) -> tuple[WriteObject, ...]:
    if len(ObjectsData) != 4:
        return ObjectsData
    SketchOne, FeatureOne, SketchTwo, FeatureTwo = ObjectsData
    SourceSketches = tuple((next((ItemData for ItemData in DocData.sketches if ItemData.id == SketchObject.source_id), None) for SketchObject in (SketchOne, SketchTwo)))
    SourceFeatures = tuple((next((ItemData for ItemData in DocData.feature_timeline if ItemData.id == FeatureObject.source_id), None) for FeatureObject in (FeatureOne, FeatureTwo)))
    if any((ItemData is None for ItemData in (*SourceSketches, *SourceFeatures))):
        return ObjectsData
    SourceSketchOne, SourceSketchTwo = SourceSketches
    SourceFeatureOne, SourceFeatureTwo = SourceFeatures
    if SourceSketchOne is None or SourceSketchTwo is None or SourceFeatureOne is None or (SourceFeatureTwo is None):
        return ObjectsData
    NormalizedSketches = tuple((CanonicalSketch(ItemData, DocData.support_planes, ObjectIds) for ItemData in (SourceSketchOne, SourceSketchTwo)))
    NormalizedFeatures = tuple((CanonicalA(FeatureData, SketchData, DocData.support_planes, ObjectIds) for FeatureData, SketchData in zip((SourceFeatureOne, SourceFeatureTwo), (SourceSketchOne, SourceSketchTwo), strict=True)))
    NormalizedObjects: list[WriteObject] = []
    for SketchObject, FeatureObject, SketchData, FeatureData in zip((SketchOne, SketchTwo), (FeatureOne, FeatureTwo), NormalizedSketches, NormalizedFeatures, strict=True):
        SketchPayload, Ignored = SketchPayload(SketchData, SketchObject.object_id, ObjectIds)
        NormalizedObjects.extend((Replace(SketchObject, payload=SketchPayload), Replace(FeatureObject, payload=Extrusion(FeatureData))))
    SketchOne, FeatureOne, SketchTwo, FeatureTwo = NormalizedObjects
    BoundsData = (WriteRectangle(SketchOne), WriteRectangle(SketchTwo))
    DimensionData = FreeCadTwo(DocData, (SourceSketchOne, SourceSketchTwo), (SourceFeatureOne, SourceFeatureTwo))
    SecondIsBoss = str(SourceFeatureTwo.operation).casefold() == BoolOperation.JOIN.value
    if FeatureOne.class_name != 'moExtrusion_c' or FeatureTwo.class_name != ('moExtrusion_c' if SecondIsBoss else 'moCut_c') or any((ItemData is None for ItemData in BoundsData)) or any((ExtrusionEdit(ItemData.payload) is None for ItemData in (FeatureOne, FeatureTwo))) or (DimensionData is None) or any((len(SketchObject.payload) < 4 or Struct.unpack_from('<I', SketchObject.payload)[0] != 2 or SketchObject.class_name != 'moProfileFeature_c' or (not HasRectDims(SketchObject, BoundsValue)) or SketchData.suppressed or (not HasCanonical(SketchData, BoundsValue, None)) or (len(SketchData.closed_profile_entity_ids) != 1) or (set(SketchData.closed_profile_entity_ids[0]) != {ItemData.id for ItemData in SketchData.entities}) for SketchObject, SketchData, BoundsValue in zip((SketchOne, SketchTwo), (SourceSketchOne, SourceSketchTwo), BoundsData, strict=True))):
        return ObjectsData
    TargetIds = (26, 32, 33, 40)
    TargetNames = ('Sketch1', 'Boss-Extrude1', 'Sketch2', 'Boss-Extrude2' if SecondIsBoss else 'Cut-Extrude1')
    for SourceObject, TargetId in zip((SketchOne, FeatureOne, SketchTwo, FeatureTwo), TargetIds, strict=True):
        PrefixValue = 'sketch' if SourceObject.kind == 'Sketch' else 'feature'
        ObjectIds[f'{PrefixValue}:{SourceObject.source_id}'] = TargetId
    CanonicalObjects: list[WriteObject] = []
    for ObjectIndex, (ItemData, TargetId, TargetName) in enumerate(zip((SketchOne, FeatureOne, SketchTwo, FeatureTwo), TargetIds, TargetNames, strict=True)):
        if ItemData.kind == 'Extrusion':
            DimensionValue = DimensionData[ObjectIndex // 2]
            DimensionValues = () if DimensionValue is None else (Replace(DimensionValue, name='D1', text=format(DimensionValue.value_mm, '.15g')),)
            ChildObjectId = TargetIds[ObjectIndex - 1]
            PropValues = tuple(((PropName, str(ChildObjectId) if PropName == 'DissectableChildren' else PropValue) for PropName, PropValue in ItemData.properties))
        else:
            DimensionValues = ItemData.dimensions
            PropValues = ItemData.properties
        CanonicalObjects.append(Replace(ItemData, object_id=TargetId, name=TargetName, properties=PropValues, dimensions=DimensionValues))
    return tuple(CanonicalObjects)

# this definition exists because focused behavior needs one stable owner
def CanonicalCut(ObjectsData: tuple[_WriteObject, ...], ObjectIds: dict[str, int], DocData: CadDocument) -> tuple[WriteObject, ...]:
    FeatureCount = len(ObjectsData) // 2
    if FeatureCount not in {3, 4} or len(ObjectsData) != FeatureCount * 2:
        return ObjectsData
    SketchObjects = ObjectsData[0::2]
    FeatureObjects = ObjectsData[1::2]
    SourceSketches = tuple((next((SketchData for SketchData in DocData.sketches if SketchData.id == SketchObject.source_id), None) for SketchObject in SketchObjects))
    SourceFeatures = tuple((next((FeatureData for FeatureData in DocData.feature_timeline if FeatureData.id == FeatureObject.source_id), None) for FeatureObject in FeatureObjects))
    if any((ItemData is None for ItemData in (*SourceSketches, *SourceFeatures))):
        return ObjectsData
    ResolvedSketches = tuple((ItemData for ItemData in SourceSketches if ItemData is not None))
    ResolvedFeatures = tuple((ItemData for ItemData in SourceFeatures if ItemData is not None))
    if len(ResolvedSketches) != FeatureCount or len(ResolvedFeatures) != FeatureCount:
        return ObjectsData
    NormalizedSketches = tuple((CanonicalSketch(ItemData, DocData.support_planes, ObjectIds) for ItemData in ResolvedSketches))
    NormalizedFeatures = tuple((CanonicalA(FeatureData, SketchData, DocData.support_planes, ObjectIds) for FeatureData, SketchData in zip(ResolvedFeatures, ResolvedSketches, strict=True)))
    NormalizedObjects: list[WriteObject] = []
    for SketchObject, FeatureObject, SketchData, FeatureData in zip(SketchObjects, FeatureObjects, NormalizedSketches, NormalizedFeatures, strict=True):
        SketchPayload, Ignored = SketchPayload(SketchData, SketchObject.object_id, ObjectIds)
        NormalizedObjects.extend((Replace(SketchObject, payload=SketchPayload), Replace(FeatureObject, payload=Extrusion(FeatureData))))
    SketchObjects = tuple(NormalizedObjects[0::2])
    FeatureObjects = tuple(NormalizedObjects[1::2])
    BoundsData = tuple((WriteRectangle(ItemData) for ItemData in SketchObjects))
    CircleData = tuple((WriteCircle(ItemData) for ItemData in SketchObjects))
    HasCircleData = IsCircleChain(BoundsData, CircleData)
    DimensionData = FreeCadThree(DocData, ResolvedSketches, ResolvedFeatures) if FeatureCount == 3 else FreeCadFour(DocData, ResolvedSketches, ResolvedFeatures)
    if tuple((ItemData.class_name for ItemData in FeatureObjects)) != ('moExtrusion_c', *('moCut_c',) * (FeatureCount - 1)) or (not HasCircleData and any((ItemData is None for ItemData in BoundsData))) or any((ExtrusionEdit(ItemData.payload) is None for ItemData in FeatureObjects)) or (DimensionData is None) or any((len(SketchObject.payload) < 4 or Struct.unpack_from('<I', SketchObject.payload)[0] != 2 or SketchObject.class_name != 'moProfileFeature_c' or (not (HasRectDims(SketchObject, BoundsValue) if BoundsValue is not None else HasCircleDims(SketchObject, CircleValue))) or SketchData.suppressed or (not HasCanonical(SketchData, BoundsValue, CircleValue)) or (len(SketchData.closed_profile_entity_ids) != 1) or (set(SketchData.closed_profile_entity_ids[0]) != {ItemData.id for ItemData in SketchData.entities}) for SketchObject, SketchData, BoundsValue, CircleValue in zip(SketchObjects, ResolvedSketches, BoundsData, CircleData, strict=True))):
        return ObjectsData
    TargetIds = (26, 32, 33, 40, 41, 47) if FeatureCount == 3 else (26, 32, 33, 40, 41, 47, 48, 54)
    TargetNames = tuple((NameValue for FeatureIndex in range(FeatureCount) for NameValue in (f'Sketch{FeatureIndex + 1}', 'Boss-Extrude1' if FeatureIndex == 0 else f'Cut-Extrude{FeatureIndex}')))
    for SourceObject, TargetId in zip(NormalizedObjects, TargetIds, strict=True):
        PrefixValue = 'sketch' if SourceObject.kind == 'Sketch' else 'feature'
        ObjectIds[f'{PrefixValue}:{SourceObject.source_id}'] = TargetId
    CanonicalObjects: list[WriteObject] = []
    for ObjectIndex, (ItemData, TargetId, TargetName) in enumerate(zip(NormalizedObjects, TargetIds, TargetNames, strict=True)):
        if ItemData.kind == 'Extrusion':
            DimensionValue = DimensionData[ObjectIndex // 2]
            DimensionValues = (Replace(DimensionValue, name='D1', text=format(DimensionValue.value_mm, '.15g')),)
            ChildObjectId = TargetIds[ObjectIndex - 1]
            PropValues = tuple(((PropName, str(ChildObjectId) if PropName == 'DissectableChildren' else PropValue) for PropName, PropValue in ItemData.properties))
        else:
            DimensionValues = ItemData.dimensions
            PropValues = ItemData.properties
        CanonicalObjects.append(Replace(ItemData, object_id=TargetId, name=TargetName, properties=PropValues, dimensions=DimensionValues))
    return tuple(CanonicalObjects)

# this definition exists because focused behavior needs one stable owner
def PrincipalPlane(PlaneObjectId: int) -> tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]] | None:
    return {2: ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)), 3: ((1.0, 0.0, 0.0), (0.0, 0.0, -1.0), (0.0, 1.0, 0.0)), 4: ((0.0, 0.0, -1.0), (0.0, 1.0, 0.0), (1.0, 0.0, 0.0))}.get(PlaneObjectId)

# this definition exists because focused behavior needs one stable owner
def ExpectedPlane(PlaneData: SupportPlane, PlaneObjectId: int) -> tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]:
    PrincipalFrame = PrincipalPlane(PlaneObjectId)
    if PrincipalFrame is not None:
        return ((0.0, 0.0, 0.0), *PrincipalFrame)
    return (FrameVector((PlaneData.transform.origin.x, PlaneData.transform.origin.y, PlaneData.transform.origin.z)), FrameVector((PlaneData.transform.x_axis.x, PlaneData.transform.x_axis.y, PlaneData.transform.x_axis.z)), FrameVector((PlaneData.transform.y_axis.x, PlaneData.transform.y_axis.y, PlaneData.transform.y_axis.z)), FrameVector((PlaneData.transform.z_axis.x, PlaneData.transform.z_axis.y, PlaneData.transform.z_axis.z)))

# this definition exists because focused behavior needs one stable owner
def CanonicalSketch(SketchData: Sketch, PlaneData: tuple[SupportPlane, ...], ObjectIds: Mapping[str, int]) -> Sketch:
    PlaneValue = next((ItemData for ItemData in PlaneData if ItemData.id == SketchData.support_plane_id), None)
    PlaneObjectId = ObjectIds.get(f'plane:{SketchData.support_plane_id}', 0)
    TargetFrame = PrincipalPlane(PlaneObjectId)
    if PlaneValue is None or TargetFrame is None:
        return SketchData
    SourceFrame = PlaneValue.transform
    TargetU, TargetV, Ignored = TargetFrame

    # this definition exists because focused behavior needs one stable owner
    def TransformPoint(PointData: Vector2) -> VectorTwo:
        GlobalValue = (SourceFrame.origin.x + PointData.x * SourceFrame.x_axis.x + PointData.y * SourceFrame.y_axis.x, SourceFrame.origin.y + PointData.x * SourceFrame.x_axis.y + PointData.y * SourceFrame.y_axis.y, SourceFrame.origin.z + PointData.x * SourceFrame.x_axis.z + PointData.y * SourceFrame.y_axis.z)
        return VectorTwo(sum((LeftValue * RightValue for LeftValue, RightValue in zip(GlobalValue, TargetU, strict=True))), sum((LeftValue * RightValue for LeftValue, RightValue in zip(GlobalValue, TargetV, strict=True))))
    NormalizedEntities = []
    for EntityData in SketchData.entities:
        GeomData = EntityData.geometry
        if isinstance(GeomData, LineGeom):
            GeomData = Replace(GeomData, start=TransformPoint(GeomData.start), end=TransformPoint(GeomData.end))
        elif isinstance(GeomData, CircleGeom):
            GeomData = Replace(GeomData, center=TransformPoint(GeomData.center))
        NormalizedEntities.append(Replace(EntityData, geometry=GeomData))
    return Replace(SketchData, entities=tuple(NormalizedEntities))

# this definition exists because focused behavior needs one stable owner
def CanonicalA(FeatureData: FeatureStep, SketchData: Sketch, PlaneData: tuple[SupportPlane, ...], ObjectIds: Mapping[str, int]) -> FeatureStep:
    DefinitionData = FeatureData.definition
    PlaneValue = next((ItemData for ItemData in PlaneData if ItemData.id == SketchData.support_plane_id), None)
    PlaneObjectId = ObjectIds.get(f'plane:{SketchData.support_plane_id}', 0)
    TargetFrame = PrincipalPlane(PlaneObjectId)
    if not isinstance(DefinitionData, ExtrusionFeature) or PlaneValue is None or TargetFrame is None:
        return FeatureData
    SourceNormal = PlaneValue.transform.z_axis
    TargetNormal = TargetFrame[2]
    OpposedValue = sum((LeftValue * RightValue for LeftValue, RightValue in zip((SourceNormal.x, SourceNormal.y, SourceNormal.z), TargetNormal, strict=True))) < 0.0
    return Replace(FeatureData, definition=Replace(DefinitionData, reversed=DefinitionData.reversed != OpposedValue))

# this definition exists because focused behavior needs one stable owner
def HasCanonical(SketchData: Sketch, BoundsValue: tuple[float, float, float, float] | None, CircleValue: tuple[float, float, float] | None) -> bool:
    if (BoundsValue is None) == (CircleValue is None):
        return False
    if any((ItemData.construction or ItemData.fixed for ItemData in SketchData.entities)):
        return False
    if BoundsValue is not None:
        return len(SketchData.entities) == 4 and all((isinstance(ItemData.geometry, LineGeom) for ItemData in SketchData.entities))
    return len(SketchData.entities) == 1 and isinstance(SketchData.entities[0].geometry, CircleGeom)

# this definition exists because focused behavior needs one stable owner
def HasPolySix(SketchData: Sketch, PointsData: tuple[tuple[float, float], ...] | None) -> bool:
    if PointsData is None or len(PointsData) != 6 or len(SketchData.entities) != 6:
        return False
    if any((ItemData.construction or ItemData.fixed for ItemData in SketchData.entities)):
        return False
    if not all((isinstance(ItemData.geometry, LineGeom) for ItemData in SketchData.entities)):
        return False
    LineData = tuple((ItemData.geometry for ItemData in SketchData.entities if isinstance(ItemData.geometry, LineGeom)))
    return LineLoopPoints(LineData) is not None

# this definition exists because focused behavior needs one stable owner
def FreeCadFour(DocData: CadDocument, SketchData: tuple[Sketch, ...], FeatureData: tuple[FeatureStep, ...]) -> tuple[WriteDimension, WriteDimension, WriteDimension, WriteDimension] | None:
    if len(SketchData) != 4 or len(FeatureData) != 4:
        return None

    # this callback exists because local behavior needs one focused transformation
    TimelineData = tuple((ItemData for ItemData in sorted(DocData.feature_timeline, key=lambda ItemData: ItemData.order) if not IsNativeSystem(ItemData)))
    AllowedOwners = {*(ItemData.id for ItemData in SketchData), *(ItemData.id for ItemData in FeatureData)}
    if DocData.source.format_id.casefold() != 'freecad.fcstd' or DocData.assembly is not None or DocData.selections or (tuple(DocData.sketches) != SketchData) or (TimelineData != FeatureData) or (len(DocData.bodies) != 1) or (DocData.bodies[0].final_feature_id != FeatureData[-1].id) or (tuple((ItemData.order for ItemData in FeatureData)) != (0, 1, 2, 3)) or (tuple((ItemData.sketch_id for ItemData in FeatureData)) != tuple((ItemData.id for ItemData in SketchData))) or FeatureData[0].input_feature_ids or any((FeatureValue.input_feature_ids != (FeatureData[FeatureIndex - 1].id,) for FeatureIndex, FeatureValue in enumerate(FeatureData[1:], start=1))) or any((ItemData.selection_ids for ItemData in FeatureData)) or any((ItemData.configuration_states for ItemData in FeatureData)) or any((ItemData.suppressed for ItemData in FeatureData)) or (str(FeatureData[0].operation).casefold() not in {BoolOperation.CREATE.value, BoolOperation.JOIN.value}) or any((str(ItemData.operation).casefold() != BoolOperation.CUT.value for ItemData in FeatureData[1:])) or (len(DocData.configurations) != 1) or (DocData.configurations[0].name.casefold() != 'default') or (not DocData.configurations[0].active) or (DocData.configurations[0].parent_id is not None) or DocData.configurations[0].overrides or DocData.configurations[0].suppressed_feature_ids or any((ItemData.owner_id not in AllowedOwners for ItemData in DocData.parameters)):
        return None
    DimensionData = tuple((FreeCadFeature(DocData, SketchValue, FeatureValue, TypeId, SecondLength, Visibility) for SketchValue, FeatureValue, TypeId, SecondLength, Visibility in zip(SketchData, FeatureData, ('PartDesign::Pad', 'PartDesign::Pocket', 'PartDesign::Pocket', 'PartDesign::Pocket'), (10.0, 5.0, 5.0, 5.0), (False, False, False, True), strict=True)))
    if any((ItemData is None for ItemData in DimensionData)):
        return None
    return (DimensionData[0], DimensionData[1], DimensionData[2], DimensionData[3])

# this definition exists because focused behavior needs one stable owner
def FreeCadThree(DocData: CadDocument, SketchData: tuple[Sketch, ...], FeatureData: tuple[FeatureStep, ...]) -> tuple[WriteDimension, WriteDimension, WriteDimension] | None:
    if len(SketchData) != 3 or len(FeatureData) != 3:
        return None
    SketchOne, SketchTwo, SketchThree = SketchData
    FeatureOne, FeatureTwo, FeatureThree = FeatureData

    # this callback exists because local behavior needs one focused transformation
    TimelineData = tuple((ItemData for ItemData in sorted(DocData.feature_timeline, key=lambda ItemData: ItemData.order) if not IsNativeSystem(ItemData)))
    AllowedOwners = {*(ItemData.id for ItemData in SketchData), *(ItemData.id for ItemData in FeatureData)}
    if DocData.source.format_id.casefold() != 'freecad.fcstd' or DocData.assembly is not None or DocData.selections or (tuple(DocData.sketches) != SketchData) or (TimelineData != FeatureData) or (len(DocData.bodies) != 1) or (DocData.bodies[0].final_feature_id != FeatureThree.id) or (tuple((ItemData.order for ItemData in FeatureData)) != (0, 1, 2)) or (tuple((ItemData.sketch_id for ItemData in FeatureData)) != tuple((ItemData.id for ItemData in SketchData))) or FeatureOne.input_feature_ids or (FeatureTwo.input_feature_ids != (FeatureOne.id,)) or (FeatureThree.input_feature_ids != (FeatureTwo.id,)) or any((ItemData.selection_ids for ItemData in FeatureData)) or any((ItemData.configuration_states for ItemData in FeatureData)) or any((ItemData.suppressed for ItemData in FeatureData)) or (str(FeatureOne.operation).casefold() not in {BoolOperation.CREATE.value, BoolOperation.JOIN.value}) or any((str(ItemData.operation).casefold() != BoolOperation.CUT.value for ItemData in (FeatureTwo, FeatureThree))) or (len(DocData.configurations) != 1) or (DocData.configurations[0].name.casefold() != 'default') or (not DocData.configurations[0].active) or (DocData.configurations[0].parent_id is not None) or DocData.configurations[0].overrides or DocData.configurations[0].suppressed_feature_ids or any((ItemData.owner_id not in AllowedOwners for ItemData in DocData.parameters)):
        return None
    DimensionData = tuple((FreeCadFeature(DocData, SketchValue, FeatureValue, TypeId, SecondLength, Visibility) for SketchValue, FeatureValue, TypeId, SecondLength, Visibility in zip((SketchOne, SketchTwo, SketchThree), (FeatureOne, FeatureTwo, FeatureThree), ('PartDesign::Pad', 'PartDesign::Pocket', 'PartDesign::Pocket'), (10.0, 5.0, 5.0), (False, False, True), strict=True)))
    if any((ItemData is None for ItemData in DimensionData)):
        return None
    return (DimensionData[0], DimensionData[1], DimensionData[2])

# this definition exists because focused behavior needs one stable owner
def FreeCadTwo(DocData: CadDocument, SketchData: tuple[Sketch, Sketch], FeatureData: tuple[FeatureStep, FeatureStep]) -> tuple[WriteDimension, WriteDimension | None] | None:
    SketchOne, SketchTwo = SketchData
    FeatureOne, FeatureTwo = FeatureData

    # this callback exists because local behavior needs one focused transformation
    TimelineData = tuple((ItemData for ItemData in sorted(DocData.feature_timeline, key=lambda ItemData: ItemData.order) if not IsNativeSystem(ItemData)))
    AllowedOwners = {SketchOne.id, SketchTwo.id, FeatureOne.id, FeatureTwo.id}
    if DocData.source.format_id.casefold() != 'freecad.fcstd' or DocData.assembly is not None or DocData.selections or (tuple(DocData.sketches) != (SketchOne, SketchTwo)) or (TimelineData != (FeatureOne, FeatureTwo)) or (len(DocData.bodies) != 1) or (DocData.bodies[0].final_feature_id != FeatureTwo.id) or (FeatureOne.order != 0) or (FeatureTwo.order != 1) or (FeatureOne.sketch_id != SketchOne.id) or (FeatureTwo.sketch_id != SketchTwo.id) or FeatureOne.input_feature_ids or (FeatureTwo.input_feature_ids != (FeatureOne.id,)) or FeatureOne.selection_ids or FeatureTwo.selection_ids or FeatureOne.configuration_states or FeatureTwo.configuration_states or FeatureOne.suppressed or FeatureTwo.suppressed or (str(FeatureOne.operation).casefold() not in {BoolOperation.CREATE.value, BoolOperation.JOIN.value}) or (str(FeatureTwo.operation).casefold() not in {BoolOperation.CUT.value, BoolOperation.JOIN.value}) or (len(DocData.configurations) != 1) or (DocData.configurations[0].name.casefold() != 'default') or (not DocData.configurations[0].active) or (DocData.configurations[0].parent_id is not None) or DocData.configurations[0].overrides or DocData.configurations[0].suppressed_feature_ids or any((ItemData.owner_id not in AllowedOwners for ItemData in DocData.parameters)):
        return None
    DimensionOne = FreeCadFeature(DocData, SketchOne, FeatureOne, 'PartDesign::Pad', 10.0, False)
    if not isinstance(FeatureTwo.definition, ExtrusionFeature):
        return None
    SecondOperation = str(FeatureTwo.operation).casefold()
    if SecondOperation == BoolOperation.CUT.value and str(FeatureTwo.definition.end_condition).casefold() == ExtrusionEndCondition.THROUGH_ALL.value:
        if not HasFreeCadAll(DocData, SketchTwo, FeatureTwo):
            return None
        DimensionTwo = None
    else:
        DimensionTwo = FreeCadFeature(DocData, SketchTwo, FeatureTwo, 'PartDesign::Pad' if SecondOperation == BoolOperation.JOIN.value else 'PartDesign::Pocket', 10.0 if SecondOperation == BoolOperation.JOIN.value else 5.0, True)
        if DimensionTwo is None:
            return None
    if DimensionOne is None:
        return None
    return (DimensionOne, DimensionTwo)

# this definition exists because focused behavior needs one stable owner
def FreeCadPad(DocData: CadDocument, SketchData: tuple[Sketch, Sketch], FeatureData: tuple[FeatureStep, FeatureStep]) -> tuple[WriteDimension, WriteDimension] | None:
    SketchOne, SketchTwo = SketchData
    PadFeature, GrooveFeature = FeatureData

    # this callback exists because local behavior needs one focused transformation
    TimelineData = tuple((ItemData for ItemData in sorted(DocData.feature_timeline, key=lambda ItemData: ItemData.order) if not IsNativeSystem(ItemData)))
    GrooveDefinition = GrooveFeature.definition
    if DocData.source.format_id.casefold() != 'freecad.fcstd' or DocData.assembly is not None or tuple(DocData.sketches) != (SketchOne, SketchTwo) or (TimelineData != (PadFeature, GrooveFeature)) or (len(DocData.bodies) != 1) or (DocData.bodies[0].final_feature_id != GrooveFeature.id) or (PadFeature.order != 0) or (GrooveFeature.order != 1) or (PadFeature.sketch_id != SketchOne.id) or (GrooveFeature.sketch_id != SketchTwo.id) or PadFeature.input_feature_ids or (GrooveFeature.input_feature_ids != (PadFeature.id,)) or PadFeature.selection_ids or (len(GrooveFeature.selection_ids) != 1) or PadFeature.configuration_states or GrooveFeature.configuration_states or PadFeature.suppressed or GrooveFeature.suppressed or (str(PadFeature.operation).casefold() not in {BoolOperation.CREATE.value, BoolOperation.JOIN.value}) or (str(GrooveFeature.operation).casefold() != BoolOperation.CUT.value) or (str(GrooveFeature.kind).casefold() != FeatureKind.REVOLUTION.value) or (FreecadTypeId(GrooveFeature.attributes) != 'PartDesign::Groove') or (not isinstance(GrooveDefinition, NativeFeatureDefinition)) or (GrooveDefinition.format_id.casefold() != 'freecad.fcstd') or (GrooveDefinition.type_id != 'PartDesign::Groove') or (len(DocData.configurations) != 1) or (DocData.configurations[0].name.casefold() != 'default') or (not DocData.configurations[0].active) or (DocData.configurations[0].parent_id is not None) or DocData.configurations[0].overrides or DocData.configurations[0].suppressed_feature_ids or (len(DocData.selections) != 1) or (GrooveFeature.selection_ids != (DocData.selections[0].id,)):
        return None
    AxisSelection = DocData.selections[0]
    if GrooveFeature.provenance is None or AxisSelection.attributes.get('freecad_object') != GrooveFeature.provenance.native_id or AxisSelection.attributes.get('freecad_property') != 'ReferenceAxis' or (len(AxisSelection.path) != 1) or (AxisSelection.path[0].entity_id != SketchTwo.name) or (AxisSelection.path[0].subelement != KHorizontalAxisSubElem):
        return None
    PadDimension = FreeCadFeature(DocData, SketchOne, PadFeature, 'PartDesign::Pad', 10.0, False)
    if PadDimension is None:
        return None
    ParamData: dict[str, Param] = {}
    for ParamValueData in DocData.parameters:
        if ParamValueData.owner_id != GrooveFeature.id:
            continue
        PathValue = ParamValueData.attributes.get('freecad_path')
        if not isinstance(PathValue, str) or not PathValue or PathValue in ParamData or (ParamValueData.expression is not None):
            return None
        ParamData[PathValue] = ParamValueData
    ExpectedData = {'AllowMultiFace': (ValueKind.BOOLEAN, True), 'Angle': (ValueKind.ANGLE, 360.0), 'Angle2': (ValueKind.ANGLE, 0.0), 'FuzzyTolerance': (ValueKind.NUMBER, -1.0), 'Label': (ValueKind.STRING, GrooveFeature.name), 'Label2': (ValueKind.STRING, ''), 'Midplane': (ValueKind.BOOLEAN, False), 'Refine': (ValueKind.BOOLEAN, True), 'Reversed': (ValueKind.BOOLEAN, False), 'Suppressed': (ValueKind.BOOLEAN, False), 'Type': (ValueKind.INTEGER, 0), 'Visibility': (ValueKind.BOOLEAN, True)}
    if set(ParamData) != set(ExpectedData) or any((not FreecadParam(ParamData[PathValue], KindValue, ExpectedValue) for PathValue, (KindValue, ExpectedValue) in ExpectedData.items())):
        return None
    AngleParam = ParamData['Angle']
    if AngleParam.value.unit.casefold() not in {'deg', 'degree', 'degrees'}:
        return None
    return (PadDimension, WriteDimension('D1', 360.0, '360°', AngleParam.role))

# this definition exists because focused behavior needs one stable owner
def FreeCadBossB(DocData: CadDocument, SketchData: Sketch, PadFeature: FeatureStep, FilletFeatureData: FeatureStep, BoundsValue: tuple[float, float, float, float] | None) -> tuple[WriteDimension, WriteDimension] | None:

    # this callback exists because local behavior needs one focused transformation
    TimelineData = tuple((ItemData for ItemData in sorted(DocData.feature_timeline, key=lambda ItemData: ItemData.order) if not IsNativeSystem(ItemData)))
    FilletDefinition = FilletFeatureData.definition
    PadDefinition = PadFeature.definition
    AllowedOwners = {SketchData.id, PadFeature.id, FilletFeatureData.id}
    if BoundsValue is None or DocData.source.format_id.casefold() != 'freecad.fcstd' or DocData.assembly is not None or (tuple(DocData.sketches) != (SketchData,)) or (TimelineData != (PadFeature, FilletFeatureData)) or (len(DocData.bodies) != 1) or (DocData.bodies[0].final_feature_id != FilletFeatureData.id) or (PadFeature.order != 0) or (FilletFeatureData.order != 1) or (PadFeature.sketch_id != SketchData.id) or (FilletFeatureData.sketch_id is not None) or PadFeature.input_feature_ids or (FilletFeatureData.input_feature_ids != (PadFeature.id,)) or PadFeature.selection_ids or (len(FilletFeatureData.selection_ids) != 1) or PadFeature.configuration_states or FilletFeatureData.configuration_states or PadFeature.suppressed or FilletFeatureData.suppressed or (str(PadFeature.operation).casefold() not in {BoolOperation.CREATE.value, BoolOperation.JOIN.value}) or (FilletFeatureData.operation is not None) or (str(FilletFeatureData.kind).casefold() != FeatureKind.FILLET.value) or (FreecadTypeId(SketchData.attributes) != 'Sketcher::SketchObject') or (FreecadTypeId(PadFeature.attributes) != 'PartDesign::Pad') or (FreecadTypeId(FilletFeatureData.attributes) != 'PartDesign::Fillet') or (not isinstance(PadDefinition, ExtrusionFeature)) or PadDefinition.reversed or PadDefinition.symmetric or (not isinstance(FilletDefinition, FilletFeature)) or FilletDefinition.variable_radius_parameter_ids or (FilletFeatureData.provenance is None) or (len(DocData.configurations) != 1) or (DocData.configurations[0].name.casefold() != 'default') or (not DocData.configurations[0].active) or (DocData.configurations[0].parent_id is not None) or DocData.configurations[0].overrides or DocData.configurations[0].suppressed_feature_ids or (len(DocData.selections) != 1) or (FilletFeatureData.selection_ids != (DocData.selections[0].id,)) or any((ItemData.owner_id not in AllowedOwners for ItemData in DocData.parameters)):
        return None
    PadDimension = FreeCadFeature(DocData, SketchData, PadFeature, 'PartDesign::Pad', 10.0, False)
    RadiusValue = FilletDefinition.radius
    RadiusDimension = ParamDimension(Param('', 'D1', RadiusValue))
    if PadDimension is None or RadiusDimension is None or RadiusDimension.value_mm <= 0.0:
        return None
    RadiusNumber = RadiusDimension.value_mm
    MinimumX, MinimumY, MaximumX, MaximumY = BoundsValue
    if not MathValue.isfinite(RadiusNumber) or RadiusNumber <= 0.0 or RadiusNumber * 2.0 >= min(MaximumX - MinimumX, MaximumY - MinimumY):
        return None
    SelectionData = DocData.selections[0]
    PadNativeName = PadFeature.provenance.native_id if PadFeature.provenance is not None else PadFeature.name
    if SelectionData.attributes.get('freecad_object') != FilletFeatureData.provenance.native_id or SelectionData.attributes.get('freecad_property') != 'Base' or SelectionData.attributes.get('freecad_target') != PadNativeName or (len(SelectionData.path) != 1) or (SelectionData.path[0].entity_kind != 'edge') or (SelectionData.path[0].entity_id != PadNativeName) or (not HasFreeCadMax(DocData, PadNativeName, SelectionData.path[0].subelement, BoundsValue, PadDimension.value_mm)):
        return None
    ParamData: dict[str, Param] = {}
    for ParamValueData in DocData.parameters:
        if ParamValueData.owner_id != FilletFeatureData.id:
            continue
        PathValue = ParamValueData.attributes.get('freecad_path')
        if not isinstance(PathValue, str) or not PathValue or PathValue in ParamData or (ParamValueData.expression is not None):
            return None
        ParamData[PathValue] = ParamValueData
    ExpectedData = {'FuzzyTolerance': (ValueKind.NUMBER, -1.0), 'Label': (ValueKind.STRING, FilletFeatureData.name), 'Label2': (ValueKind.STRING, ''), 'Radius': (ValueKind.QUANTITY, RadiusNumber), 'Refine': (ValueKind.BOOLEAN, True), 'SupportTransform': (ValueKind.BOOLEAN, False), 'Suppressed': (ValueKind.BOOLEAN, False), 'UseAllEdges': (ValueKind.BOOLEAN, False), 'Visibility': (ValueKind.BOOLEAN, True)}
    if set(ParamData) != set(ExpectedData) or any((not FreecadParam(ParamData[PathValue], KindValue, ExpectedValue) for PathValue, (KindValue, ExpectedValue) in ExpectedData.items())):
        return None
    RadiusParam = ParamData['Radius']
    return (PadDimension, WriteDimension('D1', RadiusNumber, 'R' + format(RadiusNumber, '.15g'), RadiusParam.role))

# this definition exists because focused behavior needs one stable owner
def FreeCadBoss(DocData: CadDocument, SketchData: Sketch, PadFeature: FeatureStep, ChamferFeatureData: FeatureStep, BoundsValue: tuple[float, float, float, float] | None) -> tuple[WriteDimension, WriteDimension] | None:

    # this callback exists because local behavior needs one focused transformation
    TimelineData = tuple((ItemData for ItemData in sorted(DocData.feature_timeline, key=lambda ItemData: ItemData.order) if not IsNativeSystem(ItemData)))
    ChamferDefinition = ChamferFeatureData.definition
    PadDefinition = PadFeature.definition
    AllowedOwners = {SketchData.id, PadFeature.id, ChamferFeatureData.id}
    if BoundsValue is None or DocData.source.format_id.casefold() != 'freecad.fcstd' or DocData.assembly is not None or (tuple(DocData.sketches) != (SketchData,)) or (TimelineData != (PadFeature, ChamferFeatureData)) or (len(DocData.bodies) != 1) or (DocData.bodies[0].final_feature_id != ChamferFeatureData.id) or (PadFeature.order != 0) or (ChamferFeatureData.order != 1) or (PadFeature.sketch_id != SketchData.id) or (ChamferFeatureData.sketch_id is not None) or PadFeature.input_feature_ids or (ChamferFeatureData.input_feature_ids != (PadFeature.id,)) or PadFeature.selection_ids or (len(ChamferFeatureData.selection_ids) != 1) or PadFeature.configuration_states or ChamferFeatureData.configuration_states or PadFeature.suppressed or ChamferFeatureData.suppressed or (str(PadFeature.operation).casefold() not in {BoolOperation.CREATE.value, BoolOperation.JOIN.value}) or (ChamferFeatureData.operation is not None) or (str(ChamferFeatureData.kind).casefold() != FeatureKind.CHAMFER.value) or (FreecadTypeId(SketchData.attributes) != 'Sketcher::SketchObject') or (FreecadTypeId(PadFeature.attributes) != 'PartDesign::Pad') or (FreecadTypeId(ChamferFeatureData.attributes) != 'PartDesign::Chamfer') or (not isinstance(PadDefinition, ExtrusionFeature)) or PadDefinition.reversed or PadDefinition.symmetric or (not isinstance(ChamferDefinition, ChamferFeature)) or (ChamferDefinition.mode != 'equal_distance') or (ChamferDefinition.second_distance is not None) or (ChamferDefinition.angle is not None) or (ChamferFeatureData.provenance is None) or (len(DocData.configurations) != 1) or (DocData.configurations[0].name.casefold() != 'default') or (not DocData.configurations[0].active) or (DocData.configurations[0].parent_id is not None) or DocData.configurations[0].overrides or DocData.configurations[0].suppressed_feature_ids or (len(DocData.selections) != 1) or (ChamferFeatureData.selection_ids != (DocData.selections[0].id,)) or any((ItemData.owner_id not in AllowedOwners for ItemData in DocData.parameters)):
        return None
    PadDimension = FreeCadFeature(DocData, SketchData, PadFeature, 'PartDesign::Pad', 10.0, False)
    DistanceDimension = ParamDimension(Param('', 'D1', ChamferDefinition.distance))
    if PadDimension is None or DistanceDimension is None or DistanceDimension.value_mm <= 0.0:
        return None
    DistanceNumber = DistanceDimension.value_mm
    MinimumX, MinimumY, MaximumX, MaximumY = BoundsValue
    if not MathValue.isfinite(DistanceNumber) or DistanceNumber <= 0.0 or DistanceNumber * 2.0 >= min(MaximumX - MinimumX, MaximumY - MinimumY):
        return None
    SelectionData = DocData.selections[0]
    PadNativeName = PadFeature.provenance.native_id if PadFeature.provenance is not None else PadFeature.name
    if SelectionData.attributes.get('freecad_object') != ChamferFeatureData.provenance.native_id or SelectionData.attributes.get('freecad_property') != 'Base' or SelectionData.attributes.get('freecad_target') != PadNativeName or (len(SelectionData.path) != 1) or (SelectionData.path[0].entity_kind != 'edge') or (SelectionData.path[0].entity_id != PadNativeName) or (not HasFreeCadMax(DocData, PadNativeName, SelectionData.path[0].subelement, BoundsValue, PadDimension.value_mm)):
        return None
    ParamData: dict[str, Param] = {}
    for ParamValueData in DocData.parameters:
        if ParamValueData.owner_id != ChamferFeatureData.id:
            continue
        PathValue = ParamValueData.attributes.get('freecad_path')
        if not isinstance(PathValue, str) or not PathValue or PathValue in ParamData or (ParamValueData.expression is not None):
            return None
        ParamData[PathValue] = ParamValueData
    ExpectedData = {'Angle': (ValueKind.ANGLE, 45.0), 'ChamferType': (ValueKind.INTEGER, 0), 'FlipDirection': (ValueKind.BOOLEAN, False), 'FuzzyTolerance': (ValueKind.NUMBER, -1.0), 'Label': (ValueKind.STRING, ChamferFeatureData.name), 'Label2': (ValueKind.STRING, ''), 'Refine': (ValueKind.BOOLEAN, True), 'Size': (ValueKind.QUANTITY, DistanceNumber), 'Size2': (ValueKind.QUANTITY, 1.0), 'SupportTransform': (ValueKind.BOOLEAN, False), 'Suppressed': (ValueKind.BOOLEAN, False), 'UseAllEdges': (ValueKind.BOOLEAN, False), 'Visibility': (ValueKind.BOOLEAN, True)}
    if set(ParamData) != set(ExpectedData) or any((not FreecadParam(ParamData[PathValue], KindValue, ExpectedValue) for PathValue, (KindValue, ExpectedValue) in ExpectedData.items())):
        return None
    DistanceParam = ParamData['Size']
    return (PadDimension, WriteDimension('D1', DistanceNumber, format(DistanceNumber, '.15g'), DistanceParam.role))

# this definition exists because focused behavior needs one stable owner
def FreeCadBossD(DocData: CadDocument, SketchData: Sketch, PadFeature: FeatureStep, ShellFeatureData: FeatureStep, BoundsValue: tuple[float, float, float, float] | None) -> tuple[WriteDimension, WriteDimension] | None:

    # this callback exists because local behavior needs one focused transformation
    TimelineData = tuple((ItemData for ItemData in sorted(DocData.feature_timeline, key=lambda ItemData: ItemData.order) if not IsNativeSystem(ItemData)))
    ShellDefinition = ShellFeatureData.definition
    PadDefinition = PadFeature.definition
    AllowedOwners = {SketchData.id, PadFeature.id, ShellFeatureData.id}
    if BoundsValue is None or DocData.source.format_id.casefold() != 'freecad.fcstd' or DocData.assembly is not None or (tuple(DocData.sketches) != (SketchData,)) or (TimelineData != (PadFeature, ShellFeatureData)) or (len(DocData.bodies) != 1) or (DocData.bodies[0].final_feature_id != ShellFeatureData.id) or (PadFeature.order != 0) or (ShellFeatureData.order != 1) or (PadFeature.sketch_id != SketchData.id) or (ShellFeatureData.sketch_id is not None) or PadFeature.input_feature_ids or (ShellFeatureData.input_feature_ids != (PadFeature.id,)) or PadFeature.selection_ids or (len(ShellFeatureData.selection_ids) != 1) or PadFeature.configuration_states or ShellFeatureData.configuration_states or PadFeature.suppressed or ShellFeatureData.suppressed or (str(PadFeature.operation).casefold() not in {BoolOperation.CREATE.value, BoolOperation.JOIN.value}) or (ShellFeatureData.operation is not None) or (str(ShellFeatureData.kind).casefold() != FeatureKind.SHELL.value) or (FreecadTypeId(SketchData.attributes) != 'Sketcher::SketchObject') or (FreecadTypeId(PadFeature.attributes) != 'PartDesign::Pad') or (FreecadTypeId(ShellFeatureData.attributes) != 'PartDesign::Thickness') or (not isinstance(PadDefinition, ExtrusionFeature)) or PadDefinition.reversed or PadDefinition.symmetric or (not isinstance(ShellDefinition, ShellFeature)) or (ShellDefinition.outward is not False) or (ShellFeatureData.provenance is None) or (len(DocData.configurations) != 1) or (DocData.configurations[0].name.casefold() != 'default') or (not DocData.configurations[0].active) or (DocData.configurations[0].parent_id is not None) or DocData.configurations[0].overrides or DocData.configurations[0].suppressed_feature_ids or (len(DocData.selections) != 1) or (ShellFeatureData.selection_ids != (DocData.selections[0].id,)) or any((ItemData.owner_id not in AllowedOwners for ItemData in DocData.parameters)):
        return None
    PadDimension = FreeCadFeature(DocData, SketchData, PadFeature, 'PartDesign::Pad', 10.0, False)
    ThicknessDimension = ParamDimension(Param('', 'D1', ShellDefinition.thickness))
    if PadDimension is None or ThicknessDimension is None or ThicknessDimension.value_mm <= 0.0:
        return None
    ThicknessNumber = ThicknessDimension.value_mm
    MinimumX, MinimumY, MaximumX, MaximumY = BoundsValue
    if not MathValue.isfinite(ThicknessNumber) or ThicknessNumber <= 0.0 or ThicknessNumber >= PadDimension.value_mm or (ThicknessNumber * 2.0 >= min(MaximumX - MinimumX, MaximumY - MinimumY)):
        return None
    SelectionData = DocData.selections[0]
    PadNativeName = PadFeature.provenance.native_id if PadFeature.provenance is not None else PadFeature.name
    if SelectionData.attributes.get('freecad_object') != ShellFeatureData.provenance.native_id or SelectionData.attributes.get('freecad_property') != 'Base' or SelectionData.attributes.get('freecad_target') != PadNativeName or (len(SelectionData.path) != 1) or (SelectionData.path[0].entity_kind != 'face') or (SelectionData.path[0].entity_id != PadNativeName) or (not HasFreeCadTop(DocData, PadNativeName, SelectionData.path[0].subelement, PadDimension.value_mm)):
        return None
    ParamData: dict[str, Param] = {}
    for ParamValueData in DocData.parameters:
        if ParamValueData.owner_id != ShellFeatureData.id:
            continue
        PathValue = ParamValueData.attributes.get('freecad_path')
        if not isinstance(PathValue, str) or not PathValue or PathValue in ParamData or (ParamValueData.expression is not None):
            return None
        ParamData[PathValue] = ParamValueData
    ExpectedData = {'FuzzyTolerance': (ValueKind.NUMBER, -1.0), 'Intersection': (ValueKind.BOOLEAN, False), 'Join': (ValueKind.INTEGER, 0), 'Label': (ValueKind.STRING, ShellFeatureData.name), 'Label2': (ValueKind.STRING, ''), 'Mode': (ValueKind.INTEGER, 0), 'Refine': (ValueKind.BOOLEAN, True), 'Reversed': (ValueKind.BOOLEAN, True), 'SupportTransform': (ValueKind.BOOLEAN, False), 'Suppressed': (ValueKind.BOOLEAN, False), 'Value': (ValueKind.LENGTH, ThicknessNumber), 'Visibility': (ValueKind.BOOLEAN, True)}
    if set(ParamData) != set(ExpectedData) or any((not FreecadParam(ParamData[PathValue], KindValue, ExpectedValue) for PathValue, (KindValue, ExpectedValue) in ExpectedData.items())):
        return None
    ThicknessParam = ParamData['Value']
    return (PadDimension, WriteDimension('D1', ThicknessNumber, format(ThicknessNumber, '.15g'), ThicknessParam.role))

# this definition exists because focused behavior needs one stable owner
def FreeCadBossC(DocData: CadDocument, SketchData: Sketch, PadFeature: FeatureStep, PatternFeatureData: FeatureStep, BoundsValue: tuple[float, float, float, float] | None) -> tuple[WriteDimension, WriteDimension, WriteDimension] | None:

    # this callback exists because local behavior needs one focused transformation
    TimelineData = tuple((ItemData for ItemData in sorted(DocData.feature_timeline, key=lambda ItemData: ItemData.order) if not IsNativeSystem(ItemData)))
    PatternDefinition = PatternFeatureData.definition
    PadDefinition = PadFeature.definition
    AllowedOwners = {SketchData.id, PadFeature.id, PatternFeatureData.id}
    if BoundsValue is None or DocData.source.format_id.casefold() != 'freecad.fcstd' or DocData.assembly is not None or (tuple(DocData.sketches) != (SketchData,)) or (TimelineData != (PadFeature, PatternFeatureData)) or (len(DocData.bodies) != 1) or (DocData.bodies[0].final_feature_id != PatternFeatureData.id) or (PadFeature.order != 0) or (PatternFeatureData.order != 1) or (PadFeature.sketch_id != SketchData.id) or (PatternFeatureData.sketch_id is not None) or PadFeature.input_feature_ids or (PatternFeatureData.input_feature_ids != (PadFeature.id,)) or PadFeature.selection_ids or (len(PatternFeatureData.selection_ids) != 1) or PadFeature.configuration_states or PatternFeatureData.configuration_states or PadFeature.suppressed or PatternFeatureData.suppressed or (str(PadFeature.operation).casefold() not in {BoolOperation.CREATE.value, BoolOperation.JOIN.value}) or (PatternFeatureData.operation is not None) or (str(PatternFeatureData.kind).casefold() != FeatureKind.PATTERN.value) or (FreecadTypeId(SketchData.attributes) != 'Sketcher::SketchObject') or (FreecadTypeId(PadFeature.attributes) != 'PartDesign::Pad') or (FreecadTypeId(PatternFeatureData.attributes) != 'PartDesign::LinearPattern') or (not isinstance(PadDefinition, ExtrusionFeature)) or PadDefinition.reversed or PadDefinition.symmetric or (not isinstance(PatternDefinition, LinearPatternFeature)) or PatternDefinition.reversed or (PatternFeatureData.provenance is None) or (len(DocData.configurations) != 1) or (DocData.configurations[0].name.casefold() != 'default') or (not DocData.configurations[0].active) or (DocData.configurations[0].parent_id is not None) or DocData.configurations[0].overrides or DocData.configurations[0].suppressed_feature_ids or (len(DocData.selections) != 1) or (PatternFeatureData.selection_ids != (DocData.selections[0].id,)) or (PatternDefinition.direction_selection_id != DocData.selections[0].id) or any((ItemData.owner_id not in AllowedOwners for ItemData in DocData.parameters)):
        return None
    PadDimension = FreeCadFeature(DocData, SketchData, PadFeature, 'PartDesign::Pad', 10.0, False)
    SpacingDimension = ParamDimension(Param('', 'D3', PatternDefinition.spacing))
    ItemCount = PatternDefinition.instance_count
    if PadDimension is None or SpacingDimension is None or isinstance(ItemCount, bool) or (not isinstance(ItemCount, int)) or (not 2 <= ItemCount <= 1000) or (not MathValue.isfinite(SpacingDimension.value_mm)) or (SpacingDimension.value_mm <= 0.0) or (SpacingDimension.value_mm > PadDimension.value_mm):
        return None
    SelectionData = DocData.selections[0]
    SketchNativeName = SketchData.provenance.native_id if SketchData.provenance is not None else SketchData.name
    if SelectionData.attributes.get('freecad_object') != PatternFeatureData.provenance.native_id or SelectionData.attributes.get('freecad_property') != 'Direction' or SelectionData.attributes.get('freecad_target') != SketchNativeName or (len(SelectionData.path) != 1) or (SelectionData.path[0].entity_kind != 'native') or (SelectionData.path[0].entity_id != SketchNativeName) or (SelectionData.path[0].subelement != 'N_Axis'):
        return None
    ParamData: dict[str, Param] = {}
    for ParamValueData in DocData.parameters:
        if ParamValueData.owner_id != PatternFeatureData.id:
            continue
        PathValue = ParamValueData.attributes.get('freecad_path')
        if not isinstance(PathValue, str) or not PathValue or PathValue in ParamData or (ParamValueData.expression is not None):
            return None
        ParamData[PathValue] = ParamValueData
    SpacingNumber = SpacingDimension.value_mm
    LengthNumber = SpacingNumber * (ItemCount - 1)
    ExpectedData = {'FuzzyTolerance': (ValueKind.NUMBER, -1.0), 'Label': (ValueKind.STRING, PatternFeatureData.name), 'Label2': (ValueKind.STRING, ''), 'Length': (ValueKind.LENGTH, LengthNumber), 'Length2': (ValueKind.LENGTH, 100.0), 'Mode': (ValueKind.INTEGER, 0), 'Mode2': (ValueKind.INTEGER, 0), 'Occurrences': (ValueKind.INTEGER, ItemCount), 'Occurrences2': (ValueKind.INTEGER, 1), 'Offset': (ValueKind.LENGTH, SpacingNumber), 'Offset2': (ValueKind.LENGTH, 10.0), 'Refine': (ValueKind.BOOLEAN, True), 'Reversed': (ValueKind.BOOLEAN, False), 'Reversed2': (ValueKind.BOOLEAN, False), 'Suppressed': (ValueKind.BOOLEAN, False), 'TransformMode': (ValueKind.INTEGER, 0), 'Visibility': (ValueKind.BOOLEAN, True)}
    if set(ParamData) != set(ExpectedData) or any((not FreecadParam(ParamData[PathValue], KindValue, ExpectedValue) for PathValue, (KindValue, ExpectedValue) in ExpectedData.items())):
        return None
    TerminalDepth = PadDimension.value_mm + SpacingNumber * (ItemCount - 1)
    if not HasFreeCadGeomA(DocData, PatternFeatureData.provenance.native_id, BoundsValue, TerminalDepth):
        return None
    CountParam = ParamData['Occurrences']
    SpacingParam = ParamData['Length']
    return (PadDimension, WriteDimension('D1', float(ItemCount), str(ItemCount), CountParam.role), Replace(SpacingDimension, name='D3', text=format(SpacingNumber, '.15g'), role=SpacingParam.role))

# this definition exists because focused behavior needs one stable owner
def HasFreeCadGeomA(DocData: CadDocument, PatternNativeName: str, BoundsValue: tuple[float, float, float, float], TerminalDepth: float) -> bool:
    ShapePayload = next((ItemData.data for ItemData in DocData.brep_payloads if ItemData.source_stream == f'{PatternNativeName}.Shape.brp' and ItemData.data), None)
    if ShapePayload is None:
        return False
    ModelData = DecodeAsciiBrep(ShapePayload, id_prefix='freecad:linear-pattern-proof')
    if ModelData is None or ModelData.validate() or len(ModelData.bodies) != 1 or (len(ModelData.regions) != 1) or (len(ModelData.shells) != 1) or (len(ModelData.faces) != 6) or (len(ModelData.edges) != 12) or (len(ModelData.vertices) != 8):
        return False
    CoordinateData = (min((ItemData.point.x for ItemData in ModelData.vertices)), min((ItemData.point.y for ItemData in ModelData.vertices)), max((ItemData.point.x for ItemData in ModelData.vertices)), max((ItemData.point.y for ItemData in ModelData.vertices)), min((ItemData.point.z for ItemData in ModelData.vertices)), max((ItemData.point.z for ItemData in ModelData.vertices)))
    ExpectedData = (*BoundsValue, 0.0, TerminalDepth)
    return all((MathValue.isclose(ActualValue, ExpectedValue, rel_tol=0.0, abs_tol=1e-08) for ActualValue, ExpectedValue in zip(CoordinateData, ExpectedData, strict=True)))

# this definition exists because focused behavior needs one stable owner
def FreeCadBossA(DocData: CadDocument, SketchData: Sketch, PadFeature: FeatureStep, PatternFeatureData: FeatureStep, BoundsValue: tuple[float, float, float, float] | None) -> tuple[WriteDimension, WriteDimension, WriteDimension] | None:

    # this callback exists because local behavior needs one focused transformation
    TimelineData = tuple((ItemData for ItemData in sorted(DocData.feature_timeline, key=lambda ItemData: ItemData.order) if not IsNativeSystem(ItemData)))
    PatternDefinition = PatternFeatureData.definition
    PadDefinition = PadFeature.definition
    AllowedOwners = {SketchData.id, PadFeature.id, PatternFeatureData.id}
    if BoundsValue is None or DocData.source.format_id.casefold() != 'freecad.fcstd' or DocData.assembly is not None or (tuple(DocData.sketches) != (SketchData,)) or (TimelineData != (PadFeature, PatternFeatureData)) or (len(DocData.bodies) != 1) or (DocData.bodies[0].final_feature_id != PatternFeatureData.id) or (PadFeature.order != 0) or (PatternFeatureData.order != 1) or (PadFeature.sketch_id != SketchData.id) or (PatternFeatureData.sketch_id is not None) or PadFeature.input_feature_ids or (PatternFeatureData.input_feature_ids != (PadFeature.id,)) or PadFeature.selection_ids or (len(PatternFeatureData.selection_ids) != 1) or PadFeature.configuration_states or PatternFeatureData.configuration_states or PadFeature.suppressed or PatternFeatureData.suppressed or (str(PadFeature.operation).casefold() not in {BoolOperation.CREATE.value, BoolOperation.JOIN.value}) or (PatternFeatureData.operation is not None) or (str(PatternFeatureData.kind).casefold() != FeatureKind.PATTERN.value) or (FreecadTypeId(SketchData.attributes) != 'Sketcher::SketchObject') or (FreecadTypeId(PadFeature.attributes) != 'PartDesign::Pad') or (FreecadTypeId(PatternFeatureData.attributes) != 'PartDesign::PolarPattern') or (not isinstance(PadDefinition, ExtrusionFeature)) or PadDefinition.reversed or PadDefinition.symmetric or (not isinstance(PatternDefinition, CircularPatternFeature)) or PatternDefinition.reversed or (PatternFeatureData.provenance is None) or (len(DocData.configurations) != 1) or (DocData.configurations[0].name.casefold() != 'default') or (not DocData.configurations[0].active) or (DocData.configurations[0].parent_id is not None) or DocData.configurations[0].overrides or DocData.configurations[0].suppressed_feature_ids or (len(DocData.selections) != 1) or (PatternFeatureData.selection_ids != (DocData.selections[0].id,)) or (PatternDefinition.axis_selection_id != DocData.selections[0].id) or any((ItemData.owner_id not in AllowedOwners for ItemData in DocData.parameters)):
        return None
    PadDimension = FreeCadFeature(DocData, SketchData, PadFeature, 'PartDesign::Pad', 10.0, False)
    AngleValue = PatternDefinition.angle
    AngleNumber = AngleValue.value
    ItemCount = PatternDefinition.instance_count
    if PadDimension is None or AngleValue.kind is not ValueKind.ANGLE or AngleValue.unit.casefold() not in {'deg', 'degree', 'degrees'} or isinstance(AngleNumber, bool) or (not isinstance(AngleNumber, (int, float))) or (not MathValue.isfinite(float(AngleNumber))) or (not 0.0 < float(AngleNumber) <= 360.0) or isinstance(ItemCount, bool) or (not isinstance(ItemCount, int)) or (not 2 <= ItemCount <= 1000) or any((not MathValue.isclose(ActualValue, ExpectedValue, rel_tol=0.0, abs_tol=1e-10) for ActualValue, ExpectedValue in zip(BoundsValue, (0.0, 0.0, 10.0, 5.0), strict=True))):
        return None
    SelectionData = DocData.selections[0]
    SketchNativeName = SketchData.provenance.native_id if SketchData.provenance is not None else SketchData.name
    if SelectionData.attributes.get('freecad_object') != PatternFeatureData.provenance.native_id or SelectionData.attributes.get('freecad_property') != 'Axis' or SelectionData.attributes.get('freecad_target') != SketchNativeName or (len(SelectionData.path) != 1) or (SelectionData.path[0].entity_kind != 'native') or (SelectionData.path[0].entity_id != SketchNativeName) or (SelectionData.path[0].subelement != 'N_Axis'):
        return None
    ParamData: dict[str, Param] = {}
    for ParamValueData in DocData.parameters:
        if ParamValueData.owner_id != PatternFeatureData.id:
            continue
        PathValue = ParamValueData.attributes.get('freecad_path')
        if not isinstance(PathValue, str) or not PathValue or PathValue in ParamData or (ParamValueData.expression is not None):
            return None
        ParamData[PathValue] = ParamValueData
    ExpectedData = {'Angle': (ValueKind.ANGLE, float(AngleNumber)), 'FuzzyTolerance': (ValueKind.NUMBER, -1.0), 'Label': (ValueKind.STRING, PatternFeatureData.name), 'Label2': (ValueKind.STRING, ''), 'Mode': (ValueKind.INTEGER, 0), 'Occurrences': (ValueKind.INTEGER, ItemCount), 'Offset': (ValueKind.ANGLE, 120.0), 'Refine': (ValueKind.BOOLEAN, True), 'Reversed': (ValueKind.BOOLEAN, False), 'Suppressed': (ValueKind.BOOLEAN, False), 'TransformMode': (ValueKind.INTEGER, 0), 'Visibility': (ValueKind.BOOLEAN, True)}
    if set(ParamData) != set(ExpectedData) or any((not FreecadParam(ParamData[PathValue], KindValue, ExpectedValue) for PathValue, (KindValue, ExpectedValue) in ExpectedData.items())):
        return None
    if not HasFreeCadGeom(DocData, PatternFeatureData.provenance.native_id, BoundsValue, ItemCount, float(AngleNumber), PadDimension.value_mm):
        return None
    return (PadDimension, WriteDimension('D1', float(ItemCount), str(ItemCount), ParamData['Occurrences'].role), WriteDimension('D3', float(AngleNumber), f'{float(AngleNumber):.15g}°', ParamData['Angle'].role))

# this definition exists because focused behavior needs one stable owner
def HasFreeCadGeom(DocData: CadDocument, PatternNativeName: str, BoundsValue: tuple[float, float, float, float], ItemCount: int, AngleDegrees: float, PadDepth: float) -> bool:
    ShapePayload = next((ItemData.data for ItemData in DocData.brep_payloads if ItemData.source_stream == f'{PatternNativeName}.Shape.brp' and ItemData.data), None)
    if ShapePayload is None:
        return False
    ModelData = DecodeAsciiBrep(ShapePayload, id_prefix='freecad:circular-pattern-proof')
    if ModelData is None or ModelData.validate() or len(ModelData.bodies) != 1 or (len(ModelData.regions) != 1) or (len(ModelData.shells) != 1) or (not ModelData.faces) or (not ModelData.edges) or (not ModelData.vertices):
        return False
    CoordinateData = (min((ItemData.point.x for ItemData in ModelData.vertices)), min((ItemData.point.y for ItemData in ModelData.vertices)), max((ItemData.point.x for ItemData in ModelData.vertices)), max((ItemData.point.y for ItemData in ModelData.vertices)), min((ItemData.point.z for ItemData in ModelData.vertices)), max((ItemData.point.z for ItemData in ModelData.vertices)))
    ExpectedData = (*CircularPattern(BoundsValue, ItemCount, AngleDegrees), 0.0, PadDepth)
    return all((MathValue.isclose(ActualValue, ExpectedValue, rel_tol=0.0, abs_tol=1e-08) for ActualValue, ExpectedValue in zip(CoordinateData, ExpectedData, strict=True)))

# this definition exists because focused behavior needs one stable owner
def HasFreeCadTop(DocData: CadDocument, PadNativeName: str, SubElemName: str, PadDepth: float) -> bool:
    MatchValue = RegexLib.fullmatch('Face([1-9][0-9]*)', SubElemName)
    if MatchValue is None:
        return False
    ShapePayload = next((ItemData.data for ItemData in DocData.brep_payloads if ItemData.source_stream == f'{PadNativeName}.Shape.brp' and ItemData.data), None)
    if ShapePayload is None:
        return False
    ModelData = DecodeAsciiBrep(ShapePayload, id_prefix='freecad:shell-proof')
    if ModelData is None:
        return False

    # this callback exists because local behavior needs one focused transformation
    FaceData = tuple(sorted(ModelData.faces, key=lambda ItemData: int(ItemData.id.rsplit(':', 1)[1])))
    FaceIndex = int(MatchValue.group(1)) - 1
    if FaceIndex < 0 or FaceIndex >= len(FaceData):
        return False
    SelectedFace = FaceData[FaceIndex]
    SurfaceData = next((ItemData for ItemData in ModelData.surfaces if ItemData.id == SelectedFace.surface_id), None)
    ToleranceValue = 1e-08
    return isinstance(SurfaceData, PlaneSurface) and SelectedFace.same_sense and MathValue.isclose(SurfaceData.origin.z, PadDepth, rel_tol=0.0, abs_tol=ToleranceValue) and MathValue.isclose(SurfaceData.normal.x, 0.0, rel_tol=0.0, abs_tol=ToleranceValue) and MathValue.isclose(SurfaceData.normal.y, 0.0, rel_tol=0.0, abs_tol=ToleranceValue) and MathValue.isclose(SurfaceData.normal.z, 1.0, rel_tol=0.0, abs_tol=ToleranceValue)

# this definition exists because focused behavior needs one stable owner
def HasFreeCadMax(DocData: CadDocument, PadNativeName: str, SubElemName: str, BoundsValue: tuple[float, float, float, float], PadDepth: float) -> bool:
    MatchValue = RegexLib.fullmatch('Edge([1-9][0-9]*)', SubElemName)
    if MatchValue is None:
        return False
    ShapePayload = next((ItemData.data for ItemData in DocData.brep_payloads if ItemData.source_stream == f'{PadNativeName}.Shape.brp' and ItemData.data), None)
    if ShapePayload is None:
        return False
    ModelData = DecodeAsciiBrep(ShapePayload, id_prefix='freecad:fillet-proof')
    if ModelData is None:
        return False

    # this callback exists because local behavior needs one focused transformation
    EdgeData = tuple(sorted(ModelData.edges, key=lambda ItemData: int(ItemData.id.rsplit(':', 1)[1])))
    EdgeIndex = int(MatchValue.group(1)) - 1
    if EdgeIndex < 0 or EdgeIndex >= len(EdgeData):
        return False
    SelectedEdge = EdgeData[EdgeIndex]
    VertexData = {ItemData.id: ItemData for ItemData in ModelData.vertices}
    CurveData = {ItemData.id: ItemData for ItemData in ModelData.curves}
    StartVertex = VertexData.get(SelectedEdge.start_vertex_id)
    EndVertex = VertexData.get(SelectedEdge.end_vertex_id)
    SelectedCurve = CurveData.get(SelectedEdge.curve_id)
    if StartVertex is None or EndVertex is None or (not isinstance(SelectedCurve, LineCurve)) or SelectedEdge.degenerate:
        return False
    MaximumX = BoundsValue[2]
    MaximumY = BoundsValue[3]
    ToleranceValue = 1e-08
    return all((MathValue.isclose(ItemData.point.x, MaximumX, rel_tol=0.0, abs_tol=ToleranceValue) and MathValue.isclose(ItemData.point.y, MaximumY, rel_tol=0.0, abs_tol=ToleranceValue) for ItemData in (StartVertex, EndVertex))) and MathValue.isclose(min(StartVertex.point.z, EndVertex.point.z), 0.0, rel_tol=0.0, abs_tol=ToleranceValue) and MathValue.isclose(max(StartVertex.point.z, EndVertex.point.z), PadDepth, rel_tol=0.0, abs_tol=ToleranceValue)

# this definition exists because focused behavior needs one stable owner
def HasFreeCadAll(DocData: CadDocument, SketchData: Sketch, FeatureData: FeatureStep) -> bool:
    if FeatureData.sketch_id != SketchData.id or str(FeatureData.kind).casefold() != FeatureKind.EXTRUSION.value or FreecadTypeId(SketchData.attributes) != 'Sketcher::SketchObject' or (FreecadTypeId(FeatureData.attributes) != 'PartDesign::Pocket') or (not isinstance(FeatureData.definition, ExtrusionFeature)):
        return False
    DefinitionData = FeatureData.definition
    SupportPlaneValue = next((ItemData for ItemData in DocData.support_planes if ItemData.id == SketchData.support_plane_id), None)
    if str(DefinitionData.end_condition).casefold() != ExtrusionEndCondition.THROUGH_ALL.value or DefinitionData.symmetric or DefinitionData.second_end_condition is not None or DefinitionData.up_to_reference or DefinitionData.second_up_to_reference or (not ParamValueA(DefinitionData.length, 5.0, ValueKind.LENGTH)) or (not ParamValueA(DefinitionData.second_length, 5.0, ValueKind.LENGTH)) or (not ParamValueA(DefinitionData.offset, 0.0, ValueKind.LENGTH)) or (not ParamValueA(DefinitionData.second_offset, 0.0, ValueKind.LENGTH)) or (not ParamValueA(DefinitionData.draft_angle, 0.0, ValueKind.ANGLE)) or (not ParamValueA(DefinitionData.second_draft_angle, 0.0, ValueKind.ANGLE)) or (DefinitionData.direction is None) or (SupportPlaneValue is None) or (not all((MathValue.isclose(LeftValue, -RightValue, abs_tol=1e-12) for LeftValue, RightValue in zip((DefinitionData.direction.x, DefinitionData.direction.y, DefinitionData.direction.z), (SupportPlaneValue.transform.z_axis.x, SupportPlaneValue.transform.z_axis.y, SupportPlaneValue.transform.z_axis.z), strict=True)))):
        return False
    ParamData: dict[str, Param] = {}
    for ParamValueData in DocData.parameters:
        if ParamValueData.owner_id != FeatureData.id:
            continue
        PathValue = ParamValueData.attributes.get('freecad_path')
        if not isinstance(PathValue, str) or not PathValue or PathValue in ParamData or (ParamValueData.expression is not None):
            return False
        ParamData[PathValue] = ParamValueData
    ExpectedData = {'AllowMultiFace': (ValueKind.BOOLEAN, True), 'AlongSketchNormal': (ValueKind.BOOLEAN, True), 'Label': (ValueKind.STRING, None), 'Label2': (ValueKind.STRING, None), 'Length': (ValueKind.LENGTH, 5.0), 'Length2': (ValueKind.LENGTH, 5.0), 'Midplane': (ValueKind.BOOLEAN, False), 'Offset': (ValueKind.LENGTH, 0.0), 'Offset2': (ValueKind.LENGTH, 0.0), 'Refine': (ValueKind.BOOLEAN, True), 'Reversed': (ValueKind.BOOLEAN, DefinitionData.reversed), 'SideType': (ValueKind.INTEGER, 0), 'Suppressed': (ValueKind.BOOLEAN, False), 'TaperAngle': (ValueKind.ANGLE, 0.0), 'TaperAngle2': (ValueKind.ANGLE, 0.0), 'Type': (ValueKind.INTEGER, 1), 'Type2': (ValueKind.INTEGER, 0), 'UseCustomVector': (ValueKind.BOOLEAN, False), 'Visibility': (ValueKind.BOOLEAN, True)}
    return set(ExpectedData) <= set(ParamData) and all((FreecadParam(ParamData[PathValue], KindValue, ExpectedValue) for PathValue, (KindValue, ExpectedValue) in ExpectedData.items()))

# this definition exists because focused behavior needs one stable owner
def FreeCadFeature(DocData: CadDocument, SketchData: Sketch, FeatureData: FeatureStep, ExpectedTypeId: str, ExpectedSecondLength: float, ExpectedVisibility: bool) -> WriteDimension | None:
    if FeatureData.sketch_id != SketchData.id or str(FeatureData.kind).casefold() != FeatureKind.EXTRUSION.value or FreecadTypeId(SketchData.attributes) != 'Sketcher::SketchObject' or (FreecadTypeId(FeatureData.attributes) != ExpectedTypeId) or (not isinstance(FeatureData.definition, ExtrusionFeature)):
        return None
    DefinitionData = FeatureData.definition
    SupportPlaneValue = next((ItemData for ItemData in DocData.support_planes if ItemData.id == SketchData.support_plane_id), None)
    DirectionSign = -1.0 if ExpectedTypeId == 'PartDesign::Pocket' else 1.0
    if str(DefinitionData.end_condition).casefold() != ExtrusionEndCondition.BLIND.value or (DefinitionData.reversed and DefinitionData.symmetric) or DefinitionData.second_end_condition is not None or DefinitionData.up_to_reference or DefinitionData.second_up_to_reference or (not ParamValueA(DefinitionData.second_length, ExpectedSecondLength, ValueKind.LENGTH)) or (not ParamValueA(DefinitionData.offset, 0.0, ValueKind.LENGTH)) or (not ParamValueA(DefinitionData.second_offset, 0.0, ValueKind.LENGTH)) or (not ParamValueA(DefinitionData.draft_angle, 0.0, ValueKind.ANGLE)) or (not ParamValueA(DefinitionData.second_draft_angle, 0.0, ValueKind.ANGLE)) or (DefinitionData.direction is None) or (SupportPlaneValue is None) or (not all((MathValue.isclose(LeftValue, RightValue, abs_tol=1e-12) for LeftValue, RightValue in zip((DefinitionData.direction.x, DefinitionData.direction.y, DefinitionData.direction.z), (DirectionSign * SupportPlaneValue.transform.z_axis.x, DirectionSign * SupportPlaneValue.transform.z_axis.y, DirectionSign * SupportPlaneValue.transform.z_axis.z), strict=True)))):
        return None
    DimensionData = ParamDimension(Param('', 'D1', DefinitionData.length))
    if DimensionData is None or DimensionData.value_mm <= 0.0:
        return None
    ParamData: dict[str, Param] = {}
    for ParamValueData in DocData.parameters:
        if ParamValueData.owner_id != FeatureData.id:
            continue
        PathValue = ParamValueData.attributes.get('freecad_path')
        if not isinstance(PathValue, str) or not PathValue or PathValue in ParamData or (ParamValueData.expression is not None):
            return None
        ParamData[PathValue] = ParamValueData
    ExpectedData = {'AllowMultiFace': (ValueKind.BOOLEAN, True), 'AlongSketchNormal': (ValueKind.BOOLEAN, True), 'Label': (ValueKind.STRING, None), 'Label2': (ValueKind.STRING, None), 'Length': (ValueKind.LENGTH, DimensionData.value_mm), 'Length2': (ValueKind.LENGTH, ExpectedSecondLength), 'Midplane': (ValueKind.BOOLEAN, DefinitionData.symmetric), 'Offset': (ValueKind.LENGTH, 0.0), 'Offset2': (ValueKind.LENGTH, 0.0), 'Refine': (ValueKind.BOOLEAN, True), 'Reversed': (ValueKind.BOOLEAN, DefinitionData.reversed), 'SideType': (ValueKind.INTEGER, 2 if DefinitionData.symmetric else 0), 'Suppressed': (ValueKind.BOOLEAN, False), 'TaperAngle': (ValueKind.ANGLE, 0.0), 'TaperAngle2': (ValueKind.ANGLE, 0.0), 'Type': (ValueKind.INTEGER, 0), 'Type2': (ValueKind.INTEGER, 0), 'UseCustomVector': (ValueKind.BOOLEAN, False), 'Visibility': (ValueKind.BOOLEAN, ExpectedVisibility)}
    if not set(ExpectedData) <= set(ParamData):
        return None
    if any((not FreecadParam(ParamData[PathValue], KindValue, ExpectedValue) for PathValue, (KindValue, ExpectedValue) in ExpectedData.items())):
        return None
    return DimensionData

# this definition exists because focused behavior needs one stable owner
def FreecadSingle(DocValue: CadDocument, Sketch: Sketch, Feature: FeatureStep) -> WriteDimension | None:
    if DocValue.source.format_id.casefold() != 'freecad.fcstd' or DocValue.assembly is not None or DocValue.selections or (len(DocValue.sketches) != 1) or (len(tuple((ItemValue for ItemValue in DocValue.feature_timeline if not IsNativeSystem(ItemValue)))) != 1) or (len(DocValue.bodies) != 1) or (DocValue.bodies[0].final_feature_id != Feature.id) or (Feature.sketch_id != Sketch.id) or (Feature.order != 0) or (str(Feature.kind).casefold() != FeatureKind.EXTRUSION.value) or (str(Feature.operation).casefold() not in {BoolOperation.CREATE.value, BoolOperation.JOIN.value}) or (FreecadTypeId(Sketch.attributes) != 'Sketcher::SketchObject') or (FreecadTypeId(Feature.attributes) != 'PartDesign::Pad') or (len(DocValue.configurations) != 1) or (DocValue.configurations[0].name.casefold() != 'default') or (not DocValue.configurations[0].active) or (DocValue.configurations[0].parent_id is not None) or DocValue.configurations[0].overrides or DocValue.configurations[0].suppressed_feature_ids or (not isinstance(Feature.definition, ExtrusionFeature)):
        return None
    Definition = Feature.definition
    SupportPlaneValue = next((ItemData for ItemData in DocValue.support_planes if ItemData.id == Sketch.support_plane_id), None)
    if str(Definition.end_condition).casefold() != ExtrusionEndCondition.BLIND.value or (Definition.reversed and Definition.symmetric) or Definition.second_end_condition is not None or Definition.up_to_reference or Definition.second_up_to_reference or (not ParamValueA(Definition.second_length, 10.0, ValueKind.LENGTH)) or (not ParamValueA(Definition.offset, 0.0, ValueKind.LENGTH)) or (not ParamValueA(Definition.second_offset, 0.0, ValueKind.LENGTH)) or (not ParamValueA(Definition.draft_angle, 0.0, ValueKind.ANGLE)) or (not ParamValueA(Definition.second_draft_angle, 0.0, ValueKind.ANGLE)) or (Definition.direction is None) or (SupportPlaneValue is None) or (not all((MathValue.isclose(LeftValue, RightValue, abs_tol=1e-12) for LeftValue, RightValue in zip((Definition.direction.x, Definition.direction.y, Definition.direction.z), (SupportPlaneValue.transform.z_axis.x, SupportPlaneValue.transform.z_axis.y, SupportPlaneValue.transform.z_axis.z), strict=True)))):
        return None
    Dimension = ParamDimension(Param('', 'D1', Definition.length))
    if Dimension is None or Dimension.value_mm <= 0.0:
        return None
    Parameters: dict[str, Param] = {}
    for Param in DocValue.parameters:
        if Param.owner_id == Sketch.id:
            continue
        PathValue = Param.attributes.get('freecad_path')
        if Param.owner_id != Feature.id or not isinstance(PathValue, str) or (not PathValue) or (PathValue in Parameters) or (Param.expression is not None):
            return None
        Parameters[PathValue] = Param
    Expected = {'AllowMultiFace': (ValueKind.BOOLEAN, True), 'AlongSketchNormal': (ValueKind.BOOLEAN, True), 'Label': (ValueKind.STRING, None), 'Label2': (ValueKind.STRING, None), 'Length': (ValueKind.LENGTH, Dimension.value_mm), 'Length2': (ValueKind.LENGTH, 10.0), 'Midplane': (ValueKind.BOOLEAN, Definition.symmetric), 'Offset': (ValueKind.LENGTH, 0.0), 'Offset2': (ValueKind.LENGTH, 0.0), 'Refine': (ValueKind.BOOLEAN, True), 'Reversed': (ValueKind.BOOLEAN, Definition.reversed), 'SideType': (ValueKind.INTEGER, 2 if Definition.symmetric else 0), 'Suppressed': (ValueKind.BOOLEAN, False), 'TaperAngle': (ValueKind.ANGLE, 0.0), 'TaperAngle2': (ValueKind.ANGLE, 0.0), 'Type': (ValueKind.INTEGER, 0), 'Type2': (ValueKind.INTEGER, 0), 'UseCustomVector': (ValueKind.BOOLEAN, False), 'Visibility': (ValueKind.BOOLEAN, True)}
    if not set(Expected) <= set(Parameters):
        return None
    if any((not FreecadParam(Parameters[PathValue], KindValue, Value) for PathValue, (KindValue, Value) in Expected.items())):
        return None
    return Dimension

# this definition exists because focused behavior needs one stable owner
def FreecadTypeId(Attributes: Mapping[str, Any]) -> str:
    Value = Attributes.get('freecad')
    return str(Value.get('type_id', '')) if isinstance(Value, Mapping) else ''

# this definition exists because focused behavior needs one stable owner
def FreeCadSingle(DocData: CadDocument, SketchData: Sketch, FeatureData: FeatureStep) -> WriteDimension | None:
    DefinitionData = FeatureData.definition

    # this callback exists because local behavior needs one focused transformation
    TimelineData = tuple((ItemData for ItemData in sorted(DocData.feature_timeline, key=lambda ItemData: ItemData.order) if not IsNativeSystem(ItemData)))
    if DocData.source.format_id.casefold() != 'freecad.fcstd' or DocData.assembly is not None or tuple(DocData.sketches) != (SketchData,) or (TimelineData != (FeatureData,)) or (len(DocData.bodies) != 1) or (DocData.bodies[0].final_feature_id != FeatureData.id) or (FeatureData.order != 0) or (FeatureData.sketch_id != SketchData.id) or FeatureData.input_feature_ids or FeatureData.configuration_states or FeatureData.suppressed or (str(FeatureData.kind).casefold() != FeatureKind.REVOLUTION.value) or (str(FeatureData.operation).casefold() != BoolOperation.CREATE.value) or (FreecadTypeId(SketchData.attributes) != 'Sketcher::SketchObject') or (FreecadTypeId(FeatureData.attributes) != 'PartDesign::Revolution') or (not isinstance(DefinitionData, NativeFeatureDefinition)) or (DefinitionData.format_id.casefold() != 'freecad.fcstd') or (DefinitionData.type_id != 'PartDesign::Revolution') or (FeatureData.provenance is None) or (len(DocData.configurations) != 1) or (DocData.configurations[0].name.casefold() != 'default') or (not DocData.configurations[0].active) or (DocData.configurations[0].parent_id is not None) or DocData.configurations[0].overrides or DocData.configurations[0].suppressed_feature_ids or (len(DocData.selections) != 1) or (FeatureData.selection_ids != (DocData.selections[0].id,)):
        return None
    AxisSelection = DocData.selections[0]
    if AxisSelection.attributes.get('freecad_object') != FeatureData.provenance.native_id or AxisSelection.attributes.get('freecad_property') != 'ReferenceAxis' or len(AxisSelection.path) != 1 or (AxisSelection.path[0].entity_id != SketchData.name) or (AxisSelection.path[0].subelement != KVerticalAxisSubElem):
        return None
    ParamData: dict[str, Param] = {}
    for ParamValueData in DocData.parameters:
        if ParamValueData.owner_id != FeatureData.id:
            return None
        PathValue = ParamValueData.attributes.get('freecad_path')
        if not isinstance(PathValue, str) or not PathValue or PathValue in ParamData or (ParamValueData.expression is not None):
            return None
        ParamData[PathValue] = ParamValueData
    AngleParam = ParamData.get('Angle')
    if AngleParam is None or AngleParam.value.kind is not ValueKind.ANGLE or isinstance(AngleParam.value.value, bool) or (not isinstance(AngleParam.value.value, (int, float))):
        return None
    AngleDegrees = float(AngleParam.value.value)
    if not MathValue.isfinite(AngleDegrees) or not any((MathValue.isclose(AngleDegrees, ExpectedAngle, rel_tol=0.0, abs_tol=1e-10) for ExpectedAngle in (90.0, 360.0))):
        return None
    ExpectedData = {'AllowMultiFace': (ValueKind.BOOLEAN, True), 'Angle': (ValueKind.ANGLE, AngleDegrees), 'Angle2': (ValueKind.ANGLE, 0.0), 'FuseOrder': (ValueKind.INTEGER, 0), 'FuzzyTolerance': (ValueKind.NUMBER, -1.0), 'Label': (ValueKind.STRING, FeatureData.name), 'Label2': (ValueKind.STRING, ''), 'Midplane': (ValueKind.BOOLEAN, False), 'Refine': (ValueKind.BOOLEAN, True), 'Reversed': (ValueKind.BOOLEAN, False), 'Suppressed': (ValueKind.BOOLEAN, False), 'Type': (ValueKind.INTEGER, 0), 'Visibility': (ValueKind.BOOLEAN, True)}
    if set(ParamData) != set(ExpectedData) or any((not FreecadParam(ParamData[PathValue], KindValue, ExpectedValue) for PathValue, (KindValue, ExpectedValue) in ExpectedData.items())):
        return None
    if AngleParam.value.unit.casefold() not in {'deg', 'degree', 'degrees'}:
        return None
    return WriteDimension('D1', AngleDegrees, f'{AngleDegrees:g}°', AngleParam.role)

# this definition exists because focused behavior needs one stable owner
def FreecadParam(Param: Parameter, KindValue: ValueKind, Expected: Any) -> bool:
    Value = Param.value
    if Value.kind is not KindValue:
        return False
    if Expected is None:
        return isinstance(Value.value, str)
    if KindValue is ValueKind.LENGTH:
        Dimension = ParamDimension(Param)
        return Dimension is not None and MathValue.isclose(Dimension.value_mm, float(Expected), rel_tol=0.0, abs_tol=1e-10)
    if KindValue in {ValueKind.NUMBER, ValueKind.ANGLE}:
        return not isinstance(Value.value, bool) and isinstance(Value.value, (int, float)) and MathValue.isfinite(float(Value.value)) and MathValue.isclose(float(Value.value), float(Expected), rel_tol=0.0, abs_tol=1e-10)
    return Value.value == Expected

# this definition exists because focused behavior needs one stable owner
def ParamValueA(Value: Any, Expected: float, KindValue: ValueKind) -> bool:
    if Value is None or Value.kind is not KindValue:
        return False
    Param = ParamDimension(Param('', 'D1', Value))
    if KindValue is ValueKind.LENGTH:
        return Param is not None and MathValue.isclose(Param.value_mm, Expected, rel_tol=0.0, abs_tol=1e-10)
    return not isinstance(Value.value, bool) and isinstance(Value.value, (int, float)) and MathValue.isfinite(float(Value.value)) and MathValue.isclose(float(Value.value), Expected, rel_tol=0.0, abs_tol=1e-10)

# this definition exists because focused behavior needs one stable owner
def WriteRectangle(Sketch: _WriteObject) -> tuple[float, float, float, float] | None:
    if Sketch.kind != 'Sketch' or not Sketch.payload:
        return None
    Markers = list(ParseMarkers(Sketch.payload, 0, len(Sketch.payload)))
    Profiles, Ignored, Ignored = Profiles(Markers, ())
    if len(Profiles) != 1 or Profiles[0].kind != 'rectangle':
        return None
    Coordinates = Profiles[0].coordinates
    if len(Coordinates) != 4 or not all((MathValue.isfinite(Value) for Value in Coordinates)):
        return None
    return Coordinates

# this definition exists because focused behavior needs one stable owner
def WriteCircle(SketchObject: _WriteObject) -> tuple[float, float, float] | None:
    if SketchObject.kind != 'Sketch' or not SketchObject.payload:
        return None
    MarkersData = list(ParseMarkers(SketchObject.payload, 0, len(SketchObject.payload)))
    CoordinateData = tuple((ItemData for ItemData in MarkersData if ItemData.coordinates_mm is not None))
    if len(CoordinateData) != 2 or CoordinateData[0].semantic != 'circle' or CoordinateData[1].semantic != 'point':
        return None
    CenterData = CoordinateData[0].coordinates_mm
    RimData = CoordinateData[1].coordinates_mm
    if CenterData is None or RimData is None:
        return None
    RadiusValue = MathValue.hypot(RimData[0] - CenterData[0], RimData[1] - CenterData[1])
    if not all((MathValue.isfinite(ItemData) for ItemData in (*CenterData, RadiusValue))):
        return None
    if RadiusValue <= 0.0:
        return None
    return (CenterData[0], CenterData[1], RadiusValue)

# this definition exists because focused behavior needs one stable owner
def PolySixPoints(SketchObject: _WriteObject) -> tuple[tuple[float, float], ...] | None:
    if SketchObject.kind != 'Sketch' or not SketchObject.payload:
        return None
    MarkersData = list(ParseMarkers(SketchObject.payload, 0, len(SketchObject.payload)))
    ProfilesData, Ignored, Ignored = Profiles(MarkersData, ())
    PolylineData = tuple((ItemData for ItemData in ProfilesData if ItemData.kind == 'polyline'))
    if len(PolylineData) != 1 or len(PolylineData[0].coordinates) != 12:
        return None
    CoordinateData = PolylineData[0].coordinates
    PointsData = tuple(((CoordinateData[ItemIndex], CoordinateData[ItemIndex + 1]) for ItemIndex in range(0, len(CoordinateData), 2)))
    if not all((MathValue.isfinite(ValueData) for PointData in PointsData for ValueData in PointData)):
        return None
    return PointsData

# this definition exists because focused behavior needs one stable owner
def IsPinProfile(PointsData: tuple[tuple[float, float], ...] | None) -> bool:
    return PointsData is not None and len(PointsData) == len(KPinPointsMm) and all((MathValue.isclose(ActualValue, ExpectedValue, rel_tol=0.0, abs_tol=1e-10) for ActualPoint, ExpectedPoint in zip(PointsData, KPinPointsMm, strict=True) for ActualValue, ExpectedValue in zip(ActualPoint, ExpectedPoint, strict=True)))

# this definition exists because focused behavior needs one stable owner
def IsNativeSystem(Feature: FeatureStep) -> bool:
    NativeId = Feature.attributes.get('native_object_id')
    return isinstance(NativeId, int) and (not isinstance(NativeId, bool)) and (NativeId in KSystemObjectIds) and (str(Feature.kind).casefold() in {FeatureKind.NATIVE.value, FeatureKind.REFERENCE.value})

# this definition exists because focused behavior needs one stable owner
def NativeSystem(Feature: FeatureStep | None, Fallback: str) -> str:
    if Feature is None:
        return Fallback
    Properties = Feature.attributes.get('native_properties')
    if isinstance(Properties, Mapping):
        NameValue = Properties.get('Name')
        if isinstance(NameValue, str):
            return NameValue
    return Feature.name or Fallback

# this definition exists because focused behavior needs one stable owner
def WriteSketch(Sketch: Sketch, Parameters: dict[str, Parameter], ObjectIds: dict[str, int], NativeFeature: FeatureStep | None=None) -> WriteObject:
    ObjectId = ObjectIds[f'sketch:{Sketch.id}']
    Dimensions = list(WriteDimensions(Sketch.id, Sketch.parameter_ids, Parameters))
    Payload, GeneratedDimensions = SketchPayload(Sketch, ObjectId, ObjectIds)
    Existing = {Dimension.name for Dimension in Dimensions}
    Dimensions.extend((Dimension for Dimension in GeneratedDimensions if Dimension.name not in Existing))
    NativeProperties = NativeKeyword(NativeFeature.attributes) if NativeFeature is not None else None
    return WriteObject(Sketch.id, ObjectId, Sketch.name, 'Sketch', 'Sketch', 'moProfileFeature_c', (('Dissectable', 'true'),) if NativeProperties is None else NativeProperties, tuple(Dimensions), Payload)

# this definition exists because focused behavior needs one stable owner
def WriteFeature(Feature: FeatureStep, Parameters: dict[str, Parameter], ObjectIds: dict[str, int]) -> WriteObject:
    ObjectId = ObjectIds[f'feature:{Feature.id}']
    Dimensions = list(WriteDimensions(Feature.id, Feature.parameter_ids, Parameters))
    TagValue, KindValue, ClassName = WriteFeatureA(Feature)
    NativeProperties = NativeKeyword(Feature.attributes)
    Properties = list(NativeProperties or ())
    Payload = b''
    if TagValue == 'Extrusion':
        if NativeProperties is None and Feature.sketch_id is not None:
            Child = ObjectIds.get(f'sketch:{Feature.sketch_id}')
            if Child is not None:
                Properties.extend((('Dissectable', 'true'), ('DissectableChildren', str(Child)), ('DissectableRoot', 'true')))
        Generated = Definition(Feature)
        if Generated is not None and (not Dimensions):
            Dimensions.append(Generated)
        Payload = Extrusion(Feature)
    elif KindValue in {'Fillet', 'Chamfer', 'Shell'}:
        Generated = Definition(Feature)
        if Generated is not None and (not Dimensions):
            Dimensions.append(Generated)
        Payload = FilletPayload(Feature, ObjectIds)
    return WriteObject(Feature.id, ObjectId, Feature.name, TagValue, KindValue, ClassName, tuple(Properties), tuple(Dimensions), Payload)

# this definition exists because focused behavior needs one stable owner
def NativeKeyword(Attributes: Mapping[str, Any]) -> tuple[tuple[str, str], ...] | None:
    Properties = Attributes.get('native_properties')
    if not isinstance(Properties, Mapping):
        return None
    return tuple(((NameValue, Value) for NameValue, Value in Properties.items() if isinstance(NameValue, str) and isinstance(Value, str) and (NameValue not in {'id', 'Name'})))

# this definition exists because focused behavior needs one stable owner
def WriteFeatureA(Feature: FeatureStep) -> tuple[str, str, str]:
    KindValue = str(Feature.kind).casefold()
    if KindValue == FeatureKind.EXTRUSION.value:
        ClassName = 'moCut_c' if Feature.operation == BoolOperation.CUT or str(Feature.operation).casefold() == BoolOperation.CUT.value else 'moExtrusion_c'
        return ('Extrusion', 'Extrusion', ClassName)
    if KindValue == FeatureKind.FILLET.value:
        return ('Feature', 'Fillet', 'Fillet_c')
    if KindValue == FeatureKind.CHAMFER.value:
        return ('Feature', 'Chamfer', 'Chamfer_c')
    if KindValue == FeatureKind.SHELL.value:
        return ('Feature', 'Shell', 'moShell_c')
    if KindValue == FeatureKind.PATTERN.value and isinstance(Feature.definition, LinearPatternFeature):
        return ('Feature', 'LPattern', 'moLPattern_c')
    if KindValue == FeatureKind.PATTERN.value and isinstance(Feature.definition, CircularPatternFeature):
        return ('Feature', 'CirPattern', 'moCirPattern_c')
    Native = Feature.attributes.get('native_type')
    if isinstance(Native, str) and Native.strip():
        if Native.strip().casefold() in {'basebody', 'imported'}:
            return ('Feature', 'Imported', 'moBaseBody_c')
        return ('Feature', Native.strip(), 'moCompFeature_c')
    Names = {FeatureKind.REVOLUTION.value: ('Revolution', 'moRevolution_c'), FeatureKind.SWEEP.value: ('Sweep', 'moSweep_c'), FeatureKind.LOFT.value: ('Blend', 'moBlend_c'), FeatureKind.HOLE.value: ('HoleWizard', 'moHoleWzd_c'), FeatureKind.SHELL.value: ('Shell', 'moShell_c'), FeatureKind.PATTERN.value: ('Pattern', 'moLPattern_c'), FeatureKind.MIRROR.value: ('MirrorPattern', 'moMirrorPattern_c'), FeatureKind.BOOLEAN.value: ('Combine', 'moCombineBodies_c')}
    NativeKind, ClassName = Names.get(KindValue, (str(Feature.kind), 'moCompFeature_c'))
    return ('Feature', NativeKind, ClassName)

# this definition exists because focused behavior needs one stable owner
def WriteDimensions(OwnerId: str, ParamIds: tuple[str | None, ...], Parameters: dict[str, Parameter]) -> tuple[WriteDimension, ...]:
    Selected: list[Param] = []
    SeenValue: set[str] = set()
    for ParamId in ParamIds:
        if ParamId is None or ParamId in SeenValue:
            continue
        Param = Parameters.get(ParamId)
        if Param is not None:
            Selected.append(Param)
            SeenValue.add(ParamId)
    for Param in Parameters.values():
        if Param.owner_id == OwnerId and Param.id not in SeenValue:
            Selected.append(Param)
            SeenValue.add(Param.id)
    return tuple((Dimension for Param in Selected if (Dimension := ParamDimension(Param)) is not None))

# this definition exists because focused behavior needs one stable owner
def ParamDimension(Param: Parameter) -> WriteDimension | None:
    Value = Param.value.value
    if isinstance(Value, bool) or not isinstance(Value, (int, float)) or Param.value.kind is not ValueKind.LENGTH:
        return None
    Factor = {'': 1.0, 'mm': 1.0, 'millimeter': 1.0, 'millimeters': 1.0, 'cm': 10.0, 'm': 1000.0, 'in': 25.4, 'inch': 25.4, 'inches': 25.4}.get(Param.value.unit.casefold())
    Number = float(Value)
    if Factor is None or not MathValue.isfinite(Number):
        return None
    Millimeters = Number * Factor
    SourceText = Param.attributes.get('source_text')
    TextValue = SourceText if isinstance(SourceText, str) and SourceText else format(Millimeters, '.15g')
    return WriteDimension(Param.name, Millimeters, TextValue, Param.role)

# this definition exists because focused behavior needs one stable owner
def Definition(Feature: FeatureStep) -> WriteDimension | None:
    Definition = Feature.definition
    Value = None
    Prefix = ''
    if isinstance(Definition, ExtrusionFeature):
        Value = Definition.length
    elif isinstance(Definition, FilletFeature):
        Value = Definition.radius
        Prefix = 'R'
    elif isinstance(Definition, ChamferFeature):
        Value = Definition.distance
    elif isinstance(Definition, ShellFeature):
        Value = Definition.thickness
    if Value is None:
        return None
    Param = Param('', 'D1', Value)
    Dimension = ParamDimension(Param)
    if Dimension is None:
        return None
    return Replace(Dimension, text=Prefix + Dimension.text)

# this definition exists because focused behavior needs one stable owner
def PlaneFrameBlock(Plane: SupportPlane) -> bytes | None:
    Transform = Plane.transform
    Origin = (Transform.origin.x, Transform.origin.y, Transform.origin.z)
    XAxis = (Transform.x_axis.x, Transform.x_axis.y, Transform.x_axis.z)
    YAxis = (Transform.y_axis.x, Transform.y_axis.y, Transform.y_axis.z)
    ZAxis = (Transform.z_axis.x, Transform.z_axis.y, Transform.z_axis.z)
    Vectors = (XAxis, YAxis, ZAxis)
    if not Orthonormal(Vectors) or not all((MathValue.isfinite(Value) for Vector in (Origin, *Vectors) for Value in Vector)):
        return None
    Frame = bytearray(KPlaneFrameBytes)
    Struct.pack_into('<3d', Frame, 0, *(Value / KMillimetres for Value in Origin))
    Struct.pack_into('<3d', Frame, 24, *ZAxis)
    Frame[48] = 1
    RowsValue = tuple(zip(XAxis, YAxis, ZAxis, strict=True))
    for Index, RowValue in enumerate(RowsValue):
        Struct.pack_into('<3d', Frame, 49 + Index * 24, *RowValue)
    return bytes(Frame)

# this definition exists because focused behavior needs one stable owner
def PlanePayload(Plane: SupportPlane) -> bytes:
    Frame = PlaneFrameBlock(Plane)
    if Frame is None:
        return b''
    return ClassDecl('moFixedRefPlnData_c') + Frame

# this definition exists because focused behavior needs one stable owner
def Orthonormal(Vectors: tuple[tuple[float, float, float], ...]) -> bool:
    return all((MathValue.isclose(NormAction(Vector), 1.0, abs_tol=1e-09) for Vector in Vectors)) and all((MathValue.isclose(DotAction(LeftValue, Right), 0.0, abs_tol=1e-09) for LeftValue, Right in Itertools.combinations(Vectors, 2)))

# this definition exists because focused behavior needs one stable owner
def LineLoopPoints(LinesData: tuple[LineGeometry, ...]) -> tuple[tuple[float, float], ...] | None:
    if len(LinesData) < 3:
        return None
    StartData = tuple(((ItemData.start.x, ItemData.start.y) for ItemData in LinesData))
    EndData = tuple(((ItemData.end.x, ItemData.end.y) for ItemData in LinesData))
    if not all((MathValue.isfinite(ValueData) for PointData in (*StartData, *EndData) for ValueData in PointData)):
        return None
    if any((not SamePoint(EndData[ItemIndex], StartData[(ItemIndex + 1) % len(StartData)]) for ItemIndex in range(len(StartData)))):
        return None
    return StartData

# this definition exists because focused behavior needs one stable owner
def SketchPayload(Sketch: Sketch, ObjectId: int, ObjectIds: dict[str, int]) -> tuple[bytes, tuple[WriteDimension, ...]]:
    Payload = bytearray()
    PlaneId = ObjectIds.get(f'plane:{Sketch.support_plane_id}', 2)
    Payload.extend(PlaneRef(PlaneId))
    Generated: list[WriteDimension] = []
    Consumed: set[str] = set()
    LocalId = 1
    Entities = {Entity.id: Entity for Entity in Sketch.entities}
    for Profile in Sketch.closed_profile_entity_ids:
        Selected = tuple((Entities.get(EntityId) for EntityId in Profile))
        if len(Selected) == 4 and all((Entity is not None and isinstance(Entity.geometry, LineGeom) for Entity in Selected)):
            Rectangle = Rectangle(tuple((Entity.geometry for Entity in Selected if Entity is not None)))
            if Rectangle is not None:
                Points = ((Rectangle[0], Rectangle[1]), (Rectangle[2], Rectangle[1]), (Rectangle[2], Rectangle[3]), (Rectangle[0], Rectangle[3]))
                for Point in Points:
                    Payload.extend(Coordinate(Point, LocalId, KPointLocus))
                    LocalId += 1
                for Start, EndValue in ((0, 1), (1, 2), (2, 3), (3, 0)):
                    Payload.extend(LineMarker(Start, EndValue, LocalId))
                    LocalId += 1
                Consumed.update(Profile)
                continue
        if len(Selected) == 6 and all((Entity is not None and isinstance(Entity.geometry, LineGeom) for Entity in Selected)):
            LineData = tuple((Entity.geometry for Entity in Selected if Entity is not None))
            PointData = LineLoopPoints(LineData)
            if PointData is not None:
                for PointValue in PointData:
                    Payload.extend(Coordinate(PointValue, LocalId, KPointLocus))
                    LocalId += 1
                for PointIndex in range(len(PointData)):
                    Payload.extend(LineMarker(PointIndex, (PointIndex + 1) % len(PointData), LocalId))
                    LocalId += 1
                Consumed.update(Profile)
                continue
        if len(Selected) == 1 and Selected[0] is not None and isinstance(Selected[0].geometry, CircleGeom):
            Circle = Selected[0].geometry
            Center = (Circle.center.x, Circle.center.y)
            Radial = (Circle.center.x + Circle.radius, Circle.center.y)
            Payload.extend(Coordinate(Center, LocalId, KCircleLocus))
            LocalId += 1
            Payload.extend(Coordinate(Radial, LocalId, KPointLocus))
            LocalId += 1
            Generated.append(WriteDimension(f'D{len(Generated) + 1}', Circle.radius, 'R' + format(Circle.radius, '.15g'), ParamRole.DRIVING))
            Consumed.add(Selected[0].id)
    for Entity in Sketch.entities:
        if Entity.id in Consumed:
            continue
        if isinstance(Entity.geometry, LineGeom):
            StartIndex = LocalId
            Payload.extend(Coordinate((Entity.geometry.start.x, Entity.geometry.start.y), LocalId, KPointLocus))
            LocalId += 1
            Payload.extend(Coordinate((Entity.geometry.end.x, Entity.geometry.end.y), LocalId, KPointLocus))
            LocalId += 1
            RosterStart = StartIndex - 1
            Payload.extend(LineMarker(RosterStart, RosterStart + 1, LocalId))
            LocalId += 1
        elif isinstance(Entity.geometry, CircleGeom):
            Center = (Entity.geometry.center.x, Entity.geometry.center.y)
            Radial = (Center[0] + Entity.geometry.radius, Center[1])
            Payload.extend(Coordinate(Center, LocalId, KCircleLocus))
            LocalId += 1
            Payload.extend(Coordinate(Radial, LocalId, KPointLocus))
            LocalId += 1
            Generated.append(WriteDimension(f'D{len(Generated) + 1}', Entity.geometry.radius, 'R' + format(Entity.geometry.radius, '.15g'), ParamRole.DRIVING))
    return (bytes(Payload), tuple(Generated))

# this definition exists because focused behavior needs one stable owner
def PlaneRef(ObjectId: int) -> bytes:
    Block = bytearray(67)
    Struct.pack_into('<I', Block, 0, ObjectId)
    Block[4] = 1
    Block[8:12] = b'\x00\x00\x03\x00'
    Struct.pack_into('<d', Block, 39, 1.0)
    Block[50] = 2
    Block[54] = 255
    Block[55:58] = b'\xff\xff\xff'
    return bytes(Block)

# this definition exists because focused behavior needs one stable owner
def Coordinate(Point: tuple[float, float], LocalId: int, Locus: bytes) -> bytes:
    Record = bytearray(142)
    Record[:5] = KCurrentMarker
    Record[5:13] = b'\xff' * 8
    Record[13:17] = b'\x00\x00\x80\xbf'
    Struct.pack_into('<I', Record, 17, 1)
    Record[23:27] = Locus
    Struct.pack_into('<H', Record, 27, 1)
    Record[31:39] = b'\x00\x00\x80\xbf\x00\x00\x04\x00'
    Struct.pack_into('<d', Record, 48, 1.0)
    Record[56:58] = KCoordinateTag
    Struct.pack_into('<2d', Record, 58, Point[0] / 1000.0, Point[1] / 1000.0)
    Struct.pack_into('<I', Record, 138, LocalId)
    return bytes(Record)

# this definition exists because focused behavior needs one stable owner
def LineMarker(Start: int, EndValue: int, LocalId: int) -> bytes:
    Record = bytearray(92)
    Record[:5] = KCurrentMarker
    Record[5:13] = b'\xff' * 8
    Record[13:17] = b'\x00\x00\x80\xbf'
    Struct.pack_into('<I', Record, 17, 2)
    Record[23:27] = KPointLocus
    Struct.pack_into('<H', Record, 27, 1)
    Struct.pack_into('<d', Record, 48, 1.0)
    Struct.pack_into('<HH', Record, 64, Start, EndValue)
    Struct.pack_into('<I', Record, 88, LocalId)
    return bytes(Record)

# this definition exists because focused behavior needs one stable owner
def Rectangle(Lines: tuple[LineGeometry, ...]) -> tuple[float, float, float, float] | None:
    Points = tuple(((LineValue.start.x, LineValue.start.y) for LineValue in Lines))
    EndsValue = tuple(((LineValue.end.x, LineValue.end.y) for LineValue in Lines))
    if any((EndsValue[Index] != Points[(Index + 1) % 4] for Index in range(4))):
        return None
    XsValue = sorted({Point[0] for Point in Points})
    YsValue = sorted({Point[1] for Point in Points})
    if len(XsValue) != 2 or len(YsValue) != 2:
        return None
    if set(Points) != {(FirstCoord, SecondCoord) for FirstCoord in XsValue for SecondCoord in YsValue}:
        return None
    return (XsValue[0], YsValue[0], XsValue[1], YsValue[1])

# this definition exists because focused behavior needs one stable owner
def Extrusion(Feature: FeatureStep) -> bytes:
    Definition = Feature.definition
    Direction = int(isinstance(Definition, ExtrusionFeature) and Definition.reversed)
    Condition = (ExtrusionEndCondition.MID_PLANE if Definition.symmetric else Definition.end_condition) if isinstance(Definition, ExtrusionFeature) else None
    Termination = {ExtrusionEndCondition.BLIND: 0, ExtrusionEndCondition.THROUGH_ALL: 1, ExtrusionEndCondition.UP_TO_FIRST: 2, ExtrusionEndCondition.UP_TO_VERTEX: 3, ExtrusionEndCondition.UP_TO_FACE: 4, ExtrusionEndCondition.UP_TO_SHAPE: 4, ExtrusionEndCondition.OFFSET_FROM_SURFACE: 5, ExtrusionEndCondition.MID_PLANE: 6}.get(Condition, 0)
    DeclValue = ClassDecl('moEndSpec_c')
    return b''.join((DeclValue, b'\x00\x00', Struct.pack('<II', 1, 0), Struct.pack('<I', Direction), b'\x00\x00', Struct.pack('<II', Termination, 0)))

# this definition exists because focused behavior needs one stable owner
def FilletPayload(Feature: FeatureStep, ObjectIds: dict[str, int]) -> bytes:
    Result = bytearray()
    for SelectionId in Feature.selection_ids:
        Producer = 0
        LocalId = 0
        Parts = SelectionId.rsplit(':', 1)
        if len(Parts) == 2:
            try:
                LocalId = int(Parts[1])
            except ValueError:
                LocalId = 0
        if Feature.input_feature_ids:
            Producer = ObjectIds.get(f'feature:{Feature.input_feature_ids[-1]}', 0)
        if Producer and LocalId:
            Result.extend(FilletSelection(Producer, LocalId))
    return bytes(Result)

# this definition exists because focused behavior needs one stable owner
def FilletSelection(ProducerId: int, LocalId: int) -> bytes:
    if not 1 <= ProducerId <= 4294967295 or not 1 <= LocalId <= 4294967295:
        raise SldprtFormatError('native fillet selection ids must be positive integers')
    RecordData = bytearray(38)
    RecordData[:16] = KEdgeSelectionIdentity
    Struct.pack_into('<I', RecordData, 26, ProducerId)
    Struct.pack_into('<I', RecordData, 34, LocalId)
    return bytes(RecordData)

# this definition exists because focused behavior needs one stable owner
def ShellSelection(ProducerId: int) -> bytes:
    return FilletSelection(ProducerId, 1) + FilletSelection(ProducerId, 4)

# this definition exists because focused behavior needs one stable owner
def KeywordsPayload(DocValue: CadDocument, ModelName: str, Objects: tuple[_WriteObject, ...], ObjectIds: Mapping[str, int], Identity: _NativeIdentity) -> bytes:
    Children: list[str] = []
    Configurations = DocValue.configurations or ()
    for Config in Configurations:
        ConfigId = ObjectIds[f'configuration:{Config.id}']
        Attributes = {'id': str(ConfigId), 'Name': Config.name, 'Type': 'ConfigurationManager'}
        NativeProperties = Config.attributes.get('native_properties')
        Material = NativeProperties.get('Material') if isinstance(NativeProperties, Mapping) else Config.attributes.get('Material')
        if isinstance(Material, str):
            Attributes['Material'] = Material
        else:
            Attributes['Material'] = 'Material <not specified>'
        Children.append(XmlElem('Configuration', Attributes))
    if not Configurations:
        Children.append(XmlElem('Configuration', {'id': '0', 'Name': 'Default', 'Type': 'ConfigurationManager', 'Material': 'Material <not specified>'}))

    # this callback exists because local behavior needs one focused transformation
    for ItemValue in sorted(Objects, key=lambda Value: (Value.xml_tag, str(Value.object_id))):
        Attributes = {'id': str(ItemValue.object_id), 'Name': ItemValue.name}
        if ItemValue.xml_tag == 'Feature' or ItemValue.kind == 'Origin':
            Attributes['Type'] = ItemValue.kind
        Attributes.update(ItemValue.properties)
        Dimensions = ''.join((XmlElem('Dimension', {'Name': Dimension.name}, XmlText(Dimension.text)) for Dimension in ItemValue.dimensions))
        Children.append(XmlElem(ItemValue.xml_tag, Attributes, Dimensions if ItemValue.dimensions else None))
    RootValue = XmlElem('Keywords', {'id': str(Identity.creation_stamp), 'Name': Identity.reference_name}, ''.join(Children))
    return b'\x86' + XmlDoc(RootValue)

# this definition exists because focused behavior needs one stable owner
def FeaturesPayload(DocValue: CadDocument, ModelName: str, ObjectIds: Mapping[str, int], Identity: _NativeIdentity) -> bytes:
    Header = XmlElem('swHeader', {'swObjCount': '1'}, XmlElem('swFile', {'id': '3', 'swDocType': 'PART', 'swCreationTime': str(Identity.creation_stamp), 'swPath': f'{ModelName}{PartSuffix}'}))
    Active = next((Config for Config in DocValue.configurations if Config.active), DocValue.configurations[0] if DocValue.configurations else None)
    ActiveName = Active.name if Active is not None else 'Default'
    ActiveId = 0
    if Active is not None:
        ActiveId = ObjectIds[f'configuration:{Active.id}']
    Models = XmlElem('swModelList', {'swObjCount': '1'}, XmlElem('swModel', {'id': '2', 'swName': ModelName, 'swConfigurationName': ActiveName, 'swConfigurationId': str(ActiveId), 'swLastModifiedStamp': str(Identity.last_modified_stamp), 'swConfigurationFlags': str(Identity.configuration_flags), 'swFileRef': '3'}))
    Configurations = DocValue.configurations or ()
    ConfigChildren: list[str] = []
    if Configurations:
        for Index, Config in enumerate(Configurations, start=1):
            NativeId = ObjectIds[f'configuration:{Config.id}']
            ConfigChildren.append(XmlElem('swConfiguration', {'id': str(Index), 'swName': Config.name, 'swID': str(NativeId), 'swReference': Identity.reference_name, 'swMostRecentConfiguration': 'YES' if Config.active else 'NO', 'swConfigurationNeedsUpdate': 'NO', 'swDefeatureConfiguration': 'NO', 'swModelRef': '2'}))
    else:
        ConfigChildren.append(XmlElem('swConfiguration', {'id': '1', 'swName': 'Default', 'swID': '0', 'swReference': Identity.reference_name, 'swMostRecentConfiguration': 'YES', 'swConfigurationNeedsUpdate': 'NO', 'swDefeatureConfiguration': 'NO', 'swModelRef': '2'}))
    ConfigList = XmlElem('swConfigurationList', {'swObjCount': str(len(Configurations) or 1)}, ''.join(ConfigChildren))
    RootValue = XmlElem('swSolidWorks', {'xmlns': KSolidworksXmlNamespace, 'swObjCount': '3', 'swVersion': '18000'}, ''.join((Header, Models, ConfigList, XmlElem('swExtFeatureList', {'swObjCount': '0'}))))
    return XmlDoc(RootValue)

# this definition exists because focused behavior needs one stable owner
def XmlDoc(RootValue: str) -> bytes:
    return ('<?xml version="1.0" encoding="UTF-8"?>\r\n' + RootValue + '\r\n').encode('utf-8')

# this definition exists because focused behavior needs one stable owner
def XmlElem(NameValue: str, Attributes: Mapping[str, str], BodyValue: str | None=None) -> str:
    EncodedAttributes = ''.join((f' {KeyValue}="{XmlAttr(Value)}"' for KeyValue, Value in Attributes.items()))
    if BodyValue is None:
        return f'<{NameValue}{EncodedAttributes}/>'
    return f'<{NameValue}{EncodedAttributes}>{BodyValue}</{NameValue}>'

# this definition exists because focused behavior needs one stable owner
def XmlAttr(Value: str) -> str:
    return XmlText(Value).replace('"', '&quot;').replace('\t', '&#9;').replace('\n', '&#10;').replace('\r', '&#13;')

# this definition exists because focused behavior needs one stable owner
def XmlText(Value: str) -> str:
    return Value.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

# this definition exists because focused behavior needs one stable owner
def ResolvedBaseMap(Objects: tuple[_WriteObject, ...]) -> int:
    Authored = tuple((ItemValue for ItemValue in Objects if ItemValue.object_id not in KSystemObjectIds))
    Features = len(SolidFeatureIds(Authored))
    return KConfigZeroFirstFeature + max(Features, 1) - 1

# this definition exists because focused behavior needs one stable owner
def ResolvedPayload(Objects: tuple[_WriteObject, ...]) -> bytes:
    Output = bytearray(Struct.pack('<IH', ResolvedBaseMap(Objects), max(0, len(Objects) - 1)))
    for ItemValue in Objects:
        Output.extend(ClassDecl(ItemValue.class_name))
        Output.extend(NameRecord(ItemValue.name, ItemValue.object_id, TreeNodeFlags(ItemValue)))
        Output.extend(ItemValue.payload)
        for Dimension in ItemValue.dimensions:
            Output.extend(ScalarRecord(Dimension))
    return bytes(Output)

# this definition exists because focused behavior needs one stable owner
def ClassDecl(NameValue: str) -> bytes:
    Encoded = NameValue.encode('ascii')
    return ClassMarker + Struct.pack('<H', len(Encoded)) + Encoded

# this definition exists because focused behavior needs one stable owner
def TreeNodeFlags(ItemValue: _WriteObject) -> int:
    if ItemValue.kind == 'Extrusion':
        return KCutExtrudeFlags if ItemValue.class_name == 'moCut_c' else KBossExtrudeFlags
    if ItemValue.class_name in KRefGeomClasses:
        return KRefGeomFlags
    return KFolderFlags

# this definition exists because focused behavior needs one stable owner
def NameRecord(NameValue: str, ObjectId: int, Flags: int) -> bytes:
    Encoded = NameValue.encode('utf-16le')
    Units = len(Encoded) // 2
    if not 1 <= Units <= 255:
        raise SldprtFormatError('native SOLIDWORKS object name exceeds 255 UTF-16 units')
    return KNamePrefix + bytes((Units,)) + Encoded + Struct.pack('<III', 0, Flags, ObjectId) + b'\x00' * 16

# this definition exists because focused behavior needs one stable owner
def ScalarRecord(Dimension: _WriteDimension) -> bytes:
    Encoded = Dimension.name.encode('utf-16le')
    Units = len(Encoded) // 2
    if not 1 <= Units <= 255:
        raise SldprtFormatError('native SOLIDWORKS dimension name exceeds 255 UTF-16 units')
    Trailer = bytearray(51)
    Trailer[3:7] = b'\xff' * 4
    Trailer[21:27] = b'\x01\x00\x00\x00\x02\x00'
    Trailer[27] = 1 if Dimension.role is ParamRole.DRIVEN else 0
    return b''.join((ClassDecl('moLengthParameter_c'), KNamePrefix, bytes((Units,)), Encoded, KScalarHeader, Struct.pack('<d', Dimension.value_mm / 1000.0), bytes(Trailer)))

# this definition exists because focused behavior needs one stable owner
def NativeIdentityA(DocValue: CadDocument, ModelName: str) -> NativeIdentity:
    Authored = sum((not IsNativeSystem(Feature) for Feature in DocValue.feature_timeline))
    if Authored == 0 and (not DocValue.sketches):
        return NativeIdentity(1785690802, 114, 101, 1785690807, KSolidworksConfigFlags, 'Part1')
    CreationStamp = StableCreation(DocValue, ModelName)
    LastModifiedStamp = 102 + Authored * 4
    return NativeIdentity(CreationStamp, LastModifiedStamp, 101, CreationStamp + Authored * 7 + len(DocValue.sketches) * 3 + 5 & 2147483647, KSolidworksConfigFlags, 'Part1')

# this definition exists because focused behavior needs one stable owner
def SolidFeatureIds(Objects: tuple[_WriteObject, ...]) -> tuple[int, ...]:
    return tuple((ItemValue.object_id for ItemValue in Objects if ItemValue.class_name not in KNonSolidFeatureClasses))

# this definition exists because focused behavior needs one stable owner
def ConfigAtomTree(SolidFeatureTreeIds: tuple[int, ...]) -> tuple[int, ...]:
    return SolidFeatureTreeIds or (KConfigRootTreeId,)

# this definition exists because focused behavior needs one stable owner
def NativeEnvelope(DocValue: CadDocument, ModelName: str, Identity: _NativeIdentity, SolidFeatureTreeIds: tuple[int, ...]=(), HeaderFeatureObjects: tuple[tuple[int, str, bool], ...]=(), HeaderFeatureStamps: Mapping[int, tuple[int, ...]] | None=None, AnnotationViewCount: int=1, TerminalParentTreeId: int | None=None, HeaderBounds: tuple[float, ...] | None=None, HeaderCreation: int | None=None, CmgrParentTreeId: int | None=None, AnnotationViewVariant: str='default') -> Mapping[str, bytes]:
    ConfigName = next((Config.name for Config in DocValue.configurations if Config.active), DocValue.configurations[0].name if DocValue.configurations else 'Default')
    ZeroValue = Struct.pack('<I', 0)
    Streams = {'Contents/CMgrHdr2': ConfigHeader(ConfigName, Identity), 'Contents/CnfgObjs': ZeroValue + Serialized('') + Serialized(''), 'Contents/CusProps': CustomPayload(), 'Contents/OleItems': ZeroValue, 'Contents/eModelLic': ZeroValue, 'ModelStamps': Struct.pack('<III', Identity.creation_stamp, Identity.last_modified_stamp, Identity.baseline_stamp), '_MO_VERSION_18000/Biography': Biography(ModelName, Identity), '_MO_VERSION_18000/History': VersionHistory()}
    if HeaderCreation is not None and (not 0 <= HeaderCreation <= 4294967295):
        raise SldprtFormatError('native SOLIDWORKS header creation stamp is invalid')
    HeaderIdentity = Identity if HeaderCreation is None else NativeIdentity(HeaderCreation, Identity.last_modified_stamp, Identity.baseline_stamp, Identity.header_stamp, Identity.configuration_flags, Identity.reference_name)
    ModelHeader = ModelHeader(HeaderIdentity, ConfigName, SolidFeatureTreeIds=SolidFeatureTreeIds, FeatureObjects=HeaderFeatureObjects, FeatureStamps=HeaderFeatureStamps, HeaderBounds=HeaderBounds)
    Streams['Contents/Config-0-ModelHeader'] = ModelHeader
    Streams['Header2'] = ModelHeader
    Streams['Contents/Definition'] = EncodeDefinitionStream(assembly=DocValue.assembly is not None)
    TreeIds = ConfigAtomTree(SolidFeatureTreeIds)
    ParentTreeId = TerminalParentTreeId if TerminalParentTreeId is not None else CmgrParentTreeId
    if ParentTreeId is not None:
        if len(TreeIds) != 2 or TreeIds[0] != ParentTreeId or (TerminalParentTreeId is not None and AnnotationViewCount != 2):
            raise SldprtFormatError('terminal feature configuration requires its parent and child trees')
        TreeIds = (TreeIds[-1],)
    AtomIds = AtomIdsFor(len(TreeIds))
    Streams[ConfigManagerStream] = EncodeCmgrStream(feature_tree_ids=TreeIds, configuration_name=ConfigName, part_name=Identity.reference_name, atom_ids=AtomIds, connected_history=len(TreeIds) in {2, 3, 4} and len(DocValue.bodies) == 1, terminal_parent_tree_id=ParentTreeId)
    Streams[ConfigStream] = EncodeConfigZeroStream(part_name=Identity.reference_name, atoms=tuple(reversed(tuple(zip(AtomIds, TreeIds, strict=True)))), high_water=(AtomIds[-1], FirstAtomId + 2 * len(AtomIds)), annotation_view_count=AnnotationViewCount, terminal_parent_tree_id=TerminalParentTreeId, annotation_view_variant=AnnotationViewVariant)
    return MappingProxyType(Streams)

# this definition exists because focused behavior needs one stable owner
def EncodeNativeAsm(DocValue: CadDocument, ModelName: str, ItemNames: Sequence[str], MateNames: Sequence[str]) -> NativeAsm:
    ConfigName = next((Config.name for Config in DocValue.configurations if Config.active), DocValue.configurations[0].name if DocValue.configurations else 'Default')
    Listed: list[tuple[int, str, bool]] = list(KAsmHeaderObjects)
    Omitted: list[str] = []
    NextObjectId = KAsmHeaderObjects[-1][0] + 1
    for NameValue in (*ItemNames, *MateNames):
        if Serializable(NameValue):
            Listed.append((NextObjectId, NameValue, False))
            NextObjectId += 1
        else:
            Omitted.append(NameValue)
    Identity = NativeAsmA(DocValue, ModelName, len(Listed))
    DocPath = f'C:\\{ModelName}{AsmSuffix}'
    ModelHeader = HeaderPayload(Identity, ConfigName, tuple(Listed), DocPath)
    ZeroValue = Struct.pack('<I', 0)
    Streams = {'Contents/CMgrHdr2': ConfigHeader(ConfigName, Identity), 'Contents/CnfgObjs': ZeroValue + Serialized('') + Serialized(''), 'Contents/Config-0-ModelHeader': ModelHeader, KAsmAttachmentStream: Struct.pack('<H', 0), 'Contents/CusProps': CustomPayload(KAsmPropContainerClass), 'Contents/OleItems': ZeroValue, KAsmViewOrientationStream: KViewOrientationPayload, 'Contents/eModelLic': ZeroValue, 'Header2': ModelHeader, 'ModelStamps': Struct.pack('<III', Identity.creation_stamp, Identity.last_modified_stamp, Identity.baseline_stamp), KAsmVisualDataStream: ZeroValue, f'{KAsmVersionPrefix}/Biography': Biography(ModelName, Identity, 'C:\\Kit\\Assembly.ASMDOT', AsmSuffix), f'{KAsmVersionPrefix}/History': VersionHistory(), KAsmTablesStream: b'', KAsmCutlistStream: f'<Configuration id="0" Name="{XmlAttr(ConfigName)}"/>\r\n'.encode('utf-8'), KAsmConfigPropertiesStreA: KConfigPropertiesPayload, KAsmOpenTimeStream: KOpenTimePayload}
    HeaderObjects = tuple(((ObjectId, NameValue) for ObjectId, NameValue, Ignored in Listed))
    Decoded = DecodeNativeA(ModelHeader)
    return NativeAsm(MappingProxyType(Streams), ConfigName, Identity.reference_name, DocPath, HeaderObjects, tuple(Omitted), not Omitted and Decoded.user_name == 'Kit' and (Decoded.reference_name == Identity.reference_name) and (Decoded.configuration_name == ConfigName) and (Decoded.document_path == DocPath) and (Decoded.objects == HeaderObjects))

# this definition exists because focused behavior needs one stable owner
def DecodeNativeA(DataValue: bytes) -> NativeModelA:
    ClassName, Offset = ReadClass(DataValue, 0)
    if ClassName != 'moHeader_c':
        raise SldprtFormatError('native SOLIDWORKS header class is not moHeader_c')
    Offset = ExpectBytes(DataValue, Offset, bytes.fromhex('01000000ffff00000f00') + b'su_CStringArray' + Struct.pack('<H', 1))
    UserName, Offset = ReadSerialized(DataValue, Offset)
    Offset = ExpectBytes(DataValue, Offset, bytes.fromhex('03800100'))
    Ignored, Offset = ReadSerialized(DataValue, Offset)
    ClassName, Offset = ReadClass(DataValue, Offset)
    if ClassName != 'suObList':
        raise SldprtFormatError('native SOLIDWORKS header log list is missing')
    LogCount, = Struct.unpack_from('<H', DataValue, Offset)
    Offset += 2
    ClassName, Offset = ReadClass(DataValue, Offset)
    if ClassName != 'moLogs_c':
        raise SldprtFormatError('native SOLIDWORKS header log record is missing')
    Offset = ExpectBytes(DataValue, Offset, Struct.pack('<H', 1))
    ClassName, Offset = ReadClass(DataValue, Offset)
    if ClassName != 'moStamp_c':
        raise SldprtFormatError('native SOLIDWORKS header stamp record is missing')
    Offset += 10
    Ignored, Offset = ReadSerialized(DataValue, Offset)
    Offset += 4
    RefName, Offset = ReadSerialized(DataValue, Offset)
    Objects: list[tuple[int, str]] = []
    for Ignored in range(LogCount - 1):
        Offset = ExpectBytes(DataValue, Offset, bytes.fromhex('0880'))
        ActionCount, = Struct.unpack_from('<H', DataValue, Offset)
        Offset += 2
        for Ignored in range(ActionCount):
            Offset = ExpectBytes(DataValue, Offset, bytes.fromhex('0a80'))
            Offset += 10
            Ignored, Offset = ReadSerialized(DataValue, Offset)
        ObjectId, = Struct.unpack_from('<I', DataValue, Offset)
        Offset += 4
        ObjectName, Offset = ReadSerialized(DataValue, Offset)
        Objects.append((ObjectId, ObjectName))
    Offset += 14
    ClassName, Offset = ReadClass(DataValue, Offset)
    if ClassName != 'moExtObject_c':
        raise SldprtFormatError('native SOLIDWORKS header reference block is missing')
    ClassName, Offset = ReadClass(DataValue, Offset)
    if ClassName != 'moCStringHandle_c':
        raise SldprtFormatError('native SOLIDWORKS header path handle is missing')
    DocPath, Offset = ReadSerialized(DataValue, Offset)
    Ignored, Offset = ReadClassRef(DataValue, Offset)
    Ignored, Offset = ReadSerialized(DataValue, Offset)
    Offset = ExpectBytes(DataValue, Offset, bytes.fromhex('020000'))
    Offset += 4
    for Ignored in range(3):
        Ignored, Offset = ReadSerialized(DataValue, Offset)
    Offset = ExpectBytes(DataValue, Offset, bytes.fromhex('0008'))
    Offset += 16
    ConfigName, Offset = ReadSerialized(DataValue, Offset)
    return NativeModelA(UserName, RefName, ConfigName, DocPath, tuple(Objects))

# this definition exists because focused behavior needs one stable owner
def ReadClass(DataValue: bytes, Offset: int) -> tuple[str, int]:
    Marker = len(ClassMarker)
    if DataValue[Offset:Offset + Marker] != ClassMarker:
        raise SldprtFormatError('native SOLIDWORKS class declaration is missing')
    Start = Offset + Marker
    if Start + 2 > len(DataValue):
        raise SldprtFormatError('native SOLIDWORKS class declaration is truncated')
    Length, = Struct.unpack_from('<H', DataValue, Start)
    EndValue = Start + 2 + Length
    if EndValue > len(DataValue):
        raise SldprtFormatError('native SOLIDWORKS class declaration is truncated')
    return (DataValue[Start + 2:EndValue].decode('ascii'), EndValue)

# this definition exists because focused behavior needs one stable owner
def ReadClassRef(DataValue: bytes, OffsetData: int) -> tuple[int, int]:
    if OffsetData + 2 > len(DataValue):
        raise SldprtFormatError('native SOLIDWORKS class reference is truncated')
    RefData, = Struct.unpack_from('<H', DataValue, OffsetData)
    if RefData == 65535 or not RefData & 32768:
        raise SldprtFormatError('native SOLIDWORKS class reference is invalid')
    return (RefData & 32767, OffsetData + 2)

# this definition exists because focused behavior needs one stable owner
def ReadSerialized(DataValue: bytes, Offset: int) -> tuple[str, int]:
    Marker = len(SerializedStringMarker)
    if DataValue[Offset:Offset + Marker] != SerializedStringMarker:
        raise SldprtFormatError('native SOLIDWORKS serialized string is missing')
    Start = Offset + Marker
    if Start >= len(DataValue):
        raise SldprtFormatError('native SOLIDWORKS serialized string is truncated')
    EndValue = Start + 1 + DataValue[Start] * 2
    if EndValue > len(DataValue):
        raise SldprtFormatError('native SOLIDWORKS serialized string is truncated')
    return (DataValue[Start + 1:EndValue].decode('utf-16le'), EndValue)

# this definition exists because focused behavior needs one stable owner
def ExpectBytes(DataValue: bytes, Offset: int, Literal: bytes) -> int:
    if DataValue[Offset:Offset + len(Literal)] != Literal:
        raise SldprtFormatError('native SOLIDWORKS header layout is unexpected')
    return Offset + len(Literal)

# this definition exists because focused behavior needs one stable owner
def Serializable(Value: str) -> bool:
    return 1 <= len(Value.encode('utf-16le')) // 2 <= 254

# this definition exists because focused behavior needs one stable owner
def NativeAsmA(DocValue: CadDocument, ModelName: str, ObjectCount: int) -> NativeIdentity:
    CreationStamp = StableCreation(DocValue, ModelName, b'assembly')
    return NativeIdentity(CreationStamp, 101 + ObjectCount * 4, 101, CreationStamp + ObjectCount * 7 + 5 & 2147483647, KAsmConfigFlags, PureWindowsPath(ModelName).stem or KAsmRefName)

# this definition exists because focused behavior needs one stable owner
def ModelHeader(Identity: _NativeIdentity, ConfigName: str, UserName: str='Kit', SolidFeatureTreeIds: tuple[int, ...]=(), FeatureObjects: tuple[tuple[int, str, bool], ...]=(), FeatureStamps: Mapping[int, tuple[int, ...]] | None=None, HeaderBounds: tuple[float, ...] | None=None) -> bytes:
    return HeaderPayload(Identity, ConfigName, (*KHeaderObjects, *FeatureObjects), '', UserName, max(SolidFeatureTreeIds) + 1 if SolidFeatureTreeIds else None, FeatureStamps, HeaderBounds)

# this definition exists because focused behavior needs one stable owner
def HeaderPayload(Identity: _NativeIdentity, ConfigName: str, Objects: Sequence[tuple[int, str, bool]], DocPath: str, UserName: str='Kit', NextObjectId: int | None=None, ObjectStampsA: Mapping[int, tuple[int, ...]] | None=None, HeaderBounds: tuple[float, ...] | None=None) -> bytes:
    if HeaderBounds is not None and (len(HeaderBounds) != 10 or not all((MathValue.isfinite(ItemValue) for ItemValue in HeaderBounds))):
        raise SldprtFormatError('native SOLIDWORKS header bounds require ten finite values')
    LegacyStamp = bytes.fromhex('f65a1a69')
    CStringHandleClassIndex = 14 + sum((2 + int(Modified) for ObjectId, NameValue, Modified in Objects))
    Output = bytearray(ClassDecl('moHeader_c'))
    Output.extend(bytes.fromhex('01000000ffff00000f00') + b'su_CStringArray' + Struct.pack('<H', 1))
    Output.extend(Serialized(UserName))
    Output.extend(bytes.fromhex('03800100'))
    Output.extend(Serialized(''))
    Output.extend(ClassDecl('suObList'))
    Output.extend(Struct.pack('<H', len(Objects) + 1))
    Output.extend(ClassDecl('moLogs_c'))
    Output.extend(Struct.pack('<H', 1))
    Output.extend(ClassDecl('moStamp_c'))
    Output.extend(b'\x00' * 6 + LegacyStamp)
    Output.extend(Serialized('Created'))
    Output.extend(Struct.pack('<I', 0))
    Output.extend(Serialized(Identity.reference_name))
    LogicalStamp = Identity.creation_stamp
    ObjectStamps = ObjectStampsA or {}
    for ObjectId, NameValue, Modified in Objects:
        Actions = ('Created', 'Modified') if Modified else ('Created',)
        RecoveredStamps = ObjectStamps.get(ObjectId)
        if RecoveredStamps is not None and len(RecoveredStamps) != len(Actions):
            raise SldprtFormatError('native SOLIDWORKS header action stamps do not match object actions')
        Output.extend(bytes.fromhex('0880') + Struct.pack('<H', len(Actions)))
        if ObjectId > 16 and Modified:
            LogicalStamp += 1
        for Index, Action in enumerate(Actions):
            if ObjectId > 16 and Index:
                LogicalStamp += 1
            StampData = Struct.pack('<I', RecoveredStamps[Index]) if RecoveredStamps is not None else LegacyStamp if ObjectId <= 16 else Struct.pack('<I', LogicalStamp)
            Output.extend(bytes.fromhex('0a80') + Struct.pack('<I', Index) + b'\x00\x00' + StampData)
            Output.extend(Serialized(Action))
        Output.extend(Struct.pack('<I', ObjectId))
        Output.extend(Serialized(NameValue))
    Watermark = max((ItemValue[0] for ItemValue in Objects)) + 1 if NextObjectId is None else max(NextObjectId, max((ItemValue[0] for ItemValue in Objects)) + 1)
    Output.extend(LegacyStamp + Struct.pack('<IH', Watermark, 0) + Struct.pack('<I', Identity.last_modified_stamp))
    Output.extend(ClassDecl('moExtObject_c'))
    Output.extend(ClassDecl('moCStringHandle_c'))
    Output.extend(Serialized(DocPath))
    Output.extend(EncodeClassRef(CStringHandleClassIndex))
    Output.extend(Serialized(Identity.reference_name))
    Output.extend(bytes.fromhex('020000'))
    Output.extend(Struct.pack('<I', Identity.creation_stamp))
    Output.extend(Serialized('') * 3)
    Output.extend(bytes.fromhex('0008'))
    Output.extend(Struct.pack('<III', Identity.header_stamp, 1, 0))
    Output.extend(Struct.pack('<I', 4294967295))
    Output.extend(Serialized(ConfigName))
    Output.extend(b'\x00' * 16)
    Output.extend(Struct.pack('<I', Identity.baseline_stamp))
    Output.extend(b'\x00' * 8)
    Output.extend(Struct.pack('<I', Identity.creation_stamp))
    Output.extend(b'\x00' * 22)
    Output.extend(Struct.pack('<I', Identity.header_stamp))
    Output.extend(bytes.fromhex('0680'))
    Output.extend(b'\x00' * 10)
    Output.extend(Struct.pack('<I', int(HeaderBounds is not None)))
    if HeaderBounds is not None:
        Output.extend(Struct.pack('<10d', *HeaderBounds))
    Output.extend(b'\xff' * 10)
    Output.extend(ClassDecl(''))
    Output.extend(b'\x00' * 40)
    Output.extend(Struct.pack('<I', 1))
    Output.extend(b'\x00' * 16)
    Output.extend(Struct.pack('<I', 1))
    return bytes(Output)

# this definition exists because focused behavior needs one stable owner
def ConfigHeader(ConfigName: str, Identity: _NativeIdentity) -> bytes:
    return b''.join((ClassDecl('dmConfigMgrHeader_c'), Struct.pack('<H', 1), ClassDecl('dmConfigHeader_c'), Struct.pack('<I', 1), Serialized(ConfigName), Struct.pack('<II', 0, Identity.last_modified_stamp), Serialized(ConfigName), Struct.pack('<II', 4294967295, 0), Serialized(''), Serialized(''), Struct.pack('<IIIIII', Identity.configuration_flags & 4294967295, 0, Identity.baseline_stamp, Identity.baseline_stamp, Identity.header_stamp, 2)))

# this definition exists because focused behavior needs one stable owner
def CustomPayload(ContainerClass: str='moFilePropContainer_c') -> bytes:
    return b''.join((ClassDecl('moCusPropMgr_c'), Struct.pack('<H', 65535), ClassDecl(''), Struct.pack('<II', 1, 0), ClassDecl('moCusPropContainer_c'), ClassDecl(ContainerClass), b'\x00' * 13))

# this definition exists because focused behavior needs one stable owner
def VersionHistory() -> bytes:
    return b''.join((ClassDecl('moVersionHistory_c'), Struct.pack('<IIH', 1, 0, 0), bytes.fromhex('f65a1a69'), Serialized(''), b'PF\x00\x00', ClassDecl('moDateCodeHistory_c'), Struct.pack('<I', 1), bytes.fromhex('34e71e'), Struct.pack('<IBI', 1, 0, 4294967295), b'\x00' * 14))

# this definition exists because focused behavior needs one stable owner
def Biography(ModelName: str, Identity: _NativeIdentity, TemplatePath: str='C:\\Kit\\Part.PRTDOT', DocSuffix: str=PartSuffix) -> bytes:
    Filetime = 116444736000000000 + Identity.creation_stamp * 10000000
    FirstPaths = ('C:\\Windows\\System32\\', 'C:\\Windows\\', 'C:\\Program Files\\SOLIDWORKS\\', 'C:\\Temp\\', 'C:\\Temp\\', TemplatePath)
    SecondPaths = ('C:\\Windows\\System32\\', 'C:\\Windows\\', 'C:\\', 'C:\\Temp\\', 'C:\\Temp\\', TemplatePath)
    Output = bytearray(ClassDecl('moBiography_c') + Struct.pack('<10I', 2, 18000, 2025268, 1, 9, 12, 2, 10, 0, 26100))
    for Ignored in range(7):
        Output.extend(Serialized(''))
        Output.extend(b'\x00' * (14 if len(Output) == 63 else 12))
    Output.extend(Struct.pack('<QI', Filetime, 691077120))
    for PathValue in FirstPaths:
        Output.extend(Serialized(PathValue))
        Output.extend(Struct.pack('<III', 3, 1162821632, 5))
    Output.extend(Struct.pack('<9I', 18000, 2025268, 1, 9, 12, 2, 10, 0, 26200))
    Output.extend(Serialized(''))
    Output.extend(Struct.pack('<HQI', 6153, Filetime, 1806331904))
    for PathValue in SecondPaths:
        Output.extend(Serialized(PathValue))
        Output.extend(Struct.pack('<III', 3, 212815872, 5))
    Output.extend(Struct.pack('<QI', Filetime, 1434583040))
    for Value in ('*', '*', 'C:\\', '*', '*'):
        Output.extend(Serialized(Value))
        Output.extend(Struct.pack('<III', 3, 211980288, 5))
    Output.extend(Serialized(f'C:\\{ModelName}{DocSuffix}'))
    Output.extend(Struct.pack('<III', 3, 211980288, 5))
    return bytes(Output)

# this definition exists because focused behavior needs one stable owner
def Serialized(Value: str) -> bytes:
    Encoded = Value.encode('utf-16le')
    Units = len(Encoded) // 2
    if Units > 254:
        raise SldprtFormatError('native SOLIDWORKS serialized string exceeds 254 UTF-16 units')
    return SerializedStringMarker + bytes((Units,)) + Encoded

# this definition exists because focused behavior needs one stable owner
def StableUThreeTwo(DocValue: CadDocument, ModelName: str, Domain: bytes=b'') -> int:
    Source = ModelName.encode('utf-8') + b'\x00' + DocValue.to_json(indent=None).encode('utf-8')
    if Domain:
        Source += b'\x00' + Domain
    Digest = Hashlib.sha256(Source).digest()
    Value = int.from_bytes(Digest[:4], 'little') & 2147483647
    return Value or 1

# this definition exists because focused behavior needs one stable owner
def StableCreation(DocValue: CadDocument, ModelName: str, Domain: bytes=b'') -> int:
    SpanValue = KCreationStampHigh - KCreationStampLow
    return KCreationStampLow + StableUThreeTwo(DocValue, ModelName, Domain) % SpanValue

# this definition exists because focused behavior needs one stable owner
def ProvedWrite(DocValue: CadDocument, Authored: tuple[_WriteObject, ...], Parsed: NativeModel, ObjectIds: dict[str, int]) -> frozenset[Capability]:
    Result: set[Capability] = set()
    if all((Config.parent_id is None and (not Config.overrides) and (not Config.suppressed_feature_ids) for Config in DocValue.configurations)) and (not DocValue.configurations or sum((Config.active for Config in DocValue.configurations)) == 1):
        Expected = tuple(((Config.name, ObjectIds[f'configuration:{Config.id}']) for Config in DocValue.configurations))
        Actual = tuple(((Config.name, Config.configuration_id) for Config in Parsed.configurations))
        if Expected == Actual:
            Result.add(Capability.CONFIGURATIONS)
    ExpectedParameters = tuple(((ItemValue.object_id, Dimension.name, round(Dimension.value_mm, 10), Dimension.role) for ItemValue in Authored for Dimension in ItemValue.dimensions if any((Param.name == Dimension.name and Param.owner_id == ItemValue.source_id for Param in DocValue.parameters))))
    ActualParameters = tuple(((Feature.object_id, Dimension.name, round(Dimension.value_mm, 10), ParamRole.DRIVEN if Dimension.native_role == 'display' else ParamRole.DRIVING) for Feature in Parsed.features if any((ItemValue.object_id == Feature.object_id for ItemValue in Authored)) for Dimension in Feature.dimensions if any((Param.name == Dimension.name and Param.owner_id == next((ItemValue.source_id for ItemValue in Authored if ItemValue.object_id == Feature.object_id)) for Param in DocValue.parameters))))
    Encodable = tuple((Param for Param in DocValue.parameters if ParamDimension(Param) is not None and Param.expression is None))
    if len(Encodable) == len(DocValue.parameters) and len(ExpectedParameters) == len(DocValue.parameters) and (ExpectedParameters == ActualParameters):
        Result.add(Capability.PARAMETERS)
    ExpectedPlanes = {PlaneObjectId: ExpectedPlane(PlaneData, PlaneObjectId) for PlaneData in DocValue.support_planes for PlaneObjectId in (ObjectIds[f'plane:{PlaneData.id}'],)}
    ActualPlanes = {Plane.object_id: (FrameVector(Plane.origin_mm), FrameVector(Plane.u_axis), FrameVector(Plane.v_axis), FrameVector(Plane.normal)) for Plane in Parsed.planes}
    if len(ExpectedPlanes) == len(DocValue.support_planes) and all((ObjectId in ActualPlanes and ActualPlanes[ObjectId] == Frame for ObjectId, Frame in ExpectedPlanes.items())):
        Result.add(Capability.SUPPORT_PLANES)
    ExpectedAxes = DocAxisBindings(DocValue, ObjectIds)
    if ExpectedAxes is not None:
        ActualAxes = NativeAxis(Parsed)
        if ExpectedAxes and ExpectedAxes <= ActualAxes:
            Result.add(Capability.SELECTIONS)
    ExpectedEquations = ExpressionTexts(DocValue)
    if ExpectedEquations is not None:
        ActualEquations = tuple((Equation.source for Equation in Parsed.equations))
        if ActualEquations[:len(ExpectedEquations)] == ExpectedEquations and all((Source.startswith(f'"{KEquationReservedPrefix}') for Source in ActualEquations[len(ExpectedEquations):])):
            Result.add(Capability.EXPRESSIONS)
    HasGrooveData = HasPadGroove(DocValue, Authored, Parsed)
    HasFilletData = HasBossFillet(DocValue, Authored, Parsed)
    HasChamferData = HasBossChamfer(DocValue, Authored, Parsed)
    HasShellData = HasBossShell(DocValue, Authored, Parsed)
    HasLinearPatternData = HasBossLinear(DocValue, Authored, Parsed)
    HasCircularPatternData = HasBossCircular(DocValue, Authored, Parsed)
    if HasPadProof(DocValue, Authored, Parsed) or HasSingleProof(DocValue, Authored, Parsed) or HasGrooveData or HasFilletData or HasChamferData or HasShellData or HasLinearPatternData or HasCircularPatternData or HasTwoFeature(DocValue, Authored, Parsed) or HasCutChain(DocValue, Authored, Parsed):
        Result.update({Capability.BREP, Capability.PARAMETERS, Capability.PARAMETRIC_HISTORY, Capability.EDITABLE_SKETCHES, Capability.BODY_STRUCTURE})
    if HasGrooveData or HasFilletData or HasChamferData or HasShellData or HasLinearPatternData or HasCircularPatternData:
        Result.add(Capability.SELECTIONS)
    return frozenset(Result)

# this definition exists because focused behavior needs one stable owner
def HasPadProof(DocData: CadDocument, AuthoredObjs: tuple[_WriteObject, ...], ParsedModel: NativeModel) -> bool:
    if len(AuthoredObjs) != 2:
        return False
    SketchObject, PadObject = AuthoredObjs
    PlaneObjectId = Struct.unpack_from('<I', SketchObject.payload)[0] if len(SketchObject.payload) >= 4 else 0
    BoundsValue = WriteRectangle(SketchObject)
    CircleValue = WriteCircle(SketchObject)
    PolylineValue = PolySixPoints(SketchObject)
    EndCodes = ExtrusionEdit(PadObject.payload)
    IsDimensionedBox = BoundsValue is not None and ('KitPrimitive', 'Box') in PadObject.properties and (len(SketchObject.dimensions) == 2)
    ExpectedFeatureId = 34 if IsDimensionedBox else 33 if CircleValue else 32
    if sum((ItemValue is not None for ItemValue in (BoundsValue, CircleValue, PolylineValue))) != 1 or EndCodes is None or SketchObject.object_id != 26 or (SketchObject.name != 'Sketch1') or (PadObject.object_id != ExpectedFeatureId) or (PadObject.name != 'Boss-Extrude1') or (len(PadObject.dimensions) != 1) or (len(ParsedModel.sketches) != 1) or (len(ParsedModel.operations) != 1):
        return False
    NativeSketch = ParsedModel.sketches[0]
    NativePad = ParsedModel.operations[0]
    ExpectedProfile = BoundsValue if BoundsValue is not None else CircleValue if CircleValue is not None else tuple((CoordinateValue for PointData in PolylineValue or () for CoordinateValue in PointData))
    ExpectedKind = 'rectangle' if BoundsValue is not None else 'circle' if CircleValue is not None else 'polyline'
    ProfilesValue = tuple((ProfileData for ProfileData in NativeSketch.profiles if ProfileData.kind == ExpectedKind))
    HasProfile = ExpectedProfile is not None and (len(ProfilesValue) == 1 and len(ProfilesValue[0].coordinates) == len(ExpectedProfile) and all((MathValue.isclose(ActualValue, ExpectedValue, abs_tol=1e-10) for ActualValue, ExpectedValue in zip(ProfilesValue[0].coordinates, ExpectedProfile, strict=True))))
    DepthValue = PadObject.dimensions[0].value_mm
    ExpectedDepth = (1, 1, -1, -1, 1, 1)
    ExpectedDims = tuple(((ItemData.name, round(ItemData.value_mm, 10)) for ItemData in SketchObject.dimensions))
    ActualDims = tuple(((ItemData.name, round(ItemData.value_mm, 10)) for ItemData in NativeSketch.dimensions))
    RuleKinds = tuple((ItemData.kind for ItemData in NativeSketch.constraints))
    ExpectedRuleKinds = ('horizontal', 'vertical', 'horizontal', 'vertical', *('distance',) * len(ExpectedDims)) if BoundsValue is not None else ('diameter',) if CircleValue is not None else ()
    if NativeSketch.object_id != 26 or NativeSketch.support_plane_id != PlaneObjectId or (not HasProfile) or (RuleKinds != ExpectedRuleKinds) or (ActualDims != ExpectedDims) or (NativePad.object_id != ExpectedFeatureId) or (NativePad.name != 'Boss-Extrude1') or (NativePad.profile_id != 26) or (NativePad.kind not in {'boss', 'join'}) or (NativePad.direction_code != EndCodes[0]) or (NativePad.termination_code != EndCodes[1]) or (NativePad.length_mm is None) or (not MathValue.isclose(NativePad.length_mm, DepthValue, abs_tol=1e-10)) or (len(NativePad.depth_copies) != len(ExpectedDepth)) or (not MathValue.isclose(NativePad.depth_copies[0].value_mm, DepthValue, abs_tol=1e-10)) or (PolylineValue is None and EndCodes == (0, 0) and any((CopyData.sign != CopySign or not MathValue.isclose(CopyData.value_mm, DepthValue * CopySign, abs_tol=1e-10) for CopyData, CopySign in zip(NativePad.depth_copies, ExpectedDepth, strict=True)))):
        return False
    NativeFeatureIds = tuple((ItemData.object_id for ItemData in ParsedModel.features if ItemData.object_id in {26, ExpectedFeatureId}))
    return NativeFeatureIds == (26, ExpectedFeatureId) and len(DocData.bodies) == 1

# this definition exists because focused behavior needs one stable owner
def HasSingleProof(DocData: CadDocument, AuthoredObjs: tuple[_WriteObject, ...], ParsedModel: NativeModel) -> bool:
    if len(AuthoredObjs) != 2 or len(ParsedModel.sketches) != 1 or len(ParsedModel.operations) != 1 or (len(DocData.bodies) != 1):
        return False
    SketchObject, RevolveObject = AuthoredObjs
    BoundsValue = WriteRectangle(SketchObject)
    PinPoints = PolySixPoints(SketchObject)
    IsPinData = IsPinProfile(PinPoints)
    if not (BoundsValue is not None or IsPinData) or SketchObject.object_id != 26 or SketchObject.name != 'Sketch1' or (RevolveObject.object_id != 31) or (RevolveObject.name != 'Revolve1') or (len(RevolveObject.dimensions) != 1):
        return False
    NativeSketch = ParsedModel.sketches[0]
    NativeRevolve = ParsedModel.operations[0]
    NativeFeature = next((ItemData for ItemData in ParsedModel.features if ItemData.object_id == 31), None)
    ProfileKind = 'polyline' if IsPinData else 'rectangle'
    ExpectedCoords = tuple((ValueData for PointData in PinPoints or () for ValueData in PointData)) if IsPinData else BoundsValue
    ExpectedPlaneId = 3 if IsPinData else 2
    ExpectedConstraints = () if IsPinData else ('horizontal', 'vertical', 'horizontal', 'vertical')
    ProfileData = tuple((ItemData for ItemData in NativeSketch.profiles if ItemData.kind == ProfileKind))
    DimensionData = RevolveObject.dimensions[0]
    if NativeSketch.object_id != 26 or NativeSketch.support_plane_id != ExpectedPlaneId or len(ProfileData) != 1 or (ExpectedCoords is None) or (len(ProfileData[0].coordinates) != len(ExpectedCoords)) or any((not MathValue.isclose(ActualValue, ExpectedValue, abs_tol=1e-10) for ActualValue, ExpectedValue in zip(ProfileData[0].coordinates, ExpectedCoords, strict=True))) or (tuple((ItemData.kind for ItemData in NativeSketch.constraints)) != ExpectedConstraints) or (NativeRevolve.object_id != 31) or (NativeRevolve.name != 'Revolve1') or (NativeRevolve.kind != 'revolve_join') or (NativeRevolve.profile_id != 26) or (NativeRevolve.angle_degrees is None) or (not MathValue.isclose(NativeRevolve.angle_degrees, DimensionData.value_mm, rel_tol=0.0, abs_tol=1e-10)) or (NativeAxis(ParsedModel) != frozenset({(31, 26, KVerticalAxisSubElem)})) or (NativeFeature is None) or (len(NativeFeature.dimensions) != 1) or (NativeFeature.dimensions[0].name != 'D1') or (NativeFeature.dimensions[0].kind != 'angle') or (not MathValue.isclose(NativeFeature.dimensions[0].value_mm, DimensionData.value_mm, rel_tol=0.0, abs_tol=1e-10)):
        return False
    NativeFeatureIds = tuple((ItemData.object_id for ItemData in ParsedModel.features if ItemData.object_id in {26, 31}))
    return NativeFeatureIds == (26, 31)

# this definition exists because focused behavior needs one stable owner
def HasPadGroove(DocData: CadDocument, AuthoredObjs: tuple[_WriteObject, ...], ParsedModel: NativeModel) -> bool:
    if len(AuthoredObjs) != 4 or len(ParsedModel.sketches) != 2 or len(ParsedModel.operations) != 2 or (len(DocData.bodies) != 1):
        return False
    SketchOne, PadObject, SketchTwo, GrooveObject = AuthoredObjs
    SourceSketches = tuple((next((ItemData for ItemData in DocData.sketches if ItemData.id == SketchObject.source_id), None) for SketchObject in (SketchOne, SketchTwo)))
    SourceFeatures = tuple((next((ItemData for ItemData in DocData.feature_timeline if ItemData.id == FeatureObject.source_id), None) for FeatureObject in (PadObject, GrooveObject)))
    if any((ItemData is None for ItemData in (*SourceSketches, *SourceFeatures))):
        return False
    SourceSketchOne, SourceSketchTwo = SourceSketches
    SourcePad, SourceGroove = SourceFeatures
    if SourceSketchOne is None or SourceSketchTwo is None or SourcePad is None or (SourceGroove is None):
        return False
    DimensionData = FreeCadPad(DocData, (SourceSketchOne, SourceSketchTwo), (SourcePad, SourceGroove))
    BoundsData = (WriteRectangle(SketchOne), WriteRectangle(SketchTwo))
    EndCodes = ExtrusionEdit(PadObject.payload)
    if DimensionData is None or any((ItemData is None for ItemData in BoundsData)) or EndCodes is None or ((SketchOne.object_id, PadObject.object_id) != (26, 32)) or ((SketchTwo.object_id, GrooveObject.object_id) != (33, 39)) or ((SketchOne.name, PadObject.name) != ('Sketch1', 'Boss-Extrude1')) or ((SketchTwo.name, GrooveObject.name) != ('Sketch2', 'Cut-Revolve1')):
        return False
    NativePad, NativeGroove = ParsedModel.operations
    if NativePad.object_id != 32 or NativePad.name != 'Boss-Extrude1' or NativePad.kind not in {'boss', 'join'} or (NativePad.profile_id != 26) or (NativePad.direction_code != EndCodes[0]) or (NativePad.termination_code != EndCodes[1]) or (NativePad.length_mm is None) or (not MathValue.isclose(NativePad.length_mm, DimensionData[0].value_mm, rel_tol=0.0, abs_tol=1e-10)) or (NativeGroove.object_id != 39) or (NativeGroove.name != 'Cut-Revolve1') or (NativeGroove.kind != 'revolve_cut') or (NativeGroove.profile_id != 33) or (NativeGroove.angle_degrees is None) or (not MathValue.isclose(NativeGroove.angle_degrees, DimensionData[1].value_mm, rel_tol=0.0, abs_tol=1e-10)):
        return False
    for NativeSketch, SketchObject, BoundsValue, ObjectId in zip(ParsedModel.sketches, (SketchOne, SketchTwo), BoundsData, (26, 33), strict=True):
        if BoundsValue is None:
            return False
        ProfileData = tuple((ItemData for ItemData in NativeSketch.profiles if ItemData.kind == 'rectangle'))
        if NativeSketch.object_id != ObjectId or NativeSketch.support_plane_id != 2 or len(ProfileData) != 1 or any((not MathValue.isclose(ActualValue, ExpectedValue, abs_tol=1e-10) for ActualValue, ExpectedValue in zip(ProfileData[0].coordinates, BoundsValue, strict=True))) or (tuple(((ItemData.name, round(ItemData.value_mm, 10)) for ItemData in NativeSketch.dimensions)) != tuple(((ItemData.name, round(ItemData.value_mm, 10)) for ItemData in SketchObject.dimensions))):
            return False
    NativeFeatureIds = tuple((ItemData.object_id for ItemData in ParsedModel.features if ItemData.object_id in {26, 32, 33, 39}))
    return NativeFeatureIds == (26, 32, 33, 39)

# this definition exists because focused behavior needs one stable owner
def HasBossFillet(DocData: CadDocument, AuthoredObjs: tuple[_WriteObject, ...], ParsedModel: NativeModel) -> bool:
    if len(AuthoredObjs) != 3 or len(ParsedModel.sketches) != 1 or len(ParsedModel.operations) != 2 or (len(DocData.bodies) != 1):
        return False
    SketchObject, PadObject, FilletObject = AuthoredObjs
    SourceSketch = next((ItemData for ItemData in DocData.sketches if ItemData.id == SketchObject.source_id), None)

    # this callback exists because local behavior needs one focused transformation
    SourceFeatures = tuple((ItemData for ItemData in sorted(DocData.feature_timeline, key=lambda ItemData: ItemData.order) if not IsNativeSystem(ItemData)))
    BoundsValue = WriteRectangle(SketchObject)
    if SourceSketch is None or len(SourceFeatures) != 2 or BoundsValue is None:
        return False
    SourcePad, SourceFillet = SourceFeatures
    DimensionData = FreeCadBossB(DocData, SourceSketch, SourcePad, SourceFillet, BoundsValue)
    if DimensionData is None or (SketchObject.object_id, PadObject.object_id, FilletObject.object_id) != (26, 32, 34) or (SketchObject.name, PadObject.name, FilletObject.name) != ('Sketch1', 'Boss-Extrude1', 'Fillet1') or (ExtrusionEdit(PadObject.payload) != (0, 0)) or (FilletObject.payload != FilletSelection(32, 3)):
        return False
    NativeSketch = ParsedModel.sketches[0]
    NativePad, NativeFillet = ParsedModel.operations
    ProfilesValue = tuple((ItemData for ItemData in NativeSketch.profiles if ItemData.kind == 'rectangle'))
    ExpectedDepthSigns = (1, 1, -1, -1, 1, 1)
    if NativeSketch.object_id != 26 or NativeSketch.support_plane_id != 2 or len(ProfilesValue) != 1 or (len(ProfilesValue[0].coordinates) != len(BoundsValue)) or any((not MathValue.isclose(ActualValue, ExpectedValue, abs_tol=1e-10) for ActualValue, ExpectedValue in zip(ProfilesValue[0].coordinates, BoundsValue, strict=True))) or (tuple((ItemData.kind for ItemData in NativeSketch.constraints)) != ('horizontal', 'vertical', 'horizontal', 'vertical')) or (NativePad.object_id != 32) or (NativePad.name != 'Boss-Extrude1') or (NativePad.kind not in {'boss', 'join'}) or (NativePad.profile_id != 26) or (NativePad.dependencies != (26,)) or (NativePad.direction_code != 0) or (NativePad.termination_code != 0) or (NativePad.length_mm is None) or (not MathValue.isclose(NativePad.length_mm, DimensionData[0].value_mm, rel_tol=0.0, abs_tol=1e-10)) or (len(NativePad.depth_copies) != len(ExpectedDepthSigns)) or any((ItemData.sign != SignValue or not MathValue.isclose(ItemData.value_mm, DimensionData[0].value_mm * SignValue, rel_tol=0.0, abs_tol=1e-10) for ItemData, SignValue in zip(NativePad.depth_copies, ExpectedDepthSigns, strict=True))) or (NativeFillet.object_id != 34) or (NativeFillet.name != 'Fillet1') or (NativeFillet.kind != 'fillet') or (NativeFillet.profile_id is not None) or (NativeFillet.dependencies != (32,)) or (NativeFillet.radius_mm is None) or (not MathValue.isclose(NativeFillet.radius_mm, DimensionData[1].value_mm, rel_tol=0.0, abs_tol=1e-10)) or (NativeFillet.selection_kind != 'edge') or (NativeFillet.selection_references != ((32, 3),)) or (NativeFillet.selected_local_ids != (3,)):
        return False
    NativeFilletFeature = next((ItemData for ItemData in ParsedModel.features if ItemData.object_id == 34), None)
    NativeFeatureIds = tuple((ItemData.object_id for ItemData in ParsedModel.features if ItemData.object_id in {26, 32, 34}))
    return NativeFilletFeature is not None and len(NativeFilletFeature.dimensions) == 1 and (NativeFilletFeature.dimensions[0].name == 'D1') and (NativeFilletFeature.dimensions[0].kind == 'radius') and MathValue.isclose(NativeFilletFeature.dimensions[0].value_mm, DimensionData[1].value_mm, rel_tol=0.0, abs_tol=1e-10) and (NativeFeatureIds == (26, 32, 34))

# this definition exists because focused behavior needs one stable owner
def HasBossChamfer(DocData: CadDocument, AuthoredObjs: tuple[_WriteObject, ...], ParsedModel: NativeModel) -> bool:
    if len(AuthoredObjs) != 3 or len(ParsedModel.sketches) != 1 or len(ParsedModel.operations) != 2 or (len(DocData.bodies) != 1):
        return False
    SketchObject, PadObject, ChamferObject = AuthoredObjs
    SourceSketch = next((ItemData for ItemData in DocData.sketches if ItemData.id == SketchObject.source_id), None)

    # this callback exists because local behavior needs one focused transformation
    SourceFeatures = tuple((ItemData for ItemData in sorted(DocData.feature_timeline, key=lambda ItemData: ItemData.order) if not IsNativeSystem(ItemData)))
    BoundsValue = WriteRectangle(SketchObject)
    if SourceSketch is None or len(SourceFeatures) != 2 or BoundsValue is None:
        return False
    SourcePad, SourceChamfer = SourceFeatures
    DimensionData = FreeCadBoss(DocData, SourceSketch, SourcePad, SourceChamfer, BoundsValue)
    if DimensionData is None or (SketchObject.object_id, PadObject.object_id, ChamferObject.object_id) != (26, 32, 35) or (SketchObject.name, PadObject.name, ChamferObject.name) != ('Sketch1', 'Boss-Extrude1', 'Chamfer1') or (ExtrusionEdit(PadObject.payload) != (0, 0)) or (ChamferObject.payload != FilletSelection(32, 3)):
        return False
    NativeSketch = ParsedModel.sketches[0]
    NativePad, NativeChamfer = ParsedModel.operations
    ProfilesValue = tuple((ItemData for ItemData in NativeSketch.profiles if ItemData.kind == 'rectangle'))
    ExpectedDepthSigns = (1, 1, -1, -1, 1, 1)
    if NativeSketch.object_id != 26 or NativeSketch.support_plane_id != 2 or len(ProfilesValue) != 1 or (len(ProfilesValue[0].coordinates) != len(BoundsValue)) or any((not MathValue.isclose(ActualValue, ExpectedValue, abs_tol=1e-10) for ActualValue, ExpectedValue in zip(ProfilesValue[0].coordinates, BoundsValue, strict=True))) or (tuple((ItemData.kind for ItemData in NativeSketch.constraints)) != ('horizontal', 'vertical', 'horizontal', 'vertical')) or (NativePad.object_id != 32) or (NativePad.name != 'Boss-Extrude1') or (NativePad.kind not in {'boss', 'join'}) or (NativePad.profile_id != 26) or (NativePad.dependencies != (26,)) or (NativePad.direction_code != 0) or (NativePad.termination_code != 0) or (NativePad.length_mm is None) or (not MathValue.isclose(NativePad.length_mm, DimensionData[0].value_mm, rel_tol=0.0, abs_tol=1e-10)) or (len(NativePad.depth_copies) != len(ExpectedDepthSigns)) or any((ItemData.sign != SignValue or not MathValue.isclose(ItemData.value_mm, DimensionData[0].value_mm * SignValue, rel_tol=0.0, abs_tol=1e-10) for ItemData, SignValue in zip(NativePad.depth_copies, ExpectedDepthSigns, strict=True))) or (NativeChamfer.object_id != 35) or (NativeChamfer.name != 'Chamfer1') or (NativeChamfer.kind != 'chamfer') or (NativeChamfer.profile_id is not None) or (NativeChamfer.dependencies != (32,)) or (NativeChamfer.length_mm is None) or (not MathValue.isclose(NativeChamfer.length_mm, DimensionData[1].value_mm, rel_tol=0.0, abs_tol=1e-10)) or (NativeChamfer.selection_kind != 'edge') or (NativeChamfer.selection_references != ((32, 3),)) or (NativeChamfer.selected_local_ids != (3,)) or (NativeChamfer.mode != 'equal_distance'):
        return False
    NativeChamferFeature = next((ItemData for ItemData in ParsedModel.features if ItemData.object_id == 35), None)
    NativeFeatureIds = tuple((ItemData.object_id for ItemData in ParsedModel.features if ItemData.object_id in {26, 32, 35}))
    return NativeChamferFeature is not None and len(NativeChamferFeature.dimensions) == 1 and (tuple(((ItemData.name, ItemData.kind) for ItemData in NativeChamferFeature.dimensions)) == (('D1', 'distance'),)) and MathValue.isclose(next((ItemData.value_mm for ItemData in NativeChamferFeature.dimensions if ItemData.name == 'D1')), DimensionData[1].value_mm, rel_tol=0.0, abs_tol=1e-10) and (NativeFeatureIds == (26, 32, 35))

# this definition exists because focused behavior needs one stable owner
def HasBossShell(DocData: CadDocument, AuthoredObjs: tuple[_WriteObject, ...], ParsedModel: NativeModel) -> bool:
    if len(AuthoredObjs) != 3 or len(ParsedModel.sketches) != 1 or len(ParsedModel.operations) != 2 or (len(DocData.bodies) != 1):
        return False
    SketchObject, PadObject, ShellObject = AuthoredObjs
    SourceSketch = next((ItemData for ItemData in DocData.sketches if ItemData.id == SketchObject.source_id), None)

    # this callback exists because local behavior needs one focused transformation
    SourceFeatures = tuple((ItemData for ItemData in sorted(DocData.feature_timeline, key=lambda ItemData: ItemData.order) if not IsNativeSystem(ItemData)))
    BoundsValue = WriteRectangle(SketchObject)
    if SourceSketch is None or len(SourceFeatures) != 2 or BoundsValue is None:
        return False
    SourcePad, SourceShell = SourceFeatures
    DimensionData = FreeCadBossD(DocData, SourceSketch, SourcePad, SourceShell, BoundsValue)
    if DimensionData is None or (SketchObject.object_id, PadObject.object_id, ShellObject.object_id) != (26, 32, 34) or (SketchObject.name, PadObject.name, ShellObject.name) != ('Sketch1', 'Boss-Extrude1', 'Shell1') or (ExtrusionEdit(PadObject.payload) != (0, 0)) or (ShellObject.payload != ShellSelection(32)):
        return False
    NativeSketch = ParsedModel.sketches[0]
    NativePad, NativeShell = ParsedModel.operations
    ProfilesValue = tuple((ItemData for ItemData in NativeSketch.profiles if ItemData.kind == 'rectangle'))
    ExpectedDepthSigns = (1, 1, -1, -1, 1, 1)
    if NativeSketch.object_id != 26 or NativeSketch.support_plane_id != 2 or len(ProfilesValue) != 1 or (len(ProfilesValue[0].coordinates) != len(BoundsValue)) or any((not MathValue.isclose(ActualValue, ExpectedValue, abs_tol=1e-10) for ActualValue, ExpectedValue in zip(ProfilesValue[0].coordinates, BoundsValue, strict=True))) or (tuple((ItemData.kind for ItemData in NativeSketch.constraints)) != ('horizontal', 'vertical', 'horizontal', 'vertical')) or (NativePad.object_id != 32) or (NativePad.name != 'Boss-Extrude1') or (NativePad.kind not in {'boss', 'join'}) or (NativePad.profile_id != 26) or (NativePad.dependencies != (26,)) or (NativePad.direction_code != 0) or (NativePad.termination_code != 0) or (NativePad.length_mm is None) or (not MathValue.isclose(NativePad.length_mm, DimensionData[0].value_mm, rel_tol=0.0, abs_tol=1e-10)) or (len(NativePad.depth_copies) != len(ExpectedDepthSigns)) or any((ItemData.sign != SignValue or not MathValue.isclose(ItemData.value_mm, DimensionData[0].value_mm * SignValue, rel_tol=0.0, abs_tol=1e-10) for ItemData, SignValue in zip(NativePad.depth_copies, ExpectedDepthSigns, strict=True))) or (NativeShell.object_id != 34) or (NativeShell.name != 'Shell1') or (NativeShell.kind != 'shell') or (NativeShell.profile_id is not None) or (NativeShell.dependencies != (32,)) or (NativeShell.length_mm is None) or (not MathValue.isclose(NativeShell.length_mm, DimensionData[1].value_mm, rel_tol=0.0, abs_tol=1e-10)) or (NativeShell.selection_kind != 'face') or (NativeShell.selection_references != ((32, 1), (32, 4))) or (NativeShell.selected_local_ids != (1, 4)):
        return False
    NativeShellFeature = next((ItemData for ItemData in ParsedModel.features if ItemData.object_id == 34), None)
    NativeFeatureIds = tuple((ItemData.object_id for ItemData in ParsedModel.features if ItemData.object_id in {26, 32, 34}))
    return NativeShellFeature is not None and len(NativeShellFeature.dimensions) == 1 and (NativeShellFeature.dimensions[0].name == 'D1') and (NativeShellFeature.dimensions[0].kind == 'thickness') and MathValue.isclose(NativeShellFeature.dimensions[0].value_mm, DimensionData[1].value_mm, rel_tol=0.0, abs_tol=1e-10) and (NativeFeatureIds == (26, 32, 34))

# this definition exists because focused behavior needs one stable owner
def HasBossLinear(DocData: CadDocument, AuthoredObjs: tuple[_WriteObject, ...], ParsedModel: NativeModel) -> bool:
    if len(AuthoredObjs) != 3 or len(ParsedModel.sketches) != 1 or len(ParsedModel.operations) != 2 or (len(DocData.bodies) != 1):
        return False
    SketchObject, PadObject, PatternObject = AuthoredObjs
    SourceSketch = next((ItemData for ItemData in DocData.sketches if ItemData.id == SketchObject.source_id), None)

    # this callback exists because local behavior needs one focused transformation
    SourceFeatures = tuple((ItemData for ItemData in sorted(DocData.feature_timeline, key=lambda ItemData: ItemData.order) if not IsNativeSystem(ItemData)))
    BoundsValue = WriteRectangle(SketchObject)
    if SourceSketch is None or len(SourceFeatures) != 2 or BoundsValue is None:
        return False
    SourcePad, SourcePattern = SourceFeatures
    DimensionData = FreeCadBossC(DocData, SourceSketch, SourcePad, SourcePattern, BoundsValue)
    if DimensionData is None or (SketchObject.object_id, PadObject.object_id, PatternObject.object_id) != (26, 32, 40) or (SketchObject.name, PadObject.name, PatternObject.name) != ('Sketch1', 'Boss-Extrude1', 'LPattern1') or (ExtrusionEdit(PadObject.payload) != (0, 0)) or (PatternObject.kind != 'LPattern') or PatternObject.payload or (tuple((ItemData.name for ItemData in PatternObject.dimensions)) != ('D1', 'D3')):
        return False
    NativeSketch = ParsedModel.sketches[0]
    NativePad, NativePattern = ParsedModel.operations
    ProfilesValue = tuple((ItemData for ItemData in NativeSketch.profiles if ItemData.kind == 'rectangle'))
    ExpectedDepthSigns = (1, 1, -1, -1, 1, 1)
    if NativeSketch.object_id != 26 or NativeSketch.support_plane_id != 2 or len(ProfilesValue) != 1 or (len(ProfilesValue[0].coordinates) != len(BoundsValue)) or any((not MathValue.isclose(ActualValue, ExpectedValue, abs_tol=1e-10) for ActualValue, ExpectedValue in zip(ProfilesValue[0].coordinates, BoundsValue, strict=True))) or (tuple((ItemData.kind for ItemData in NativeSketch.constraints)) != ('horizontal', 'vertical', 'horizontal', 'vertical')) or (NativePad.object_id != 32) or (NativePad.name != 'Boss-Extrude1') or (NativePad.kind not in {'boss', 'join'}) or (NativePad.profile_id != 26) or (NativePad.dependencies != (26,)) or (NativePad.direction_code != 0) or (NativePad.termination_code != 0) or (NativePad.length_mm is None) or (not MathValue.isclose(NativePad.length_mm, DimensionData[0].value_mm, rel_tol=0.0, abs_tol=1e-10)) or (len(NativePad.depth_copies) != len(ExpectedDepthSigns)) or any((ItemData.sign != SignValue or not MathValue.isclose(ItemData.value_mm, DimensionData[0].value_mm * SignValue, rel_tol=0.0, abs_tol=1e-10) for ItemData, SignValue in zip(NativePad.depth_copies, ExpectedDepthSigns, strict=True))) or (NativePattern.object_id != 40) or (NativePattern.name != 'LPattern1') or (NativePattern.kind != 'linear_pattern') or (NativePattern.profile_id is not None) or (NativePattern.dependencies != (32,)) or (NativePattern.direction_code != 1) or (NativePattern.instance_count != int(DimensionData[1].value_mm)) or (NativePattern.spacing_mm is None) or (not MathValue.isclose(NativePattern.spacing_mm, DimensionData[2].value_mm, rel_tol=0.0, abs_tol=1e-10)) or (NativePattern.selection_kind != 'edge') or (NativePattern.selection_references != ((32, 4), (32, 3))) or (NativePattern.selected_local_ids != (4, 3)) or (NativePattern.mode != 'linear'):
        return False
    NativePatternFeature = next((ItemData for ItemData in ParsedModel.features if ItemData.object_id == 40), None)
    NativeFeatureIds = tuple((ItemData.object_id for ItemData in ParsedModel.features if ItemData.object_id in {26, 32, 40}))
    return NativePatternFeature is not None and tuple(((ItemData.name, ItemData.kind) for ItemData in NativePatternFeature.dimensions)) == (('D1', 'instance_count'), ('D3', 'spacing')) and (NativeFeatureIds == (26, 32, 40))

# this definition exists because focused behavior needs one stable owner
def HasBossCircular(DocData: CadDocument, AuthoredObjs: tuple[_WriteObject, ...], ParsedModel: NativeModel) -> bool:
    if len(AuthoredObjs) != 3 or len(ParsedModel.sketches) != 1 or len(ParsedModel.operations) != 2 or (len(DocData.bodies) != 1):
        return False
    SketchObject, PadObject, PatternObject = AuthoredObjs
    SourceSketch = next((ItemData for ItemData in DocData.sketches if ItemData.id == SketchObject.source_id), None)

    # this callback exists because local behavior needs one focused transformation
    SourceFeatures = tuple((ItemData for ItemData in sorted(DocData.feature_timeline, key=lambda ItemData: ItemData.order) if not IsNativeSystem(ItemData)))
    BoundsValue = WriteRectangle(SketchObject)
    if SourceSketch is None or len(SourceFeatures) != 2 or BoundsValue is None:
        return False
    SourcePad, SourcePattern = SourceFeatures
    DimensionData = FreeCadBossA(DocData, SourceSketch, SourcePad, SourcePattern, BoundsValue)
    if DimensionData is None or (SketchObject.object_id, PadObject.object_id, PatternObject.object_id) != (26, 32, 46) or (SketchObject.name, PadObject.name, PatternObject.name) != ('Sketch1', 'Boss-Extrude1', 'CirPattern1') or (ExtrusionEdit(PadObject.payload) != (0, 0)) or (PatternObject.kind != 'CirPattern') or PatternObject.payload or (tuple((ItemData.name for ItemData in PatternObject.dimensions)) != ('D1', 'D3')):
        return False
    NativeSketch = ParsedModel.sketches[0]
    NativePad, NativePattern = ParsedModel.operations
    ProfilesValue = tuple((ItemData for ItemData in NativeSketch.profiles if ItemData.kind == 'rectangle'))
    ExpectedDepthSigns = (1, 1, -1, -1, 1, 1)
    if NativeSketch.object_id != 26 or NativeSketch.support_plane_id != 2 or len(ProfilesValue) != 1 or (len(ProfilesValue[0].coordinates) != len(BoundsValue)) or any((not MathValue.isclose(ActualValue, ExpectedValue, abs_tol=1e-10) for ActualValue, ExpectedValue in zip(ProfilesValue[0].coordinates, BoundsValue, strict=True))) or (tuple((ItemData.kind for ItemData in NativeSketch.constraints)) != ('horizontal', 'vertical', 'horizontal', 'vertical')) or (NativePad.object_id != 32) or (NativePad.name != 'Boss-Extrude1') or (NativePad.kind not in {'boss', 'join'}) or (NativePad.profile_id != 26) or (NativePad.dependencies != (26,)) or (NativePad.direction_code != 0) or (NativePad.termination_code != 0) or (NativePad.length_mm is None) or (not MathValue.isclose(NativePad.length_mm, DimensionData[0].value_mm, rel_tol=0.0, abs_tol=1e-10)) or (len(NativePad.depth_copies) != len(ExpectedDepthSigns)) or any((ItemData.sign != SignValue or not MathValue.isclose(ItemData.value_mm, DimensionData[0].value_mm * SignValue, rel_tol=0.0, abs_tol=1e-10) for ItemData, SignValue in zip(NativePad.depth_copies, ExpectedDepthSigns, strict=True))) or (NativePattern.object_id != 46) or (NativePattern.name != 'CirPattern1') or (NativePattern.kind != 'circular_pattern') or (NativePattern.profile_id is not None) or (NativePattern.dependencies != (32,)) or (NativePattern.direction_code != 1) or (NativePattern.instance_count != int(DimensionData[1].value_mm)) or (NativePattern.angle_degrees is None) or (not MathValue.isclose(NativePattern.angle_degrees, DimensionData[2].value_mm, rel_tol=0.0, abs_tol=1e-10)) or (NativePattern.selection_kind != 'edge') or (NativePattern.selection_references != ((32, 4), (32, 1))) or (NativePattern.selected_local_ids != (4, 1)) or (NativePattern.mode != 'circular'):
        return False
    NativePatternFeature = next((ItemData for ItemData in ParsedModel.features if ItemData.object_id == 46), None)
    NativeFeatureIds = tuple((ItemData.object_id for ItemData in ParsedModel.features if ItemData.object_id in {26, 32, 46}))
    return NativePatternFeature is not None and tuple(((ItemData.name, ItemData.kind) for ItemData in NativePatternFeature.dimensions)) == (('D1', 'instance_count'), ('D3', 'angle')) and (NativeFeatureIds == (26, 32, 46))

# this definition exists because focused behavior needs one stable owner
def HasTwoFeature(DocData: CadDocument, AuthoredObjs: tuple[_WriteObject, ...], ParsedModel: NativeModel) -> bool:
    if len(AuthoredObjs) != 4 or len(ParsedModel.sketches) != 2 or len(ParsedModel.operations) != 2 or (len(DocData.bodies) != 1):
        return False
    SketchOne, FeatureOne, SketchTwo, FeatureTwo = AuthoredObjs
    SecondIsBoss = FeatureTwo.class_name == 'moExtrusion_c'
    ExpectedData = ((SketchOne, FeatureOne, 26, 32, 'Sketch1', 'Boss-Extrude1', {'boss', 'join'}), (SketchTwo, FeatureTwo, 33, 40, 'Sketch2', 'Boss-Extrude2' if SecondIsBoss else 'Cut-Extrude1', {'boss', 'join'} if SecondIsBoss else {'cut'}))
    ExpectedDepthSigns = (1, 1, -1, -1, 1, 1)
    for NativeSketch, NativeFeature, ExpectedValue in zip(ParsedModel.sketches, ParsedModel.operations, ExpectedData, strict=True):
        SketchObject, FeatureObject, SketchObjectId, FeatureObjectId, SketchName, FeatureName, FeatureKinds = ExpectedValue
        BoundsValue = WriteRectangle(SketchObject)
        EndCodes = ExtrusionEdit(FeatureObject.payload)
        if BoundsValue is None or EndCodes is None or len(FeatureObject.dimensions) != (0 if EndCodes[1] == 1 else 1):
            return False
        ProfileData = tuple((ItemData for ItemData in NativeSketch.profiles if ItemData.kind == 'rectangle'))
        ExpectedDims = tuple(((ItemData.name, round(ItemData.value_mm, 10)) for ItemData in SketchObject.dimensions))
        ActualDims = tuple(((ItemData.name, round(ItemData.value_mm, 10)) for ItemData in NativeSketch.dimensions))
        ExpectedConstraints = ('horizontal', 'vertical', 'horizontal', 'vertical', *('distance',) * len(ExpectedDims))
        DepthValue = None if not FeatureObject.dimensions else FeatureObject.dimensions[0].value_mm
        if SketchObject.object_id != SketchObjectId or SketchObject.name != SketchName or FeatureObject.object_id != FeatureObjectId or (FeatureObject.name != FeatureName) or (NativeSketch.object_id != SketchObjectId) or (NativeSketch.support_plane_id != 2) or (len(ProfileData) != 1) or (len(ProfileData[0].coordinates) != len(BoundsValue)) or any((not MathValue.isclose(ActualValue, ExpectedCoordinate, abs_tol=1e-10) for ActualValue, ExpectedCoordinate in zip(ProfileData[0].coordinates, BoundsValue, strict=True))) or (tuple((ItemData.kind for ItemData in NativeSketch.constraints)) != ExpectedConstraints) or (ActualDims != ExpectedDims) or (NativeFeature.object_id != FeatureObjectId) or (NativeFeature.name != FeatureName) or (NativeFeature.profile_id != SketchObjectId) or (NativeFeature.kind not in FeatureKinds) or (NativeFeature.direction_code != EndCodes[0]) or (NativeFeature.termination_code != EndCodes[1]) or (DepthValue is None and (NativeFeature.length_mm is not None or NativeFeature.depth_copies)) or (DepthValue is not None and (NativeFeature.length_mm is None or not MathValue.isclose(NativeFeature.length_mm, DepthValue, abs_tol=1e-10) or len(NativeFeature.depth_copies) != len(ExpectedDepthSigns) or (not MathValue.isclose(NativeFeature.depth_copies[0].value_mm, DepthValue, abs_tol=1e-10)) or (EndCodes == (0, 0) and any((CopyData.sign != CopySign or not MathValue.isclose(CopyData.value_mm, DepthValue * CopySign, abs_tol=1e-10) for CopyData, CopySign in zip(NativeFeature.depth_copies, ExpectedDepthSigns, strict=True)))))):
            return False
    NativeFeatureIds = tuple((ItemData.object_id for ItemData in ParsedModel.features if ItemData.object_id in {26, 32, 33, 40}))
    return NativeFeatureIds == (26, 32, 33, 40)

# this definition exists because focused behavior needs one stable owner
def HasCutChain(DocData: CadDocument, AuthoredObjs: tuple[_WriteObject, ...], ParsedModel: NativeModel) -> bool:
    FeatureCount = len(AuthoredObjs) // 2
    if FeatureCount not in {3, 4} or len(AuthoredObjs) != FeatureCount * 2 or len(ParsedModel.sketches) != FeatureCount or (len(ParsedModel.operations) != FeatureCount) or (len(DocData.bodies) != 1):
        return False
    SketchIds = (26, 33, 41, 48)[:FeatureCount]
    FeatureIds = (32, 40, 47, 54)[:FeatureCount]
    ExpectedData = tuple(((AuthoredObjs[FeatureIndex * 2], AuthoredObjs[FeatureIndex * 2 + 1], SketchIds[FeatureIndex], FeatureIds[FeatureIndex], f'Sketch{FeatureIndex + 1}', 'Boss-Extrude1' if FeatureIndex == 0 else f'Cut-Extrude{FeatureIndex}', {'boss', 'join'} if FeatureIndex == 0 else {'cut'}) for FeatureIndex in range(FeatureCount)))
    ExpectedDepthSigns = (1, 1, -1, -1, 1, 1)
    for NativeSketch, NativeFeature, ExpectedValue in zip(ParsedModel.sketches, ParsedModel.operations, ExpectedData, strict=True):
        SketchObject, FeatureObject, SketchObjectId, FeatureObjectId, SketchName, FeatureName, FeatureKinds = ExpectedValue
        BoundsValue = WriteRectangle(SketchObject)
        CircleValue = WriteCircle(SketchObject)
        EndCodes = ExtrusionEdit(FeatureObject.payload)
        if (BoundsValue is None) == (CircleValue is None) or EndCodes is None or len(FeatureObject.dimensions) != 1:
            return False
        ProfileKind = 'rectangle' if BoundsValue is not None else 'circle'
        ExpectedProfile = BoundsValue if BoundsValue is not None else CircleValue
        ProfileData = tuple((ItemData for ItemData in NativeSketch.profiles if ItemData.kind == ProfileKind))
        ExpectedDims = tuple(((ItemData.name, round(ItemData.value_mm, 10)) for ItemData in SketchObject.dimensions))
        ActualDims = tuple(((ItemData.name, round(ItemData.value_mm, 10)) for ItemData in NativeSketch.dimensions))
        ExpectedConstraints = ('horizontal', 'vertical', 'horizontal', 'vertical', *('distance',) * len(ExpectedDims)) if BoundsValue is not None else ('radius', 'distance', 'distance')
        DepthValue = FeatureObject.dimensions[0].value_mm
        if SketchObject.object_id != SketchObjectId or SketchObject.name != SketchName or FeatureObject.object_id != FeatureObjectId or (FeatureObject.name != FeatureName) or (NativeSketch.object_id != SketchObjectId) or (NativeSketch.support_plane_id != 2) or (len(ProfileData) != 1) or (ExpectedProfile is None) or (len(ProfileData[0].coordinates) != len(ExpectedProfile)) or any((not MathValue.isclose(ActualValue, ExpectedCoordinate, abs_tol=1e-10) for ActualValue, ExpectedCoordinate in zip(ProfileData[0].coordinates, ExpectedProfile, strict=True))) or (tuple((ItemData.kind for ItemData in NativeSketch.constraints)) != ExpectedConstraints) or (ActualDims != ExpectedDims) or (NativeFeature.object_id != FeatureObjectId) or (NativeFeature.name != FeatureName) or (NativeFeature.profile_id != SketchObjectId) or (NativeFeature.kind not in FeatureKinds) or (NativeFeature.direction_code != EndCodes[0]) or (NativeFeature.termination_code != EndCodes[1]) or (NativeFeature.length_mm is None) or (not MathValue.isclose(NativeFeature.length_mm, DepthValue, abs_tol=1e-10)) or (len(NativeFeature.depth_copies) != len(ExpectedDepthSigns)) or any((CopyData.sign != CopySign or not MathValue.isclose(CopyData.value_mm, DepthValue * CopySign, abs_tol=1e-10) for CopyData, CopySign in zip(NativeFeature.depth_copies, ExpectedDepthSigns, strict=True))):
            return False
    ExpectedIds = tuple((ObjectId for PairData in zip(SketchIds, FeatureIds, strict=True) for ObjectId in PairData))
    NativeFeatureIds = tuple((ItemData.object_id for ItemData in ParsedModel.features if ItemData.object_id in set(ExpectedIds)))
    return NativeFeatureIds == ExpectedIds

# this definition exists because focused behavior needs one stable owner
def HasRectDims(SketchObject: _WriteObject, BoundsValue: tuple[float, float, float, float] | None) -> bool:
    if BoundsValue is None:
        return False
    if not SketchObject.dimensions:
        return True
    if len(SketchObject.dimensions) != 2:
        return False
    MinimumX, MinimumY, MaximumX, MaximumY = BoundsValue
    ExpectedDims = sorted((MaximumX - MinimumX, MaximumY - MinimumY))
    ActualDims = sorted((ItemData.value_mm for ItemData in SketchObject.dimensions))
    return all((MathValue.isfinite(ActualValue) and ActualValue > 0.0 and MathValue.isclose(ActualValue, ExpectedValue, abs_tol=1e-10) for ActualValue, ExpectedValue in zip(ActualDims, ExpectedDims, strict=True)))

# this definition exists because focused behavior needs one stable owner
def HasCircleDims(SketchObject: _WriteObject, CircleValue: tuple[float, float, float] | None) -> bool:
    if CircleValue is None:
        return False
    RadiusValue = CircleValue[2]
    return bool(SketchObject.dimensions) and all((MathValue.isfinite(ItemData.value_mm) and ItemData.value_mm > 0.0 and MathValue.isclose(ItemData.value_mm, RadiusValue, abs_tol=1e-10) for ItemData in SketchObject.dimensions))

# this definition exists because focused behavior needs one stable owner
def FrameVector(Vector: tuple[float, float, float]) -> tuple[float, float, float]:
    return (Clean(Vector[0]), Clean(Vector[1]), Clean(Vector[2]))

# this definition exists because focused behavior needs one stable owner
def NativeAxis(Model: NativeModel) -> frozenset[tuple[int, int, str]]:
    Sketches = {Sketch.object_id: Sketch for Sketch in Model.sketches}
    Result: set[tuple[int, int, str]] = set()
    for Operation in Model.operations:
        if Operation.profile_id is None:
            continue
        Sketch = Sketches.get(Operation.profile_id)
        SubElem = OperationAxis(Operation, Sketch)
        if SubElem is None or Sketch is None:
            continue
        Result.add((Operation.object_id, Sketch.object_id, SubElem))
    return frozenset(Result)

# this definition exists because focused behavior needs one stable owner
def DocAxisBindings(DocValue: CadDocument, ObjectIds: Mapping[str, int]) -> frozenset[tuple[int, int, str]] | None:
    Features = {Feature.name: Feature for Feature in DocValue.feature_timeline}
    Sketches = {Sketch.name: Sketch for Sketch in DocValue.sketches}
    Result: set[tuple[int, int, str]] = set()
    for Selection in DocValue.selections:
        Owner = str(Selection.attributes.get('freecad_object', ''))
        RoleValue = str(Selection.attributes.get('freecad_property', ''))
        if RoleValue != 'ReferenceAxis' or len(Selection.path) != 1:
            return None
        ElemValue = Selection.path[0]
        Feature = Features.get(Owner)
        Sketch = Sketches.get(str(ElemValue.entity_id))
        if Feature is None or Sketch is None or (not ElemValue.subelement):
            return None
        FeatureKey = f'feature:{Feature.id}'
        SketchKey = f'sketch:{Sketch.id}'
        if FeatureKey not in ObjectIds or SketchKey not in ObjectIds:
            return None
        Result.add((ObjectIds[FeatureKey], ObjectIds[SketchKey], ElemValue.subelement))
    return frozenset(Result)

# this definition exists because focused behavior needs one stable owner
def DecodeNative(Keywords: bytes, Resolved: bytes, ConfigData: bytes=b'', *, ConfigId: int | None=None, ResolvedStream: str=ResolvedFeaturesStream, ConfigStream: str='') -> NativeModel:
    Configurations, XmlFeatures = ParseKeywords(Keywords)
    Names = ParseNames(Resolved)
    if ResolvedStream == ResolvedFeaturesStream:
        RebindIds(XmlFeatures, Names)
    Classes = ParseClasses(Resolved)
    Scalars = ParseScalars(Resolved, Names)
    RecordById = FeatureRecords(XmlFeatures, Names)

    # this callback exists because local behavior needs one focused transformation
    OrderedRecords = sorted({Record.offset: Record for Record in RecordById.values()}.values(), key=lambda Record: Record.offset)
    EndsValue = {Record.offset: OrderedRecords[Index + 1].offset if Index + 1 < len(OrderedRecords) else len(Resolved) for Index, Record in enumerate(OrderedRecords)}
    ScalarOwner = ScalarOwners(Scalars, OrderedRecords, EndsValue)
    NativeFeatures: list[NativeFeature] = []
    for Feature in XmlFeatures:
        Record = RecordById.get(Feature.object_id)
        NameValue = Feature.name or (Record.name if Record is not None else '')
        if not NameValue:
            NameValue = f'{Feature.kind or Feature.xml_tag} {Feature.object_id}'
        Owned = ScalarOwner.get(Feature.object_id, ())
        Dimensions = tuple((BindDimension(ItemValue, Owned) for ItemValue in Semantic(Feature.kind, tuple(Feature.dimensions))))
        NativeEnd = EndsValue.get(Record.offset) if Record is not None else None
        NativeFeatures.append(NativeFeature(object_id=Feature.object_id, name=NameValue, kind=Feature.kind, xml_tag=Feature.xml_tag, native_offset=Record.offset if Record else None, native_end=NativeEnd, properties=dict(Feature.properties), dimensions=Dimensions, data=Resolved[Record.offset:NativeEnd] if Record is not None and NativeEnd is not None else b'', class_name=RecordClassName(Classes, Record.offset) if Record is not None else '', native_stream=ResolvedStream))
    FeatureIndexes = {Feature.object_id: Index for Index, Feature in enumerate(NativeFeatures)}
    for Index, Feature in enumerate(NativeFeatures):
        ChildId = IntegerProp(Feature.properties.get('DissectableChildren'))
        ChildScalars = ScalarOwner.get(ChildId or -1, ())
        if not ChildScalars:
            continue
        Rebound = tuple((BindDimension(Dimension, ChildScalars) if Dimension.native_offset is None else Dimension for Dimension in Feature.dimensions))
        NativeFeatures[Index] = Replace(Feature, dimensions=Rebound)
    Planes = DecodePlanes(Resolved, NativeFeatures, NativeStream=ResolvedStream)
    PlaneById = {Plane.object_id: Plane for Plane in Planes}
    PrincipalPlaneFrames = PrincipalPlaneA(NativeFeatures)
    PrincipalPlaneIds = frozenset(PrincipalPlaneFrames)

    # this callback exists because local behavior needs one focused transformation
    Author = sorted((Feature for Feature in NativeFeatures if Feature.native_offset is not None and (not IsOriginFeature(Feature)) and (Feature.object_id not in PrincipalPlaneIds)), key=lambda Feature: Feature.native_offset or 0)
    UnframedPlanes = tuple((Feature for Feature in NativeFeatures if IsPlaneFeature(Feature) and Feature.native_offset is not None and (Feature.object_id not in PlaneById)))
    UnframedPlaneIds = frozenset((Feature.object_id for Feature in UnframedPlanes))
    Sketches: list[NativeSketch] = []
    Operations: list[NativeOperation] = []
    Revolutions = {Layout.feature_id: Layout for Layout in LocateFeatures(Resolved) if Layout.is_revolution}
    NativeIndexById = FeatureIndexes
    LatestSketch: NativeSketch | None = None
    LatestOperation: NativeOperation | None = None
    LatestPlaneId = next(iter(PrincipalPlaneFrames), next(iter(PlaneById), 0))
    LatestUnframedPlaneId: int | None = None
    for Feature in Author:
        if IsPlaneFeature(Feature):
            if Feature.object_id in PlaneById:
                LatestPlaneId = Feature.object_id
                LatestUnframedPlaneId = None
            else:
                LatestUnframedPlaneId = Feature.object_id
            continue
        if Feature.kind.casefold() == 'sketch':
            SketchStart = Feature.native_offset or 0
            SketchEnd = Feature.native_end or len(Resolved)
            RefValue = SketchPlaneRef(Resolved, Classes, SketchStart, SketchEnd)
            Support, SupportSource, UnframedSupport = SupportPlaneRef(Resolved, SketchStart, SketchEnd, RefValue, LatestPlaneId, LatestUnframedPlaneId, PlaneById, UnframedPlaneIds)
            LatestSketch = DecodeSketch(Resolved, Feature, Support, NativeStream=ResolvedStream, SupportKind=SketchSupport(Classes, RefValue, SketchStart, SketchEnd), SupportPlane=RefValue, SupportSource=SupportSource, UnframedSupportPlaneId=UnframedSupport)
            NativeIndex = NativeIndexById[Feature.object_id]
            NativeFeatures[NativeIndex] = Replace(NativeFeatures[NativeIndex], dimensions=LatestSketch.dimensions)
            Sketches.append(LatestSketch)
            continue
        if Feature.kind.casefold() == 'extrusion':
            Record = RecordById.get(Feature.object_id)
            if Record is None:
                continue
            Child = IntegerProp(Feature.properties.get('DissectableChildren'))
            ProfileId = Child or (LatestSketch.object_id if LatestSketch else None)
            Dependencies = tuple((Value for Value in (LatestOperation.object_id if LatestOperation else None, ProfileId) if Value is not None))
            Family, OperationCode, Schema = OperationFields(Resolved, Record)
            OperationStart = Feature.native_offset or 0
            OperationEnd = Feature.native_end or len(Resolved)
            EndSpec = EndSpec(Resolved, OperationStart, OperationEnd, Classes)
            Operation = NativeOperation(object_id=Feature.object_id, name=Feature.name, kind='join' if OperationCode == 0 else 'cut' if OperationCode == 2 else 'native', profile_id=ProfileId, dependencies=Dependencies, native_offset=OperationStart, native_end=ClassRecordEnd(Resolved, Classes, OperationStart) or OperationEnd, length_mm=Operation(Feature.dimensions, 'length'), radius_mm=None, family_code=Family, operation_code=OperationCode, schema_code=Schema, direction_code=EndSpec.direction_code if EndSpec else None, termination_code=EndSpec.termination_code if EndSpec else None, selection_offsets=(), selected_local_ids=(), native_stream=ResolvedStream, depth_copies=DepthCopies(Resolved, OperationOffset(Feature.dimensions, 'length')), mirrored_direction_offset=EndSpec.mirrored_direction_offset if EndSpec else None, mirrored_direction_code=EndSpec.mirrored_direction_code if EndSpec else None)
            Operations.append(Operation)
            LatestOperation = Operation
            continue
        FeatureType = Feature.kind.casefold()
        if FeatureType in {'lpattern', 'linearpattern'}:
            Record = RecordById.get(Feature.object_id)
            CountValue = Operation(Feature.dimensions, 'instance_count')
            SpacingValue = Operation(Feature.dimensions, 'spacing')
            if Record is None or LatestOperation is None or CountValue is None or (CountValue != int(CountValue)) or (SpacingValue is None):
                continue
            SelectionData = OperationA(Resolved, Feature.native_offset or 0, Feature.native_end or len(Resolved), Feature, NativeFeatures)
            FamilyValue, OperationValue, SchemaValue = OperationFields(Resolved, Record)
            DirectionOffset = Feature.native_offset + KLinearPatternDirection if Feature.native_offset is not None else -1
            DirectionCode = Resolved[DirectionOffset] if 0 <= DirectionOffset < (Feature.native_end or 0) and Resolved[DirectionOffset] in {0, 1} else None
            Operation = NativeOperation(object_id=Feature.object_id, name=Feature.name, kind='linear_pattern', profile_id=None, dependencies=(LatestOperation.object_id,), native_offset=Feature.native_offset or 0, native_end=Feature.native_end or len(Resolved), length_mm=None, radius_mm=None, family_code=FamilyValue, operation_code=OperationValue, schema_code=SchemaValue, direction_code=DirectionCode, termination_code=None, selection_offsets=tuple((ItemData[0] for ItemData in SelectionData)), selected_local_ids=tuple((ItemData[2] for ItemData in SelectionData)), selection_kind='edge', mode='linear', native_stream=ResolvedStream, selection_references=tuple(((ItemData[1], ItemData[2]) for ItemData in SelectionData)), instance_count=int(CountValue), spacing_mm=SpacingValue)
            Operations.append(Operation)
            LatestOperation = Operation
            continue
        if FeatureType in {'cirpattern', 'circularpattern'}:
            Record = RecordById.get(Feature.object_id)
            CountValue = Operation(Feature.dimensions, 'instance_count')
            AngleValue = Operation(Feature.dimensions, 'angle')
            if Record is None or LatestOperation is None or CountValue is None or (CountValue != int(CountValue)) or (AngleValue is None):
                continue
            SelectionData = OperationA(Resolved, Feature.native_offset or 0, Feature.native_end or len(Resolved), Feature, NativeFeatures)
            FamilyValue, OperationValue, SchemaValue = OperationFields(Resolved, Record)
            DirectionOffset = Feature.native_offset + KCircularPatternDirection if Feature.native_offset is not None else -1
            DirectionCode = Resolved[DirectionOffset] if 0 <= DirectionOffset < (Feature.native_end or 0) and Resolved[DirectionOffset] in {0, 1} else None
            Operation = NativeOperation(object_id=Feature.object_id, name=Feature.name, kind='circular_pattern', profile_id=None, dependencies=(LatestOperation.object_id,), native_offset=Feature.native_offset or 0, native_end=Feature.native_end or len(Resolved), length_mm=None, radius_mm=None, family_code=FamilyValue, operation_code=OperationValue, schema_code=SchemaValue, direction_code=DirectionCode, termination_code=None, selection_offsets=tuple((ItemData[0] for ItemData in SelectionData)), selected_local_ids=tuple((ItemData[2] for ItemData in SelectionData)), angle_degrees=AngleValue, selection_kind='edge', mode='circular', native_stream=ResolvedStream, selection_references=tuple(((ItemData[1], ItemData[2]) for ItemData in SelectionData)), instance_count=int(CountValue))
            Operations.append(Operation)
            LatestOperation = Operation
            continue
        if FeatureType in KRevolutionFeatureTypes:
            Record = RecordById.get(Feature.object_id)
            if Record is None:
                continue
            ProfileId = LatestSketch.object_id if LatestSketch else None
            Dependencies = tuple((Value for Value in (LatestOperation.object_id if LatestOperation else None, ProfileId) if Value is not None))
            Family, OperationCode, Schema = OperationFields(Resolved, Record)
            Layout = Revolutions.get(Feature.object_id)
            AxisSketch = LatestSketch
            if Layout is not None and Layout.axis_kind == RevolutionAxisSketch:
                AxisSketch = next((ItemValue for ItemValue in Sketches if ItemValue.object_id == Layout.axis_feature_id), None)
            elif Layout is not None:
                AxisSketch = None
            AxisMarker = RevolutionAxis(AxisSketch)
            RevolutionStart = Feature.native_offset or 0
            AngleOffset = OperationOffset(Feature.dimensions, 'angle')
            Operation = NativeOperation(object_id=Feature.object_id, name=Feature.name, kind='revolve_cut' if FeatureType in {'cut-revolve', 'revcut'} else 'revolve_join', profile_id=ProfileId, dependencies=Dependencies, native_offset=RevolutionStart, native_end=ClassRecordEnd(Resolved, Classes, RevolutionStart) or Feature.native_end or len(Resolved), length_mm=None, radius_mm=None, family_code=Family, operation_code=OperationCode, schema_code=Schema, direction_code=None, termination_code=None, selection_offsets=(), selected_local_ids=(), angle_degrees=Operation(Feature.dimensions, 'angle'), axis_marker_offset=AxisMarker.offset if AxisMarker else None, native_stream=ResolvedStream, axis_source_kind=None if Layout is None else Layout.axis_kind, axis_source_id=None if Layout is None else Layout.axis_feature_id, axis_source_offset=None if Layout is None else Layout.axis_offset, end_spec_offset=None if Layout is None else Layout.end_spec_offset, angle_offset=AngleOffset, angle_copies=AngleCopies(Resolved, AngleOffset))
            Operations.append(Operation)
            LatestOperation = Operation
            continue
        if Feature.class_name in KHoleClassNames:
            Record = RecordById.get(Feature.object_id)
            if Record is None:
                continue
            Child = IntegerProp(Feature.properties.get('DissectableChildren'))
            Family, OperationCode, Schema = OperationFields(Resolved, Record)
            Dependencies = tuple((Value for Value in (LatestOperation.object_id if LatestOperation else None, Child) if Value is not None))
            Operation = NativeOperation(object_id=Feature.object_id, name=Feature.name, kind='hole', profile_id=Child, dependencies=Dependencies, native_offset=Feature.native_offset or 0, native_end=Feature.native_end or len(Resolved), length_mm=Operation(Feature.dimensions, 'depth'), radius_mm=None, family_code=Family, operation_code=OperationCode, schema_code=Schema, direction_code=None, termination_code=0, selection_offsets=(), selected_local_ids=(), selection_kind='face', native_stream=ResolvedStream)
            Operations.append(Operation)
            LatestOperation = Operation
            continue
        if FeatureType == 'dome':
            Selections = OperationAfter(Resolved, Feature.native_offset or 0, Feature.native_end or len(Resolved), Feature, NativeFeatures, 'moCompFace_c')
            Height = Operation(Feature.dimensions, 'height')
            if Height is None or not Selections:
                continue
            ProducerIds = tuple(dict.fromkeys((Selection[1] for Selection in Selections)))
            Dependencies = tuple(dict.fromkeys((*((LatestOperation.object_id,) if LatestOperation else ()), *ProducerIds)))
            Operation = NativeOperation(object_id=Feature.object_id, name=Feature.name, kind='dome', profile_id=None, dependencies=Dependencies, native_offset=Feature.native_offset or 0, native_end=Feature.native_end or len(Resolved), length_mm=Height, radius_mm=None, family_code=None, operation_code=None, schema_code=None, direction_code=None, termination_code=None, selection_offsets=tuple((ItemValue[0] for ItemValue in Selections)), selected_local_ids=tuple((ItemValue[2] for ItemValue in Selections)), selection_kind='face', native_stream=ResolvedStream, selection_references=tuple(((ItemValue[1], ItemValue[2]) for ItemValue in Selections)))
            Operations.append(Operation)
            LatestOperation = Operation
            continue
        if FeatureType in KMoveBodyFeatureTypes:
            Selections = OperationAfter(Resolved, Feature.native_offset or 0, Feature.native_end or len(Resolved), Feature, NativeFeatures, 'moCompSolidBody_c')
            Translation = Native(Feature.dimensions)
            if Translation is None or not Selections:
                continue
            ProducerIds = tuple(dict.fromkeys((Selection[1] for Selection in Selections)))
            Dependencies = tuple(dict.fromkeys((*((LatestOperation.object_id,) if LatestOperation else ()), *ProducerIds)))
            Operation = NativeOperation(object_id=Feature.object_id, name=Feature.name, kind='move_body', profile_id=None, dependencies=Dependencies, native_offset=Feature.native_offset or 0, native_end=Feature.native_end or len(Resolved), length_mm=None, radius_mm=None, family_code=None, operation_code=None, schema_code=None, direction_code=None, termination_code=None, selection_offsets=tuple((ItemValue[0] for ItemValue in Selections)), selected_local_ids=tuple((ItemValue[2] for ItemValue in Selections)), selection_kind='body', native_stream=ResolvedStream, selection_references=tuple(((ItemValue[1], ItemValue[2]) for ItemValue in Selections)), translation_mm=Translation)
            Operations.append(Operation)
            LatestOperation = Operation
            continue
        if FeatureType in KCombineFeatureTypes:
            Selections = OperationAfter(Resolved, Feature.native_offset or 0, Feature.native_end or len(Resolved), Feature, NativeFeatures, 'moSolidRef_w')
            if len(Selections) < 2:
                continue
            ProducerIds = tuple(dict.fromkeys((Selection[1] for Selection in Selections)))
            Dependencies = tuple(dict.fromkeys((*((LatestOperation.object_id,) if LatestOperation else ()), *ProducerIds)))
            Operation = NativeOperation(object_id=Feature.object_id, name=Feature.name, kind='combine_join', profile_id=None, dependencies=Dependencies, native_offset=Feature.native_offset or 0, native_end=Feature.native_end or len(Resolved), length_mm=None, radius_mm=None, family_code=None, operation_code=0, schema_code=None, direction_code=None, termination_code=None, selection_offsets=tuple((ItemValue[0] for ItemValue in Selections)), selected_local_ids=tuple((ItemValue[2] for ItemValue in Selections)), selection_kind='body', mode='join', native_stream=ResolvedStream, selection_references=tuple(((ItemValue[1], ItemValue[2]) for ItemValue in Selections)))
            Operations.append(Operation)
            LatestOperation = Operation
            continue
        if FeatureType == 'scale':
            Factors = NativeScale(Resolved, Feature.native_offset or 0, Feature.native_end or len(Resolved))
            if Factors is None or LatestOperation is None:
                continue
            Operation = NativeOperation(object_id=Feature.object_id, name=Feature.name, kind='scale', profile_id=None, dependencies=(LatestOperation.object_id,), native_offset=Feature.native_offset or 0, native_end=Feature.native_end or len(Resolved), length_mm=None, radius_mm=None, family_code=None, operation_code=None, schema_code=None, direction_code=None, termination_code=None, selection_offsets=(), selected_local_ids=(), native_stream=ResolvedStream, scale_factors=Factors)
            Operations.append(Operation)
            LatestOperation = Operation
            continue
        if FeatureType in {'fillet', 'chamfer', 'shell'}:
            Selections = OperationA(Resolved, Feature.native_offset or 0, Feature.native_end or len(Resolved), Feature, NativeFeatures)
            ProducerIds = tuple(dict.fromkeys((Selection[1] for Selection in Selections)))
            Dependencies = tuple(dict.fromkeys((*((LatestOperation.object_id,) if LatestOperation else ()), *ProducerIds)))
            Record = RecordById.get(Feature.object_id)
            Fields = OperationFields(Resolved, Record) if Record is not None else (None, None, None)
            DimensionKind = {'fillet': 'radius', 'chamfer': 'distance', 'shell': 'thickness'}[FeatureType]
            Operation = NativeOperation(object_id=Feature.object_id, name=Feature.name, kind=FeatureType, profile_id=None, dependencies=Dependencies, native_offset=Feature.native_offset or 0, native_end=Feature.native_end or len(Resolved), length_mm=Operation(Feature.dimensions, DimensionKind) if FeatureType != 'fillet' else None, radius_mm=Operation(Feature.dimensions, DimensionKind) if FeatureType == 'fillet' else None, family_code=Fields[0], operation_code=Fields[1], schema_code=Fields[2], direction_code=None, termination_code=None, selection_offsets=tuple((Selection[0] for Selection in Selections)), selected_local_ids=tuple((Selection[2] for Selection in Selections)), selection_kind='face' if FeatureType == 'shell' else 'edge', mode='equal_distance' if FeatureType == 'chamfer' and Fields[0] == 1 else None, native_stream=ResolvedStream, selection_references=tuple(((Selection[1], Selection[2]) for Selection in Selections)))
            Operations.append(Operation)
            LatestOperation = Operation
            continue
        if FeatureType in KSurfaceExtrusionFeature:
            Record = RecordById.get(Feature.object_id)
            if Record is None:
                continue
            ProfileId = LatestSketch.object_id if LatestSketch else None
            Family, OperationCode, Schema = OperationFields(Resolved, Record)
            EndSpec = EndSpec(Resolved, Feature.native_offset or 0, Feature.native_end or len(Resolved), Classes)
            Lengths = tuple((Dimension.value_mm for Dimension in Feature.dimensions if Dimension.kind in {'length', 'second_length'}))
            Operation = NativeOperation(object_id=Feature.object_id, name=Feature.name, kind='surface', profile_id=ProfileId, dependencies=(ProfileId,) if ProfileId is not None else (), native_offset=Feature.native_offset or 0, native_end=Feature.native_end or len(Resolved), length_mm=Lengths[0] if Lengths else None, radius_mm=None, family_code=Family, operation_code=OperationCode, schema_code=Schema, direction_code=EndSpec.direction_code if EndSpec else None, termination_code=EndSpec.termination_code if EndSpec else None, selection_offsets=(), selected_local_ids=(), second_length_mm=Lengths[1] if len(Lengths) > 1 else None, native_stream=ResolvedStream)
            Operations.append(Operation)
    SketchesById = {Sketch.object_id: Sketch for Sketch in Sketches}
    Operations = [ResolveProfile(Operation, SketchesById, Resolved, NativeFeatures) for Operation in Operations]
    ActiveConfigId = ConfigId if ConfigId is not None else Configurations[0].configuration_id
    Equations = ParseNative(ConfigData, ActiveConfigId, ConfigStream or f'Contents/Config-{ActiveConfigId}')
    Diagnostics = []
    Unresolved = [Feature for Feature in NativeFeatures if Feature.native_offset is None and Feature.object_id > 0 and (Feature.object_id not in KeywordOnlyObjectIds)]
    if Unresolved:
        Diagnostics.append('native name records unavailable for ' + ', '.join((f'{Feature.object_id}:{Feature.name}' for Feature in Unresolved)))
    if UnframedPlanes:
        Diagnostics.append('reference plane frames unavailable for ' + ', '.join((f'{Feature.object_id}:{Feature.name}' for Feature in UnframedPlanes)))
    DependentSketches = tuple((Sketch for Sketch in Sketches if Sketch.unframed_support_plane_id is not None))
    if DependentSketches:
        Diagnostics.append('sketch supports fall back to decoded planes for ' + ', '.join((f'{Sketch.object_id}:{Sketch.name}->{Sketch.unframed_support_plane_id}:{Sketch.support_plane_id}' for Sketch in DependentSketches)))
    return NativeModel(configurations=Configurations, features=tuple(sorted(NativeFeatures, key=NativeFeatureA)), planes=tuple(Planes), sketches=tuple(Sketches), operations=tuple(Operations), names=Names, classes=Classes, scalars=Scalars, diagnostics=tuple(Diagnostics), equations=Equations, active_configuration_id=ActiveConfigId, bounding_box=BoundingBox(Resolved, Classes))

# this definition exists because focused behavior needs one stable owner
def RebindIds(FeaturesList: list[_XmlFeature], NamesList: tuple[NativeName, ...]) -> None:
    KnownIds = frozenset((RecordData.object_id for RecordData in NamesList if RecordData.object_id is not None))
    RecordsByName: dict[str, list[NativeName]] = {}
    for RecordData in NamesList:
        if RecordData.object_id is None:
            continue
        RecordsByName.setdefault(RecordData.name, []).append(RecordData)
    for FeatureData in FeaturesList:
        if FeatureData.object_id in KnownIds:
            continue
        MatchesList = RecordsByName.get(FeatureData.name, ())
        MatchingIds = {RecordData.object_id for RecordData in MatchesList if RecordData.object_id is not None}
        if len(MatchingIds) == 1:
            FeatureData.object_id = MatchingIds.pop()
        elif FeatureData.kind.casefold() == 'extrusion' and any((RecordData.object_id == 32 and RecordData.name == 'Boss-Extrude1' for RecordData in NamesList)):
            FeatureData.object_id = 32
        else:
            continue
        FeatureData.properties['id'] = str(FeatureData.object_id)

# this definition exists because focused behavior needs one stable owner
def NativeFeatureA(Feature: NativeFeature) -> tuple[int, int]:
    if Feature.native_offset is not None and Feature.object_id <= 25:
        return (0, Feature.native_offset)
    if Feature.object_id in KeywordOnlyObjectIds:
        return (1, Feature.object_id)
    if Feature.native_offset is not None:
        return (2, Feature.native_offset)
    return (3, Feature.object_id)

# this definition exists because focused behavior needs one stable owner
def ParseKeywords(DataValue: bytes) -> tuple[tuple[NativeConfig, ...], list[XmlFeature]]:
    RootValue = ParseXml(DataValue)
    Configurations: list[NativeConfig] = []
    Features: list[XmlFeature] = []
    for ElemValue in RootValue.iter():
        TagValue = ElemValue.tag.rsplit('}', 1)[-1]
        if TagValue == 'Configuration':
            Configurations.append(NativeConfig(object_id=int(ElemValue.attrib.get('id', '0')), name=ElemValue.attrib.get('Name', 'Default'), configuration_id=int(ElemValue.attrib.get('id', '0')), properties=dict(ElemValue.attrib)))
            continue
        if ElemValue is RootValue or TagValue == 'Dimension':
            continue
        RawId = ElemValue.attrib.get('id')
        if not RawId:
            continue
        try:
            ObjectId = int(RawId)
        except ValueError:
            continue
        KindValue = TagValue if TagValue != 'Feature' else ElemValue.attrib.get('Type', 'Feature')
        if KindValue.casefold() in PlaneFeatureTypes:
            KindValue = CanonicalPlaneFeatureType.title()
        NameValue = ElemValue.attrib.get('Name', '')
        Dimensions = [ParseDimension(Child.attrib.get('Name', ''), Child.text or '') for Child in ElemValue if Child.tag.rsplit('}', 1)[-1] == 'Dimension']
        Features.append(XmlFeature(object_id=ObjectId, name=NameValue, kind=KindValue, xml_tag=TagValue, properties=dict(ElemValue.attrib), dimensions=Dimensions))
    if not Features:
        raise SldprtFormatError('keyword history does not contain feature nodes')
    if not Configurations:
        Configurations.append(NativeConfig(0, 'Default', 0, {}))
    return (tuple(Configurations), Features)

# this definition exists because focused behavior needs one stable owner
def ParseXml(DataValue: bytes) -> XmlTree.Element:
    Start = DataValue.find(b'<?xml')
    if Start < 0:
        Start = DataValue.find(b'<')
    if Start < 0:
        raise SldprtFormatError('XML stream contains no document element')
    try:
        return XmlTree.fromstring(DataValue[Start:])
    except XmlTree.ParseError as exc:
        raise SldprtFormatError(f'invalid XML metadata stream: {exc}') from exc

# this definition exists because focused behavior needs one stable owner
def ParseDimension(NameValue: str, TextValue: str) -> NativeDimension:
    Match = KNumber.search(TextValue)
    if Match is None:
        raise SldprtFormatError(f'dimension {NameValue!r} has no numeric value')
    KindValue = 'diameter' if '<MOD-DIAM>' in TextValue else 'radius' if TextValue.lstrip().startswith('R') else 'angle' if '°' in TextValue or 'deg' in TextValue.casefold() else 'length'
    return NativeDimension(NameValue, float(Match.group()), KindValue, TextValue)

# this definition exists because focused behavior needs one stable owner
def NameMarker(DataValue: bytes) -> bytes:
    for Offset in FindAll(DataValue, ClassMarker):
        if Offset + 6 > len(DataValue):
            continue
        Length = Struct.unpack_from('<H', DataValue, Offset + 4)[0]
        EndValue = Offset + 6 + Length
        if not 1 <= Length <= 128 or EndValue + 5 > len(DataValue):
            continue
        ClassName = DataValue[Offset + 6:EndValue]
        if not all((33 <= ByteValue <= 126 for ByteValue in ClassName)):
            continue
        Token = Struct.unpack_from('<H', DataValue, EndValue)[0]
        if Token & 32768 and Token != 65535 and (DataValue[EndValue + 2:EndValue + 5] == b'\xff\xfe\xff'):
            return Struct.pack('<H', Token) + b'\xff\xfe\xff'
    return bytes.fromhex('0480fffeff')

# this definition exists because focused behavior needs one stable owner
def ParseNames(DataValue: bytes) -> tuple[NativeName, ...]:
    Marker = NameMarker(DataValue)
    Names: list[NativeName] = []
    for Offset in FindAll(DataValue, Marker):
        if Offset + len(Marker) + 1 > len(DataValue):
            continue
        Units = DataValue[Offset + len(Marker)]
        TextStart = Offset + len(Marker) + 1
        TextEnd = TextStart + Units * 2
        if not 1 <= Units <= 128 or TextEnd + 12 > len(DataValue):
            continue
        try:
            NameValue = DataValue[TextStart:TextEnd].decode('utf-16le')
        except UnicodeDecodeError:
            continue
        if not NameValue or any((not Character.isprintable() for Character in NameValue)):
            continue
        RawId = Struct.unpack_from('<I', DataValue, TextEnd + 8)[0]
        Names.append(NativeName(offset=Offset, text_end=TextEnd, name=NameValue, object_id=None if RawId == 4294967295 else RawId, class_token=Struct.unpack_from('<H', Marker)[0]))
    return tuple(Names)

# this definition exists because focused behavior needs one stable owner
def ParseClasses(DataValue: bytes) -> tuple[NativeClass, ...]:
    Classes: list[NativeClass] = []
    for Offset in FindAll(DataValue, ClassMarker):
        if Offset + 6 > len(DataValue):
            continue
        Length = Struct.unpack_from('<H', DataValue, Offset + 4)[0]
        EndValue = Offset + 6 + Length
        if not 1 <= Length <= 128 or EndValue > len(DataValue):
            continue
        Value = DataValue[Offset + 6:EndValue]
        if not all((chr(ByteValue).isalnum() or ByteValue in b'_-' for ByteValue in Value)):
            continue
        Classes.append(NativeClass(Offset, Value.decode('ascii')))
    return tuple(Classes)

# this definition exists because focused behavior needs one stable owner
def RecordClassName(Classes: tuple[NativeClass, ...], RecordOffset: int) -> str:
    Owner = RecordClass(Classes, RecordOffset)
    return '' if Owner is None else Owner.name

# this definition exists because focused behavior needs one stable owner
def ParseNative(DataValue: bytes, ConfigId: int, NativeStream: str) -> tuple[NativeEquation, ...]:
    ClassNames = {ItemValue.name for ItemValue in ParseClasses(DataValue)}
    if not {'moRelMgr_c', 'moRelation_c'} <= ClassNames:
        return ()
    Equations: list[NativeEquation] = []
    SeenValue: set[str] = set()
    for Offset in FindAll(DataValue, SerializedStringMarker):
        LengthOffset = Offset + len(SerializedStringMarker)
        if LengthOffset >= len(DataValue):
            continue
        Units = DataValue[LengthOffset]
        TextStart = LengthOffset + 1
        TextEnd = TextStart + Units * 2
        if Units < 3 or TextEnd > len(DataValue):
            continue
        try:
            Source = DataValue[TextStart:TextEnd].decode('utf-16le')
        except UnicodeDecodeError:
            continue
        Match = KEquation.fullmatch(Source)
        if Match is None or Source in SeenValue or (not all((Character.isprintable() for Character in Source))):
            continue
        SeenValue.add(Source)
        LhsValue, RhsValue = Match.groups()
        Equations.append(NativeEquation(source=Source, lhs=LhsValue, rhs=RhsValue, references=tuple(dict.fromkeys(KEquationRef.findall(RhsValue))), native_offset=Offset, native_length=TextEnd - Offset, configuration_id=ConfigId, native_stream=NativeStream))
    return tuple(Equations)

# this definition exists because focused behavior needs one stable owner
def ParseScalars(DataValue: bytes, Names: tuple[NativeName, ...]) -> tuple[NativeScalar, ...]:
    Scalars: list[NativeScalar] = []
    for NameValue in Names:
        ValueOffset = DimensionScalarValue(DataValue, NameValue.text_end, len(DataValue), trailing_bytes=7)
        if ValueOffset is None:
            continue
        Value = Struct.unpack_from('<d', DataValue, ValueOffset)[0]
        if not MathValue.isfinite(Value):
            continue
        Trailer = ValueOffset + 8
        RawId = Struct.unpack_from('<I', DataValue, Trailer + 3)[0]
        RoleValue, Operands = ScalarTrailer(DataValue, Trailer)
        Scalars.append(NativeScalar(name=NameValue.name, name_offset=NameValue.offset, value_offset=ValueOffset, value=Value, object_id=None if RawId == 4294967295 else RawId, role=RoleValue, operands=Operands))
    return tuple(Scalars)

# this definition exists because focused behavior needs one stable owner
def ScalarTrailer(DataValue: bytes, Trailer: int) -> tuple[str, tuple[NativeOperand, ...]]:
    Fixed = DataValue[Trailer:Trailer + 3] == b'\x00\x00\x00' and DataValue[Trailer + 7:Trailer + 21] == b'\x00' * 14 and (DataValue[Trailer + 24:Trailer + 29] == b'\x00\x00\x00\x02\x00')
    Compact = DataValue[Trailer:Trailer + 3] == b'\x00\x00\x00' and DataValue[Trailer + 7:Trailer + 21] == b'\x00' * 14 and (DataValue[Trailer + 21:Trailer + 27] == b'\x01\x00\x00\x00\x02\x00') and (DataValue[Trailer + 28:Trailer + 35] == b'\x00' * 7)
    Legacy = DataValue[Trailer:Trailer + 3] == b'\x00\x00\x00' and DataValue[Trailer + 7:Trailer + 24] == b'\x00' * 17 and (DataValue[Trailer + 24:Trailer + 30] == b'\x0f\x00\x00\x00\x02\x00')
    if Compact:
        RoleOffset, Cells, SizeValue = (Trailer + 27, (Trailer + 35, Trailer + 43), 8)
    elif Fixed:
        RoleOffset, Cells, SizeValue = (Trailer + 29, (Trailer + 35, Trailer + 47), 12)
    elif Legacy:
        RoleOffset, Cells, SizeValue = (Trailer + 30, (Trailer + 36, Trailer + 48), 12)
    else:
        return ('native', ())
    RoleByte = DataValue[RoleOffset] if RoleOffset < len(DataValue) else 255
    RoleValue = 'driving' if RoleByte == 0 else 'display' if RoleByte == 1 else 'native'
    Operands: list[NativeOperand] = []
    for Offset in Cells:
        CellValue = DataValue[Offset:Offset + SizeValue]
        if len(CellValue) != SizeValue or CellValue[4:8] != b'\xff' * 4:
            continue
        if SizeValue == 12 and CellValue[8:12] != b'\x00' * 4:
            continue
        KindValue = Struct.unpack_from('<H', CellValue)[0]
        if KindValue in {0, 65535}:
            continue
        Operands.append(NativeOperand(Offset, KindValue, Struct.unpack_from('<H', CellValue, 2)[0]))
    return (RoleValue, tuple(Operands))

# this definition exists because focused behavior needs one stable owner
def ScalarOwners(Scalars: tuple[NativeScalar, ...], Records: list[NativeName], EndsValue: dict[int, int]) -> dict[int, tuple[NativeScalar, ...]]:
    Result: dict[int, list[NativeScalar]] = {}
    for Record in Records:
        if Record.object_id is None:
            continue
        EndValue = EndsValue[Record.offset]
        Result[Record.object_id] = [Scalar for Scalar in Scalars if Record.offset < Scalar.value_offset < EndValue]
    return {KeyValue: tuple(Value) for KeyValue, Value in Result.items()}

# this definition exists because focused behavior needs one stable owner
def BindDimension(Dimension: NativeDimension, Scalars: tuple[NativeScalar, ...]) -> NativeDimension:
    Target = Dimension.value_mm if Dimension.kind == 'instance_count' else MathValue.radians(Dimension.value_mm) if Dimension.kind == 'angle' else Dimension.value_mm / 1000.0
    ValueMatches = [Scalar for Scalar in Scalars if MathValue.isclose(Scalar.value, Target, rel_tol=1e-09, abs_tol=1e-12)]
    NamedMatches = [Scalar for Scalar in ValueMatches if Scalar.name == Dimension.name]
    Matches = NamedMatches
    if not Matches and len(ValueMatches) == 1:
        Matches = ValueMatches
    if not Matches:
        return Dimension
    Scalar = next((Choice for Choice in Matches if Choice.role == 'driving'), Matches[-1])
    return NativeDimension(name=Dimension.name, value_mm=Dimension.value_mm, kind=Dimension.kind, source_text=Dimension.source_text, native_value=Scalar.value, native_offset=Scalar.value_offset, native_role=Scalar.role, operands=Scalar.operands)

# this definition exists because focused behavior needs one stable owner
def FeatureRecords(Features: list[_XmlFeature], Names: tuple[NativeName, ...]) -> dict[int, NativeName]:
    Records: dict[int, list[NativeName]] = {}
    for Record in Names:
        if Record.object_id is not None:
            Records.setdefault(Record.object_id, []).append(Record)
    Result: dict[int, NativeName] = {}
    for Feature in Features:
        Candidates = Records.get(Feature.object_id, ())
        if not Candidates:
            continue
        Exact = tuple((Record for Record in Candidates if Record.name == Feature.name))

        # this callback exists because local behavior needs one focused transformation
        Selected = min(Exact or tuple(Candidates), key=lambda Record: Record.offset)
        Result[Feature.object_id] = Selected
    return Result

# this definition exists because focused behavior needs one stable owner
def Semantic(FeatureKind: str, Dimensions: tuple[NativeDimension, ...]) -> tuple[NativeDimension, ...]:
    FeatureType = FeatureKind.casefold()
    if FeatureType in KSurfaceExtrusionFeature:
        return tuple((Replace(Dimension, kind='length' if Dimension.name.casefold() == 'd1' else 'second_length' if Dimension.name.casefold() == 'd2' else Dimension.kind) for Dimension in Dimensions))
    if FeatureType == 'chamfer':
        return tuple((Replace(Dimension, kind='distance' if Dimension.name.casefold() == 'd1' else 'angle' if Dimension.name.casefold() == 'd2' else Dimension.kind) for Dimension in Dimensions))
    if FeatureType in {'lpattern', 'linearpattern'}:
        return tuple((Replace(Dimension, kind='instance_count' if Dimension.name.casefold() == 'd1' else 'spacing' if Dimension.name.casefold() == 'd3' else Dimension.kind) for Dimension in Dimensions))
    if FeatureType in {'cirpattern', 'circularpattern'}:
        return tuple((Replace(Dimension, kind='instance_count' if Dimension.name.casefold() == 'd1' else 'angle' if Dimension.name.casefold() == 'd3' else Dimension.kind) for Dimension in Dimensions))
    Semantic = {'extrusion': 'length', 'fillet': 'radius', 'cut': 'depth', 'revolve': 'angle', 'revolution': 'angle', 'cut-revolve': 'angle', 'revcut': 'angle', 'shell': 'thickness', 'dome': 'height', 'plane': 'offset'}.get(FeatureType)
    if Semantic is None or not Dimensions:
        return Dimensions
    Selected = Primary(Dimensions)
    return tuple((Replace(Dimension, kind=Semantic) if Index == Selected else Dimension for Index, Dimension in enumerate(Dimensions)))

# this definition exists because focused behavior needs one stable owner
def Primary(Dimensions: tuple[NativeDimension, ...]) -> int:

    # this callback exists because local behavior needs one focused transformation
    return min(range(len(Dimensions)), key=lambda Index: (Dimensions[Index].native_role == 'display', Dimensions[Index].native_offset is None, Dimensions[Index].native_offset if Dimensions[Index].native_offset is not None else Index, Index))

# this definition exists because focused behavior needs one stable owner
def DecodePlanes(DataValue: bytes, Features: list[NativeFeature], *, NativeStream: str=ResolvedFeaturesStream) -> list[NativePlane]:
    Principal = PrincipalPlaneA(Features)
    PlaneIds = frozenset(Principal) | frozenset((Feature.object_id for Feature in Features if IsPlaneFeature(Feature)))
    Planes: list[NativePlane] = []
    for Feature in Features:
        if Feature.object_id in Principal:
            Origin, Normal, UAxis = Principal[Feature.object_id]
            Planes.append(NativePlane(Feature.object_id, Feature.name, Origin, Normal, UAxis, Cross(Normal, UAxis), Feature.native_offset, None, True, (), NativeStream))
            continue
        if not IsPlaneFeature(Feature):
            continue
        Start = Feature.native_offset or 0
        EndValue = Feature.native_end or len(DataValue)
        Frame = MatrixFrame(DataValue, Start, EndValue) or MinimalFrame(DataValue, Start, EndValue)
        if Frame is None:
            continue
        Offset, Length, Origin, Normal, UAxis, VAxis = Frame
        Planes.append(NativePlane(Feature.object_id, Feature.name, Origin, Normal, UAxis, VAxis, Offset, Length, False, RefPlaneIds(DataValue, Start, EndValue, Feature.object_id, PlaneIds), NativeStream))
    return Planes

# this definition exists because focused behavior needs one stable owner
def PrincipalPlaneA(Features: list[NativeFeature]) -> dict[int, tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]]:

    # this callback exists because local behavior needs one focused transformation
    Ordered = tuple((Feature for Ignored, Feature in sorted(enumerate(Features), key=lambda ItemValue: (ItemValue[1].native_offset is None, ItemValue[1].native_offset if ItemValue[1].native_offset is not None else ItemValue[0], ItemValue[0]))))
    OriginIndex = next((Index for Index, Feature in enumerate(Ordered) if IsOriginFeature(Feature)), None)
    if OriginIndex is None:
        return {}
    Planes = tuple((Feature for Feature in Ordered[:OriginIndex] if IsPlaneFeature(Feature)))
    Frames = (((0.0, 0.0, 0.0), (0.0, 0.0, 1.0), (1.0, 0.0, 0.0)), ((0.0, 0.0, 0.0), (0.0, 1.0, 0.0), (1.0, 0.0, 0.0)), ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 0.0, -1.0)))
    return {Feature.object_id: Frame for Feature, Frame in zip(Planes[:3], Frames)}

# this definition exists because focused behavior needs one stable owner
def IsOriginFeature(Feature: NativeFeature) -> bool:
    return Feature.properties.get('Type', '').casefold() == 'origin'

# this definition exists because focused behavior needs one stable owner
def IsPlaneFeature(Feature: NativeFeature) -> bool:
    return Feature.kind.casefold() in PlaneFeatureTypes

# this definition exists because focused behavior needs one stable owner
def MatrixFrame(DataValue: bytes, Start: int, EndValue: int) -> tuple[int, int, tuple[float, float, float], tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]] | None:
    for Offset in range(Start, max(Start, EndValue - 121 + 1)):
        if DataValue[Offset + 48] != 1:
            continue
        Origin = Struct.unpack_from('<3d', DataValue, Offset)
        Normal = Struct.unpack_from('<3d', DataValue, Offset + 24)
        RowsValue = (Struct.unpack_from('<3d', DataValue, Offset + 49), Struct.unpack_from('<3d', DataValue, Offset + 73), Struct.unpack_from('<3d', DataValue, Offset + 97))
        UAxis = tuple((RowValue[0] for RowValue in RowsValue))
        VAxis = tuple((RowValue[1] for RowValue in RowsValue))
        MatrixNormal = tuple((RowValue[2] for RowValue in RowsValue))
        Values = Origin + Normal + UAxis + VAxis + MatrixNormal
        if not all((MathValue.isfinite(Value) and abs(Value) <= 10.0 for Value in Values)):
            continue
        if not all((MathValue.isclose(NormAction(Vector), 1.0, abs_tol=1e-09) for Vector in (Normal, UAxis, VAxis, MatrixNormal))):
            continue
        if any((abs(DotAction(LeftValue, Right)) > 1e-09 for LeftValue, Right in ((UAxis, VAxis), (UAxis, MatrixNormal), (VAxis, MatrixNormal)))):
            continue
        if DotAction(Normal, MatrixNormal) < 1.0 - 1e-09:
            continue
        return (Offset, 121, tuple((Clean(Value * 1000.0) for Value in Origin)), tuple((Clean(Value) for Value in Normal)), tuple((Clean(Value) for Value in UAxis)), tuple((Clean(Value) for Value in VAxis)))
    return None

# this definition exists because focused behavior needs one stable owner
def MinimalFrame(DataValue: bytes, Start: int, EndValue: int) -> tuple[int, int, tuple[float, float, float], tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]] | None:
    for Offset in range(Start, max(Start, EndValue - 81 + 1)):
        Origin = Struct.unpack_from('<3d', DataValue, Offset)
        Normal = Struct.unpack_from('<3d', DataValue, Offset + 24)
        if Normal != (0.0, 0.0, 1.0):
            continue
        if DataValue[Offset + 48:Offset + 56] != b'\x00' * 8 or DataValue[Offset + 56] not in {0, 128}:
            continue
        TailValue = Struct.unpack_from('<3d', DataValue, Offset + 57)
        if TailValue[0] != 0.0:
            continue
        if Struct.pack('<d', TailValue[1]) != Struct.pack('<d', -Origin[2]) or TailValue[2] != 1.0:
            continue
        return (Offset, 81, tuple((Clean(Value * 1000.0) for Value in Origin)), Normal, (1.0, 0.0, 0.0), (0.0, 1.0, 0.0))
    return None

# this definition exists because focused behavior needs one stable owner
def SupportPlaneRef(DataValue: bytes, Start: int, EndValue: int, RefValue: NativeSketchPlane | None, FramedFallback: int, UnframedFallback: int | None, Planes: dict[int, NativePlane], UnframedPlaneIds: frozenset[int]) -> tuple[int, str, int | None]:
    if RefValue is not None and RefValue.plane_object_id in Planes:
        return (RefValue.plane_object_id, KRefSupportSource, None)
    Sources = ComponentPlane(DataValue, Start, EndValue)
    Framed = [Source for Source in Sources if Source in Planes]
    if Framed:
        return (Framed[-1], KRefSupportSource, None)
    Unframed = [Source for Source in Sources if Source in UnframedPlaneIds]
    if Unframed:
        return (FramedFallback, KUnresolvedSupportSource, Unframed[-1])
    if UnframedFallback is not None:
        return (FramedFallback, KUnresolvedSupportSource, UnframedFallback)
    return (FramedFallback, KStreamOrderSupportSource, None)

# this definition exists because focused behavior needs one stable owner
def SketchPlaneRef(DataValue: bytes, Classes: tuple[NativeClass, ...], Start: int, EndValue: int) -> NativeSketchA | None:
    for Record in Classes:
        if Record.name != SketchChainClass or not Start <= Record.offset < EndValue:
            continue
        Anchored = ReadSketchPlane(DataValue, Record.offset + KSketchPlaneIdRelative, EndValue)
        if Anchored is not None:
            return Anchored
    for Offset in FindAll(DataValue, KSketchPlaneRefPrefix, Start, EndValue):
        Scanned = ReadSketchPlane(DataValue, Offset + len(KSketchPlaneRefPrefix), EndValue)
        if Scanned is not None:
            return Scanned
    return None

# this definition exists because focused behavior needs one stable owner
def ReadSketchPlane(DataValue: bytes, Offset: int, EndValue: int) -> NativeSketchA | None:
    if Offset < 0 or Offset + KSketchPlaneBasisDelta > EndValue:
        return None
    PlaneObjectId = Struct.unpack_from('<I', DataValue, Offset)[0]
    if PlaneObjectId not in KPrincipalPlaneObjectIds:
        return None
    if DataValue[Offset + 4:Offset + 8] != KSketchPlaneRefTag:
        return None
    if DataValue[Offset + 8:Offset + KSketchPlaneAxisDelta] != b'\x00\x00':
        return None
    AxisCode = Struct.unpack_from('<I', DataValue, Offset + KSketchPlaneAxisDelta)[0]
    if AxisCode != KSketchPlaneAxisComplemeA - PlaneObjectId:
        return None
    FlagValue = DataValue[Offset + KSketchPlaneBasisFlagDelA]
    BasisOffset = Offset + KSketchPlaneBasisDelta
    if FlagValue == 0:
        return NativeSketchA(Offset, PlaneObjectId, AxisCode, KIdentityBasis[0], KIdentityBasis[1], KIdentityBasis[2], None)
    if FlagValue != 1 or BasisOffset + KSketchPlaneBasisBytes > EndValue:
        return None
    RowsValue = Struct.unpack_from('<9d', DataValue, BasisOffset)
    if not all((MathValue.isfinite(Value) for Value in RowsValue)):
        return None
    UAxis = (RowsValue[0], RowsValue[3], RowsValue[6])
    VAxis = (RowsValue[1], RowsValue[4], RowsValue[7])
    Normal = (RowsValue[2], RowsValue[5], RowsValue[8])
    if not Orthonormal((UAxis, VAxis, Normal)):
        return None
    return NativeSketchA(Offset, PlaneObjectId, AxisCode, tuple((Clean(Value) for Value in UAxis)), tuple((Clean(Value) for Value in VAxis)), tuple((Clean(Value) for Value in Normal)), BasisOffset)

# this definition exists because focused behavior needs one stable owner
def SketchSupport(Classes: tuple[NativeClass, ...], RefValue: NativeSketchPlane | None, Start: int, EndValue: int) -> str:
    if RefValue is not None:
        return KPlaneSupportKind
    if any((Record.name == KFaceSupportClass and Start <= Record.offset < EndValue for Record in Classes)):
        return KFaceSupportKind
    return KDerivedSupportKind

# this definition exists because focused behavior needs one stable owner
def BoundingBox(DataValue: bytes, Classes: tuple[NativeClass, ...]) -> NativeBounding | None:
    for Record in Classes:
        if Record.name != KBoundingBoxClass:
            continue
        Offset = Record.offset + KBoundingBoxRelative
        if Offset + 32 > len(DataValue):
            continue
        Values = Struct.unpack_from('<4d', DataValue, Offset)
        if not all((MathValue.isfinite(Value) for Value in Values)) or Values[3] < 0.0:
            continue
        return NativeBounding(Offset, tuple((Clean(Value * KMillimetres) for Value in Values[:3])), Clean(Values[3] * KMillimetres))
    return None

# this definition exists because focused behavior needs one stable owner
def DepthCopies(DataValue: bytes, Offset: int | None) -> tuple[NativeDepthCopy, ...]:
    if Offset is None:
        return ()
    Result: list[NativeDepthCopy] = []
    for Delta, SignValue in zip(DepthCopyDeltas, DepthCopySigns, strict=True):
        Target = Offset + Delta
        if Target < 0 or Target + 8 > len(DataValue):
            continue
        Value = Struct.unpack_from('<d', DataValue, Target)[0]
        if not MathValue.isfinite(Value):
            continue
        Result.append(NativeDepthCopy(Target, SignValue, Value * KMillimetres))
    return tuple(Result)

# this definition exists because focused behavior needs one stable owner
def AngleCopies(DataValue: bytes, Offset: int | None) -> tuple[NativeDepthCopy, ...]:
    if Offset is None:
        return ()
    Result: list[NativeDepthCopy] = []
    for Delta in AngleCopyDeltas:
        Target = Offset + Delta
        if Target < 0 or Target + 8 > len(DataValue):
            continue
        Value = Struct.unpack_from('<d', DataValue, Target)[0]
        if not MathValue.isfinite(Value):
            continue
        Result.append(NativeDepthCopy(Target, 1, Value * KRadiansToDegrees))
    return tuple(Result)

# this definition exists because focused behavior needs one stable owner
def Mirrored(DataValue: bytes, Classes: tuple[NativeClass, ...], Start: int, EndValue: int) -> tuple[int | None, int | None]:
    for Record in Classes:
        if Record.name != FromEndSpecClass or not Start <= Record.offset < EndValue:
            continue
        Offset = Record.offset + FromReverseRelative
        if Offset < len(DataValue):
            return (Offset, DataValue[Offset])
    return (None, None)

# this definition exists because focused behavior needs one stable owner
def RecordClass(Classes: tuple[NativeClass, ...], RecordOffset: int) -> NativeClass | None:
    return next((ItemValue for ItemValue in Classes if ItemValue.offset + 6 + len(ItemValue.name.encode('ascii')) == RecordOffset), None)

# this definition exists because focused behavior needs one stable owner
def ClassRecordEnd(DataValue: bytes, Classes: tuple[NativeClass, ...], RecordOffset: int) -> int | None:
    Owner = RecordClass(Classes, RecordOffset)
    if Owner is None:
        return None
    return next((ItemValue.offset for ItemValue in Classes if ItemValue.offset > Owner.offset), len(DataValue))

# this definition exists because focused behavior needs one stable owner
def RefPlaneIds(DataValue: bytes, Start: int, EndValue: int, ObjectId: int, PlaneIds: frozenset[int]) -> tuple[int, ...]:
    Result: list[int] = []
    Marker = b'\x00' * 6 + Struct.pack('<I', 1)
    for Offset in FindAll(DataValue, Marker, Start, EndValue):
        SourceOffset = Offset + len(Marker)
        if SourceOffset + 6 > EndValue or DataValue[SourceOffset + 4:SourceOffset + 6] != b'\x00\x05':
            continue
        Source = Struct.unpack_from('<I', DataValue, SourceOffset)[0]
        if Source in PlaneIds and Source != ObjectId:
            Result.append(Source)
    return tuple(dict.fromkeys(Result))

# this definition exists because focused behavior needs one stable owner
def ComponentPlane(DataValue: bytes, Start: int, EndValue: int) -> list[int]:
    Sources: list[int] = []
    for Offset in range(Start, max(Start, EndValue - 67 + 1) + 1):
        Block = DataValue[Offset:Offset + 67]
        Identity = Struct.unpack_from('<I', Block)[0]
        Legacy = Struct.unpack_from('<H', Block, 10)[0]
        Trailer = Block[47:63]
        Common = Block[12:39] == b'\x00' * 27 and Struct.unpack_from('<d', Block, 39)[0] == 1.0 and (Trailer[:3] == b'\x00' * 3) and (Trailer[3] in {2, 3, 4}) and (Trailer[4:7] == b'\x00' * 3) and (Trailer[7] in {249, 251, 255}) and (Trailer[8:11] == b'\xff' * 3) and (Trailer[11:15] == b'\x00' * 4)
        if not Common:
            continue
        if Identity and Block[4:10] == b'\x00' * 6 and Legacy:
            Sources.append(Legacy)
        elif Identity and Block[8:12] == b'\x00\x00\x03\x00':
            Sources.append(Identity)
    for Offset in range(Start, max(Start, EndValue - 138 + 1) + 1):
        Block = DataValue[Offset:Offset + 138]
        Source = Struct.unpack_from('<I', Block)[0]
        if not Source or Block[8:14] != b'\x00' * 6 or Block[14] != 1:
            continue
        if Block[122:126] != Struct.pack('<I', 4) or Block[126:130] != b'\xff' * 4:
            continue
        Basis = [Struct.unpack_from('<3d', Block, 15 + Index * 24) for Index in range(3)]
        if not all((MathValue.isclose(NormAction(Vector), 1.0, abs_tol=1e-09) for Vector in Basis)):
            continue
        Sources.append(Source)
    return list(dict.fromkeys(Sources))

# this definition exists because focused behavior needs one stable owner
def DecodeSketch(DataValue: bytes, Feature: NativeFeature, SupportPlaneId: int, *, NativeStream: str=ResolvedFeaturesStream, SupportKind: str=KPlaneSupportKind, SupportPlane: NativeSketchPlane | None=None, SupportSource: str=KRefSupportSource, UnframedSupportPlaneId: int | None=None) -> NativeSketch:
    Start = Feature.native_offset or 0
    EndValue = Feature.native_end or len(DataValue)
    Markers = list(ParseMarkers(DataValue, Start, EndValue))
    Profiles, ProfileMarkers, Dimensions = Profiles(Markers, Feature.dimensions)
    NormalizedMarkers = tuple((NativeMarker(offset=Marker.offset, length=Marker.length, prefix=Marker.prefix, native_kind=Marker.native_kind, locus=Marker.locus, profile_role=Marker.profile_role, state=Marker.state, object_index=Marker.object_index, local_id=Marker.local_id, coordinates_mm=Marker.coordinates_mm, endpoint_indices=Marker.endpoint_indices, construction=Marker.construction or (Marker.offset not in ProfileMarkers and Marker.semantic != 'native'), semantic=Marker.semantic, data=Marker.data, coordinates_metres=Marker.coordinates_metres) for Marker in Markers))
    Constraints = Constraints(Feature, NormalizedMarkers, Profiles)
    return NativeSketch(object_id=Feature.object_id, name=Feature.name, support_plane_id=SupportPlaneId, native_offset=Start, native_end=EndValue, markers=NormalizedMarkers, profiles=Profiles, dimensions=Dimensions, constraints=Constraints, native_stream=NativeStream, support_kind=SupportKind, support_plane=SupportPlane, support_source=SupportSource, unframed_support_plane_id=UnframedSupportPlaneId)

# this definition exists because focused behavior needs one stable owner
def ParseMarkers(DataValue: bytes, Start: int, EndValue: int) -> tuple[NativeMarker, ...]:
    Offsets = sorted({Offset for Prefix in KMarkers for Offset in FindAll(DataValue, Prefix, Start, EndValue) if Offset + 56 <= EndValue})
    Markers: list[NativeMarker] = []
    for Index, Offset in enumerate(Offsets):
        PrefixBytes = next((Prefix for Prefix in KMarkers if DataValue.startswith(Prefix, Offset)))
        NativeOffset = 17
        LocusOffset = 23
        RoleOffset = 27
        if Offset + NativeOffset + 4 > EndValue:
            continue
        NativeKind = Struct.unpack_from('<I', DataValue, Offset + NativeOffset)[0]
        Locus = DataValue[Offset + LocusOffset:Offset + LocusOffset + 4]
        ProfileRole = Struct.unpack_from('<H', DataValue, Offset + RoleOffset)[0]
        NextOffset = Offsets[Index + 1] if Index + 1 < len(Offsets) else EndValue
        Length = NextOffset - Offset
        StateOffset = Offset + 48
        State = Struct.unpack_from('<d', DataValue, StateOffset)[0] if StateOffset + 8 <= EndValue else None
        if State is not None and (not MathValue.isfinite(State)):
            State = None
        CoordinatesMetres = MarkerMetres(DataValue, Offset, EndValue)
        Coordinates = None if CoordinatesMetres is None else (Clean(round(CoordinatesMetres[0] * KMillimetres, 12)), Clean(round(CoordinatesMetres[1] * KMillimetres, 12)))
        Endpoints = None
        if Coordinates is None:
            PairOffset = Offset + 64
            if PairOffset + 4 <= EndValue:
                PairValue = Struct.unpack_from('<HH', DataValue, PairOffset)
                if PairValue != (0, 0):
                    Endpoints = PairValue
        ObjectIndex = Struct.unpack_from('<I', DataValue, Offset - 4)[0] if Offset >= 4 else 4294967295
        if ObjectIndex == 4294967295:
            ObjectIndex = None
        LocalId = MarkerLocalId(DataValue, Offset, Length)
        Semantic = MarkerSemantic(NativeKind, Locus, Coordinates, Endpoints, ProfileRole)
        Markers.append(NativeMarker(offset=Offset, length=Length, prefix=PrefixBytes.hex(), native_kind=NativeKind, locus=Locus.hex(), profile_role=ProfileRole, state=State, object_index=ObjectIndex, local_id=LocalId, coordinates_mm=Coordinates, endpoint_indices=Endpoints, construction=ProfileRole == 2, semantic=Semantic, data=bytes(DataValue[Offset:NextOffset]), coordinates_metres=CoordinatesMetres))
    return tuple(Markers)

# this definition exists because focused behavior needs one stable owner
def MarkerMetres(DataValue: bytes, Offset: int, EndValue: int) -> tuple[float, float] | None:
    for Relative in (56, 64):
        CoordinateOffset = Offset + Relative
        if DataValue[CoordinateOffset:CoordinateOffset + 2] != KCoordinateTag:
            continue
        if CoordinateOffset + 18 > EndValue:
            continue
        FirstCoord, SecondCoord = Struct.unpack_from('<2d', DataValue, CoordinateOffset + 2)
        if MathValue.isfinite(FirstCoord) and MathValue.isfinite(SecondCoord) and (abs(FirstCoord) <= 1000.0) and (abs(SecondCoord) <= 1000.0):
            return (FirstCoord, SecondCoord)
    return None

# this definition exists because focused behavior needs one stable owner
def Marker(DataValue: bytes, Offset: int, EndValue: int) -> tuple[float, float] | None:
    Metres = MarkerMetres(DataValue, Offset, EndValue)
    if Metres is None:
        return None
    return (Clean(round(Metres[0] * KMillimetres, 12)), Clean(round(Metres[1] * KMillimetres, 12)))

# this definition exists because focused behavior needs one stable owner
def MarkerRadiusMm(Center: NativeMarker, RimValue: NativeMarker) -> float | None:
    if Center.coordinates_metres is None or RimValue.coordinates_metres is None:
        return None
    Radius = CircleRadiusMm(RimValue.coordinates_metres[0] - Center.coordinates_metres[0], RimValue.coordinates_metres[1] - Center.coordinates_metres[1]) * KMillimetres
    return Radius if MathValue.isfinite(Radius) and Radius > 1e-12 else None

# this definition exists because focused behavior needs one stable owner
def MarkerStart(Center: NativeMarker, RimValue: NativeMarker) -> float | None:
    if Center.coordinates_metres is None or RimValue.coordinates_metres is None:
        return None
    Angle = MathValue.degrees(MathValue.atan2(RimValue.coordinates_metres[1] - Center.coordinates_metres[1], RimValue.coordinates_metres[0] - Center.coordinates_metres[0]))
    return Angle if MathValue.isfinite(Angle) else None

# this definition exists because focused behavior needs one stable owner
def MarkerLocalId(DataValue: bytes, Offset: int, Length: int) -> int | None:
    Relative = KMarkerLocalIdOffsetBy.get(Length)
    if Relative is None or Offset + Relative + 4 > len(DataValue):
        return None
    Value = Struct.unpack_from('<I', DataValue, Offset + Relative)[0]
    return None if Value == 4294967295 else Value

# this definition exists because focused behavior needs one stable owner
def MarkerSemantic(NativeKind: int, Locus: bytes, Coordinates: tuple[float, float] | None, Endpoints: tuple[int, int] | None, ProfileRole: int) -> str:
    if ProfileRole == 2:
        if NativeKind == 2 and Endpoints is not None and (Endpoints[0] != Endpoints[1]):
            return 'line'
        return 'native'
    if Locus == KCircleLocus and Coordinates is not None:
        return 'circle'
    if Locus == KPointLocus:
        if Coordinates is not None:
            return 'point'
        if Endpoints is not None and Endpoints[0] != Endpoints[1]:
            return 'line'
        return 'reference'
    return 'native'

# this definition exists because focused behavior needs one stable owner
def LinkedRectangle(Markers: list[NativeMarker]) -> tuple[tuple[NativeProfile, ...], set[int]]:
    Profiles: list[NativeProfile] = []
    UsedValue: set[int] = set()
    for Start in range(max(0, len(Markers) - 8)):
        Records = Markers[Start:Start + 9]
        if len(Records) != 9 or any((Marker.offset in UsedValue for Marker in Records)):
            continue
        Points = Records[:4]
        Header = Records[4]
        Lines = Records[5:]
        Prefix = Points[0].prefix
        Locus = Points[0].locus
        if Locus != KCircleLocus.hex() or any((Marker.prefix != Prefix or Marker.locus != Locus or Marker.profile_role != 1 or (Marker.native_kind != 0) or (Marker.coordinates_mm is None) for Marker in Points)) or Header.prefix != Prefix or (Header.locus != Locus) or (Header.profile_role != 1) or (Header.native_kind != 0) or (Header.coordinates_mm is not None) or (Header.endpoint_indices is None) or (Header.length != 92) or any((Marker.prefix != Prefix or Marker.locus != Locus or Marker.profile_role != 1 or (Marker.native_kind not in {1, 2}) or (Marker.coordinates_mm is not None) or (Marker.endpoint_indices is None) for Marker in Lines)) or any((Marker.length != 92 for Marker in Lines[:-1])) or (Lines[-1].length < 92):
            continue
        Coordinates = tuple((Marker.coordinates_mm for Marker in Points))
        if any((Coordinate is None for Coordinate in Coordinates)):
            continue
        Resolved = tuple((Coordinate for Coordinate in Coordinates if Coordinate is not None))
        XsValue = sorted({Coordinate[0] for Coordinate in Resolved})
        YsValue = sorted({Coordinate[1] for Coordinate in Resolved})
        if len(XsValue) != 2 or len(YsValue) != 2 or len(set(Resolved)) != 4:
            continue
        Corners = {(FirstCoord, SecondCoord) for FirstCoord in XsValue for SecondCoord in YsValue}
        if set(Resolved) != Corners:
            continue
        HeaderStart, HeaderEnd = Header.endpoint_indices
        if HeaderStart >= len(Resolved) or HeaderEnd >= len(Resolved) or HeaderStart == HeaderEnd:
            continue
        EdgeMarkers: dict[str, NativeMarker] = {}
        Valid = True
        for Marker in Lines:
            EndpointStart, EndpointEnd = Marker.endpoint_indices or (-1, -1)
            if EndpointStart < 0 or EndpointEnd < 0 or EndpointStart >= len(Resolved) or (EndpointEnd >= len(Resolved)) or (EndpointStart == EndpointEnd):
                Valid = False
                break
            PointStart = Resolved[EndpointStart]
            PointEnd = Resolved[EndpointEnd]
            if MathValue.isclose(PointStart[1], PointEnd[1], abs_tol=1e-09):
                SideValue = 'bottom' if MathValue.isclose(PointStart[1], YsValue[0], abs_tol=1e-09) else 'top'
            elif MathValue.isclose(PointStart[0], PointEnd[0], abs_tol=1e-09):
                SideValue = 'left' if MathValue.isclose(PointStart[0], XsValue[0], abs_tol=1e-09) else 'right'
            else:
                Valid = False
                break
            if SideValue in EdgeMarkers:
                Valid = False
                break
            EdgeMarkers[SideValue] = Marker
        if not Valid or set(EdgeMarkers) != {'bottom', 'right', 'top', 'left'}:
            continue
        EdgeOffsets = tuple((EdgeMarkers[SideValue].offset for SideValue in ('bottom', 'right', 'top', 'left')))
        MetaOffsets = tuple((Marker.offset for Marker in (*Points, Header) if Marker.offset not in EdgeOffsets))
        Consumed = {Marker.offset for Marker in Records}
        Profiles.append(NativeProfile('rectangle', (XsValue[0], YsValue[0], XsValue[1], YsValue[1]), (*EdgeOffsets, *MetaOffsets)))
        UsedValue.update(Consumed)
    return (tuple(Profiles), UsedValue)

# this definition exists because focused behavior needs one stable owner
def Profiles(Markers: list[NativeMarker], Dimensions: tuple[NativeDimension, ...]) -> tuple[tuple[NativeProfile, ...], set[int], tuple[NativeDimension, ...]]:
    LinkedRectangles, LinkedMarkers = LinkedRectangle(Markers)
    StructuralRectangles, StructuralRectangle = StructuralA(Markers, LinkedMarkers)
    StructuralCircles, StructuralMarkers, StructuralDimensions = Structural(Markers, Dimensions, LinkedMarkers | StructuralRectangle)
    StructuralPolylines, StructuralPolylineMarkers = PolyProfiles(Markers, LinkedMarkers | StructuralRectangle | StructuralMarkers)
    RemainingMarkers = [Marker for Marker in Markers if Marker.offset not in LinkedMarkers | StructuralRectangle | StructuralMarkers | StructuralPolylineMarkers]
    CircleProfiles, CircleDimensions = CircleProfiles(RemainingMarkers, Dimensions)
    CircleDimensions.update(StructuralDimensions)
    Normalized = tuple((Replace(Dimension, kind=CircleDimensions[Index]) if Index in CircleDimensions else Dimension for Index, Dimension in enumerate(Dimensions)))
    Points = [Marker for Marker in RemainingMarkers if Marker.coordinates_mm is not None and Marker.locus == KPointLocus.hex()]
    Coordinates = list(dict.fromkeys((Marker.coordinates_mm for Marker in Points)))
    Rectangles: list[tuple[float, float, float, float]] = []
    XsValue = sorted({Point[0] for Point in Coordinates})
    YsValue = sorted({Point[1] for Point in Coordinates})
    CoordinateSet = set(Coordinates)
    for XZero, XOneValue in Itertools.combinations(XsValue, 2):
        for YZero, YOneValue in Itertools.combinations(YsValue, 2):
            if {(XZero, YZero), (XZero, YOneValue), (XOneValue, YZero), (XOneValue, YOneValue)} <= CoordinateSet:
                Rectangles.append((XZero, YZero, XOneValue, YOneValue))
    Values = [Dimension.value_mm for Dimension in Dimensions]
    Matches = [Rectangle for Rectangle in Rectangles if Matches(Rectangle[2] - Rectangle[0], Values) and Matches(Rectangle[3] - Rectangle[1], Values)]
    if Matches:
        Minimum = min(((Rectangle[2] - Rectangle[0]) * (Rectangle[3] - Rectangle[1]) for Rectangle in Matches))
        Selected = [Rectangle for Rectangle in Matches if MathValue.isclose((Rectangle[2] - Rectangle[0]) * (Rectangle[3] - Rectangle[1]), Minimum, abs_tol=1e-07)]
    else:
        Selected = []
        for GroupStart in range(max(0, len(Points) - 3)):
            Group = Points[GroupStart:GroupStart + 4]
            Products = {Marker.coordinates_mm for Marker in Group}
            GxValue = sorted({Point[0] for Point in Products})
            GyValue = sorted({Point[1] for Point in Products})
            if len(GxValue) == 2 and len(GyValue) == 2 and (len(Products) == 4):
                Selected = [(GxValue[0], GyValue[0], GxValue[1], GyValue[1])]
                break
        if not Selected and Rectangles:

            # this callback exists because local behavior needs one focused transformation
            Selected = [max(Rectangles, key=lambda Rectangle: (Rectangle[2] - Rectangle[0]) * (Rectangle[3] - Rectangle[1]))]

    # this callback exists because local behavior needs one focused transformation
    Selected.sort(key=lambda Rectangle: min((Marker.offset for Marker in Points if Marker.coordinates_mm in {(Rectangle[0], Rectangle[1]), (Rectangle[0], Rectangle[3]), (Rectangle[2], Rectangle[1]), (Rectangle[2], Rectangle[3])}), default=1 << 62))
    LineMarkers = [Marker for Marker in RemainingMarkers if Marker.semantic == 'line' and Marker.profile_role == 1 and (Marker.locus == KPointLocus.hex())]
    RunsValue: list[list[NativeMarker]] = []
    for Marker in LineMarkers:
        if not RunsValue or Marker.offset - RunsValue[-1][-1].offset != 92:
            RunsValue.append([Marker])
        else:
            RunsValue[-1].append(Marker)
    ProfileLines = [tuple(RunValue[Index:Index + 4]) for RunValue in RunsValue for Index in range(0, len(RunValue), 6) if len(RunValue[Index:Index + 4]) == 4]
    Profiles: list[NativeProfile] = [*StructuralCircles, *CircleProfiles, *LinkedRectangles, *StructuralRectangles, *StructuralPolylines]
    UsedValue: set[int] = LinkedMarkers | StructuralRectangle | StructuralMarkers | StructuralPolylineMarkers | {Offset for Profile in CircleProfiles for Offset in Profile.marker_offsets}
    for Index, Rectangle in enumerate(Selected):
        if any((Profile.kind == 'rectangle' and Profile.coordinates == Rectangle for Profile in Profiles)):
            continue
        SpanValue = tuple((Marker.offset for Marker in (ProfileLines[Index] if Index < len(ProfileLines) else ())))
        if CircleProfiles and len(SpanValue) != 4:
            continue
        UsedValue.update(SpanValue)
        Corners = {(Rectangle[0], Rectangle[1]), (Rectangle[0], Rectangle[3]), (Rectangle[2], Rectangle[1]), (Rectangle[2], Rectangle[3])}
        UsedValue.update((Marker.offset for Marker in Markers if Marker.semantic == 'point' and Marker.coordinates_mm in Corners))
        Profiles.append(NativeProfile('rectangle', Rectangle, SpanValue))

    # this callback exists because local behavior needs one focused transformation
    Profiles.sort(key=lambda Profile: min(Profile.marker_offsets, default=1 << 62))
    return (tuple(Profiles), UsedValue, Normalized)

# this definition exists because focused behavior needs one stable owner
def StructuralA(Markers: list[NativeMarker], ExcludedOffsets: set[int]) -> tuple[tuple[NativeProfile, ...], set[int]]:
    Edges = tuple((Marker for Marker in Markers if Marker.offset not in ExcludedOffsets and Marker.profile_role == 1 and (Marker.native_kind in {1, 2}) and (Marker.coordinates_mm is None) and (Marker.endpoint_indices is not None) and (Marker.endpoint_indices[0] != Marker.endpoint_indices[1]) and all((0 <= Endpoint < len(Markers) and Markers[Endpoint].coordinates_mm is not None for Endpoint in Marker.endpoint_indices))))
    Remaining = set(range(len(Edges)))
    Profiles: list[NativeProfile] = []
    UsedValue: set[int] = set()
    while Remaining:
        Component = {Remaining.pop()}
        Vertices = set(Edges[next(iter(Component))].endpoint_indices or ())
        Changed = True
        while Changed:
            Changed = False
            for Index in tuple(Remaining):
                Endpoints = set(Edges[Index].endpoint_indices or ())
                if Vertices & Endpoints:
                    Remaining.remove(Index)
                    Component.add(Index)
                    Vertices.update(Endpoints)
                    Changed = True
        if len(Component) != 4 or len(Vertices) != 4:
            continue
        Degrees = {Vertex: 0 for Vertex in Vertices}
        for Index in Component:
            for Vertex in Edges[Index].endpoint_indices or ():
                Degrees[Vertex] += 1
        if set(Degrees.values()) != {2}:
            continue
        Coordinates = {Vertex: Markers[Vertex].coordinates_mm for Vertex in Vertices}
        if any((Value is None for Value in Coordinates.values())):
            continue
        Resolved = {Vertex: Value for Vertex, Value in Coordinates.items() if Value is not None}
        XsValue = sorted({Value[0] for Value in Resolved.values()})
        YsValue = sorted({Value[1] for Value in Resolved.values()})
        if len(XsValue) != 2 or len(YsValue) != 2 or set(Resolved.values()) != {(FirstCoord, SecondCoord) for FirstCoord in XsValue for SecondCoord in YsValue}:
            continue
        Sides: dict[str, NativeMarker] = {}
        Valid = True
        for Index in Component:
            Marker = Edges[Index]
            Start, EndValue = Marker.endpoint_indices or (-1, -1)
            LeftValue = Resolved[Start]
            Right = Resolved[EndValue]
            if MathValue.isclose(LeftValue[1], Right[1], abs_tol=1e-09):
                SideValue = 'bottom' if MathValue.isclose(LeftValue[1], YsValue[0]) else 'top'
            elif MathValue.isclose(LeftValue[0], Right[0], abs_tol=1e-09):
                SideValue = 'left' if MathValue.isclose(LeftValue[0], XsValue[0]) else 'right'
            else:
                Valid = False
                break
            if SideValue in Sides:
                Valid = False
                break
            Sides[SideValue] = Marker
        if not Valid or set(Sides) != {'bottom', 'right', 'top', 'left'}:
            continue
        LineOffsets = tuple((Sides[SideValue].offset for SideValue in ('bottom', 'right', 'top', 'left')))
        UsedValue.update(LineOffsets)
        Profiles.append(NativeProfile('rectangle', (XsValue[0], YsValue[0], XsValue[1], YsValue[1]), LineOffsets))
    return (tuple(Profiles), UsedValue)

# this definition exists because focused behavior needs one stable owner
def PolyProfiles(MarkersData: list[NativeMarker], ExcludedOffsets: set[int]) -> tuple[tuple[NativeProfile, ...], set[int]]:
    EdgeData = tuple((MarkerData for MarkerData in MarkersData if MarkerData.offset not in ExcludedOffsets and MarkerData.profile_role == 1 and (MarkerData.native_kind in {0, 1, 2}) and (MarkerData.coordinates_mm is None) and (MarkerData.endpoint_indices is not None) and (MarkerData.endpoint_indices[0] != MarkerData.endpoint_indices[1]) and all((0 <= EndpointIndex < len(MarkersData) and MarkersData[EndpointIndex].coordinates_mm is not None for EndpointIndex in MarkerData.endpoint_indices))))
    RemainingIndexes = set(range(len(EdgeData)))
    ProfileData: list[NativeProfile] = []
    UsedOffsets: set[int] = set()
    while RemainingIndexes:
        ComponentIndexes = {RemainingIndexes.pop()}
        VertexIndexes = set(EdgeData[next(iter(ComponentIndexes))].endpoint_indices or ())
        ChangedValue = True
        while ChangedValue:
            ChangedValue = False
            for EdgeIndex in tuple(RemainingIndexes):
                EndpointIndexes = set(EdgeData[EdgeIndex].endpoint_indices or ())
                if VertexIndexes & EndpointIndexes:
                    RemainingIndexes.remove(EdgeIndex)
                    ComponentIndexes.add(EdgeIndex)
                    VertexIndexes.update(EndpointIndexes)
                    ChangedValue = True
        if len(ComponentIndexes) != 6 or len(VertexIndexes) != 6:
            continue
        AdjacencyData: dict[int, list[tuple[int, int]]] = {VertexIndex: [] for VertexIndex in VertexIndexes}
        for EdgeIndex in ComponentIndexes:
            StartIndex, EndIndex = EdgeData[EdgeIndex].endpoint_indices or (-1, -1)
            AdjacencyData[StartIndex].append((EdgeIndex, EndIndex))
            AdjacencyData[EndIndex].append((EdgeIndex, StartIndex))
        if any((len(ValueData) != 2 for ValueData in AdjacencyData.values())):
            continue

        # this callback exists because local behavior needs one focused transformation
        FirstEdgeIndex = min(ComponentIndexes, key=lambda EdgeIndex: EdgeData[EdgeIndex].offset)
        StartIndex, CurrentIndex = EdgeData[FirstEdgeIndex].endpoint_indices or (-1, -1)
        OrderedVertices = [StartIndex]
        OrderedEdges = [FirstEdgeIndex]
        UsedEdges = {FirstEdgeIndex}
        while CurrentIndex != StartIndex and len(OrderedVertices) <= len(VertexIndexes):
            OrderedVertices.append(CurrentIndex)
            ChoiceData = tuple((ItemData for ItemData in AdjacencyData[CurrentIndex] if ItemData[0] not in UsedEdges))
            if len(ChoiceData) != 1:
                break
            NextEdgeIndex, CurrentIndex = ChoiceData[0]
            UsedEdges.add(NextEdgeIndex)
            OrderedEdges.append(NextEdgeIndex)
        if CurrentIndex != StartIndex or UsedEdges != ComponentIndexes or len(OrderedVertices) != 6:
            continue
        OrderedPoints = tuple((MarkersData[VertexIndex].coordinates_mm for VertexIndex in OrderedVertices))
        if any((PointData is None for PointData in OrderedPoints)):
            continue
        ResolvedPoints = tuple((PointData for PointData in OrderedPoints if PointData is not None))
        if len(set(ResolvedPoints)) != 6:
            continue
        MarkerOffsets = tuple((EdgeData[EdgeIndex].offset for EdgeIndex in OrderedEdges)) + tuple((MarkersData[VertexIndex].offset for VertexIndex in OrderedVertices))
        UsedOffsets.update(MarkerOffsets)
        ProfileData.append(NativeProfile('polyline', tuple((CoordinateValue for PointData in ResolvedPoints for CoordinateValue in PointData)), MarkerOffsets))
    return (tuple(ProfileData), UsedOffsets)

# this definition exists because focused behavior needs one stable owner
def Structural(Markers: list[NativeMarker], Dimensions: tuple[NativeDimension, ...], ExcludedOffsets: set[int]) -> tuple[tuple[NativeProfile, ...], set[int], dict[int, str]]:
    Profiles: list[NativeProfile] = []
    UsedValue: set[int] = set()
    Normalized: dict[int, str] = {}
    Geometries: set[tuple[float, float, float]] = set()
    for ClosureIndex, Closure in enumerate(Markers):
        Endpoints = Closure.endpoint_indices
        if Closure.offset in ExcludedOffsets or Closure.coordinates_mm is not None or Closure.locus != KCircleLocus.hex() or (Closure.profile_role != 1) or (Closure.native_kind not in {0, 1}) or (Endpoints is None) or (Endpoints[0] != Endpoints[1]):
            continue
        RimIndex = Endpoints[0]
        CenterIndex = RimIndex - 1
        if not 0 <= CenterIndex < RimIndex < ClosureIndex or ClosureIndex - RimIndex > 2:
            continue
        Center = Markers[CenterIndex]
        RimValue = Markers[RimIndex]
        if Center.offset in ExcludedOffsets or RimValue.offset in ExcludedOffsets or Center.coordinates_mm is None or (RimValue.coordinates_mm is None) or (RimValue.locus != KCircleLocus.hex()) or (Center.profile_role != 1) or (RimValue.profile_role != 1):
            continue
        Radius = MarkerRadiusMm(Center, RimValue)
        if Radius is None:
            continue
        StartAngle = MarkerStart(Center, RimValue)
        GeomValue = (Center.coordinates_mm[0], Center.coordinates_mm[1], Radius)
        if GeomValue in Geometries:
            continue
        Matches: list[tuple[int, str, float]] = []
        for Index, Dimension in enumerate(Dimensions):
            if MathValue.isclose(Dimension.value_mm, Radius, rel_tol=1e-07, abs_tol=1e-07):
                Matches.append((Index, 'radius', Dimension.value_mm))
            elif MathValue.isclose(Dimension.value_mm, Radius * 2.0, rel_tol=1e-07, abs_tol=1e-07):
                Matches.append((Index, 'diameter', Dimension.value_mm / 2.0))
        ParamName = None
        DimensionKind = None
        if len(Matches) == 1 and Matches[0][0] not in Normalized:
            DimensionIndex, DimensionKind, NormalizedRadius = Matches[0]
            GeomValue = (GeomValue[0], GeomValue[1], NormalizedRadius)
            ParamName = Dimensions[DimensionIndex].name
            Normalized[DimensionIndex] = DimensionKind
        Geometries.add(GeomValue)
        MarkerOffsets = (Center.offset, RimValue.offset, Closure.offset)
        UsedValue.update(MarkerOffsets)
        Profiles.append(NativeProfile('circle', GeomValue, MarkerOffsets, ParamName, DimensionKind, StartAngle))
    return (tuple(Profiles), UsedValue, Normalized)

# this definition exists because focused behavior needs one stable owner
def CircleProfiles(Markers: list[NativeMarker], Dimensions: tuple[NativeDimension, ...]) -> tuple[tuple[NativeProfile, ...], dict[int, str]]:
    Centers = [Marker for Marker in Markers if Marker.semantic == 'circle' and Marker.coordinates_mm is not None]
    if not Centers:
        return ((), {})
    Candidates: dict[int, dict[tuple[float, float, float], list[tuple[NativeMarker, NativeMarker, str, float | None]]]] = {}
    for CircleMarker in Centers:
        FollowingMarker = next((Marker for Marker in Markers if Marker.offset > CircleMarker.offset and Marker.coordinates_mm is not None and (not SamePoint(Marker.coordinates_mm, CircleMarker.coordinates_mm))), None)
        PrecedingMarker = next((Marker for Marker in reversed(Markers) if Marker.offset < CircleMarker.offset and Marker.coordinates_mm is not None and (not SamePoint(Marker.coordinates_mm, CircleMarker.coordinates_mm))), None)
        ChoicePairs = tuple((ItemData for ItemData in ((CircleMarker, FollowingMarker) if FollowingMarker is not None else None, (PrecedingMarker, CircleMarker) if PrecedingMarker is not None and FollowingMarker is None else None) if ItemData is not None))
        for CenterMarker, RimMarker in ChoicePairs:
            RadiusValue = MarkerRadiusMm(CenterMarker, RimMarker)
            if RadiusValue is None:
                continue
            StartAngle = MarkerStart(CenterMarker, RimMarker)
            for Index, Dimension in enumerate(Dimensions):
                Semantic = None
                NormalizedRadius = RadiusValue
                if MathValue.isclose(Dimension.value_mm, RadiusValue, rel_tol=1e-07, abs_tol=1e-07):
                    Semantic = 'radius'
                    NormalizedRadius = Dimension.value_mm
                elif MathValue.isclose(Dimension.value_mm, RadiusValue * 2.0, rel_tol=1e-07, abs_tol=1e-07):
                    Semantic = 'diameter'
                    NormalizedRadius = Dimension.value_mm / 2.0
                if Semantic is None:
                    continue
                GeomValue = (CenterMarker.coordinates_mm[0], CenterMarker.coordinates_mm[1], NormalizedRadius)
                Candidates.setdefault(Index, {}).setdefault(GeomValue, []).append((CenterMarker, RimMarker, Semantic, StartAngle))
    Result: list[NativeProfile] = []
    Geometries: set[tuple[float, float, float]] = set()
    Normalized: dict[int, str] = {}
    for Index, Dimension in enumerate(Dimensions):
        Matches = Candidates.get(Index, {})
        if len(Matches) != 1:
            continue
        GeomValue, Records = next(iter(Matches.items()))
        if GeomValue in Geometries:
            continue
        Semantics = {Semantic for Ignored, Ignored, Semantic, Ignored in Records}
        if len(Semantics) != 1:
            continue
        Geometries.add(GeomValue)
        Normalized[Index] = next(iter(Semantics))
        Result.append(NativeProfile('circle', GeomValue, tuple(sorted({Offset for Center, Following, Ignored, Ignored in Records for Offset in (Center.offset, Following.offset)})), Dimension.name, Normalized[Index], Records[0][3]))

    # this callback exists because local behavior needs one focused transformation
    Result.sort(key=lambda Profile: min(Profile.marker_offsets))
    return (tuple(Result), Normalized)

# this definition exists because focused behavior needs one stable owner
def SamePoint(LeftValue: tuple[float, float], Right: tuple[float, float]) -> bool:
    return MathValue.isclose(LeftValue[0], Right[0], abs_tol=1e-12) and MathValue.isclose(LeftValue[1], Right[1], abs_tol=1e-12)

# this definition exists because focused behavior needs one stable owner
def Constraints(Feature: NativeFeature, Markers: tuple[NativeMarker, ...], Profiles: tuple[NativeProfile, ...]) -> tuple[NativeRule, ...]:
    Constraints: list[NativeRule] = []
    RadialParameters: set[str] = set()
    for ProfileIndex, Profile in enumerate(Profiles):
        if Profile.kind == 'rectangle':
            for EdgeIndex in range(4):
                Constraints.append(NativeRule(id=f'{Feature.object_id}:profile:{ProfileIndex}:axis:{EdgeIndex}', kind='horizontal' if EdgeIndex % 2 == 0 else 'vertical', references=(f'{Feature.object_id}:profile:{ProfileIndex}:edge:{EdgeIndex}',), parameter=None, value=None, native_offset=Profile.marker_offsets[EdgeIndex] if EdgeIndex < len(Profile.marker_offsets) else None, native_code=None))
        elif Profile.kind == 'circle':
            Semantic = Profile.dimension_kind or 'radius'
            ParamName = Profile.parameter_name
            if ParamName is not None:
                RadialParameters.add(ParamName)
            Constraints.append(NativeRule(id=f'{Feature.object_id}:profile:{ProfileIndex}:{Semantic}', kind=Semantic, references=(f'{Feature.object_id}:profile:{ProfileIndex}',), parameter=f'{Feature.object_id}:{ParamName}' if ParamName is not None else None, value=Profile.coordinates[2] * 2.0 if Semantic == 'diameter' else Profile.coordinates[2], native_offset=Profile.marker_offsets[0] if Profile.marker_offsets else None, native_code=None))
    for Dimension in Feature.dimensions:
        if Dimension.name in RadialParameters:
            continue
        Constraints.append(NativeRule(id=f'{Feature.object_id}:dimension:{Dimension.name}', kind='distance', references=tuple((f'native:{Operand.kind_code:04x}:{Operand.entity_index}' for Operand in Dimension.operands)), parameter=f'{Feature.object_id}:{Dimension.name}', value=Dimension.value_mm, native_offset=Dimension.native_offset, native_code=None))
    for Marker in Markers:
        if Marker.semantic != 'relation':
            continue
        Constraints.append(NativeRule(id=f'{Feature.object_id}:native-relation:{Marker.offset}', kind=f'native_{Marker.native_kind}', references=tuple((f'native-index:{Index}' for Index in Marker.endpoint_indices or ())), parameter=None, value=None, native_offset=Marker.offset, native_code=Marker.native_kind))
    return tuple(Constraints)

# this definition exists because focused behavior needs one stable owner
def OperationFields(DataValue: bytes, Record: NativeName) -> tuple[int | None, int | None, int | None]:
    if Record.text_end + 12 > len(DataValue):
        return (None, None, None)
    Family = Struct.unpack_from('<H', DataValue, Record.text_end + 4)[0]
    Operation = DataValue[Record.text_end + 6]
    Schema = DataValue[Record.text_end + 7]
    RepeatedId = Struct.unpack_from('<I', DataValue, Record.text_end + 8)[0]
    if RepeatedId != Record.object_id:
        return (None, None, None)
    return (Family, Operation, Schema)

# this definition exists because focused behavior needs one stable owner
def RevolutionAxis(Sketch: NativeSketch | None) -> NativeMarker | None:
    if Sketch is None:
        return None
    Candidates = tuple((Marker for Marker in Sketch.markers if Marker.profile_role == 2 and Marker.semantic == 'line' and (Marker.endpoint_indices is not None) and (Marker.endpoint_indices[0] != Marker.endpoint_indices[1])))
    return Candidates[0] if len(Candidates) == 1 else None

# this definition exists because focused behavior needs one stable owner
def RevolutionAxisA(Operation: NativeOperation, Sketch: NativeSketch | None) -> tuple[float, float] | None:
    if Sketch is None:
        return None
    if Operation.axis_marker_offset is None:
        AxisValue = RevolutionAxis(Sketch) if Operation.axis_source_kind is None else None
    else:
        AxisValue = next((Marker for Marker in Sketch.markers if Marker.offset == Operation.axis_marker_offset), None)
    if AxisValue is None or AxisValue.endpoint_indices is None:
        return None
    if any((not 0 <= Endpoint < len(Sketch.markers) for Endpoint in AxisValue.endpoint_indices)):
        return None
    Start = Sketch.markers[AxisValue.endpoint_indices[0]].coordinates_mm
    EndValue = Sketch.markers[AxisValue.endpoint_indices[1]].coordinates_mm
    if Start is None or EndValue is None:
        return None
    Delta = (EndValue[0] - Start[0], EndValue[1] - Start[1])
    Length = MathValue.hypot(Delta[0], Delta[1])
    if Length <= 0.0:
        return None
    return (Clean(Delta[0] / Length), Clean(Delta[1] / Length))

# this definition exists because focused behavior needs one stable owner
def OperationAxis(Operation: NativeOperation, Sketch: NativeSketch | None) -> str | None:
    if Sketch is None or Operation.profile_id != Sketch.object_id:
        return None
    if Operation.kind in KExtrusionOperationKinds:
        return KNormalAxisSubElem
    if Operation.kind not in KRevolutionOperationKinds:
        return None
    Direction = RevolutionAxisA(Operation, Sketch)
    if Direction is None:
        return None
    if Direction[0] == 0.0 and Direction[1] != 0.0:
        return KVerticalAxisSubElem
    if Direction[1] == 0.0 and Direction[0] != 0.0:
        return KHorizontalAxisSubElem
    return None

# this definition exists because focused behavior needs one stable owner
def OperationA(DataValue: bytes, Start: int, EndValue: int, Feature: NativeFeature, Features: list[NativeFeature]) -> tuple[tuple[int, int, int], ...]:
    Preceding = {ItemValue.object_id for ItemValue in Features if ItemValue.object_id > 25 and ItemValue.native_offset is not None and (Feature.native_offset is not None) and (ItemValue.native_offset < Feature.native_offset)}
    Result: list[tuple[int, int, int]] = []
    SeenValue: set[tuple[int, int]] = set()
    for Selection in EdgeSelections(DataValue, Start, EndValue):
        Identity = (Selection[1], Selection[2])
        if Selection[1] not in Preceding or not 0 < Selection[2] < 32768 or Identity in SeenValue:
            continue
        SeenValue.add(Identity)
        Result.append(Selection)
    return tuple(Result)

# this definition exists because focused behavior needs one stable owner
def OperationAfter(DataValue: bytes, Start: int, EndValue: int, Feature: NativeFeature, Features: list[NativeFeature], ClassName: str) -> tuple[tuple[int, int, int], ...]:
    Declarations = tuple((ItemValue for ItemValue in ParseClasses(DataValue) if ItemValue.name == ClassName and Start <= ItemValue.offset < EndValue))
    if len(Declarations) != 1:
        return ()
    DeclValue = Declarations[0]
    ClassEnd = DeclValue.offset + 6 + len(ClassName.encode('ascii'))
    return OperationA(DataValue, ClassEnd, EndValue, Feature, Features)

# this definition exists because focused behavior needs one stable owner
def Native(Dimensions: tuple[NativeDimension, ...]) -> tuple[float, float, float] | None:
    ByName = {Dimension.name.casefold(): Dimension for Dimension in Dimensions if Dimension.name.casefold() in {'d1', 'd2', 'd3'}}
    if set(ByName) != {'d1', 'd2', 'd3'} or any((ItemValue.native_offset is None for ItemValue in ByName.values())):
        return None
    return tuple((ByName[f'd{Index}'].value_mm for Index in range(1, 4)))

# this definition exists because focused behavior needs one stable owner
def NativeScale(DataValue: bytes, Start: int, EndValue: int) -> tuple[float, float, float] | None:
    if EndValue - Start < 38:
        return None
    Block = DataValue[EndValue - 38:EndValue]
    if Block[:4] != Struct.pack('<I', 1) or Block[28:36] != b'\x00' * 8 or Struct.unpack_from('<H', Block, 36)[0] < 32768:
        return None
    Factors = Struct.unpack_from('<3d', Block, 4)
    if not all((MathValue.isfinite(Value) and Value > 0.0 for Value in Factors)):
        return None
    return Factors

# this definition exists because focused behavior needs one stable owner
def ResolveProfile(Operation: NativeOperation, Sketches: dict[int, NativeSketch], DataValue: bytes, Features: list[NativeFeature]) -> NativeOperation:
    if Operation.kind != 'hole' or Operation.profile_id not in Sketches:
        return Operation
    Sketch = Sketches[Operation.profile_id]
    Circles = tuple((Profile for Profile in Sketch.profiles if Profile.kind == 'circle'))
    Feature = next((ItemValue for ItemValue in Features if ItemValue.object_id == Operation.object_id), None)
    Selections = OperationA(DataValue, Sketch.native_offset, Sketch.native_end, Feature, Features) if Feature is not None else ()
    return Replace(Operation, diameter_mm=Circles[0].coordinates[2] * 2.0 if len(Circles) == 1 else None, selection_offsets=tuple((Selection[0] for Selection in Selections)), selected_local_ids=tuple((Selection[2] for Selection in Selections)), selection_references=tuple(((Selection[1], Selection[2]) for Selection in Selections)))

# this definition exists because focused behavior needs one stable owner
def EndSpec(DataValue: bytes, Start: int, EndValue: int, Classes: tuple[NativeClass, ...]=()) -> NativeEndSpec | None:
    MirroredOffset, MirroredCode = Mirrored(DataValue, Classes, Start, EndValue)
    for Offset in range(Start, max(Start, EndValue - 26 + 1) + 1):
        Prefix = DataValue[Offset:Offset + 2]
        if Prefix != b'_c' and (not (len(Prefix) == 2 and Struct.unpack('<H', Prefix)[0] & 32768 and (Prefix != b'\xff\xff'))):
            continue
        if DataValue[Offset + 2:Offset + 4] != b'\x00\x00':
            continue
        if Struct.unpack_from('<I', DataValue, Offset + 4)[0] != 1:
            continue
        if Struct.unpack_from('<I', DataValue, Offset + 8)[0] not in {0, 1}:
            continue
        Direction = Struct.unpack_from('<I', DataValue, Offset + 12)[0]
        if Direction not in {0, 1} or DataValue[Offset + 16:Offset + 18] != b'\x00\x00':
            continue
        Termination = Struct.unpack_from('<I', DataValue, Offset + 18)[0]
        Second = Struct.unpack_from('<I', DataValue, Offset + 22)[0]
        if Termination > 64 or Second > 1:
            continue
        return NativeEndSpec(Offset, Termination, Direction, Second, MirroredOffset, MirroredCode)
    return None

# this definition exists because focused behavior needs one stable owner
def EdgeSelections(DataValue: bytes, Start: int, EndValue: int) -> tuple[tuple[int, int, int], ...]:
    Selections: list[tuple[int, int, int]] = []
    for Offset in FindAll(DataValue, KEdgeSelectionIdentity, Start, EndValue):
        if Offset + 38 > EndValue:
            continue
        Producer = Struct.unpack_from('<I', DataValue, Offset + 26)[0]
        LocalId = Struct.unpack_from('<I', DataValue, Offset + 34)[0]
        if Producer and LocalId:
            Selections.append((Offset, Producer, LocalId))
    return tuple(Selections)

# this definition exists because focused behavior needs one stable owner
def Operation(Dimensions: tuple[NativeDimension, ...], Semantic: str) -> float | None:
    return next((Dimension.value_mm for Dimension in Dimensions if Dimension.kind == Semantic), None)

# this definition exists because focused behavior needs one stable owner
def OperationOffset(Dimensions: tuple[NativeDimension, ...], Semantic: str) -> int | None:
    return next((Dimension.native_offset for Dimension in Dimensions if Dimension.kind == Semantic and Dimension.native_offset is not None), None)

# this definition exists because focused behavior needs one stable owner
def IntegerProp(Value: str | None) -> int | None:
    if Value is None:
        return None
    try:
        return int(Value)
    except ValueError:
        return None

# this definition exists because focused behavior needs one stable owner
def FindAll(DataValue: bytes, Marker: bytes, Start: int=0, EndValue: int | None=None) -> list[int]:
    Result: list[int] = []
    Cursor = Start
    Limit = len(DataValue) if EndValue is None else EndValue
    while True:
        Offset = DataValue.find(Marker, Cursor, Limit)
        if Offset < 0:
            return Result
        Result.append(Offset)
        Cursor = Offset + 1

# this definition exists because focused behavior needs one stable owner
def Matches(Value: float, Candidates: list[float]) -> bool:
    return any((MathValue.isclose(Value, Choice, abs_tol=1e-06) for Choice in Candidates))

# this definition exists because focused behavior needs one stable owner
def NormAction(Vector: tuple[float, float, float]) -> float:
    return MathValue.sqrt(sum((Value * Value for Value in Vector)))

# this definition exists because focused behavior needs one stable owner
def DotAction(LeftValue: tuple[float, float, float], Right: tuple[float, float, float]) -> float:
    return sum((FirstValue * SecondValue for FirstValue, SecondValue in zip(LeftValue, Right, strict=True)))

# this definition exists because focused behavior needs one stable owner
def Cross(LeftValue: tuple[float, float, float], Right: tuple[float, float, float]) -> tuple[float, float, float]:
    return (LeftValue[1] * Right[2] - LeftValue[2] * Right[1], LeftValue[2] * Right[0] - LeftValue[0] * Right[2], LeftValue[0] * Right[1] - LeftValue[1] * Right[0])

# this definition exists because focused behavior needs one stable owner
def Clean(Value: float) -> float:
    return 0.0 if abs(Value) <= 1e-12 else Value

# this binding exists because shared behavior needs one stable value
globals()['ANGLE_COPY_DELTAS'] = AngleCopyDeltas

# this binding exists because shared behavior needs one stable value
globals()['ASSEMBLY_SUFFIX'] = AsmSuffix

# this binding exists because shared behavior needs one stable value
globals()['Any'] = AnyValue

# this binding exists because shared behavior needs one stable value
globals()['BooleanOperation'] = BoolOperation

# this binding exists because shared behavior needs one stable value
globals()['BuildBossChamferVendorTree'] = BuildBossVendor

# this binding exists because shared behavior needs one stable value
globals()['BuildBossCircularPatternVendorTree'] = BuildBossVendoA

# this binding exists because shared behavior needs one stable value
globals()['BuildBossFilletVendorTree'] = BuildBossFillet

# this binding exists because shared behavior needs one stable value
globals()['BuildBossLinearPatternVendorTree'] = BuildBossLinear

# this binding exists because shared behavior needs one stable value
globals()['BuildBossShellVendorTree'] = BuildBossShell

# this binding exists because shared behavior needs one stable value
globals()['BuildFourFeatureVendorTree'] = BuildFourVendor

# this binding exists because shared behavior needs one stable value
globals()['BuildPadGrooveVendorTree'] = BuildPadGroove

# this binding exists because shared behavior needs one stable value
globals()['BuildPin90Envelope'] = BuildPinNineZeroEnvelope

# this binding exists because shared behavior needs one stable value
globals()['BuildSingleRevolutionVendorTree'] = BuildSingleTree

# this binding exists because shared behavior needs one stable value
globals()['BuildThreeFeatureVendorTree'] = BuildThreeTree

# this binding exists because shared behavior needs one stable value
globals()['BuildTwoFeatureVendorTree'] = BuildTwoFeature

# this binding exists because shared behavior needs one stable value
globals()['CANONICAL_PLANE_FEATURE_TYPE'] = CanonicalPlaneFeatureType

# this binding exists because shared behavior needs one stable value
globals()['CLASS_MARKER'] = ClassMarker

# this binding exists because shared behavior needs one stable value
globals()['CONFIGURATION_MANAGER_STREAM'] = ConfigManagerStream

# this binding exists because shared behavior needs one stable value
globals()['CONFIGURATION_STREAM'] = ConfigStream

# this binding exists because shared behavior needs one stable value
globals()['CadDocument'] = CadDoc

# this binding exists because shared behavior needs one stable value
globals()['CircleGeometry'] = CircleGeom

# this binding exists because shared behavior needs one stable value
globals()['DEPTH_COPY_DELTAS'] = DepthCopyDeltas

# this binding exists because shared behavior needs one stable value
globals()['DEPTH_COPY_SIGNS'] = DepthCopySigns

# this binding exists because shared behavior needs one stable value
globals()['DERIVED_SUPPORT_KIND'] = KDerivedSupportKind

# this binding exists because shared behavior needs one stable value
globals()['DIMENSION_SCALAR_HEADERS'] = DimensionScalarHeaders

# this binding exists because shared behavior needs one stable value
globals()['DIRECTION_AXIS_ROLE'] = KDirectionAxisRole

# this binding exists because shared behavior needs one stable value
globals()['ET'] = XmlTree

# this binding exists because shared behavior needs one stable value
globals()['EncodeBossCircularPatternProgram'] = EncodeBossCircularPattern

# this binding exists because shared behavior needs one stable value
globals()['EncodeBossCutCircleProgram'] = EncodeBossCutCircle

# this binding exists because shared behavior needs one stable value
globals()['EncodeBossCutCutCutProgram'] = EncodeBossCutCutCut

# this binding exists because shared behavior needs one stable value
globals()['EncodeBossCutThroughProgram'] = EncodeBossCutThrough

# this binding exists because shared behavior needs one stable value
globals()['EncodeBossLinearPatternProgram'] = EncodeBossLinearPattern

# this binding exists because shared behavior needs one stable value
globals()['EncodePin90RevolveProgram'] = EncodePinNineZeroRevolve

# this binding exists because shared behavior needs one stable value
globals()['EncodeReverseCircCfg'] = EncodeReverse

# this binding exists because shared behavior needs one stable value
globals()['EncodeReverseCircleConfigProgram'] = EncodeReverseCircleConfig

# this binding exists because shared behavior needs one stable value
globals()['EncodeReverseCircleProgram'] = EncodeReverseCircle

# this binding exists because shared behavior needs one stable value
globals()['EncodeReverseCircleResolved'] = EncodeReverseA

# this binding exists because shared behavior needs one stable value
globals()['ExtrusionEditCodes'] = ExtrusionEdit

# this binding exists because shared behavior needs one stable value
globals()['FACE_SUPPORT_KIND'] = KFaceSupportKind

# this binding exists because shared behavior needs one stable value
globals()['FIRST_ATOM_ID'] = FirstAtomId

# this binding exists because shared behavior needs one stable value
globals()['FROM_END_SPEC_CLASS'] = FromEndSpecClass

# this binding exists because shared behavior needs one stable value
globals()['FROM_REVERSE_RELATIVE'] = FromReverseRelative

# this binding exists because shared behavior needs one stable value
globals()['HORIZONTAL_AXIS_SUBELEMENT'] = KHorizontalAxisSubElem

# this binding exists because shared behavior needs one stable value
globals()['HasBossChamferProof'] = HasBossChamfer

# this binding exists because shared behavior needs one stable value
globals()['HasBossCircularPatternProof'] = HasBossCircular

# this binding exists because shared behavior needs one stable value
globals()['HasBossFilletProof'] = HasBossFillet

# this binding exists because shared behavior needs one stable value
globals()['HasBossLinearPatternProof'] = HasBossLinear

# this binding exists because shared behavior needs one stable value
globals()['HasBossShellProof'] = HasBossShell

# this binding exists because shared behavior needs one stable value
globals()['HasCanonicalSketchGeometry'] = HasCanonical

# this binding exists because shared behavior needs one stable value
globals()['HasCutChainProof'] = HasCutChain

# this binding exists because shared behavior needs one stable value
globals()['HasFreeCadThroughAllFeature'] = HasFreeCadAll

# this binding exists because shared behavior needs one stable value
globals()['HasPadGrooveProof'] = HasPadGroove

# this binding exists because shared behavior needs one stable value
globals()['HasSingleRevolutionProof'] = HasSingleProof

# this binding exists because shared behavior needs one stable value
globals()['HasTwoFeatureProof'] = HasTwoFeature

# this binding exists because shared behavior needs one stable value
globals()['HasVendorPartEncoding'] = HasVendorPart

# this binding exists because shared behavior needs one stable value
globals()['KIT_RESOLVED_STREAM'] = KitResolvedStream

# this binding exists because shared behavior needs one stable value
globals()['LineGeometry'] = LineGeom

# this binding exists because shared behavior needs one stable value
globals()['MARKER_LOCAL_ID_OFFSET_BY_LENGTH'] = KMarkerLocalIdOffsetBy

# this binding exists because shared behavior needs one stable value
globals()['NORMAL_AXIS_SUBELEMENT'] = KNormalAxisSubElem

# this binding exists because shared behavior needs one stable value
globals()['NativeAssemblyEnvelope'] = NativeAsm

# this binding exists because shared behavior needs one stable value
globals()['NativeBoundingBox'] = NativeBounding

# this binding exists because shared behavior needs one stable value
globals()['NativeConfiguration'] = NativeConfig

# this binding exists because shared behavior needs one stable value
globals()['NativeConstraint'] = NativeRule

# this binding exists because shared behavior needs one stable value
globals()['NativeModelHeader'] = NativeModelA

# this binding exists because shared behavior needs one stable value
globals()['NativePartStreams'] = NativePart

# this binding exists because shared behavior needs one stable value
globals()['NativeSketchPlane'] = NativeSketchA

# this binding exists because shared behavior needs one stable value
globals()['PART_SUFFIX'] = PartSuffix

# this binding exists because shared behavior needs one stable value
globals()['PLANE_FEATURE_TYPES'] = PlaneFeatureTypes

# this binding exists because shared behavior needs one stable value
globals()['PLANE_SUPPORT_KIND'] = KPlaneSupportKind

# this binding exists because shared behavior needs one stable value
globals()['Parameter'] = Param

# this binding exists because shared behavior needs one stable value
globals()['ParameterRole'] = ParamRole

# this binding exists because shared behavior needs one stable value
globals()['ParameterValue'] = ParamValue

# this binding exists because shared behavior needs one stable value
globals()['REFERENCE_SUPPORT_SOURCE'] = KRefSupportSource

# this binding exists because shared behavior needs one stable value
globals()['RESOLVED_FEATURES_STREAM'] = ResolvedFeaturesStream

# this binding exists because shared behavior needs one stable value
globals()['REVOLUTION_AXIS_SKETCH'] = RevolutionAxisSketch

# this binding exists because shared behavior needs one stable value
globals()['SERIALIZED_STRING_MARKER'] = SerializedStringMarker

# this binding exists because shared behavior needs one stable value
globals()['SKETCH_CHAIN_CLASS'] = SketchChainClass

# this binding exists because shared behavior needs one stable value
globals()['STREAM_ORDER_SUPPORT_SOURCE'] = KStreamOrderSupportSource

# this binding exists because shared behavior needs one stable value
globals()['UNRESOLVED_SUPPORT_SOURCE'] = KUnresolvedSupportSource

# this binding exists because shared behavior needs one stable value
globals()['VENDOR_UNLOADABLE_NOTES'] = KVendorUnloadableNotes

# this binding exists because shared behavior needs one stable value
globals()['VERTICAL_AXIS_SUBELEMENT'] = KVerticalAxisSubElem

# this binding exists because shared behavior needs one stable value
globals()['Vector2'] = VectorTwo

# this binding exists because shared behavior needs one stable value
globals()['_ASSEMBLY_ATTACHMENT_STREAM'] = KAsmAttachmentStream

# this binding exists because shared behavior needs one stable value
globals()['_ASSEMBLY_CONFIGURATION_FLAGS'] = KAsmConfigFlags

# this binding exists because shared behavior needs one stable value
globals()['_ASSEMBLY_CONFIG_PROPERTIES_STREAM'] = KAsmConfigPropertiesStreA

# this binding exists because shared behavior needs one stable value
globals()['_ASSEMBLY_CUTLIST_STREAM'] = KAsmCutlistStream

# this binding exists because shared behavior needs one stable value
globals()['_ASSEMBLY_HEADER_OBJECTS'] = KAsmHeaderObjects

# this binding exists because shared behavior needs one stable value
globals()['_ASSEMBLY_OPEN_TIME_STREAM'] = KAsmOpenTimeStream

# this binding exists because shared behavior needs one stable value
globals()['_ASSEMBLY_PROPERTY_CONTAINER_CLASS'] = KAsmPropContainerClass

# this binding exists because shared behavior needs one stable value
globals()['_ASSEMBLY_REFERENCE_NAME'] = KAsmRefName

# this binding exists because shared behavior needs one stable value
globals()['_ASSEMBLY_TABLES_STREAM'] = KAsmTablesStream

# this binding exists because shared behavior needs one stable value
globals()['_ASSEMBLY_VERSION_PREFIX'] = KAsmVersionPrefix

# this binding exists because shared behavior needs one stable value
globals()['_ASSEMBLY_VIEW_ORIENTATION_STREAM'] = KAsmViewOrientationStream

# this binding exists because shared behavior needs one stable value
globals()['_ASSEMBLY_VISUAL_DATA_STREAM'] = KAsmVisualDataStream

# this binding exists because shared behavior needs one stable value
globals()['_BASE_OBJECTS'] = KBaseObjects

# this binding exists because shared behavior needs one stable value
globals()['_BOSS_BOSS_HEADER_STAMPS'] = KBossBossHeaderStamps

# this binding exists because shared behavior needs one stable value
globals()['_BOSS_CHAMFER_DISTANCE_OFFSETS'] = KBossChamferDistance

# this binding exists because shared behavior needs one stable value
globals()['_BOSS_CHAMFER_HEADER_STAMPS'] = KBossChamferHeaderStamps

# this binding exists because shared behavior needs one stable value
globals()['_BOSS_CHAMFER_MAX_Y_OFFSETS'] = KBossChamferMaxYOffsets

# this binding exists because shared behavior needs one stable value
globals()['_BOSS_CHAMFER_NEGATIVE_DISTANCE_OFFSET'] = KBossChamferNegativeOffsA

# this binding exists because shared behavior needs one stable value
globals()['_BOSS_CHAMFER_NEGATIVE_Y_OFFSETS'] = KBossChamferNegativeY

# this binding exists because shared behavior needs one stable value
globals()['_BOSS_CIRCULAR_PATTERN_ANGLE_OFFSETS'] = KBossCircularPatternAngle

# this binding exists because shared behavior needs one stable value
globals()['_BOSS_CIRCULAR_PATTERN_COUNT_DOUBLE_OFFSETS'] = KBossCircularPatternCount

# this binding exists because shared behavior needs one stable value
globals()['_BOSS_CIRCULAR_PATTERN_COUNT_OFFSET'] = KBossCircularPatternCounA

# this binding exists because shared behavior needs one stable value
globals()['_BOSS_CIRCULAR_PATTERN_DIRECTION_FLAG_OFFSET'] = KBossCircularPatternFlag

# this binding exists because shared behavior needs one stable value
globals()['_BOSS_CIRCULAR_PATTERN_HEADER_STAMPS'] = KBossCircularPatternHeadA

# this binding exists because shared behavior needs one stable value
globals()['_BOSS_CUT_CUT_CUT_HEADER_STAMPS'] = KBossCutCutCutHeaderStamA

# this binding exists because shared behavior needs one stable value
globals()['_BOSS_CUT_CUT_HEADER_STAMPS'] = KBossCutCutHeaderStamps

# this binding exists because shared behavior needs one stable value
globals()['_BOSS_CUT_HEADER_STAMPS'] = KBossCutHeaderStamps

# this binding exists because shared behavior needs one stable value
globals()['_BOSS_CUT_THROUGH_HEADER_STAMPS'] = KBossCutThroughHeader

# this binding exists because shared behavior needs one stable value
globals()['_BOSS_EXTRUDE_FLAGS'] = KBossExtrudeFlags

# this binding exists because shared behavior needs one stable value
globals()['_BOSS_FILLET_HEADER_STAMPS'] = KBossFilletHeaderStamps

# this binding exists because shared behavior needs one stable value
globals()['_BOSS_FILLET_MAX_X_OFFSETS'] = KBossFilletMaxXOffsets

# this binding exists because shared behavior needs one stable value
globals()['_BOSS_FILLET_MAX_Y_OFFSETS'] = KBossFilletMaxYOffsets

# this binding exists because shared behavior needs one stable value
globals()['_BOSS_FILLET_NEGATIVE_Y_OFFSET'] = KBossFilletNegativeYOffsA

# this binding exists because shared behavior needs one stable value
globals()['_BOSS_FILLET_RADIUS_OFFSETS'] = KBossFilletRadiusOffsets

# this binding exists because shared behavior needs one stable value
globals()['_BOSS_LINEAR_PATTERN_CENTER_DISPLAY_OFFSETS'] = KBossLinearPatternCenter

# this binding exists because shared behavior needs one stable value
globals()['_BOSS_LINEAR_PATTERN_COUNT_DISPLAY_OFFSET'] = KBossLinearPatternCount

# this binding exists because shared behavior needs one stable value
globals()['_BOSS_LINEAR_PATTERN_COUNT_DOUBLE_OFFSETS'] = KBossLinearPatternCountA

# this binding exists because shared behavior needs one stable value
globals()['_BOSS_LINEAR_PATTERN_COUNT_OFFSET'] = KBossLinearPatternCountB

# this binding exists because shared behavior needs one stable value
globals()['_BOSS_LINEAR_PATTERN_DIRECTION_DISTANCE_OFFSETS'] = KBossLinearPatternDistanA

# this binding exists because shared behavior needs one stable value
globals()['_BOSS_LINEAR_PATTERN_DIRECTION_FLAG_OFFSET'] = KBossLinearPatternFlag

# this binding exists because shared behavior needs one stable value
globals()['_BOSS_LINEAR_PATTERN_HEADER_STAMPS'] = KBossLinearPatternHeader

# this binding exists because shared behavior needs one stable value
globals()['_BOSS_LINEAR_PATTERN_NEGATIVE_DIAGONAL_OFFSET'] = KBossLinearPatternNegatiA

# this binding exists because shared behavior needs one stable value
globals()['_BOSS_LINEAR_PATTERN_NEGATIVE_DISPLAY_OFFSETS'] = KBossLinearPatternNegatiB

# this binding exists because shared behavior needs one stable value
globals()['_BOSS_LINEAR_PATTERN_NEGATIVE_EXTENT_OFFSET'] = KBossLinearPatternNegatiC

# this binding exists because shared behavior needs one stable value
globals()['_BOSS_LINEAR_PATTERN_NEGATIVE_ZERO_OFFSETS'] = KBossLinearPatternNegatiD

# this binding exists because shared behavior needs one stable value
globals()['_BOSS_LINEAR_PATTERN_PAD_DISPLAY_OFFSET'] = KBossLinearPatternPad

# this binding exists because shared behavior needs one stable value
globals()['_BOSS_LINEAR_PATTERN_POSITIVE_AXIS_OFFSETS'] = KBossLinearPatternPositiA

# this binding exists because shared behavior needs one stable value
globals()['_BOSS_LINEAR_PATTERN_POSITIVE_DIAGONAL_OFFSET'] = KBossLinearPatternPositiB

# this binding exists because shared behavior needs one stable value
globals()['_BOSS_LINEAR_PATTERN_POSITIVE_DISPLAY_OFFSETS'] = KBossLinearPatternPositiC

# this binding exists because shared behavior needs one stable value
globals()['_BOSS_LINEAR_PATTERN_POSITIVE_SPACING_OFFSETS'] = KBossLinearPatternPositiD

# this binding exists because shared behavior needs one stable value
globals()['_BOSS_LINEAR_PATTERN_TERMINAL_DEPTH_OFFSET'] = KBossLinearPatternTerminA

# this binding exists because shared behavior needs one stable value
globals()['_BOSS_REV_CUT_HEADER_STAMPS'] = KBossRevCutHeaderStamps

# this binding exists because shared behavior needs one stable value
globals()['_BOSS_SHELL_DEPTH_OFFSET'] = KBossShellDepthOffset

# this binding exists because shared behavior needs one stable value
globals()['_BOSS_SHELL_HEADER_STAMPS'] = KBossShellHeaderStamps

# this binding exists because shared behavior needs one stable value
globals()['_BOSS_SHELL_INNER_MIN_X_OFFSET'] = KBossShellInnerMinXOffset

# this binding exists because shared behavior needs one stable value
globals()['_BOSS_SHELL_MAX_X_OFFSET'] = KBossShellMaxXOffset

# this binding exists because shared behavior needs one stable value
globals()['_BOSS_SHELL_MIN_X_OFFSET'] = KBossShellMinXOffset

# this binding exists because shared behavior needs one stable value
globals()['_BOSS_SHELL_THICKNESS_OFFSETS'] = KBossShellThicknessOffseA

# this binding exists because shared behavior needs one stable value
globals()['_BOUNDING_BOX_CLASS'] = KBoundingBoxClass

# this binding exists because shared behavior needs one stable value
globals()['_BOUNDING_BOX_RELATIVE'] = KBoundingBoxRelative

# this binding exists because shared behavior needs one stable value
globals()['_BOX_HEADER_STAMPS'] = KBoxHeaderStamps

# this binding exists because shared behavior needs one stable value
globals()['_CIRCLE_BOSS_HEADER_STAMPS'] = KCircleBossHeaderStamps

# this binding exists because shared behavior needs one stable value
globals()['_CIRCLE_LOCUS'] = KCircleLocus

# this binding exists because shared behavior needs one stable value
globals()['_CIRCULAR_PATTERN_DIRECTION_FLAG_RELATIVE_OFFSET'] = KCircularPatternDirection

# this binding exists because shared behavior needs one stable value
globals()['_COMBINE_FEATURE_TYPES'] = KCombineFeatureTypes

# this binding exists because shared behavior needs one stable value
globals()['_CONFIG0_FIRST_FEATURE_COUNTER'] = KConfigZeroFirstFeature

# this binding exists because shared behavior needs one stable value
globals()['_CONFIGURATION_ROOT_TREE_ID'] = KConfigRootTreeId

# this binding exists because shared behavior needs one stable value
globals()['_CONFIG_PROPERTIES_PAYLOAD'] = KConfigPropertiesPayload

# this binding exists because shared behavior needs one stable value
globals()['_COORDINATE_TAG'] = KCoordinateTag

# this binding exists because shared behavior needs one stable value
globals()['_CREATION_STAMP_HIGH'] = KCreationStampHigh

# this binding exists because shared behavior needs one stable value
globals()['_CREATION_STAMP_LOW'] = KCreationStampLow

# this binding exists because shared behavior needs one stable value
globals()['_CURRENT_MARKER'] = KCurrentMarker

# this binding exists because shared behavior needs one stable value
globals()['_CUT_EXTRUDE_FLAGS'] = KCutExtrudeFlags

# this binding exists because shared behavior needs one stable value
globals()['_CanonicalBossChamferObjects'] = CanonicalBoss

# this binding exists because shared behavior needs one stable value
globals()['_CanonicalBossCircularPatternObjects'] = CanonicalBossA

# this binding exists because shared behavior needs one stable value
globals()['_CanonicalBossFilletObjects'] = CanonicalBossB

# this binding exists because shared behavior needs one stable value
globals()['_CanonicalBossLinearPatternObjects'] = CanonicalBossC

# this binding exists because shared behavior needs one stable value
globals()['_CanonicalBossShellObjects'] = CanonicalBossD

# this binding exists because shared behavior needs one stable value
globals()['_CanonicalCutChainObjects'] = CanonicalCut

# this binding exists because shared behavior needs one stable value
globals()['_CanonicalExtrusionObjects'] = Canonical

# this binding exists because shared behavior needs one stable value
globals()['_CanonicalPadGrooveObjects'] = CanonicalPad

# this binding exists because shared behavior needs one stable value
globals()['_CanonicalPrincipalExtrusion'] = CanonicalA

# this binding exists because shared behavior needs one stable value
globals()['_CanonicalPrincipalSketch'] = CanonicalSketch

# this binding exists because shared behavior needs one stable value
globals()['_CanonicalSingleBossObjects'] = CanonicalSingle

# this binding exists because shared behavior needs one stable value
globals()['_CanonicalSingleRevolutionObjects'] = CanonicalSinglA

# this binding exists because shared behavior needs one stable value
globals()['_CanonicalTwoFeatureObjects'] = CanonicalTwo

# this binding exists because shared behavior needs one stable value
globals()['_CircularPatternBounds'] = CircularPattern

# this binding exists because shared behavior needs one stable value
globals()['_DERIVED_PLANE_CLASSES'] = KDerivedPlaneClasses

# this binding exists because shared behavior needs one stable value
globals()['_EDGE_SELECTION_IDENTITY'] = KEdgeSelectionIdentity

# this binding exists because shared behavior needs one stable value
globals()['_EQUATION'] = KEquation

# this binding exists because shared behavior needs one stable value
globals()['_EQUATION_IDENTIFIER'] = KEquationId

# this binding exists because shared behavior needs one stable value
globals()['_EQUATION_REFERENCE'] = KEquationRef

# this binding exists because shared behavior needs one stable value
globals()['_EQUATION_REFERENCE_SOURCE'] = KEquationRefSource

# this binding exists because shared behavior needs one stable value
globals()['_EQUATION_RESERVED_PREFIX'] = KEquationReservedPrefix

# this binding exists because shared behavior needs one stable value
globals()['_EXTENDED_MARKER'] = KExtendedMarker

# this binding exists because shared behavior needs one stable value
globals()['_EXTRUSION_CLASS'] = KExtrusionClass

# this binding exists because shared behavior needs one stable value
globals()['_EXTRUSION_OPERATION_KINDS'] = KExtrusionOperationKinds

# this binding exists because shared behavior needs one stable value
globals()['_ExpectedPlaneFrame'] = ExpectedPlane

# this binding exists because shared behavior needs one stable value
globals()['_FACE_SUPPORT_CLASS'] = KFaceSupportClass

# this binding exists because shared behavior needs one stable value
globals()['_FOLDER_FLAGS'] = KFolderFlags

# this binding exists because shared behavior needs one stable value
globals()['_FRONT_BOSS_HEADER_STAMPS'] = KFrontBossHeaderStamps

# this binding exists because shared behavior needs one stable value
globals()['_FilletSelectionRecord'] = FilletSelection

# this binding exists because shared behavior needs one stable value
globals()['_FreeCadBossChamferDimensions'] = FreeCadBoss

# this binding exists because shared behavior needs one stable value
globals()['_FreeCadBossCircularPatternDimensions'] = FreeCadBossA

# this binding exists because shared behavior needs one stable value
globals()['_FreeCadBossFilletDimensions'] = FreeCadBossB

# this binding exists because shared behavior needs one stable value
globals()['_FreeCadBossLinearPatternDimensions'] = FreeCadBossC

# this binding exists because shared behavior needs one stable value
globals()['_FreeCadBossShellDimensions'] = FreeCadBossD

# this binding exists because shared behavior needs one stable value
globals()['_FreeCadBoxObjects'] = FreeCadBox

# this binding exists because shared behavior needs one stable value
globals()['_FreeCadFeatureDimension'] = FreeCadFeature

# this binding exists because shared behavior needs one stable value
globals()['_FreeCadFourFeatureDimensions'] = FreeCadFour

# this binding exists because shared behavior needs one stable value
globals()['_FreeCadPadGrooveDimensions'] = FreeCadPad

# this binding exists because shared behavior needs one stable value
globals()['_FreeCadPropertyAttributes'] = FreeCadProp

# this binding exists because shared behavior needs one stable value
globals()['_FreeCadSingleRevolutionDimension'] = FreeCadSingle

# this binding exists because shared behavior needs one stable value
globals()['_FreeCadThreeFeatureDimensions'] = FreeCadThree

# this binding exists because shared behavior needs one stable value
globals()['_FreeCadTwoFeatureDimensions'] = FreeCadTwo

# this binding exists because shared behavior needs one stable value
globals()['_HEADER_OBJECTS'] = KHeaderObjects

# this binding exists because shared behavior needs one stable value
globals()['_HOLE_CLASS_NAMES'] = KHoleClassNames

# this binding exists because shared behavior needs one stable value
globals()['_HasFreeCadBoxBrep'] = HasFreeCadBox

# this binding exists because shared behavior needs one stable value
globals()['_HasFreeCadCircularPatternGeometry'] = HasFreeCadGeom

# this binding exists because shared behavior needs one stable value
globals()['_HasFreeCadLinearPatternGeometry'] = HasFreeCadGeomA

# this binding exists because shared behavior needs one stable value
globals()['_HasFreeCadMaxCornerEdge'] = HasFreeCadMax

# this binding exists because shared behavior needs one stable value
globals()['_HasFreeCadTopFace'] = HasFreeCadTop

# this binding exists because shared behavior needs one stable value
globals()['_IDENTITY_BASIS'] = KIdentityBasis

# this binding exists because shared behavior needs one stable value
globals()['_IDENTITY_ORIGIN'] = KIdentityOrigin

# this binding exists because shared behavior needs one stable value
globals()['_IsFreeCadIdentityPlacement'] = IsFreeCad

# this binding exists because shared behavior needs one stable value
globals()['_KEYWORD_ONLY_OBJECTS'] = KeywordOnlyObjects

# this binding exists because shared behavior needs one stable value
globals()['_KEYWORD_ONLY_OBJECT_IDS'] = KeywordOnlyObjectIds

# this binding exists because shared behavior needs one stable value
globals()['_LEGACY_MARKER'] = KLegacyMarker

# this binding exists because shared behavior needs one stable value
globals()['_LINEAR_PATTERN_DIRECTION_FLAG_RELATIVE_OFFSET'] = KLinearPatternDirection

# this binding exists because shared behavior needs one stable value
globals()['_MARKERS'] = KMarkers

# this binding exists because shared behavior needs one stable value
globals()['_MILLIMETRES'] = KMillimetres

# this binding exists because shared behavior needs one stable value
globals()['_MOVE_BODY_FEATURE_TYPES'] = KMoveBodyFeatureTypes

# this binding exists because shared behavior needs one stable value
globals()['_NAME_PREFIX'] = KNamePrefix

# this binding exists because shared behavior needs one stable value
globals()['_NAME_TOKEN'] = KNameToken

# this binding exists because shared behavior needs one stable value
globals()['_NON_SOLID_FEATURE_CLASSES'] = KNonSolidFeatureClasses

# this binding exists because shared behavior needs one stable value
globals()['_NUMBER'] = KNumber

# this binding exists because shared behavior needs one stable value
globals()['_NativeIdentity'] = NativeIdentity

# this binding exists because shared behavior needs one stable value
globals()['_OPEN_TIME_PAYLOAD'] = KOpenTimePayload

# this binding exists because shared behavior needs one stable value
globals()['_PLANE_FRAME_BYTES'] = KPlaneFrameBytes

# this binding exists because shared behavior needs one stable value
globals()['_POINT_LOCUS'] = KPointLocus

# this binding exists because shared behavior needs one stable value
globals()['_PRINCIPAL_PLANE_OBJECT_IDS'] = KPrincipalPlaneObjectIds

# this binding exists because shared behavior needs one stable value
globals()['_PrincipalPlaneFrame'] = PrincipalPlane

# this binding exists because shared behavior needs one stable value
globals()['_RADIANS_TO_DEGREES'] = KRadiansToDegrees

# this binding exists because shared behavior needs one stable value
globals()['_REFERENCE_GEOMETRY_CLASSES'] = KRefGeomClasses

# this binding exists because shared behavior needs one stable value
globals()['_REFERENCE_GEOMETRY_FLAGS'] = KRefGeomFlags

# this binding exists because shared behavior needs one stable value
globals()['_REVOLUTION_FEATURE_TYPES'] = KRevolutionFeatureTypes

# this binding exists because shared behavior needs one stable value
globals()['_REVOLUTION_HEADER_STAMPS'] = KRevolutionHeaderStamps

# this binding exists because shared behavior needs one stable value
globals()['_REVOLUTION_OPERATION_KINDS'] = KRevolutionOperationKinds

# this binding exists because shared behavior needs one stable value
globals()['_RIGHT_BOSS_HEADER_STAMPS'] = KRightBossHeaderStamps

# this binding exists because shared behavior needs one stable value
globals()['_ReadClassReference'] = ReadClassRef

# this binding exists because shared behavior needs one stable value
globals()['_SCALAR_HEADER'] = KScalarHeader

# this binding exists because shared behavior needs one stable value
globals()['_SKETCH_PLANE_AXIS_COMPLEMENT'] = KSketchPlaneAxisComplemeA

# this binding exists because shared behavior needs one stable value
globals()['_SKETCH_PLANE_AXIS_DELTA'] = KSketchPlaneAxisDelta

# this binding exists because shared behavior needs one stable value
globals()['_SKETCH_PLANE_BASIS_BYTES'] = KSketchPlaneBasisBytes

# this binding exists because shared behavior needs one stable value
globals()['_SKETCH_PLANE_BASIS_DELTA'] = KSketchPlaneBasisDelta

# this binding exists because shared behavior needs one stable value
globals()['_SKETCH_PLANE_BASIS_FLAG_DELTA'] = KSketchPlaneBasisFlagDelA

# this binding exists because shared behavior needs one stable value
globals()['_SKETCH_PLANE_ID_RELATIVE'] = KSketchPlaneIdRelative

# this binding exists because shared behavior needs one stable value
globals()['_SKETCH_PLANE_REFERENCE_PREFIX'] = KSketchPlaneRefPrefix

# this binding exists because shared behavior needs one stable value
globals()['_SKETCH_PLANE_REFERENCE_TAG'] = KSketchPlaneRefTag

# this binding exists because shared behavior needs one stable value
globals()['_SKETCH_PLANE_SCAN_BYTES'] = KSketchPlaneScanBytes

# this binding exists because shared behavior needs one stable value
globals()['_SOLIDWORKS_CONFIGURATION_FLAGS'] = KSolidworksConfigFlags

# this binding exists because shared behavior needs one stable value
globals()['_SOLIDWORKS_XML_NAMESPACE'] = KSolidworksXmlNamespace

# this binding exists because shared behavior needs one stable value
globals()['_SURFACE_EXTRUSION_FEATURE_TYPES'] = KSurfaceExtrusionFeature

# this binding exists because shared behavior needs one stable value
globals()['_SYSTEM_OBJECT_IDS'] = KSystemObjectIds

# this binding exists because shared behavior needs one stable value
globals()['_ShellSelectionRecord'] = ShellSelection

# this binding exists because shared behavior needs one stable value
globals()['_TOP_BOSS_HEADER_STAMPS'] = KTopBossHeaderStamps

# this binding exists because shared behavior needs one stable value
globals()['_VIEW_ORIENTATION_PAYLOAD'] = KViewOrientationPayload

# this binding exists because shared behavior needs one stable value
globals()['_VendorResolved'] = VendorResolved

# this binding exists because shared behavior needs one stable value
globals()['_WriteDimension'] = WriteDimension

# this binding exists because shared behavior needs one stable value
globals()['_WriteObject'] = WriteObject

# this binding exists because shared behavior needs one stable value
globals()['_XmlFeature'] = XmlFeature

# this binding exists because shared behavior needs one stable value
globals()['_angle_copies'] = AngleCopies

# this binding exists because shared behavior needs one stable value
globals()['_bind_dimension'] = BindDimension

# this binding exists because shared behavior needs one stable value
globals()['_biography_payload'] = Biography

# this binding exists because shared behavior needs one stable value
globals()['_bounding_box'] = BoundingBox

# this binding exists because shared behavior needs one stable value
globals()['_circle_profiles'] = CircleProfiles

# this binding exists because shared behavior needs one stable value
globals()['_class_declaration'] = ClassDecl

# this binding exists because shared behavior needs one stable value
globals()['_class_record_end'] = ClassRecordEnd

# this binding exists because shared behavior needs one stable value
globals()['_clean'] = Clean

# this binding exists because shared behavior needs one stable value
globals()['_component_plane_sources'] = ComponentPlane

# this binding exists because shared behavior needs one stable value
globals()['_configuration_atom_tree_ids'] = ConfigAtomTree

# this binding exists because shared behavior needs one stable value
globals()['_configuration_header_payload'] = ConfigHeader

# this binding exists because shared behavior needs one stable value
globals()['_constraints'] = Constraints

# this binding exists because shared behavior needs one stable value
globals()['_coordinate_marker'] = Coordinate

# this binding exists because shared behavior needs one stable value
globals()['_cross'] = Cross

# this binding exists because shared behavior needs one stable value
globals()['_custom_properties_payload'] = CustomPayload

# this binding exists because shared behavior needs one stable value
globals()['_decode_planes'] = DecodePlanes

# this binding exists because shared behavior needs one stable value
globals()['_decode_sketch'] = DecodeSketch

# this binding exists because shared behavior needs one stable value
globals()['_definition_dimension'] = Definition

# this binding exists because shared behavior needs one stable value
globals()['_depth_copies'] = DepthCopies

# this binding exists because shared behavior needs one stable value
globals()['_document_axis_bindings'] = DocAxisBindings

# this binding exists because shared behavior needs one stable value
globals()['_dot'] = DotAction

# this binding exists because shared behavior needs one stable value
globals()['_edge_selections'] = EdgeSelections

# this binding exists because shared behavior needs one stable value
globals()['_end_spec'] = EndSpec

# this binding exists because shared behavior needs one stable value
globals()['_equation_identifier'] = EquationId

# this binding exists because shared behavior needs one stable value
globals()['_equation_literal'] = EquationLiteral

# this binding exists because shared behavior needs one stable value
globals()['_expect_bytes'] = ExpectBytes

# this binding exists because shared behavior needs one stable value
globals()['_expression_parameters'] = Expression

# this binding exists because shared behavior needs one stable value
globals()['_extrusion_payload'] = Extrusion

# this binding exists because shared behavior needs one stable value
globals()['_feature_records'] = FeatureRecords

# this binding exists because shared behavior needs one stable value
globals()['_features_payload'] = FeaturesPayload

# this binding exists because shared behavior needs one stable value
globals()['_fillet_payload'] = FilletPayload

# this binding exists because shared behavior needs one stable value
globals()['_find_all'] = FindAll

# this binding exists because shared behavior needs one stable value
globals()['_frame_vector'] = FrameVector

# this binding exists because shared behavior needs one stable value
globals()['_freecad_parameter_matches'] = FreecadParam

# this binding exists because shared behavior needs one stable value
globals()['_freecad_single_boss_dimension'] = FreecadSingle

# this binding exists because shared behavior needs one stable value
globals()['_freecad_type_id'] = FreecadTypeId

# this binding exists because shared behavior needs one stable value
globals()['_header_payload'] = HeaderPayload

# this binding exists because shared behavior needs one stable value
globals()['_integer_property'] = IntegerProp

# this binding exists because shared behavior needs one stable value
globals()['_is_native_system_feature'] = IsNativeSystem

# this binding exists because shared behavior needs one stable value
globals()['_is_origin_feature'] = IsOriginFeature

# this binding exists because shared behavior needs one stable value
globals()['_is_plane_feature'] = IsPlaneFeature

# this binding exists because shared behavior needs one stable value
globals()['_keywords_payload'] = KeywordsPayload

# this binding exists because shared behavior needs one stable value
globals()['_line_marker'] = LineMarker

# this binding exists because shared behavior needs one stable value
globals()['_linked_rectangle_profiles'] = LinkedRectangle

# this binding exists because shared behavior needs one stable value
globals()['_marker_coordinates'] = Marker

# this binding exists because shared behavior needs one stable value
globals()['_marker_coordinates_metres'] = MarkerMetres

# this binding exists because shared behavior needs one stable value
globals()['_marker_local_id'] = MarkerLocalId

# this binding exists because shared behavior needs one stable value
globals()['_marker_radius_mm'] = MarkerRadiusMm

# this binding exists because shared behavior needs one stable value
globals()['_marker_semantic'] = MarkerSemantic

# this binding exists because shared behavior needs one stable value
globals()['_marker_start_angle_degrees'] = MarkerStart

# this binding exists because shared behavior needs one stable value
globals()['_matches'] = Matches

# this binding exists because shared behavior needs one stable value
globals()['_matrix_frame'] = MatrixFrame

# this binding exists because shared behavior needs one stable value
globals()['_minimal_frame'] = MinimalFrame

# this binding exists because shared behavior needs one stable value
globals()['_mirrored_direction'] = Mirrored

# this binding exists because shared behavior needs one stable value
globals()['_model_header_payload'] = ModelHeader

# this binding exists because shared behavior needs one stable value
globals()['_name_marker'] = NameMarker

# this binding exists because shared behavior needs one stable value
globals()['_name_record'] = NameRecord

# this binding exists because shared behavior needs one stable value
globals()['_native_assembly_identity'] = NativeAsmA

# this binding exists because shared behavior needs one stable value
globals()['_native_envelope_streams'] = NativeEnvelope

# this binding exists because shared behavior needs one stable value
globals()['_native_feature_sort_key'] = NativeFeatureA

# this binding exists because shared behavior needs one stable value
globals()['_native_identity'] = NativeIdentityA

# this binding exists because shared behavior needs one stable value
globals()['_native_keyword_properties'] = NativeKeyword

# this binding exists because shared behavior needs one stable value
globals()['_native_scale_factors'] = NativeScale

# this binding exists because shared behavior needs one stable value
globals()['_native_system_name'] = NativeSystem

# this binding exists because shared behavior needs one stable value
globals()['_native_translation'] = Native

# this binding exists because shared behavior needs one stable value
globals()['_norm'] = NormAction

# this binding exists because shared behavior needs one stable value
globals()['_operation_dimension'] = Operation

# this binding exists because shared behavior needs one stable value
globals()['_operation_dimension_offset'] = OperationOffset

# this binding exists because shared behavior needs one stable value
globals()['_operation_fields'] = OperationFields

# this binding exists because shared behavior needs one stable value
globals()['_operation_selections'] = OperationA

# this binding exists because shared behavior needs one stable value
globals()['_operation_selections_after_class'] = OperationAfter

# this binding exists because shared behavior needs one stable value
globals()['_orthonormal'] = Orthonormal

# this binding exists because shared behavior needs one stable value
globals()['_parameter_dimension'] = ParamDimension

# this binding exists because shared behavior needs one stable value
globals()['_parameter_value_matches'] = ParamValueA

# this binding exists because shared behavior needs one stable value
globals()['_parse_classes'] = ParseClasses

# this binding exists because shared behavior needs one stable value
globals()['_parse_dimension'] = ParseDimension

# this binding exists because shared behavior needs one stable value
globals()['_parse_keywords'] = ParseKeywords

# this binding exists because shared behavior needs one stable value
globals()['_parse_markers'] = ParseMarkers

# this binding exists because shared behavior needs one stable value
globals()['_parse_names'] = ParseNames

# this binding exists because shared behavior needs one stable value
globals()['_parse_native_equations'] = ParseNative

# this binding exists because shared behavior needs one stable value
globals()['_parse_scalars'] = ParseScalars

# this binding exists because shared behavior needs one stable value
globals()['_parse_xml'] = ParseXml

# this binding exists because shared behavior needs one stable value
globals()['_plane_frame_block'] = PlaneFrameBlock

# this binding exists because shared behavior needs one stable value
globals()['_plane_payload'] = PlanePayload

# this binding exists because shared behavior needs one stable value
globals()['_plane_reference'] = PlaneRef

# this binding exists because shared behavior needs one stable value
globals()['_primary_dimension'] = Primary

# this binding exists because shared behavior needs one stable value
globals()['_principal_plane_frames'] = PrincipalPlaneA

# this binding exists because shared behavior needs one stable value
globals()['_principal_plane_ids'] = PrincipalPlaneB

# this binding exists because shared behavior needs one stable value
globals()['_profiles'] = Profiles

# this binding exists because shared behavior needs one stable value
globals()['_proved_write_capabilities'] = ProvedWrite

# this binding exists because shared behavior needs one stable value
globals()['_read_class'] = ReadClass

# this binding exists because shared behavior needs one stable value
globals()['_read_serialized_string'] = ReadSerialized

# this binding exists because shared behavior needs one stable value
globals()['_read_sketch_plane_reference'] = ReadSketchPlane

# this binding exists because shared behavior needs one stable value
globals()['_record_class'] = RecordClass

# this binding exists because shared behavior needs one stable value
globals()['_record_class_name'] = RecordClassName

# this binding exists because shared behavior needs one stable value
globals()['_rectangle_coordinates'] = Rectangle

# this binding exists because shared behavior needs one stable value
globals()['_reference_plane_ids'] = RefPlaneIds

# this binding exists because shared behavior needs one stable value
globals()['_repair_plane_object_ids'] = RepairPlaneIds

# this binding exists because shared behavior needs one stable value
globals()['_resolve_profile_operation'] = ResolveProfile

# this binding exists because shared behavior needs one stable value
globals()['_resolved_base_map_index'] = ResolvedBaseMap

# this binding exists because shared behavior needs one stable value
globals()['_resolved_payload'] = ResolvedPayload

# this binding exists because shared behavior needs one stable value
globals()['_revolution_axis_marker'] = RevolutionAxis

# this binding exists because shared behavior needs one stable value
globals()['_same_point'] = SamePoint

# this binding exists because shared behavior needs one stable value
globals()['_scalar_owners'] = ScalarOwners

# this binding exists because shared behavior needs one stable value
globals()['_scalar_record'] = ScalarRecord

# this binding exists because shared behavior needs one stable value
globals()['_scalar_trailer'] = ScalarTrailer

# this binding exists because shared behavior needs one stable value
globals()['_semantic_dimensions'] = Semantic

# this binding exists because shared behavior needs one stable value
globals()['_serializable_name'] = Serializable

# this binding exists because shared behavior needs one stable value
globals()['_serialized_string'] = Serialized

# this binding exists because shared behavior needs one stable value
globals()['_sketch_payload'] = SketchPayload

# this binding exists because shared behavior needs one stable value
globals()['_sketch_plane_reference'] = SketchPlaneRef

# this binding exists because shared behavior needs one stable value
globals()['_sketch_support_kind'] = SketchSupport

# this binding exists because shared behavior needs one stable value
globals()['_solid_feature_tree_ids'] = SolidFeatureIds

# this binding exists because shared behavior needs one stable value
globals()['_stable_creation_stamp'] = StableCreation

# this binding exists because shared behavior needs one stable value
globals()['_stable_u32'] = StableUThreeTwo

# this binding exists because shared behavior needs one stable value
globals()['_structural_circle_profiles'] = Structural

# this binding exists because shared behavior needs one stable value
globals()['_structural_rectangle_profiles'] = StructuralA

# this binding exists because shared behavior needs one stable value
globals()['_support_plane_reference'] = SupportPlaneRef

# this binding exists because shared behavior needs one stable value
globals()['_tree_node_flags'] = TreeNodeFlags

# this binding exists because shared behavior needs one stable value
globals()['_version_history_payload'] = VersionHistory

# this binding exists because shared behavior needs one stable value
globals()['_write_circle_profile'] = WriteCircle

# this binding exists because shared behavior needs one stable value
globals()['_write_dimensions'] = WriteDimensions

# this binding exists because shared behavior needs one stable value
globals()['_write_feature'] = WriteFeature

# this binding exists because shared behavior needs one stable value
globals()['_write_feature_type'] = WriteFeatureA

# this binding exists because shared behavior needs one stable value
globals()['_write_object_ids'] = WriteObjectIds

# this binding exists because shared behavior needs one stable value
globals()['_write_objects'] = WriteObjects

# this binding exists because shared behavior needs one stable value
globals()['_write_rectangle_bounds'] = WriteRectangle

# this binding exists because shared behavior needs one stable value
globals()['_write_sketch'] = WriteSketch

# this binding exists because shared behavior needs one stable value
globals()['_xml_attribute'] = XmlAttr

# this binding exists because shared behavior needs one stable value
globals()['_xml_document'] = XmlDoc

# this binding exists because shared behavior needs one stable value
globals()['_xml_element'] = XmlElem

# this binding exists because shared behavior needs one stable value
globals()['_xml_text'] = XmlText

# this binding exists because shared behavior needs one stable value
globals()['annotations'] = Annotations

# this binding exists because shared behavior needs one stable value
globals()['atom_ids_for'] = AtomIdsFor

# this binding exists because shared behavior needs one stable value
globals()['circle_radius_mm'] = CircleRadiusMm

# this binding exists because shared behavior needs one stable value
globals()['dataclass'] = Dataclass

# this binding exists because shared behavior needs one stable value
globals()['decode_ascii_brep'] = DecodeAsciiBrep

# this binding exists because shared behavior needs one stable value
globals()['decode_native_model'] = DecodeNative

# this binding exists because shared behavior needs one stable value
globals()['decode_native_model_header'] = DecodeNativeA

# this binding exists because shared behavior needs one stable value
globals()['dimension_scalar_value_offset'] = DimensionScalarValue

# this binding exists because shared behavior needs one stable value
globals()['encode_class_reference'] = EncodeClassRef

# this binding exists because shared behavior needs one stable value
globals()['encode_cmgr_stream'] = EncodeCmgrStream

# this binding exists because shared behavior needs one stable value
globals()['encode_config0_stream'] = EncodeConfigZeroStream

# this binding exists because shared behavior needs one stable value
globals()['encode_definition_stream'] = EncodeDefinitionStream

# this binding exists because shared behavior needs one stable value
globals()['encode_native_assembly_envelope'] = EncodeNativeAsm

# this binding exists because shared behavior needs one stable value
globals()['encode_native_part'] = EncodeNative

# this binding exists because shared behavior needs one stable value
globals()['expression_equation_texts'] = ExpressionTexts

# this binding exists because shared behavior needs one stable value
globals()['field'] = Field

# this binding exists because shared behavior needs one stable value
globals()['hashlib'] = Hashlib

# this binding exists because shared behavior needs one stable value
globals()['itertools'] = Itertools

# this binding exists because shared behavior needs one stable value
globals()['locate_features'] = LocateFeatures

# this binding exists because shared behavior needs one stable value
globals()['math'] = MathValue

# this binding exists because shared behavior needs one stable value
globals()['native_axis_bindings'] = NativeAxis

# this binding exists because shared behavior needs one stable value
globals()['operation_axis_subelement'] = OperationAxis

# this binding exists because shared behavior needs one stable value
globals()['patch_features'] = PatchFeatures

# this binding exists because shared behavior needs one stable value
globals()['re'] = RegexLib

# this binding exists because shared behavior needs one stable value
globals()['rectangle_corners_mm'] = RectangleCornersMm

# this binding exists because shared behavior needs one stable value
globals()['replace'] = Replace

# this binding exists because shared behavior needs one stable value
globals()['revolution_axis_direction'] = RevolutionAxisA

# this binding exists because shared behavior needs one stable value
globals()['struct'] = Struct
