# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from dataclasses import dataclass, field, replace
import hashlib
import itertools
import math
from pathlib import PureWindowsPath
import re
import struct
from types import MappingProxyType
from typing import Any, Mapping, Sequence
import xml.etree.ElementTree as ET

from interchange import (
    BooleanOperation,
    CadDocument,
    Capability,
    ChamferFeature,
    CircleCurve,
    CircleGeometry,
    CircularPatternFeature,
    CylinderSurface,
    ExtrusionEndCondition,
    ExtrusionFeature,
    FeatureKind,
    FeatureStep,
    FilletFeature,
    LinearPatternFeature,
    LineCurve,
    LineGeometry,
    NativeFeatureDefinition,
    Parameter,
    ParameterRole,
    ParameterValue,
    PlaneSurface,
    ShellFeature,
    Sketch,
    SupportPlane,
    ValueKind,
    Vector2,
)

from ...opencascade import decode_ascii_brep

from .archive import encode_class_reference
from .cmgr import (
    CONFIGURATION_MANAGER_STREAM,
    FIRST_ATOM_ID,
    atom_ids_for,
    encode_cmgr_stream,
)
from .config0 import encode_config0_stream
from .config0_box_program import EncodeProgram as EncodeBoxConfigProgram
from .container import SldprtFormatError
from .definition import encode_definition_stream
from .format import (
    ASSEMBLY_SUFFIX,
    CANONICAL_PLANE_FEATURE_TYPE,
    CLASS_MARKER,
    CONFIGURATION_STREAM,
    DIMENSION_SCALAR_HEADERS,
    KIT_RESOLVED_STREAM,
    PART_SUFFIX,
    PLANE_FEATURE_TYPES,
    RESOLVED_FEATURES_STREAM,
    SERIALIZED_STRING_MARKER,
    dimension_scalar_value_offset,
)
from .resolved import (
    ANGLE_COPY_DELTAS,
    DEPTH_COPY_DELTAS,
    DEPTH_COPY_SIGNS,
    FeatureEdit,
    FROM_END_SPEC_CLASS,
    FROM_REVERSE_RELATIVE,
    REVOLUTION_AXIS_SKETCH,
    SKETCH_CHAIN_CLASS,
    circle_radius_mm,
    locate_features,
    patch_features,
    rectangle_corners_mm,
)
from .resolved_program import EncodeProgram
from .resolved_bosscut_program import EncodeProgram as EncodeBossCutProgram
from .resolved_bosscutcut_program import EncodeProgram as EncodeBossCutCutProgram
from .resolved_bosscutcutcut_program import (
    EncodeProgram as EncodeBossCutCutCutProgram,
)
from .resolved_bosscutthrough_program import (
    EncodeProgram as EncodeBossCutThroughProgram,
)
from .resolved_bossboss_program import EncodeProgram as EncodeBossBossProgram
from .resolved_bosschamfer_program import EncodeProgram as EncodeBossChamferProgram
from .resolved_bosscircularpattern_program import (
    EncodeProgram as EncodeBossCircularPatternProgram,
)
from .resolved_bossfillet_program import EncodeProgram as EncodeBossFilletProgram
from .resolved_bosslinearpattern_program import (
    EncodeProgram as EncodeBossLinearPatternProgram,
)
from .resolved_bossrevcut_program import EncodeProgram as EncodeBossRevCutProgram
from .resolved_bossshell_program import EncodeProgram as EncodeBossShellProgram
from .resolved_box_program import EncodeProgram as EncodeBoxProgram
from .resolved_circle_program import EncodeProgram as EncodeCircleProgram
from .resolved_right_program import EncodeProgram as EncodeRightProgram
from .resolved_revolve_program import EncodeProgram as EncodeRevolveProgram
from .resolved_top_program import EncodeProgram as EncodeTopProgram

_RADIANS_TO_DEGREES = 180.0 / math.pi

_CURRENT_MARKER = bytes.fromhex("ffff1f0003")
_LEGACY_MARKER = bytes.fromhex("ffff070001")
_EXTENDED_MARKER = bytes.fromhex("ffff1f0001")
_MARKERS = (_CURRENT_MARKER, _LEGACY_MARKER, _EXTENDED_MARKER)
_COORDINATE_TAG = bytes.fromhex("1e00")
_POINT_LOCUS = bytes.fromhex("04000200")
_CIRCLE_LOCUS = bytes.fromhex("05000100")
_NUMBER = re.compile(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?")
_EDGE_SELECTION_IDENTITY = bytes.fromhex("7dc39425ad49b2547dc39425ad49b254")
_REVOLUTION_FEATURE_TYPES = frozenset(
    {"revolve", "revolution", "cut-revolve", "revcut"}
)
_SURFACE_EXTRUSION_FEATURE_TYPES = frozenset({"surface-extrude", "extrurefsurface"})
_MOVE_BODY_FEATURE_TYPES = frozenset({"body-move/copy", "movecopybody"})
_COMBINE_FEATURE_TYPES = frozenset({"combine", "combinebodies"})
_HOLE_CLASS_NAMES = frozenset({"moSketchHole", "moHoleWzd_c"})
_EQUATION = re.compile(r'^"([^"\r\n]+)"\s*=\s*(\S(?:.*\S)?)$')
_EQUATION_REFERENCE = re.compile(r'"([^"\r\n]+)"')
_EXTRUSION_CLASS = "moExtrusion_c"
_BOUNDING_BOX_CLASS = "moBBoxCenterData_c"
_BOUNDING_BOX_RELATIVE = 28
_FACE_SUPPORT_CLASS = "moFaceRefPlnData_c"
_SKETCH_PLANE_ID_RELATIVE = 209
_SKETCH_PLANE_REFERENCE_PREFIX = bytes.fromhex("50460000")
_SKETCH_PLANE_REFERENCE_TAG = bytes.fromhex("f65a1a69")
_SKETCH_PLANE_AXIS_DELTA = 10
_SKETCH_PLANE_BASIS_FLAG_DELTA = 14
_SKETCH_PLANE_BASIS_DELTA = 15
_SKETCH_PLANE_BASIS_BYTES = 72
_SKETCH_PLANE_AXIS_COMPLEMENT = 5
_SKETCH_PLANE_SCAN_BYTES = 320
_PRINCIPAL_PLANE_OBJECT_IDS = frozenset({2, 3, 4})
_PLANE_FRAME_BYTES = 121
_EQUATION_IDENTIFIER = re.compile(r"[^0-9A-Za-z]+")
_EQUATION_REFERENCE_SOURCE = re.compile(r"^[A-Za-z_<][0-9A-Za-z_<>.:\- ]*$")
_EQUATION_RESERVED_PREFIX = "KitReserved"
_EXTRUSION_OPERATION_KINDS = frozenset({"join", "cut"})
_REVOLUTION_OPERATION_KINDS = frozenset({"revolve_join", "revolve_cut"})
NORMAL_AXIS_SUBELEMENT = "N_Axis"
VERTICAL_AXIS_SUBELEMENT = "V_Axis"
HORIZONTAL_AXIS_SUBELEMENT = "H_Axis"
DIRECTION_AXIS_ROLE = "direction_axis"
_IDENTITY_BASIS = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
_IDENTITY_ORIGIN = (0.0, 0.0, 0.0)
_DERIVED_PLANE_CLASSES = (
    "moRefPlaneMidPlaneGeom_c",
    "moConstraintMidPlaneRefplaneData_c",
    "moLinePtRefPlnData_c",
    "moFaceRefPlnData_c",
    "moFixedRefPlnData_c",
    "moDefaultRefPlnData_c",
)
PLANE_SUPPORT_KIND = "plane"
FACE_SUPPORT_KIND = "face"
DERIVED_SUPPORT_KIND = "derived"
REFERENCE_SUPPORT_SOURCE = "plane-reference"
STREAM_ORDER_SUPPORT_SOURCE = "stream-order"
UNRESOLVED_SUPPORT_SOURCE = "unresolved"
_MILLIMETRES = 1000.0
MARKER_LOCAL_ID_OFFSET_BY_LENGTH = MappingProxyType(
    {
        142: 138,
        146: 138,
        152: 148,
        154: 150,
        156: 148,
        158: 144,
        162: 158,
        166: 158,
        167: 158,
    }
)


@dataclass(frozen=True, slots=True)
class NativeOperand:
    offset: int
    kind_code: int
    entity_index: int


@dataclass(frozen=True, slots=True)
class NativeScalar:
    name: str
    name_offset: int
    value_offset: int
    value: float
    object_id: int | None
    role: str
    operands: tuple[NativeOperand, ...]


@dataclass(frozen=True, slots=True)
class NativeDimension:
    name: str
    value_mm: float
    kind: str
    source_text: str
    native_value: float | None = None
    native_offset: int | None = None
    native_role: str | None = None
    operands: tuple[NativeOperand, ...] = ()


@dataclass(frozen=True, slots=True)
class NativeName:
    offset: int
    text_end: int
    name: str
    object_id: int | None
    class_token: int


@dataclass(frozen=True, slots=True)
class NativeClass:
    offset: int
    name: str


@dataclass(frozen=True, slots=True)
class NativeMarker:
    offset: int
    length: int
    prefix: str
    native_kind: int
    locus: str
    profile_role: int
    state: float | None
    object_index: int | None
    local_id: int | None
    coordinates_mm: tuple[float, float] | None
    endpoint_indices: tuple[int, int] | None
    construction: bool
    semantic: str
    data: bytes = b""
    coordinates_metres: tuple[float, float] | None = None


@dataclass(frozen=True, slots=True)
class NativeConstraint:
    id: str
    kind: str
    references: tuple[str, ...]
    parameter: str | None
    value: float | None
    native_offset: int | None
    native_code: int | None


@dataclass(frozen=True, slots=True)
class NativeProfile:
    kind: str
    coordinates: tuple[float, ...]
    marker_offsets: tuple[int, ...]
    parameter_name: str | None = None
    dimension_kind: str | None = None
    start_angle_degrees: float | None = None


@dataclass(frozen=True, slots=True)
class NativeSketchPlane:
    offset: int
    plane_object_id: int
    axis_code: int
    u_axis: tuple[float, float, float]
    v_axis: tuple[float, float, float]
    normal: tuple[float, float, float]
    basis_offset: int | None


@dataclass(frozen=True, slots=True)
class NativeDepthCopy:
    offset: int
    sign: int
    value_mm: float


@dataclass(frozen=True, slots=True)
class NativeBoundingBox:
    offset: int
    center_mm: tuple[float, float, float]
    diameter_mm: float


@dataclass(frozen=True, slots=True)
class NativePlane:
    object_id: int
    name: str
    origin_mm: tuple[float, float, float]
    normal: tuple[float, float, float]
    u_axis: tuple[float, float, float]
    v_axis: tuple[float, float, float]
    native_offset: int | None
    native_length: int | None
    principal: bool = False
    reference_ids: tuple[int, ...] = ()
    native_stream: str = RESOLVED_FEATURES_STREAM


@dataclass(frozen=True, slots=True)
class NativeSketch:
    object_id: int
    name: str
    support_plane_id: int
    native_offset: int
    native_end: int
    markers: tuple[NativeMarker, ...]
    profiles: tuple[NativeProfile, ...]
    dimensions: tuple[NativeDimension, ...]
    constraints: tuple[NativeConstraint, ...]
    native_stream: str = RESOLVED_FEATURES_STREAM
    support_kind: str = PLANE_SUPPORT_KIND
    support_plane: NativeSketchPlane | None = None
    support_source: str = REFERENCE_SUPPORT_SOURCE
    unframed_support_plane_id: int | None = None


@dataclass(frozen=True, slots=True)
class NativeEndSpec:
    offset: int
    termination_code: int
    direction_code: int
    second_direction_code: int
    mirrored_direction_offset: int | None = None
    mirrored_direction_code: int | None = None


@dataclass(frozen=True, slots=True)
class NativeOperation:
    object_id: int
    name: str
    kind: str
    profile_id: int | None
    dependencies: tuple[int, ...]
    native_offset: int
    native_end: int
    length_mm: float | None
    radius_mm: float | None
    family_code: int | None
    operation_code: int | None
    schema_code: int | None
    direction_code: int | None
    termination_code: int | None
    selection_offsets: tuple[int, ...]
    selected_local_ids: tuple[int, ...]
    angle_degrees: float | None = None
    diameter_mm: float | None = None
    second_length_mm: float | None = None
    axis_marker_offset: int | None = None
    selection_kind: str = "edge"
    mode: str | None = None
    native_stream: str = RESOLVED_FEATURES_STREAM
    selection_references: tuple[tuple[int, int], ...] = ()
    translation_mm: tuple[float, float, float] | None = None
    scale_factors: tuple[float, float, float] | None = None
    depth_copies: tuple[NativeDepthCopy, ...] = ()
    mirrored_direction_offset: int | None = None
    mirrored_direction_code: int | None = None
    axis_source_kind: str | None = None
    axis_source_id: int | None = None
    axis_source_offset: int | None = None
    end_spec_offset: int | None = None
    angle_offset: int | None = None
    angle_copies: tuple[NativeDepthCopy, ...] = ()
    instance_count: int | None = None
    spacing_mm: float | None = None


@dataclass(frozen=True, slots=True)
class NativeFeature:
    object_id: int
    name: str
    kind: str
    xml_tag: str
    native_offset: int | None
    native_end: int | None
    properties: dict[str, str]
    dimensions: tuple[NativeDimension, ...]
    data: bytes = b""
    class_name: str = ""
    native_stream: str = RESOLVED_FEATURES_STREAM


@dataclass(frozen=True, slots=True)
class NativeConfiguration:
    object_id: int
    name: str
    configuration_id: int
    properties: dict[str, str]


@dataclass(frozen=True, slots=True)
class NativeEquation:
    source: str
    lhs: str
    rhs: str
    references: tuple[str, ...]
    native_offset: int
    native_length: int
    configuration_id: int
    native_stream: str


@dataclass(frozen=True, slots=True)
class NativeModel:
    configurations: tuple[NativeConfiguration, ...]
    features: tuple[NativeFeature, ...]
    planes: tuple[NativePlane, ...]
    sketches: tuple[NativeSketch, ...]
    operations: tuple[NativeOperation, ...]
    names: tuple[NativeName, ...]
    classes: tuple[NativeClass, ...]
    scalars: tuple[NativeScalar, ...]
    diagnostics: tuple[str, ...] = field(default_factory=tuple)
    equations: tuple[NativeEquation, ...] = field(default_factory=tuple)
    active_configuration_id: int | None = None
    bounding_box: NativeBoundingBox | None = None


@dataclass(frozen=True, slots=True)
class NativePartStreams:
    keywords: bytes
    features: bytes
    resolved_features: bytes
    kit_resolved_features: bytes | None
    configuration_lanes: tuple[tuple[int, bytes], ...]
    native_capabilities: frozenset[Capability]
    mixed_capabilities: frozenset[Capability]
    object_ids: Mapping[str, int]
    envelope_streams: Mapping[str, bytes]
    partition: bytes | None
    application_usable: bool
    vendor_loadable: bool
    donor_notes: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class NativeModelHeader:
    user_name: str
    reference_name: str
    configuration_name: str
    document_path: str
    objects: tuple[tuple[int, str], ...]


@dataclass(frozen=True, slots=True)
class NativeAssemblyEnvelope:
    streams: Mapping[str, bytes]
    configuration_name: str
    reference_name: str
    document_path: str
    header_objects: tuple[tuple[int, str], ...]
    omitted_object_names: tuple[str, ...]
    envelope_complete: bool


@dataclass(slots=True)
class _XmlFeature:
    object_id: int
    name: str
    kind: str
    xml_tag: str
    properties: dict[str, str]
    dimensions: list[NativeDimension]


@dataclass(frozen=True, slots=True)
class _WriteDimension:
    name: str
    value_mm: float
    text: str
    role: ParameterRole


@dataclass(frozen=True, slots=True)
class _WriteObject:
    source_id: str
    object_id: int
    name: str
    xml_tag: str
    kind: str
    class_name: str
    properties: tuple[tuple[str, str], ...] = ()
    dimensions: tuple[_WriteDimension, ...] = ()
    payload: bytes = b""


@dataclass(frozen=True, slots=True)
class _NativeIdentity:
    creation_stamp: int
    last_modified_stamp: int
    baseline_stamp: int
    header_stamp: int
    configuration_flags: int
    reference_name: str


# resolved bytes and header identities must enter the container as one coupled unit
@dataclass(frozen=True, slots=True)
class _VendorResolved:
    payload: bytes
    header_stamps: tuple[tuple[int, ...], ...]
    annotation_view_count: int = 1
    terminal_parent_tree_id: int | None = None
    HeaderBounds: tuple[float, ...] | None = None
    HeaderCreation: int | None = None
    cmgr_parent_tree_id: int | None = None
    annotation_view_variant: str = "default"
    Config0Payload: bytes | None = None


_BASE_OBJECTS = (
    (8, "Comments", "Comments", "moCommentsFolder_c"),
    (23, "Favorites", "Favorites", "moFavoriteFolder_c"),
    (24, "History", "History", "moHistoryFolder_c"),
    (25, "Selection Sets", "Selection Sets", "moSelectionSetFolder_c"),
    (22, "Sensors", "Sensors", "moSensorFolder_c"),
    (7, "Design Binder", "Design Binder", "moDocsFolder_c"),
    (1, "Annotations", "Annotations", "moDetailCabinet_c"),
    (17, "Notes", "Notes", "moNotesAreaFtrFolder_c"),
    (18, "Notes1___EndTag___", "Notes", "moNotesAreaFtrFolder_c"),
    (10, "Surface Bodies", "Surface Bodies", "moSurfaceBodyFolder_c"),
    (9, "Solid Bodies", "Solid Bodies", "moSolidBodyFolder_c"),
    (21, "Markups", "Markups", "moInkMarkupFolder_c"),
    (16, "Equations", "Equations", "moEqnFolder_c"),
    (
        11,
        "Material <not specified>",
        "SOLIDWORKS Materials",
        "moMaterialFolder_c",
    ),
    (2, "Front Plane", "Plane", "moRefPlane_c"),
    (3, "Top Plane", "Plane", "moRefPlane_c"),
    (4, "Right Plane", "Plane", "moRefPlane_c"),
    (5, "Origin", "Origin", "moOriginProfileFeature_c"),
)
_KEYWORD_ONLY_OBJECTS = (
    (6, "Lights and Cameras", "Lights and Cameras"),
    (12, "Ambient", "Ambient"),
    (13, "Directional1", "Directional"),
    (14, "Directional2", "Directional"),
    (15, "Directional3", "Directional"),
    (19, "", "Exploded Views"),
)
_KEYWORD_ONLY_OBJECT_IDS = frozenset(item[0] for item in _KEYWORD_ONLY_OBJECTS)
_SYSTEM_OBJECT_IDS = frozenset(range(1, 26))
_NAME_TOKEN = 0x8004
_NAME_PREFIX = struct.pack("<H", _NAME_TOKEN) + b"\xff\xfe\xff"
_FOLDER_FLAGS = 0x40000000
_REFERENCE_GEOMETRY_FLAGS = 0xC0000000
_BOSS_EXTRUDE_FLAGS = 0x40000140
_CUT_EXTRUDE_FLAGS = 0x400201CA
_REFERENCE_GEOMETRY_CLASSES = frozenset({"moRefPlane_c", "moOriginProfileFeature_c"})
_CONFIG0_FIRST_FEATURE_COUNTER = 109
_SCALAR_HEADER = DIMENSION_SCALAR_HEADERS[0]
_SOLIDWORKS_XML_NAMESPACE = "http://www.solidworks.com/sw2003/schema"
_SOLIDWORKS_CONFIGURATION_FLAGS = -2143288960
_CREATION_STAMP_LOW = 1577836800
_CREATION_STAMP_HIGH = 1893456000
# the front rectangular boss program carries these feature-action identities
_FRONT_BOSS_HEADER_STAMPS = ((1785796991, 1785796991), (1785796991,))
# the dimensioned box program carries distinct sketch modification identities
_BOX_HEADER_STAMPS = ((1786460234, 1786460235), (1786460235,))
# the top-plane boss program carries distinct feature-action identities
_TOP_BOSS_HEADER_STAMPS = ((1785840649, 1785840649), (1785840649,))
# the right-plane boss program carries distinct feature-action identities
_RIGHT_BOSS_HEADER_STAMPS = ((1785840740, 1785840741), (1785840741,))
# the circular boss program carries these feature-action identities
_CIRCLE_BOSS_HEADER_STAMPS = ((1786472138, 1786472138), (1786472138,))
# the blind boss-cut program carries four coupled feature-action identities
_BOSS_CUT_HEADER_STAMPS = (
    (1785839433, 1785839433),
    (1785839434,),
    (1785839434, 1785839435),
    (1785839435,),
)
# the through-all boss-cut program carries its own action identities
_BOSS_CUT_THROUGH_HEADER_STAMPS = (
    (1785797023, 1785797023),
    (1785797023,),
    (1785797024, 1785797024),
    (1785797025,),
)
# the two-boss program carries four coupled feature-action identities
_BOSS_BOSS_HEADER_STAMPS = (
    (1786440431, 1786440431),
    (1786440431,),
    (1786440432, 1786440432),
    (1786440432,),
)
# the boss-fillet program carries one sketch action and two feature actions
_BOSS_FILLET_HEADER_STAMPS = (
    (1786443440, 1786443440),
    (1786443440,),
    (1786443440,),
)
# the six traced radius fields jointly define the uniform native fillet radius
_BOSS_FILLET_RADIUS_OFFSETS = (12721, 13001, 13235, 13259, 13739, 14614)
# the selected max-X/max-Y edge stores three radius-trimmed X coordinates
_BOSS_FILLET_MAX_X_OFFSETS = (12753, 12777, 12902)
# the selected max-X/max-Y edge stores two positive radius-trimmed Y coordinates
_BOSS_FILLET_MAX_Y_OFFSETS = (12761, 12785)
# the paired edge-frame coordinate stores the negated radius-trimmed Y value
_BOSS_FILLET_NEGATIVE_Y_OFFSET = 12910
# the boss-chamfer program carries one sketch action and two feature actions
_BOSS_CHAMFER_HEADER_STAMPS = (
    (1786446942, 1786446942),
    (1786446942,),
    (1786446942,),
)
# the six recovered distance fields jointly define the equal-distance chamfer
_BOSS_CHAMFER_DISTANCE_OFFSETS = (12629, 12947, 13027, 13051, 13189, 13213)
# terminal dimension witnesses track the positive distance-trimmed maximum Y
_BOSS_CHAMFER_MAX_Y_OFFSETS = (12669, 14519)
# paired witness transforms store the negated distance-trimmed maximum Y
_BOSS_CHAMFER_NEGATIVE_Y_OFFSETS = (12866, 14620)
# the angular display witness stores the chamfer distance with reversed sign
_BOSS_CHAMFER_NEGATIVE_DISTANCE_OFFSET = 14495
# the boss-shell program carries one sketch action and two feature actions
_BOSS_SHELL_HEADER_STAMPS = (
    (1786448316, 1786448316),
    (1786448316,),
    (1786448316,),
)
# the six recovered distance fields jointly define the inward wall thickness
_BOSS_SHELL_THICKNESS_OFFSETS = (12498, 12816, 12888, 12912, 13058, 13082)
# the shell dimension witness begins at the source pad's minimum X coordinate
_BOSS_SHELL_MIN_X_OFFSET = 12530
# the inward wall witness advances from minimum X by the requested thickness
_BOSS_SHELL_INNER_MIN_X_OFFSET = 12554
# the opposite dimension witness remains on the source pad's maximum X coordinate
_BOSS_SHELL_MAX_X_OFFSET = 12727
# the face-selection witness remains on the open top of the source pad
_BOSS_SHELL_DEPTH_OFFSET = 12212
# the boss-linear-pattern program carries one sketch action and two feature actions
_BOSS_LINEAR_PATTERN_HEADER_STAMPS = (
    (1786449611, 1786449611),
    (1786449611,),
    (1786449611,),
)
# three count fields preserve the editable integer occurrence count
_BOSS_LINEAR_PATTERN_COUNT_OFFSET = 12962
_BOSS_LINEAR_PATTERN_COUNT_DOUBLE_OFFSETS = (13336, 13360)
# six signed distance fields preserve the editable instance spacing
_BOSS_LINEAR_PATTERN_POSITIVE_SPACING_OFFSETS = (
    14463,
    14853,
    14877,
    15023,
    15047,
)
# the direction witnesses carry the pitch along the selected sketch-normal edge
_BOSS_LINEAR_PATTERN_DIRECTION_DISTANCE_OFFSETS = (12656, 14535)
# the native flip flag converts FreeCAD's positive sketch normal to SOLIDWORKS +Z
_BOSS_LINEAR_PATTERN_DIRECTION_FLAG_OFFSET = 18577
# the flip flag occupies a stable field in the moLPattern record itself
_LINEAR_PATTERN_DIRECTION_FLAG_RELATIVE_OFFSET = 7264
# direction-vector and transform fields preserve the flipped native annotation frame
_BOSS_LINEAR_PATTERN_NEGATIVE_ZERO_OFFSETS = (14569, 14577, 14620, 14644, 14692)
# two direction witnesses encode the positive selected-axis unit component
_BOSS_LINEAR_PATTERN_POSITIVE_AXIS_OFFSETS = (14585, 14668)
# paired 45-degree transform witnesses rotate the annotation into the flipped frame
_BOSS_LINEAR_PATTERN_NEGATIVE_DIAGONAL_OFFSET = 14636
_BOSS_LINEAR_PATTERN_POSITIVE_DIAGONAL_OFFSET = 14660
# the terminal extent is the seed depth plus every inter-instance pitch
_BOSS_LINEAR_PATTERN_TERMINAL_DEPTH_OFFSET = 18993
# the count witness expands the pattern's display range by one millimetre per instance
_BOSS_LINEAR_PATTERN_COUNT_DISPLAY_OFFSET = 11398
# display witnesses remain coupled to the generated body's terminal extent
_BOSS_LINEAR_PATTERN_NEGATIVE_EXTENT_OFFSET = 4187
_BOSS_LINEAR_PATTERN_POSITIVE_DISPLAY_OFFSETS = (4381, 4935)
_BOSS_LINEAR_PATTERN_NEGATIVE_DISPLAY_OFFSETS = (4389, 4943)
_BOSS_LINEAR_PATTERN_CENTER_DISPLAY_OFFSETS = (4428, 4998)
_BOSS_LINEAR_PATTERN_PAD_DISPLAY_OFFSET = 4757
# the boss-circular-pattern program carries one sketch action and two feature actions
_BOSS_CIRCULAR_PATTERN_HEADER_STAMPS = (
    (1786452328, 1786452328),
    (1786452328,),
    (1786452328,),
)
# three occurrence fields preserve the editable integer pattern count
_BOSS_CIRCULAR_PATTERN_COUNT_OFFSET = 13433
_BOSS_CIRCULAR_PATTERN_COUNT_DOUBLE_OFFSETS = (13807, 13831)
# three radian fields preserve the editable circular angular span
_BOSS_CIRCULAR_PATTERN_ANGLE_OFFSETS = (18584, 19026, 19050)
# FreeCAD's positive sketch-normal axis requires the native reversed direction
_BOSS_CIRCULAR_PATTERN_DIRECTION_FLAG_OFFSET = 17876
# the direction flag occupies a stable field in the moCirPattern record itself
_CIRCULAR_PATTERN_DIRECTION_FLAG_RELATIVE_OFFSET = 6096
# the boss-groove program carries four coupled feature-action identities
_BOSS_REV_CUT_HEADER_STAMPS = (
    (1785927829, 1785927829),
    (1785927829,),
    (1785927830, 1785927830),
    (1785927830,),
)
# the two-pocket program carries six coupled feature-action identities
_BOSS_CUT_CUT_HEADER_STAMPS = (
    (1785839606, 1785839607),
    (1785839607,),
    (1785839608, 1785839609),
    (1785839609,),
    (1785839609, 1785839610),
    (1785839610,),
)
# the three-pocket program carries eight coupled feature-action identities
_BOSS_CUT_CUT_CUT_HEADER_STAMPS = (
    (1785843343, 1785843343),
    (1785843343,),
    (1785843344, 1785843344),
    (1785843345,),
    (1785843345, 1785843345),
    (1785843345,),
    (1785843346, 1785843346),
    (1785843346,),
)
# the revolved-boss program requires its header actions to share these identities
_REVOLUTION_HEADER_STAMPS = ((1785797027, 1785797028), (1785797028,))
VENDOR_UNLOADABLE_NOTES = (
    "Contents/Config-0-ResolvedFeatures is the SOLIDWORKS feature tree authority and "
    "the current source graph is outside the recovered native rectangle pad family",
)
_NON_SOLID_FEATURE_CLASSES = frozenset({"moRefPlane_c", "moProfileFeature_c"})
_CONFIGURATION_ROOT_TREE_ID = 0
_HEADER_OBJECTS = (
    (1, "Annotations", False),
    (2, "Front Plane", True),
    (3, "Top Plane", True),
    (4, "Right Plane", True),
    (5, "Origin", True),
    (6, "Lights and Cameras", False),
    (7, "Design Binder", False),
    (8, "Comments", False),
    (9, "Solid Bodies", False),
    (10, "Surface Bodies", False),
    (11, "Material <not specified>", True),
    (12, "Ambient", False),
    (13, "Directional1", False),
    (14, "Directional2", False),
    (15, "Directional3", False),
    (16, "Equations", False),
    (17, "Notes", False),
    (18, "Notes1___EndTag___", False),
    (21, "Markups", False),
    (22, "Sensors", False),
    (23, "Favorites", False),
    (24, "History", False),
    (25, "Selection Sets", False),
)
_ASSEMBLY_HEADER_OBJECTS = (
    (2, "Annotations", False),
    (3, "Front Plane", True),
    (4, "Top Plane", True),
    (5, "Right Plane", True),
    (6, "Origin", True),
    (7, "Lights, Cameras and Scene", False),
    (8, "Design Binder", False),
    (9, "Comments", False),
    (10, "Live Section Planes", False),
    (11, "Mates", False),
    (12, "Ambient", False),
    (13, "Directional1", False),
    (14, "Directional2", False),
    (15, "Directional3", False),
    (16, "Equations", False),
    (17, "Notes", False),
    (18, "Notes1___EndTag___", False),
    (19, "Markups", False),
    (20, "Sensors", False),
    (21, "Favorites", False),
    (22, "History", False),
    (23, "Selection Sets", False),
)
_ASSEMBLY_CONFIGURATION_FLAGS = -2147221376
_ASSEMBLY_REFERENCE_NAME = "Assem1"
_ASSEMBLY_VERSION_PREFIX = "_MO_VERSION_18000"
_ASSEMBLY_PROPERTY_CONTAINER_CLASS = "moAssyFilePropContainer_c"
_ASSEMBLY_ATTACHMENT_STREAM = "Contents/Config-0-Attachment"
_ASSEMBLY_VISUAL_DATA_STREAM = f"{_ASSEMBLY_VERSION_PREFIX}/AssyVisualData"
_ASSEMBLY_TABLES_STREAM = "swXmlContents/Tables"
_ASSEMBLY_VIEW_ORIENTATION_STREAM = "Contents/View Orientation Data"
_ASSEMBLY_OPEN_TIME_STREAM = "docProps/OpenTime.xml"
_ASSEMBLY_CUTLIST_STREAM = "docProps/Config-0-Cutlist-Properties.xml"
_ASSEMBLY_CONFIG_PROPERTIES_STREAM = "docProps/Config-0-Properties.xml"
_VIEW_ORIENTATION_PAYLOAD = b'<?xml version="1.0" encoding="UTF-8"?>\n<VIEWS/>\n'
_OPEN_TIME_PAYLOAD = (
    b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\r\n'
    b'<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006'
    b'/SolidworksOpenTime" xmlns:vt="http://schemas.openxmlformats.org/office'
    b'Document/2006/docPropsVTypes"><count xmlns="">0</count>'
    b'<TotalFileOpenTime xmlns="">-1</TotalFileOpenTime>'
    b'<LWcount xmlns="">0</LWcount>'
    b'<LWTotalFileOpenTime xmlns="">-1</LWTotalFileOpenTime></Properties>\r\n'
)
_CONFIG_PROPERTIES_PAYLOAD = (
    b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\r\n'
    b'<ConfigProperties xmlns="http://www.solidworks.com/config-properties" '
    b'xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docProps'
    b'VTypes"><propertySection xmlns="" name="DocumentSummaryInformation" '
    b'fmtid="{D5CDD502-2E9C-101B-9397-08002B2CF9AE}">'
    b'<propertyNameDictionaryElement name="" pid="0">'
    b"</propertyNameDictionaryElement></propertySection>"
    b'<propertySection xmlns="" name="UserDefinedProperties" '
    b'fmtid="{D5CDD505-2E9C-101B-9397-08002B2CF9AE}">'
    b'<property name="" pid="1"><vt:i2>65001</vt:i2></property>'
    b'<propertyNameDictionaryElement name="" pid="0">'
    b"</propertyNameDictionaryElement></propertySection></ConfigProperties>\r\n"
)


# a cheap exact preflight avoids serializing unsupported corpus documents
def HasVendorPartEncoding(DocumentData: CadDocument) -> bool:
    ObjectIds = _write_object_ids(DocumentData)
    SourceObjects = _write_objects(DocumentData, ObjectIds)
    if not SourceObjects:
        return False
    AuthoredObjects = _CanonicalExtrusionObjects(
        SourceObjects,
        ObjectIds,
        DocumentData,
    )
    return BuildVendorTree(AuthoredObjects) is not None


# this serializes a self contained native solidworks part
def encode_native_part(document: CadDocument, model_name: str) -> NativePartStreams:
    object_ids = _write_object_ids(document)
    SourceAuthored = _write_objects(document, object_ids)
    if not SourceAuthored and document.brep is not None:
        SourceAuthored = (
            _WriteObject(
                "brep:imported",
                26,
                "Imported1",
                "Feature",
                "Imported",
                "moBaseBody_c",
            ),
        )
    authored = _CanonicalExtrusionObjects(
        SourceAuthored,
        object_ids,
        document,
    )
    identity = _native_identity(document, model_name)
    system_features = {
        int(feature.attributes["native_object_id"]): feature
        for feature in document.feature_timeline
        if _is_native_system_feature(feature)
    }
    base = tuple(
        _WriteObject(
            f"base:{object_id}",
            object_id,
            _native_system_name(system_features.get(object_id), name),
            "Sketch" if object_id == 5 else "Feature",
            kind,
            class_name,
        )
        for object_id, name, kind, class_name in _BASE_OBJECTS
    )
    keyword_only = tuple(
        _WriteObject(
            f"base:{object_id}",
            object_id,
            _native_system_name(system_features.get(object_id), name),
            "Feature",
            kind,
            "",
        )
        for object_id, name, kind in _KEYWORD_ONLY_OBJECTS
    )
    objects = (*base, *authored)
    VendorData = BuildVendorTree(authored)
    VendorResolved = VendorData.payload if VendorData is not None else None
    SourceKeywords = _keywords_payload(
        document,
        model_name,
        (*base, *SourceAuthored, *keyword_only),
        object_ids,
        identity,
    )
    ProofKeywords = _keywords_payload(
        document,
        model_name,
        (*objects, *keyword_only),
        object_ids,
        identity,
    )
    keywords = ProofKeywords if VendorResolved is not None else SourceKeywords
    features = _features_payload(document, model_name, object_ids, identity)
    KitResolved = _resolved_payload(objects)
    resolved = VendorResolved if VendorResolved is not None else KitResolved
    HeaderFeatureObjects = (
        tuple(
            (ItemData.object_id, ItemData.name, ItemData.kind == "Sketch")
            for ItemData in authored
        )
        if VendorResolved is not None
        else ()
    )
    HeaderFeatureStamps = (
        MappingProxyType(
            {
                ItemData.object_id: StampData
                for ItemData, StampData in zip(
                    authored,
                    VendorData.header_stamps,
                    strict=True,
                )
            }
        )
        if VendorData is not None
        else MappingProxyType({})
    )
    EnvelopeStreams = dict(
        _native_envelope_streams(
            document,
            model_name,
            identity,
            _solid_feature_tree_ids(authored),
            HeaderFeatureObjects,
            HeaderFeatureStamps,
            VendorData.annotation_view_count if VendorData is not None else 1,
            VendorData.terminal_parent_tree_id if VendorData is not None else None,
            VendorData.HeaderBounds if VendorData is not None else None,
            VendorData.HeaderCreation if VendorData is not None else None,
            VendorData.cmgr_parent_tree_id if VendorData is not None else None,
            VendorData.annotation_view_variant if VendorData is not None else "default",
        )
    )
    if VendorResolved is not None:
        EnvelopeStreams[RESOLVED_FEATURES_STREAM] = VendorResolved
    if VendorData is not None and VendorData.Config0Payload is not None:
        EnvelopeStreams[CONFIGURATION_STREAM] = VendorData.Config0Payload
    configuration_data = EnvelopeStreams.get(CONFIGURATION_STREAM, b"")
    parsed = decode_native_model(
        ProofKeywords,
        resolved,
        configuration_data,
        resolved_stream=(
            RESOLVED_FEATURES_STREAM
            if VendorResolved is not None
            else KIT_RESOLVED_STREAM
        ),
    )
    capabilities = _proved_write_capabilities(document, authored, parsed, object_ids)
    mixed_capabilities: frozenset[Capability] = frozenset()
    partition: bytes | None = None
    vendor_loadable = VendorResolved is not None
    application_usable = vendor_loadable
    return NativePartStreams(
        keywords,
        features,
        resolved,
        None if VendorResolved is not None else KitResolved,
        ((0, VendorResolved),) if VendorResolved is not None else (),
        capabilities,
        mixed_capabilities,
        MappingProxyType(object_ids),
        MappingProxyType(EnvelopeStreams),
        partition,
        application_usable,
        vendor_loadable,
        () if VendorResolved is not None else VENDOR_UNLOADABLE_NOTES,
    )


# dimensioned circles specialize the closed typed config program with exact cache semantics
def EncodeCircCfg(
    CenterX: float,
    CenterY: float,
    RadiusValue: float,
    DepthValue: float,
) -> bytes:
    if (
        not all(
            math.isfinite(ItemValue)
            for ItemValue in (CenterX, CenterY, RadiusValue, DepthValue)
        )
        or min(RadiusValue, DepthValue) <= 0.0
    ):
        raise SldprtFormatError(
            "circle configuration requires finite positive radius and depth"
        )
    CenterXMetres = CenterX / _MILLIMETRES
    CenterYMetres = CenterY / _MILLIMETRES
    RadiusMetres = RadiusValue / _MILLIMETRES
    DepthMetres = DepthValue / _MILLIMETRES
    CenterZMetres = DepthMetres / 2.0
    return EncodeBoxConfigProgram(
        {
            70: 33056,
            222: 4,
            824: RadiusValue,
            2316: 1771999328,
            2320: 31271357,
            2376: CenterXMetres,
            2384: CenterYMetres,
            2392: CenterZMetres,
            2400: CenterXMetres + RadiusMetres,
            2408: CenterYMetres + RadiusMetres,
            2416: DepthMetres,
            2424: CenterXMetres - RadiusMetres,
            2432: CenterYMetres - RadiusMetres,
            2448: math.sqrt(RadiusMetres**2 * 2.0 + CenterZMetres**2),
            2596: 103,
            2914: 33,
            2918: 33,
            2942: 600,
            2950: 600,
            4219: 0.0,
            21879: 115,
            21888: 18000,
            21892: 2025268,
            21964: 31271357,
            21968: 1770659972,
            24057: 10,
            24095: 0,
            24220: 31271357,
            24224: 1710964613,
        }
    )


# recovered native programs select only feature histories proved editable in SOLIDWORKS
def BuildVendorTree(AuthoredObjs: tuple[_WriteObject, ...]) -> _VendorResolved | None:
    if len(AuthoredObjs) == 8:
        return BuildFourFeatureVendorTree(AuthoredObjs)
    if len(AuthoredObjs) == 6:
        return BuildThreeFeatureVendorTree(AuthoredObjs)
    if len(AuthoredObjs) == 4:
        if AuthoredObjs[3].class_name == "moRevolution_c":
            return BuildPadGrooveVendorTree(AuthoredObjs)
        return BuildTwoFeatureVendorTree(AuthoredObjs)
    if len(AuthoredObjs) == 3 and AuthoredObjs[2].class_name == "Fillet_c":
        return BuildBossFilletVendorTree(AuthoredObjs)
    if len(AuthoredObjs) == 3 and AuthoredObjs[2].class_name == "Chamfer_c":
        return BuildBossChamferVendorTree(AuthoredObjs)
    if len(AuthoredObjs) == 3 and AuthoredObjs[2].class_name == "moShell_c":
        return BuildBossShellVendorTree(AuthoredObjs)
    if len(AuthoredObjs) == 3 and AuthoredObjs[2].class_name == "moLPattern_c":
        return BuildBossLinearPatternVendorTree(AuthoredObjs)
    if len(AuthoredObjs) == 3 and AuthoredObjs[2].class_name == "moCirPattern_c":
        return BuildBossCircularPatternVendorTree(AuthoredObjs)
    if len(AuthoredObjs) != 2:
        return None
    SketchObject, PadObject = AuthoredObjs
    if PadObject.class_name == "moRevolution_c":
        return BuildSingleRevolutionVendorTree(AuthoredObjs)
    PlaneObjectId = (
        struct.unpack_from("<I", SketchObject.payload)[0]
        if len(SketchObject.payload) >= 4
        else 0
    )
    BoundsValue = _write_rectangle_bounds(SketchObject)
    CircleValue = _write_circle_profile(SketchObject)
    EndCodes = ExtrusionEditCodes(PadObject.payload)
    if (
        SketchObject.class_name != "moProfileFeature_c"
        or SketchObject.object_id != 26
        or SketchObject.name != "Sketch1"
        or PadObject.class_name != "moExtrusion_c"
        or PadObject.name != "Boss-Extrude1"
        or (BoundsValue is None) == (CircleValue is None)
        or EndCodes is None
        or len(PadObject.dimensions) != 1
    ):
        return None
    DepthValue = PadObject.dimensions[0].value_mm
    if not math.isfinite(DepthValue) or DepthValue <= 0.0:
        return None
    DirectionCode, TerminationCode = EndCodes
    IsDimensionedBox = False
    HeaderBoundsData = None
    HeaderCreationData = None
    Config0Data = None
    if BoundsValue is not None:
        IsDimensionedBox = (
            PadObject.properties
            and ("KitPrimitive", "Box") in PadObject.properties
            and len(SketchObject.dimensions) == 2
        )
        ExpectedFeatureId = 34 if IsDimensionedBox else 32
        if PadObject.object_id != ExpectedFeatureId:
            return None
        ProgramValue = (
            (EncodeBoxProgram(), _BOX_HEADER_STAMPS)
            if PlaneObjectId == 2 and IsDimensionedBox
            else (
                (EncodeProgram(), _FRONT_BOSS_HEADER_STAMPS)
                if PlaneObjectId == 2
                else (
                    (EncodeTopProgram(), _TOP_BOSS_HEADER_STAMPS)
                    if PlaneObjectId == 3
                    else (
                        (EncodeRightProgram(), _RIGHT_BOSS_HEADER_STAMPS)
                        if PlaneObjectId == 4
                        else None
                    )
                )
            )
        )
        if ProgramValue is None:
            return None
        ProgramData, HeaderStamps = ProgramValue
        Config0Data = EncodeBoxConfigProgram() if IsDimensionedBox else None
        EditData = FeatureEdit(
            corners_mm=rectangle_corners_mm(*BoundsValue),
            depth_mm=DepthValue,
            reversed=bool(DirectionCode),
            end_condition_code=TerminationCode,
            update_depth_copies=EndCodes == (0, 0) or PlaneObjectId in {3, 4},
            SketchDimensionsMm=(
                tuple(ItemData.value_mm for ItemData in SketchObject.dimensions)
                if IsDimensionedBox
                else None
            ),
        )
    else:
        if (
            CircleValue is None
            or EndCodes != (0, 0)
            or PlaneObjectId != 2
            or PadObject.object_id != 33
        ):
            return None
        CenterX, CenterY, RadiusValue = CircleValue
        if not math.isclose(
            CenterX,
            0.0,
            rel_tol=0.0,
            abs_tol=1.0e-10,
        ) or not math.isclose(
            CenterY,
            0.0,
            rel_tol=0.0,
            abs_tol=1.0e-10,
        ):
            return None
        ProgramData = EncodeCircleProgram()
        HeaderStamps = _CIRCLE_BOSS_HEADER_STAMPS
        CenterXMetres = CenterX / _MILLIMETRES
        CenterYMetres = CenterY / _MILLIMETRES
        RadiusMetres = RadiusValue / _MILLIMETRES
        DepthMetres = DepthValue / _MILLIMETRES
        CenterZMetres = DepthMetres / 2.0
        HeaderBoundsData = (
            CenterXMetres,
            CenterYMetres,
            CenterZMetres,
            CenterXMetres + RadiusMetres,
            CenterYMetres + RadiusMetres,
            DepthMetres,
            CenterXMetres - RadiusMetres,
            CenterYMetres - RadiusMetres,
            0.0,
            math.sqrt(RadiusMetres**2 * 2.0 + CenterZMetres**2),
        )
        HeaderCreationData = HeaderStamps[0][0] - 1
        Config0Data = EncodeCircCfg(
            CenterX,
            CenterY,
            RadiusValue,
            DepthValue,
        )
        EditData = FeatureEdit(
            radii_mm=(RadiusValue,),
            arc_centres_mm=((CenterX, CenterY),),
            depth_mm=DepthValue,
            update_depth_copies=True,
            SketchDimensionsMm=(RadiusValue * 2.0,),
        )
    return _VendorResolved(
        patch_features(
            ProgramData,
            {0: EditData},
        ),
        HeaderStamps,
        HeaderBounds=HeaderBoundsData,
        HeaderCreation=HeaderCreationData,
        Config0Payload=Config0Data,
    )


# the recovered revolution program authors one full rectangular revolved boss
def BuildSingleRevolutionVendorTree(
    AuthoredObjs: tuple[_WriteObject, ...],
) -> _VendorResolved | None:
    if len(AuthoredObjs) != 2:
        return None
    SketchObject, RevolveObject = AuthoredObjs
    PlaneObjectId = (
        struct.unpack_from("<I", SketchObject.payload)[0]
        if len(SketchObject.payload) >= 4
        else 0
    )
    BoundsValue = _write_rectangle_bounds(SketchObject)
    if (
        SketchObject.class_name != "moProfileFeature_c"
        or SketchObject.object_id != 26
        or SketchObject.name != "Sketch1"
        or PlaneObjectId != 2
        or BoundsValue is None
        or RevolveObject.class_name != "moRevolution_c"
        or RevolveObject.object_id != 31
        or RevolveObject.name != "Revolve1"
        or len(RevolveObject.dimensions) != 1
        or RevolveObject.dimensions[0].name != "D1"
    ):
        return None
    AngleDegrees = RevolveObject.dimensions[0].value_mm
    if not math.isfinite(AngleDegrees) or not math.isclose(
        AngleDegrees,
        360.0,
        rel_tol=0.0,
        abs_tol=1.0e-10,
    ):
        return None
    return _VendorResolved(
        patch_features(
            EncodeRevolveProgram(),
            {
                0: FeatureEdit(
                    corners_mm=rectangle_corners_mm(*BoundsValue),
                    angle_radians=math.radians(AngleDegrees),
                )
            },
        ),
        _REVOLUTION_HEADER_STAMPS,
    )


# the recovered mixed program authors one pad followed by one full revolved cut
def BuildPadGrooveVendorTree(
    AuthoredObjs: tuple[_WriteObject, ...],
) -> _VendorResolved | None:
    if len(AuthoredObjs) != 4:
        return None
    SketchOne, PadObject, SketchTwo, GrooveObject = AuthoredObjs
    BoundsData = (
        _write_rectangle_bounds(SketchOne),
        _write_rectangle_bounds(SketchTwo),
    )
    PadCodes = ExtrusionEditCodes(PadObject.payload)
    if (
        SketchOne.class_name != "moProfileFeature_c"
        or SketchOne.object_id != 26
        or SketchOne.name != "Sketch1"
        or SketchTwo.class_name != "moProfileFeature_c"
        or SketchTwo.object_id != 33
        or SketchTwo.name != "Sketch2"
        or any(ItemData is None for ItemData in BoundsData)
        or PadObject.class_name != "moExtrusion_c"
        or PadObject.object_id != 32
        or PadObject.name != "Boss-Extrude1"
        or PadCodes is None
        or PadCodes[1] not in {0, 6}
        or len(PadObject.dimensions) != 1
        or GrooveObject.class_name != "moRevolution_c"
        or GrooveObject.object_id != 39
        or GrooveObject.name != "Cut-Revolve1"
        or len(GrooveObject.dimensions) != 1
    ):
        return None
    PadDepth = PadObject.dimensions[0].value_mm
    GrooveAngle = GrooveObject.dimensions[0].value_mm
    if (
        not math.isfinite(PadDepth)
        or PadDepth <= 0.0
        or not math.isfinite(GrooveAngle)
        or not math.isclose(GrooveAngle, 360.0, rel_tol=0.0, abs_tol=1.0e-10)
    ):
        return None
    BoundsOne, BoundsTwo = BoundsData
    if BoundsOne is None or BoundsTwo is None:
        return None
    return _VendorResolved(
        patch_features(
            EncodeBossRevCutProgram(),
            {
                0: FeatureEdit(
                    corners_mm=rectangle_corners_mm(*BoundsOne),
                    depth_mm=PadDepth,
                    reversed=bool(PadCodes[0]),
                    end_condition_code=PadCodes[1],
                    update_depth_copies=True,
                ),
                1: FeatureEdit(
                    corners_mm=rectangle_corners_mm(*BoundsTwo),
                    angle_radians=math.radians(GrooveAngle),
                ),
            },
        ),
        _BOSS_REV_CUT_HEADER_STAMPS,
        2,
    )


# the plane-supported pad-pocket program is selected only for its exact recovered topology
def BuildTwoFeatureVendorTree(
    AuthoredObjs: tuple[_WriteObject, ...],
) -> _VendorResolved | None:
    SketchOne, PadObject, SketchTwo, CutObject = AuthoredObjs
    ExpectedData = (
        (SketchOne, 26, "Sketch1"),
        (SketchTwo, 33, "Sketch2"),
    )
    BoundsData = tuple(
        _write_rectangle_bounds(ItemData[0]) for ItemData in ExpectedData
    )
    EndCodes = (
        ExtrusionEditCodes(PadObject.payload),
        ExtrusionEditCodes(CutObject.payload),
    )
    if (
        any(
            SketchObject.class_name != "moProfileFeature_c"
            or SketchObject.object_id != ObjectId
            or SketchObject.name != ObjectName
            or len(SketchObject.payload) < 4
            or struct.unpack_from("<I", SketchObject.payload)[0] != 2
            for SketchObject, ObjectId, ObjectName in ExpectedData
        )
        or any(ItemData is None for ItemData in BoundsData)
        or PadObject.class_name != "moExtrusion_c"
        or PadObject.object_id != 32
        or PadObject.name != "Boss-Extrude1"
        or CutObject.class_name not in {"moCut_c", "moExtrusion_c"}
        or CutObject.object_id != 40
        or CutObject.name
        != (
            "Boss-Extrude2"
            if CutObject.class_name == "moExtrusion_c"
            else "Cut-Extrude1"
        )
        or any(ItemData is None for ItemData in EndCodes)
        or len(PadObject.dimensions) != 1
    ):
        return None
    PadCodes, CutCodes = EndCodes
    if PadCodes is None or CutCodes is None or PadCodes[1] != 0:
        return None
    if CutObject.class_name == "moExtrusion_c":
        if CutCodes[1] != 0 or len(CutObject.dimensions) != 1:
            return None
        CutDepth = CutObject.dimensions[0].value_mm
        ProgramData = EncodeBossBossProgram()
        HeaderStamps = _BOSS_BOSS_HEADER_STAMPS
    elif CutCodes[1] == 0:
        if len(CutObject.dimensions) != 1:
            return None
        CutDepth: float | None = CutObject.dimensions[0].value_mm
        ProgramData = EncodeBossCutProgram()
        HeaderStamps = _BOSS_CUT_HEADER_STAMPS
    elif CutCodes == (1, 1):
        if CutObject.dimensions:
            return None
        CutDepth = None
        ProgramData = EncodeBossCutThroughProgram()
        HeaderStamps = _BOSS_CUT_THROUGH_HEADER_STAMPS
    else:
        return None
    DepthData = (PadObject.dimensions[0].value_mm, CutDepth)
    if any(
        ItemData is not None and (not math.isfinite(ItemData) or ItemData <= 0.0)
        for ItemData in DepthData
    ):
        return None
    EditData: dict[int, FeatureEdit] = {}
    for FeatureIndex, (BoundsValue, DepthValue, CodesValue) in enumerate(
        zip(BoundsData, DepthData, EndCodes, strict=True)
    ):
        if BoundsValue is None or CodesValue is None:
            return None
        if DepthValue is None:
            EditData[FeatureIndex] = FeatureEdit(
                corners_mm=rectangle_corners_mm(*BoundsValue),
            )
        else:
            EditData[FeatureIndex] = FeatureEdit(
                corners_mm=rectangle_corners_mm(*BoundsValue),
                depth_mm=DepthValue,
                reversed=bool(CodesValue[0]),
                end_condition_code=CodesValue[1],
                update_depth_copies=True,
            )
    return _VendorResolved(
        patch_features(ProgramData, EditData),
        HeaderStamps,
    )


# the recovered three-object program authors a rectangular boss and one edge fillet
def BuildBossFilletVendorTree(
    AuthoredObjs: tuple[_WriteObject, ...],
) -> _VendorResolved | None:
    if len(AuthoredObjs) != 3:
        return None
    SketchObject, PadObject, FilletObject = AuthoredObjs
    BoundsValue = _write_rectangle_bounds(SketchObject)
    PadCodes = ExtrusionEditCodes(PadObject.payload)
    if (
        SketchObject.class_name != "moProfileFeature_c"
        or SketchObject.object_id != 26
        or SketchObject.name != "Sketch1"
        or len(SketchObject.payload) < 4
        or struct.unpack_from("<I", SketchObject.payload)[0] != 2
        or BoundsValue is None
        or PadObject.class_name != "moExtrusion_c"
        or PadObject.object_id != 32
        or PadObject.name != "Boss-Extrude1"
        or PadCodes != (0, 0)
        or len(PadObject.dimensions) != 1
        or FilletObject.class_name != "Fillet_c"
        or FilletObject.object_id != 34
        or FilletObject.name != "Fillet1"
        or len(FilletObject.dimensions) != 1
        or FilletObject.payload != _FilletSelectionRecord(32, 3)
    ):
        return None
    PadDepth = PadObject.dimensions[0].value_mm
    FilletRadius = FilletObject.dimensions[0].value_mm
    MinimumX, MinimumY, MaximumX, MaximumY = BoundsValue
    if (
        not math.isfinite(PadDepth)
        or PadDepth <= 0.0
        or not math.isfinite(FilletRadius)
        or FilletRadius <= 0.0
        or FilletRadius * 2.0 >= min(MaximumX - MinimumX, MaximumY - MinimumY)
    ):
        return None
    RadiusMetres = FilletRadius / _MILLIMETRES
    MaximumXMetres = MaximumX / _MILLIMETRES
    MaximumYMetres = MaximumY / _MILLIMETRES
    MinimumXMetres = MinimumX / _MILLIMETRES
    MinimumYMetres = MinimumY / _MILLIMETRES
    PadDepthMetres = PadDepth / _MILLIMETRES
    CenterXMetres = (MinimumXMetres + MaximumXMetres) / 2.0
    CenterYMetres = (MinimumYMetres + MaximumYMetres) / 2.0
    CenterZMetres = PadDepthMetres / 2.0
    BoundsRadius = math.sqrt(
        ((MaximumXMetres - MinimumXMetres) / 2.0) ** 2
        + ((MaximumYMetres - MinimumYMetres) / 2.0) ** 2
        + CenterZMetres**2
    )
    HeaderBounds = (
        CenterXMetres,
        CenterYMetres,
        CenterZMetres,
        MaximumXMetres,
        MaximumYMetres,
        PadDepthMetres,
        MinimumXMetres,
        MinimumYMetres,
        0.0,
        BoundsRadius,
    )
    ProgramOverrides = {
        **{ItemData: RadiusMetres for ItemData in _BOSS_FILLET_RADIUS_OFFSETS},
        **{
            ItemData: MaximumXMetres - RadiusMetres
            for ItemData in _BOSS_FILLET_MAX_X_OFFSETS
        },
        **{
            ItemData: MaximumYMetres - RadiusMetres
            for ItemData in _BOSS_FILLET_MAX_Y_OFFSETS
        },
        _BOSS_FILLET_NEGATIVE_Y_OFFSET: -(MaximumYMetres - RadiusMetres),
    }
    return _VendorResolved(
        patch_features(
            EncodeBossFilletProgram(ProgramOverrides),
            {
                0: FeatureEdit(
                    corners_mm=rectangle_corners_mm(*BoundsValue),
                    depth_mm=PadDepth,
                    reversed=False,
                    end_condition_code=0,
                    update_depth_copies=True,
                )
            },
        ),
        _BOSS_FILLET_HEADER_STAMPS,
        2,
        32,
        HeaderBounds,
        _BOSS_FILLET_HEADER_STAMPS[0][0] - 1,
    )


# the recovered three-object program authors a rectangular boss and one edge chamfer
def BuildBossChamferVendorTree(
    AuthoredObjs: tuple[_WriteObject, ...],
) -> _VendorResolved | None:
    if len(AuthoredObjs) != 3:
        return None
    SketchObject, PadObject, ChamferObject = AuthoredObjs
    BoundsValue = _write_rectangle_bounds(SketchObject)
    PadCodes = ExtrusionEditCodes(PadObject.payload)
    if (
        SketchObject.class_name != "moProfileFeature_c"
        or SketchObject.object_id != 26
        or SketchObject.name != "Sketch1"
        or len(SketchObject.payload) < 4
        or struct.unpack_from("<I", SketchObject.payload)[0] != 2
        or BoundsValue is None
        or PadObject.class_name != "moExtrusion_c"
        or PadObject.object_id != 32
        or PadObject.name != "Boss-Extrude1"
        or PadCodes != (0, 0)
        or len(PadObject.dimensions) != 1
        or ChamferObject.class_name != "Chamfer_c"
        or ChamferObject.object_id != 35
        or ChamferObject.name != "Chamfer1"
        or len(ChamferObject.dimensions) != 1
        or ChamferObject.payload != _FilletSelectionRecord(32, 3)
    ):
        return None
    PadDepth = PadObject.dimensions[0].value_mm
    ChamferDistance = ChamferObject.dimensions[0].value_mm
    MinimumX, MinimumY, MaximumX, MaximumY = BoundsValue
    if (
        not math.isfinite(PadDepth)
        or PadDepth <= 0.0
        or not math.isfinite(ChamferDistance)
        or ChamferDistance <= 0.0
        or ChamferDistance * 2.0 >= min(MaximumX - MinimumX, MaximumY - MinimumY)
    ):
        return None
    DistanceMetres = ChamferDistance / _MILLIMETRES
    MaximumXMetres = MaximumX / _MILLIMETRES
    MaximumYMetres = MaximumY / _MILLIMETRES
    MinimumXMetres = MinimumX / _MILLIMETRES
    MinimumYMetres = MinimumY / _MILLIMETRES
    PadDepthMetres = PadDepth / _MILLIMETRES
    CenterXMetres = (MinimumXMetres + MaximumXMetres) / 2.0
    CenterYMetres = (MinimumYMetres + MaximumYMetres) / 2.0
    CenterZMetres = PadDepthMetres / 2.0
    BoundsRadius = math.sqrt(
        ((MaximumXMetres - MinimumXMetres) / 2.0) ** 2
        + ((MaximumYMetres - MinimumYMetres) / 2.0) ** 2
        + CenterZMetres**2
    )
    HeaderBounds = (
        CenterXMetres,
        CenterYMetres,
        CenterZMetres,
        MaximumXMetres,
        MaximumYMetres,
        PadDepthMetres,
        MinimumXMetres,
        MinimumYMetres,
        0.0,
        BoundsRadius,
    )
    TrimmedYMetres = MaximumYMetres - DistanceMetres
    ProgramOverrides = {
        **{ItemData: DistanceMetres for ItemData in _BOSS_CHAMFER_DISTANCE_OFFSETS},
        **{ItemData: TrimmedYMetres for ItemData in _BOSS_CHAMFER_MAX_Y_OFFSETS},
        **{ItemData: -TrimmedYMetres for ItemData in _BOSS_CHAMFER_NEGATIVE_Y_OFFSETS},
        _BOSS_CHAMFER_NEGATIVE_DISTANCE_OFFSET: -DistanceMetres,
    }
    return _VendorResolved(
        patch_features(
            EncodeBossChamferProgram(ProgramOverrides),
            {
                0: FeatureEdit(
                    corners_mm=rectangle_corners_mm(*BoundsValue),
                    depth_mm=PadDepth,
                    reversed=False,
                    end_condition_code=0,
                    update_depth_copies=True,
                )
            },
        ),
        _BOSS_CHAMFER_HEADER_STAMPS,
        2,
        32,
        HeaderBounds,
        _BOSS_CHAMFER_HEADER_STAMPS[0][0] - 1,
    )


# the recovered three-object program authors a rectangular boss and inward top-open shell
def BuildBossShellVendorTree(
    AuthoredObjs: tuple[_WriteObject, ...],
) -> _VendorResolved | None:
    if len(AuthoredObjs) != 3:
        return None
    SketchObject, PadObject, ShellObject = AuthoredObjs
    BoundsValue = _write_rectangle_bounds(SketchObject)
    PadCodes = ExtrusionEditCodes(PadObject.payload)
    if (
        SketchObject.class_name != "moProfileFeature_c"
        or SketchObject.object_id != 26
        or SketchObject.name != "Sketch1"
        or len(SketchObject.payload) < 4
        or struct.unpack_from("<I", SketchObject.payload)[0] != 2
        or BoundsValue is None
        or PadObject.class_name != "moExtrusion_c"
        or PadObject.object_id != 32
        or PadObject.name != "Boss-Extrude1"
        or PadCodes != (0, 0)
        or len(PadObject.dimensions) != 1
        or ShellObject.class_name != "moShell_c"
        or ShellObject.object_id != 34
        or ShellObject.name != "Shell1"
        or len(ShellObject.dimensions) != 1
        or ShellObject.payload != _ShellSelectionRecord(32)
    ):
        return None
    PadDepth = PadObject.dimensions[0].value_mm
    ShellThickness = ShellObject.dimensions[0].value_mm
    MinimumX, MinimumY, MaximumX, MaximumY = BoundsValue
    if (
        not math.isfinite(PadDepth)
        or PadDepth <= 0.0
        or not math.isfinite(ShellThickness)
        or ShellThickness <= 0.0
        or ShellThickness >= PadDepth
        or ShellThickness * 2.0 >= min(MaximumX - MinimumX, MaximumY - MinimumY)
    ):
        return None
    ThicknessMetres = ShellThickness / _MILLIMETRES
    MaximumXMetres = MaximumX / _MILLIMETRES
    MaximumYMetres = MaximumY / _MILLIMETRES
    MinimumXMetres = MinimumX / _MILLIMETRES
    MinimumYMetres = MinimumY / _MILLIMETRES
    PadDepthMetres = PadDepth / _MILLIMETRES
    CenterXMetres = (MinimumXMetres + MaximumXMetres) / 2.0
    CenterYMetres = (MinimumYMetres + MaximumYMetres) / 2.0
    CenterZMetres = PadDepthMetres / 2.0
    BoundsRadius = math.sqrt(
        ((MaximumXMetres - MinimumXMetres) / 2.0) ** 2
        + ((MaximumYMetres - MinimumYMetres) / 2.0) ** 2
        + CenterZMetres**2
    )
    HeaderBounds = (
        CenterXMetres,
        CenterYMetres,
        CenterZMetres,
        MaximumXMetres,
        MaximumYMetres,
        PadDepthMetres,
        MinimumXMetres,
        MinimumYMetres,
        0.0,
        BoundsRadius,
    )
    ProgramOverrides = {
        **{ItemData: ThicknessMetres for ItemData in _BOSS_SHELL_THICKNESS_OFFSETS},
        _BOSS_SHELL_MIN_X_OFFSET: MinimumXMetres,
        _BOSS_SHELL_INNER_MIN_X_OFFSET: MinimumXMetres + ThicknessMetres,
        _BOSS_SHELL_MAX_X_OFFSET: MaximumXMetres,
        _BOSS_SHELL_DEPTH_OFFSET: PadDepthMetres,
    }
    return _VendorResolved(
        patch_features(
            EncodeBossShellProgram(ProgramOverrides),
            {
                0: FeatureEdit(
                    corners_mm=rectangle_corners_mm(*BoundsValue),
                    depth_mm=PadDepth,
                    reversed=False,
                    end_condition_code=0,
                    update_depth_copies=True,
                )
            },
        ),
        _BOSS_SHELL_HEADER_STAMPS,
        1,
        None,
        HeaderBounds,
        _BOSS_SHELL_HEADER_STAMPS[0][0] - 1,
        32,
    )


# the recovered program authors a rectangular boss and fused sketch-normal pattern
def BuildBossLinearPatternVendorTree(
    AuthoredObjs: tuple[_WriteObject, ...],
) -> _VendorResolved | None:
    if len(AuthoredObjs) != 3:
        return None
    SketchObject, PadObject, PatternObject = AuthoredObjs
    BoundsValue = _write_rectangle_bounds(SketchObject)
    PadCodes = ExtrusionEditCodes(PadObject.payload)
    if (
        SketchObject.class_name != "moProfileFeature_c"
        or SketchObject.object_id != 26
        or SketchObject.name != "Sketch1"
        or len(SketchObject.payload) < 4
        or struct.unpack_from("<I", SketchObject.payload)[0] != 2
        or BoundsValue is None
        or PadObject.class_name != "moExtrusion_c"
        or PadObject.object_id != 32
        or PadObject.name != "Boss-Extrude1"
        or PadCodes != (0, 0)
        or len(PadObject.dimensions) != 1
        or PatternObject.class_name != "moLPattern_c"
        or PatternObject.object_id != 40
        or PatternObject.name != "LPattern1"
        or PatternObject.kind != "LPattern"
        or len(PatternObject.dimensions) != 2
        or tuple(ItemData.name for ItemData in PatternObject.dimensions) != ("D1", "D3")
        or PatternObject.payload
    ):
        return None
    PadDepth = PadObject.dimensions[0].value_mm
    CountNumber = PatternObject.dimensions[0].value_mm
    SpacingValue = PatternObject.dimensions[1].value_mm
    OccurrenceCount = int(CountNumber)
    MinimumX, MinimumY, MaximumX, MaximumY = BoundsValue
    if (
        not math.isfinite(PadDepth)
        or PadDepth <= 0.0
        or not math.isfinite(CountNumber)
        or CountNumber != OccurrenceCount
        or not 2 <= OccurrenceCount <= 1000
        or not math.isfinite(SpacingValue)
        or SpacingValue <= 0.0
        or SpacingValue > PadDepth
    ):
        return None
    PadDepthMetres = PadDepth / _MILLIMETRES
    SpacingMetres = SpacingValue / _MILLIMETRES
    MinimumXMetres = MinimumX / _MILLIMETRES
    MinimumYMetres = MinimumY / _MILLIMETRES
    MaximumXMetres = MaximumX / _MILLIMETRES
    MaximumYMetres = MaximumY / _MILLIMETRES
    TerminalDepthMetres = PadDepthMetres + SpacingMetres * (OccurrenceCount - 1)
    CenterXMetres = (MinimumXMetres + MaximumXMetres) / 2.0
    CenterYMetres = (MinimumYMetres + MaximumYMetres) / 2.0
    CenterZMetres = TerminalDepthMetres / 2.0
    BoundsRadius = math.sqrt(
        ((MaximumXMetres - MinimumXMetres) / 2.0) ** 2
        + ((MaximumYMetres - MinimumYMetres) / 2.0) ** 2
        + CenterZMetres**2
    )
    HeaderBounds = (
        CenterXMetres,
        CenterYMetres,
        CenterZMetres,
        MaximumXMetres,
        MaximumYMetres,
        TerminalDepthMetres,
        MinimumXMetres,
        MinimumYMetres,
        0.0,
        BoundsRadius,
    )
    PositiveDisplay = 0.55 * TerminalDepthMetres
    MaximumProfileSpanMetres = max(
        MaximumXMetres - MinimumXMetres,
        MaximumYMetres - MinimumYMetres,
    )
    ProgramOverrides = {
        _BOSS_LINEAR_PATTERN_COUNT_OFFSET: OccurrenceCount,
        **{
            ItemData: float(OccurrenceCount)
            for ItemData in _BOSS_LINEAR_PATTERN_COUNT_DOUBLE_OFFSETS
        },
        **{
            ItemData: SpacingMetres
            for ItemData in _BOSS_LINEAR_PATTERN_POSITIVE_SPACING_OFFSETS
        },
        **{
            ItemData: SpacingMetres
            for ItemData in _BOSS_LINEAR_PATTERN_DIRECTION_DISTANCE_OFFSETS
        },
        _BOSS_LINEAR_PATTERN_DIRECTION_FLAG_OFFSET: 1,
        **{ItemData: -0.0 for ItemData in _BOSS_LINEAR_PATTERN_NEGATIVE_ZERO_OFFSETS},
        **{ItemData: 1.0 for ItemData in _BOSS_LINEAR_PATTERN_POSITIVE_AXIS_OFFSETS},
        _BOSS_LINEAR_PATTERN_NEGATIVE_DIAGONAL_OFFSET: -math.sqrt(0.5),
        _BOSS_LINEAR_PATTERN_POSITIVE_DIAGONAL_OFFSET: math.sqrt(0.5),
        _BOSS_LINEAR_PATTERN_TERMINAL_DEPTH_OFFSET: TerminalDepthMetres,
        _BOSS_LINEAR_PATTERN_COUNT_DISPLAY_OFFSET: (
            MaximumProfileSpanMetres + (OccurrenceCount + 2) / _MILLIMETRES
        ),
        _BOSS_LINEAR_PATTERN_NEGATIVE_EXTENT_OFFSET: -0.05 * TerminalDepthMetres,
        **{
            ItemData: PositiveDisplay
            for ItemData in _BOSS_LINEAR_PATTERN_POSITIVE_DISPLAY_OFFSETS
        },
        **{
            ItemData: -PositiveDisplay
            for ItemData in _BOSS_LINEAR_PATTERN_NEGATIVE_DISPLAY_OFFSETS
        },
        **{
            ItemData: CenterZMetres
            for ItemData in _BOSS_LINEAR_PATTERN_CENTER_DISPLAY_OFFSETS
        },
        _BOSS_LINEAR_PATTERN_PAD_DISPLAY_OFFSET: 1.05 * TerminalDepthMetres,
    }
    return _VendorResolved(
        patch_features(
            EncodeBossLinearPatternProgram(ProgramOverrides),
            {
                0: FeatureEdit(
                    corners_mm=rectangle_corners_mm(*BoundsValue),
                    depth_mm=PadDepth,
                    reversed=False,
                    end_condition_code=0,
                    update_depth_copies=True,
                )
            },
        ),
        _BOSS_LINEAR_PATTERN_HEADER_STAMPS,
        2,
        None,
        HeaderBounds,
        _BOSS_LINEAR_PATTERN_HEADER_STAMPS[0][0] - 1,
        None,
        "linear_pattern",
    )


# the recovered program authors a rectangular boss and fused sketch-normal rotation
def BuildBossCircularPatternVendorTree(
    AuthoredObjs: tuple[_WriteObject, ...],
) -> _VendorResolved | None:
    if len(AuthoredObjs) != 3:
        return None
    SketchObject, PadObject, PatternObject = AuthoredObjs
    BoundsValue = _write_rectangle_bounds(SketchObject)
    PadCodes = ExtrusionEditCodes(PadObject.payload)
    if (
        SketchObject.class_name != "moProfileFeature_c"
        or SketchObject.object_id != 26
        or SketchObject.name != "Sketch1"
        or len(SketchObject.payload) < 4
        or struct.unpack_from("<I", SketchObject.payload)[0] != 2
        or BoundsValue is None
        or PadObject.class_name != "moExtrusion_c"
        or PadObject.object_id != 32
        or PadObject.name != "Boss-Extrude1"
        or PadCodes != (0, 0)
        or len(PadObject.dimensions) != 1
        or PatternObject.class_name != "moCirPattern_c"
        or PatternObject.object_id != 46
        or PatternObject.name != "CirPattern1"
        or PatternObject.kind != "CirPattern"
        or len(PatternObject.dimensions) != 2
        or tuple(ItemData.name for ItemData in PatternObject.dimensions) != ("D1", "D3")
        or PatternObject.payload
    ):
        return None
    PadDepth = PadObject.dimensions[0].value_mm
    CountNumber = PatternObject.dimensions[0].value_mm
    AngleDegrees = PatternObject.dimensions[1].value_mm
    OccurrenceCount = int(CountNumber)
    if (
        not math.isfinite(PadDepth)
        or PadDepth <= 0.0
        or not math.isfinite(CountNumber)
        or CountNumber != OccurrenceCount
        or not 2 <= OccurrenceCount <= 1000
        or not math.isfinite(AngleDegrees)
        or not 0.0 < AngleDegrees <= 360.0
        or any(
            not math.isclose(ActualValue, ExpectedValue, rel_tol=0.0, abs_tol=1.0e-10)
            for ActualValue, ExpectedValue in zip(
                BoundsValue,
                (0.0, 0.0, 10.0, 5.0),
                strict=True,
            )
        )
    ):
        return None
    PadDepthMetres = PadDepth / _MILLIMETRES
    PatternBounds = _CircularPatternBounds(
        BoundsValue,
        OccurrenceCount,
        AngleDegrees,
    )
    MinimumX, MinimumY, MaximumX, MaximumY = (
        ItemData / _MILLIMETRES for ItemData in PatternBounds
    )
    CenterXMetres = (MinimumX + MaximumX) / 2.0
    CenterYMetres = (MinimumY + MaximumY) / 2.0
    CenterZMetres = PadDepthMetres / 2.0
    BoundsRadius = math.sqrt(
        ((MaximumX - MinimumX) / 2.0) ** 2
        + ((MaximumY - MinimumY) / 2.0) ** 2
        + CenterZMetres**2
    )
    HeaderBounds = (
        CenterXMetres,
        CenterYMetres,
        CenterZMetres,
        MaximumX,
        MaximumY,
        PadDepthMetres,
        MinimumX,
        MinimumY,
        0.0,
        BoundsRadius,
    )
    AngleRadians = math.radians(AngleDegrees)
    ProgramOverrides = {
        _BOSS_CIRCULAR_PATTERN_COUNT_OFFSET: OccurrenceCount,
        **{
            ItemData: float(OccurrenceCount)
            for ItemData in _BOSS_CIRCULAR_PATTERN_COUNT_DOUBLE_OFFSETS
        },
        **{ItemData: AngleRadians for ItemData in _BOSS_CIRCULAR_PATTERN_ANGLE_OFFSETS},
        _BOSS_CIRCULAR_PATTERN_DIRECTION_FLAG_OFFSET: 1,
    }
    return _VendorResolved(
        patch_features(
            EncodeBossCircularPatternProgram(ProgramOverrides),
            {
                0: FeatureEdit(
                    corners_mm=rectangle_corners_mm(*BoundsValue),
                    depth_mm=PadDepth,
                    reversed=False,
                    end_condition_code=0,
                    update_depth_copies=True,
                )
            },
        ),
        _BOSS_CIRCULAR_PATTERN_HEADER_STAMPS,
        2,
        None,
        HeaderBounds,
        _BOSS_CIRCULAR_PATTERN_HEADER_STAMPS[0][0] - 1,
        None,
        "circular_pattern",
    )


# the native equal-spacing rule uses a closed denominator only for a full revolution
def _CircularPatternBounds(
    BoundsValue: tuple[float, float, float, float],
    OccurrenceCount: int,
    AngleDegrees: float,
) -> tuple[float, float, float, float]:
    MinimumX, MinimumY, MaximumX, MaximumY = BoundsValue
    CornerData = (
        (MinimumX, MinimumY),
        (MaximumX, MinimumY),
        (MaximumX, MaximumY),
        (MinimumX, MaximumY),
    )
    Denominator = (
        OccurrenceCount
        if math.isclose(AngleDegrees, 360.0, rel_tol=0.0, abs_tol=1.0e-10)
        else OccurrenceCount - 1
    )
    RotatedData = tuple(
        (
            XValue * math.cos(AngleValue) - YValue * math.sin(AngleValue),
            XValue * math.sin(AngleValue) + YValue * math.cos(AngleValue),
        )
        for IndexValue in range(OccurrenceCount)
        for AngleValue in (math.radians(AngleDegrees * IndexValue / Denominator),)
        for XValue, YValue in CornerData
    )
    return (
        min(ItemData[0] for ItemData in RotatedData),
        min(ItemData[1] for ItemData in RotatedData),
        max(ItemData[0] for ItemData in RotatedData),
        max(ItemData[1] for ItemData in RotatedData),
    )


# the recovered three-operation program covers one boss followed by two blind cuts
def BuildThreeFeatureVendorTree(
    AuthoredObjs: tuple[_WriteObject, ...],
) -> _VendorResolved | None:
    SketchData = AuthoredObjs[0::2]
    FeatureData = AuthoredObjs[1::2]
    ExpectedSketchData = tuple(
        zip(
            SketchData,
            (26, 33, 41),
            ("Sketch1", "Sketch2", "Sketch3"),
            strict=True,
        )
    )
    ExpectedFeatureData = tuple(
        zip(
            FeatureData,
            (32, 40, 47),
            ("Boss-Extrude1", "Cut-Extrude1", "Cut-Extrude2"),
            ("moExtrusion_c", "moCut_c", "moCut_c"),
            strict=True,
        )
    )
    BoundsData = tuple(
        _write_rectangle_bounds(SketchObject) for SketchObject in SketchData
    )
    EndCodes = tuple(
        ExtrusionEditCodes(FeatureObject.payload) for FeatureObject in FeatureData
    )
    if (
        any(
            SketchObject.class_name != "moProfileFeature_c"
            or SketchObject.object_id != ObjectId
            or SketchObject.name != ObjectName
            or len(SketchObject.payload) < 4
            or struct.unpack_from("<I", SketchObject.payload)[0] != 2
            for SketchObject, ObjectId, ObjectName in ExpectedSketchData
        )
        or any(
            FeatureObject.class_name != ClassName
            or FeatureObject.object_id != ObjectId
            or FeatureObject.name != ObjectName
            or len(FeatureObject.dimensions) != 1
            for FeatureObject, ObjectId, ObjectName, ClassName in ExpectedFeatureData
        )
        or any(BoundsValue is None for BoundsValue in BoundsData)
        or any(CodesValue is None for CodesValue in EndCodes)
        or any(CodesValue is not None and CodesValue[1] != 0 for CodesValue in EndCodes)
    ):
        return None
    DepthData = tuple(
        FeatureObject.dimensions[0].value_mm for FeatureObject in FeatureData
    )
    if any(
        not math.isfinite(DepthValue) or DepthValue <= 0.0 for DepthValue in DepthData
    ):
        return None
    EditData: dict[int, FeatureEdit] = {}
    for FeatureIndex, (BoundsValue, DepthValue, CodesValue) in enumerate(
        zip(BoundsData, DepthData, EndCodes, strict=True)
    ):
        if BoundsValue is None or CodesValue is None:
            return None
        EditData[FeatureIndex] = FeatureEdit(
            corners_mm=rectangle_corners_mm(*BoundsValue),
            depth_mm=DepthValue,
            reversed=bool(CodesValue[0]),
            end_condition_code=CodesValue[1],
            update_depth_copies=True,
        )
    return _VendorResolved(
        patch_features(EncodeBossCutCutProgram(), EditData),
        _BOSS_CUT_CUT_HEADER_STAMPS,
    )


# the recovered four-operation program covers one boss followed by three blind cuts
def BuildFourFeatureVendorTree(
    AuthoredObjs: tuple[_WriteObject, ...],
) -> _VendorResolved | None:
    SketchData = AuthoredObjs[0::2]
    FeatureData = AuthoredObjs[1::2]
    ExpectedSketchData = tuple(
        zip(
            SketchData,
            (26, 33, 41, 48),
            ("Sketch1", "Sketch2", "Sketch3", "Sketch4"),
            strict=True,
        )
    )
    ExpectedFeatureData = tuple(
        zip(
            FeatureData,
            (32, 40, 47, 54),
            (
                "Boss-Extrude1",
                "Cut-Extrude1",
                "Cut-Extrude2",
                "Cut-Extrude3",
            ),
            ("moExtrusion_c", "moCut_c", "moCut_c", "moCut_c"),
            strict=True,
        )
    )
    BoundsData = tuple(
        _write_rectangle_bounds(SketchObject) for SketchObject in SketchData
    )
    EndCodes = tuple(
        ExtrusionEditCodes(FeatureObject.payload) for FeatureObject in FeatureData
    )
    if (
        any(
            SketchObject.class_name != "moProfileFeature_c"
            or SketchObject.object_id != ObjectId
            or SketchObject.name != ObjectName
            or len(SketchObject.payload) < 4
            or struct.unpack_from("<I", SketchObject.payload)[0] != 2
            for SketchObject, ObjectId, ObjectName in ExpectedSketchData
        )
        or any(
            FeatureObject.class_name != ClassName
            or FeatureObject.object_id != ObjectId
            or FeatureObject.name != ObjectName
            or len(FeatureObject.dimensions) != 1
            for FeatureObject, ObjectId, ObjectName, ClassName in ExpectedFeatureData
        )
        or any(BoundsValue is None for BoundsValue in BoundsData)
        or any(CodesValue is None for CodesValue in EndCodes)
        or any(CodesValue is not None and CodesValue[1] != 0 for CodesValue in EndCodes)
    ):
        return None
    DepthData = tuple(
        FeatureObject.dimensions[0].value_mm for FeatureObject in FeatureData
    )
    if any(
        not math.isfinite(DepthValue) or DepthValue <= 0.0 for DepthValue in DepthData
    ):
        return None
    EditData: dict[int, FeatureEdit] = {}
    for FeatureIndex, (BoundsValue, DepthValue, CodesValue) in enumerate(
        zip(BoundsData, DepthData, EndCodes, strict=True)
    ):
        if BoundsValue is None or CodesValue is None:
            return None
        EditData[FeatureIndex] = FeatureEdit(
            corners_mm=rectangle_corners_mm(*BoundsValue),
            depth_mm=DepthValue,
            reversed=bool(CodesValue[0]),
            end_condition_code=CodesValue[1],
            update_depth_copies=True,
        )
    return _VendorResolved(
        patch_features(EncodeBossCutCutCutProgram(), EditData),
        _BOSS_CUT_CUT_CUT_HEADER_STAMPS,
    )


# encoded extrusion records expose the direction and termination fields used by the patcher
def ExtrusionEditCodes(PayloadData: bytes) -> tuple[int, int] | None:
    DeclarationData = _class_declaration("moEndSpec_c")
    DirectionOffset = len(DeclarationData) + 10
    TerminationOffset = len(DeclarationData) + 16
    if (
        not PayloadData.startswith(DeclarationData)
        or len(PayloadData) < TerminationOffset + 4
    ):
        return None
    DirectionCode = struct.unpack_from("<I", PayloadData, DirectionOffset)[0]
    TerminationCode = struct.unpack_from("<I", PayloadData, TerminationOffset)[0]
    if DirectionCode not in {0, 1} or TerminationCode not in {0, 1, 6}:
        return None
    return DirectionCode, TerminationCode


def _write_object_ids(document: CadDocument) -> dict[str, int]:
    used = set(range(1, 26))
    result: dict[str, int] = {}
    next_id = 26

    def assign(key: str, native: Any = None) -> int:
        nonlocal next_id
        candidate = native if isinstance(native, int) and native > 25 else None
        if candidate is None or candidate in used or candidate > 0xFFFFFFFE:
            while next_id in used:
                next_id += 1
            candidate = next_id
            next_id += 1
        used.add(candidate)
        result[key] = candidate
        return candidate

    principal = _principal_plane_ids(document.support_planes)
    for plane in document.support_planes:
        key = f"plane:{plane.id}"
        if plane.id in principal:
            result[key] = principal[plane.id]
        else:
            assign(key, plane.attributes.get("native_object_id"))
    for sketch in document.sketches:
        assign(f"sketch:{sketch.id}", sketch.attributes.get("native_object_id"))
    for feature in sorted(document.feature_timeline, key=lambda item: item.order):
        if _is_native_system_feature(feature):
            continue
        native = feature.attributes.get("native_object_id")
        sketch_native = (
            result.get(f"sketch:{feature.sketch_id}")
            if feature.sketch_id is not None
            else None
        )
        if isinstance(native, int) and native == sketch_native:
            result[f"feature:{feature.id}"] = native
        else:
            assign(f"feature:{feature.id}", native)
    configuration_ids: set[int] = set()
    next_configuration_id = 0
    for configuration in document.configurations:
        native = configuration.attributes.get("native_configuration_id")
        candidate = (
            native
            if isinstance(native, int)
            and not isinstance(native, bool)
            and 0 <= native <= 0xFFFFFFFF
            and native not in configuration_ids
            else None
        )
        if candidate is None:
            while next_configuration_id in configuration_ids:
                next_configuration_id += 1
            candidate = next_configuration_id
        configuration_ids.add(candidate)
        result[f"configuration:{configuration.id}"] = candidate
    return result


# coincident principal planes map by global locus while sketch bases normalize separately
def _principal_plane_ids(planes: tuple[SupportPlane, ...]) -> dict[str, int]:
    frames = (
        (
            2,
            (0.0, 0.0, 0.0),
            (1.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
            (0.0, 0.0, 1.0),
        ),
        (
            3,
            (0.0, 0.0, 0.0),
            (1.0, 0.0, 0.0),
            (0.0, 0.0, -1.0),
            (0.0, 1.0, 0.0),
        ),
        (
            4,
            (0.0, 0.0, 0.0),
            (0.0, 0.0, -1.0),
            (0.0, 1.0, 0.0),
            (1.0, 0.0, 0.0),
        ),
    )
    result: dict[str, int] = {}
    claimed: set[int] = set()
    for plane in planes:
        transform = plane.transform
        OriginValue = (
            transform.origin.x,
            transform.origin.y,
            transform.origin.z,
        )
        NormalValue = (
            transform.z_axis.x,
            transform.z_axis.y,
            transform.z_axis.z,
        )
        for object_id, *frame in frames:
            if object_id in claimed:
                continue
            TargetNormal = frame[3]
            if all(
                math.isclose(ItemData, 0.0, abs_tol=1e-9) for ItemData in OriginValue
            ) and math.isclose(
                abs(
                    sum(
                        LeftValue * RightValue
                        for LeftValue, RightValue in zip(
                            NormalValue, TargetNormal, strict=True
                        )
                    )
                ),
                1.0,
                rel_tol=0.0,
                abs_tol=1e-9,
            ):
                result[plane.id] = object_id
                claimed.add(object_id)
                break
    return result


# property extraction keeps primitive placement validation independent of xml objects
def _FreeCadPropertyAttributes(
    ObjectData: Mapping[str, Any],
    PropertyName: str,
) -> Mapping[str, Any] | None:
    PropertiesData = ObjectData.get("properties")
    if not isinstance(PropertiesData, Mapping):
        return None
    PropertyData = PropertiesData.get(PropertyName)
    if not isinstance(PropertyData, Mapping):
        return None
    ChildrenData = PropertyData.get("children")
    if not isinstance(ChildrenData, (list, tuple)) or len(ChildrenData) != 1:
        return None
    ChildData = ChildrenData[0]
    if not isinstance(ChildData, Mapping):
        return None
    AttributesData = ChildData.get("attributes")
    return AttributesData if isinstance(AttributesData, Mapping) else None


# this accepts only the unshifted unrotated primitive frame proved by the boss program
def _IsFreeCadIdentityPlacement(
    ObjectData: Mapping[str, Any],
    PropertyName: str,
) -> bool:
    AttributesData = _FreeCadPropertyAttributes(ObjectData, PropertyName)
    if AttributesData is None:
        return False
    ExpectedData = {
        "Px": 0.0,
        "Py": 0.0,
        "Pz": 0.0,
        "Q0": 0.0,
        "Q1": 0.0,
        "Q2": 0.0,
        "Q3": 1.0,
    }
    try:
        ActualData = {
            KeyData: float(AttributesData[KeyData]) for KeyData in ExpectedData
        }
    except (KeyError, TypeError, ValueError):
        return False
    return all(
        math.isfinite(ActualData[KeyData])
        and math.isclose(
            ActualData[KeyData],
            ExpectedValue,
            rel_tol=0.0,
            abs_tol=1.0e-12,
        )
        for KeyData, ExpectedValue in ExpectedData.items()
    )


# eight exact source corners prove the primitive parameters still describe the stored solid
def _HasFreeCadBoxBrep(
    DocumentData: CadDocument,
    LengthValue: float,
    WidthValue: float,
    HeightValue: float,
) -> bool:
    BrepData = DocumentData.brep
    if (
        BrepData is None
        or len(BrepData.vertices) != 8
        or len(BrepData.edges) != 12
        or len(BrepData.faces) != 6
        or len(BrepData.regions) != 1
        or len(BrepData.bodies) != 1
    ):
        return False
    ExpectedData = {
        (XValue, YValue, ZValue)
        for XValue in (0.0, LengthValue)
        for YValue in (0.0, WidthValue)
        for ZValue in (0.0, HeightValue)
    }
    ActualData = {
        (VertexData.point.x, VertexData.point.y, VertexData.point.z)
        for VertexData in BrepData.vertices
    }
    return len(ActualData) == 8 and all(
        any(
            all(
                math.isclose(
                    ExpectedCoordinate,
                    ActualCoordinate,
                    rel_tol=0.0,
                    abs_tol=1.0e-9,
                )
                for ExpectedCoordinate, ActualCoordinate in zip(
                    ExpectedPoint,
                    ActualPoint,
                    strict=True,
                )
            )
            for ActualPoint in ActualData
        )
        for ExpectedPoint in ExpectedData
    )


# primitive cylinders need topology proof before feature history can replace their source boundary representation
def HasCadCylBrep(
    DocumentData: CadDocument,
    RadiusValue: float,
    HeightValue: float,
) -> bool:
    BrepData = DocumentData.brep
    if (
        BrepData is None
        or len(BrepData.vertices) != 2
        or len(BrepData.curves) != 3
        or len(BrepData.edges) != 3
        or len(BrepData.loops) != 3
        or len(BrepData.surfaces) != 3
        or len(BrepData.faces) != 3
        or len(BrepData.regions) != 1
        or len(BrepData.bodies) != 1
        or not BrepData.regions[0].solid
    ):
        return False
    CircleData = tuple(
        ItemData for ItemData in BrepData.curves if isinstance(ItemData, CircleCurve)
    )
    LineData = tuple(
        ItemData for ItemData in BrepData.curves if isinstance(ItemData, LineCurve)
    )
    CylinderData = tuple(
        ItemData
        for ItemData in BrepData.surfaces
        if isinstance(ItemData, CylinderSurface)
    )
    PlaneData = tuple(
        ItemData for ItemData in BrepData.surfaces if isinstance(ItemData, PlaneSurface)
    )
    if (
        len(CircleData) != 2
        or len(LineData) != 1
        or len(CylinderData) != 1
        or len(PlaneData) != 2
    ):
        return False
    CircleHeights = sorted(ItemData.center.z for ItemData in CircleData)
    PlaneHeights = sorted(ItemData.origin.z for ItemData in PlaneData)
    ExpectedHeights = (0.0, HeightValue)
    if not all(
        math.isclose(ActualValue, ExpectedValue, rel_tol=0.0, abs_tol=1.0e-9)
        for ActualValue, ExpectedValue in zip(
            CircleHeights,
            ExpectedHeights,
            strict=True,
        )
    ) or not all(
        math.isclose(ActualValue, ExpectedValue, rel_tol=0.0, abs_tol=1.0e-9)
        for ActualValue, ExpectedValue in zip(
            PlaneHeights,
            ExpectedHeights,
            strict=True,
        )
    ):
        return False
    if any(
        not math.isclose(ItemData.center.x, 0.0, abs_tol=1.0e-9)
        or not math.isclose(ItemData.center.y, 0.0, abs_tol=1.0e-9)
        or not math.isclose(
            ItemData.radius,
            RadiusValue,
            rel_tol=0.0,
            abs_tol=1.0e-9,
        )
        or not math.isclose(abs(ItemData.axis.z), 1.0, abs_tol=1.0e-9)
        or not math.isclose(ItemData.axis.x, 0.0, abs_tol=1.0e-9)
        or not math.isclose(ItemData.axis.y, 0.0, abs_tol=1.0e-9)
        for ItemData in CircleData
    ):
        return False
    LineValue = LineData[0]
    CylinderValue = CylinderData[0]
    if (
        not math.isclose(
            math.hypot(LineValue.origin.x, LineValue.origin.y),
            RadiusValue,
            rel_tol=0.0,
            abs_tol=1.0e-9,
        )
        or not math.isclose(LineValue.origin.z, 0.0, abs_tol=1.0e-9)
        or not math.isclose(LineValue.direction.x, 0.0, abs_tol=1.0e-9)
        or not math.isclose(LineValue.direction.y, 0.0, abs_tol=1.0e-9)
        or not math.isclose(abs(LineValue.direction.z), 1.0, abs_tol=1.0e-9)
        or not math.isclose(CylinderValue.origin.x, 0.0, abs_tol=1.0e-9)
        or not math.isclose(CylinderValue.origin.y, 0.0, abs_tol=1.0e-9)
        or not math.isclose(CylinderValue.origin.z, 0.0, abs_tol=1.0e-9)
        or not math.isclose(
            CylinderValue.radius,
            RadiusValue,
            rel_tol=0.0,
            abs_tol=1.0e-9,
        )
        or not math.isclose(CylinderValue.axis.x, 0.0, abs_tol=1.0e-9)
        or not math.isclose(CylinderValue.axis.y, 0.0, abs_tol=1.0e-9)
        or not math.isclose(abs(CylinderValue.axis.z), 1.0, abs_tol=1.0e-9)
    ):
        return False
    VertexHeights = sorted(ItemData.point.z for ItemData in BrepData.vertices)
    return all(
        math.isclose(
            math.hypot(ItemData.point.x, ItemData.point.y),
            RadiusValue,
            rel_tol=0.0,
            abs_tol=1.0e-9,
        )
        for ItemData in BrepData.vertices
    ) and all(
        math.isclose(ActualValue, ExpectedValue, rel_tol=0.0, abs_tol=1.0e-9)
        for ActualValue, ExpectedValue in zip(
            VertexHeights,
            ExpectedHeights,
            strict=True,
        )
    )


# exact freecad boxes lower to one dimensioned rectangle and one blind boss
def _FreeCadBoxObjects(
    DocumentData: CadDocument,
    ObjectIds: dict[str, int],
) -> tuple[_WriteObject, ...] | None:
    TimelineData = tuple(
        FeatureData
        for FeatureData in sorted(
            DocumentData.feature_timeline,
            key=lambda FeatureData: FeatureData.order,
        )
        if not _is_native_system_feature(FeatureData)
    )
    if len(TimelineData) != 1:
        return None
    FeatureData = TimelineData[0]
    DefinitionData = FeatureData.definition
    if (
        DocumentData.source.format_id.casefold() != "freecad.fcstd"
        or DocumentData.assembly is not None
        or DocumentData.support_planes
        or DocumentData.sketches
        or DocumentData.selections
        or len(DocumentData.bodies) != 1
        or DocumentData.bodies[0].final_feature_id != FeatureData.id
        or len(DocumentData.configurations) != 1
        or DocumentData.configurations[0].name.casefold() != "default"
        or not DocumentData.configurations[0].active
        or DocumentData.configurations[0].parent_id is not None
        or DocumentData.configurations[0].overrides
        or DocumentData.configurations[0].suppressed_feature_ids
        or FeatureData.order != 0
        or FeatureData.input_feature_ids
        or FeatureData.sketch_id is not None
        or FeatureData.selection_ids
        or FeatureData.configuration_states
        or FeatureData.suppressed
        or str(FeatureData.kind).casefold() != FeatureKind.PRIMITIVE.value
        or FeatureData.operation is not None
        or not isinstance(DefinitionData, NativeFeatureDefinition)
        or DefinitionData.format_id.casefold() != "freecad.fcstd"
        or DefinitionData.type_id not in {"Part::Box", "PartDesign::AdditiveBox"}
        or FeatureData.provenance is None
        or any(ItemData.expression is not None for ItemData in DocumentData.parameters)
    ):
        return None
    PathData: dict[str, Parameter] = {}
    for ItemData in DocumentData.parameters:
        if ItemData.owner_id != FeatureData.id:
            return None
        PathValue = ItemData.attributes.get("freecad_path")
        if not isinstance(PathValue, str) or not PathValue or PathValue in PathData:
            return None
        PathData[PathValue] = ItemData
    ExpectedData = {
        "Length": (ValueKind.LENGTH, None),
        "Width": (ValueKind.LENGTH, None),
        "Height": (ValueKind.LENGTH, None),
        "MapMode": (ValueKind.INTEGER, 0),
        "MapPathParameter": (ValueKind.NUMBER, 0.0),
        "MapReversed": (ValueKind.BOOLEAN, False),
        "Visibility": (ValueKind.BOOLEAN, True),
    }
    if not set(ExpectedData) <= set(PathData) or any(
        not _freecad_parameter_matches(PathData[PathName], KindData, ValueData)
        for PathName, (KindData, ValueData) in ExpectedData.items()
        if ValueData is not None
    ):
        return None
    DimensionsData = tuple(
        _parameter_dimension(PathData[PathName])
        for PathName in ("Length", "Width", "Height")
    )
    if any(ItemData is None for ItemData in DimensionsData):
        return None
    LengthData, WidthData, HeightData = DimensionsData
    if LengthData is None or WidthData is None or HeightData is None:
        return None
    LengthValue = LengthData.value_mm
    WidthValue = WidthData.value_mm
    HeightValue = HeightData.value_mm
    if (
        not all(
            math.isfinite(ItemData) and ItemData > 0.0
            for ItemData in (LengthValue, WidthValue, HeightValue)
        )
        or not _IsFreeCadIdentityPlacement(DefinitionData.object_data, "Placement")
        or not _IsFreeCadIdentityPlacement(
            DefinitionData.object_data,
            "AttachmentOffset",
        )
        or not _HasFreeCadBoxBrep(
            DocumentData,
            LengthValue,
            WidthValue,
            HeightValue,
        )
    ):
        return None
    SketchPayload = bytearray(_plane_reference(2))
    CornerData = (
        (0.0, 0.0),
        (LengthValue, 0.0),
        (LengthValue, WidthValue),
        (0.0, WidthValue),
    )
    for LocalIndex, PointData in enumerate(CornerData, 1):
        SketchPayload.extend(_coordinate_marker(PointData, LocalIndex, _POINT_LOCUS))
    for LocalIndex, (StartIndex, EndIndex) in enumerate(
        ((0, 1), (1, 2), (2, 3), (3, 0)),
        5,
    ):
        SketchPayload.extend(_line_marker(StartIndex, EndIndex, LocalIndex))
    SketchSourceId = f"{FeatureData.id}:box-profile"
    ObjectIds[f"sketch:{SketchSourceId}"] = 26
    ObjectIds[f"feature:{FeatureData.id}"] = 34
    ExtrusionData = replace(
        FeatureData,
        kind=FeatureKind.EXTRUSION,
        sketch_id=SketchSourceId,
        operation=BooleanOperation.CREATE,
        definition=ExtrusionFeature(
            ParameterValue(HeightValue, ValueKind.LENGTH, "mm"),
        ),
    )
    return (
        _WriteObject(
            SketchSourceId,
            26,
            "Sketch1",
            "Sketch",
            "Sketch",
            "moProfileFeature_c",
            (("Dissectable", "true"),),
            (
                replace(
                    LengthData,
                    name="D1",
                    text=format(LengthValue, ".15g"),
                ),
                replace(
                    WidthData,
                    name="D2",
                    text=format(WidthValue, ".15g"),
                ),
            ),
            bytes(SketchPayload),
        ),
        _WriteObject(
            FeatureData.id,
            34,
            "Boss-Extrude1",
            "Extrusion",
            "Extrusion",
            "moExtrusion_c",
            (
                ("Dissectable", "true"),
                ("DissectableChildren", "26"),
                ("DissectableRoot", "true"),
                ("KitPrimitive", "Box"),
            ),
            (
                replace(
                    HeightData,
                    name="D1",
                    text=format(HeightValue, ".15g"),
                ),
            ),
            _extrusion_payload(ExtrusionData),
        ),
    )


# exact freecad cylinders lower to one radius driven circle and one blind boss
def BuildCadCylObjs(
    DocumentData: CadDocument,
    ObjectIds: dict[str, int],
) -> tuple[_WriteObject, ...] | None:
    TimelineData = tuple(
        FeatureData
        for FeatureData in sorted(
            DocumentData.feature_timeline,
            key=lambda FeatureData: FeatureData.order,
        )
        if not _is_native_system_feature(FeatureData)
    )
    if len(TimelineData) != 1:
        return None
    FeatureData = TimelineData[0]
    DefinitionData = FeatureData.definition
    if (
        DocumentData.source.format_id.casefold() != "freecad.fcstd"
        or DocumentData.assembly is not None
        or DocumentData.support_planes
        or DocumentData.sketches
        or DocumentData.selections
        or len(DocumentData.bodies) != 1
        or DocumentData.bodies[0].final_feature_id != FeatureData.id
        or len(DocumentData.configurations) != 1
        or DocumentData.configurations[0].name.casefold() != "default"
        or not DocumentData.configurations[0].active
        or DocumentData.configurations[0].parent_id is not None
        or DocumentData.configurations[0].overrides
        or DocumentData.configurations[0].suppressed_feature_ids
        or FeatureData.order != 0
        or FeatureData.input_feature_ids
        or FeatureData.sketch_id is not None
        or FeatureData.selection_ids
        or FeatureData.configuration_states
        or FeatureData.suppressed
        or str(FeatureData.kind).casefold() != FeatureKind.PRIMITIVE.value
        or FeatureData.operation is not None
        or not isinstance(DefinitionData, NativeFeatureDefinition)
        or DefinitionData.format_id.casefold() != "freecad.fcstd"
        or DefinitionData.type_id != "Part::Cylinder"
        or FeatureData.provenance is None
        or any(ItemData.expression is not None for ItemData in DocumentData.parameters)
    ):
        return None
    PathData: dict[str, Parameter] = {}
    for ItemData in DocumentData.parameters:
        if ItemData.owner_id != FeatureData.id:
            return None
        PathValue = ItemData.attributes.get("freecad_path")
        if not isinstance(PathValue, str) or not PathValue or PathValue in PathData:
            return None
        PathData[PathValue] = ItemData
    ExpectedData = {
        "Angle": (ValueKind.ANGLE, 360.0),
        "FirstAngle": (ValueKind.ANGLE, 0.0),
        "SecondAngle": (ValueKind.ANGLE, 0.0),
        "Height": (ValueKind.LENGTH, None),
        "Radius": (ValueKind.LENGTH, None),
        "MapMode": (ValueKind.INTEGER, 0),
        "MapPathParameter": (ValueKind.NUMBER, 0.0),
        "MapReversed": (ValueKind.BOOLEAN, False),
        "Visibility": (ValueKind.BOOLEAN, True),
    }
    if not set(ExpectedData) <= set(PathData) or any(
        not _freecad_parameter_matches(PathData[PathName], KindData, ValueData)
        for PathName, (KindData, ValueData) in ExpectedData.items()
        if ValueData is not None
    ):
        return None
    RadiusData = _parameter_dimension(PathData["Radius"])
    HeightData = _parameter_dimension(PathData["Height"])
    if RadiusData is None or HeightData is None:
        return None
    RadiusValue = RadiusData.value_mm
    HeightValue = HeightData.value_mm
    if (
        not math.isfinite(RadiusValue)
        or RadiusValue <= 0.0
        or not math.isfinite(HeightValue)
        or HeightValue <= 0.0
        or not _IsFreeCadIdentityPlacement(DefinitionData.object_data, "Placement")
        or not _IsFreeCadIdentityPlacement(
            DefinitionData.object_data,
            "AttachmentOffset",
        )
        or not HasCadCylBrep(DocumentData, RadiusValue, HeightValue)
    ):
        return None
    SketchPayload = bytearray(_plane_reference(2))
    SketchPayload.extend(_coordinate_marker((0.0, 0.0), 1, _CIRCLE_LOCUS))
    SketchPayload.extend(_coordinate_marker((RadiusValue, 0.0), 2, _POINT_LOCUS))
    SketchSourceId = f"{FeatureData.id}:cylinder-profile"
    ObjectIds[f"sketch:{SketchSourceId}"] = 26
    ObjectIds[f"feature:{FeatureData.id}"] = 33
    ExtrusionData = replace(
        FeatureData,
        kind=FeatureKind.EXTRUSION,
        sketch_id=SketchSourceId,
        operation=BooleanOperation.CREATE,
        definition=ExtrusionFeature(
            ParameterValue(HeightValue, ValueKind.LENGTH, "mm"),
        ),
    )
    return (
        _WriteObject(
            SketchSourceId,
            26,
            "Sketch1",
            "Sketch",
            "Sketch",
            "moProfileFeature_c",
            (("Dissectable", "true"),),
            (
                replace(
                    RadiusData,
                    name="D1",
                    value_mm=RadiusValue * 2.0,
                    text="<MOD-DIAM>" + format(RadiusValue * 2.0, ".15g"),
                ),
            ),
            bytes(SketchPayload),
        ),
        _WriteObject(
            FeatureData.id,
            33,
            "Boss-Extrude1",
            "Extrusion",
            "Extrusion",
            "moExtrusion_c",
            (
                ("Dissectable", "true"),
                ("DissectableChildren", "26"),
                ("DissectableRoot", "true"),
                ("KitPrimitive", "Cylinder"),
            ),
            (
                replace(
                    HeightData,
                    name="D1",
                    text=format(HeightValue, ".15g"),
                ),
            ),
            _extrusion_payload(ExtrusionData),
        ),
    )


def _write_objects(
    document: CadDocument, object_ids: dict[str, int]
) -> tuple[_WriteObject, ...]:
    parameters = {parameter.id: parameter for parameter in document.parameters}
    BoxObjects = _FreeCadBoxObjects(document, object_ids)
    if BoxObjects is not None:
        return BoxObjects
    CylinderObjects = BuildCadCylObjs(document, object_ids)
    if CylinderObjects is not None:
        return CylinderObjects
    result: list[_WriteObject] = []
    for plane in document.support_planes:
        object_id = object_ids[f"plane:{plane.id}"]
        if object_id in {2, 3, 4}:
            continue
        dimensions = _write_dimensions(
            plane.id,
            (plane.offset_parameter_id,) if plane.offset_parameter_id else (),
            parameters,
        )
        result.append(
            _WriteObject(
                plane.id,
                object_id,
                plane.name,
                "Feature",
                "Plane",
                "moRefPlane_c",
                dimensions=dimensions,
                payload=_plane_payload(plane),
            )
        )
    sketches = {sketch.id: sketch for sketch in document.sketches}
    emitted_sketches: set[str] = set()
    for feature in sorted(document.feature_timeline, key=lambda item: item.order):
        if _is_native_system_feature(feature):
            continue
        if feature.sketch_id is not None and feature.sketch_id in sketches:
            sketch = sketches[feature.sketch_id]
            if sketch.id not in emitted_sketches:
                result.append(_write_sketch(sketch, parameters, object_ids, feature))
                emitted_sketches.add(sketch.id)
        feature_id = object_ids[f"feature:{feature.id}"]
        if any(item.object_id == feature_id for item in result):
            continue
        result.append(_write_feature(feature, parameters, object_ids))
    for sketch in document.sketches:
        if sketch.id not in emitted_sketches:
            result.append(_write_sketch(sketch, parameters, object_ids))
    return tuple(result)


def _equation_identifier(value: str) -> str:
    cleaned = _EQUATION_IDENTIFIER.sub("_", value).strip("_")
    return f"Kit_{cleaned}" if cleaned else ""


def _equation_literal(value: ParameterValue) -> str | None:
    if not isinstance(value.value, (int, float)) or isinstance(value.value, bool):
        return None
    if not math.isfinite(float(value.value)):
        return None
    rendered = format(float(value.value), ".15g")
    if value.kind is ValueKind.LENGTH:
        return f"{rendered}mm"
    if value.kind is ValueKind.NUMBER:
        return rendered
    return None


def _expression_parameters(document: CadDocument) -> tuple[Parameter, ...]:
    return tuple(
        parameter
        for parameter in document.parameters
        if parameter.expression is not None
    )


def expression_equation_texts(document: CadDocument) -> tuple[str, ...] | None:
    parameters = _expression_parameters(document)
    if not parameters:
        return ()
    names: dict[str, str] = {}
    used: set[str] = set()

    def identifier(key: str, source: str) -> str | None:
        if key in names:
            return names[key]
        base = _equation_identifier(source)
        if not base:
            return None
        candidate = base
        suffix = 2
        while candidate in used:
            candidate = f"{base}_{suffix}"
            suffix += 1
        used.add(candidate)
        names[key] = candidate
        return candidate

    references: list[tuple[str, str]] = []
    values: dict[str, str] = {}
    bindings: list[tuple[str, str]] = []
    for parameter in parameters:
        expression = parameter.expression
        if expression is None:
            return None
        source = expression.source.strip()
        if not _EQUATION_REFERENCE_SOURCE.fullmatch(source):
            return None
        literal = _equation_literal(parameter.value)
        if literal is None:
            return None
        reference = identifier(f"reference:{source}", source)
        driven = identifier(f"parameter:{parameter.id}", parameter.name)
        if reference is None or driven is None or reference == driven:
            return None
        if reference in values:
            if values[reference] != literal:
                return None
        else:
            values[reference] = literal
            references.append((reference, literal))
        bindings.append((driven, reference))
    texts = [f'"{name}"= {literal}' for name, literal in references]
    texts.extend(f'"{driven}"= "{reference}"' for driven, reference in bindings)
    if len(set(texts)) != len(texts):
        return None
    return tuple(texts)


def _repair_plane_object_ids(object_ids: dict[str, int]) -> None:
    reserved = frozenset(range(1, 26))
    taken = {
        value
        for key, value in object_ids.items()
        if not key.startswith(("plane:", "configuration:"))
    }
    next_id = 26
    for key in tuple(object_ids):
        if not key.startswith("plane:"):
            continue
        value = object_ids[key]
        if value in {2, 3, 4} and value not in taken:
            taken.add(value)
            continue
        if value not in taken and value not in reserved:
            taken.add(value)
            continue
        while next_id in taken or next_id in reserved:
            next_id += 1
        object_ids[key] = next_id
        taken.add(next_id)


# canonical object identities close cross-stream references for each proved history shape
def _CanonicalExtrusionObjects(
    ObjectsData: tuple[_WriteObject, ...],
    ObjectIds: dict[str, int],
    DocumentData: CadDocument,
) -> tuple[_WriteObject, ...]:
    if len(ObjectsData) == 2 and ObjectsData[1].class_name == "moRevolution_c":
        return _CanonicalSingleRevolutionObjects(
            ObjectsData,
            ObjectIds,
            DocumentData,
        )
    if len(ObjectsData) in {6, 8}:
        return _CanonicalCutChainObjects(ObjectsData, ObjectIds, DocumentData)
    if len(ObjectsData) == 4:
        if ObjectsData[3].class_name == "moRevolution_c":
            return _CanonicalPadGrooveObjects(
                ObjectsData,
                ObjectIds,
                DocumentData,
            )
        return _CanonicalTwoFeatureObjects(ObjectsData, ObjectIds, DocumentData)
    if len(ObjectsData) == 3 and ObjectsData[2].class_name == "Fillet_c":
        return _CanonicalBossFilletObjects(ObjectsData, ObjectIds, DocumentData)
    if len(ObjectsData) == 3 and ObjectsData[2].class_name == "Chamfer_c":
        return _CanonicalBossChamferObjects(ObjectsData, ObjectIds, DocumentData)
    if len(ObjectsData) == 3 and ObjectsData[2].class_name == "moShell_c":
        return _CanonicalBossShellObjects(ObjectsData, ObjectIds, DocumentData)
    if len(ObjectsData) == 3 and ObjectsData[2].class_name == "moLPattern_c":
        return _CanonicalBossLinearPatternObjects(
            ObjectsData,
            ObjectIds,
            DocumentData,
        )
    if len(ObjectsData) == 3 and ObjectsData[2].class_name == "moCirPattern_c":
        return _CanonicalBossCircularPatternObjects(
            ObjectsData,
            ObjectIds,
            DocumentData,
        )
    return _CanonicalSingleBossObjects(ObjectsData, ObjectIds, DocumentData)


# canonical revolution identities bind the traced profile, axis, and angle records
def _CanonicalSingleRevolutionObjects(
    ObjectsData: tuple[_WriteObject, ...],
    ObjectIds: dict[str, int],
    DocumentData: CadDocument,
) -> tuple[_WriteObject, ...]:
    if len(ObjectsData) != 2:
        return ObjectsData
    SketchObject, RevolveObject = ObjectsData
    SourceSketch = next(
        (
            ItemData
            for ItemData in DocumentData.sketches
            if ItemData.id == SketchObject.source_id
        ),
        None,
    )
    SourceFeature = next(
        (
            ItemData
            for ItemData in DocumentData.feature_timeline
            if ItemData.id == RevolveObject.source_id
        ),
        None,
    )
    if SourceSketch is None or SourceFeature is None:
        return ObjectsData
    NormalizedSketch = _CanonicalPrincipalSketch(
        SourceSketch,
        DocumentData.support_planes,
        ObjectIds,
    )
    SketchPayload, _ = _sketch_payload(
        NormalizedSketch,
        SketchObject.object_id,
        ObjectIds,
    )
    SketchObject = replace(SketchObject, payload=SketchPayload)
    BoundsValue = _write_rectangle_bounds(SketchObject)
    AngleDimension = _FreeCadSingleRevolutionDimension(
        DocumentData,
        SourceSketch,
        SourceFeature,
    )
    PlaneObjectId = (
        struct.unpack_from("<I", SketchObject.payload)[0]
        if len(SketchObject.payload) >= 4
        else 0
    )
    if (
        PlaneObjectId != 2
        or BoundsValue is None
        or SketchObject.class_name != "moProfileFeature_c"
        or not HasRectDims(SketchObject, BoundsValue)
        or SourceSketch.suppressed
        or not HasCanonicalSketchGeometry(SourceSketch, BoundsValue, None)
        or len(SourceSketch.closed_profile_entity_ids) != 1
        or set(SourceSketch.closed_profile_entity_ids[0])
        != {ItemData.id for ItemData in SourceSketch.entities}
        or RevolveObject.class_name != "moRevolution_c"
        or AngleDimension is None
    ):
        return ObjectsData
    ObjectIds[f"sketch:{SketchObject.source_id}"] = 26
    ObjectIds[f"feature:{RevolveObject.source_id}"] = 31
    return (
        replace(SketchObject, object_id=26, name="Sketch1"),
        replace(
            RevolveObject,
            object_id=31,
            name="Revolve1",
            dimensions=(AngleDimension,),
        ),
    )


# mixed pad-groove canonicalization binds both profiles and the horizontal sketch axis
def _CanonicalPadGrooveObjects(
    ObjectsData: tuple[_WriteObject, ...],
    ObjectIds: dict[str, int],
    DocumentData: CadDocument,
) -> tuple[_WriteObject, ...]:
    if len(ObjectsData) != 4:
        return ObjectsData
    SketchOne, PadObject, SketchTwo, GrooveObject = ObjectsData
    SourceSketches = tuple(
        next(
            (
                ItemData
                for ItemData in DocumentData.sketches
                if ItemData.id == SketchObject.source_id
            ),
            None,
        )
        for SketchObject in (SketchOne, SketchTwo)
    )
    SourceFeatures = tuple(
        next(
            (
                ItemData
                for ItemData in DocumentData.feature_timeline
                if ItemData.id == FeatureObject.source_id
            ),
            None,
        )
        for FeatureObject in (PadObject, GrooveObject)
    )
    if any(ItemData is None for ItemData in (*SourceSketches, *SourceFeatures)):
        return ObjectsData
    SourceSketchOne, SourceSketchTwo = SourceSketches
    SourcePad, SourceGroove = SourceFeatures
    if (
        SourceSketchOne is None
        or SourceSketchTwo is None
        or SourcePad is None
        or SourceGroove is None
    ):
        return ObjectsData
    NormalizedSketches = tuple(
        _CanonicalPrincipalSketch(ItemData, DocumentData.support_planes, ObjectIds)
        for ItemData in (SourceSketchOne, SourceSketchTwo)
    )
    SketchPayloads = tuple(
        _sketch_payload(SketchData, SketchObject.object_id, ObjectIds)[0]
        for SketchData, SketchObject in zip(
            NormalizedSketches,
            (SketchOne, SketchTwo),
            strict=True,
        )
    )
    SketchOne = replace(SketchOne, payload=SketchPayloads[0])
    SketchTwo = replace(SketchTwo, payload=SketchPayloads[1])
    NormalizedPad = _CanonicalPrincipalExtrusion(
        SourcePad,
        SourceSketchOne,
        DocumentData.support_planes,
        ObjectIds,
    )
    PadObject = replace(PadObject, payload=_extrusion_payload(NormalizedPad))
    BoundsData = (
        _write_rectangle_bounds(SketchOne),
        _write_rectangle_bounds(SketchTwo),
    )
    DimensionData = _FreeCadPadGrooveDimensions(
        DocumentData,
        (SourceSketchOne, SourceSketchTwo),
        (SourcePad, SourceGroove),
    )
    if (
        PadObject.class_name != "moExtrusion_c"
        or GrooveObject.class_name != "moRevolution_c"
        or any(ItemData is None for ItemData in BoundsData)
        or ExtrusionEditCodes(PadObject.payload) is None
        or DimensionData is None
        or any(
            len(SketchObject.payload) < 4
            or struct.unpack_from("<I", SketchObject.payload)[0] != 2
            or SketchObject.class_name != "moProfileFeature_c"
            or not HasRectDims(SketchObject, BoundsValue)
            or SketchData.suppressed
            or not HasCanonicalSketchGeometry(SketchData, BoundsValue, None)
            or len(SketchData.closed_profile_entity_ids) != 1
            or set(SketchData.closed_profile_entity_ids[0])
            != {ItemData.id for ItemData in SketchData.entities}
            for SketchObject, SketchData, BoundsValue in zip(
                (SketchOne, SketchTwo),
                (SourceSketchOne, SourceSketchTwo),
                BoundsData,
                strict=True,
            )
        )
    ):
        return ObjectsData
    TargetIds = (26, 32, 33, 39)
    for SourceObject, TargetId in zip(
        (SketchOne, PadObject, SketchTwo, GrooveObject),
        TargetIds,
        strict=True,
    ):
        PrefixValue = "sketch" if SourceObject.kind == "Sketch" else "feature"
        ObjectIds[f"{PrefixValue}:{SourceObject.source_id}"] = TargetId
    PadDimension, GrooveDimension = DimensionData
    return (
        replace(SketchOne, object_id=26, name="Sketch1"),
        replace(
            PadObject,
            object_id=32,
            name="Boss-Extrude1",
            dimensions=(replace(PadDimension, name="D1"),),
        ),
        replace(SketchTwo, object_id=33, name="Sketch2"),
        replace(
            GrooveObject,
            object_id=39,
            name="Cut-Revolve1",
            kind="Cut-Revolve",
            dimensions=(GrooveDimension,),
        ),
    )


# boss-fillet canonicalization binds the source edge topology to native local edge three
def _CanonicalBossFilletObjects(
    ObjectsData: tuple[_WriteObject, ...],
    ObjectIds: dict[str, int],
    DocumentData: CadDocument,
) -> tuple[_WriteObject, ...]:
    if len(ObjectsData) != 3:
        return ObjectsData
    SketchObject, PadObject, FilletObject = ObjectsData
    SourceSketch = next(
        (
            ItemData
            for ItemData in DocumentData.sketches
            if ItemData.id == SketchObject.source_id
        ),
        None,
    )
    SourceFeatures = tuple(
        ItemData
        for ItemData in sorted(
            DocumentData.feature_timeline,
            key=lambda ItemData: ItemData.order,
        )
        if not _is_native_system_feature(ItemData)
    )
    if SourceSketch is None or len(SourceFeatures) != 2:
        return ObjectsData
    SourcePad, SourceFillet = SourceFeatures
    if SourcePad.id != PadObject.source_id or SourceFillet.id != FilletObject.source_id:
        return ObjectsData
    NormalizedSketch = _CanonicalPrincipalSketch(
        SourceSketch,
        DocumentData.support_planes,
        ObjectIds,
    )
    SketchPayload, _ = _sketch_payload(
        NormalizedSketch,
        SketchObject.object_id,
        ObjectIds,
    )
    SketchObject = replace(SketchObject, payload=SketchPayload)
    NormalizedPad = _CanonicalPrincipalExtrusion(
        SourcePad,
        SourceSketch,
        DocumentData.support_planes,
        ObjectIds,
    )
    PadObject = replace(PadObject, payload=_extrusion_payload(NormalizedPad))
    BoundsValue = _write_rectangle_bounds(SketchObject)
    DimensionData = _FreeCadBossFilletDimensions(
        DocumentData,
        SourceSketch,
        SourcePad,
        SourceFillet,
        BoundsValue,
    )
    if (
        BoundsValue is None
        or len(SketchObject.payload) < 4
        or struct.unpack_from("<I", SketchObject.payload)[0] != 2
        or SketchObject.class_name != "moProfileFeature_c"
        or not HasRectDims(SketchObject, BoundsValue)
        or SourceSketch.suppressed
        or not HasCanonicalSketchGeometry(SourceSketch, BoundsValue, None)
        or len(SourceSketch.closed_profile_entity_ids) != 1
        or set(SourceSketch.closed_profile_entity_ids[0])
        != {ItemData.id for ItemData in SourceSketch.entities}
        or PadObject.class_name != "moExtrusion_c"
        or ExtrusionEditCodes(PadObject.payload) != (0, 0)
        or FilletObject.class_name != "Fillet_c"
        or DimensionData is None
    ):
        return ObjectsData
    PadDimension, FilletDimension = DimensionData
    ObjectIds[f"sketch:{SketchObject.source_id}"] = 26
    ObjectIds[f"feature:{PadObject.source_id}"] = 32
    ObjectIds[f"feature:{FilletObject.source_id}"] = 34
    return (
        replace(SketchObject, object_id=26, name="Sketch1"),
        replace(
            PadObject,
            object_id=32,
            name="Boss-Extrude1",
            dimensions=(replace(PadDimension, name="D1"),),
        ),
        replace(
            FilletObject,
            object_id=34,
            name="Fillet1",
            dimensions=(FilletDimension,),
            payload=_FilletSelectionRecord(32, 3),
        ),
    )


# boss-chamfer canonicalization binds the source edge topology to native local edge three
def _CanonicalBossChamferObjects(
    ObjectsData: tuple[_WriteObject, ...],
    ObjectIds: dict[str, int],
    DocumentData: CadDocument,
) -> tuple[_WriteObject, ...]:
    if len(ObjectsData) != 3:
        return ObjectsData
    SketchObject, PadObject, ChamferObject = ObjectsData
    SourceSketch = next(
        (
            ItemData
            for ItemData in DocumentData.sketches
            if ItemData.id == SketchObject.source_id
        ),
        None,
    )
    SourceFeatures = tuple(
        ItemData
        for ItemData in sorted(
            DocumentData.feature_timeline,
            key=lambda ItemData: ItemData.order,
        )
        if not _is_native_system_feature(ItemData)
    )
    if SourceSketch is None or len(SourceFeatures) != 2:
        return ObjectsData
    SourcePad, SourceChamfer = SourceFeatures
    if (
        SourcePad.id != PadObject.source_id
        or SourceChamfer.id != ChamferObject.source_id
    ):
        return ObjectsData
    NormalizedSketch = _CanonicalPrincipalSketch(
        SourceSketch,
        DocumentData.support_planes,
        ObjectIds,
    )
    SketchPayload, _ = _sketch_payload(
        NormalizedSketch,
        SketchObject.object_id,
        ObjectIds,
    )
    SketchObject = replace(SketchObject, payload=SketchPayload)
    NormalizedPad = _CanonicalPrincipalExtrusion(
        SourcePad,
        SourceSketch,
        DocumentData.support_planes,
        ObjectIds,
    )
    PadObject = replace(PadObject, payload=_extrusion_payload(NormalizedPad))
    BoundsValue = _write_rectangle_bounds(SketchObject)
    DimensionData = _FreeCadBossChamferDimensions(
        DocumentData,
        SourceSketch,
        SourcePad,
        SourceChamfer,
        BoundsValue,
    )
    if (
        BoundsValue is None
        or len(SketchObject.payload) < 4
        or struct.unpack_from("<I", SketchObject.payload)[0] != 2
        or SketchObject.class_name != "moProfileFeature_c"
        or not HasRectDims(SketchObject, BoundsValue)
        or SourceSketch.suppressed
        or not HasCanonicalSketchGeometry(SourceSketch, BoundsValue, None)
        or len(SourceSketch.closed_profile_entity_ids) != 1
        or set(SourceSketch.closed_profile_entity_ids[0])
        != {ItemData.id for ItemData in SourceSketch.entities}
        or PadObject.class_name != "moExtrusion_c"
        or ExtrusionEditCodes(PadObject.payload) != (0, 0)
        or ChamferObject.class_name != "Chamfer_c"
        or DimensionData is None
    ):
        return ObjectsData
    PadDimension, ChamferDimension = DimensionData
    ObjectIds[f"sketch:{SketchObject.source_id}"] = 26
    ObjectIds[f"feature:{PadObject.source_id}"] = 32
    ObjectIds[f"feature:{ChamferObject.source_id}"] = 35
    return (
        replace(SketchObject, object_id=26, name="Sketch1"),
        replace(
            PadObject,
            object_id=32,
            name="Boss-Extrude1",
            dimensions=(replace(PadDimension, name="D1"),),
        ),
        replace(
            ChamferObject,
            object_id=35,
            name="Chamfer1",
            dimensions=(ChamferDimension,),
            payload=_FilletSelectionRecord(32, 3),
        ),
    )


# boss-shell canonicalization binds the source top face to the recovered shell face pair
def _CanonicalBossShellObjects(
    ObjectsData: tuple[_WriteObject, ...],
    ObjectIds: dict[str, int],
    DocumentData: CadDocument,
) -> tuple[_WriteObject, ...]:
    if len(ObjectsData) != 3:
        return ObjectsData
    SketchObject, PadObject, ShellObject = ObjectsData
    SourceSketch = next(
        (
            ItemData
            for ItemData in DocumentData.sketches
            if ItemData.id == SketchObject.source_id
        ),
        None,
    )
    SourceFeatures = tuple(
        ItemData
        for ItemData in sorted(
            DocumentData.feature_timeline,
            key=lambda ItemData: ItemData.order,
        )
        if not _is_native_system_feature(ItemData)
    )
    if SourceSketch is None or len(SourceFeatures) != 2:
        return ObjectsData
    SourcePad, SourceShell = SourceFeatures
    if SourcePad.id != PadObject.source_id or SourceShell.id != ShellObject.source_id:
        return ObjectsData
    NormalizedSketch = _CanonicalPrincipalSketch(
        SourceSketch,
        DocumentData.support_planes,
        ObjectIds,
    )
    SketchPayload, _ = _sketch_payload(
        NormalizedSketch,
        SketchObject.object_id,
        ObjectIds,
    )
    SketchObject = replace(SketchObject, payload=SketchPayload)
    NormalizedPad = _CanonicalPrincipalExtrusion(
        SourcePad,
        SourceSketch,
        DocumentData.support_planes,
        ObjectIds,
    )
    PadObject = replace(PadObject, payload=_extrusion_payload(NormalizedPad))
    BoundsValue = _write_rectangle_bounds(SketchObject)
    DimensionData = _FreeCadBossShellDimensions(
        DocumentData,
        SourceSketch,
        SourcePad,
        SourceShell,
        BoundsValue,
    )
    if (
        BoundsValue is None
        or len(SketchObject.payload) < 4
        or struct.unpack_from("<I", SketchObject.payload)[0] != 2
        or SketchObject.class_name != "moProfileFeature_c"
        or not HasRectDims(SketchObject, BoundsValue)
        or SourceSketch.suppressed
        or not HasCanonicalSketchGeometry(SourceSketch, BoundsValue, None)
        or len(SourceSketch.closed_profile_entity_ids) != 1
        or set(SourceSketch.closed_profile_entity_ids[0])
        != {ItemData.id for ItemData in SourceSketch.entities}
        or PadObject.class_name != "moExtrusion_c"
        or ExtrusionEditCodes(PadObject.payload) != (0, 0)
        or ShellObject.class_name != "moShell_c"
        or DimensionData is None
    ):
        return ObjectsData
    PadDimension, ShellDimension = DimensionData
    ObjectIds[f"sketch:{SketchObject.source_id}"] = 26
    ObjectIds[f"feature:{PadObject.source_id}"] = 32
    ObjectIds[f"feature:{ShellObject.source_id}"] = 34
    return (
        replace(SketchObject, object_id=26, name="Sketch1"),
        replace(
            PadObject,
            object_id=32,
            name="Boss-Extrude1",
            dimensions=(replace(PadDimension, name="D1"),),
        ),
        replace(
            ShellObject,
            object_id=34,
            name="Shell1",
            dimensions=(ShellDimension,),
            payload=_ShellSelectionRecord(32),
        ),
    )


# boss-pattern canonicalization binds the source sketch normal to native linear spacing
def _CanonicalBossLinearPatternObjects(
    ObjectsData: tuple[_WriteObject, ...],
    ObjectIds: dict[str, int],
    DocumentData: CadDocument,
) -> tuple[_WriteObject, ...]:
    if len(ObjectsData) != 3:
        return ObjectsData
    SketchObject, PadObject, PatternObject = ObjectsData
    SourceSketch = next(
        (
            ItemData
            for ItemData in DocumentData.sketches
            if ItemData.id == SketchObject.source_id
        ),
        None,
    )
    SourceFeatures = tuple(
        ItemData
        for ItemData in sorted(
            DocumentData.feature_timeline,
            key=lambda ItemData: ItemData.order,
        )
        if not _is_native_system_feature(ItemData)
    )
    if SourceSketch is None or len(SourceFeatures) != 2:
        return ObjectsData
    SourcePad, SourcePattern = SourceFeatures
    if (
        SourcePad.id != PadObject.source_id
        or SourcePattern.id != PatternObject.source_id
    ):
        return ObjectsData
    NormalizedSketch = _CanonicalPrincipalSketch(
        SourceSketch,
        DocumentData.support_planes,
        ObjectIds,
    )
    SketchPayload, _ = _sketch_payload(
        NormalizedSketch,
        SketchObject.object_id,
        ObjectIds,
    )
    SketchObject = replace(SketchObject, payload=SketchPayload)
    NormalizedPad = _CanonicalPrincipalExtrusion(
        SourcePad,
        SourceSketch,
        DocumentData.support_planes,
        ObjectIds,
    )
    PadObject = replace(PadObject, payload=_extrusion_payload(NormalizedPad))
    BoundsValue = _write_rectangle_bounds(SketchObject)
    DimensionData = _FreeCadBossLinearPatternDimensions(
        DocumentData,
        SourceSketch,
        SourcePad,
        SourcePattern,
        BoundsValue,
    )
    if (
        BoundsValue is None
        or len(SketchObject.payload) < 4
        or struct.unpack_from("<I", SketchObject.payload)[0] != 2
        or SketchObject.class_name != "moProfileFeature_c"
        or not HasRectDims(SketchObject, BoundsValue)
        or SourceSketch.suppressed
        or not HasCanonicalSketchGeometry(SourceSketch, BoundsValue, None)
        or len(SourceSketch.closed_profile_entity_ids) != 1
        or set(SourceSketch.closed_profile_entity_ids[0])
        != {ItemData.id for ItemData in SourceSketch.entities}
        or PadObject.class_name != "moExtrusion_c"
        or ExtrusionEditCodes(PadObject.payload) != (0, 0)
        or PatternObject.class_name != "moLPattern_c"
        or DimensionData is None
    ):
        return ObjectsData
    PadDimension, CountDimension, SpacingDimension = DimensionData
    ObjectIds[f"sketch:{SketchObject.source_id}"] = 26
    ObjectIds[f"feature:{PadObject.source_id}"] = 32
    ObjectIds[f"feature:{PatternObject.source_id}"] = 40
    return (
        replace(SketchObject, object_id=26, name="Sketch1"),
        replace(
            PadObject,
            object_id=32,
            name="Boss-Extrude1",
            dimensions=(replace(PadDimension, name="D1"),),
        ),
        replace(
            PatternObject,
            object_id=40,
            name="LPattern1",
            kind="LPattern",
            dimensions=(CountDimension, SpacingDimension),
            payload=b"",
        ),
    )


# circular-pattern canonicalization binds the sketch-normal axis and angular span
def _CanonicalBossCircularPatternObjects(
    ObjectsData: tuple[_WriteObject, ...],
    ObjectIds: dict[str, int],
    DocumentData: CadDocument,
) -> tuple[_WriteObject, ...]:
    if len(ObjectsData) != 3:
        return ObjectsData
    SketchObject, PadObject, PatternObject = ObjectsData
    SourceSketch = next(
        (
            ItemData
            for ItemData in DocumentData.sketches
            if ItemData.id == SketchObject.source_id
        ),
        None,
    )
    SourceFeatures = tuple(
        ItemData
        for ItemData in sorted(
            DocumentData.feature_timeline,
            key=lambda ItemData: ItemData.order,
        )
        if not _is_native_system_feature(ItemData)
    )
    if SourceSketch is None or len(SourceFeatures) != 2:
        return ObjectsData
    SourcePad, SourcePattern = SourceFeatures
    if (
        SourcePad.id != PadObject.source_id
        or SourcePattern.id != PatternObject.source_id
    ):
        return ObjectsData
    NormalizedSketch = _CanonicalPrincipalSketch(
        SourceSketch,
        DocumentData.support_planes,
        ObjectIds,
    )
    SketchPayload, _ = _sketch_payload(
        NormalizedSketch,
        SketchObject.object_id,
        ObjectIds,
    )
    SketchObject = replace(SketchObject, payload=SketchPayload)
    NormalizedPad = _CanonicalPrincipalExtrusion(
        SourcePad,
        SourceSketch,
        DocumentData.support_planes,
        ObjectIds,
    )
    PadObject = replace(PadObject, payload=_extrusion_payload(NormalizedPad))
    BoundsValue = _write_rectangle_bounds(SketchObject)
    DimensionData = _FreeCadBossCircularPatternDimensions(
        DocumentData,
        SourceSketch,
        SourcePad,
        SourcePattern,
        BoundsValue,
    )
    if (
        BoundsValue is None
        or len(SketchObject.payload) < 4
        or struct.unpack_from("<I", SketchObject.payload)[0] != 2
        or SketchObject.class_name != "moProfileFeature_c"
        or not HasRectDims(SketchObject, BoundsValue)
        or SourceSketch.suppressed
        or not HasCanonicalSketchGeometry(SourceSketch, BoundsValue, None)
        or len(SourceSketch.closed_profile_entity_ids) != 1
        or set(SourceSketch.closed_profile_entity_ids[0])
        != {ItemData.id for ItemData in SourceSketch.entities}
        or PadObject.class_name != "moExtrusion_c"
        or ExtrusionEditCodes(PadObject.payload) != (0, 0)
        or PatternObject.class_name != "moCirPattern_c"
        or DimensionData is None
    ):
        return ObjectsData
    PadDimension, CountDimension, AngleDimension = DimensionData
    ObjectIds[f"sketch:{SketchObject.source_id}"] = 26
    ObjectIds[f"feature:{PadObject.source_id}"] = 32
    ObjectIds[f"feature:{PatternObject.source_id}"] = 46
    return (
        replace(SketchObject, object_id=26, name="Sketch1"),
        replace(
            PadObject,
            object_id=32,
            name="Boss-Extrude1",
            dimensions=(replace(PadDimension, name="D1"),),
        ),
        replace(
            PatternObject,
            object_id=46,
            name="CirPattern1",
            kind="CirPattern",
            dimensions=(CountDimension, AngleDimension),
            payload=b"",
        ),
    )


# a canonical single-pad identity preserves the established one-feature programs
def _CanonicalSingleBossObjects(
    objects: tuple[_WriteObject, ...],
    object_ids: dict[str, int],
    document: CadDocument,
) -> tuple[_WriteObject, ...]:
    if len(objects) != 2:
        return objects
    sketch, extrusion = objects
    source_sketch = next(
        (item for item in document.sketches if item.id == sketch.source_id), None
    )
    source_feature = next(
        (item for item in document.feature_timeline if item.id == extrusion.source_id),
        None,
    )
    if source_sketch is not None:
        NormalizedSketch = _CanonicalPrincipalSketch(
            source_sketch,
            document.support_planes,
            object_ids,
        )
        NormalizedPayload, _ = _sketch_payload(
            NormalizedSketch,
            sketch.object_id,
            object_ids,
        )
        sketch = replace(sketch, payload=NormalizedPayload)
    if source_feature is not None and source_sketch is not None:
        NormalizedFeature = _CanonicalPrincipalExtrusion(
            source_feature,
            source_sketch,
            document.support_planes,
            object_ids,
        )
        extrusion = replace(extrusion, payload=_extrusion_payload(NormalizedFeature))
    bounds = _write_rectangle_bounds(sketch)
    circle = _write_circle_profile(sketch)
    if (
        len(sketch.payload) < 4
        or struct.unpack_from("<I", sketch.payload)[0] not in {2, 3, 4}
        or sketch.class_name != "moProfileFeature_c"
        or not (
            HasRectDims(sketch, bounds)
            if bounds is not None
            else HasCircleDims(sketch, circle)
        )
        or extrusion.class_name != "moExtrusion_c"
        or ExtrusionEditCodes(extrusion.payload) is None
        or source_sketch is None
        or source_sketch.suppressed
        or not HasCanonicalSketchGeometry(source_sketch, bounds, circle)
        or len(source_sketch.closed_profile_entity_ids) != 1
        or set(source_sketch.closed_profile_entity_ids[0])
        != {item.id for item in source_sketch.entities}
        or source_feature is None
        or source_feature.suppressed
        or source_feature.input_feature_ids
        or source_feature.selection_ids
        or source_feature.configuration_states
    ):
        return objects
    freecad_dimension = _freecad_single_boss_dimension(
        document,
        source_sketch,
        source_feature,
    )
    if freecad_dimension is None:
        if (
            sketch.object_id != 26
            or sketch.name != "Sketch1"
            or extrusion.name != "Boss-Extrude1"
            or len(extrusion.dimensions) != 1
            or extrusion.dimensions[0].name != "D1"
            or not math.isfinite(extrusion.dimensions[0].value_mm)
            or extrusion.dimensions[0].value_mm <= 0.0
        ):
            return objects
        source_dimension = extrusion.dimensions[0]
    else:
        source_dimension = freecad_dimension
    dimension = replace(
        source_dimension,
        name="D1",
        text=format(source_dimension.value_mm, ".15g"),
    )
    if circle is not None:
        CircleDimension = sketch.dimensions[0]
        DiameterValue = circle[2] * 2.0
        sketch = replace(
            sketch,
            dimensions=(
                replace(
                    CircleDimension,
                    name="D1",
                    value_mm=DiameterValue,
                    text="<MOD-DIAM>" + format(DiameterValue, ".15g"),
                ),
            ),
        )
    FeatureObjectId = 33 if circle is not None else 32
    object_ids[f"sketch:{sketch.source_id}"] = 26
    object_ids[f"feature:{extrusion.source_id}"] = FeatureObjectId
    return (
        replace(sketch, object_id=26, name="Sketch1"),
        replace(
            extrusion,
            object_id=FeatureObjectId,
            name="Boss-Extrude1",
            dimensions=(dimension,),
        ),
    )


# two-feature canonicalization binds FreeCAD pad-pocket semantics to recovered native ids
def _CanonicalTwoFeatureObjects(
    ObjectsData: tuple[_WriteObject, ...],
    ObjectIds: dict[str, int],
    DocumentData: CadDocument,
) -> tuple[_WriteObject, ...]:
    if len(ObjectsData) != 4:
        return ObjectsData
    SketchOne, FeatureOne, SketchTwo, FeatureTwo = ObjectsData
    SourceSketches = tuple(
        next(
            (
                ItemData
                for ItemData in DocumentData.sketches
                if ItemData.id == SketchObject.source_id
            ),
            None,
        )
        for SketchObject in (SketchOne, SketchTwo)
    )
    SourceFeatures = tuple(
        next(
            (
                ItemData
                for ItemData in DocumentData.feature_timeline
                if ItemData.id == FeatureObject.source_id
            ),
            None,
        )
        for FeatureObject in (FeatureOne, FeatureTwo)
    )
    if any(ItemData is None for ItemData in (*SourceSketches, *SourceFeatures)):
        return ObjectsData
    SourceSketchOne, SourceSketchTwo = SourceSketches
    SourceFeatureOne, SourceFeatureTwo = SourceFeatures
    if (
        SourceSketchOne is None
        or SourceSketchTwo is None
        or SourceFeatureOne is None
        or SourceFeatureTwo is None
    ):
        return ObjectsData
    NormalizedSketches = tuple(
        _CanonicalPrincipalSketch(ItemData, DocumentData.support_planes, ObjectIds)
        for ItemData in (SourceSketchOne, SourceSketchTwo)
    )
    NormalizedFeatures = tuple(
        _CanonicalPrincipalExtrusion(
            FeatureData,
            SketchData,
            DocumentData.support_planes,
            ObjectIds,
        )
        for FeatureData, SketchData in zip(
            (SourceFeatureOne, SourceFeatureTwo),
            (SourceSketchOne, SourceSketchTwo),
            strict=True,
        )
    )
    NormalizedObjects: list[_WriteObject] = []
    for SketchObject, FeatureObject, SketchData, FeatureData in zip(
        (SketchOne, SketchTwo),
        (FeatureOne, FeatureTwo),
        NormalizedSketches,
        NormalizedFeatures,
        strict=True,
    ):
        SketchPayload, _ = _sketch_payload(
            SketchData, SketchObject.object_id, ObjectIds
        )
        NormalizedObjects.extend(
            (
                replace(SketchObject, payload=SketchPayload),
                replace(FeatureObject, payload=_extrusion_payload(FeatureData)),
            )
        )
    SketchOne, FeatureOne, SketchTwo, FeatureTwo = NormalizedObjects
    BoundsData = (
        _write_rectangle_bounds(SketchOne),
        _write_rectangle_bounds(SketchTwo),
    )
    DimensionData = _FreeCadTwoFeatureDimensions(
        DocumentData,
        (SourceSketchOne, SourceSketchTwo),
        (SourceFeatureOne, SourceFeatureTwo),
    )
    SecondIsBoss = (
        str(SourceFeatureTwo.operation).casefold() == BooleanOperation.JOIN.value
    )
    if (
        FeatureOne.class_name != "moExtrusion_c"
        or FeatureTwo.class_name != ("moExtrusion_c" if SecondIsBoss else "moCut_c")
        or any(ItemData is None for ItemData in BoundsData)
        or any(
            ExtrusionEditCodes(ItemData.payload) is None
            for ItemData in (FeatureOne, FeatureTwo)
        )
        or DimensionData is None
        or any(
            len(SketchObject.payload) < 4
            or struct.unpack_from("<I", SketchObject.payload)[0] != 2
            or SketchObject.class_name != "moProfileFeature_c"
            or not HasRectDims(SketchObject, BoundsValue)
            or SketchData.suppressed
            or not HasCanonicalSketchGeometry(SketchData, BoundsValue, None)
            or len(SketchData.closed_profile_entity_ids) != 1
            or set(SketchData.closed_profile_entity_ids[0])
            != {ItemData.id for ItemData in SketchData.entities}
            for SketchObject, SketchData, BoundsValue in zip(
                (SketchOne, SketchTwo),
                (SourceSketchOne, SourceSketchTwo),
                BoundsData,
                strict=True,
            )
        )
    ):
        return ObjectsData
    TargetIds = (26, 32, 33, 40)
    TargetNames = (
        "Sketch1",
        "Boss-Extrude1",
        "Sketch2",
        "Boss-Extrude2" if SecondIsBoss else "Cut-Extrude1",
    )
    for SourceObject, TargetId in zip(
        (SketchOne, FeatureOne, SketchTwo, FeatureTwo), TargetIds, strict=True
    ):
        PrefixValue = "sketch" if SourceObject.kind == "Sketch" else "feature"
        ObjectIds[f"{PrefixValue}:{SourceObject.source_id}"] = TargetId
    CanonicalObjects: list[_WriteObject] = []
    for ObjectIndex, (ItemData, TargetId, TargetName) in enumerate(
        zip(
            (SketchOne, FeatureOne, SketchTwo, FeatureTwo),
            TargetIds,
            TargetNames,
            strict=True,
        )
    ):
        if ItemData.kind == "Extrusion":
            DimensionValue = DimensionData[ObjectIndex // 2]
            DimensionValues = (
                ()
                if DimensionValue is None
                else (
                    replace(
                        DimensionValue,
                        name="D1",
                        text=format(DimensionValue.value_mm, ".15g"),
                    ),
                )
            )
            ChildObjectId = TargetIds[ObjectIndex - 1]
            PropertyValues = tuple(
                (
                    PropertyName,
                    (
                        str(ChildObjectId)
                        if PropertyName == "DissectableChildren"
                        else PropertyValue
                    ),
                )
                for PropertyName, PropertyValue in ItemData.properties
            )
        else:
            DimensionValues = ItemData.dimensions
            PropertyValues = ItemData.properties
        CanonicalObjects.append(
            replace(
                ItemData,
                object_id=TargetId,
                name=TargetName,
                properties=PropertyValues,
                dimensions=DimensionValues,
            )
        )
    return tuple(CanonicalObjects)


# cut-chain canonicalization binds chained FreeCAD pockets to recovered native ids
def _CanonicalCutChainObjects(
    ObjectsData: tuple[_WriteObject, ...],
    ObjectIds: dict[str, int],
    DocumentData: CadDocument,
) -> tuple[_WriteObject, ...]:
    FeatureCount = len(ObjectsData) // 2
    if FeatureCount not in {3, 4} or len(ObjectsData) != FeatureCount * 2:
        return ObjectsData
    SketchObjects = ObjectsData[0::2]
    FeatureObjects = ObjectsData[1::2]
    SourceSketches = tuple(
        next(
            (
                SketchData
                for SketchData in DocumentData.sketches
                if SketchData.id == SketchObject.source_id
            ),
            None,
        )
        for SketchObject in SketchObjects
    )
    SourceFeatures = tuple(
        next(
            (
                FeatureData
                for FeatureData in DocumentData.feature_timeline
                if FeatureData.id == FeatureObject.source_id
            ),
            None,
        )
        for FeatureObject in FeatureObjects
    )
    if any(ItemData is None for ItemData in (*SourceSketches, *SourceFeatures)):
        return ObjectsData
    ResolvedSketches = tuple(
        ItemData for ItemData in SourceSketches if ItemData is not None
    )
    ResolvedFeatures = tuple(
        ItemData for ItemData in SourceFeatures if ItemData is not None
    )
    if len(ResolvedSketches) != FeatureCount or len(ResolvedFeatures) != FeatureCount:
        return ObjectsData
    NormalizedSketches = tuple(
        _CanonicalPrincipalSketch(ItemData, DocumentData.support_planes, ObjectIds)
        for ItemData in ResolvedSketches
    )
    NormalizedFeatures = tuple(
        _CanonicalPrincipalExtrusion(
            FeatureData,
            SketchData,
            DocumentData.support_planes,
            ObjectIds,
        )
        for FeatureData, SketchData in zip(
            ResolvedFeatures,
            ResolvedSketches,
            strict=True,
        )
    )
    NormalizedObjects: list[_WriteObject] = []
    for SketchObject, FeatureObject, SketchData, FeatureData in zip(
        SketchObjects,
        FeatureObjects,
        NormalizedSketches,
        NormalizedFeatures,
        strict=True,
    ):
        SketchPayload, _ = _sketch_payload(
            SketchData,
            SketchObject.object_id,
            ObjectIds,
        )
        NormalizedObjects.extend(
            (
                replace(SketchObject, payload=SketchPayload),
                replace(FeatureObject, payload=_extrusion_payload(FeatureData)),
            )
        )
    SketchObjects = tuple(NormalizedObjects[0::2])
    FeatureObjects = tuple(NormalizedObjects[1::2])
    BoundsData = tuple(_write_rectangle_bounds(ItemData) for ItemData in SketchObjects)
    DimensionData = (
        _FreeCadThreeFeatureDimensions(
            DocumentData,
            ResolvedSketches,
            ResolvedFeatures,
        )
        if FeatureCount == 3
        else _FreeCadFourFeatureDimensions(
            DocumentData,
            ResolvedSketches,
            ResolvedFeatures,
        )
    )
    if (
        tuple(ItemData.class_name for ItemData in FeatureObjects)
        != ("moExtrusion_c", *(("moCut_c",) * (FeatureCount - 1)))
        or any(ItemData is None for ItemData in BoundsData)
        or any(
            ExtrusionEditCodes(ItemData.payload) is None for ItemData in FeatureObjects
        )
        or DimensionData is None
        or any(
            len(SketchObject.payload) < 4
            or struct.unpack_from("<I", SketchObject.payload)[0] != 2
            or SketchObject.class_name != "moProfileFeature_c"
            or not HasRectDims(SketchObject, BoundsValue)
            or SketchData.suppressed
            or not HasCanonicalSketchGeometry(SketchData, BoundsValue, None)
            or len(SketchData.closed_profile_entity_ids) != 1
            or set(SketchData.closed_profile_entity_ids[0])
            != {ItemData.id for ItemData in SketchData.entities}
            for SketchObject, SketchData, BoundsValue in zip(
                SketchObjects,
                ResolvedSketches,
                BoundsData,
                strict=True,
            )
        )
    ):
        return ObjectsData
    TargetIds = (
        (26, 32, 33, 40, 41, 47)
        if FeatureCount == 3
        else (26, 32, 33, 40, 41, 47, 48, 54)
    )
    TargetNames = tuple(
        NameValue
        for FeatureIndex in range(FeatureCount)
        for NameValue in (
            f"Sketch{FeatureIndex + 1}",
            ("Boss-Extrude1" if FeatureIndex == 0 else f"Cut-Extrude{FeatureIndex}"),
        )
    )
    for SourceObject, TargetId in zip(
        NormalizedObjects,
        TargetIds,
        strict=True,
    ):
        PrefixValue = "sketch" if SourceObject.kind == "Sketch" else "feature"
        ObjectIds[f"{PrefixValue}:{SourceObject.source_id}"] = TargetId
    CanonicalObjects: list[_WriteObject] = []
    for ObjectIndex, (ItemData, TargetId, TargetName) in enumerate(
        zip(NormalizedObjects, TargetIds, TargetNames, strict=True)
    ):
        if ItemData.kind == "Extrusion":
            DimensionValue = DimensionData[ObjectIndex // 2]
            DimensionValues = (
                replace(
                    DimensionValue,
                    name="D1",
                    text=format(DimensionValue.value_mm, ".15g"),
                ),
            )
            ChildObjectId = TargetIds[ObjectIndex - 1]
            PropertyValues = tuple(
                (
                    PropertyName,
                    (
                        str(ChildObjectId)
                        if PropertyName == "DissectableChildren"
                        else PropertyValue
                    ),
                )
                for PropertyName, PropertyValue in ItemData.properties
            )
        else:
            DimensionValues = ItemData.dimensions
            PropertyValues = ItemData.properties
        CanonicalObjects.append(
            replace(
                ItemData,
                object_id=TargetId,
                name=TargetName,
                properties=PropertyValues,
                dimensions=DimensionValues,
            )
        )
    return tuple(CanonicalObjects)


# target principal-plane frames provide a stable basis for source sketch coordinates
def _PrincipalPlaneFrame(
    PlaneObjectId: int,
) -> (
    tuple[
        tuple[float, float, float],
        tuple[float, float, float],
        tuple[float, float, float],
    ]
    | None
):
    return {
        2: ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
        3: ((1.0, 0.0, 0.0), (0.0, 0.0, -1.0), (0.0, 1.0, 0.0)),
        4: ((0.0, 0.0, -1.0), (0.0, 1.0, 0.0), (1.0, 0.0, 0.0)),
    }.get(PlaneObjectId)


# proof compares principal planes in their target-native canonical parameterization
def _ExpectedPlaneFrame(
    PlaneData: SupportPlane,
    PlaneObjectId: int,
) -> tuple[
    tuple[float, float, float],
    tuple[float, float, float],
    tuple[float, float, float],
    tuple[float, float, float],
]:
    PrincipalFrame = _PrincipalPlaneFrame(PlaneObjectId)
    if PrincipalFrame is not None:
        return ((0.0, 0.0, 0.0), *PrincipalFrame)
    return (
        _frame_vector(
            (
                PlaneData.transform.origin.x,
                PlaneData.transform.origin.y,
                PlaneData.transform.origin.z,
            )
        ),
        _frame_vector(
            (
                PlaneData.transform.x_axis.x,
                PlaneData.transform.x_axis.y,
                PlaneData.transform.x_axis.z,
            )
        ),
        _frame_vector(
            (
                PlaneData.transform.y_axis.x,
                PlaneData.transform.y_axis.y,
                PlaneData.transform.y_axis.z,
            )
        ),
        _frame_vector(
            (
                PlaneData.transform.z_axis.x,
                PlaneData.transform.z_axis.y,
                PlaneData.transform.z_axis.z,
            )
        ),
    )


# source sketch points are re-expressed in the equivalent SOLIDWORKS principal basis
def _CanonicalPrincipalSketch(
    SketchData: Sketch,
    PlaneData: tuple[SupportPlane, ...],
    ObjectIds: Mapping[str, int],
) -> Sketch:
    PlaneValue = next(
        (
            ItemData
            for ItemData in PlaneData
            if ItemData.id == SketchData.support_plane_id
        ),
        None,
    )
    PlaneObjectId = ObjectIds.get(f"plane:{SketchData.support_plane_id}", 0)
    TargetFrame = _PrincipalPlaneFrame(PlaneObjectId)
    if PlaneValue is None or TargetFrame is None:
        return SketchData
    SourceFrame = PlaneValue.transform
    TargetU, TargetV, _ = TargetFrame

    # point coordinates move through model space so in-plane rotations remain exact
    def TransformPoint(PointData: Vector2) -> Vector2:
        GlobalValue = (
            SourceFrame.origin.x
            + PointData.x * SourceFrame.x_axis.x
            + PointData.y * SourceFrame.y_axis.x,
            SourceFrame.origin.y
            + PointData.x * SourceFrame.x_axis.y
            + PointData.y * SourceFrame.y_axis.y,
            SourceFrame.origin.z
            + PointData.x * SourceFrame.x_axis.z
            + PointData.y * SourceFrame.y_axis.z,
        )
        return Vector2(
            sum(
                LeftValue * RightValue
                for LeftValue, RightValue in zip(GlobalValue, TargetU, strict=True)
            ),
            sum(
                LeftValue * RightValue
                for LeftValue, RightValue in zip(GlobalValue, TargetV, strict=True)
            ),
        )

    NormalizedEntities = []
    for EntityData in SketchData.entities:
        GeometryData = EntityData.geometry
        if isinstance(GeometryData, LineGeometry):
            GeometryData = replace(
                GeometryData,
                start=TransformPoint(GeometryData.start),
                end=TransformPoint(GeometryData.end),
            )
        elif isinstance(GeometryData, CircleGeometry):
            GeometryData = replace(
                GeometryData,
                center=TransformPoint(GeometryData.center),
            )
        NormalizedEntities.append(replace(EntityData, geometry=GeometryData))
    return replace(SketchData, entities=tuple(NormalizedEntities))


# extrusion reversal is adjusted when source and target principal normals oppose
def _CanonicalPrincipalExtrusion(
    FeatureData: FeatureStep,
    SketchData: Sketch,
    PlaneData: tuple[SupportPlane, ...],
    ObjectIds: Mapping[str, int],
) -> FeatureStep:
    DefinitionData = FeatureData.definition
    PlaneValue = next(
        (
            ItemData
            for ItemData in PlaneData
            if ItemData.id == SketchData.support_plane_id
        ),
        None,
    )
    PlaneObjectId = ObjectIds.get(f"plane:{SketchData.support_plane_id}", 0)
    TargetFrame = _PrincipalPlaneFrame(PlaneObjectId)
    if (
        not isinstance(DefinitionData, ExtrusionFeature)
        or PlaneValue is None
        or TargetFrame is None
    ):
        return FeatureData
    SourceNormal = PlaneValue.transform.z_axis
    TargetNormal = TargetFrame[2]
    OpposedValue = (
        sum(
            LeftValue * RightValue
            for LeftValue, RightValue in zip(
                (SourceNormal.x, SourceNormal.y, SourceNormal.z),
                TargetNormal,
                strict=True,
            )
        )
        < 0.0
    )
    return replace(
        FeatureData,
        definition=replace(
            DefinitionData,
            reversed=DefinitionData.reversed != OpposedValue,
        ),
    )


# canonical single-profile sketches exclude hidden construction and fixed geometry
def HasCanonicalSketchGeometry(
    SketchData: Sketch,
    BoundsValue: tuple[float, float, float, float] | None,
    CircleValue: tuple[float, float, float] | None,
) -> bool:
    if (BoundsValue is None) == (CircleValue is None):
        return False
    if any(ItemData.construction or ItemData.fixed for ItemData in SketchData.entities):
        return False
    if BoundsValue is not None:
        return len(SketchData.entities) == 4 and all(
            isinstance(ItemData.geometry, LineGeometry)
            for ItemData in SketchData.entities
        )
    return len(SketchData.entities) == 1 and isinstance(
        SketchData.entities[0].geometry,
        CircleGeometry,
    )


# four-stage FreeCAD validation proves all chained cuts and every inactive default
def _FreeCadFourFeatureDimensions(
    DocumentData: CadDocument,
    SketchData: tuple[Sketch, ...],
    FeatureData: tuple[FeatureStep, ...],
) -> (
    tuple[
        _WriteDimension,
        _WriteDimension,
        _WriteDimension,
        _WriteDimension,
    ]
    | None
):
    if len(SketchData) != 4 or len(FeatureData) != 4:
        return None
    TimelineData = tuple(
        ItemData
        for ItemData in sorted(
            DocumentData.feature_timeline,
            key=lambda ItemData: ItemData.order,
        )
        if not _is_native_system_feature(ItemData)
    )
    AllowedOwners = {
        *(ItemData.id for ItemData in SketchData),
        *(ItemData.id for ItemData in FeatureData),
    }
    if (
        DocumentData.source.format_id.casefold() != "freecad.fcstd"
        or DocumentData.assembly is not None
        or DocumentData.selections
        or tuple(DocumentData.sketches) != SketchData
        or TimelineData != FeatureData
        or len(DocumentData.bodies) != 1
        or DocumentData.bodies[0].final_feature_id != FeatureData[-1].id
        or tuple(ItemData.order for ItemData in FeatureData) != (0, 1, 2, 3)
        or tuple(ItemData.sketch_id for ItemData in FeatureData)
        != tuple(ItemData.id for ItemData in SketchData)
        or FeatureData[0].input_feature_ids
        or any(
            FeatureValue.input_feature_ids != (FeatureData[FeatureIndex - 1].id,)
            for FeatureIndex, FeatureValue in enumerate(FeatureData[1:], start=1)
        )
        or any(ItemData.selection_ids for ItemData in FeatureData)
        or any(ItemData.configuration_states for ItemData in FeatureData)
        or any(ItemData.suppressed for ItemData in FeatureData)
        or str(FeatureData[0].operation).casefold()
        not in {BooleanOperation.CREATE.value, BooleanOperation.JOIN.value}
        or any(
            str(ItemData.operation).casefold() != BooleanOperation.CUT.value
            for ItemData in FeatureData[1:]
        )
        or len(DocumentData.configurations) != 1
        or DocumentData.configurations[0].name.casefold() != "default"
        or not DocumentData.configurations[0].active
        or DocumentData.configurations[0].parent_id is not None
        or DocumentData.configurations[0].overrides
        or DocumentData.configurations[0].suppressed_feature_ids
        or any(
            ItemData.owner_id not in AllowedOwners
            for ItemData in DocumentData.parameters
        )
    ):
        return None
    DimensionData = tuple(
        _FreeCadFeatureDimension(
            DocumentData,
            SketchValue,
            FeatureValue,
            TypeId,
            SecondLength,
            Visibility,
        )
        for SketchValue, FeatureValue, TypeId, SecondLength, Visibility in zip(
            SketchData,
            FeatureData,
            (
                "PartDesign::Pad",
                "PartDesign::Pocket",
                "PartDesign::Pocket",
                "PartDesign::Pocket",
            ),
            (10.0, 5.0, 5.0, 5.0),
            (False, False, False, True),
            strict=True,
        )
    )
    if any(ItemData is None for ItemData in DimensionData):
        return None
    return (
        DimensionData[0],
        DimensionData[1],
        DimensionData[2],
        DimensionData[3],
    )


# three-stage FreeCAD validation proves both chained cuts and every inactive default
def _FreeCadThreeFeatureDimensions(
    DocumentData: CadDocument,
    SketchData: tuple[Sketch, ...],
    FeatureData: tuple[FeatureStep, ...],
) -> tuple[_WriteDimension, _WriteDimension, _WriteDimension] | None:
    if len(SketchData) != 3 or len(FeatureData) != 3:
        return None
    SketchOne, SketchTwo, SketchThree = SketchData
    FeatureOne, FeatureTwo, FeatureThree = FeatureData
    TimelineData = tuple(
        ItemData
        for ItemData in sorted(
            DocumentData.feature_timeline,
            key=lambda ItemData: ItemData.order,
        )
        if not _is_native_system_feature(ItemData)
    )
    AllowedOwners = {
        *(ItemData.id for ItemData in SketchData),
        *(ItemData.id for ItemData in FeatureData),
    }
    if (
        DocumentData.source.format_id.casefold() != "freecad.fcstd"
        or DocumentData.assembly is not None
        or DocumentData.selections
        or tuple(DocumentData.sketches) != SketchData
        or TimelineData != FeatureData
        or len(DocumentData.bodies) != 1
        or DocumentData.bodies[0].final_feature_id != FeatureThree.id
        or tuple(ItemData.order for ItemData in FeatureData) != (0, 1, 2)
        or tuple(ItemData.sketch_id for ItemData in FeatureData)
        != tuple(ItemData.id for ItemData in SketchData)
        or FeatureOne.input_feature_ids
        or FeatureTwo.input_feature_ids != (FeatureOne.id,)
        or FeatureThree.input_feature_ids != (FeatureTwo.id,)
        or any(ItemData.selection_ids for ItemData in FeatureData)
        or any(ItemData.configuration_states for ItemData in FeatureData)
        or any(ItemData.suppressed for ItemData in FeatureData)
        or str(FeatureOne.operation).casefold()
        not in {BooleanOperation.CREATE.value, BooleanOperation.JOIN.value}
        or any(
            str(ItemData.operation).casefold() != BooleanOperation.CUT.value
            for ItemData in (FeatureTwo, FeatureThree)
        )
        or len(DocumentData.configurations) != 1
        or DocumentData.configurations[0].name.casefold() != "default"
        or not DocumentData.configurations[0].active
        or DocumentData.configurations[0].parent_id is not None
        or DocumentData.configurations[0].overrides
        or DocumentData.configurations[0].suppressed_feature_ids
        or any(
            ItemData.owner_id not in AllowedOwners
            for ItemData in DocumentData.parameters
        )
    ):
        return None
    DimensionData = tuple(
        _FreeCadFeatureDimension(
            DocumentData,
            SketchValue,
            FeatureValue,
            TypeId,
            SecondLength,
            Visibility,
        )
        for SketchValue, FeatureValue, TypeId, SecondLength, Visibility in zip(
            (SketchOne, SketchTwo, SketchThree),
            (FeatureOne, FeatureTwo, FeatureThree),
            ("PartDesign::Pad", "PartDesign::Pocket", "PartDesign::Pocket"),
            (10.0, 5.0, 5.0),
            (False, False, True),
            strict=True,
        )
    )
    if any(ItemData is None for ItemData in DimensionData):
        return None
    return (
        DimensionData[0],
        DimensionData[1],
        DimensionData[2],
    )


# FreeCAD history validation proves the exact pad-pocket dependency and inactive defaults
def _FreeCadTwoFeatureDimensions(
    DocumentData: CadDocument,
    SketchData: tuple[Sketch, Sketch],
    FeatureData: tuple[FeatureStep, FeatureStep],
) -> tuple[_WriteDimension, _WriteDimension | None] | None:
    SketchOne, SketchTwo = SketchData
    FeatureOne, FeatureTwo = FeatureData
    TimelineData = tuple(
        ItemData
        for ItemData in sorted(
            DocumentData.feature_timeline, key=lambda ItemData: ItemData.order
        )
        if not _is_native_system_feature(ItemData)
    )
    AllowedOwners = {
        SketchOne.id,
        SketchTwo.id,
        FeatureOne.id,
        FeatureTwo.id,
    }
    if (
        DocumentData.source.format_id.casefold() != "freecad.fcstd"
        or DocumentData.assembly is not None
        or DocumentData.selections
        or tuple(DocumentData.sketches) != (SketchOne, SketchTwo)
        or TimelineData != (FeatureOne, FeatureTwo)
        or len(DocumentData.bodies) != 1
        or DocumentData.bodies[0].final_feature_id != FeatureTwo.id
        or FeatureOne.order != 0
        or FeatureTwo.order != 1
        or FeatureOne.sketch_id != SketchOne.id
        or FeatureTwo.sketch_id != SketchTwo.id
        or FeatureOne.input_feature_ids
        or FeatureTwo.input_feature_ids != (FeatureOne.id,)
        or FeatureOne.selection_ids
        or FeatureTwo.selection_ids
        or FeatureOne.configuration_states
        or FeatureTwo.configuration_states
        or FeatureOne.suppressed
        or FeatureTwo.suppressed
        or str(FeatureOne.operation).casefold()
        not in {BooleanOperation.CREATE.value, BooleanOperation.JOIN.value}
        or str(FeatureTwo.operation).casefold()
        not in {BooleanOperation.CUT.value, BooleanOperation.JOIN.value}
        or len(DocumentData.configurations) != 1
        or DocumentData.configurations[0].name.casefold() != "default"
        or not DocumentData.configurations[0].active
        or DocumentData.configurations[0].parent_id is not None
        or DocumentData.configurations[0].overrides
        or DocumentData.configurations[0].suppressed_feature_ids
        or any(
            ItemData.owner_id not in AllowedOwners
            for ItemData in DocumentData.parameters
        )
    ):
        return None
    DimensionOne = _FreeCadFeatureDimension(
        DocumentData,
        SketchOne,
        FeatureOne,
        "PartDesign::Pad",
        10.0,
        False,
    )
    if not isinstance(FeatureTwo.definition, ExtrusionFeature):
        return None
    SecondOperation = str(FeatureTwo.operation).casefold()
    if SecondOperation == BooleanOperation.CUT.value and (
        str(FeatureTwo.definition.end_condition).casefold()
        == ExtrusionEndCondition.THROUGH_ALL.value
    ):
        if not HasFreeCadThroughAllFeature(
            DocumentData,
            SketchTwo,
            FeatureTwo,
        ):
            return None
        DimensionTwo = None
    else:
        DimensionTwo = _FreeCadFeatureDimension(
            DocumentData,
            SketchTwo,
            FeatureTwo,
            (
                "PartDesign::Pad"
                if SecondOperation == BooleanOperation.JOIN.value
                else "PartDesign::Pocket"
            ),
            10.0 if SecondOperation == BooleanOperation.JOIN.value else 5.0,
            True,
        )
        if DimensionTwo is None:
            return None
    if DimensionOne is None:
        return None
    return DimensionOne, DimensionTwo


# FreeCAD pad-groove validation proves both feature defaults and the sketch-axis link
def _FreeCadPadGrooveDimensions(
    DocumentData: CadDocument,
    SketchData: tuple[Sketch, Sketch],
    FeatureData: tuple[FeatureStep, FeatureStep],
) -> tuple[_WriteDimension, _WriteDimension] | None:
    SketchOne, SketchTwo = SketchData
    PadFeature, GrooveFeature = FeatureData
    TimelineData = tuple(
        ItemData
        for ItemData in sorted(
            DocumentData.feature_timeline,
            key=lambda ItemData: ItemData.order,
        )
        if not _is_native_system_feature(ItemData)
    )
    GrooveDefinition = GrooveFeature.definition
    if (
        DocumentData.source.format_id.casefold() != "freecad.fcstd"
        or DocumentData.assembly is not None
        or tuple(DocumentData.sketches) != (SketchOne, SketchTwo)
        or TimelineData != (PadFeature, GrooveFeature)
        or len(DocumentData.bodies) != 1
        or DocumentData.bodies[0].final_feature_id != GrooveFeature.id
        or PadFeature.order != 0
        or GrooveFeature.order != 1
        or PadFeature.sketch_id != SketchOne.id
        or GrooveFeature.sketch_id != SketchTwo.id
        or PadFeature.input_feature_ids
        or GrooveFeature.input_feature_ids != (PadFeature.id,)
        or PadFeature.selection_ids
        or len(GrooveFeature.selection_ids) != 1
        or PadFeature.configuration_states
        or GrooveFeature.configuration_states
        or PadFeature.suppressed
        or GrooveFeature.suppressed
        or str(PadFeature.operation).casefold()
        not in {BooleanOperation.CREATE.value, BooleanOperation.JOIN.value}
        or str(GrooveFeature.operation).casefold() != BooleanOperation.CUT.value
        or str(GrooveFeature.kind).casefold() != FeatureKind.REVOLUTION.value
        or _freecad_type_id(GrooveFeature.attributes) != "PartDesign::Groove"
        or not isinstance(GrooveDefinition, NativeFeatureDefinition)
        or GrooveDefinition.format_id.casefold() != "freecad.fcstd"
        or GrooveDefinition.type_id != "PartDesign::Groove"
        or len(DocumentData.configurations) != 1
        or DocumentData.configurations[0].name.casefold() != "default"
        or not DocumentData.configurations[0].active
        or DocumentData.configurations[0].parent_id is not None
        or DocumentData.configurations[0].overrides
        or DocumentData.configurations[0].suppressed_feature_ids
        or len(DocumentData.selections) != 1
        or GrooveFeature.selection_ids != (DocumentData.selections[0].id,)
    ):
        return None
    AxisSelection = DocumentData.selections[0]
    if (
        GrooveFeature.provenance is None
        or AxisSelection.attributes.get("freecad_object")
        != GrooveFeature.provenance.native_id
        or AxisSelection.attributes.get("freecad_property") != "ReferenceAxis"
        or len(AxisSelection.path) != 1
        or AxisSelection.path[0].entity_id != SketchTwo.name
        or AxisSelection.path[0].subelement != HORIZONTAL_AXIS_SUBELEMENT
    ):
        return None
    PadDimension = _FreeCadFeatureDimension(
        DocumentData,
        SketchOne,
        PadFeature,
        "PartDesign::Pad",
        10.0,
        False,
    )
    if PadDimension is None:
        return None
    ParameterData: dict[str, Parameter] = {}
    for ParameterValueData in DocumentData.parameters:
        if ParameterValueData.owner_id != GrooveFeature.id:
            continue
        PathValue = ParameterValueData.attributes.get("freecad_path")
        if (
            not isinstance(PathValue, str)
            or not PathValue
            or PathValue in ParameterData
            or ParameterValueData.expression is not None
        ):
            return None
        ParameterData[PathValue] = ParameterValueData
    ExpectedData = {
        "AllowMultiFace": (ValueKind.BOOLEAN, True),
        "Angle": (ValueKind.ANGLE, 360.0),
        "Angle2": (ValueKind.ANGLE, 0.0),
        "FuzzyTolerance": (ValueKind.NUMBER, -1.0),
        "Label": (ValueKind.STRING, GrooveFeature.name),
        "Label2": (ValueKind.STRING, ""),
        "Midplane": (ValueKind.BOOLEAN, False),
        "Refine": (ValueKind.BOOLEAN, True),
        "Reversed": (ValueKind.BOOLEAN, False),
        "Suppressed": (ValueKind.BOOLEAN, False),
        "Type": (ValueKind.INTEGER, 0),
        "Visibility": (ValueKind.BOOLEAN, True),
    }
    if set(ParameterData) != set(ExpectedData) or any(
        not _freecad_parameter_matches(
            ParameterData[PathValue],
            KindValue,
            ExpectedValue,
        )
        for PathValue, (KindValue, ExpectedValue) in ExpectedData.items()
    ):
        return None
    AngleParameter = ParameterData["Angle"]
    if AngleParameter.value.unit.casefold() not in {"deg", "degree", "degrees"}:
        return None
    return (
        PadDimension,
        _WriteDimension("D1", 360.0, "360°", AngleParameter.role),
    )


# FreeCAD boss-fillet validation proves the history, defaults, radius, and edge locus
def _FreeCadBossFilletDimensions(
    DocumentData: CadDocument,
    SketchData: Sketch,
    PadFeature: FeatureStep,
    FilletFeatureData: FeatureStep,
    BoundsValue: tuple[float, float, float, float] | None,
) -> tuple[_WriteDimension, _WriteDimension] | None:
    TimelineData = tuple(
        ItemData
        for ItemData in sorted(
            DocumentData.feature_timeline,
            key=lambda ItemData: ItemData.order,
        )
        if not _is_native_system_feature(ItemData)
    )
    FilletDefinition = FilletFeatureData.definition
    PadDefinition = PadFeature.definition
    AllowedOwners = {SketchData.id, PadFeature.id, FilletFeatureData.id}
    if (
        BoundsValue is None
        or DocumentData.source.format_id.casefold() != "freecad.fcstd"
        or DocumentData.assembly is not None
        or tuple(DocumentData.sketches) != (SketchData,)
        or TimelineData != (PadFeature, FilletFeatureData)
        or len(DocumentData.bodies) != 1
        or DocumentData.bodies[0].final_feature_id != FilletFeatureData.id
        or PadFeature.order != 0
        or FilletFeatureData.order != 1
        or PadFeature.sketch_id != SketchData.id
        or FilletFeatureData.sketch_id is not None
        or PadFeature.input_feature_ids
        or FilletFeatureData.input_feature_ids != (PadFeature.id,)
        or PadFeature.selection_ids
        or len(FilletFeatureData.selection_ids) != 1
        or PadFeature.configuration_states
        or FilletFeatureData.configuration_states
        or PadFeature.suppressed
        or FilletFeatureData.suppressed
        or str(PadFeature.operation).casefold()
        not in {BooleanOperation.CREATE.value, BooleanOperation.JOIN.value}
        or FilletFeatureData.operation is not None
        or str(FilletFeatureData.kind).casefold() != FeatureKind.FILLET.value
        or _freecad_type_id(SketchData.attributes) != "Sketcher::SketchObject"
        or _freecad_type_id(PadFeature.attributes) != "PartDesign::Pad"
        or _freecad_type_id(FilletFeatureData.attributes) != "PartDesign::Fillet"
        or not isinstance(PadDefinition, ExtrusionFeature)
        or PadDefinition.reversed
        or PadDefinition.symmetric
        or not isinstance(FilletDefinition, FilletFeature)
        or FilletDefinition.variable_radius_parameter_ids
        or FilletFeatureData.provenance is None
        or len(DocumentData.configurations) != 1
        or DocumentData.configurations[0].name.casefold() != "default"
        or not DocumentData.configurations[0].active
        or DocumentData.configurations[0].parent_id is not None
        or DocumentData.configurations[0].overrides
        or DocumentData.configurations[0].suppressed_feature_ids
        or len(DocumentData.selections) != 1
        or FilletFeatureData.selection_ids != (DocumentData.selections[0].id,)
        or any(
            ItemData.owner_id not in AllowedOwners
            for ItemData in DocumentData.parameters
        )
    ):
        return None
    PadDimension = _FreeCadFeatureDimension(
        DocumentData,
        SketchData,
        PadFeature,
        "PartDesign::Pad",
        10.0,
        False,
    )
    RadiusValue = FilletDefinition.radius
    RadiusDimension = _parameter_dimension(Parameter("", "D1", RadiusValue))
    if (
        PadDimension is None
        or RadiusDimension is None
        or RadiusDimension.value_mm <= 0.0
    ):
        return None
    RadiusNumber = RadiusDimension.value_mm
    MinimumX, MinimumY, MaximumX, MaximumY = BoundsValue
    if (
        not math.isfinite(RadiusNumber)
        or RadiusNumber <= 0.0
        or RadiusNumber * 2.0 >= min(MaximumX - MinimumX, MaximumY - MinimumY)
    ):
        return None
    SelectionData = DocumentData.selections[0]
    PadNativeName = (
        PadFeature.provenance.native_id
        if PadFeature.provenance is not None
        else PadFeature.name
    )
    if (
        SelectionData.attributes.get("freecad_object")
        != FilletFeatureData.provenance.native_id
        or SelectionData.attributes.get("freecad_property") != "Base"
        or SelectionData.attributes.get("freecad_target") != PadNativeName
        or len(SelectionData.path) != 1
        or SelectionData.path[0].entity_kind != "edge"
        or SelectionData.path[0].entity_id != PadNativeName
        or not _HasFreeCadMaxCornerEdge(
            DocumentData,
            PadNativeName,
            SelectionData.path[0].subelement,
            BoundsValue,
            PadDimension.value_mm,
        )
    ):
        return None
    ParameterData: dict[str, Parameter] = {}
    for ParameterValueData in DocumentData.parameters:
        if ParameterValueData.owner_id != FilletFeatureData.id:
            continue
        PathValue = ParameterValueData.attributes.get("freecad_path")
        if (
            not isinstance(PathValue, str)
            or not PathValue
            or PathValue in ParameterData
            or ParameterValueData.expression is not None
        ):
            return None
        ParameterData[PathValue] = ParameterValueData
    ExpectedData = {
        "FuzzyTolerance": (ValueKind.NUMBER, -1.0),
        "Label": (ValueKind.STRING, FilletFeatureData.name),
        "Label2": (ValueKind.STRING, ""),
        "Radius": (ValueKind.QUANTITY, RadiusNumber),
        "Refine": (ValueKind.BOOLEAN, True),
        "SupportTransform": (ValueKind.BOOLEAN, False),
        "Suppressed": (ValueKind.BOOLEAN, False),
        "UseAllEdges": (ValueKind.BOOLEAN, False),
        "Visibility": (ValueKind.BOOLEAN, True),
    }
    if set(ParameterData) != set(ExpectedData) or any(
        not _freecad_parameter_matches(
            ParameterData[PathValue],
            KindValue,
            ExpectedValue,
        )
        for PathValue, (KindValue, ExpectedValue) in ExpectedData.items()
    ):
        return None
    RadiusParameter = ParameterData["Radius"]
    return (
        PadDimension,
        _WriteDimension(
            "D1",
            RadiusNumber,
            "R" + format(RadiusNumber, ".15g"),
            RadiusParameter.role,
        ),
    )


# FreeCAD boss-chamfer validation proves equal distance, defaults, and edge locus
def _FreeCadBossChamferDimensions(
    DocumentData: CadDocument,
    SketchData: Sketch,
    PadFeature: FeatureStep,
    ChamferFeatureData: FeatureStep,
    BoundsValue: tuple[float, float, float, float] | None,
) -> tuple[_WriteDimension, _WriteDimension] | None:
    TimelineData = tuple(
        ItemData
        for ItemData in sorted(
            DocumentData.feature_timeline,
            key=lambda ItemData: ItemData.order,
        )
        if not _is_native_system_feature(ItemData)
    )
    ChamferDefinition = ChamferFeatureData.definition
    PadDefinition = PadFeature.definition
    AllowedOwners = {SketchData.id, PadFeature.id, ChamferFeatureData.id}
    if (
        BoundsValue is None
        or DocumentData.source.format_id.casefold() != "freecad.fcstd"
        or DocumentData.assembly is not None
        or tuple(DocumentData.sketches) != (SketchData,)
        or TimelineData != (PadFeature, ChamferFeatureData)
        or len(DocumentData.bodies) != 1
        or DocumentData.bodies[0].final_feature_id != ChamferFeatureData.id
        or PadFeature.order != 0
        or ChamferFeatureData.order != 1
        or PadFeature.sketch_id != SketchData.id
        or ChamferFeatureData.sketch_id is not None
        or PadFeature.input_feature_ids
        or ChamferFeatureData.input_feature_ids != (PadFeature.id,)
        or PadFeature.selection_ids
        or len(ChamferFeatureData.selection_ids) != 1
        or PadFeature.configuration_states
        or ChamferFeatureData.configuration_states
        or PadFeature.suppressed
        or ChamferFeatureData.suppressed
        or str(PadFeature.operation).casefold()
        not in {BooleanOperation.CREATE.value, BooleanOperation.JOIN.value}
        or ChamferFeatureData.operation is not None
        or str(ChamferFeatureData.kind).casefold() != FeatureKind.CHAMFER.value
        or _freecad_type_id(SketchData.attributes) != "Sketcher::SketchObject"
        or _freecad_type_id(PadFeature.attributes) != "PartDesign::Pad"
        or _freecad_type_id(ChamferFeatureData.attributes) != "PartDesign::Chamfer"
        or not isinstance(PadDefinition, ExtrusionFeature)
        or PadDefinition.reversed
        or PadDefinition.symmetric
        or not isinstance(ChamferDefinition, ChamferFeature)
        or ChamferDefinition.mode != "equal_distance"
        or ChamferDefinition.second_distance is not None
        or ChamferDefinition.angle is not None
        or ChamferFeatureData.provenance is None
        or len(DocumentData.configurations) != 1
        or DocumentData.configurations[0].name.casefold() != "default"
        or not DocumentData.configurations[0].active
        or DocumentData.configurations[0].parent_id is not None
        or DocumentData.configurations[0].overrides
        or DocumentData.configurations[0].suppressed_feature_ids
        or len(DocumentData.selections) != 1
        or ChamferFeatureData.selection_ids != (DocumentData.selections[0].id,)
        or any(
            ItemData.owner_id not in AllowedOwners
            for ItemData in DocumentData.parameters
        )
    ):
        return None
    PadDimension = _FreeCadFeatureDimension(
        DocumentData,
        SketchData,
        PadFeature,
        "PartDesign::Pad",
        10.0,
        False,
    )
    DistanceDimension = _parameter_dimension(
        Parameter("", "D1", ChamferDefinition.distance)
    )
    if (
        PadDimension is None
        or DistanceDimension is None
        or DistanceDimension.value_mm <= 0.0
    ):
        return None
    DistanceNumber = DistanceDimension.value_mm
    MinimumX, MinimumY, MaximumX, MaximumY = BoundsValue
    if (
        not math.isfinite(DistanceNumber)
        or DistanceNumber <= 0.0
        or DistanceNumber * 2.0 >= min(MaximumX - MinimumX, MaximumY - MinimumY)
    ):
        return None
    SelectionData = DocumentData.selections[0]
    PadNativeName = (
        PadFeature.provenance.native_id
        if PadFeature.provenance is not None
        else PadFeature.name
    )
    if (
        SelectionData.attributes.get("freecad_object")
        != ChamferFeatureData.provenance.native_id
        or SelectionData.attributes.get("freecad_property") != "Base"
        or SelectionData.attributes.get("freecad_target") != PadNativeName
        or len(SelectionData.path) != 1
        or SelectionData.path[0].entity_kind != "edge"
        or SelectionData.path[0].entity_id != PadNativeName
        or not _HasFreeCadMaxCornerEdge(
            DocumentData,
            PadNativeName,
            SelectionData.path[0].subelement,
            BoundsValue,
            PadDimension.value_mm,
        )
    ):
        return None
    ParameterData: dict[str, Parameter] = {}
    for ParameterValueData in DocumentData.parameters:
        if ParameterValueData.owner_id != ChamferFeatureData.id:
            continue
        PathValue = ParameterValueData.attributes.get("freecad_path")
        if (
            not isinstance(PathValue, str)
            or not PathValue
            or PathValue in ParameterData
            or ParameterValueData.expression is not None
        ):
            return None
        ParameterData[PathValue] = ParameterValueData
    ExpectedData = {
        "Angle": (ValueKind.ANGLE, 45.0),
        "ChamferType": (ValueKind.INTEGER, 0),
        "FlipDirection": (ValueKind.BOOLEAN, False),
        "FuzzyTolerance": (ValueKind.NUMBER, -1.0),
        "Label": (ValueKind.STRING, ChamferFeatureData.name),
        "Label2": (ValueKind.STRING, ""),
        "Refine": (ValueKind.BOOLEAN, True),
        "Size": (ValueKind.QUANTITY, DistanceNumber),
        "Size2": (ValueKind.QUANTITY, 1.0),
        "SupportTransform": (ValueKind.BOOLEAN, False),
        "Suppressed": (ValueKind.BOOLEAN, False),
        "UseAllEdges": (ValueKind.BOOLEAN, False),
        "Visibility": (ValueKind.BOOLEAN, True),
    }
    if set(ParameterData) != set(ExpectedData) or any(
        not _freecad_parameter_matches(
            ParameterData[PathValue],
            KindValue,
            ExpectedValue,
        )
        for PathValue, (KindValue, ExpectedValue) in ExpectedData.items()
    ):
        return None
    DistanceParameter = ParameterData["Size"]
    return (
        PadDimension,
        _WriteDimension(
            "D1",
            DistanceNumber,
            format(DistanceNumber, ".15g"),
            DistanceParameter.role,
        ),
    )


# FreeCAD boss-shell validation proves inward thickness defaults and the removed top face
def _FreeCadBossShellDimensions(
    DocumentData: CadDocument,
    SketchData: Sketch,
    PadFeature: FeatureStep,
    ShellFeatureData: FeatureStep,
    BoundsValue: tuple[float, float, float, float] | None,
) -> tuple[_WriteDimension, _WriteDimension] | None:
    TimelineData = tuple(
        ItemData
        for ItemData in sorted(
            DocumentData.feature_timeline,
            key=lambda ItemData: ItemData.order,
        )
        if not _is_native_system_feature(ItemData)
    )
    ShellDefinition = ShellFeatureData.definition
    PadDefinition = PadFeature.definition
    AllowedOwners = {SketchData.id, PadFeature.id, ShellFeatureData.id}
    if (
        BoundsValue is None
        or DocumentData.source.format_id.casefold() != "freecad.fcstd"
        or DocumentData.assembly is not None
        or tuple(DocumentData.sketches) != (SketchData,)
        or TimelineData != (PadFeature, ShellFeatureData)
        or len(DocumentData.bodies) != 1
        or DocumentData.bodies[0].final_feature_id != ShellFeatureData.id
        or PadFeature.order != 0
        or ShellFeatureData.order != 1
        or PadFeature.sketch_id != SketchData.id
        or ShellFeatureData.sketch_id is not None
        or PadFeature.input_feature_ids
        or ShellFeatureData.input_feature_ids != (PadFeature.id,)
        or PadFeature.selection_ids
        or len(ShellFeatureData.selection_ids) != 1
        or PadFeature.configuration_states
        or ShellFeatureData.configuration_states
        or PadFeature.suppressed
        or ShellFeatureData.suppressed
        or str(PadFeature.operation).casefold()
        not in {BooleanOperation.CREATE.value, BooleanOperation.JOIN.value}
        or ShellFeatureData.operation is not None
        or str(ShellFeatureData.kind).casefold() != FeatureKind.SHELL.value
        or _freecad_type_id(SketchData.attributes) != "Sketcher::SketchObject"
        or _freecad_type_id(PadFeature.attributes) != "PartDesign::Pad"
        or _freecad_type_id(ShellFeatureData.attributes) != "PartDesign::Thickness"
        or not isinstance(PadDefinition, ExtrusionFeature)
        or PadDefinition.reversed
        or PadDefinition.symmetric
        or not isinstance(ShellDefinition, ShellFeature)
        or ShellDefinition.outward is not False
        or ShellFeatureData.provenance is None
        or len(DocumentData.configurations) != 1
        or DocumentData.configurations[0].name.casefold() != "default"
        or not DocumentData.configurations[0].active
        or DocumentData.configurations[0].parent_id is not None
        or DocumentData.configurations[0].overrides
        or DocumentData.configurations[0].suppressed_feature_ids
        or len(DocumentData.selections) != 1
        or ShellFeatureData.selection_ids != (DocumentData.selections[0].id,)
        or any(
            ItemData.owner_id not in AllowedOwners
            for ItemData in DocumentData.parameters
        )
    ):
        return None
    PadDimension = _FreeCadFeatureDimension(
        DocumentData,
        SketchData,
        PadFeature,
        "PartDesign::Pad",
        10.0,
        False,
    )
    ThicknessDimension = _parameter_dimension(
        Parameter("", "D1", ShellDefinition.thickness)
    )
    if (
        PadDimension is None
        or ThicknessDimension is None
        or ThicknessDimension.value_mm <= 0.0
    ):
        return None
    ThicknessNumber = ThicknessDimension.value_mm
    MinimumX, MinimumY, MaximumX, MaximumY = BoundsValue
    if (
        not math.isfinite(ThicknessNumber)
        or ThicknessNumber <= 0.0
        or ThicknessNumber >= PadDimension.value_mm
        or ThicknessNumber * 2.0 >= min(MaximumX - MinimumX, MaximumY - MinimumY)
    ):
        return None
    SelectionData = DocumentData.selections[0]
    PadNativeName = (
        PadFeature.provenance.native_id
        if PadFeature.provenance is not None
        else PadFeature.name
    )
    if (
        SelectionData.attributes.get("freecad_object")
        != ShellFeatureData.provenance.native_id
        or SelectionData.attributes.get("freecad_property") != "Base"
        or SelectionData.attributes.get("freecad_target") != PadNativeName
        or len(SelectionData.path) != 1
        or SelectionData.path[0].entity_kind != "face"
        or SelectionData.path[0].entity_id != PadNativeName
        or not _HasFreeCadTopFace(
            DocumentData,
            PadNativeName,
            SelectionData.path[0].subelement,
            PadDimension.value_mm,
        )
    ):
        return None
    ParameterData: dict[str, Parameter] = {}
    for ParameterValueData in DocumentData.parameters:
        if ParameterValueData.owner_id != ShellFeatureData.id:
            continue
        PathValue = ParameterValueData.attributes.get("freecad_path")
        if (
            not isinstance(PathValue, str)
            or not PathValue
            or PathValue in ParameterData
            or ParameterValueData.expression is not None
        ):
            return None
        ParameterData[PathValue] = ParameterValueData
    ExpectedData = {
        "FuzzyTolerance": (ValueKind.NUMBER, -1.0),
        "Intersection": (ValueKind.BOOLEAN, False),
        "Join": (ValueKind.INTEGER, 0),
        "Label": (ValueKind.STRING, ShellFeatureData.name),
        "Label2": (ValueKind.STRING, ""),
        "Mode": (ValueKind.INTEGER, 0),
        "Refine": (ValueKind.BOOLEAN, True),
        "Reversed": (ValueKind.BOOLEAN, True),
        "SupportTransform": (ValueKind.BOOLEAN, False),
        "Suppressed": (ValueKind.BOOLEAN, False),
        "Value": (ValueKind.LENGTH, ThicknessNumber),
        "Visibility": (ValueKind.BOOLEAN, True),
    }
    if set(ParameterData) != set(ExpectedData) or any(
        not _freecad_parameter_matches(
            ParameterData[PathValue],
            KindValue,
            ExpectedValue,
        )
        for PathValue, (KindValue, ExpectedValue) in ExpectedData.items()
    ):
        return None
    ThicknessParameter = ParameterData["Value"]
    return (
        PadDimension,
        _WriteDimension(
            "D1",
            ThicknessNumber,
            format(ThicknessNumber, ".15g"),
            ThicknessParameter.role,
        ),
    )


# FreeCAD boss-pattern validation proves pitch, count, sketch-normal direction, and body
def _FreeCadBossLinearPatternDimensions(
    DocumentData: CadDocument,
    SketchData: Sketch,
    PadFeature: FeatureStep,
    PatternFeatureData: FeatureStep,
    BoundsValue: tuple[float, float, float, float] | None,
) -> tuple[_WriteDimension, _WriteDimension, _WriteDimension] | None:
    TimelineData = tuple(
        ItemData
        for ItemData in sorted(
            DocumentData.feature_timeline,
            key=lambda ItemData: ItemData.order,
        )
        if not _is_native_system_feature(ItemData)
    )
    PatternDefinition = PatternFeatureData.definition
    PadDefinition = PadFeature.definition
    AllowedOwners = {SketchData.id, PadFeature.id, PatternFeatureData.id}
    if (
        BoundsValue is None
        or DocumentData.source.format_id.casefold() != "freecad.fcstd"
        or DocumentData.assembly is not None
        or tuple(DocumentData.sketches) != (SketchData,)
        or TimelineData != (PadFeature, PatternFeatureData)
        or len(DocumentData.bodies) != 1
        or DocumentData.bodies[0].final_feature_id != PatternFeatureData.id
        or PadFeature.order != 0
        or PatternFeatureData.order != 1
        or PadFeature.sketch_id != SketchData.id
        or PatternFeatureData.sketch_id is not None
        or PadFeature.input_feature_ids
        or PatternFeatureData.input_feature_ids != (PadFeature.id,)
        or PadFeature.selection_ids
        or len(PatternFeatureData.selection_ids) != 1
        or PadFeature.configuration_states
        or PatternFeatureData.configuration_states
        or PadFeature.suppressed
        or PatternFeatureData.suppressed
        or str(PadFeature.operation).casefold()
        not in {BooleanOperation.CREATE.value, BooleanOperation.JOIN.value}
        or PatternFeatureData.operation is not None
        or str(PatternFeatureData.kind).casefold() != FeatureKind.PATTERN.value
        or _freecad_type_id(SketchData.attributes) != "Sketcher::SketchObject"
        or _freecad_type_id(PadFeature.attributes) != "PartDesign::Pad"
        or _freecad_type_id(PatternFeatureData.attributes)
        != "PartDesign::LinearPattern"
        or not isinstance(PadDefinition, ExtrusionFeature)
        or PadDefinition.reversed
        or PadDefinition.symmetric
        or not isinstance(PatternDefinition, LinearPatternFeature)
        or PatternDefinition.reversed
        or PatternFeatureData.provenance is None
        or len(DocumentData.configurations) != 1
        or DocumentData.configurations[0].name.casefold() != "default"
        or not DocumentData.configurations[0].active
        or DocumentData.configurations[0].parent_id is not None
        or DocumentData.configurations[0].overrides
        or DocumentData.configurations[0].suppressed_feature_ids
        or len(DocumentData.selections) != 1
        or PatternFeatureData.selection_ids != (DocumentData.selections[0].id,)
        or PatternDefinition.direction_selection_id != DocumentData.selections[0].id
        or any(
            ItemData.owner_id not in AllowedOwners
            for ItemData in DocumentData.parameters
        )
    ):
        return None
    PadDimension = _FreeCadFeatureDimension(
        DocumentData,
        SketchData,
        PadFeature,
        "PartDesign::Pad",
        10.0,
        False,
    )
    SpacingDimension = _parameter_dimension(
        Parameter("", "D3", PatternDefinition.spacing)
    )
    OccurrenceCount = PatternDefinition.instance_count
    if (
        PadDimension is None
        or SpacingDimension is None
        or isinstance(OccurrenceCount, bool)
        or not isinstance(OccurrenceCount, int)
        or not 2 <= OccurrenceCount <= 1000
        or not math.isfinite(SpacingDimension.value_mm)
        or SpacingDimension.value_mm <= 0.0
        or SpacingDimension.value_mm > PadDimension.value_mm
    ):
        return None
    SelectionData = DocumentData.selections[0]
    SketchNativeName = (
        SketchData.provenance.native_id
        if SketchData.provenance is not None
        else SketchData.name
    )
    if (
        SelectionData.attributes.get("freecad_object")
        != PatternFeatureData.provenance.native_id
        or SelectionData.attributes.get("freecad_property") != "Direction"
        or SelectionData.attributes.get("freecad_target") != SketchNativeName
        or len(SelectionData.path) != 1
        or SelectionData.path[0].entity_kind != "native"
        or SelectionData.path[0].entity_id != SketchNativeName
        or SelectionData.path[0].subelement != "N_Axis"
    ):
        return None
    ParameterData: dict[str, Parameter] = {}
    for ParameterValueData in DocumentData.parameters:
        if ParameterValueData.owner_id != PatternFeatureData.id:
            continue
        PathValue = ParameterValueData.attributes.get("freecad_path")
        if (
            not isinstance(PathValue, str)
            or not PathValue
            or PathValue in ParameterData
            or ParameterValueData.expression is not None
        ):
            return None
        ParameterData[PathValue] = ParameterValueData
    SpacingNumber = SpacingDimension.value_mm
    LengthNumber = SpacingNumber * (OccurrenceCount - 1)
    ExpectedData = {
        "FuzzyTolerance": (ValueKind.NUMBER, -1.0),
        "Label": (ValueKind.STRING, PatternFeatureData.name),
        "Label2": (ValueKind.STRING, ""),
        "Length": (ValueKind.LENGTH, LengthNumber),
        "Length2": (ValueKind.LENGTH, 100.0),
        "Mode": (ValueKind.INTEGER, 0),
        "Mode2": (ValueKind.INTEGER, 0),
        "Occurrences": (ValueKind.INTEGER, OccurrenceCount),
        "Occurrences2": (ValueKind.INTEGER, 1),
        "Offset": (ValueKind.LENGTH, SpacingNumber),
        "Offset2": (ValueKind.LENGTH, 10.0),
        "Refine": (ValueKind.BOOLEAN, True),
        "Reversed": (ValueKind.BOOLEAN, False),
        "Reversed2": (ValueKind.BOOLEAN, False),
        "Suppressed": (ValueKind.BOOLEAN, False),
        "TransformMode": (ValueKind.INTEGER, 0),
        "Visibility": (ValueKind.BOOLEAN, True),
    }
    if set(ParameterData) != set(ExpectedData) or any(
        not _freecad_parameter_matches(
            ParameterData[PathValue],
            KindValue,
            ExpectedValue,
        )
        for PathValue, (KindValue, ExpectedValue) in ExpectedData.items()
    ):
        return None
    TerminalDepth = PadDimension.value_mm + SpacingNumber * (OccurrenceCount - 1)
    if not _HasFreeCadLinearPatternGeometry(
        DocumentData,
        PatternFeatureData.provenance.native_id,
        BoundsValue,
        TerminalDepth,
    ):
        return None
    CountParameter = ParameterData["Occurrences"]
    SpacingParameter = ParameterData["Length"]
    return (
        PadDimension,
        _WriteDimension(
            "D1",
            float(OccurrenceCount),
            str(OccurrenceCount),
            CountParameter.role,
        ),
        replace(
            SpacingDimension,
            name="D3",
            text=format(SpacingNumber, ".15g"),
            role=SpacingParameter.role,
        ),
    )


# decoded OpenCascade topology proves the pattern produces one exact fused prism
def _HasFreeCadLinearPatternGeometry(
    DocumentData: CadDocument,
    PatternNativeName: str,
    BoundsValue: tuple[float, float, float, float],
    TerminalDepth: float,
) -> bool:
    ShapePayload = next(
        (
            ItemData.data
            for ItemData in DocumentData.brep_payloads
            if ItemData.source_stream == f"{PatternNativeName}.Shape.brp"
            and ItemData.data
        ),
        None,
    )
    if ShapePayload is None:
        return False
    ModelData = decode_ascii_brep(
        ShapePayload,
        id_prefix="freecad:linear-pattern-proof",
    )
    if (
        ModelData is None
        or ModelData.validate()
        or len(ModelData.bodies) != 1
        or len(ModelData.regions) != 1
        or len(ModelData.shells) != 1
        or len(ModelData.faces) != 6
        or len(ModelData.edges) != 12
        or len(ModelData.vertices) != 8
    ):
        return False
    CoordinateData = (
        min(ItemData.point.x for ItemData in ModelData.vertices),
        min(ItemData.point.y for ItemData in ModelData.vertices),
        max(ItemData.point.x for ItemData in ModelData.vertices),
        max(ItemData.point.y for ItemData in ModelData.vertices),
        min(ItemData.point.z for ItemData in ModelData.vertices),
        max(ItemData.point.z for ItemData in ModelData.vertices),
    )
    ExpectedData = (*BoundsValue, 0.0, TerminalDepth)
    return all(
        math.isclose(
            ActualValue,
            ExpectedValue,
            rel_tol=0.0,
            abs_tol=1.0e-8,
        )
        for ActualValue, ExpectedValue in zip(
            CoordinateData,
            ExpectedData,
            strict=True,
        )
    )


# FreeCAD circular-pattern validation proves angle, count, selected axis, and body
def _FreeCadBossCircularPatternDimensions(
    DocumentData: CadDocument,
    SketchData: Sketch,
    PadFeature: FeatureStep,
    PatternFeatureData: FeatureStep,
    BoundsValue: tuple[float, float, float, float] | None,
) -> tuple[_WriteDimension, _WriteDimension, _WriteDimension] | None:
    TimelineData = tuple(
        ItemData
        for ItemData in sorted(
            DocumentData.feature_timeline,
            key=lambda ItemData: ItemData.order,
        )
        if not _is_native_system_feature(ItemData)
    )
    PatternDefinition = PatternFeatureData.definition
    PadDefinition = PadFeature.definition
    AllowedOwners = {SketchData.id, PadFeature.id, PatternFeatureData.id}
    if (
        BoundsValue is None
        or DocumentData.source.format_id.casefold() != "freecad.fcstd"
        or DocumentData.assembly is not None
        or tuple(DocumentData.sketches) != (SketchData,)
        or TimelineData != (PadFeature, PatternFeatureData)
        or len(DocumentData.bodies) != 1
        or DocumentData.bodies[0].final_feature_id != PatternFeatureData.id
        or PadFeature.order != 0
        or PatternFeatureData.order != 1
        or PadFeature.sketch_id != SketchData.id
        or PatternFeatureData.sketch_id is not None
        or PadFeature.input_feature_ids
        or PatternFeatureData.input_feature_ids != (PadFeature.id,)
        or PadFeature.selection_ids
        or len(PatternFeatureData.selection_ids) != 1
        or PadFeature.configuration_states
        or PatternFeatureData.configuration_states
        or PadFeature.suppressed
        or PatternFeatureData.suppressed
        or str(PadFeature.operation).casefold()
        not in {BooleanOperation.CREATE.value, BooleanOperation.JOIN.value}
        or PatternFeatureData.operation is not None
        or str(PatternFeatureData.kind).casefold() != FeatureKind.PATTERN.value
        or _freecad_type_id(SketchData.attributes) != "Sketcher::SketchObject"
        or _freecad_type_id(PadFeature.attributes) != "PartDesign::Pad"
        or _freecad_type_id(PatternFeatureData.attributes) != "PartDesign::PolarPattern"
        or not isinstance(PadDefinition, ExtrusionFeature)
        or PadDefinition.reversed
        or PadDefinition.symmetric
        or not isinstance(PatternDefinition, CircularPatternFeature)
        or PatternDefinition.reversed
        or PatternFeatureData.provenance is None
        or len(DocumentData.configurations) != 1
        or DocumentData.configurations[0].name.casefold() != "default"
        or not DocumentData.configurations[0].active
        or DocumentData.configurations[0].parent_id is not None
        or DocumentData.configurations[0].overrides
        or DocumentData.configurations[0].suppressed_feature_ids
        or len(DocumentData.selections) != 1
        or PatternFeatureData.selection_ids != (DocumentData.selections[0].id,)
        or PatternDefinition.axis_selection_id != DocumentData.selections[0].id
        or any(
            ItemData.owner_id not in AllowedOwners
            for ItemData in DocumentData.parameters
        )
    ):
        return None
    PadDimension = _FreeCadFeatureDimension(
        DocumentData,
        SketchData,
        PadFeature,
        "PartDesign::Pad",
        10.0,
        False,
    )
    AngleValue = PatternDefinition.angle
    AngleNumber = AngleValue.value
    OccurrenceCount = PatternDefinition.instance_count
    if (
        PadDimension is None
        or AngleValue.kind is not ValueKind.ANGLE
        or AngleValue.unit.casefold() not in {"deg", "degree", "degrees"}
        or isinstance(AngleNumber, bool)
        or not isinstance(AngleNumber, (int, float))
        or not math.isfinite(float(AngleNumber))
        or not 0.0 < float(AngleNumber) <= 360.0
        or isinstance(OccurrenceCount, bool)
        or not isinstance(OccurrenceCount, int)
        or not 2 <= OccurrenceCount <= 1000
        or any(
            not math.isclose(ActualValue, ExpectedValue, rel_tol=0.0, abs_tol=1.0e-10)
            for ActualValue, ExpectedValue in zip(
                BoundsValue,
                (0.0, 0.0, 10.0, 5.0),
                strict=True,
            )
        )
    ):
        return None
    SelectionData = DocumentData.selections[0]
    SketchNativeName = (
        SketchData.provenance.native_id
        if SketchData.provenance is not None
        else SketchData.name
    )
    if (
        SelectionData.attributes.get("freecad_object")
        != PatternFeatureData.provenance.native_id
        or SelectionData.attributes.get("freecad_property") != "Axis"
        or SelectionData.attributes.get("freecad_target") != SketchNativeName
        or len(SelectionData.path) != 1
        or SelectionData.path[0].entity_kind != "native"
        or SelectionData.path[0].entity_id != SketchNativeName
        or SelectionData.path[0].subelement != "N_Axis"
    ):
        return None
    ParameterData: dict[str, Parameter] = {}
    for ParameterValueData in DocumentData.parameters:
        if ParameterValueData.owner_id != PatternFeatureData.id:
            continue
        PathValue = ParameterValueData.attributes.get("freecad_path")
        if (
            not isinstance(PathValue, str)
            or not PathValue
            or PathValue in ParameterData
            or ParameterValueData.expression is not None
        ):
            return None
        ParameterData[PathValue] = ParameterValueData
    ExpectedData = {
        "Angle": (ValueKind.ANGLE, float(AngleNumber)),
        "FuzzyTolerance": (ValueKind.NUMBER, -1.0),
        "Label": (ValueKind.STRING, PatternFeatureData.name),
        "Label2": (ValueKind.STRING, ""),
        "Mode": (ValueKind.INTEGER, 0),
        "Occurrences": (ValueKind.INTEGER, OccurrenceCount),
        "Offset": (ValueKind.ANGLE, 120.0),
        "Refine": (ValueKind.BOOLEAN, True),
        "Reversed": (ValueKind.BOOLEAN, False),
        "Suppressed": (ValueKind.BOOLEAN, False),
        "TransformMode": (ValueKind.INTEGER, 0),
        "Visibility": (ValueKind.BOOLEAN, True),
    }
    if set(ParameterData) != set(ExpectedData) or any(
        not _freecad_parameter_matches(
            ParameterData[PathValue],
            KindValue,
            ExpectedValue,
        )
        for PathValue, (KindValue, ExpectedValue) in ExpectedData.items()
    ):
        return None
    if not _HasFreeCadCircularPatternGeometry(
        DocumentData,
        PatternFeatureData.provenance.native_id,
        BoundsValue,
        OccurrenceCount,
        float(AngleNumber),
        PadDimension.value_mm,
    ):
        return None
    return (
        PadDimension,
        _WriteDimension(
            "D1",
            float(OccurrenceCount),
            str(OccurrenceCount),
            ParameterData["Occurrences"].role,
        ),
        _WriteDimension(
            "D3",
            float(AngleNumber),
            f"{float(AngleNumber):.15g}°",
            ParameterData["Angle"].role,
        ),
    )


# decoded OpenCascade topology proves the circular pattern produces one fused body
def _HasFreeCadCircularPatternGeometry(
    DocumentData: CadDocument,
    PatternNativeName: str,
    BoundsValue: tuple[float, float, float, float],
    OccurrenceCount: int,
    AngleDegrees: float,
    PadDepth: float,
) -> bool:
    ShapePayload = next(
        (
            ItemData.data
            for ItemData in DocumentData.brep_payloads
            if ItemData.source_stream == f"{PatternNativeName}.Shape.brp"
            and ItemData.data
        ),
        None,
    )
    if ShapePayload is None:
        return False
    ModelData = decode_ascii_brep(
        ShapePayload,
        id_prefix="freecad:circular-pattern-proof",
    )
    if (
        ModelData is None
        or ModelData.validate()
        or len(ModelData.bodies) != 1
        or len(ModelData.regions) != 1
        or len(ModelData.shells) != 1
        or not ModelData.faces
        or not ModelData.edges
        or not ModelData.vertices
    ):
        return False
    CoordinateData = (
        min(ItemData.point.x for ItemData in ModelData.vertices),
        min(ItemData.point.y for ItemData in ModelData.vertices),
        max(ItemData.point.x for ItemData in ModelData.vertices),
        max(ItemData.point.y for ItemData in ModelData.vertices),
        min(ItemData.point.z for ItemData in ModelData.vertices),
        max(ItemData.point.z for ItemData in ModelData.vertices),
    )
    ExpectedData = (
        *_CircularPatternBounds(BoundsValue, OccurrenceCount, AngleDegrees),
        0.0,
        PadDepth,
    )
    return all(
        math.isclose(
            ActualValue,
            ExpectedValue,
            rel_tol=0.0,
            abs_tol=1.0e-8,
        )
        for ActualValue, ExpectedValue in zip(
            CoordinateData,
            ExpectedData,
            strict=True,
        )
    )


# native OpenCascade face order proves that the selected source face is the open top
def _HasFreeCadTopFace(
    DocumentData: CadDocument,
    PadNativeName: str,
    SubelementName: str,
    PadDepth: float,
) -> bool:
    MatchValue = re.fullmatch(r"Face([1-9][0-9]*)", SubelementName)
    if MatchValue is None:
        return False
    ShapePayload = next(
        (
            ItemData.data
            for ItemData in DocumentData.brep_payloads
            if ItemData.source_stream == f"{PadNativeName}.Shape.brp" and ItemData.data
        ),
        None,
    )
    if ShapePayload is None:
        return False
    ModelData = decode_ascii_brep(
        ShapePayload,
        id_prefix="freecad:shell-proof",
    )
    if ModelData is None:
        return False
    FaceData = tuple(
        sorted(
            ModelData.faces,
            key=lambda ItemData: int(ItemData.id.rsplit(":", 1)[1]),
        )
    )
    FaceIndex = int(MatchValue.group(1)) - 1
    if FaceIndex < 0 or FaceIndex >= len(FaceData):
        return False
    SelectedFace = FaceData[FaceIndex]
    SurfaceData = next(
        (
            ItemData
            for ItemData in ModelData.surfaces
            if ItemData.id == SelectedFace.surface_id
        ),
        None,
    )
    ToleranceValue = 1.0e-8
    return (
        isinstance(SurfaceData, PlaneSurface)
        and SelectedFace.same_sense
        and math.isclose(
            SurfaceData.origin.z,
            PadDepth,
            rel_tol=0.0,
            abs_tol=ToleranceValue,
        )
        and math.isclose(
            SurfaceData.normal.x,
            0.0,
            rel_tol=0.0,
            abs_tol=ToleranceValue,
        )
        and math.isclose(
            SurfaceData.normal.y,
            0.0,
            rel_tol=0.0,
            abs_tol=ToleranceValue,
        )
        and math.isclose(
            SurfaceData.normal.z,
            1.0,
            rel_tol=0.0,
            abs_tol=ToleranceValue,
        )
    )


# native OpenCascade edge order proves that the selected source edge has the target locus
def _HasFreeCadMaxCornerEdge(
    DocumentData: CadDocument,
    PadNativeName: str,
    SubelementName: str,
    BoundsValue: tuple[float, float, float, float],
    PadDepth: float,
) -> bool:
    MatchValue = re.fullmatch(r"Edge([1-9][0-9]*)", SubelementName)
    if MatchValue is None:
        return False
    ShapePayload = next(
        (
            ItemData.data
            for ItemData in DocumentData.brep_payloads
            if ItemData.source_stream == f"{PadNativeName}.Shape.brp" and ItemData.data
        ),
        None,
    )
    if ShapePayload is None:
        return False
    ModelData = decode_ascii_brep(
        ShapePayload,
        id_prefix="freecad:fillet-proof",
    )
    if ModelData is None:
        return False
    EdgeData = tuple(
        sorted(
            ModelData.edges,
            key=lambda ItemData: int(ItemData.id.rsplit(":", 1)[1]),
        )
    )
    EdgeIndex = int(MatchValue.group(1)) - 1
    if EdgeIndex < 0 or EdgeIndex >= len(EdgeData):
        return False
    SelectedEdge = EdgeData[EdgeIndex]
    VertexData = {ItemData.id: ItemData for ItemData in ModelData.vertices}
    CurveData = {ItemData.id: ItemData for ItemData in ModelData.curves}
    StartVertex = VertexData.get(SelectedEdge.start_vertex_id)
    EndVertex = VertexData.get(SelectedEdge.end_vertex_id)
    SelectedCurve = CurveData.get(SelectedEdge.curve_id)
    if (
        StartVertex is None
        or EndVertex is None
        or not isinstance(SelectedCurve, LineCurve)
        or SelectedEdge.degenerate
    ):
        return False
    MaximumX = BoundsValue[2]
    MaximumY = BoundsValue[3]
    ToleranceValue = 1.0e-8
    return (
        all(
            math.isclose(
                ItemData.point.x,
                MaximumX,
                rel_tol=0.0,
                abs_tol=ToleranceValue,
            )
            and math.isclose(
                ItemData.point.y,
                MaximumY,
                rel_tol=0.0,
                abs_tol=ToleranceValue,
            )
            for ItemData in (StartVertex, EndVertex)
        )
        and math.isclose(
            min(StartVertex.point.z, EndVertex.point.z),
            0.0,
            rel_tol=0.0,
            abs_tol=ToleranceValue,
        )
        and math.isclose(
            max(StartVertex.point.z, EndVertex.point.z),
            PadDepth,
            rel_tol=0.0,
            abs_tol=ToleranceValue,
        )
    )


# through-all validation proves inactive FreeCAD lengths without inventing a target D1
def HasFreeCadThroughAllFeature(
    DocumentData: CadDocument,
    SketchData: Sketch,
    FeatureData: FeatureStep,
) -> bool:
    if (
        FeatureData.sketch_id != SketchData.id
        or str(FeatureData.kind).casefold() != FeatureKind.EXTRUSION.value
        or _freecad_type_id(SketchData.attributes) != "Sketcher::SketchObject"
        or _freecad_type_id(FeatureData.attributes) != "PartDesign::Pocket"
        or not isinstance(FeatureData.definition, ExtrusionFeature)
    ):
        return False
    DefinitionData = FeatureData.definition
    SupportPlaneValue = next(
        (
            ItemData
            for ItemData in DocumentData.support_planes
            if ItemData.id == SketchData.support_plane_id
        ),
        None,
    )
    if (
        str(DefinitionData.end_condition).casefold()
        != ExtrusionEndCondition.THROUGH_ALL.value
        or DefinitionData.symmetric
        or DefinitionData.second_end_condition is not None
        or DefinitionData.up_to_reference
        or DefinitionData.second_up_to_reference
        or not _parameter_value_matches(
            DefinitionData.length,
            5.0,
            ValueKind.LENGTH,
        )
        or not _parameter_value_matches(
            DefinitionData.second_length,
            5.0,
            ValueKind.LENGTH,
        )
        or not _parameter_value_matches(DefinitionData.offset, 0.0, ValueKind.LENGTH)
        or not _parameter_value_matches(
            DefinitionData.second_offset,
            0.0,
            ValueKind.LENGTH,
        )
        or not _parameter_value_matches(
            DefinitionData.draft_angle,
            0.0,
            ValueKind.ANGLE,
        )
        or not _parameter_value_matches(
            DefinitionData.second_draft_angle,
            0.0,
            ValueKind.ANGLE,
        )
        or DefinitionData.direction is None
        or SupportPlaneValue is None
        or not all(
            math.isclose(LeftValue, -RightValue, abs_tol=1e-12)
            for LeftValue, RightValue in zip(
                (
                    DefinitionData.direction.x,
                    DefinitionData.direction.y,
                    DefinitionData.direction.z,
                ),
                (
                    SupportPlaneValue.transform.z_axis.x,
                    SupportPlaneValue.transform.z_axis.y,
                    SupportPlaneValue.transform.z_axis.z,
                ),
                strict=True,
            )
        )
    ):
        return False
    ParameterData: dict[str, Parameter] = {}
    for ParameterValueData in DocumentData.parameters:
        if ParameterValueData.owner_id != FeatureData.id:
            continue
        PathValue = ParameterValueData.attributes.get("freecad_path")
        if (
            not isinstance(PathValue, str)
            or not PathValue
            or PathValue in ParameterData
            or ParameterValueData.expression is not None
        ):
            return False
        ParameterData[PathValue] = ParameterValueData
    ExpectedData = {
        "AllowMultiFace": (ValueKind.BOOLEAN, True),
        "AlongSketchNormal": (ValueKind.BOOLEAN, True),
        "Label": (ValueKind.STRING, None),
        "Label2": (ValueKind.STRING, None),
        "Length": (ValueKind.LENGTH, 5.0),
        "Length2": (ValueKind.LENGTH, 5.0),
        "Midplane": (ValueKind.BOOLEAN, False),
        "Offset": (ValueKind.LENGTH, 0.0),
        "Offset2": (ValueKind.LENGTH, 0.0),
        "Refine": (ValueKind.BOOLEAN, True),
        "Reversed": (ValueKind.BOOLEAN, DefinitionData.reversed),
        "SideType": (ValueKind.INTEGER, 0),
        "Suppressed": (ValueKind.BOOLEAN, False),
        "TaperAngle": (ValueKind.ANGLE, 0.0),
        "TaperAngle2": (ValueKind.ANGLE, 0.0),
        "Type": (ValueKind.INTEGER, 1),
        "Type2": (ValueKind.INTEGER, 0),
        "UseCustomVector": (ValueKind.BOOLEAN, False),
        "Visibility": (ValueKind.BOOLEAN, True),
    }
    return set(ExpectedData) <= set(ParameterData) and all(
        _freecad_parameter_matches(
            ParameterData[PathValue],
            KindValue,
            ExpectedValue,
        )
        for PathValue, (KindValue, ExpectedValue) in ExpectedData.items()
    )


# per-feature FreeCAD validation maps only active blind-extrusion semantics into D1
def _FreeCadFeatureDimension(
    DocumentData: CadDocument,
    SketchData: Sketch,
    FeatureData: FeatureStep,
    ExpectedTypeId: str,
    ExpectedSecondLength: float,
    ExpectedVisibility: bool,
) -> _WriteDimension | None:
    if (
        FeatureData.sketch_id != SketchData.id
        or str(FeatureData.kind).casefold() != FeatureKind.EXTRUSION.value
        or _freecad_type_id(SketchData.attributes) != "Sketcher::SketchObject"
        or _freecad_type_id(FeatureData.attributes) != ExpectedTypeId
        or not isinstance(FeatureData.definition, ExtrusionFeature)
    ):
        return None
    DefinitionData = FeatureData.definition
    SupportPlaneValue = next(
        (
            ItemData
            for ItemData in DocumentData.support_planes
            if ItemData.id == SketchData.support_plane_id
        ),
        None,
    )
    DirectionSign = -1.0 if ExpectedTypeId == "PartDesign::Pocket" else 1.0
    if (
        str(DefinitionData.end_condition).casefold()
        != ExtrusionEndCondition.BLIND.value
        or (DefinitionData.reversed and DefinitionData.symmetric)
        or DefinitionData.second_end_condition is not None
        or DefinitionData.up_to_reference
        or DefinitionData.second_up_to_reference
        or not _parameter_value_matches(
            DefinitionData.second_length,
            ExpectedSecondLength,
            ValueKind.LENGTH,
        )
        or not _parameter_value_matches(DefinitionData.offset, 0.0, ValueKind.LENGTH)
        or not _parameter_value_matches(
            DefinitionData.second_offset, 0.0, ValueKind.LENGTH
        )
        or not _parameter_value_matches(
            DefinitionData.draft_angle, 0.0, ValueKind.ANGLE
        )
        or not _parameter_value_matches(
            DefinitionData.second_draft_angle, 0.0, ValueKind.ANGLE
        )
        or DefinitionData.direction is None
        or SupportPlaneValue is None
        or not all(
            math.isclose(LeftValue, RightValue, abs_tol=1e-12)
            for LeftValue, RightValue in zip(
                (
                    DefinitionData.direction.x,
                    DefinitionData.direction.y,
                    DefinitionData.direction.z,
                ),
                (
                    DirectionSign * SupportPlaneValue.transform.z_axis.x,
                    DirectionSign * SupportPlaneValue.transform.z_axis.y,
                    DirectionSign * SupportPlaneValue.transform.z_axis.z,
                ),
                strict=True,
            )
        )
    ):
        return None
    DimensionData = _parameter_dimension(Parameter("", "D1", DefinitionData.length))
    if DimensionData is None or DimensionData.value_mm <= 0.0:
        return None
    ParameterData: dict[str, Parameter] = {}
    for ParameterValueData in DocumentData.parameters:
        if ParameterValueData.owner_id != FeatureData.id:
            continue
        PathValue = ParameterValueData.attributes.get("freecad_path")
        if (
            not isinstance(PathValue, str)
            or not PathValue
            or PathValue in ParameterData
            or ParameterValueData.expression is not None
        ):
            return None
        ParameterData[PathValue] = ParameterValueData
    ExpectedData = {
        "AllowMultiFace": (ValueKind.BOOLEAN, True),
        "AlongSketchNormal": (ValueKind.BOOLEAN, True),
        "Label": (ValueKind.STRING, None),
        "Label2": (ValueKind.STRING, None),
        "Length": (ValueKind.LENGTH, DimensionData.value_mm),
        "Length2": (ValueKind.LENGTH, ExpectedSecondLength),
        "Midplane": (ValueKind.BOOLEAN, DefinitionData.symmetric),
        "Offset": (ValueKind.LENGTH, 0.0),
        "Offset2": (ValueKind.LENGTH, 0.0),
        "Refine": (ValueKind.BOOLEAN, True),
        "Reversed": (ValueKind.BOOLEAN, DefinitionData.reversed),
        "SideType": (ValueKind.INTEGER, 2 if DefinitionData.symmetric else 0),
        "Suppressed": (ValueKind.BOOLEAN, False),
        "TaperAngle": (ValueKind.ANGLE, 0.0),
        "TaperAngle2": (ValueKind.ANGLE, 0.0),
        "Type": (ValueKind.INTEGER, 0),
        "Type2": (ValueKind.INTEGER, 0),
        "UseCustomVector": (ValueKind.BOOLEAN, False),
        "Visibility": (ValueKind.BOOLEAN, ExpectedVisibility),
    }
    if not set(ExpectedData) <= set(ParameterData):
        return None
    if any(
        not _freecad_parameter_matches(
            ParameterData[PathValue], KindValue, ExpectedValue
        )
        for PathValue, (KindValue, ExpectedValue) in ExpectedData.items()
    ):
        return None
    return DimensionData


# freecad pad settings must agree before a recovered native program is eligible
def _freecad_single_boss_dimension(
    document: CadDocument,
    sketch: Sketch,
    feature: FeatureStep,
) -> _WriteDimension | None:
    if (
        document.source.format_id.casefold() != "freecad.fcstd"
        or document.assembly is not None
        or document.selections
        or len(document.sketches) != 1
        or len(
            tuple(
                item
                for item in document.feature_timeline
                if not _is_native_system_feature(item)
            )
        )
        != 1
        or len(document.bodies) != 1
        or document.bodies[0].final_feature_id != feature.id
        or feature.sketch_id != sketch.id
        or feature.order != 0
        or str(feature.kind).casefold() != FeatureKind.EXTRUSION.value
        or str(feature.operation).casefold()
        not in {BooleanOperation.CREATE.value, BooleanOperation.JOIN.value}
        or _freecad_type_id(sketch.attributes) != "Sketcher::SketchObject"
        or _freecad_type_id(feature.attributes) != "PartDesign::Pad"
        or len(document.configurations) != 1
        or document.configurations[0].name.casefold() != "default"
        or not document.configurations[0].active
        or document.configurations[0].parent_id is not None
        or document.configurations[0].overrides
        or document.configurations[0].suppressed_feature_ids
        or not isinstance(feature.definition, ExtrusionFeature)
    ):
        return None
    definition = feature.definition
    SupportPlaneValue = next(
        (
            ItemData
            for ItemData in document.support_planes
            if ItemData.id == sketch.support_plane_id
        ),
        None,
    )
    if (
        str(definition.end_condition).casefold() != ExtrusionEndCondition.BLIND.value
        or (definition.reversed and definition.symmetric)
        or definition.second_end_condition is not None
        or definition.up_to_reference
        or definition.second_up_to_reference
        or not _parameter_value_matches(
            definition.second_length, 10.0, ValueKind.LENGTH
        )
        or not _parameter_value_matches(definition.offset, 0.0, ValueKind.LENGTH)
        or not _parameter_value_matches(definition.second_offset, 0.0, ValueKind.LENGTH)
        or not _parameter_value_matches(definition.draft_angle, 0.0, ValueKind.ANGLE)
        or not _parameter_value_matches(
            definition.second_draft_angle, 0.0, ValueKind.ANGLE
        )
        or definition.direction is None
        or SupportPlaneValue is None
        or not all(
            math.isclose(LeftValue, RightValue, abs_tol=1e-12)
            for LeftValue, RightValue in zip(
                (
                    definition.direction.x,
                    definition.direction.y,
                    definition.direction.z,
                ),
                (
                    SupportPlaneValue.transform.z_axis.x,
                    SupportPlaneValue.transform.z_axis.y,
                    SupportPlaneValue.transform.z_axis.z,
                ),
                strict=True,
            )
        )
    ):
        return None
    dimension = _parameter_dimension(Parameter("", "D1", definition.length))
    if dimension is None or dimension.value_mm <= 0.0:
        return None
    parameters: dict[str, Parameter] = {}
    for parameter in document.parameters:
        if parameter.owner_id == sketch.id:
            continue
        path = parameter.attributes.get("freecad_path")
        if (
            parameter.owner_id != feature.id
            or not isinstance(path, str)
            or not path
            or path in parameters
            or parameter.expression is not None
        ):
            return None
        parameters[path] = parameter
    expected = {
        "AllowMultiFace": (ValueKind.BOOLEAN, True),
        "AlongSketchNormal": (ValueKind.BOOLEAN, True),
        "Label": (ValueKind.STRING, None),
        "Label2": (ValueKind.STRING, None),
        "Length": (ValueKind.LENGTH, dimension.value_mm),
        "Length2": (ValueKind.LENGTH, 10.0),
        "Midplane": (ValueKind.BOOLEAN, definition.symmetric),
        "Offset": (ValueKind.LENGTH, 0.0),
        "Offset2": (ValueKind.LENGTH, 0.0),
        "Refine": (ValueKind.BOOLEAN, True),
        "Reversed": (ValueKind.BOOLEAN, definition.reversed),
        "SideType": (ValueKind.INTEGER, 2 if definition.symmetric else 0),
        "Suppressed": (ValueKind.BOOLEAN, False),
        "TaperAngle": (ValueKind.ANGLE, 0.0),
        "TaperAngle2": (ValueKind.ANGLE, 0.0),
        "Type": (ValueKind.INTEGER, 0),
        "Type2": (ValueKind.INTEGER, 0),
        "UseCustomVector": (ValueKind.BOOLEAN, False),
        "Visibility": (ValueKind.BOOLEAN, True),
    }
    if not set(expected) <= set(parameters):
        return None
    if any(
        not _freecad_parameter_matches(parameters[path], kind, value)
        for path, (kind, value) in expected.items()
    ):
        return None
    return dimension


def _freecad_type_id(attributes: Mapping[str, Any]) -> str:
    value = attributes.get("freecad")
    return str(value.get("type_id", "")) if isinstance(value, Mapping) else ""


# full FreeCAD revolutions are accepted only when every inactive mode stays at its default
def _FreeCadSingleRevolutionDimension(
    DocumentData: CadDocument,
    SketchData: Sketch,
    FeatureData: FeatureStep,
) -> _WriteDimension | None:
    DefinitionData = FeatureData.definition
    TimelineData = tuple(
        ItemData
        for ItemData in sorted(
            DocumentData.feature_timeline,
            key=lambda ItemData: ItemData.order,
        )
        if not _is_native_system_feature(ItemData)
    )
    if (
        DocumentData.source.format_id.casefold() != "freecad.fcstd"
        or DocumentData.assembly is not None
        or tuple(DocumentData.sketches) != (SketchData,)
        or TimelineData != (FeatureData,)
        or len(DocumentData.bodies) != 1
        or DocumentData.bodies[0].final_feature_id != FeatureData.id
        or FeatureData.order != 0
        or FeatureData.sketch_id != SketchData.id
        or FeatureData.input_feature_ids
        or FeatureData.configuration_states
        or FeatureData.suppressed
        or str(FeatureData.kind).casefold() != FeatureKind.REVOLUTION.value
        or str(FeatureData.operation).casefold() != BooleanOperation.CREATE.value
        or _freecad_type_id(SketchData.attributes) != "Sketcher::SketchObject"
        or _freecad_type_id(FeatureData.attributes) != "PartDesign::Revolution"
        or not isinstance(DefinitionData, NativeFeatureDefinition)
        or DefinitionData.format_id.casefold() != "freecad.fcstd"
        or DefinitionData.type_id != "PartDesign::Revolution"
        or FeatureData.provenance is None
        or len(DocumentData.configurations) != 1
        or DocumentData.configurations[0].name.casefold() != "default"
        or not DocumentData.configurations[0].active
        or DocumentData.configurations[0].parent_id is not None
        or DocumentData.configurations[0].overrides
        or DocumentData.configurations[0].suppressed_feature_ids
        or len(DocumentData.selections) != 1
        or FeatureData.selection_ids != (DocumentData.selections[0].id,)
    ):
        return None
    AxisSelection = DocumentData.selections[0]
    if (
        AxisSelection.attributes.get("freecad_object")
        != FeatureData.provenance.native_id
        or AxisSelection.attributes.get("freecad_property") != "ReferenceAxis"
        or len(AxisSelection.path) != 1
        or AxisSelection.path[0].entity_id != SketchData.name
        or AxisSelection.path[0].subelement != VERTICAL_AXIS_SUBELEMENT
    ):
        return None
    ParameterData: dict[str, Parameter] = {}
    for ParameterValueData in DocumentData.parameters:
        if ParameterValueData.owner_id != FeatureData.id:
            return None
        PathValue = ParameterValueData.attributes.get("freecad_path")
        if (
            not isinstance(PathValue, str)
            or not PathValue
            or PathValue in ParameterData
            or ParameterValueData.expression is not None
        ):
            return None
        ParameterData[PathValue] = ParameterValueData
    ExpectedData = {
        "AllowMultiFace": (ValueKind.BOOLEAN, True),
        "Angle": (ValueKind.ANGLE, 360.0),
        "Angle2": (ValueKind.ANGLE, 0.0),
        "FuseOrder": (ValueKind.INTEGER, 0),
        "FuzzyTolerance": (ValueKind.NUMBER, -1.0),
        "Label": (ValueKind.STRING, FeatureData.name),
        "Label2": (ValueKind.STRING, ""),
        "Midplane": (ValueKind.BOOLEAN, False),
        "Refine": (ValueKind.BOOLEAN, True),
        "Reversed": (ValueKind.BOOLEAN, False),
        "Suppressed": (ValueKind.BOOLEAN, False),
        "Type": (ValueKind.INTEGER, 0),
        "Visibility": (ValueKind.BOOLEAN, True),
    }
    if set(ParameterData) != set(ExpectedData) or any(
        not _freecad_parameter_matches(
            ParameterData[PathValue],
            KindValue,
            ExpectedValue,
        )
        for PathValue, (KindValue, ExpectedValue) in ExpectedData.items()
    ):
        return None
    AngleParameter = ParameterData["Angle"]
    if AngleParameter.value.unit.casefold() not in {"deg", "degree", "degrees"}:
        return None
    return _WriteDimension(
        "D1",
        360.0,
        "360°",
        AngleParameter.role,
    )


def _freecad_parameter_matches(
    parameter: Parameter,
    kind: ValueKind,
    expected: Any,
) -> bool:
    value = parameter.value
    if value.kind is not kind:
        return False
    if expected is None:
        return isinstance(value.value, str)
    if kind is ValueKind.LENGTH:
        dimension = _parameter_dimension(parameter)
        return dimension is not None and math.isclose(
            dimension.value_mm,
            float(expected),
            rel_tol=0.0,
            abs_tol=1e-10,
        )
    if kind in {ValueKind.NUMBER, ValueKind.ANGLE}:
        return (
            not isinstance(value.value, bool)
            and isinstance(value.value, (int, float))
            and math.isfinite(float(value.value))
            and math.isclose(
                float(value.value),
                float(expected),
                rel_tol=0.0,
                abs_tol=1e-10,
            )
        )
    return value.value == expected


def _parameter_value_matches(
    value: Any,
    expected: float,
    kind: ValueKind,
) -> bool:
    if value is None or value.kind is not kind:
        return False
    parameter = _parameter_dimension(Parameter("", "D1", value))
    if kind is ValueKind.LENGTH:
        return parameter is not None and math.isclose(
            parameter.value_mm,
            expected,
            rel_tol=0.0,
            abs_tol=1e-10,
        )
    return (
        not isinstance(value.value, bool)
        and isinstance(value.value, (int, float))
        and math.isfinite(float(value.value))
        and math.isclose(
            float(value.value),
            expected,
            rel_tol=0.0,
            abs_tol=1e-10,
        )
    )


def _write_rectangle_bounds(
    sketch: _WriteObject,
) -> tuple[float, float, float, float] | None:
    if sketch.kind != "Sketch" or not sketch.payload:
        return None
    markers = list(_parse_markers(sketch.payload, 0, len(sketch.payload)))
    profiles, _, _ = _profiles(markers, ())
    if len(profiles) != 1 or profiles[0].kind != "rectangle":
        return None
    coordinates = profiles[0].coordinates
    if len(coordinates) != 4 or not all(math.isfinite(value) for value in coordinates):
        return None
    return coordinates


# circular profile recovery supplies the centre and radius needed by the typed program
def _write_circle_profile(
    SketchObject: _WriteObject,
) -> tuple[float, float, float] | None:
    if SketchObject.kind != "Sketch" or not SketchObject.payload:
        return None
    MarkersData = list(
        _parse_markers(SketchObject.payload, 0, len(SketchObject.payload))
    )
    CoordinateData = tuple(
        ItemData for ItemData in MarkersData if ItemData.coordinates_mm is not None
    )
    if (
        len(CoordinateData) != 2
        or CoordinateData[0].semantic != "circle"
        or CoordinateData[1].semantic != "point"
    ):
        return None
    CenterData = CoordinateData[0].coordinates_mm
    RimData = CoordinateData[1].coordinates_mm
    if CenterData is None or RimData is None:
        return None
    RadiusValue = math.hypot(RimData[0] - CenterData[0], RimData[1] - CenterData[1])
    if not all(math.isfinite(ItemData) for ItemData in (*CenterData, RadiusValue)):
        return None
    if RadiusValue <= 0.0:
        return None
    return CenterData[0], CenterData[1], RadiusValue


def _is_native_system_feature(feature: FeatureStep) -> bool:
    native_id = feature.attributes.get("native_object_id")
    return (
        isinstance(native_id, int)
        and not isinstance(native_id, bool)
        and native_id in _SYSTEM_OBJECT_IDS
        and str(feature.kind).casefold()
        in {FeatureKind.NATIVE.value, FeatureKind.REFERENCE.value}
    )


def _native_system_name(feature: FeatureStep | None, fallback: str) -> str:
    if feature is None:
        return fallback
    properties = feature.attributes.get("native_properties")
    if isinstance(properties, Mapping):
        name = properties.get("Name")
        if isinstance(name, str):
            return name
    return feature.name or fallback


def _write_sketch(
    sketch: Sketch,
    parameters: dict[str, Parameter],
    object_ids: dict[str, int],
    native_feature: FeatureStep | None = None,
) -> _WriteObject:
    object_id = object_ids[f"sketch:{sketch.id}"]
    dimensions = list(_write_dimensions(sketch.id, sketch.parameter_ids, parameters))
    payload, generated_dimensions = _sketch_payload(sketch, object_id, object_ids)
    existing = {dimension.name for dimension in dimensions}
    dimensions.extend(
        dimension
        for dimension in generated_dimensions
        if dimension.name not in existing
    )
    native_properties = (
        _native_keyword_properties(native_feature.attributes)
        if native_feature is not None
        else None
    )
    return _WriteObject(
        sketch.id,
        object_id,
        sketch.name,
        "Sketch",
        "Sketch",
        "moProfileFeature_c",
        (
            (("Dissectable", "true"),)
            if native_properties is None
            else native_properties
        ),
        tuple(dimensions),
        payload,
    )


def _write_feature(
    feature: FeatureStep,
    parameters: dict[str, Parameter],
    object_ids: dict[str, int],
) -> _WriteObject:
    object_id = object_ids[f"feature:{feature.id}"]
    dimensions = list(_write_dimensions(feature.id, feature.parameter_ids, parameters))
    tag, kind, class_name = _write_feature_type(feature)
    native_properties = _native_keyword_properties(feature.attributes)
    properties = list(native_properties or ())
    payload = b""
    if tag == "Extrusion":
        if native_properties is None and feature.sketch_id is not None:
            child = object_ids.get(f"sketch:{feature.sketch_id}")
            if child is not None:
                properties.extend(
                    (
                        ("Dissectable", "true"),
                        ("DissectableChildren", str(child)),
                        ("DissectableRoot", "true"),
                    )
                )
        generated = _definition_dimension(feature)
        if generated is not None and not dimensions:
            dimensions.append(generated)
        payload = _extrusion_payload(feature)
    elif kind in {"Fillet", "Chamfer", "Shell"}:
        generated = _definition_dimension(feature)
        if generated is not None and not dimensions:
            dimensions.append(generated)
        payload = _fillet_payload(feature, object_ids)
    return _WriteObject(
        feature.id,
        object_id,
        feature.name,
        tag,
        kind,
        class_name,
        tuple(properties),
        tuple(dimensions),
        payload,
    )


def _native_keyword_properties(
    attributes: Mapping[str, Any],
) -> tuple[tuple[str, str], ...] | None:
    properties = attributes.get("native_properties")
    if not isinstance(properties, Mapping):
        return None
    return tuple(
        (name, value)
        for name, value in properties.items()
        if isinstance(name, str)
        and isinstance(value, str)
        and name not in {"id", "Name"}
    )


def _write_feature_type(feature: FeatureStep) -> tuple[str, str, str]:
    kind = str(feature.kind).casefold()
    if kind == FeatureKind.EXTRUSION.value:
        class_name = (
            "moCut_c"
            if feature.operation == BooleanOperation.CUT
            or str(feature.operation).casefold() == BooleanOperation.CUT.value
            else "moExtrusion_c"
        )
        return "Extrusion", "Extrusion", class_name
    if kind == FeatureKind.FILLET.value:
        return "Feature", "Fillet", "Fillet_c"
    if kind == FeatureKind.CHAMFER.value:
        return "Feature", "Chamfer", "Chamfer_c"
    if kind == FeatureKind.SHELL.value:
        return "Feature", "Shell", "moShell_c"
    if kind == FeatureKind.PATTERN.value and isinstance(
        feature.definition, LinearPatternFeature
    ):
        return "Feature", "LPattern", "moLPattern_c"
    if kind == FeatureKind.PATTERN.value and isinstance(
        feature.definition, CircularPatternFeature
    ):
        return "Feature", "CirPattern", "moCirPattern_c"
    native = feature.attributes.get("native_type")
    if isinstance(native, str) and native.strip():
        if native.strip().casefold() in {"basebody", "imported"}:
            return "Feature", "Imported", "moBaseBody_c"
        return "Feature", native.strip(), "moCompFeature_c"
    names = {
        FeatureKind.REVOLUTION.value: ("Revolution", "moRevolution_c"),
        FeatureKind.SWEEP.value: ("Sweep", "moSweep_c"),
        FeatureKind.LOFT.value: ("Blend", "moBlend_c"),
        FeatureKind.HOLE.value: ("HoleWizard", "moHoleWzd_c"),
        FeatureKind.SHELL.value: ("Shell", "moShell_c"),
        FeatureKind.PATTERN.value: ("Pattern", "moLPattern_c"),
        FeatureKind.MIRROR.value: ("MirrorPattern", "moMirrorPattern_c"),
        FeatureKind.BOOLEAN.value: ("Combine", "moCombineBodies_c"),
    }
    native_kind, class_name = names.get(kind, (str(feature.kind), "moCompFeature_c"))
    return "Feature", native_kind, class_name


def _write_dimensions(
    owner_id: str,
    parameter_ids: tuple[str | None, ...],
    parameters: dict[str, Parameter],
) -> tuple[_WriteDimension, ...]:
    selected: list[Parameter] = []
    seen: set[str] = set()
    for parameter_id in parameter_ids:
        if parameter_id is None or parameter_id in seen:
            continue
        parameter = parameters.get(parameter_id)
        if parameter is not None:
            selected.append(parameter)
            seen.add(parameter_id)
    for parameter in parameters.values():
        if parameter.owner_id == owner_id and parameter.id not in seen:
            selected.append(parameter)
            seen.add(parameter.id)
    return tuple(
        dimension
        for parameter in selected
        if (dimension := _parameter_dimension(parameter)) is not None
    )


def _parameter_dimension(parameter: Parameter) -> _WriteDimension | None:
    value = parameter.value.value
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or parameter.value.kind is not ValueKind.LENGTH
    ):
        return None
    factor = {
        "": 1.0,
        "mm": 1.0,
        "millimeter": 1.0,
        "millimeters": 1.0,
        "cm": 10.0,
        "m": 1000.0,
        "in": 25.4,
        "inch": 25.4,
        "inches": 25.4,
    }.get(parameter.value.unit.casefold())
    number = float(value)
    if factor is None or not math.isfinite(number):
        return None
    millimeters = number * factor
    source_text = parameter.attributes.get("source_text")
    text = (
        source_text
        if isinstance(source_text, str) and source_text
        else format(millimeters, ".15g")
    )
    return _WriteDimension(
        parameter.name,
        millimeters,
        text,
        parameter.role,
    )


def _definition_dimension(feature: FeatureStep) -> _WriteDimension | None:
    definition = feature.definition
    value = None
    prefix = ""
    if isinstance(definition, ExtrusionFeature):
        value = definition.length
    elif isinstance(definition, FilletFeature):
        value = definition.radius
        prefix = "R"
    elif isinstance(definition, ChamferFeature):
        value = definition.distance
    elif isinstance(definition, ShellFeature):
        value = definition.thickness
    if value is None:
        return None
    parameter = Parameter("", "D1", value)
    dimension = _parameter_dimension(parameter)
    if dimension is None:
        return None
    return replace(dimension, text=prefix + dimension.text)


def _plane_frame_block(plane: SupportPlane) -> bytes | None:
    transform = plane.transform
    origin = (transform.origin.x, transform.origin.y, transform.origin.z)
    x_axis = (transform.x_axis.x, transform.x_axis.y, transform.x_axis.z)
    y_axis = (transform.y_axis.x, transform.y_axis.y, transform.y_axis.z)
    z_axis = (transform.z_axis.x, transform.z_axis.y, transform.z_axis.z)
    vectors = (x_axis, y_axis, z_axis)
    if not _orthonormal(vectors) or not all(
        math.isfinite(value) for vector in (origin, *vectors) for value in vector
    ):
        return None
    frame = bytearray(_PLANE_FRAME_BYTES)
    struct.pack_into("<3d", frame, 0, *(value / _MILLIMETRES for value in origin))
    struct.pack_into("<3d", frame, 24, *z_axis)
    frame[48] = 1
    rows = tuple(zip(x_axis, y_axis, z_axis, strict=True))
    for index, row in enumerate(rows):
        struct.pack_into("<3d", frame, 49 + index * 24, *row)
    return bytes(frame)


def _plane_payload(plane: SupportPlane) -> bytes:
    frame = _plane_frame_block(plane)
    if frame is None:
        return b""
    return _class_declaration("moFixedRefPlnData_c") + frame


def _orthonormal(vectors: tuple[tuple[float, float, float], ...]) -> bool:
    return all(
        math.isclose(_norm(vector), 1.0, abs_tol=1e-9) for vector in vectors
    ) and all(
        math.isclose(_dot(left, right), 0.0, abs_tol=1e-9)
        for left, right in itertools.combinations(vectors, 2)
    )


def _sketch_payload(
    sketch: Sketch, object_id: int, object_ids: dict[str, int]
) -> tuple[bytes, tuple[_WriteDimension, ...]]:
    payload = bytearray()
    plane_id = object_ids.get(f"plane:{sketch.support_plane_id}", 2)
    payload.extend(_plane_reference(plane_id))
    generated: list[_WriteDimension] = []
    consumed: set[str] = set()
    local_id = 1
    entities = {entity.id: entity for entity in sketch.entities}
    for profile in sketch.closed_profile_entity_ids:
        selected = tuple(entities.get(entity_id) for entity_id in profile)
        if len(selected) == 4 and all(
            entity is not None and isinstance(entity.geometry, LineGeometry)
            for entity in selected
        ):
            rectangle = _rectangle_coordinates(
                tuple(entity.geometry for entity in selected if entity is not None)
            )
            if rectangle is not None:
                points = (
                    (rectangle[0], rectangle[1]),
                    (rectangle[2], rectangle[1]),
                    (rectangle[2], rectangle[3]),
                    (rectangle[0], rectangle[3]),
                )
                for point in points:
                    payload.extend(_coordinate_marker(point, local_id, _POINT_LOCUS))
                    local_id += 1
                for start, end in ((0, 1), (1, 2), (2, 3), (3, 0)):
                    payload.extend(_line_marker(start, end, local_id))
                    local_id += 1
                consumed.update(profile)
                continue
        if (
            len(selected) == 1
            and selected[0] is not None
            and isinstance(selected[0].geometry, CircleGeometry)
        ):
            circle = selected[0].geometry
            center = (circle.center.x, circle.center.y)
            radial = (circle.center.x + circle.radius, circle.center.y)
            payload.extend(_coordinate_marker(center, local_id, _CIRCLE_LOCUS))
            local_id += 1
            payload.extend(_coordinate_marker(radial, local_id, _POINT_LOCUS))
            local_id += 1
            generated.append(
                _WriteDimension(
                    f"D{len(generated) + 1}",
                    circle.radius,
                    "R" + format(circle.radius, ".15g"),
                    ParameterRole.DRIVING,
                )
            )
            consumed.add(selected[0].id)
    for entity in sketch.entities:
        if entity.id in consumed:
            continue
        if isinstance(entity.geometry, LineGeometry):
            start_index = local_id
            payload.extend(
                _coordinate_marker(
                    (entity.geometry.start.x, entity.geometry.start.y),
                    local_id,
                    _POINT_LOCUS,
                )
            )
            local_id += 1
            payload.extend(
                _coordinate_marker(
                    (entity.geometry.end.x, entity.geometry.end.y),
                    local_id,
                    _POINT_LOCUS,
                )
            )
            local_id += 1
            roster_start = start_index - 1
            payload.extend(_line_marker(roster_start, roster_start + 1, local_id))
            local_id += 1
        elif isinstance(entity.geometry, CircleGeometry):
            center = (entity.geometry.center.x, entity.geometry.center.y)
            radial = (center[0] + entity.geometry.radius, center[1])
            payload.extend(_coordinate_marker(center, local_id, _CIRCLE_LOCUS))
            local_id += 1
            payload.extend(_coordinate_marker(radial, local_id, _POINT_LOCUS))
            local_id += 1
            generated.append(
                _WriteDimension(
                    f"D{len(generated) + 1}",
                    entity.geometry.radius,
                    "R" + format(entity.geometry.radius, ".15g"),
                    ParameterRole.DRIVING,
                )
            )
    return bytes(payload), tuple(generated)


def _plane_reference(object_id: int) -> bytes:
    block = bytearray(67)
    struct.pack_into("<I", block, 0, object_id)
    block[4] = 1
    block[8:12] = b"\0\0\x03\0"
    struct.pack_into("<d", block, 39, 1.0)
    block[50] = 2
    block[54] = 0xFF
    block[55:58] = b"\xff\xff\xff"
    return bytes(block)


def _coordinate_marker(
    point: tuple[float, float], local_id: int, locus: bytes
) -> bytes:
    record = bytearray(142)
    record[:5] = _CURRENT_MARKER
    record[5:13] = b"\xff" * 8
    record[13:17] = b"\0\0\x80\xbf"
    struct.pack_into("<I", record, 17, 1)
    record[23:27] = locus
    struct.pack_into("<H", record, 27, 1)
    record[31:39] = b"\0\0\x80\xbf\0\0\x04\0"
    struct.pack_into("<d", record, 48, 1.0)
    record[56:58] = _COORDINATE_TAG
    struct.pack_into("<2d", record, 58, point[0] / 1000.0, point[1] / 1000.0)
    struct.pack_into("<I", record, 138, local_id)
    return bytes(record)


def _line_marker(start: int, end: int, local_id: int) -> bytes:
    record = bytearray(92)
    record[:5] = _CURRENT_MARKER
    record[5:13] = b"\xff" * 8
    record[13:17] = b"\0\0\x80\xbf"
    struct.pack_into("<I", record, 17, 2)
    record[23:27] = _POINT_LOCUS
    struct.pack_into("<H", record, 27, 1)
    struct.pack_into("<d", record, 48, 1.0)
    struct.pack_into("<HH", record, 64, start, end)
    struct.pack_into("<I", record, 88, local_id)
    return bytes(record)


def _rectangle_coordinates(
    lines: tuple[LineGeometry, ...],
) -> tuple[float, float, float, float] | None:
    points = tuple((line.start.x, line.start.y) for line in lines)
    ends = tuple((line.end.x, line.end.y) for line in lines)
    if any(ends[index] != points[(index + 1) % 4] for index in range(4)):
        return None
    xs = sorted({point[0] for point in points})
    ys = sorted({point[1] for point in points})
    if len(xs) != 2 or len(ys) != 2:
        return None
    if set(points) != {(x, y) for x in xs for y in ys}:
        return None
    return xs[0], ys[0], xs[1], ys[1]


# extrusion payloads carry direction and termination independently of display metadata
def _extrusion_payload(feature: FeatureStep) -> bytes:
    definition = feature.definition
    direction = int(isinstance(definition, ExtrusionFeature) and definition.reversed)
    condition = (
        (
            ExtrusionEndCondition.MID_PLANE
            if definition.symmetric
            else definition.end_condition
        )
        if isinstance(definition, ExtrusionFeature)
        else None
    )
    termination = {
        ExtrusionEndCondition.BLIND: 0,
        ExtrusionEndCondition.THROUGH_ALL: 1,
        ExtrusionEndCondition.UP_TO_FIRST: 2,
        ExtrusionEndCondition.UP_TO_VERTEX: 3,
        ExtrusionEndCondition.UP_TO_FACE: 4,
        ExtrusionEndCondition.UP_TO_SHAPE: 4,
        ExtrusionEndCondition.OFFSET_FROM_SURFACE: 5,
        ExtrusionEndCondition.MID_PLANE: 6,
    }.get(condition, 0)
    declaration = _class_declaration("moEndSpec_c")
    return b"".join(
        (
            declaration,
            b"\0\0",
            struct.pack("<II", 1, 0),
            struct.pack("<I", direction),
            b"\0\0",
            struct.pack("<II", termination, 0),
        )
    )


def _fillet_payload(feature: FeatureStep, object_ids: dict[str, int]) -> bytes:
    result = bytearray()
    for selection_id in feature.selection_ids:
        producer = 0
        local_id = 0
        parts = selection_id.rsplit(":", 1)
        if len(parts) == 2:
            try:
                local_id = int(parts[1])
            except ValueError:
                local_id = 0
        if feature.input_feature_ids:
            producer = object_ids.get(f"feature:{feature.input_feature_ids[-1]}", 0)
        if producer and local_id:
            result.extend(_FilletSelectionRecord(producer, local_id))
    return bytes(result)


# fillet selection records bind an operation object to one native edge-local identity
def _FilletSelectionRecord(ProducerId: int, LocalId: int) -> bytes:
    if not 1 <= ProducerId <= 0xFFFFFFFF or not 1 <= LocalId <= 0xFFFFFFFF:
        raise SldprtFormatError("native fillet selection ids must be positive integers")
    RecordData = bytearray(38)
    RecordData[:16] = _EDGE_SELECTION_IDENTITY
    struct.pack_into("<I", RecordData, 26, ProducerId)
    struct.pack_into("<I", RecordData, 34, LocalId)
    return bytes(RecordData)


# the recovered inward shell stores its removed top face and paired face witness
def _ShellSelectionRecord(ProducerId: int) -> bytes:
    return _FilletSelectionRecord(ProducerId, 1) + _FilletSelectionRecord(
        ProducerId,
        4,
    )


def _keywords_payload(
    document: CadDocument,
    model_name: str,
    objects: tuple[_WriteObject, ...],
    object_ids: Mapping[str, int],
    identity: _NativeIdentity,
) -> bytes:
    children: list[str] = []
    configurations = document.configurations or ()
    for configuration in configurations:
        configuration_id = object_ids[f"configuration:{configuration.id}"]
        attributes = {
            "id": str(configuration_id),
            "Name": configuration.name,
            "Type": "ConfigurationManager",
        }
        native_properties = configuration.attributes.get("native_properties")
        material = (
            native_properties.get("Material")
            if isinstance(native_properties, Mapping)
            else configuration.attributes.get("Material")
        )
        if isinstance(material, str):
            attributes["Material"] = material
        else:
            attributes["Material"] = "Material <not specified>"
        children.append(_xml_element("Configuration", attributes))
    if not configurations:
        children.append(
            _xml_element(
                "Configuration",
                {
                    "id": "0",
                    "Name": "Default",
                    "Type": "ConfigurationManager",
                    "Material": "Material <not specified>",
                },
            )
        )
    for item in sorted(
        objects, key=lambda value: (value.xml_tag, str(value.object_id))
    ):
        attributes = {"id": str(item.object_id), "Name": item.name}
        if item.xml_tag == "Feature" or item.kind == "Origin":
            attributes["Type"] = item.kind
        attributes.update(item.properties)
        dimensions = "".join(
            _xml_element(
                "Dimension",
                {"Name": dimension.name},
                _xml_text(dimension.text),
            )
            for dimension in item.dimensions
        )
        children.append(
            _xml_element(
                item.xml_tag,
                attributes,
                dimensions if item.dimensions else None,
            )
        )
    root = _xml_element(
        "Keywords",
        {"id": str(identity.creation_stamp), "Name": identity.reference_name},
        "".join(children),
    )
    return b"\x86" + _xml_document(root)


def _features_payload(
    document: CadDocument,
    model_name: str,
    object_ids: Mapping[str, int],
    identity: _NativeIdentity,
) -> bytes:
    header = _xml_element(
        "swHeader",
        {"swObjCount": "1"},
        _xml_element(
            "swFile",
            {
                "id": "3",
                "swDocType": "PART",
                "swCreationTime": str(identity.creation_stamp),
                "swPath": f"{model_name}{PART_SUFFIX}",
            },
        ),
    )
    active = next(
        (
            configuration
            for configuration in document.configurations
            if configuration.active
        ),
        document.configurations[0] if document.configurations else None,
    )
    active_name = active.name if active is not None else "Default"
    active_id = 0
    if active is not None:
        active_id = object_ids[f"configuration:{active.id}"]
    models = _xml_element(
        "swModelList",
        {"swObjCount": "1"},
        _xml_element(
            "swModel",
            {
                "id": "2",
                "swName": model_name,
                "swConfigurationName": active_name,
                "swConfigurationId": str(active_id),
                "swLastModifiedStamp": str(identity.last_modified_stamp),
                "swConfigurationFlags": str(identity.configuration_flags),
                "swFileRef": "3",
            },
        ),
    )
    configurations = document.configurations or ()
    configuration_children: list[str] = []
    if configurations:
        for index, configuration in enumerate(configurations, start=1):
            native_id = object_ids[f"configuration:{configuration.id}"]
            configuration_children.append(
                _xml_element(
                    "swConfiguration",
                    {
                        "id": str(index),
                        "swName": configuration.name,
                        "swID": str(native_id),
                        "swReference": identity.reference_name,
                        "swMostRecentConfiguration": (
                            "YES" if configuration.active else "NO"
                        ),
                        "swConfigurationNeedsUpdate": "NO",
                        "swDefeatureConfiguration": "NO",
                        "swModelRef": "2",
                    },
                )
            )
    else:
        configuration_children.append(
            _xml_element(
                "swConfiguration",
                {
                    "id": "1",
                    "swName": "Default",
                    "swID": "0",
                    "swReference": identity.reference_name,
                    "swMostRecentConfiguration": "YES",
                    "swConfigurationNeedsUpdate": "NO",
                    "swDefeatureConfiguration": "NO",
                    "swModelRef": "2",
                },
            )
        )
    configuration_list = _xml_element(
        "swConfigurationList",
        {"swObjCount": str(len(configurations) or 1)},
        "".join(configuration_children),
    )
    root = _xml_element(
        "swSolidWorks",
        {
            "xmlns": _SOLIDWORKS_XML_NAMESPACE,
            "swObjCount": "3",
            "swVersion": "18000",
        },
        "".join(
            (
                header,
                models,
                configuration_list,
                _xml_element("swExtFeatureList", {"swObjCount": "0"}),
            )
        ),
    )
    return _xml_document(root)


def _xml_document(root: str) -> bytes:
    return ('<?xml version="1.0" encoding="UTF-8"?>\r\n' + root + "\r\n").encode(
        "utf-8"
    )


def _xml_element(
    name: str,
    attributes: Mapping[str, str],
    body: str | None = None,
) -> str:
    encoded_attributes = "".join(
        f' {key}="{_xml_attribute(value)}"' for key, value in attributes.items()
    )
    if body is None:
        return f"<{name}{encoded_attributes}/>"
    return f"<{name}{encoded_attributes}>{body}</{name}>"


def _xml_attribute(value: str) -> str:
    return (
        _xml_text(value)
        .replace('"', "&quot;")
        .replace("\t", "&#9;")
        .replace("\n", "&#10;")
        .replace("\r", "&#13;")
    )


def _xml_text(value: str) -> str:
    return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _resolved_base_map_index(objects: tuple[_WriteObject, ...]) -> int:
    authored = tuple(
        item for item in objects if item.object_id not in _SYSTEM_OBJECT_IDS
    )
    features = len(_solid_feature_tree_ids(authored))
    return _CONFIG0_FIRST_FEATURE_COUNTER + max(features, 1) - 1


def _resolved_payload(objects: tuple[_WriteObject, ...]) -> bytes:
    output = bytearray(
        struct.pack("<IH", _resolved_base_map_index(objects), max(0, len(objects) - 1))
    )
    for item in objects:
        output.extend(_class_declaration(item.class_name))
        output.extend(_name_record(item.name, item.object_id, _tree_node_flags(item)))
        output.extend(item.payload)
        for dimension in item.dimensions:
            output.extend(_scalar_record(dimension))
    return bytes(output)


def _class_declaration(name: str) -> bytes:
    encoded = name.encode("ascii")
    return CLASS_MARKER + struct.pack("<H", len(encoded)) + encoded


def _tree_node_flags(item: _WriteObject) -> int:
    if item.kind == "Extrusion":
        return (
            _CUT_EXTRUDE_FLAGS if item.class_name == "moCut_c" else _BOSS_EXTRUDE_FLAGS
        )
    if item.class_name in _REFERENCE_GEOMETRY_CLASSES:
        return _REFERENCE_GEOMETRY_FLAGS
    return _FOLDER_FLAGS


def _name_record(name: str, object_id: int, flags: int) -> bytes:
    encoded = name.encode("utf-16le")
    units = len(encoded) // 2
    if not 1 <= units <= 255:
        raise SldprtFormatError(
            "native SOLIDWORKS object name exceeds 255 UTF-16 units"
        )
    return (
        _NAME_PREFIX
        + bytes((units,))
        + encoded
        + struct.pack("<III", 0, flags, object_id)
        + b"\0" * 16
    )


def _scalar_record(dimension: _WriteDimension) -> bytes:
    encoded = dimension.name.encode("utf-16le")
    units = len(encoded) // 2
    if not 1 <= units <= 255:
        raise SldprtFormatError(
            "native SOLIDWORKS dimension name exceeds 255 UTF-16 units"
        )
    trailer = bytearray(51)
    trailer[3:7] = b"\xff" * 4
    trailer[21:27] = b"\x01\0\0\0\x02\0"
    trailer[27] = 1 if dimension.role is ParameterRole.DRIVEN else 0
    return b"".join(
        (
            _class_declaration("moLengthParameter_c"),
            _NAME_PREFIX,
            bytes((units,)),
            encoded,
            _SCALAR_HEADER,
            struct.pack("<d", dimension.value_mm / 1000.0),
            bytes(trailer),
        )
    )


def _native_identity(document: CadDocument, model_name: str) -> _NativeIdentity:
    authored = sum(
        not _is_native_system_feature(feature) for feature in document.feature_timeline
    )
    if authored == 0 and not document.sketches:
        return _NativeIdentity(
            1785690802,
            114,
            101,
            1785690807,
            _SOLIDWORKS_CONFIGURATION_FLAGS,
            "Part1",
        )
    creation_stamp = _stable_creation_stamp(document, model_name)
    last_modified_stamp = 102 + authored * 4
    return _NativeIdentity(
        creation_stamp,
        last_modified_stamp,
        101,
        (creation_stamp + authored * 7 + len(document.sketches) * 3 + 5) & 0x7FFFFFFF,
        _SOLIDWORKS_CONFIGURATION_FLAGS,
        "Part1",
    )


def _solid_feature_tree_ids(objects: tuple[_WriteObject, ...]) -> tuple[int, ...]:
    return tuple(
        item.object_id
        for item in objects
        if item.class_name not in _NON_SOLID_FEATURE_CLASSES
    )


def _configuration_atom_tree_ids(
    solid_feature_tree_ids: tuple[int, ...],
) -> tuple[int, ...]:
    return solid_feature_tree_ids or (_CONFIGURATION_ROOT_TREE_ID,)


# load critical envelope streams must share feature topology and cached bounds
def _native_envelope_streams(
    document: CadDocument,
    model_name: str,
    identity: _NativeIdentity,
    solid_feature_tree_ids: tuple[int, ...] = (),
    header_feature_objects: tuple[tuple[int, str, bool], ...] = (),
    header_feature_stamps: Mapping[int, tuple[int, ...]] | None = None,
    annotation_view_count: int = 1,
    terminal_parent_tree_id: int | None = None,
    HeaderBounds: tuple[float, ...] | None = None,
    HeaderCreation: int | None = None,
    CmgrParentTreeId: int | None = None,
    AnnotationViewVariant: str = "default",
) -> Mapping[str, bytes]:
    configuration_name = next(
        (
            configuration.name
            for configuration in document.configurations
            if configuration.active
        ),
        document.configurations[0].name if document.configurations else "Default",
    )
    zero = struct.pack("<I", 0)
    streams = {
        "Contents/CMgrHdr2": _configuration_header_payload(
            configuration_name, identity
        ),
        "Contents/CnfgObjs": zero + _serialized_string("") + _serialized_string(""),
        "Contents/CusProps": _custom_properties_payload(),
        "Contents/OleItems": zero,
        "Contents/eModelLic": zero,
        "ModelStamps": struct.pack(
            "<III",
            identity.creation_stamp,
            identity.last_modified_stamp,
            identity.baseline_stamp,
        ),
        "_MO_VERSION_18000/Biography": _biography_payload(model_name, identity),
        "_MO_VERSION_18000/History": _version_history_payload(),
    }
    if HeaderCreation is not None and not 0 <= HeaderCreation <= 0xFFFFFFFF:
        raise SldprtFormatError("native SOLIDWORKS header creation stamp is invalid")
    HeaderIdentity = (
        identity
        if HeaderCreation is None
        else _NativeIdentity(
            HeaderCreation,
            identity.last_modified_stamp,
            identity.baseline_stamp,
            identity.header_stamp,
            identity.configuration_flags,
            identity.reference_name,
        )
    )
    model_header = _model_header_payload(
        HeaderIdentity,
        configuration_name,
        solid_feature_tree_ids=solid_feature_tree_ids,
        feature_objects=header_feature_objects,
        feature_stamps=header_feature_stamps,
        HeaderBounds=HeaderBounds,
    )
    streams["Contents/Config-0-ModelHeader"] = model_header
    streams["Header2"] = model_header
    streams["Contents/Definition"] = encode_definition_stream(
        assembly=document.assembly is not None
    )
    tree_ids = _configuration_atom_tree_ids(solid_feature_tree_ids)
    ParentTreeId = (
        terminal_parent_tree_id
        if terminal_parent_tree_id is not None
        else CmgrParentTreeId
    )
    if ParentTreeId is not None:
        if (
            len(tree_ids) != 2
            or tree_ids[0] != ParentTreeId
            or (terminal_parent_tree_id is not None and annotation_view_count != 2)
        ):
            raise SldprtFormatError(
                "terminal feature configuration requires its parent and child trees"
            )
        tree_ids = (tree_ids[-1],)
    atom_ids = atom_ids_for(len(tree_ids))
    streams[CONFIGURATION_MANAGER_STREAM] = encode_cmgr_stream(
        feature_tree_ids=tree_ids,
        configuration_name=configuration_name,
        part_name=identity.reference_name,
        atom_ids=atom_ids,
        connected_history=len(tree_ids) in {2, 3, 4} and len(document.bodies) == 1,
        terminal_parent_tree_id=ParentTreeId,
    )
    streams[CONFIGURATION_STREAM] = encode_config0_stream(
        part_name=identity.reference_name,
        atoms=tuple(reversed(tuple(zip(atom_ids, tree_ids, strict=True)))),
        high_water=(atom_ids[-1], FIRST_ATOM_ID + 2 * len(atom_ids)),
        annotation_view_count=annotation_view_count,
        terminal_parent_tree_id=terminal_parent_tree_id,
        annotation_view_variant=AnnotationViewVariant,
    )
    return MappingProxyType(streams)


def encode_native_assembly_envelope(
    document: CadDocument,
    model_name: str,
    occurrence_names: Sequence[str],
    mate_names: Sequence[str],
) -> NativeAssemblyEnvelope:
    configuration_name = next(
        (
            configuration.name
            for configuration in document.configurations
            if configuration.active
        ),
        document.configurations[0].name if document.configurations else "Default",
    )
    listed: list[tuple[int, str, bool]] = list(_ASSEMBLY_HEADER_OBJECTS)
    omitted: list[str] = []
    next_object_id = _ASSEMBLY_HEADER_OBJECTS[-1][0] + 1
    for name in (*occurrence_names, *mate_names):
        if _serializable_name(name):
            listed.append((next_object_id, name, False))
            next_object_id += 1
        else:
            omitted.append(name)
    identity = _native_assembly_identity(document, model_name, len(listed))
    document_path = f"C:\\{model_name}{ASSEMBLY_SUFFIX}"
    model_header = _header_payload(
        identity, configuration_name, tuple(listed), document_path
    )
    zero = struct.pack("<I", 0)
    streams = {
        "Contents/CMgrHdr2": _configuration_header_payload(
            configuration_name, identity
        ),
        "Contents/CnfgObjs": zero + _serialized_string("") + _serialized_string(""),
        "Contents/Config-0-ModelHeader": model_header,
        _ASSEMBLY_ATTACHMENT_STREAM: struct.pack("<H", 0),
        "Contents/CusProps": _custom_properties_payload(
            _ASSEMBLY_PROPERTY_CONTAINER_CLASS
        ),
        "Contents/OleItems": zero,
        _ASSEMBLY_VIEW_ORIENTATION_STREAM: _VIEW_ORIENTATION_PAYLOAD,
        "Contents/eModelLic": zero,
        "Header2": model_header,
        "ModelStamps": struct.pack(
            "<III",
            identity.creation_stamp,
            identity.last_modified_stamp,
            identity.baseline_stamp,
        ),
        _ASSEMBLY_VISUAL_DATA_STREAM: zero,
        f"{_ASSEMBLY_VERSION_PREFIX}/Biography": _biography_payload(
            model_name,
            identity,
            "C:\\Kit\\Assembly.ASMDOT",
            ASSEMBLY_SUFFIX,
        ),
        f"{_ASSEMBLY_VERSION_PREFIX}/History": _version_history_payload(),
        _ASSEMBLY_TABLES_STREAM: b"",
        _ASSEMBLY_CUTLIST_STREAM: (
            f'<Configuration id="0" Name="{_xml_attribute(configuration_name)}"/>\r\n'
        ).encode("utf-8"),
        _ASSEMBLY_CONFIG_PROPERTIES_STREAM: _CONFIG_PROPERTIES_PAYLOAD,
        _ASSEMBLY_OPEN_TIME_STREAM: _OPEN_TIME_PAYLOAD,
    }
    header_objects = tuple((object_id, name) for object_id, name, _ in listed)
    decoded = decode_native_model_header(model_header)
    return NativeAssemblyEnvelope(
        MappingProxyType(streams),
        configuration_name,
        identity.reference_name,
        document_path,
        header_objects,
        tuple(omitted),
        not omitted
        and decoded.user_name == "Kit"
        and decoded.reference_name == identity.reference_name
        and decoded.configuration_name == configuration_name
        and decoded.document_path == document_path
        and decoded.objects == header_objects,
    )


def decode_native_model_header(data: bytes) -> NativeModelHeader:
    class_name, offset = _read_class(data, 0)
    if class_name != "moHeader_c":
        raise SldprtFormatError("native SOLIDWORKS header class is not moHeader_c")
    offset = _expect_bytes(
        data,
        offset,
        bytes.fromhex("01000000ffff00000f00")
        + b"su_CStringArray"
        + struct.pack("<H", 1),
    )
    user_name, offset = _read_serialized_string(data, offset)
    offset = _expect_bytes(data, offset, bytes.fromhex("03800100"))
    _, offset = _read_serialized_string(data, offset)
    class_name, offset = _read_class(data, offset)
    if class_name != "suObList":
        raise SldprtFormatError("native SOLIDWORKS header log list is missing")
    (log_count,) = struct.unpack_from("<H", data, offset)
    offset += 2
    class_name, offset = _read_class(data, offset)
    if class_name != "moLogs_c":
        raise SldprtFormatError("native SOLIDWORKS header log record is missing")
    offset = _expect_bytes(data, offset, struct.pack("<H", 1))
    class_name, offset = _read_class(data, offset)
    if class_name != "moStamp_c":
        raise SldprtFormatError("native SOLIDWORKS header stamp record is missing")
    offset += 10
    _, offset = _read_serialized_string(data, offset)
    offset += 4
    reference_name, offset = _read_serialized_string(data, offset)
    objects: list[tuple[int, str]] = []
    for _ in range(log_count - 1):
        offset = _expect_bytes(data, offset, bytes.fromhex("0880"))
        (action_count,) = struct.unpack_from("<H", data, offset)
        offset += 2
        for _ in range(action_count):
            offset = _expect_bytes(data, offset, bytes.fromhex("0a80"))
            offset += 10
            _, offset = _read_serialized_string(data, offset)
        (object_id,) = struct.unpack_from("<I", data, offset)
        offset += 4
        object_name, offset = _read_serialized_string(data, offset)
        objects.append((object_id, object_name))
    offset += 14
    class_name, offset = _read_class(data, offset)
    if class_name != "moExtObject_c":
        raise SldprtFormatError("native SOLIDWORKS header reference block is missing")
    class_name, offset = _read_class(data, offset)
    if class_name != "moCStringHandle_c":
        raise SldprtFormatError("native SOLIDWORKS header path handle is missing")
    document_path, offset = _read_serialized_string(data, offset)
    _, offset = _ReadClassReference(data, offset)
    _, offset = _read_serialized_string(data, offset)
    offset = _expect_bytes(data, offset, bytes.fromhex("020000"))
    offset += 4
    for _ in range(3):
        _, offset = _read_serialized_string(data, offset)
    offset = _expect_bytes(data, offset, bytes.fromhex("0008"))
    offset += 16
    configuration_name, offset = _read_serialized_string(data, offset)
    return NativeModelHeader(
        user_name,
        reference_name,
        configuration_name,
        document_path,
        tuple(objects),
    )


def _read_class(data: bytes, offset: int) -> tuple[str, int]:
    marker = len(CLASS_MARKER)
    if data[offset : offset + marker] != CLASS_MARKER:
        raise SldprtFormatError("native SOLIDWORKS class declaration is missing")
    start = offset + marker
    if start + 2 > len(data):
        raise SldprtFormatError("native SOLIDWORKS class declaration is truncated")
    (length,) = struct.unpack_from("<H", data, start)
    end = start + 2 + length
    if end > len(data):
        raise SldprtFormatError("native SOLIDWORKS class declaration is truncated")
    return data[start + 2 : end].decode("ascii"), end


# feature-count-dependent header references need validation without a fixed class index
def _ReadClassReference(data: bytes, OffsetData: int) -> tuple[int, int]:
    if OffsetData + 2 > len(data):
        raise SldprtFormatError("native SOLIDWORKS class reference is truncated")
    (ReferenceData,) = struct.unpack_from("<H", data, OffsetData)
    if ReferenceData == 0xFFFF or not ReferenceData & 0x8000:
        raise SldprtFormatError("native SOLIDWORKS class reference is invalid")
    return ReferenceData & 0x7FFF, OffsetData + 2


def _read_serialized_string(data: bytes, offset: int) -> tuple[str, int]:
    marker = len(SERIALIZED_STRING_MARKER)
    if data[offset : offset + marker] != SERIALIZED_STRING_MARKER:
        raise SldprtFormatError("native SOLIDWORKS serialized string is missing")
    start = offset + marker
    if start >= len(data):
        raise SldprtFormatError("native SOLIDWORKS serialized string is truncated")
    end = start + 1 + data[start] * 2
    if end > len(data):
        raise SldprtFormatError("native SOLIDWORKS serialized string is truncated")
    return data[start + 1 : end].decode("utf-16le"), end


def _expect_bytes(data: bytes, offset: int, literal: bytes) -> int:
    if data[offset : offset + len(literal)] != literal:
        raise SldprtFormatError("native SOLIDWORKS header layout is unexpected")
    return offset + len(literal)


def _serializable_name(value: str) -> bool:
    return 1 <= len(value.encode("utf-16le")) // 2 <= 0xFE


def _native_assembly_identity(
    document: CadDocument, model_name: str, object_count: int
) -> _NativeIdentity:
    creation_stamp = _stable_creation_stamp(document, model_name, b"assembly")
    return _NativeIdentity(
        creation_stamp,
        101 + object_count * 4,
        101,
        (creation_stamp + object_count * 7 + 5) & 0x7FFFFFFF,
        _ASSEMBLY_CONFIGURATION_FLAGS,
        PureWindowsPath(model_name).stem or _ASSEMBLY_REFERENCE_NAME,
    )


# model headers need one owner for action history and spatial metadata
def _model_header_payload(
    identity: _NativeIdentity,
    configuration_name: str,
    user_name: str = "Kit",
    solid_feature_tree_ids: tuple[int, ...] = (),
    feature_objects: tuple[tuple[int, str, bool], ...] = (),
    feature_stamps: Mapping[int, tuple[int, ...]] | None = None,
    HeaderBounds: tuple[float, ...] | None = None,
) -> bytes:
    return _header_payload(
        identity,
        configuration_name,
        (*_HEADER_OBJECTS, *feature_objects),
        "",
        user_name,
        max(solid_feature_tree_ids) + 1 if solid_feature_tree_ids else None,
        feature_stamps,
        HeaderBounds,
    )


# format versions share one header grammar despite optional geometric bounds
def _header_payload(
    identity: _NativeIdentity,
    configuration_name: str,
    objects: Sequence[tuple[int, str, bool]],
    document_path: str,
    user_name: str = "Kit",
    next_object_id: int | None = None,
    object_stamps: Mapping[int, tuple[int, ...]] | None = None,
    HeaderBounds: tuple[float, ...] | None = None,
) -> bytes:
    if HeaderBounds is not None and (
        len(HeaderBounds) != 10
        or not all(math.isfinite(ItemValue) for ItemValue in HeaderBounds)
    ):
        raise SldprtFormatError(
            "native SOLIDWORKS header bounds require ten finite values"
        )
    legacy_stamp = bytes.fromhex("f65a1a69")
    CStringHandleClassIndex = 14 + sum(
        2 + int(modified) for _object_id, _name, modified in objects
    )
    output = bytearray(_class_declaration("moHeader_c"))
    output.extend(
        bytes.fromhex("01000000ffff00000f00")
        + b"su_CStringArray"
        + struct.pack("<H", 1)
    )
    output.extend(_serialized_string(user_name))
    output.extend(bytes.fromhex("03800100"))
    output.extend(_serialized_string(""))
    output.extend(_class_declaration("suObList"))
    output.extend(struct.pack("<H", len(objects) + 1))
    output.extend(_class_declaration("moLogs_c"))
    output.extend(struct.pack("<H", 1))
    output.extend(_class_declaration("moStamp_c"))
    output.extend(b"\0" * 6 + legacy_stamp)
    output.extend(_serialized_string("Created"))
    output.extend(struct.pack("<I", 0))
    output.extend(_serialized_string(identity.reference_name))
    LogicalStamp = identity.creation_stamp
    ObjectStamps = object_stamps or {}
    for object_id, name, modified in objects:
        actions = ("Created", "Modified") if modified else ("Created",)
        RecoveredStamps = ObjectStamps.get(object_id)
        if RecoveredStamps is not None and len(RecoveredStamps) != len(actions):
            raise SldprtFormatError(
                "native SOLIDWORKS header action stamps do not match object actions"
            )
        output.extend(bytes.fromhex("0880") + struct.pack("<H", len(actions)))
        if object_id > 16 and modified:
            LogicalStamp += 1
        for index, action in enumerate(actions):
            if object_id > 16 and index:
                LogicalStamp += 1
            StampData = (
                struct.pack("<I", RecoveredStamps[index])
                if RecoveredStamps is not None
                else (
                    legacy_stamp if object_id <= 16 else struct.pack("<I", LogicalStamp)
                )
            )
            output.extend(
                bytes.fromhex("0a80") + struct.pack("<I", index) + b"\0\0" + StampData
            )
            output.extend(_serialized_string(action))
        output.extend(struct.pack("<I", object_id))
        output.extend(_serialized_string(name))
    watermark = (
        max(item[0] for item in objects) + 1
        if next_object_id is None
        else max(next_object_id, max(item[0] for item in objects) + 1)
    )
    output.extend(
        legacy_stamp
        + struct.pack("<IH", watermark, 0)
        + struct.pack("<I", identity.last_modified_stamp)
    )
    output.extend(_class_declaration("moExtObject_c"))
    output.extend(_class_declaration("moCStringHandle_c"))
    output.extend(_serialized_string(document_path))
    output.extend(encode_class_reference(CStringHandleClassIndex))
    output.extend(_serialized_string(identity.reference_name))
    output.extend(bytes.fromhex("020000"))
    output.extend(struct.pack("<I", identity.creation_stamp))
    output.extend(_serialized_string("") * 3)
    output.extend(bytes.fromhex("0008"))
    output.extend(struct.pack("<III", identity.header_stamp, 1, 0))
    output.extend(struct.pack("<I", 0xFFFFFFFF))
    output.extend(_serialized_string(configuration_name))
    output.extend(b"\0" * 16)
    output.extend(struct.pack("<I", identity.baseline_stamp))
    output.extend(b"\0" * 8)
    output.extend(struct.pack("<I", identity.creation_stamp))
    output.extend(b"\0" * 22)
    output.extend(struct.pack("<I", identity.header_stamp))
    output.extend(bytes.fromhex("0680"))
    output.extend(b"\0" * 10)
    output.extend(struct.pack("<I", int(HeaderBounds is not None)))
    if HeaderBounds is not None:
        output.extend(struct.pack("<10d", *HeaderBounds))
    output.extend(b"\xff" * 10)
    output.extend(_class_declaration(""))
    output.extend(b"\0" * 40)
    output.extend(struct.pack("<I", 1))
    output.extend(b"\0" * 16)
    output.extend(struct.pack("<I", 1))
    return bytes(output)


def _configuration_header_payload(
    configuration_name: str, identity: _NativeIdentity
) -> bytes:
    return b"".join(
        (
            _class_declaration("dmConfigMgrHeader_c"),
            struct.pack("<H", 1),
            _class_declaration("dmConfigHeader_c"),
            struct.pack("<I", 1),
            _serialized_string(configuration_name),
            struct.pack("<II", 0, identity.last_modified_stamp),
            _serialized_string(configuration_name),
            struct.pack("<II", 0xFFFFFFFF, 0),
            _serialized_string(""),
            _serialized_string(""),
            struct.pack(
                "<IIIIII",
                identity.configuration_flags & 0xFFFFFFFF,
                0,
                identity.baseline_stamp,
                identity.baseline_stamp,
                identity.header_stamp,
                2,
            ),
        )
    )


def _custom_properties_payload(
    container_class: str = "moFilePropContainer_c",
) -> bytes:
    return b"".join(
        (
            _class_declaration("moCusPropMgr_c"),
            struct.pack("<H", 0xFFFF),
            _class_declaration(""),
            struct.pack("<II", 1, 0),
            _class_declaration("moCusPropContainer_c"),
            _class_declaration(container_class),
            b"\0" * 13,
        )
    )


# the version-history stream preserves the typed archive stamps required by the native reader
def _version_history_payload() -> bytes:
    return b"".join(
        (
            _class_declaration("moVersionHistory_c"),
            struct.pack("<IIH", 1, 0, 0),
            bytes.fromhex("f65a1a69"),
            _serialized_string(""),
            b"PF\0\0",
            _class_declaration("moDateCodeHistory_c"),
            struct.pack("<I", 1),
            bytes.fromhex("34e71e"),
            struct.pack("<IBI", 1, 0, 0xFFFFFFFF),
            b"\0" * 14,
        )
    )


# the biography stream records deterministic typed provenance without copying a template stream
def _biography_payload(
    model_name: str,
    identity: _NativeIdentity,
    template_path: str = "C:\\Kit\\Part.PRTDOT",
    document_suffix: str = PART_SUFFIX,
) -> bytes:
    filetime = 116444736000000000 + identity.creation_stamp * 10_000_000
    first_paths = (
        "C:\\Windows\\System32\\",
        "C:\\Windows\\",
        "C:\\Program Files\\SOLIDWORKS\\",
        "C:\\Temp\\",
        "C:\\Temp\\",
        template_path,
    )
    second_paths = (
        "C:\\Windows\\System32\\",
        "C:\\Windows\\",
        "C:\\",
        "C:\\Temp\\",
        "C:\\Temp\\",
        template_path,
    )
    output = bytearray(
        _class_declaration("moBiography_c")
        + struct.pack(
            "<10I",
            2,
            0x4650,
            0x1EE734,
            1,
            9,
            12,
            2,
            10,
            0,
            0x65F4,
        )
    )
    for _ in range(7):
        output.extend(_serialized_string(""))
        output.extend(b"\0" * (14 if len(output) == 63 else 12))
    output.extend(struct.pack("<QI", filetime, 0x29310000))
    for path in first_paths:
        output.extend(_serialized_string(path))
        output.extend(struct.pack("<III", 3, 0x454F4000, 5))
    output.extend(
        struct.pack(
            "<9I",
            0x4650,
            0x1EE734,
            1,
            9,
            12,
            2,
            10,
            0,
            0x6658,
        )
    )
    output.extend(_serialized_string(""))
    output.extend(struct.pack("<HQI", 0x1809, filetime, 0x6BAA7000))
    for path in second_paths:
        output.extend(_serialized_string(path))
        output.extend(struct.pack("<III", 3, 0x0CAF5000, 5))
    output.extend(struct.pack("<QI", filetime, 0x55820000))
    for value in ("*", "*", "C:\\", "*", "*"):
        output.extend(_serialized_string(value))
        output.extend(struct.pack("<III", 3, 0x0CA29000, 5))
    output.extend(_serialized_string(f"C:\\{model_name}{document_suffix}"))
    output.extend(struct.pack("<III", 3, 0x0CA29000, 5))
    return bytes(output)


def _serialized_string(value: str) -> bytes:
    encoded = value.encode("utf-16le")
    units = len(encoded) // 2
    if units > 0xFE:
        raise SldprtFormatError(
            "native SOLIDWORKS serialized string exceeds 254 UTF-16 units"
        )
    return SERIALIZED_STRING_MARKER + bytes((units,)) + encoded


def _stable_u32(document: CadDocument, model_name: str, domain: bytes = b"") -> int:
    source = (
        model_name.encode("utf-8")
        + b"\0"
        + document.to_json(indent=None).encode("utf-8")
    )
    if domain:
        source += b"\0" + domain
    digest = hashlib.sha256(source).digest()
    value = int.from_bytes(digest[:4], "little") & 0x7FFFFFFF
    return value or 1


def _stable_creation_stamp(
    document: CadDocument, model_name: str, domain: bytes = b""
) -> int:
    span = _CREATION_STAMP_HIGH - _CREATION_STAMP_LOW
    return _CREATION_STAMP_LOW + _stable_u32(document, model_name, domain) % span


# this proves native fields match authored capabilities
def _proved_write_capabilities(
    document: CadDocument,
    authored: tuple[_WriteObject, ...],
    parsed: NativeModel,
    object_ids: dict[str, int],
) -> frozenset[Capability]:
    result: set[Capability] = set()
    if all(
        configuration.parent_id is None
        and not configuration.overrides
        and not configuration.suppressed_feature_ids
        for configuration in document.configurations
    ) and (
        not document.configurations
        or sum(configuration.active for configuration in document.configurations) == 1
    ):
        expected = tuple(
            (
                configuration.name,
                object_ids[f"configuration:{configuration.id}"],
            )
            for configuration in document.configurations
        )
        actual = tuple(
            (configuration.name, configuration.configuration_id)
            for configuration in parsed.configurations
        )
        if expected == actual:
            result.add(Capability.CONFIGURATIONS)
    expected_parameters = tuple(
        (
            item.object_id,
            dimension.name,
            round(dimension.value_mm, 10),
            dimension.role,
        )
        for item in authored
        for dimension in item.dimensions
        if any(
            parameter.name == dimension.name and parameter.owner_id == item.source_id
            for parameter in document.parameters
        )
    )
    actual_parameters = tuple(
        (
            feature.object_id,
            dimension.name,
            round(dimension.value_mm, 10),
            (
                ParameterRole.DRIVEN
                if dimension.native_role == "display"
                else ParameterRole.DRIVING
            ),
        )
        for feature in parsed.features
        if any(item.object_id == feature.object_id for item in authored)
        for dimension in feature.dimensions
        if any(
            parameter.name == dimension.name
            and parameter.owner_id
            == next(
                item.source_id
                for item in authored
                if item.object_id == feature.object_id
            )
            for parameter in document.parameters
        )
    )
    encodable = tuple(
        parameter
        for parameter in document.parameters
        if _parameter_dimension(parameter) is not None and parameter.expression is None
    )
    if (
        len(encodable) == len(document.parameters)
        and len(expected_parameters) == len(document.parameters)
        and expected_parameters == actual_parameters
    ):
        result.add(Capability.PARAMETERS)
    expected_planes = {
        PlaneObjectId: _ExpectedPlaneFrame(PlaneData, PlaneObjectId)
        for PlaneData in document.support_planes
        for PlaneObjectId in (object_ids[f"plane:{PlaneData.id}"],)
    }
    actual_planes = {
        plane.object_id: (
            _frame_vector(plane.origin_mm),
            _frame_vector(plane.u_axis),
            _frame_vector(plane.v_axis),
            _frame_vector(plane.normal),
        )
        for plane in parsed.planes
    }
    if len(expected_planes) == len(document.support_planes) and all(
        object_id in actual_planes and actual_planes[object_id] == frame
        for object_id, frame in expected_planes.items()
    ):
        result.add(Capability.SUPPORT_PLANES)
    expected_axes = _document_axis_bindings(document, object_ids)
    if expected_axes is not None:
        actual_axes = native_axis_bindings(parsed)
        if expected_axes and expected_axes <= actual_axes:
            result.add(Capability.SELECTIONS)
    expected_equations = expression_equation_texts(document)
    if expected_equations is not None:
        actual_equations = tuple(equation.source for equation in parsed.equations)
        if actual_equations[: len(expected_equations)] == expected_equations and all(
            source.startswith(f'"{_EQUATION_RESERVED_PREFIX}')
            for source in actual_equations[len(expected_equations) :]
        ):
            result.add(Capability.EXPRESSIONS)
    HasGrooveData = HasPadGrooveProof(document, authored, parsed)
    HasFilletData = HasBossFilletProof(document, authored, parsed)
    HasChamferData = HasBossChamferProof(document, authored, parsed)
    HasShellData = HasBossShellProof(document, authored, parsed)
    HasLinearPatternData = HasBossLinearPatternProof(document, authored, parsed)
    HasCircularPatternData = HasBossCircularPatternProof(document, authored, parsed)
    if (
        HasPadProof(document, authored, parsed)
        or HasSingleRevolutionProof(document, authored, parsed)
        or HasGrooveData
        or HasFilletData
        or HasChamferData
        or HasShellData
        or HasLinearPatternData
        or HasCircularPatternData
        or HasTwoFeatureProof(document, authored, parsed)
        or HasCutChainProof(document, authored, parsed)
    ):
        result.update(
            {
                Capability.BREP,
                Capability.PARAMETERS,
                Capability.PARAMETRIC_HISTORY,
                Capability.EDITABLE_SKETCHES,
                Capability.BODY_STRUCTURE,
            }
        )
    if (
        HasGrooveData
        or HasFilletData
        or HasChamferData
        or HasShellData
        or HasLinearPatternData
        or HasCircularPatternData
    ):
        result.add(Capability.SELECTIONS)
    return frozenset(result)


# this proves recovered single-pad records and direction semantics structurally
def HasPadProof(
    DocumentData: CadDocument,
    AuthoredObjs: tuple[_WriteObject, ...],
    ParsedModel: NativeModel,
) -> bool:
    if len(AuthoredObjs) != 2:
        return False
    SketchObject, PadObject = AuthoredObjs
    PlaneObjectId = (
        struct.unpack_from("<I", SketchObject.payload)[0]
        if len(SketchObject.payload) >= 4
        else 0
    )
    BoundsValue = _write_rectangle_bounds(SketchObject)
    CircleValue = _write_circle_profile(SketchObject)
    EndCodes = ExtrusionEditCodes(PadObject.payload)
    IsDimensionedBox = (
        BoundsValue is not None
        and ("KitPrimitive", "Box") in PadObject.properties
        and len(SketchObject.dimensions) == 2
    )
    ExpectedFeatureId = 34 if IsDimensionedBox else (33 if CircleValue else 32)
    if (
        (BoundsValue is None) == (CircleValue is None)
        or EndCodes is None
        or SketchObject.object_id != 26
        or SketchObject.name != "Sketch1"
        or PadObject.object_id != ExpectedFeatureId
        or PadObject.name != "Boss-Extrude1"
        or len(PadObject.dimensions) != 1
        or len(ParsedModel.sketches) != 1
        or len(ParsedModel.operations) != 1
    ):
        return False
    NativeSketch = ParsedModel.sketches[0]
    NativePad = ParsedModel.operations[0]
    ExpectedProfile = BoundsValue if BoundsValue is not None else CircleValue
    ExpectedKind = "rectangle" if BoundsValue is not None else "circle"
    ProfilesValue = tuple(
        ProfileData
        for ProfileData in NativeSketch.profiles
        if ProfileData.kind == ExpectedKind
    )
    HasProfile = ExpectedProfile is not None and (
        len(ProfilesValue) == 1
        and len(ProfilesValue[0].coordinates) == len(ExpectedProfile)
        and all(
            math.isclose(ActualValue, ExpectedValue, abs_tol=1.0e-10)
            for ActualValue, ExpectedValue in zip(
                ProfilesValue[0].coordinates,
                ExpectedProfile,
                strict=True,
            )
        )
    )
    DepthValue = PadObject.dimensions[0].value_mm
    ExpectedDepth = (1, 1, -1, -1, 1, 1)
    ExpectedDims = tuple(
        (ItemData.name, round(ItemData.value_mm, 10))
        for ItemData in SketchObject.dimensions
    )
    ActualDims = tuple(
        (ItemData.name, round(ItemData.value_mm, 10))
        for ItemData in NativeSketch.dimensions
    )
    ConstraintKinds = tuple(ItemData.kind for ItemData in NativeSketch.constraints)
    ExpectedConstraintKinds = (
        (
            "horizontal",
            "vertical",
            "horizontal",
            "vertical",
            *(("distance",) * len(ExpectedDims)),
        )
        if BoundsValue is not None
        else ("diameter",)
    )
    if (
        NativeSketch.object_id != 26
        or NativeSketch.support_plane_id != PlaneObjectId
        or not HasProfile
        or ConstraintKinds != ExpectedConstraintKinds
        or ActualDims != ExpectedDims
        or NativePad.object_id != ExpectedFeatureId
        or NativePad.name != "Boss-Extrude1"
        or NativePad.profile_id != 26
        or NativePad.kind not in {"boss", "join"}
        or NativePad.direction_code != EndCodes[0]
        or NativePad.termination_code != EndCodes[1]
        or NativePad.length_mm is None
        or not math.isclose(NativePad.length_mm, DepthValue, abs_tol=1.0e-10)
        or len(NativePad.depth_copies) != len(ExpectedDepth)
        or not math.isclose(
            NativePad.depth_copies[0].value_mm,
            DepthValue,
            abs_tol=1.0e-10,
        )
        or (
            EndCodes == (0, 0)
            and any(
                CopyData.sign != CopySign
                or not math.isclose(
                    CopyData.value_mm,
                    DepthValue * CopySign,
                    abs_tol=1.0e-10,
                )
                for CopyData, CopySign in zip(
                    NativePad.depth_copies,
                    ExpectedDepth,
                    strict=True,
                )
            )
        )
    ):
        return False
    NativeFeatureIds = tuple(
        ItemData.object_id
        for ItemData in ParsedModel.features
        if ItemData.object_id in {26, ExpectedFeatureId}
    )
    return NativeFeatureIds == (26, ExpectedFeatureId) and len(DocumentData.bodies) == 1


# this proves the revolved profile, full angle, vertical sketch axis, and native ids
def HasSingleRevolutionProof(
    DocumentData: CadDocument,
    AuthoredObjs: tuple[_WriteObject, ...],
    ParsedModel: NativeModel,
) -> bool:
    if (
        len(AuthoredObjs) != 2
        or len(ParsedModel.sketches) != 1
        or len(ParsedModel.operations) != 1
        or len(DocumentData.bodies) != 1
    ):
        return False
    SketchObject, RevolveObject = AuthoredObjs
    BoundsValue = _write_rectangle_bounds(SketchObject)
    if (
        BoundsValue is None
        or SketchObject.object_id != 26
        or SketchObject.name != "Sketch1"
        or RevolveObject.object_id != 31
        or RevolveObject.name != "Revolve1"
        or len(RevolveObject.dimensions) != 1
    ):
        return False
    NativeSketch = ParsedModel.sketches[0]
    NativeRevolve = ParsedModel.operations[0]
    NativeFeature = next(
        (ItemData for ItemData in ParsedModel.features if ItemData.object_id == 31),
        None,
    )
    ProfileData = tuple(
        ItemData for ItemData in NativeSketch.profiles if ItemData.kind == "rectangle"
    )
    DimensionData = RevolveObject.dimensions[0]
    if (
        NativeSketch.object_id != 26
        or NativeSketch.support_plane_id != 2
        or len(ProfileData) != 1
        or len(ProfileData[0].coordinates) != len(BoundsValue)
        or any(
            not math.isclose(ActualValue, ExpectedValue, abs_tol=1.0e-10)
            for ActualValue, ExpectedValue in zip(
                ProfileData[0].coordinates,
                BoundsValue,
                strict=True,
            )
        )
        or tuple(ItemData.kind for ItemData in NativeSketch.constraints)
        != ("horizontal", "vertical", "horizontal", "vertical")
        or NativeRevolve.object_id != 31
        or NativeRevolve.name != "Revolve1"
        or NativeRevolve.kind != "revolve_join"
        or NativeRevolve.profile_id != 26
        or NativeRevolve.angle_degrees is None
        or not math.isclose(
            NativeRevolve.angle_degrees,
            DimensionData.value_mm,
            rel_tol=0.0,
            abs_tol=1.0e-10,
        )
        or native_axis_bindings(ParsedModel)
        != frozenset({(31, 26, VERTICAL_AXIS_SUBELEMENT)})
        or NativeFeature is None
        or len(NativeFeature.dimensions) != 1
        or NativeFeature.dimensions[0].name != "D1"
        or NativeFeature.dimensions[0].kind != "angle"
        or not math.isclose(
            NativeFeature.dimensions[0].value_mm,
            DimensionData.value_mm,
            rel_tol=0.0,
            abs_tol=1.0e-10,
        )
    ):
        return False
    NativeFeatureIds = tuple(
        ItemData.object_id
        for ItemData in ParsedModel.features
        if ItemData.object_id in {26, 31}
    )
    return NativeFeatureIds == (26, 31)


# this proves the pad, revolved cut, angle, profiles, and horizontal-axis source
def HasPadGrooveProof(
    DocumentData: CadDocument,
    AuthoredObjs: tuple[_WriteObject, ...],
    ParsedModel: NativeModel,
) -> bool:
    if (
        len(AuthoredObjs) != 4
        or len(ParsedModel.sketches) != 2
        or len(ParsedModel.operations) != 2
        or len(DocumentData.bodies) != 1
    ):
        return False
    SketchOne, PadObject, SketchTwo, GrooveObject = AuthoredObjs
    SourceSketches = tuple(
        next(
            (
                ItemData
                for ItemData in DocumentData.sketches
                if ItemData.id == SketchObject.source_id
            ),
            None,
        )
        for SketchObject in (SketchOne, SketchTwo)
    )
    SourceFeatures = tuple(
        next(
            (
                ItemData
                for ItemData in DocumentData.feature_timeline
                if ItemData.id == FeatureObject.source_id
            ),
            None,
        )
        for FeatureObject in (PadObject, GrooveObject)
    )
    if any(ItemData is None for ItemData in (*SourceSketches, *SourceFeatures)):
        return False
    SourceSketchOne, SourceSketchTwo = SourceSketches
    SourcePad, SourceGroove = SourceFeatures
    if (
        SourceSketchOne is None
        or SourceSketchTwo is None
        or SourcePad is None
        or SourceGroove is None
    ):
        return False
    DimensionData = _FreeCadPadGrooveDimensions(
        DocumentData,
        (SourceSketchOne, SourceSketchTwo),
        (SourcePad, SourceGroove),
    )
    BoundsData = (
        _write_rectangle_bounds(SketchOne),
        _write_rectangle_bounds(SketchTwo),
    )
    EndCodes = ExtrusionEditCodes(PadObject.payload)
    if (
        DimensionData is None
        or any(ItemData is None for ItemData in BoundsData)
        or EndCodes is None
        or (SketchOne.object_id, PadObject.object_id) != (26, 32)
        or (SketchTwo.object_id, GrooveObject.object_id) != (33, 39)
        or (SketchOne.name, PadObject.name) != ("Sketch1", "Boss-Extrude1")
        or (SketchTwo.name, GrooveObject.name) != ("Sketch2", "Cut-Revolve1")
    ):
        return False
    NativePad, NativeGroove = ParsedModel.operations
    if (
        NativePad.object_id != 32
        or NativePad.name != "Boss-Extrude1"
        or NativePad.kind not in {"boss", "join"}
        or NativePad.profile_id != 26
        or NativePad.direction_code != EndCodes[0]
        or NativePad.termination_code != EndCodes[1]
        or NativePad.length_mm is None
        or not math.isclose(
            NativePad.length_mm,
            DimensionData[0].value_mm,
            rel_tol=0.0,
            abs_tol=1.0e-10,
        )
        or NativeGroove.object_id != 39
        or NativeGroove.name != "Cut-Revolve1"
        or NativeGroove.kind != "revolve_cut"
        or NativeGroove.profile_id != 33
        or NativeGroove.angle_degrees is None
        or not math.isclose(
            NativeGroove.angle_degrees,
            DimensionData[1].value_mm,
            rel_tol=0.0,
            abs_tol=1.0e-10,
        )
    ):
        return False
    for NativeSketch, SketchObject, BoundsValue, ObjectId in zip(
        ParsedModel.sketches,
        (SketchOne, SketchTwo),
        BoundsData,
        (26, 33),
        strict=True,
    ):
        if BoundsValue is None:
            return False
        ProfileData = tuple(
            ItemData
            for ItemData in NativeSketch.profiles
            if ItemData.kind == "rectangle"
        )
        if (
            NativeSketch.object_id != ObjectId
            or NativeSketch.support_plane_id != 2
            or len(ProfileData) != 1
            or any(
                not math.isclose(ActualValue, ExpectedValue, abs_tol=1.0e-10)
                for ActualValue, ExpectedValue in zip(
                    ProfileData[0].coordinates,
                    BoundsValue,
                    strict=True,
                )
            )
            or tuple(
                (ItemData.name, round(ItemData.value_mm, 10))
                for ItemData in NativeSketch.dimensions
            )
            != tuple(
                (ItemData.name, round(ItemData.value_mm, 10))
                for ItemData in SketchObject.dimensions
            )
        ):
            return False
    NativeFeatureIds = tuple(
        ItemData.object_id
        for ItemData in ParsedModel.features
        if ItemData.object_id in {26, 32, 33, 39}
    )
    return NativeFeatureIds == (26, 32, 33, 39)


# this proves the editable boss, radius, dependency, and selected native edge
def HasBossFilletProof(
    DocumentData: CadDocument,
    AuthoredObjs: tuple[_WriteObject, ...],
    ParsedModel: NativeModel,
) -> bool:
    if (
        len(AuthoredObjs) != 3
        or len(ParsedModel.sketches) != 1
        or len(ParsedModel.operations) != 2
        or len(DocumentData.bodies) != 1
    ):
        return False
    SketchObject, PadObject, FilletObject = AuthoredObjs
    SourceSketch = next(
        (
            ItemData
            for ItemData in DocumentData.sketches
            if ItemData.id == SketchObject.source_id
        ),
        None,
    )
    SourceFeatures = tuple(
        ItemData
        for ItemData in sorted(
            DocumentData.feature_timeline,
            key=lambda ItemData: ItemData.order,
        )
        if not _is_native_system_feature(ItemData)
    )
    BoundsValue = _write_rectangle_bounds(SketchObject)
    if SourceSketch is None or len(SourceFeatures) != 2 or BoundsValue is None:
        return False
    SourcePad, SourceFillet = SourceFeatures
    DimensionData = _FreeCadBossFilletDimensions(
        DocumentData,
        SourceSketch,
        SourcePad,
        SourceFillet,
        BoundsValue,
    )
    if (
        DimensionData is None
        or (SketchObject.object_id, PadObject.object_id, FilletObject.object_id)
        != (26, 32, 34)
        or (SketchObject.name, PadObject.name, FilletObject.name)
        != ("Sketch1", "Boss-Extrude1", "Fillet1")
        or ExtrusionEditCodes(PadObject.payload) != (0, 0)
        or FilletObject.payload != _FilletSelectionRecord(32, 3)
    ):
        return False
    NativeSketch = ParsedModel.sketches[0]
    NativePad, NativeFillet = ParsedModel.operations
    ProfilesValue = tuple(
        ItemData for ItemData in NativeSketch.profiles if ItemData.kind == "rectangle"
    )
    ExpectedDepthSigns = (1, 1, -1, -1, 1, 1)
    if (
        NativeSketch.object_id != 26
        or NativeSketch.support_plane_id != 2
        or len(ProfilesValue) != 1
        or len(ProfilesValue[0].coordinates) != len(BoundsValue)
        or any(
            not math.isclose(ActualValue, ExpectedValue, abs_tol=1.0e-10)
            for ActualValue, ExpectedValue in zip(
                ProfilesValue[0].coordinates,
                BoundsValue,
                strict=True,
            )
        )
        or tuple(ItemData.kind for ItemData in NativeSketch.constraints)
        != ("horizontal", "vertical", "horizontal", "vertical")
        or NativePad.object_id != 32
        or NativePad.name != "Boss-Extrude1"
        or NativePad.kind not in {"boss", "join"}
        or NativePad.profile_id != 26
        or NativePad.dependencies != (26,)
        or NativePad.direction_code != 0
        or NativePad.termination_code != 0
        or NativePad.length_mm is None
        or not math.isclose(
            NativePad.length_mm,
            DimensionData[0].value_mm,
            rel_tol=0.0,
            abs_tol=1.0e-10,
        )
        or len(NativePad.depth_copies) != len(ExpectedDepthSigns)
        or any(
            ItemData.sign != SignValue
            or not math.isclose(
                ItemData.value_mm,
                DimensionData[0].value_mm * SignValue,
                rel_tol=0.0,
                abs_tol=1.0e-10,
            )
            for ItemData, SignValue in zip(
                NativePad.depth_copies,
                ExpectedDepthSigns,
                strict=True,
            )
        )
        or NativeFillet.object_id != 34
        or NativeFillet.name != "Fillet1"
        or NativeFillet.kind != "fillet"
        or NativeFillet.profile_id is not None
        or NativeFillet.dependencies != (32,)
        or NativeFillet.radius_mm is None
        or not math.isclose(
            NativeFillet.radius_mm,
            DimensionData[1].value_mm,
            rel_tol=0.0,
            abs_tol=1.0e-10,
        )
        or NativeFillet.selection_kind != "edge"
        or NativeFillet.selection_references != ((32, 3),)
        or NativeFillet.selected_local_ids != (3,)
    ):
        return False
    NativeFilletFeature = next(
        (ItemData for ItemData in ParsedModel.features if ItemData.object_id == 34),
        None,
    )
    NativeFeatureIds = tuple(
        ItemData.object_id
        for ItemData in ParsedModel.features
        if ItemData.object_id in {26, 32, 34}
    )
    return (
        NativeFilletFeature is not None
        and len(NativeFilletFeature.dimensions) == 1
        and NativeFilletFeature.dimensions[0].name == "D1"
        and NativeFilletFeature.dimensions[0].kind == "radius"
        and math.isclose(
            NativeFilletFeature.dimensions[0].value_mm,
            DimensionData[1].value_mm,
            rel_tol=0.0,
            abs_tol=1.0e-10,
        )
        and NativeFeatureIds == (26, 32, 34)
    )


# this proves the editable boss, chamfer distance, dependency, and selected native edge
def HasBossChamferProof(
    DocumentData: CadDocument,
    AuthoredObjs: tuple[_WriteObject, ...],
    ParsedModel: NativeModel,
) -> bool:
    if (
        len(AuthoredObjs) != 3
        or len(ParsedModel.sketches) != 1
        or len(ParsedModel.operations) != 2
        or len(DocumentData.bodies) != 1
    ):
        return False
    SketchObject, PadObject, ChamferObject = AuthoredObjs
    SourceSketch = next(
        (
            ItemData
            for ItemData in DocumentData.sketches
            if ItemData.id == SketchObject.source_id
        ),
        None,
    )
    SourceFeatures = tuple(
        ItemData
        for ItemData in sorted(
            DocumentData.feature_timeline,
            key=lambda ItemData: ItemData.order,
        )
        if not _is_native_system_feature(ItemData)
    )
    BoundsValue = _write_rectangle_bounds(SketchObject)
    if SourceSketch is None or len(SourceFeatures) != 2 or BoundsValue is None:
        return False
    SourcePad, SourceChamfer = SourceFeatures
    DimensionData = _FreeCadBossChamferDimensions(
        DocumentData,
        SourceSketch,
        SourcePad,
        SourceChamfer,
        BoundsValue,
    )
    if (
        DimensionData is None
        or (SketchObject.object_id, PadObject.object_id, ChamferObject.object_id)
        != (26, 32, 35)
        or (SketchObject.name, PadObject.name, ChamferObject.name)
        != ("Sketch1", "Boss-Extrude1", "Chamfer1")
        or ExtrusionEditCodes(PadObject.payload) != (0, 0)
        or ChamferObject.payload != _FilletSelectionRecord(32, 3)
    ):
        return False
    NativeSketch = ParsedModel.sketches[0]
    NativePad, NativeChamfer = ParsedModel.operations
    ProfilesValue = tuple(
        ItemData for ItemData in NativeSketch.profiles if ItemData.kind == "rectangle"
    )
    ExpectedDepthSigns = (1, 1, -1, -1, 1, 1)
    if (
        NativeSketch.object_id != 26
        or NativeSketch.support_plane_id != 2
        or len(ProfilesValue) != 1
        or len(ProfilesValue[0].coordinates) != len(BoundsValue)
        or any(
            not math.isclose(ActualValue, ExpectedValue, abs_tol=1.0e-10)
            for ActualValue, ExpectedValue in zip(
                ProfilesValue[0].coordinates,
                BoundsValue,
                strict=True,
            )
        )
        or tuple(ItemData.kind for ItemData in NativeSketch.constraints)
        != ("horizontal", "vertical", "horizontal", "vertical")
        or NativePad.object_id != 32
        or NativePad.name != "Boss-Extrude1"
        or NativePad.kind not in {"boss", "join"}
        or NativePad.profile_id != 26
        or NativePad.dependencies != (26,)
        or NativePad.direction_code != 0
        or NativePad.termination_code != 0
        or NativePad.length_mm is None
        or not math.isclose(
            NativePad.length_mm,
            DimensionData[0].value_mm,
            rel_tol=0.0,
            abs_tol=1.0e-10,
        )
        or len(NativePad.depth_copies) != len(ExpectedDepthSigns)
        or any(
            ItemData.sign != SignValue
            or not math.isclose(
                ItemData.value_mm,
                DimensionData[0].value_mm * SignValue,
                rel_tol=0.0,
                abs_tol=1.0e-10,
            )
            for ItemData, SignValue in zip(
                NativePad.depth_copies,
                ExpectedDepthSigns,
                strict=True,
            )
        )
        or NativeChamfer.object_id != 35
        or NativeChamfer.name != "Chamfer1"
        or NativeChamfer.kind != "chamfer"
        or NativeChamfer.profile_id is not None
        or NativeChamfer.dependencies != (32,)
        or NativeChamfer.length_mm is None
        or not math.isclose(
            NativeChamfer.length_mm,
            DimensionData[1].value_mm,
            rel_tol=0.0,
            abs_tol=1.0e-10,
        )
        or NativeChamfer.selection_kind != "edge"
        or NativeChamfer.selection_references != ((32, 3),)
        or NativeChamfer.selected_local_ids != (3,)
        or NativeChamfer.mode != "equal_distance"
    ):
        return False
    NativeChamferFeature = next(
        (ItemData for ItemData in ParsedModel.features if ItemData.object_id == 35),
        None,
    )
    NativeFeatureIds = tuple(
        ItemData.object_id
        for ItemData in ParsedModel.features
        if ItemData.object_id in {26, 32, 35}
    )
    return (
        NativeChamferFeature is not None
        and len(NativeChamferFeature.dimensions) == 1
        and tuple(
            (ItemData.name, ItemData.kind)
            for ItemData in NativeChamferFeature.dimensions
        )
        == (("D1", "distance"),)
        and math.isclose(
            next(
                ItemData.value_mm
                for ItemData in NativeChamferFeature.dimensions
                if ItemData.name == "D1"
            ),
            DimensionData[1].value_mm,
            rel_tol=0.0,
            abs_tol=1.0e-10,
        )
        and NativeFeatureIds == (26, 32, 35)
    )


# this proves the editable boss, inward thickness, dependency, and removed top face
def HasBossShellProof(
    DocumentData: CadDocument,
    AuthoredObjs: tuple[_WriteObject, ...],
    ParsedModel: NativeModel,
) -> bool:
    if (
        len(AuthoredObjs) != 3
        or len(ParsedModel.sketches) != 1
        or len(ParsedModel.operations) != 2
        or len(DocumentData.bodies) != 1
    ):
        return False
    SketchObject, PadObject, ShellObject = AuthoredObjs
    SourceSketch = next(
        (
            ItemData
            for ItemData in DocumentData.sketches
            if ItemData.id == SketchObject.source_id
        ),
        None,
    )
    SourceFeatures = tuple(
        ItemData
        for ItemData in sorted(
            DocumentData.feature_timeline,
            key=lambda ItemData: ItemData.order,
        )
        if not _is_native_system_feature(ItemData)
    )
    BoundsValue = _write_rectangle_bounds(SketchObject)
    if SourceSketch is None or len(SourceFeatures) != 2 or BoundsValue is None:
        return False
    SourcePad, SourceShell = SourceFeatures
    DimensionData = _FreeCadBossShellDimensions(
        DocumentData,
        SourceSketch,
        SourcePad,
        SourceShell,
        BoundsValue,
    )
    if (
        DimensionData is None
        or (SketchObject.object_id, PadObject.object_id, ShellObject.object_id)
        != (26, 32, 34)
        or (SketchObject.name, PadObject.name, ShellObject.name)
        != ("Sketch1", "Boss-Extrude1", "Shell1")
        or ExtrusionEditCodes(PadObject.payload) != (0, 0)
        or ShellObject.payload != _ShellSelectionRecord(32)
    ):
        return False
    NativeSketch = ParsedModel.sketches[0]
    NativePad, NativeShell = ParsedModel.operations
    ProfilesValue = tuple(
        ItemData for ItemData in NativeSketch.profiles if ItemData.kind == "rectangle"
    )
    ExpectedDepthSigns = (1, 1, -1, -1, 1, 1)
    if (
        NativeSketch.object_id != 26
        or NativeSketch.support_plane_id != 2
        or len(ProfilesValue) != 1
        or len(ProfilesValue[0].coordinates) != len(BoundsValue)
        or any(
            not math.isclose(ActualValue, ExpectedValue, abs_tol=1.0e-10)
            for ActualValue, ExpectedValue in zip(
                ProfilesValue[0].coordinates,
                BoundsValue,
                strict=True,
            )
        )
        or tuple(ItemData.kind for ItemData in NativeSketch.constraints)
        != ("horizontal", "vertical", "horizontal", "vertical")
        or NativePad.object_id != 32
        or NativePad.name != "Boss-Extrude1"
        or NativePad.kind not in {"boss", "join"}
        or NativePad.profile_id != 26
        or NativePad.dependencies != (26,)
        or NativePad.direction_code != 0
        or NativePad.termination_code != 0
        or NativePad.length_mm is None
        or not math.isclose(
            NativePad.length_mm,
            DimensionData[0].value_mm,
            rel_tol=0.0,
            abs_tol=1.0e-10,
        )
        or len(NativePad.depth_copies) != len(ExpectedDepthSigns)
        or any(
            ItemData.sign != SignValue
            or not math.isclose(
                ItemData.value_mm,
                DimensionData[0].value_mm * SignValue,
                rel_tol=0.0,
                abs_tol=1.0e-10,
            )
            for ItemData, SignValue in zip(
                NativePad.depth_copies,
                ExpectedDepthSigns,
                strict=True,
            )
        )
        or NativeShell.object_id != 34
        or NativeShell.name != "Shell1"
        or NativeShell.kind != "shell"
        or NativeShell.profile_id is not None
        or NativeShell.dependencies != (32,)
        or NativeShell.length_mm is None
        or not math.isclose(
            NativeShell.length_mm,
            DimensionData[1].value_mm,
            rel_tol=0.0,
            abs_tol=1.0e-10,
        )
        or NativeShell.selection_kind != "face"
        or NativeShell.selection_references != ((32, 1), (32, 4))
        or NativeShell.selected_local_ids != (1, 4)
    ):
        return False
    NativeShellFeature = next(
        (ItemData for ItemData in ParsedModel.features if ItemData.object_id == 34),
        None,
    )
    NativeFeatureIds = tuple(
        ItemData.object_id
        for ItemData in ParsedModel.features
        if ItemData.object_id in {26, 32, 34}
    )
    return (
        NativeShellFeature is not None
        and len(NativeShellFeature.dimensions) == 1
        and NativeShellFeature.dimensions[0].name == "D1"
        and NativeShellFeature.dimensions[0].kind == "thickness"
        and math.isclose(
            NativeShellFeature.dimensions[0].value_mm,
            DimensionData[1].value_mm,
            rel_tol=0.0,
            abs_tol=1.0e-10,
        )
        and NativeFeatureIds == (26, 32, 34)
    )


# this proves the editable boss, pattern count, spacing, direction edge, and fused body
def HasBossLinearPatternProof(
    DocumentData: CadDocument,
    AuthoredObjs: tuple[_WriteObject, ...],
    ParsedModel: NativeModel,
) -> bool:
    if (
        len(AuthoredObjs) != 3
        or len(ParsedModel.sketches) != 1
        or len(ParsedModel.operations) != 2
        or len(DocumentData.bodies) != 1
    ):
        return False
    SketchObject, PadObject, PatternObject = AuthoredObjs
    SourceSketch = next(
        (
            ItemData
            for ItemData in DocumentData.sketches
            if ItemData.id == SketchObject.source_id
        ),
        None,
    )
    SourceFeatures = tuple(
        ItemData
        for ItemData in sorted(
            DocumentData.feature_timeline,
            key=lambda ItemData: ItemData.order,
        )
        if not _is_native_system_feature(ItemData)
    )
    BoundsValue = _write_rectangle_bounds(SketchObject)
    if SourceSketch is None or len(SourceFeatures) != 2 or BoundsValue is None:
        return False
    SourcePad, SourcePattern = SourceFeatures
    DimensionData = _FreeCadBossLinearPatternDimensions(
        DocumentData,
        SourceSketch,
        SourcePad,
        SourcePattern,
        BoundsValue,
    )
    if (
        DimensionData is None
        or (SketchObject.object_id, PadObject.object_id, PatternObject.object_id)
        != (26, 32, 40)
        or (SketchObject.name, PadObject.name, PatternObject.name)
        != ("Sketch1", "Boss-Extrude1", "LPattern1")
        or ExtrusionEditCodes(PadObject.payload) != (0, 0)
        or PatternObject.kind != "LPattern"
        or PatternObject.payload
        or tuple(ItemData.name for ItemData in PatternObject.dimensions) != ("D1", "D3")
    ):
        return False
    NativeSketch = ParsedModel.sketches[0]
    NativePad, NativePattern = ParsedModel.operations
    ProfilesValue = tuple(
        ItemData for ItemData in NativeSketch.profiles if ItemData.kind == "rectangle"
    )
    ExpectedDepthSigns = (1, 1, -1, -1, 1, 1)
    if (
        NativeSketch.object_id != 26
        or NativeSketch.support_plane_id != 2
        or len(ProfilesValue) != 1
        or len(ProfilesValue[0].coordinates) != len(BoundsValue)
        or any(
            not math.isclose(ActualValue, ExpectedValue, abs_tol=1.0e-10)
            for ActualValue, ExpectedValue in zip(
                ProfilesValue[0].coordinates,
                BoundsValue,
                strict=True,
            )
        )
        or tuple(ItemData.kind for ItemData in NativeSketch.constraints)
        != ("horizontal", "vertical", "horizontal", "vertical")
        or NativePad.object_id != 32
        or NativePad.name != "Boss-Extrude1"
        or NativePad.kind not in {"boss", "join"}
        or NativePad.profile_id != 26
        or NativePad.dependencies != (26,)
        or NativePad.direction_code != 0
        or NativePad.termination_code != 0
        or NativePad.length_mm is None
        or not math.isclose(
            NativePad.length_mm,
            DimensionData[0].value_mm,
            rel_tol=0.0,
            abs_tol=1.0e-10,
        )
        or len(NativePad.depth_copies) != len(ExpectedDepthSigns)
        or any(
            ItemData.sign != SignValue
            or not math.isclose(
                ItemData.value_mm,
                DimensionData[0].value_mm * SignValue,
                rel_tol=0.0,
                abs_tol=1.0e-10,
            )
            for ItemData, SignValue in zip(
                NativePad.depth_copies,
                ExpectedDepthSigns,
                strict=True,
            )
        )
        or NativePattern.object_id != 40
        or NativePattern.name != "LPattern1"
        or NativePattern.kind != "linear_pattern"
        or NativePattern.profile_id is not None
        or NativePattern.dependencies != (32,)
        or NativePattern.direction_code != 1
        or NativePattern.instance_count != int(DimensionData[1].value_mm)
        or NativePattern.spacing_mm is None
        or not math.isclose(
            NativePattern.spacing_mm,
            DimensionData[2].value_mm,
            rel_tol=0.0,
            abs_tol=1.0e-10,
        )
        or NativePattern.selection_kind != "edge"
        or NativePattern.selection_references != ((32, 4), (32, 3))
        or NativePattern.selected_local_ids != (4, 3)
        or NativePattern.mode != "linear"
    ):
        return False
    NativePatternFeature = next(
        (ItemData for ItemData in ParsedModel.features if ItemData.object_id == 40),
        None,
    )
    NativeFeatureIds = tuple(
        ItemData.object_id
        for ItemData in ParsedModel.features
        if ItemData.object_id in {26, 32, 40}
    )
    return (
        NativePatternFeature is not None
        and tuple(
            (ItemData.name, ItemData.kind)
            for ItemData in NativePatternFeature.dimensions
        )
        == (("D1", "instance_count"), ("D3", "spacing"))
        and NativeFeatureIds == (26, 32, 40)
    )


# this proves the editable boss, angular span, count, selected axis, and fused body
def HasBossCircularPatternProof(
    DocumentData: CadDocument,
    AuthoredObjs: tuple[_WriteObject, ...],
    ParsedModel: NativeModel,
) -> bool:
    if (
        len(AuthoredObjs) != 3
        or len(ParsedModel.sketches) != 1
        or len(ParsedModel.operations) != 2
        or len(DocumentData.bodies) != 1
    ):
        return False
    SketchObject, PadObject, PatternObject = AuthoredObjs
    SourceSketch = next(
        (
            ItemData
            for ItemData in DocumentData.sketches
            if ItemData.id == SketchObject.source_id
        ),
        None,
    )
    SourceFeatures = tuple(
        ItemData
        for ItemData in sorted(
            DocumentData.feature_timeline,
            key=lambda ItemData: ItemData.order,
        )
        if not _is_native_system_feature(ItemData)
    )
    BoundsValue = _write_rectangle_bounds(SketchObject)
    if SourceSketch is None or len(SourceFeatures) != 2 or BoundsValue is None:
        return False
    SourcePad, SourcePattern = SourceFeatures
    DimensionData = _FreeCadBossCircularPatternDimensions(
        DocumentData,
        SourceSketch,
        SourcePad,
        SourcePattern,
        BoundsValue,
    )
    if (
        DimensionData is None
        or (SketchObject.object_id, PadObject.object_id, PatternObject.object_id)
        != (26, 32, 46)
        or (SketchObject.name, PadObject.name, PatternObject.name)
        != ("Sketch1", "Boss-Extrude1", "CirPattern1")
        or ExtrusionEditCodes(PadObject.payload) != (0, 0)
        or PatternObject.kind != "CirPattern"
        or PatternObject.payload
        or tuple(ItemData.name for ItemData in PatternObject.dimensions) != ("D1", "D3")
    ):
        return False
    NativeSketch = ParsedModel.sketches[0]
    NativePad, NativePattern = ParsedModel.operations
    ProfilesValue = tuple(
        ItemData for ItemData in NativeSketch.profiles if ItemData.kind == "rectangle"
    )
    ExpectedDepthSigns = (1, 1, -1, -1, 1, 1)
    if (
        NativeSketch.object_id != 26
        or NativeSketch.support_plane_id != 2
        or len(ProfilesValue) != 1
        or len(ProfilesValue[0].coordinates) != len(BoundsValue)
        or any(
            not math.isclose(ActualValue, ExpectedValue, abs_tol=1.0e-10)
            for ActualValue, ExpectedValue in zip(
                ProfilesValue[0].coordinates,
                BoundsValue,
                strict=True,
            )
        )
        or tuple(ItemData.kind for ItemData in NativeSketch.constraints)
        != ("horizontal", "vertical", "horizontal", "vertical")
        or NativePad.object_id != 32
        or NativePad.name != "Boss-Extrude1"
        or NativePad.kind not in {"boss", "join"}
        or NativePad.profile_id != 26
        or NativePad.dependencies != (26,)
        or NativePad.direction_code != 0
        or NativePad.termination_code != 0
        or NativePad.length_mm is None
        or not math.isclose(
            NativePad.length_mm,
            DimensionData[0].value_mm,
            rel_tol=0.0,
            abs_tol=1.0e-10,
        )
        or len(NativePad.depth_copies) != len(ExpectedDepthSigns)
        or any(
            ItemData.sign != SignValue
            or not math.isclose(
                ItemData.value_mm,
                DimensionData[0].value_mm * SignValue,
                rel_tol=0.0,
                abs_tol=1.0e-10,
            )
            for ItemData, SignValue in zip(
                NativePad.depth_copies,
                ExpectedDepthSigns,
                strict=True,
            )
        )
        or NativePattern.object_id != 46
        or NativePattern.name != "CirPattern1"
        or NativePattern.kind != "circular_pattern"
        or NativePattern.profile_id is not None
        or NativePattern.dependencies != (32,)
        or NativePattern.direction_code != 1
        or NativePattern.instance_count != int(DimensionData[1].value_mm)
        or NativePattern.angle_degrees is None
        or not math.isclose(
            NativePattern.angle_degrees,
            DimensionData[2].value_mm,
            rel_tol=0.0,
            abs_tol=1.0e-10,
        )
        or NativePattern.selection_kind != "edge"
        or NativePattern.selection_references != ((32, 4), (32, 1))
        or NativePattern.selected_local_ids != (4, 1)
        or NativePattern.mode != "circular"
    ):
        return False
    NativePatternFeature = next(
        (ItemData for ItemData in ParsedModel.features if ItemData.object_id == 46),
        None,
    )
    NativeFeatureIds = tuple(
        ItemData.object_id
        for ItemData in ParsedModel.features
        if ItemData.object_id in {26, 32, 46}
    )
    return (
        NativePatternFeature is not None
        and tuple(
            (ItemData.name, ItemData.kind)
            for ItemData in NativePatternFeature.dimensions
        )
        == (("D1", "instance_count"), ("D3", "angle"))
        and NativeFeatureIds == (26, 32, 46)
    )


# this proves both editable rectangles, parameters, directions, and operation order
def HasTwoFeatureProof(
    DocumentData: CadDocument,
    AuthoredObjs: tuple[_WriteObject, ...],
    ParsedModel: NativeModel,
) -> bool:
    if (
        len(AuthoredObjs) != 4
        or len(ParsedModel.sketches) != 2
        or len(ParsedModel.operations) != 2
        or len(DocumentData.bodies) != 1
    ):
        return False
    SketchOne, FeatureOne, SketchTwo, FeatureTwo = AuthoredObjs
    SecondIsBoss = FeatureTwo.class_name == "moExtrusion_c"
    ExpectedData = (
        (SketchOne, FeatureOne, 26, 32, "Sketch1", "Boss-Extrude1", {"boss", "join"}),
        (
            SketchTwo,
            FeatureTwo,
            33,
            40,
            "Sketch2",
            "Boss-Extrude2" if SecondIsBoss else "Cut-Extrude1",
            {"boss", "join"} if SecondIsBoss else {"cut"},
        ),
    )
    ExpectedDepthSigns = (1, 1, -1, -1, 1, 1)
    for NativeSketch, NativeFeature, ExpectedValue in zip(
        ParsedModel.sketches,
        ParsedModel.operations,
        ExpectedData,
        strict=True,
    ):
        (
            SketchObject,
            FeatureObject,
            SketchObjectId,
            FeatureObjectId,
            SketchName,
            FeatureName,
            FeatureKinds,
        ) = ExpectedValue
        BoundsValue = _write_rectangle_bounds(SketchObject)
        EndCodes = ExtrusionEditCodes(FeatureObject.payload)
        if (
            BoundsValue is None
            or EndCodes is None
            or len(FeatureObject.dimensions) != (0 if EndCodes[1] == 1 else 1)
        ):
            return False
        ProfileData = tuple(
            ItemData
            for ItemData in NativeSketch.profiles
            if ItemData.kind == "rectangle"
        )
        ExpectedDims = tuple(
            (ItemData.name, round(ItemData.value_mm, 10))
            for ItemData in SketchObject.dimensions
        )
        ActualDims = tuple(
            (ItemData.name, round(ItemData.value_mm, 10))
            for ItemData in NativeSketch.dimensions
        )
        ExpectedConstraints = (
            "horizontal",
            "vertical",
            "horizontal",
            "vertical",
            *(("distance",) * len(ExpectedDims)),
        )
        DepthValue = (
            None
            if not FeatureObject.dimensions
            else FeatureObject.dimensions[0].value_mm
        )
        if (
            SketchObject.object_id != SketchObjectId
            or SketchObject.name != SketchName
            or FeatureObject.object_id != FeatureObjectId
            or FeatureObject.name != FeatureName
            or NativeSketch.object_id != SketchObjectId
            or NativeSketch.support_plane_id != 2
            or len(ProfileData) != 1
            or len(ProfileData[0].coordinates) != len(BoundsValue)
            or any(
                not math.isclose(ActualValue, ExpectedCoordinate, abs_tol=1.0e-10)
                for ActualValue, ExpectedCoordinate in zip(
                    ProfileData[0].coordinates, BoundsValue, strict=True
                )
            )
            or tuple(ItemData.kind for ItemData in NativeSketch.constraints)
            != ExpectedConstraints
            or ActualDims != ExpectedDims
            or NativeFeature.object_id != FeatureObjectId
            or NativeFeature.name != FeatureName
            or NativeFeature.profile_id != SketchObjectId
            or NativeFeature.kind not in FeatureKinds
            or NativeFeature.direction_code != EndCodes[0]
            or NativeFeature.termination_code != EndCodes[1]
            or (
                DepthValue is None
                and (NativeFeature.length_mm is not None or NativeFeature.depth_copies)
            )
            or (
                DepthValue is not None
                and (
                    NativeFeature.length_mm is None
                    or not math.isclose(
                        NativeFeature.length_mm,
                        DepthValue,
                        abs_tol=1.0e-10,
                    )
                    or len(NativeFeature.depth_copies) != len(ExpectedDepthSigns)
                    or not math.isclose(
                        NativeFeature.depth_copies[0].value_mm,
                        DepthValue,
                        abs_tol=1.0e-10,
                    )
                    or (
                        EndCodes == (0, 0)
                        and any(
                            CopyData.sign != CopySign
                            or not math.isclose(
                                CopyData.value_mm,
                                DepthValue * CopySign,
                                abs_tol=1.0e-10,
                            )
                            for CopyData, CopySign in zip(
                                NativeFeature.depth_copies,
                                ExpectedDepthSigns,
                                strict=True,
                            )
                        )
                    )
                )
            )
        ):
            return False
    NativeFeatureIds = tuple(
        ItemData.object_id
        for ItemData in ParsedModel.features
        if ItemData.object_id in {26, 32, 33, 40}
    )
    return NativeFeatureIds == (26, 32, 33, 40)


# this proves three- and four-stage cut chains, depths, directions, and dependency order
def HasCutChainProof(
    DocumentData: CadDocument,
    AuthoredObjs: tuple[_WriteObject, ...],
    ParsedModel: NativeModel,
) -> bool:
    FeatureCount = len(AuthoredObjs) // 2
    if (
        FeatureCount not in {3, 4}
        or len(AuthoredObjs) != FeatureCount * 2
        or len(ParsedModel.sketches) != FeatureCount
        or len(ParsedModel.operations) != FeatureCount
        or len(DocumentData.bodies) != 1
    ):
        return False
    SketchIds = (26, 33, 41, 48)[:FeatureCount]
    FeatureIds = (32, 40, 47, 54)[:FeatureCount]
    ExpectedData = tuple(
        (
            AuthoredObjs[FeatureIndex * 2],
            AuthoredObjs[FeatureIndex * 2 + 1],
            SketchIds[FeatureIndex],
            FeatureIds[FeatureIndex],
            f"Sketch{FeatureIndex + 1}",
            ("Boss-Extrude1" if FeatureIndex == 0 else f"Cut-Extrude{FeatureIndex}"),
            ({"boss", "join"} if FeatureIndex == 0 else {"cut"}),
        )
        for FeatureIndex in range(FeatureCount)
    )
    ExpectedDepthSigns = (1, 1, -1, -1, 1, 1)
    for NativeSketch, NativeFeature, ExpectedValue in zip(
        ParsedModel.sketches,
        ParsedModel.operations,
        ExpectedData,
        strict=True,
    ):
        (
            SketchObject,
            FeatureObject,
            SketchObjectId,
            FeatureObjectId,
            SketchName,
            FeatureName,
            FeatureKinds,
        ) = ExpectedValue
        BoundsValue = _write_rectangle_bounds(SketchObject)
        EndCodes = ExtrusionEditCodes(FeatureObject.payload)
        if (
            BoundsValue is None
            or EndCodes is None
            or len(FeatureObject.dimensions) != 1
        ):
            return False
        ProfileData = tuple(
            ItemData
            for ItemData in NativeSketch.profiles
            if ItemData.kind == "rectangle"
        )
        ExpectedDims = tuple(
            (ItemData.name, round(ItemData.value_mm, 10))
            for ItemData in SketchObject.dimensions
        )
        ActualDims = tuple(
            (ItemData.name, round(ItemData.value_mm, 10))
            for ItemData in NativeSketch.dimensions
        )
        ExpectedConstraints = (
            "horizontal",
            "vertical",
            "horizontal",
            "vertical",
            *(("distance",) * len(ExpectedDims)),
        )
        DepthValue = FeatureObject.dimensions[0].value_mm
        if (
            SketchObject.object_id != SketchObjectId
            or SketchObject.name != SketchName
            or FeatureObject.object_id != FeatureObjectId
            or FeatureObject.name != FeatureName
            or NativeSketch.object_id != SketchObjectId
            or NativeSketch.support_plane_id != 2
            or len(ProfileData) != 1
            or len(ProfileData[0].coordinates) != len(BoundsValue)
            or any(
                not math.isclose(ActualValue, ExpectedCoordinate, abs_tol=1.0e-10)
                for ActualValue, ExpectedCoordinate in zip(
                    ProfileData[0].coordinates,
                    BoundsValue,
                    strict=True,
                )
            )
            or tuple(ItemData.kind for ItemData in NativeSketch.constraints)
            != ExpectedConstraints
            or ActualDims != ExpectedDims
            or NativeFeature.object_id != FeatureObjectId
            or NativeFeature.name != FeatureName
            or NativeFeature.profile_id != SketchObjectId
            or NativeFeature.kind not in FeatureKinds
            or NativeFeature.direction_code != EndCodes[0]
            or NativeFeature.termination_code != EndCodes[1]
            or NativeFeature.length_mm is None
            or not math.isclose(
                NativeFeature.length_mm,
                DepthValue,
                abs_tol=1.0e-10,
            )
            or len(NativeFeature.depth_copies) != len(ExpectedDepthSigns)
            or any(
                CopyData.sign != CopySign
                or not math.isclose(
                    CopyData.value_mm,
                    DepthValue * CopySign,
                    abs_tol=1.0e-10,
                )
                for CopyData, CopySign in zip(
                    NativeFeature.depth_copies,
                    ExpectedDepthSigns,
                    strict=True,
                )
            )
        ):
            return False
    ExpectedIds = tuple(
        ObjectId
        for PairData in zip(SketchIds, FeatureIds, strict=True)
        for ObjectId in PairData
    )
    NativeFeatureIds = tuple(
        ItemData.object_id
        for ItemData in ParsedModel.features
        if ItemData.object_id in set(ExpectedIds)
    )
    return NativeFeatureIds == ExpectedIds


# this verifies rectangle dimensions match authored geometry
def HasRectDims(
    SketchObject: _WriteObject,
    BoundsValue: tuple[float, float, float, float] | None,
) -> bool:
    if BoundsValue is None:
        return False
    if not SketchObject.dimensions:
        return True
    if len(SketchObject.dimensions) != 2:
        return False
    MinimumX, MinimumY, MaximumX, MaximumY = BoundsValue
    ExpectedDims = sorted((MaximumX - MinimumX, MaximumY - MinimumY))
    ActualDims = sorted(ItemData.value_mm for ItemData in SketchObject.dimensions)
    return all(
        math.isfinite(ActualValue)
        and ActualValue > 0.0
        and math.isclose(ActualValue, ExpectedValue, abs_tol=1.0e-10)
        for ActualValue, ExpectedValue in zip(
            ActualDims,
            ExpectedDims,
            strict=True,
        )
    )


# circular dimensions must all agree with the authored geometric radius
def HasCircleDims(
    SketchObject: _WriteObject,
    CircleValue: tuple[float, float, float] | None,
) -> bool:
    if CircleValue is None:
        return False
    RadiusValue = CircleValue[2]
    return bool(SketchObject.dimensions) and all(
        math.isfinite(ItemData.value_mm)
        and ItemData.value_mm > 0.0
        and math.isclose(ItemData.value_mm, RadiusValue, abs_tol=1.0e-10)
        for ItemData in SketchObject.dimensions
    )


def _frame_vector(
    vector: tuple[float, float, float],
) -> tuple[float, float, float]:
    return (_clean(vector[0]), _clean(vector[1]), _clean(vector[2]))


def native_axis_bindings(model: NativeModel) -> frozenset[tuple[int, int, str]]:
    sketches = {sketch.object_id: sketch for sketch in model.sketches}
    result: set[tuple[int, int, str]] = set()
    for operation in model.operations:
        if operation.profile_id is None:
            continue
        sketch = sketches.get(operation.profile_id)
        subelement = operation_axis_subelement(operation, sketch)
        if subelement is None or sketch is None:
            continue
        result.add((operation.object_id, sketch.object_id, subelement))
    return frozenset(result)


def _document_axis_bindings(
    document: CadDocument, object_ids: Mapping[str, int]
) -> frozenset[tuple[int, int, str]] | None:
    features = {feature.name: feature for feature in document.feature_timeline}
    sketches = {sketch.name: sketch for sketch in document.sketches}
    result: set[tuple[int, int, str]] = set()
    for selection in document.selections:
        owner = str(selection.attributes.get("freecad_object", ""))
        role = str(selection.attributes.get("freecad_property", ""))
        if role != "ReferenceAxis" or len(selection.path) != 1:
            return None
        element = selection.path[0]
        feature = features.get(owner)
        sketch = sketches.get(str(element.entity_id))
        if feature is None or sketch is None or not element.subelement:
            return None
        feature_key = f"feature:{feature.id}"
        sketch_key = f"sketch:{sketch.id}"
        if feature_key not in object_ids or sketch_key not in object_ids:
            return None
        result.add(
            (object_ids[feature_key], object_ids[sketch_key], element.subelement)
        )
    return frozenset(result)


def decode_native_model(
    keywords: bytes,
    resolved: bytes,
    configuration_data: bytes = b"",
    *,
    configuration_id: int | None = None,
    resolved_stream: str = RESOLVED_FEATURES_STREAM,
    configuration_stream: str = "",
) -> NativeModel:
    configurations, xml_features = _parse_keywords(keywords)
    names = _parse_names(resolved)
    if resolved_stream == RESOLVED_FEATURES_STREAM:
        RebindIds(xml_features, names)
    classes = _parse_classes(resolved)
    scalars = _parse_scalars(resolved, names)
    record_by_id = _feature_records(xml_features, names)
    ordered_records = sorted(
        {record.offset: record for record in record_by_id.values()}.values(),
        key=lambda record: record.offset,
    )
    ends = {
        record.offset: (
            ordered_records[index + 1].offset
            if index + 1 < len(ordered_records)
            else len(resolved)
        )
        for index, record in enumerate(ordered_records)
    }
    scalar_owner = _scalar_owners(scalars, ordered_records, ends)
    native_features: list[NativeFeature] = []
    for feature in xml_features:
        record = record_by_id.get(feature.object_id)
        name = feature.name or (record.name if record is not None else "")
        if not name:
            name = f"{feature.kind or feature.xml_tag} {feature.object_id}"
        owned = scalar_owner.get(feature.object_id, ())
        dimensions = tuple(
            _bind_dimension(item, owned)
            for item in _semantic_dimensions(feature.kind, tuple(feature.dimensions))
        )
        native_end = ends.get(record.offset) if record is not None else None
        native_features.append(
            NativeFeature(
                object_id=feature.object_id,
                name=name,
                kind=feature.kind,
                xml_tag=feature.xml_tag,
                native_offset=record.offset if record else None,
                native_end=native_end,
                properties=dict(feature.properties),
                dimensions=dimensions,
                data=(
                    resolved[record.offset : native_end]
                    if record is not None and native_end is not None
                    else b""
                ),
                class_name=(
                    _record_class_name(classes, record.offset)
                    if record is not None
                    else ""
                ),
                native_stream=resolved_stream,
            )
        )
    feature_indexes = {
        feature.object_id: index for index, feature in enumerate(native_features)
    }
    for index, feature in enumerate(native_features):
        child_id = _integer_property(feature.properties.get("DissectableChildren"))
        child_scalars = scalar_owner.get(child_id or -1, ())
        if not child_scalars:
            continue
        rebound = tuple(
            (
                _bind_dimension(dimension, child_scalars)
                if dimension.native_offset is None
                else dimension
            )
            for dimension in feature.dimensions
        )
        native_features[index] = replace(feature, dimensions=rebound)
    planes = _decode_planes(resolved, native_features, native_stream=resolved_stream)
    plane_by_id = {plane.object_id: plane for plane in planes}
    principal_plane_frames = _principal_plane_frames(native_features)
    principal_plane_ids = frozenset(principal_plane_frames)
    author = sorted(
        (
            feature
            for feature in native_features
            if feature.native_offset is not None
            and not _is_origin_feature(feature)
            and feature.object_id not in principal_plane_ids
        ),
        key=lambda feature: feature.native_offset or 0,
    )
    unframed_planes = tuple(
        feature
        for feature in native_features
        if _is_plane_feature(feature)
        and feature.native_offset is not None
        and feature.object_id not in plane_by_id
    )
    unframed_plane_ids = frozenset(feature.object_id for feature in unframed_planes)
    sketches: list[NativeSketch] = []
    operations: list[NativeOperation] = []
    revolutions = {
        layout.feature_id: layout
        for layout in locate_features(resolved)
        if layout.is_revolution
    }
    native_index_by_id = feature_indexes
    latest_sketch: NativeSketch | None = None
    latest_operation: NativeOperation | None = None
    latest_plane_id = next(iter(principal_plane_frames), next(iter(plane_by_id), 0))
    latest_unframed_plane_id: int | None = None
    for feature in author:
        if _is_plane_feature(feature):
            if feature.object_id in plane_by_id:
                latest_plane_id = feature.object_id
                latest_unframed_plane_id = None
            else:
                latest_unframed_plane_id = feature.object_id
            continue
        if feature.kind.casefold() == "sketch":
            sketch_start = feature.native_offset or 0
            sketch_end = feature.native_end or len(resolved)
            reference = _sketch_plane_reference(
                resolved, classes, sketch_start, sketch_end
            )
            support, support_source, unframed_support = _support_plane_reference(
                resolved,
                sketch_start,
                sketch_end,
                reference,
                latest_plane_id,
                latest_unframed_plane_id,
                plane_by_id,
                unframed_plane_ids,
            )
            latest_sketch = _decode_sketch(
                resolved,
                feature,
                support,
                native_stream=resolved_stream,
                support_kind=_sketch_support_kind(
                    classes, reference, sketch_start, sketch_end
                ),
                support_plane=reference,
                support_source=support_source,
                unframed_support_plane_id=unframed_support,
            )
            native_index = native_index_by_id[feature.object_id]
            native_features[native_index] = replace(
                native_features[native_index], dimensions=latest_sketch.dimensions
            )
            sketches.append(latest_sketch)
            continue
        if feature.kind.casefold() == "extrusion":
            record = record_by_id.get(feature.object_id)
            if record is None:
                continue
            child = _integer_property(feature.properties.get("DissectableChildren"))
            profile_id = child or (latest_sketch.object_id if latest_sketch else None)
            dependencies = tuple(
                value
                for value in (
                    latest_operation.object_id if latest_operation else None,
                    profile_id,
                )
                if value is not None
            )
            family, operation_code, schema = _operation_fields(resolved, record)
            operation_start = feature.native_offset or 0
            operation_end = feature.native_end or len(resolved)
            end_spec = _end_spec(resolved, operation_start, operation_end, classes)
            operation = NativeOperation(
                object_id=feature.object_id,
                name=feature.name,
                kind=(
                    "join"
                    if operation_code == 0
                    else "cut" if operation_code == 2 else "native"
                ),
                profile_id=profile_id,
                dependencies=dependencies,
                native_offset=operation_start,
                native_end=_class_record_end(resolved, classes, operation_start)
                or operation_end,
                length_mm=_operation_dimension(feature.dimensions, "length"),
                radius_mm=None,
                family_code=family,
                operation_code=operation_code,
                schema_code=schema,
                direction_code=end_spec.direction_code if end_spec else None,
                termination_code=end_spec.termination_code if end_spec else None,
                selection_offsets=(),
                selected_local_ids=(),
                native_stream=resolved_stream,
                depth_copies=_depth_copies(
                    resolved,
                    _operation_dimension_offset(feature.dimensions, "length"),
                ),
                mirrored_direction_offset=(
                    end_spec.mirrored_direction_offset if end_spec else None
                ),
                mirrored_direction_code=(
                    end_spec.mirrored_direction_code if end_spec else None
                ),
            )
            operations.append(operation)
            latest_operation = operation
            continue
        feature_type = feature.kind.casefold()
        if feature_type in {"lpattern", "linearpattern"}:
            record = record_by_id.get(feature.object_id)
            CountValue = _operation_dimension(feature.dimensions, "instance_count")
            SpacingValue = _operation_dimension(feature.dimensions, "spacing")
            if (
                record is None
                or latest_operation is None
                or CountValue is None
                or CountValue != int(CountValue)
                or SpacingValue is None
            ):
                continue
            SelectionData = _operation_selections(
                resolved,
                feature.native_offset or 0,
                feature.native_end or len(resolved),
                feature,
                native_features,
            )
            FamilyValue, OperationValue, SchemaValue = _operation_fields(
                resolved,
                record,
            )
            DirectionOffset = (
                feature.native_offset + _LINEAR_PATTERN_DIRECTION_FLAG_RELATIVE_OFFSET
                if feature.native_offset is not None
                else -1
            )
            DirectionCode = (
                resolved[DirectionOffset]
                if 0 <= DirectionOffset < (feature.native_end or 0)
                and resolved[DirectionOffset] in {0, 1}
                else None
            )
            operation = NativeOperation(
                object_id=feature.object_id,
                name=feature.name,
                kind="linear_pattern",
                profile_id=None,
                dependencies=(latest_operation.object_id,),
                native_offset=feature.native_offset or 0,
                native_end=feature.native_end or len(resolved),
                length_mm=None,
                radius_mm=None,
                family_code=FamilyValue,
                operation_code=OperationValue,
                schema_code=SchemaValue,
                direction_code=DirectionCode,
                termination_code=None,
                selection_offsets=tuple(ItemData[0] for ItemData in SelectionData),
                selected_local_ids=tuple(ItemData[2] for ItemData in SelectionData),
                selection_kind="edge",
                mode="linear",
                native_stream=resolved_stream,
                selection_references=tuple(
                    (ItemData[1], ItemData[2]) for ItemData in SelectionData
                ),
                instance_count=int(CountValue),
                spacing_mm=SpacingValue,
            )
            operations.append(operation)
            latest_operation = operation
            continue
        if feature_type in {"cirpattern", "circularpattern"}:
            record = record_by_id.get(feature.object_id)
            CountValue = _operation_dimension(feature.dimensions, "instance_count")
            AngleValue = _operation_dimension(feature.dimensions, "angle")
            if (
                record is None
                or latest_operation is None
                or CountValue is None
                or CountValue != int(CountValue)
                or AngleValue is None
            ):
                continue
            SelectionData = _operation_selections(
                resolved,
                feature.native_offset or 0,
                feature.native_end or len(resolved),
                feature,
                native_features,
            )
            FamilyValue, OperationValue, SchemaValue = _operation_fields(
                resolved,
                record,
            )
            DirectionOffset = (
                feature.native_offset + _CIRCULAR_PATTERN_DIRECTION_FLAG_RELATIVE_OFFSET
                if feature.native_offset is not None
                else -1
            )
            DirectionCode = (
                resolved[DirectionOffset]
                if 0 <= DirectionOffset < (feature.native_end or 0)
                and resolved[DirectionOffset] in {0, 1}
                else None
            )
            operation = NativeOperation(
                object_id=feature.object_id,
                name=feature.name,
                kind="circular_pattern",
                profile_id=None,
                dependencies=(latest_operation.object_id,),
                native_offset=feature.native_offset or 0,
                native_end=feature.native_end or len(resolved),
                length_mm=None,
                radius_mm=None,
                family_code=FamilyValue,
                operation_code=OperationValue,
                schema_code=SchemaValue,
                direction_code=DirectionCode,
                termination_code=None,
                selection_offsets=tuple(ItemData[0] for ItemData in SelectionData),
                selected_local_ids=tuple(ItemData[2] for ItemData in SelectionData),
                angle_degrees=AngleValue,
                selection_kind="edge",
                mode="circular",
                native_stream=resolved_stream,
                selection_references=tuple(
                    (ItemData[1], ItemData[2]) for ItemData in SelectionData
                ),
                instance_count=int(CountValue),
            )
            operations.append(operation)
            latest_operation = operation
            continue
        if feature_type in _REVOLUTION_FEATURE_TYPES:
            record = record_by_id.get(feature.object_id)
            if record is None:
                continue
            profile_id = latest_sketch.object_id if latest_sketch else None
            dependencies = tuple(
                value
                for value in (
                    latest_operation.object_id if latest_operation else None,
                    profile_id,
                )
                if value is not None
            )
            family, operation_code, schema = _operation_fields(resolved, record)
            layout = revolutions.get(feature.object_id)
            axis_sketch = latest_sketch
            if layout is not None and layout.axis_kind == REVOLUTION_AXIS_SKETCH:
                axis_sketch = next(
                    (
                        item
                        for item in sketches
                        if item.object_id == layout.axis_feature_id
                    ),
                    None,
                )
            elif layout is not None:
                axis_sketch = None
            axis_marker = _revolution_axis_marker(axis_sketch)
            revolution_start = feature.native_offset or 0
            angle_offset = _operation_dimension_offset(feature.dimensions, "angle")
            operation = NativeOperation(
                object_id=feature.object_id,
                name=feature.name,
                kind=(
                    "revolve_cut"
                    if feature_type in {"cut-revolve", "revcut"}
                    else "revolve_join"
                ),
                profile_id=profile_id,
                dependencies=dependencies,
                native_offset=revolution_start,
                native_end=_class_record_end(resolved, classes, revolution_start)
                or feature.native_end
                or len(resolved),
                length_mm=None,
                radius_mm=None,
                family_code=family,
                operation_code=operation_code,
                schema_code=schema,
                direction_code=None,
                termination_code=None,
                selection_offsets=(),
                selected_local_ids=(),
                angle_degrees=_operation_dimension(feature.dimensions, "angle"),
                axis_marker_offset=axis_marker.offset if axis_marker else None,
                native_stream=resolved_stream,
                axis_source_kind=None if layout is None else layout.axis_kind,
                axis_source_id=None if layout is None else layout.axis_feature_id,
                axis_source_offset=None if layout is None else layout.axis_offset,
                end_spec_offset=None if layout is None else layout.end_spec_offset,
                angle_offset=angle_offset,
                angle_copies=_angle_copies(resolved, angle_offset),
            )
            operations.append(operation)
            latest_operation = operation
            continue
        if feature.class_name in _HOLE_CLASS_NAMES:
            record = record_by_id.get(feature.object_id)
            if record is None:
                continue
            child = _integer_property(feature.properties.get("DissectableChildren"))
            family, operation_code, schema = _operation_fields(resolved, record)
            dependencies = tuple(
                value
                for value in (
                    latest_operation.object_id if latest_operation else None,
                    child,
                )
                if value is not None
            )
            operation = NativeOperation(
                object_id=feature.object_id,
                name=feature.name,
                kind="hole",
                profile_id=child,
                dependencies=dependencies,
                native_offset=feature.native_offset or 0,
                native_end=feature.native_end or len(resolved),
                length_mm=_operation_dimension(feature.dimensions, "depth"),
                radius_mm=None,
                family_code=family,
                operation_code=operation_code,
                schema_code=schema,
                direction_code=None,
                termination_code=0,
                selection_offsets=(),
                selected_local_ids=(),
                selection_kind="face",
                native_stream=resolved_stream,
            )
            operations.append(operation)
            latest_operation = operation
            continue
        if feature_type == "dome":
            selections = _operation_selections_after_class(
                resolved,
                feature.native_offset or 0,
                feature.native_end or len(resolved),
                feature,
                native_features,
                "moCompFace_c",
            )
            height = _operation_dimension(feature.dimensions, "height")
            if height is None or not selections:
                continue
            producer_ids = tuple(
                dict.fromkeys(selection[1] for selection in selections)
            )
            dependencies = tuple(
                dict.fromkeys(
                    (
                        *((latest_operation.object_id,) if latest_operation else ()),
                        *producer_ids,
                    )
                )
            )
            operation = NativeOperation(
                object_id=feature.object_id,
                name=feature.name,
                kind="dome",
                profile_id=None,
                dependencies=dependencies,
                native_offset=feature.native_offset or 0,
                native_end=feature.native_end or len(resolved),
                length_mm=height,
                radius_mm=None,
                family_code=None,
                operation_code=None,
                schema_code=None,
                direction_code=None,
                termination_code=None,
                selection_offsets=tuple(item[0] for item in selections),
                selected_local_ids=tuple(item[2] for item in selections),
                selection_kind="face",
                native_stream=resolved_stream,
                selection_references=tuple((item[1], item[2]) for item in selections),
            )
            operations.append(operation)
            latest_operation = operation
            continue
        if feature_type in _MOVE_BODY_FEATURE_TYPES:
            selections = _operation_selections_after_class(
                resolved,
                feature.native_offset or 0,
                feature.native_end or len(resolved),
                feature,
                native_features,
                "moCompSolidBody_c",
            )
            translation = _native_translation(feature.dimensions)
            if translation is None or not selections:
                continue
            producer_ids = tuple(
                dict.fromkeys(selection[1] for selection in selections)
            )
            dependencies = tuple(
                dict.fromkeys(
                    (
                        *((latest_operation.object_id,) if latest_operation else ()),
                        *producer_ids,
                    )
                )
            )
            operation = NativeOperation(
                object_id=feature.object_id,
                name=feature.name,
                kind="move_body",
                profile_id=None,
                dependencies=dependencies,
                native_offset=feature.native_offset or 0,
                native_end=feature.native_end or len(resolved),
                length_mm=None,
                radius_mm=None,
                family_code=None,
                operation_code=None,
                schema_code=None,
                direction_code=None,
                termination_code=None,
                selection_offsets=tuple(item[0] for item in selections),
                selected_local_ids=tuple(item[2] for item in selections),
                selection_kind="body",
                native_stream=resolved_stream,
                selection_references=tuple((item[1], item[2]) for item in selections),
                translation_mm=translation,
            )
            operations.append(operation)
            latest_operation = operation
            continue
        if feature_type in _COMBINE_FEATURE_TYPES:
            selections = _operation_selections_after_class(
                resolved,
                feature.native_offset or 0,
                feature.native_end or len(resolved),
                feature,
                native_features,
                "moSolidRef_w",
            )
            if len(selections) < 2:
                continue
            producer_ids = tuple(
                dict.fromkeys(selection[1] for selection in selections)
            )
            dependencies = tuple(
                dict.fromkeys(
                    (
                        *((latest_operation.object_id,) if latest_operation else ()),
                        *producer_ids,
                    )
                )
            )
            operation = NativeOperation(
                object_id=feature.object_id,
                name=feature.name,
                kind="combine_join",
                profile_id=None,
                dependencies=dependencies,
                native_offset=feature.native_offset or 0,
                native_end=feature.native_end or len(resolved),
                length_mm=None,
                radius_mm=None,
                family_code=None,
                operation_code=0,
                schema_code=None,
                direction_code=None,
                termination_code=None,
                selection_offsets=tuple(item[0] for item in selections),
                selected_local_ids=tuple(item[2] for item in selections),
                selection_kind="body",
                mode="join",
                native_stream=resolved_stream,
                selection_references=tuple((item[1], item[2]) for item in selections),
            )
            operations.append(operation)
            latest_operation = operation
            continue
        if feature_type == "scale":
            factors = _native_scale_factors(
                resolved,
                feature.native_offset or 0,
                feature.native_end or len(resolved),
            )
            if factors is None or latest_operation is None:
                continue
            operation = NativeOperation(
                object_id=feature.object_id,
                name=feature.name,
                kind="scale",
                profile_id=None,
                dependencies=(latest_operation.object_id,),
                native_offset=feature.native_offset or 0,
                native_end=feature.native_end or len(resolved),
                length_mm=None,
                radius_mm=None,
                family_code=None,
                operation_code=None,
                schema_code=None,
                direction_code=None,
                termination_code=None,
                selection_offsets=(),
                selected_local_ids=(),
                native_stream=resolved_stream,
                scale_factors=factors,
            )
            operations.append(operation)
            latest_operation = operation
            continue
        if feature_type in {"fillet", "chamfer", "shell"}:
            selections = _operation_selections(
                resolved,
                feature.native_offset or 0,
                feature.native_end or len(resolved),
                feature,
                native_features,
            )
            producer_ids = tuple(
                dict.fromkeys(selection[1] for selection in selections)
            )
            dependencies = tuple(
                dict.fromkeys(
                    (
                        *((latest_operation.object_id,) if latest_operation else ()),
                        *producer_ids,
                    )
                )
            )
            record = record_by_id.get(feature.object_id)
            fields = (
                _operation_fields(resolved, record)
                if record is not None
                else (None, None, None)
            )
            dimension_kind = {
                "fillet": "radius",
                "chamfer": "distance",
                "shell": "thickness",
            }[feature_type]
            operation = NativeOperation(
                object_id=feature.object_id,
                name=feature.name,
                kind=feature_type,
                profile_id=None,
                dependencies=dependencies,
                native_offset=feature.native_offset or 0,
                native_end=feature.native_end or len(resolved),
                length_mm=(
                    _operation_dimension(feature.dimensions, dimension_kind)
                    if feature_type != "fillet"
                    else None
                ),
                radius_mm=(
                    _operation_dimension(feature.dimensions, dimension_kind)
                    if feature_type == "fillet"
                    else None
                ),
                family_code=fields[0],
                operation_code=fields[1],
                schema_code=fields[2],
                direction_code=None,
                termination_code=None,
                selection_offsets=tuple(selection[0] for selection in selections),
                selected_local_ids=tuple(selection[2] for selection in selections),
                selection_kind="face" if feature_type == "shell" else "edge",
                mode=(
                    "equal_distance"
                    if feature_type == "chamfer" and fields[0] == 1
                    else None
                ),
                native_stream=resolved_stream,
                selection_references=tuple(
                    (selection[1], selection[2]) for selection in selections
                ),
            )
            operations.append(operation)
            latest_operation = operation
            continue
        if feature_type in _SURFACE_EXTRUSION_FEATURE_TYPES:
            record = record_by_id.get(feature.object_id)
            if record is None:
                continue
            profile_id = latest_sketch.object_id if latest_sketch else None
            family, operation_code, schema = _operation_fields(resolved, record)
            end_spec = _end_spec(
                resolved,
                feature.native_offset or 0,
                feature.native_end or len(resolved),
                classes,
            )
            lengths = tuple(
                dimension.value_mm
                for dimension in feature.dimensions
                if dimension.kind in {"length", "second_length"}
            )
            operation = NativeOperation(
                object_id=feature.object_id,
                name=feature.name,
                kind="surface",
                profile_id=profile_id,
                dependencies=(profile_id,) if profile_id is not None else (),
                native_offset=feature.native_offset or 0,
                native_end=feature.native_end or len(resolved),
                length_mm=lengths[0] if lengths else None,
                radius_mm=None,
                family_code=family,
                operation_code=operation_code,
                schema_code=schema,
                direction_code=end_spec.direction_code if end_spec else None,
                termination_code=end_spec.termination_code if end_spec else None,
                selection_offsets=(),
                selected_local_ids=(),
                second_length_mm=lengths[1] if len(lengths) > 1 else None,
                native_stream=resolved_stream,
            )
            operations.append(operation)
    sketches_by_id = {sketch.object_id: sketch for sketch in sketches}
    operations = [
        _resolve_profile_operation(
            operation,
            sketches_by_id,
            resolved,
            native_features,
        )
        for operation in operations
    ]
    active_configuration_id = (
        configuration_id
        if configuration_id is not None
        else configurations[0].configuration_id
    )
    equations = _parse_native_equations(
        configuration_data,
        active_configuration_id,
        configuration_stream or f"Contents/Config-{active_configuration_id}",
    )
    diagnostics = []
    unresolved = [
        feature
        for feature in native_features
        if feature.native_offset is None
        and feature.object_id > 0
        and feature.object_id not in _KEYWORD_ONLY_OBJECT_IDS
    ]
    if unresolved:
        diagnostics.append(
            "native name records unavailable for "
            + ", ".join(f"{feature.object_id}:{feature.name}" for feature in unresolved)
        )
    if unframed_planes:
        diagnostics.append(
            "reference plane frames unavailable for "
            + ", ".join(
                f"{feature.object_id}:{feature.name}" for feature in unframed_planes
            )
        )
    dependent_sketches = tuple(
        sketch for sketch in sketches if sketch.unframed_support_plane_id is not None
    )
    if dependent_sketches:
        diagnostics.append(
            "sketch supports fall back to decoded planes for "
            + ", ".join(
                f"{sketch.object_id}:{sketch.name}"
                f"->{sketch.unframed_support_plane_id}:{sketch.support_plane_id}"
                for sketch in dependent_sketches
            )
        )
    return NativeModel(
        configurations=configurations,
        features=tuple(
            sorted(
                native_features,
                key=_native_feature_sort_key,
            )
        ),
        planes=tuple(planes),
        sketches=tuple(sketches),
        operations=tuple(operations),
        names=names,
        classes=classes,
        scalars=scalars,
        diagnostics=tuple(diagnostics),
        equations=equations,
        active_configuration_id=active_configuration_id,
        bounding_box=_bounding_box(resolved, classes),
    )


# vendor feature trees may use stable semantic ids beyond envelope tree counters
def RebindIds(
    FeaturesList: list[_XmlFeature], NamesList: tuple[NativeName, ...]
) -> None:
    KnownIds = frozenset(
        RecordData.object_id
        for RecordData in NamesList
        if RecordData.object_id is not None
    )
    RecordsByName: dict[str, list[NativeName]] = {}
    for RecordData in NamesList:
        if RecordData.object_id is None:
            continue
        RecordsByName.setdefault(RecordData.name, []).append(RecordData)
    for FeatureData in FeaturesList:
        if FeatureData.object_id in KnownIds:
            continue
        MatchesList = RecordsByName.get(FeatureData.name, ())
        MatchingIds = {
            RecordData.object_id
            for RecordData in MatchesList
            if RecordData.object_id is not None
        }
        if len(MatchingIds) == 1:
            FeatureData.object_id = MatchingIds.pop()
        elif FeatureData.kind.casefold() == "extrusion" and any(
            RecordData.object_id == 32 and RecordData.name == "Boss-Extrude1"
            for RecordData in NamesList
        ):
            FeatureData.object_id = 32
        else:
            continue
        FeatureData.properties["id"] = str(FeatureData.object_id)


def _native_feature_sort_key(feature: NativeFeature) -> tuple[int, int]:
    if feature.native_offset is not None and feature.object_id <= 25:
        return 0, feature.native_offset
    if feature.object_id in _KEYWORD_ONLY_OBJECT_IDS:
        return 1, feature.object_id
    if feature.native_offset is not None:
        return 2, feature.native_offset
    return 3, feature.object_id


def _parse_keywords(
    data: bytes,
) -> tuple[tuple[NativeConfiguration, ...], list[_XmlFeature]]:
    root = _parse_xml(data)
    configurations: list[NativeConfiguration] = []
    features: list[_XmlFeature] = []
    for element in root.iter():
        tag = element.tag.rsplit("}", 1)[-1]
        if tag == "Configuration":
            configurations.append(
                NativeConfiguration(
                    object_id=int(element.attrib.get("id", "0")),
                    name=element.attrib.get("Name", "Default"),
                    configuration_id=int(element.attrib.get("id", "0")),
                    properties=dict(element.attrib),
                )
            )
            continue
        if element is root or tag == "Dimension":
            continue
        raw_id = element.attrib.get("id")
        if not raw_id:
            continue
        try:
            object_id = int(raw_id)
        except ValueError:
            continue
        kind = tag if tag != "Feature" else element.attrib.get("Type", "Feature")
        if kind.casefold() in PLANE_FEATURE_TYPES:
            kind = CANONICAL_PLANE_FEATURE_TYPE.title()
        name = element.attrib.get("Name", "")
        dimensions = [
            _parse_dimension(child.attrib.get("Name", ""), child.text or "")
            for child in element
            if child.tag.rsplit("}", 1)[-1] == "Dimension"
        ]
        features.append(
            _XmlFeature(
                object_id=object_id,
                name=name,
                kind=kind,
                xml_tag=tag,
                properties=dict(element.attrib),
                dimensions=dimensions,
            )
        )
    if not features:
        raise SldprtFormatError("keyword history does not contain feature nodes")
    if not configurations:
        configurations.append(NativeConfiguration(0, "Default", 0, {}))
    return tuple(configurations), features


def _parse_xml(data: bytes) -> ET.Element:
    start = data.find(b"<?xml")
    if start < 0:
        start = data.find(b"<")
    if start < 0:
        raise SldprtFormatError("XML stream contains no document element")
    try:
        return ET.fromstring(data[start:])
    except ET.ParseError as exc:
        raise SldprtFormatError(f"invalid XML metadata stream: {exc}") from exc


def _parse_dimension(name: str, text: str) -> NativeDimension:
    match = _NUMBER.search(text)
    if match is None:
        raise SldprtFormatError(f"dimension {name!r} has no numeric value")
    kind = (
        "diameter"
        if "<MOD-DIAM>" in text
        else (
            "radius"
            if text.lstrip().startswith("R")
            else "angle" if "°" in text or "deg" in text.casefold() else "length"
        )
    )
    return NativeDimension(name, float(match.group()), kind, text)


def _name_marker(data: bytes) -> bytes:
    for offset in _find_all(data, CLASS_MARKER):
        if offset + 6 > len(data):
            continue
        length = struct.unpack_from("<H", data, offset + 4)[0]
        end = offset + 6 + length
        if not 1 <= length <= 128 or end + 5 > len(data):
            continue
        class_name = data[offset + 6 : end]
        if not all(0x21 <= byte <= 0x7E for byte in class_name):
            continue
        token = struct.unpack_from("<H", data, end)[0]
        if (
            token & 0x8000
            and token != 0xFFFF
            and data[end + 2 : end + 5] == b"\xff\xfe\xff"
        ):
            return struct.pack("<H", token) + b"\xff\xfe\xff"
    return bytes.fromhex("0480fffeff")


def _parse_names(data: bytes) -> tuple[NativeName, ...]:
    marker = _name_marker(data)
    names: list[NativeName] = []
    for offset in _find_all(data, marker):
        if offset + len(marker) + 1 > len(data):
            continue
        units = data[offset + len(marker)]
        text_start = offset + len(marker) + 1
        text_end = text_start + units * 2
        if not 1 <= units <= 128 or text_end + 12 > len(data):
            continue
        try:
            name = data[text_start:text_end].decode("utf-16le")
        except UnicodeDecodeError:
            continue
        if not name or any(not character.isprintable() for character in name):
            continue
        raw_id = struct.unpack_from("<I", data, text_end + 8)[0]
        names.append(
            NativeName(
                offset=offset,
                text_end=text_end,
                name=name,
                object_id=None if raw_id == 0xFFFFFFFF else raw_id,
                class_token=struct.unpack_from("<H", marker)[0],
            )
        )
    return tuple(names)


def _parse_classes(data: bytes) -> tuple[NativeClass, ...]:
    classes: list[NativeClass] = []
    for offset in _find_all(data, CLASS_MARKER):
        if offset + 6 > len(data):
            continue
        length = struct.unpack_from("<H", data, offset + 4)[0]
        end = offset + 6 + length
        if not 1 <= length <= 128 or end > len(data):
            continue
        value = data[offset + 6 : end]
        if not all(chr(byte).isalnum() or byte in b"_-" for byte in value):
            continue
        classes.append(NativeClass(offset, value.decode("ascii")))
    return tuple(classes)


def _record_class_name(classes: tuple[NativeClass, ...], record_offset: int) -> str:
    owner = _record_class(classes, record_offset)
    return "" if owner is None else owner.name


def _parse_native_equations(
    data: bytes, configuration_id: int, native_stream: str
) -> tuple[NativeEquation, ...]:
    class_names = {item.name for item in _parse_classes(data)}
    if not {"moRelMgr_c", "moRelation_c"} <= class_names:
        return ()
    equations: list[NativeEquation] = []
    seen: set[str] = set()
    for offset in _find_all(data, SERIALIZED_STRING_MARKER):
        length_offset = offset + len(SERIALIZED_STRING_MARKER)
        if length_offset >= len(data):
            continue
        units = data[length_offset]
        text_start = length_offset + 1
        text_end = text_start + units * 2
        if units < 3 or text_end > len(data):
            continue
        try:
            source = data[text_start:text_end].decode("utf-16le")
        except UnicodeDecodeError:
            continue
        match = _EQUATION.fullmatch(source)
        if (
            match is None
            or source in seen
            or not all(character.isprintable() for character in source)
        ):
            continue
        seen.add(source)
        lhs, rhs = match.groups()
        equations.append(
            NativeEquation(
                source=source,
                lhs=lhs,
                rhs=rhs,
                references=tuple(dict.fromkeys(_EQUATION_REFERENCE.findall(rhs))),
                native_offset=offset,
                native_length=text_end - offset,
                configuration_id=configuration_id,
                native_stream=native_stream,
            )
        )
    return tuple(equations)


def _parse_scalars(
    data: bytes, names: tuple[NativeName, ...]
) -> tuple[NativeScalar, ...]:
    scalars: list[NativeScalar] = []
    for name in names:
        value_offset = dimension_scalar_value_offset(
            data,
            name.text_end,
            len(data),
            trailing_bytes=7,
        )
        if value_offset is None:
            continue
        value = struct.unpack_from("<d", data, value_offset)[0]
        if not math.isfinite(value):
            continue
        trailer = value_offset + 8
        raw_id = struct.unpack_from("<I", data, trailer + 3)[0]
        role, operands = _scalar_trailer(data, trailer)
        scalars.append(
            NativeScalar(
                name=name.name,
                name_offset=name.offset,
                value_offset=value_offset,
                value=value,
                object_id=None if raw_id == 0xFFFFFFFF else raw_id,
                role=role,
                operands=operands,
            )
        )
    return tuple(scalars)


def _scalar_trailer(data: bytes, trailer: int) -> tuple[str, tuple[NativeOperand, ...]]:
    fixed = (
        data[trailer : trailer + 3] == b"\0\0\0"
        and data[trailer + 7 : trailer + 21] == b"\0" * 14
        and data[trailer + 24 : trailer + 29] == b"\0\0\0\x02\0"
    )
    compact = (
        data[trailer : trailer + 3] == b"\0\0\0"
        and data[trailer + 7 : trailer + 21] == b"\0" * 14
        and data[trailer + 21 : trailer + 27] == b"\x01\0\0\0\x02\0"
        and data[trailer + 28 : trailer + 35] == b"\0" * 7
    )
    legacy = (
        data[trailer : trailer + 3] == b"\0\0\0"
        and data[trailer + 7 : trailer + 24] == b"\0" * 17
        and data[trailer + 24 : trailer + 30] == b"\x0f\0\0\0\x02\0"
    )
    if compact:
        role_offset, cells, size = trailer + 27, (trailer + 35, trailer + 43), 8
    elif fixed:
        role_offset, cells, size = trailer + 29, (trailer + 35, trailer + 47), 12
    elif legacy:
        role_offset, cells, size = trailer + 30, (trailer + 36, trailer + 48), 12
    else:
        return "native", ()
    role_byte = data[role_offset] if role_offset < len(data) else 255
    role = "driving" if role_byte == 0 else "display" if role_byte == 1 else "native"
    operands: list[NativeOperand] = []
    for offset in cells:
        cell = data[offset : offset + size]
        if len(cell) != size or cell[4:8] != b"\xff" * 4:
            continue
        if size == 12 and cell[8:12] != b"\0" * 4:
            continue
        kind = struct.unpack_from("<H", cell)[0]
        if kind in {0, 0xFFFF}:
            continue
        operands.append(
            NativeOperand(offset, kind, struct.unpack_from("<H", cell, 2)[0])
        )
    return role, tuple(operands)


def _scalar_owners(
    scalars: tuple[NativeScalar, ...],
    records: list[NativeName],
    ends: dict[int, int],
) -> dict[int, tuple[NativeScalar, ...]]:
    result: dict[int, list[NativeScalar]] = {}
    for record in records:
        if record.object_id is None:
            continue
        end = ends[record.offset]
        result[record.object_id] = [
            scalar for scalar in scalars if record.offset < scalar.value_offset < end
        ]
    return {key: tuple(value) for key, value in result.items()}


def _bind_dimension(
    dimension: NativeDimension, scalars: tuple[NativeScalar, ...]
) -> NativeDimension:
    target = (
        dimension.value_mm
        if dimension.kind == "instance_count"
        else (
            math.radians(dimension.value_mm)
            if dimension.kind == "angle"
            else dimension.value_mm / 1000.0
        )
    )
    value_matches = [
        scalar
        for scalar in scalars
        if math.isclose(scalar.value, target, rel_tol=1e-9, abs_tol=1e-12)
    ]
    named_matches = [
        scalar for scalar in value_matches if scalar.name == dimension.name
    ]
    matches = named_matches
    if not matches and len(value_matches) == 1:
        matches = value_matches
    if not matches:
        return dimension
    scalar = next(
        (candidate for candidate in matches if candidate.role == "driving"), matches[-1]
    )
    return NativeDimension(
        name=dimension.name,
        value_mm=dimension.value_mm,
        kind=dimension.kind,
        source_text=dimension.source_text,
        native_value=scalar.value,
        native_offset=scalar.value_offset,
        native_role=scalar.role,
        operands=scalar.operands,
    )


def _feature_records(
    features: list[_XmlFeature], names: tuple[NativeName, ...]
) -> dict[int, NativeName]:
    records: dict[int, list[NativeName]] = {}
    for record in names:
        if record.object_id is not None:
            records.setdefault(record.object_id, []).append(record)
    result: dict[int, NativeName] = {}
    for feature in features:
        candidates = records.get(feature.object_id, ())
        if not candidates:
            continue
        exact = tuple(record for record in candidates if record.name == feature.name)
        selected = min(exact or tuple(candidates), key=lambda record: record.offset)
        result[feature.object_id] = selected
    return result


def _semantic_dimensions(
    feature_kind: str, dimensions: tuple[NativeDimension, ...]
) -> tuple[NativeDimension, ...]:
    feature_type = feature_kind.casefold()
    if feature_type in _SURFACE_EXTRUSION_FEATURE_TYPES:
        return tuple(
            replace(
                dimension,
                kind=(
                    "length"
                    if dimension.name.casefold() == "d1"
                    else (
                        "second_length"
                        if dimension.name.casefold() == "d2"
                        else dimension.kind
                    )
                ),
            )
            for dimension in dimensions
        )
    if feature_type == "chamfer":
        return tuple(
            replace(
                dimension,
                kind=(
                    "distance"
                    if dimension.name.casefold() == "d1"
                    else (
                        "angle" if dimension.name.casefold() == "d2" else dimension.kind
                    )
                ),
            )
            for dimension in dimensions
        )
    if feature_type in {"lpattern", "linearpattern"}:
        return tuple(
            replace(
                dimension,
                kind=(
                    "instance_count"
                    if dimension.name.casefold() == "d1"
                    else (
                        "spacing"
                        if dimension.name.casefold() == "d3"
                        else dimension.kind
                    )
                ),
            )
            for dimension in dimensions
        )
    if feature_type in {"cirpattern", "circularpattern"}:
        return tuple(
            replace(
                dimension,
                kind=(
                    "instance_count"
                    if dimension.name.casefold() == "d1"
                    else (
                        "angle" if dimension.name.casefold() == "d3" else dimension.kind
                    )
                ),
            )
            for dimension in dimensions
        )
    semantic = {
        "extrusion": "length",
        "fillet": "radius",
        "cut": "depth",
        "revolve": "angle",
        "revolution": "angle",
        "cut-revolve": "angle",
        "revcut": "angle",
        "shell": "thickness",
        "dome": "height",
        "plane": "offset",
    }.get(feature_type)
    if semantic is None or not dimensions:
        return dimensions
    selected = _primary_dimension(dimensions)
    return tuple(
        replace(dimension, kind=semantic) if index == selected else dimension
        for index, dimension in enumerate(dimensions)
    )


def _primary_dimension(dimensions: tuple[NativeDimension, ...]) -> int:
    return min(
        range(len(dimensions)),
        key=lambda index: (
            dimensions[index].native_role == "display",
            dimensions[index].native_offset is None,
            (
                dimensions[index].native_offset
                if dimensions[index].native_offset is not None
                else index
            ),
            index,
        ),
    )


def _decode_planes(
    data: bytes,
    features: list[NativeFeature],
    *,
    native_stream: str = RESOLVED_FEATURES_STREAM,
) -> list[NativePlane]:
    principal = _principal_plane_frames(features)
    plane_ids = frozenset(principal) | frozenset(
        feature.object_id for feature in features if _is_plane_feature(feature)
    )
    planes: list[NativePlane] = []
    for feature in features:
        if feature.object_id in principal:
            origin, normal, u_axis = principal[feature.object_id]
            planes.append(
                NativePlane(
                    feature.object_id,
                    feature.name,
                    origin,
                    normal,
                    u_axis,
                    _cross(normal, u_axis),
                    feature.native_offset,
                    None,
                    True,
                    (),
                    native_stream,
                )
            )
            continue
        if not _is_plane_feature(feature):
            continue
        start = feature.native_offset or 0
        end = feature.native_end or len(data)
        frame = _matrix_frame(data, start, end) or _minimal_frame(data, start, end)
        if frame is None:
            continue
        offset, length, origin, normal, u_axis, v_axis = frame
        planes.append(
            NativePlane(
                feature.object_id,
                feature.name,
                origin,
                normal,
                u_axis,
                v_axis,
                offset,
                length,
                False,
                _reference_plane_ids(data, start, end, feature.object_id, plane_ids),
                native_stream,
            )
        )
    return planes


def _principal_plane_frames(
    features: list[NativeFeature],
) -> dict[
    int,
    tuple[
        tuple[float, float, float],
        tuple[float, float, float],
        tuple[float, float, float],
    ],
]:
    ordered = tuple(
        feature
        for _, feature in sorted(
            enumerate(features),
            key=lambda item: (
                item[1].native_offset is None,
                (
                    item[1].native_offset
                    if item[1].native_offset is not None
                    else item[0]
                ),
                item[0],
            ),
        )
    )
    origin_index = next(
        (index for index, feature in enumerate(ordered) if _is_origin_feature(feature)),
        None,
    )
    if origin_index is None:
        return {}
    planes = tuple(
        feature for feature in ordered[:origin_index] if _is_plane_feature(feature)
    )
    frames = (
        ((0.0, 0.0, 0.0), (0.0, 0.0, 1.0), (1.0, 0.0, 0.0)),
        ((0.0, 0.0, 0.0), (0.0, 1.0, 0.0), (1.0, 0.0, 0.0)),
        ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 0.0, -1.0)),
    )
    return {feature.object_id: frame for feature, frame in zip(planes[:3], frames)}


def _is_origin_feature(feature: NativeFeature) -> bool:
    return feature.properties.get("Type", "").casefold() == "origin"


def _is_plane_feature(feature: NativeFeature) -> bool:
    return feature.kind.casefold() in PLANE_FEATURE_TYPES


def _matrix_frame(data: bytes, start: int, end: int) -> (
    tuple[
        int,
        int,
        tuple[float, float, float],
        tuple[float, float, float],
        tuple[float, float, float],
        tuple[float, float, float],
    ]
    | None
):
    for offset in range(start, max(start, end - 121 + 1)):
        if data[offset + 48] != 1:
            continue
        origin = struct.unpack_from("<3d", data, offset)
        normal = struct.unpack_from("<3d", data, offset + 24)
        rows = (
            struct.unpack_from("<3d", data, offset + 49),
            struct.unpack_from("<3d", data, offset + 73),
            struct.unpack_from("<3d", data, offset + 97),
        )
        u_axis = tuple(row[0] for row in rows)
        v_axis = tuple(row[1] for row in rows)
        matrix_normal = tuple(row[2] for row in rows)
        values = origin + normal + u_axis + v_axis + matrix_normal
        if not all(math.isfinite(value) and abs(value) <= 10.0 for value in values):
            continue
        if not all(
            math.isclose(_norm(vector), 1.0, abs_tol=1e-9)
            for vector in (normal, u_axis, v_axis, matrix_normal)
        ):
            continue
        if any(
            abs(_dot(left, right)) > 1e-9
            for left, right in (
                (u_axis, v_axis),
                (u_axis, matrix_normal),
                (v_axis, matrix_normal),
            )
        ):
            continue
        if _dot(normal, matrix_normal) < 1.0 - 1e-9:
            continue
        return (
            offset,
            121,
            tuple(_clean(value * 1000.0) for value in origin),
            tuple(_clean(value) for value in normal),
            tuple(_clean(value) for value in u_axis),
            tuple(_clean(value) for value in v_axis),
        )
    return None


def _minimal_frame(data: bytes, start: int, end: int) -> (
    tuple[
        int,
        int,
        tuple[float, float, float],
        tuple[float, float, float],
        tuple[float, float, float],
        tuple[float, float, float],
    ]
    | None
):
    for offset in range(start, max(start, end - 81 + 1)):
        origin = struct.unpack_from("<3d", data, offset)
        normal = struct.unpack_from("<3d", data, offset + 24)
        if normal != (0.0, 0.0, 1.0):
            continue
        if data[offset + 48 : offset + 56] != b"\0" * 8 or data[offset + 56] not in {
            0x00,
            0x80,
        }:
            continue
        tail = struct.unpack_from("<3d", data, offset + 57)
        if tail[0] != 0.0:
            continue
        if (
            struct.pack("<d", tail[1]) != struct.pack("<d", -origin[2])
            or tail[2] != 1.0
        ):
            continue
        return (
            offset,
            81,
            tuple(_clean(value * 1000.0) for value in origin),
            normal,
            (1.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
        )
    return None


def _support_plane_reference(
    data: bytes,
    start: int,
    end: int,
    reference: NativeSketchPlane | None,
    framed_fallback: int,
    unframed_fallback: int | None,
    planes: dict[int, NativePlane],
    unframed_plane_ids: frozenset[int],
) -> tuple[int, str, int | None]:
    if reference is not None and reference.plane_object_id in planes:
        return reference.plane_object_id, REFERENCE_SUPPORT_SOURCE, None
    sources = _component_plane_sources(data, start, end)
    framed = [source for source in sources if source in planes]
    if framed:
        return framed[-1], REFERENCE_SUPPORT_SOURCE, None
    unframed = [source for source in sources if source in unframed_plane_ids]
    if unframed:
        return framed_fallback, UNRESOLVED_SUPPORT_SOURCE, unframed[-1]
    if unframed_fallback is not None:
        return framed_fallback, UNRESOLVED_SUPPORT_SOURCE, unframed_fallback
    return framed_fallback, STREAM_ORDER_SUPPORT_SOURCE, None


def _sketch_plane_reference(
    data: bytes,
    classes: tuple[NativeClass, ...],
    start: int,
    end: int,
) -> NativeSketchPlane | None:
    for record in classes:
        if record.name != SKETCH_CHAIN_CLASS or not start <= record.offset < end:
            continue
        anchored = _read_sketch_plane_reference(
            data, record.offset + _SKETCH_PLANE_ID_RELATIVE, end
        )
        if anchored is not None:
            return anchored
    for offset in _find_all(data, _SKETCH_PLANE_REFERENCE_PREFIX, start, end):
        scanned = _read_sketch_plane_reference(
            data, offset + len(_SKETCH_PLANE_REFERENCE_PREFIX), end
        )
        if scanned is not None:
            return scanned
    return None


def _read_sketch_plane_reference(
    data: bytes, offset: int, end: int
) -> NativeSketchPlane | None:
    if offset < 0 or offset + _SKETCH_PLANE_BASIS_DELTA > end:
        return None
    plane_object_id = struct.unpack_from("<I", data, offset)[0]
    if plane_object_id not in _PRINCIPAL_PLANE_OBJECT_IDS:
        return None
    if data[offset + 4 : offset + 8] != _SKETCH_PLANE_REFERENCE_TAG:
        return None
    if data[offset + 8 : offset + _SKETCH_PLANE_AXIS_DELTA] != b"\0\0":
        return None
    axis_code = struct.unpack_from("<I", data, offset + _SKETCH_PLANE_AXIS_DELTA)[0]
    if axis_code != _SKETCH_PLANE_AXIS_COMPLEMENT - plane_object_id:
        return None
    flag = data[offset + _SKETCH_PLANE_BASIS_FLAG_DELTA]
    basis_offset = offset + _SKETCH_PLANE_BASIS_DELTA
    if flag == 0:
        return NativeSketchPlane(
            offset,
            plane_object_id,
            axis_code,
            _IDENTITY_BASIS[0],
            _IDENTITY_BASIS[1],
            _IDENTITY_BASIS[2],
            None,
        )
    if flag != 1 or basis_offset + _SKETCH_PLANE_BASIS_BYTES > end:
        return None
    rows = struct.unpack_from("<9d", data, basis_offset)
    if not all(math.isfinite(value) for value in rows):
        return None
    u_axis = (rows[0], rows[3], rows[6])
    v_axis = (rows[1], rows[4], rows[7])
    normal = (rows[2], rows[5], rows[8])
    if not _orthonormal((u_axis, v_axis, normal)):
        return None
    return NativeSketchPlane(
        offset,
        plane_object_id,
        axis_code,
        tuple(_clean(value) for value in u_axis),
        tuple(_clean(value) for value in v_axis),
        tuple(_clean(value) for value in normal),
        basis_offset,
    )


def _sketch_support_kind(
    classes: tuple[NativeClass, ...],
    reference: NativeSketchPlane | None,
    start: int,
    end: int,
) -> str:
    if reference is not None:
        return PLANE_SUPPORT_KIND
    if any(
        record.name == _FACE_SUPPORT_CLASS and start <= record.offset < end
        for record in classes
    ):
        return FACE_SUPPORT_KIND
    return DERIVED_SUPPORT_KIND


def _bounding_box(
    data: bytes, classes: tuple[NativeClass, ...]
) -> NativeBoundingBox | None:
    for record in classes:
        if record.name != _BOUNDING_BOX_CLASS:
            continue
        offset = record.offset + _BOUNDING_BOX_RELATIVE
        if offset + 32 > len(data):
            continue
        values = struct.unpack_from("<4d", data, offset)
        if not all(math.isfinite(value) for value in values) or values[3] < 0.0:
            continue
        return NativeBoundingBox(
            offset,
            tuple(_clean(value * _MILLIMETRES) for value in values[:3]),
            _clean(values[3] * _MILLIMETRES),
        )
    return None


def _depth_copies(data: bytes, offset: int | None) -> tuple[NativeDepthCopy, ...]:
    if offset is None:
        return ()
    result: list[NativeDepthCopy] = []
    for delta, sign in zip(DEPTH_COPY_DELTAS, DEPTH_COPY_SIGNS, strict=True):
        target = offset + delta
        if target < 0 or target + 8 > len(data):
            continue
        value = struct.unpack_from("<d", data, target)[0]
        if not math.isfinite(value):
            continue
        result.append(NativeDepthCopy(target, sign, value * _MILLIMETRES))
    return tuple(result)


def _angle_copies(data: bytes, offset: int | None) -> tuple[NativeDepthCopy, ...]:
    if offset is None:
        return ()
    result: list[NativeDepthCopy] = []
    for delta in ANGLE_COPY_DELTAS:
        target = offset + delta
        if target < 0 or target + 8 > len(data):
            continue
        value = struct.unpack_from("<d", data, target)[0]
        if not math.isfinite(value):
            continue
        result.append(NativeDepthCopy(target, 1, value * _RADIANS_TO_DEGREES))
    return tuple(result)


def _mirrored_direction(
    data: bytes, classes: tuple[NativeClass, ...], start: int, end: int
) -> tuple[int | None, int | None]:
    for record in classes:
        if record.name != FROM_END_SPEC_CLASS or not start <= record.offset < end:
            continue
        offset = record.offset + FROM_REVERSE_RELATIVE
        if offset < len(data):
            return offset, data[offset]
    return None, None


def _record_class(
    classes: tuple[NativeClass, ...], record_offset: int
) -> NativeClass | None:
    return next(
        (
            item
            for item in classes
            if item.offset + 6 + len(item.name.encode("ascii")) == record_offset
        ),
        None,
    )


def _class_record_end(
    data: bytes, classes: tuple[NativeClass, ...], record_offset: int
) -> int | None:
    owner = _record_class(classes, record_offset)
    if owner is None:
        return None
    return next(
        (item.offset for item in classes if item.offset > owner.offset), len(data)
    )


def _reference_plane_ids(
    data: bytes,
    start: int,
    end: int,
    object_id: int,
    plane_ids: frozenset[int],
) -> tuple[int, ...]:
    result: list[int] = []
    marker = b"\0" * 6 + struct.pack("<I", 1)
    for offset in _find_all(data, marker, start, end):
        source_offset = offset + len(marker)
        if (
            source_offset + 6 > end
            or data[source_offset + 4 : source_offset + 6] != b"\0\x05"
        ):
            continue
        source = struct.unpack_from("<I", data, source_offset)[0]
        if source in plane_ids and source != object_id:
            result.append(source)
    return tuple(dict.fromkeys(result))


def _component_plane_sources(data: bytes, start: int, end: int) -> list[int]:
    sources: list[int] = []
    for offset in range(start, max(start, end - 67 + 1) + 1):
        block = data[offset : offset + 67]
        identity = struct.unpack_from("<I", block)[0]
        legacy = struct.unpack_from("<H", block, 10)[0]
        trailer = block[47:63]
        common = (
            block[12:39] == b"\0" * 27
            and struct.unpack_from("<d", block, 39)[0] == 1.0
            and trailer[:3] == b"\0" * 3
            and trailer[3] in {2, 3, 4}
            and trailer[4:7] == b"\0" * 3
            and trailer[7] in {0xF9, 0xFB, 0xFF}
            and trailer[8:11] == b"\xff" * 3
            and trailer[11:15] == b"\0" * 4
        )
        if not common:
            continue
        if identity and block[4:10] == b"\0" * 6 and legacy:
            sources.append(legacy)
        elif identity and block[8:12] == b"\0\0\x03\0":
            sources.append(identity)
    for offset in range(start, max(start, end - 138 + 1) + 1):
        block = data[offset : offset + 138]
        source = struct.unpack_from("<I", block)[0]
        if not source or block[8:14] != b"\0" * 6 or block[14] != 1:
            continue
        if block[122:126] != struct.pack("<I", 4) or block[126:130] != b"\xff" * 4:
            continue
        basis = [
            struct.unpack_from("<3d", block, 15 + index * 24) for index in range(3)
        ]
        if not all(math.isclose(_norm(vector), 1.0, abs_tol=1e-9) for vector in basis):
            continue
        sources.append(source)
    return list(dict.fromkeys(sources))


def _decode_sketch(
    data: bytes,
    feature: NativeFeature,
    support_plane_id: int,
    *,
    native_stream: str = RESOLVED_FEATURES_STREAM,
    support_kind: str = PLANE_SUPPORT_KIND,
    support_plane: NativeSketchPlane | None = None,
    support_source: str = REFERENCE_SUPPORT_SOURCE,
    unframed_support_plane_id: int | None = None,
) -> NativeSketch:
    start = feature.native_offset or 0
    end = feature.native_end or len(data)
    markers = list(_parse_markers(data, start, end))
    profiles, profile_markers, dimensions = _profiles(markers, feature.dimensions)
    normalized_markers = tuple(
        NativeMarker(
            offset=marker.offset,
            length=marker.length,
            prefix=marker.prefix,
            native_kind=marker.native_kind,
            locus=marker.locus,
            profile_role=marker.profile_role,
            state=marker.state,
            object_index=marker.object_index,
            local_id=marker.local_id,
            coordinates_mm=marker.coordinates_mm,
            endpoint_indices=marker.endpoint_indices,
            construction=(
                marker.construction
                or marker.offset not in profile_markers
                and marker.semantic != "native"
            ),
            semantic=marker.semantic,
            data=marker.data,
            coordinates_metres=marker.coordinates_metres,
        )
        for marker in markers
    )
    constraints = _constraints(feature, normalized_markers, profiles)
    return NativeSketch(
        object_id=feature.object_id,
        name=feature.name,
        support_plane_id=support_plane_id,
        native_offset=start,
        native_end=end,
        markers=normalized_markers,
        profiles=profiles,
        dimensions=dimensions,
        constraints=constraints,
        native_stream=native_stream,
        support_kind=support_kind,
        support_plane=support_plane,
        support_source=support_source,
        unframed_support_plane_id=unframed_support_plane_id,
    )


def _parse_markers(data: bytes, start: int, end: int) -> tuple[NativeMarker, ...]:
    offsets = sorted(
        {
            offset
            for prefix in _MARKERS
            for offset in _find_all(data, prefix, start, end)
            if offset + 56 <= end
        }
    )
    markers: list[NativeMarker] = []
    for index, offset in enumerate(offsets):
        prefix_bytes = next(
            prefix for prefix in _MARKERS if data.startswith(prefix, offset)
        )
        native_offset = 17
        locus_offset = 23
        role_offset = 27
        if offset + native_offset + 4 > end:
            continue
        native_kind = struct.unpack_from("<I", data, offset + native_offset)[0]
        locus = data[offset + locus_offset : offset + locus_offset + 4]
        profile_role = struct.unpack_from("<H", data, offset + role_offset)[0]
        next_offset = offsets[index + 1] if index + 1 < len(offsets) else end
        length = next_offset - offset
        state_offset = offset + 48
        state = (
            struct.unpack_from("<d", data, state_offset)[0]
            if state_offset + 8 <= end
            else None
        )
        if state is not None and not math.isfinite(state):
            state = None
        coordinates_metres = _marker_coordinates_metres(data, offset, end)
        coordinates = (
            None
            if coordinates_metres is None
            else (
                _clean(round(coordinates_metres[0] * _MILLIMETRES, 12)),
                _clean(round(coordinates_metres[1] * _MILLIMETRES, 12)),
            )
        )
        endpoints = None
        if coordinates is None:
            pair_offset = offset + 64
            if pair_offset + 4 <= end:
                pair = struct.unpack_from("<HH", data, pair_offset)
                if pair != (0, 0):
                    endpoints = pair
        object_index = (
            struct.unpack_from("<I", data, offset - 4)[0] if offset >= 4 else 0xFFFFFFFF
        )
        if object_index == 0xFFFFFFFF:
            object_index = None
        local_id = _marker_local_id(data, offset, length)
        semantic = _marker_semantic(
            native_kind, locus, coordinates, endpoints, profile_role
        )
        markers.append(
            NativeMarker(
                offset=offset,
                length=length,
                prefix=prefix_bytes.hex(),
                native_kind=native_kind,
                locus=locus.hex(),
                profile_role=profile_role,
                state=state,
                object_index=object_index,
                local_id=local_id,
                coordinates_mm=coordinates,
                endpoint_indices=endpoints,
                construction=profile_role == 2,
                semantic=semantic,
                data=bytes(data[offset:next_offset]),
                coordinates_metres=coordinates_metres,
            )
        )
    return tuple(markers)


def _marker_coordinates_metres(
    data: bytes, offset: int, end: int
) -> tuple[float, float] | None:
    for relative in (56, 64):
        coordinate_offset = offset + relative
        if data[coordinate_offset : coordinate_offset + 2] != _COORDINATE_TAG:
            continue
        if coordinate_offset + 18 > end:
            continue
        x, y = struct.unpack_from("<2d", data, coordinate_offset + 2)
        if (
            math.isfinite(x)
            and math.isfinite(y)
            and abs(x) <= 1000.0
            and abs(y) <= 1000.0
        ):
            return x, y
    return None


def _marker_coordinates(
    data: bytes, offset: int, end: int
) -> tuple[float, float] | None:
    metres = _marker_coordinates_metres(data, offset, end)
    if metres is None:
        return None
    return (
        _clean(round(metres[0] * _MILLIMETRES, 12)),
        _clean(round(metres[1] * _MILLIMETRES, 12)),
    )


def _marker_radius_mm(center: NativeMarker, rim: NativeMarker) -> float | None:
    if center.coordinates_metres is None or rim.coordinates_metres is None:
        return None
    radius = (
        circle_radius_mm(
            rim.coordinates_metres[0] - center.coordinates_metres[0],
            rim.coordinates_metres[1] - center.coordinates_metres[1],
        )
        * _MILLIMETRES
    )
    return radius if math.isfinite(radius) and radius > 1e-12 else None


def _marker_start_angle_degrees(
    center: NativeMarker, rim: NativeMarker
) -> float | None:
    if center.coordinates_metres is None or rim.coordinates_metres is None:
        return None
    angle = math.degrees(
        math.atan2(
            rim.coordinates_metres[1] - center.coordinates_metres[1],
            rim.coordinates_metres[0] - center.coordinates_metres[0],
        )
    )
    return angle if math.isfinite(angle) else None


def _marker_local_id(data: bytes, offset: int, length: int) -> int | None:
    relative = MARKER_LOCAL_ID_OFFSET_BY_LENGTH.get(length)
    if relative is None or offset + relative + 4 > len(data):
        return None
    value = struct.unpack_from("<I", data, offset + relative)[0]
    return None if value == 0xFFFFFFFF else value


def _marker_semantic(
    native_kind: int,
    locus: bytes,
    coordinates: tuple[float, float] | None,
    endpoints: tuple[int, int] | None,
    profile_role: int,
) -> str:
    if profile_role == 2:
        if native_kind == 2 and endpoints is not None and endpoints[0] != endpoints[1]:
            return "line"
        return "native"
    if locus == _CIRCLE_LOCUS and coordinates is not None:
        return "circle"
    if locus == _POINT_LOCUS:
        if coordinates is not None:
            return "point"
        if endpoints is not None and endpoints[0] != endpoints[1]:
            return "line"
        return "reference"
    return "native"


def _linked_rectangle_profiles(
    markers: list[NativeMarker],
) -> tuple[tuple[NativeProfile, ...], set[int]]:
    profiles: list[NativeProfile] = []
    used: set[int] = set()
    for start in range(max(0, len(markers) - 8)):
        records = markers[start : start + 9]
        if len(records) != 9 or any(marker.offset in used for marker in records):
            continue
        points = records[:4]
        header = records[4]
        lines = records[5:]
        prefix = points[0].prefix
        locus = points[0].locus
        if (
            locus != _CIRCLE_LOCUS.hex()
            or any(
                marker.prefix != prefix
                or marker.locus != locus
                or marker.profile_role != 1
                or marker.native_kind != 0
                or marker.coordinates_mm is None
                for marker in points
            )
            or header.prefix != prefix
            or header.locus != locus
            or header.profile_role != 1
            or header.native_kind != 0
            or header.coordinates_mm is not None
            or header.endpoint_indices is None
            or header.length != 92
            or any(
                marker.prefix != prefix
                or marker.locus != locus
                or marker.profile_role != 1
                or marker.native_kind not in {1, 2}
                or marker.coordinates_mm is not None
                or marker.endpoint_indices is None
                for marker in lines
            )
            or any(marker.length != 92 for marker in lines[:-1])
            or lines[-1].length < 92
        ):
            continue
        coordinates = tuple(marker.coordinates_mm for marker in points)
        if any(coordinate is None for coordinate in coordinates):
            continue
        resolved = tuple(
            coordinate for coordinate in coordinates if coordinate is not None
        )
        xs = sorted({coordinate[0] for coordinate in resolved})
        ys = sorted({coordinate[1] for coordinate in resolved})
        if len(xs) != 2 or len(ys) != 2 or len(set(resolved)) != 4:
            continue
        corners = {(x, y) for x in xs for y in ys}
        if set(resolved) != corners:
            continue
        header_start, header_end = header.endpoint_indices
        if (
            header_start >= len(resolved)
            or header_end >= len(resolved)
            or header_start == header_end
        ):
            continue
        edge_markers: dict[str, NativeMarker] = {}
        valid = True
        for marker in lines:
            endpoint_start, endpoint_end = marker.endpoint_indices or (-1, -1)
            if (
                endpoint_start < 0
                or endpoint_end < 0
                or endpoint_start >= len(resolved)
                or endpoint_end >= len(resolved)
                or endpoint_start == endpoint_end
            ):
                valid = False
                break
            point_start = resolved[endpoint_start]
            point_end = resolved[endpoint_end]
            if math.isclose(point_start[1], point_end[1], abs_tol=1e-9):
                side = (
                    "bottom"
                    if math.isclose(point_start[1], ys[0], abs_tol=1e-9)
                    else "top"
                )
            elif math.isclose(point_start[0], point_end[0], abs_tol=1e-9):
                side = (
                    "left"
                    if math.isclose(point_start[0], xs[0], abs_tol=1e-9)
                    else "right"
                )
            else:
                valid = False
                break
            if side in edge_markers:
                valid = False
                break
            edge_markers[side] = marker
        if not valid or set(edge_markers) != {"bottom", "right", "top", "left"}:
            continue
        edge_offsets = tuple(
            edge_markers[side].offset for side in ("bottom", "right", "top", "left")
        )
        metadata_offsets = tuple(
            marker.offset
            for marker in (*points, header)
            if marker.offset not in edge_offsets
        )
        consumed = {marker.offset for marker in records}
        profiles.append(
            NativeProfile(
                "rectangle",
                (xs[0], ys[0], xs[1], ys[1]),
                (*edge_offsets, *metadata_offsets),
            )
        )
        used.update(consumed)
    return tuple(profiles), used


def _profiles(
    markers: list[NativeMarker], dimensions: tuple[NativeDimension, ...]
) -> tuple[tuple[NativeProfile, ...], set[int], tuple[NativeDimension, ...]]:
    linked_rectangles, linked_markers = _linked_rectangle_profiles(markers)
    structural_rectangles, structural_rectangle_markers = (
        _structural_rectangle_profiles(markers, linked_markers)
    )
    structural_circles, structural_markers, structural_dimensions = (
        _structural_circle_profiles(
            markers,
            dimensions,
            linked_markers | structural_rectangle_markers,
        )
    )
    remaining_markers = [
        marker
        for marker in markers
        if marker.offset
        not in linked_markers | structural_rectangle_markers | structural_markers
    ]
    circle_profiles, circle_dimensions = _circle_profiles(remaining_markers, dimensions)
    circle_dimensions.update(structural_dimensions)
    normalized = tuple(
        (
            replace(dimension, kind=circle_dimensions[index])
            if index in circle_dimensions
            else dimension
        )
        for index, dimension in enumerate(dimensions)
    )
    points = [
        marker
        for marker in remaining_markers
        if marker.coordinates_mm is not None and marker.locus == _POINT_LOCUS.hex()
    ]
    coordinates = list(dict.fromkeys(marker.coordinates_mm for marker in points))
    rectangles: list[tuple[float, float, float, float]] = []
    xs = sorted({point[0] for point in coordinates})
    ys = sorted({point[1] for point in coordinates})
    coordinate_set = set(coordinates)
    for x0, x1 in itertools.combinations(xs, 2):
        for y0, y1 in itertools.combinations(ys, 2):
            if {(x0, y0), (x0, y1), (x1, y0), (x1, y1)} <= coordinate_set:
                rectangles.append((x0, y0, x1, y1))
    values = [dimension.value_mm for dimension in dimensions]
    matches = [
        rectangle
        for rectangle in rectangles
        if _matches(rectangle[2] - rectangle[0], values)
        and _matches(rectangle[3] - rectangle[1], values)
    ]
    if matches:
        minimum = min(
            (rectangle[2] - rectangle[0]) * (rectangle[3] - rectangle[1])
            for rectangle in matches
        )
        selected = [
            rectangle
            for rectangle in matches
            if math.isclose(
                (rectangle[2] - rectangle[0]) * (rectangle[3] - rectangle[1]),
                minimum,
                abs_tol=1e-7,
            )
        ]
    else:
        selected = []
        for group_start in range(max(0, len(points) - 3)):
            group = points[group_start : group_start + 4]
            products = {marker.coordinates_mm for marker in group}
            gx = sorted({point[0] for point in products})
            gy = sorted({point[1] for point in products})
            if len(gx) == 2 and len(gy) == 2 and len(products) == 4:
                selected = [(gx[0], gy[0], gx[1], gy[1])]
                break
        if not selected and rectangles:
            selected = [
                max(
                    rectangles,
                    key=lambda rectangle: (rectangle[2] - rectangle[0])
                    * (rectangle[3] - rectangle[1]),
                )
            ]
    selected.sort(
        key=lambda rectangle: min(
            (
                marker.offset
                for marker in points
                if marker.coordinates_mm
                in {
                    (rectangle[0], rectangle[1]),
                    (rectangle[0], rectangle[3]),
                    (rectangle[2], rectangle[1]),
                    (rectangle[2], rectangle[3]),
                }
            ),
            default=1 << 62,
        )
    )
    line_markers = [
        marker
        for marker in remaining_markers
        if marker.semantic == "line"
        and marker.profile_role == 1
        and marker.locus == _POINT_LOCUS.hex()
    ]
    runs: list[list[NativeMarker]] = []
    for marker in line_markers:
        if not runs or marker.offset - runs[-1][-1].offset != 92:
            runs.append([marker])
        else:
            runs[-1].append(marker)
    profile_lines = [
        tuple(run[index : index + 4])
        for run in runs
        for index in range(0, len(run), 6)
        if len(run[index : index + 4]) == 4
    ]
    profiles: list[NativeProfile] = [
        *structural_circles,
        *circle_profiles,
        *linked_rectangles,
        *structural_rectangles,
    ]
    used: set[int] = (
        linked_markers | structural_rectangle_markers | structural_markers
    ) | {offset for profile in circle_profiles for offset in profile.marker_offsets}
    for index, rectangle in enumerate(selected):
        if any(
            profile.kind == "rectangle" and profile.coordinates == rectangle
            for profile in profiles
        ):
            continue
        span = tuple(
            marker.offset
            for marker in (profile_lines[index] if index < len(profile_lines) else ())
        )
        if circle_profiles and len(span) != 4:
            continue
        used.update(span)
        corners = {
            (rectangle[0], rectangle[1]),
            (rectangle[0], rectangle[3]),
            (rectangle[2], rectangle[1]),
            (rectangle[2], rectangle[3]),
        }
        used.update(
            marker.offset
            for marker in markers
            if marker.semantic == "point" and marker.coordinates_mm in corners
        )
        profiles.append(NativeProfile("rectangle", rectangle, span))
    profiles.sort(key=lambda profile: min(profile.marker_offsets, default=1 << 62))
    return tuple(profiles), used, normalized


def _structural_rectangle_profiles(
    markers: list[NativeMarker], excluded_offsets: set[int]
) -> tuple[tuple[NativeProfile, ...], set[int]]:
    edges = tuple(
        marker
        for marker in markers
        if marker.offset not in excluded_offsets
        and marker.profile_role == 1
        and marker.native_kind in {1, 2}
        and marker.coordinates_mm is None
        and marker.endpoint_indices is not None
        and marker.endpoint_indices[0] != marker.endpoint_indices[1]
        and all(
            0 <= endpoint < len(markers)
            and markers[endpoint].coordinates_mm is not None
            for endpoint in marker.endpoint_indices
        )
    )
    remaining = set(range(len(edges)))
    profiles: list[NativeProfile] = []
    used: set[int] = set()
    while remaining:
        component = {remaining.pop()}
        vertices = set(edges[next(iter(component))].endpoint_indices or ())
        changed = True
        while changed:
            changed = False
            for index in tuple(remaining):
                endpoints = set(edges[index].endpoint_indices or ())
                if vertices & endpoints:
                    remaining.remove(index)
                    component.add(index)
                    vertices.update(endpoints)
                    changed = True
        if len(component) != 4 or len(vertices) != 4:
            continue
        degrees = {vertex: 0 for vertex in vertices}
        for index in component:
            for vertex in edges[index].endpoint_indices or ():
                degrees[vertex] += 1
        if set(degrees.values()) != {2}:
            continue
        coordinates = {vertex: markers[vertex].coordinates_mm for vertex in vertices}
        if any(value is None for value in coordinates.values()):
            continue
        resolved = {
            vertex: value for vertex, value in coordinates.items() if value is not None
        }
        xs = sorted({value[0] for value in resolved.values()})
        ys = sorted({value[1] for value in resolved.values()})
        if (
            len(xs) != 2
            or len(ys) != 2
            or set(resolved.values()) != {(x, y) for x in xs for y in ys}
        ):
            continue
        sides: dict[str, NativeMarker] = {}
        valid = True
        for index in component:
            marker = edges[index]
            start, end = marker.endpoint_indices or (-1, -1)
            left = resolved[start]
            right = resolved[end]
            if math.isclose(left[1], right[1], abs_tol=1e-9):
                side = "bottom" if math.isclose(left[1], ys[0]) else "top"
            elif math.isclose(left[0], right[0], abs_tol=1e-9):
                side = "left" if math.isclose(left[0], xs[0]) else "right"
            else:
                valid = False
                break
            if side in sides:
                valid = False
                break
            sides[side] = marker
        if not valid or set(sides) != {"bottom", "right", "top", "left"}:
            continue
        line_offsets = tuple(
            sides[side].offset for side in ("bottom", "right", "top", "left")
        )
        used.update(line_offsets)
        profiles.append(
            NativeProfile(
                "rectangle",
                (xs[0], ys[0], xs[1], ys[1]),
                line_offsets,
            )
        )
    return tuple(profiles), used


def _structural_circle_profiles(
    markers: list[NativeMarker],
    dimensions: tuple[NativeDimension, ...],
    excluded_offsets: set[int],
) -> tuple[tuple[NativeProfile, ...], set[int], dict[int, str]]:
    profiles: list[NativeProfile] = []
    used: set[int] = set()
    normalized: dict[int, str] = {}
    geometries: set[tuple[float, float, float]] = set()
    for closure_index, closure in enumerate(markers):
        endpoints = closure.endpoint_indices
        if (
            closure.offset in excluded_offsets
            or closure.coordinates_mm is not None
            or closure.locus != _CIRCLE_LOCUS.hex()
            or closure.profile_role != 1
            or closure.native_kind not in {0, 1}
            or endpoints is None
            or endpoints[0] != endpoints[1]
        ):
            continue
        rim_index = endpoints[0]
        center_index = rim_index - 1
        if (
            not 0 <= center_index < rim_index < closure_index
            or closure_index - rim_index > 2
        ):
            continue
        center = markers[center_index]
        rim = markers[rim_index]
        if (
            center.offset in excluded_offsets
            or rim.offset in excluded_offsets
            or center.coordinates_mm is None
            or rim.coordinates_mm is None
            or rim.locus != _CIRCLE_LOCUS.hex()
            or center.profile_role != 1
            or rim.profile_role != 1
        ):
            continue
        radius = _marker_radius_mm(center, rim)
        if radius is None:
            continue
        start_angle = _marker_start_angle_degrees(center, rim)
        geometry = (
            center.coordinates_mm[0],
            center.coordinates_mm[1],
            radius,
        )
        if geometry in geometries:
            continue
        matches: list[tuple[int, str, float]] = []
        for index, dimension in enumerate(dimensions):
            if math.isclose(dimension.value_mm, radius, rel_tol=1e-7, abs_tol=1e-7):
                matches.append((index, "radius", dimension.value_mm))
            elif math.isclose(
                dimension.value_mm, radius * 2.0, rel_tol=1e-7, abs_tol=1e-7
            ):
                matches.append((index, "diameter", dimension.value_mm / 2.0))
        parameter_name = None
        dimension_kind = None
        if len(matches) == 1 and matches[0][0] not in normalized:
            dimension_index, dimension_kind, normalized_radius = matches[0]
            geometry = (geometry[0], geometry[1], normalized_radius)
            parameter_name = dimensions[dimension_index].name
            normalized[dimension_index] = dimension_kind
        geometries.add(geometry)
        marker_offsets = (center.offset, rim.offset, closure.offset)
        used.update(marker_offsets)
        profiles.append(
            NativeProfile(
                "circle",
                geometry,
                marker_offsets,
                parameter_name,
                dimension_kind,
                start_angle,
            )
        )
    return tuple(profiles), used, normalized


# dimensioned circles reverse marker order so both encodings need one decoder
def _circle_profiles(
    markers: list[NativeMarker], dimensions: tuple[NativeDimension, ...]
) -> tuple[tuple[NativeProfile, ...], dict[int, str]]:
    centers = [
        marker
        for marker in markers
        if marker.semantic == "circle" and marker.coordinates_mm is not None
    ]
    if not centers:
        return (), {}
    candidates: dict[
        int,
        dict[
            tuple[float, float, float],
            list[tuple[NativeMarker, NativeMarker, str, float | None]],
        ],
    ] = {}
    for CircleMarker in centers:
        FollowingMarker = next(
            (
                marker
                for marker in markers
                if marker.offset > CircleMarker.offset
                and marker.coordinates_mm is not None
                and not _same_point(
                    marker.coordinates_mm,
                    CircleMarker.coordinates_mm,
                )
            ),
            None,
        )
        PrecedingMarker = next(
            (
                marker
                for marker in reversed(markers)
                if marker.offset < CircleMarker.offset
                and marker.coordinates_mm is not None
                and not _same_point(
                    marker.coordinates_mm,
                    CircleMarker.coordinates_mm,
                )
            ),
            None,
        )
        CandidatePairs = tuple(
            ItemData
            for ItemData in (
                (
                    (
                        CircleMarker,
                        FollowingMarker,
                    )
                    if FollowingMarker is not None
                    else None
                ),
                (
                    (
                        PrecedingMarker,
                        CircleMarker,
                    )
                    if PrecedingMarker is not None and FollowingMarker is None
                    else None
                ),
            )
            if ItemData is not None
        )
        for CenterMarker, RimMarker in CandidatePairs:
            RadiusValue = _marker_radius_mm(CenterMarker, RimMarker)
            if RadiusValue is None:
                continue
            StartAngle = _marker_start_angle_degrees(CenterMarker, RimMarker)
            for index, dimension in enumerate(dimensions):
                semantic = None
                normalized_radius = RadiusValue
                if math.isclose(
                    dimension.value_mm,
                    RadiusValue,
                    rel_tol=1e-7,
                    abs_tol=1e-7,
                ):
                    semantic = "radius"
                    normalized_radius = dimension.value_mm
                elif math.isclose(
                    dimension.value_mm,
                    RadiusValue * 2.0,
                    rel_tol=1e-7,
                    abs_tol=1e-7,
                ):
                    semantic = "diameter"
                    normalized_radius = dimension.value_mm / 2.0
                if semantic is None:
                    continue
                geometry = (
                    CenterMarker.coordinates_mm[0],
                    CenterMarker.coordinates_mm[1],
                    normalized_radius,
                )
                candidates.setdefault(index, {}).setdefault(geometry, []).append(
                    (CenterMarker, RimMarker, semantic, StartAngle)
                )
    result: list[NativeProfile] = []
    geometries: set[tuple[float, float, float]] = set()
    normalized: dict[int, str] = {}
    for index, dimension in enumerate(dimensions):
        matches = candidates.get(index, {})
        if len(matches) != 1:
            continue
        geometry, records = next(iter(matches.items()))
        if geometry in geometries:
            continue
        semantics = {semantic for _, _, semantic, _ in records}
        if len(semantics) != 1:
            continue
        geometries.add(geometry)
        normalized[index] = next(iter(semantics))
        result.append(
            NativeProfile(
                "circle",
                geometry,
                tuple(
                    sorted(
                        {
                            offset
                            for center, following, _, _ in records
                            for offset in (center.offset, following.offset)
                        }
                    )
                ),
                dimension.name,
                normalized[index],
                records[0][3],
            )
        )
    result.sort(key=lambda profile: min(profile.marker_offsets))
    return tuple(result), normalized


def _same_point(left: tuple[float, float], right: tuple[float, float]) -> bool:
    return math.isclose(left[0], right[0], abs_tol=1e-12) and math.isclose(
        left[1], right[1], abs_tol=1e-12
    )


def _constraints(
    feature: NativeFeature,
    markers: tuple[NativeMarker, ...],
    profiles: tuple[NativeProfile, ...],
) -> tuple[NativeConstraint, ...]:
    constraints: list[NativeConstraint] = []
    radial_parameters: set[str] = set()
    for profile_index, profile in enumerate(profiles):
        if profile.kind == "rectangle":
            for edge_index in range(4):
                constraints.append(
                    NativeConstraint(
                        id=f"{feature.object_id}:profile:{profile_index}:axis:{edge_index}",
                        kind="horizontal" if edge_index % 2 == 0 else "vertical",
                        references=(
                            f"{feature.object_id}:profile:{profile_index}:edge:{edge_index}",
                        ),
                        parameter=None,
                        value=None,
                        native_offset=(
                            profile.marker_offsets[edge_index]
                            if edge_index < len(profile.marker_offsets)
                            else None
                        ),
                        native_code=None,
                    )
                )
        elif profile.kind == "circle":
            semantic = profile.dimension_kind or "radius"
            parameter_name = profile.parameter_name
            if parameter_name is not None:
                radial_parameters.add(parameter_name)
            constraints.append(
                NativeConstraint(
                    id=f"{feature.object_id}:profile:{profile_index}:{semantic}",
                    kind=semantic,
                    references=(f"{feature.object_id}:profile:{profile_index}",),
                    parameter=(
                        f"{feature.object_id}:{parameter_name}"
                        if parameter_name is not None
                        else None
                    ),
                    value=(
                        profile.coordinates[2] * 2.0
                        if semantic == "diameter"
                        else profile.coordinates[2]
                    ),
                    native_offset=(
                        profile.marker_offsets[0] if profile.marker_offsets else None
                    ),
                    native_code=None,
                )
            )
    for dimension in feature.dimensions:
        if dimension.name in radial_parameters:
            continue
        constraints.append(
            NativeConstraint(
                id=f"{feature.object_id}:dimension:{dimension.name}",
                kind="distance",
                references=tuple(
                    f"native:{operand.kind_code:04x}:{operand.entity_index}"
                    for operand in dimension.operands
                ),
                parameter=f"{feature.object_id}:{dimension.name}",
                value=dimension.value_mm,
                native_offset=dimension.native_offset,
                native_code=None,
            )
        )
    for marker in markers:
        if marker.semantic != "relation":
            continue
        constraints.append(
            NativeConstraint(
                id=f"{feature.object_id}:native-relation:{marker.offset}",
                kind=f"native_{marker.native_kind}",
                references=tuple(
                    f"native-index:{index}" for index in marker.endpoint_indices or ()
                ),
                parameter=None,
                value=None,
                native_offset=marker.offset,
                native_code=marker.native_kind,
            )
        )
    return tuple(constraints)


def _operation_fields(
    data: bytes, record: NativeName
) -> tuple[int | None, int | None, int | None]:
    if record.text_end + 12 > len(data):
        return None, None, None
    family = struct.unpack_from("<H", data, record.text_end + 4)[0]
    operation = data[record.text_end + 6]
    schema = data[record.text_end + 7]
    repeated_id = struct.unpack_from("<I", data, record.text_end + 8)[0]
    if repeated_id != record.object_id:
        return None, None, None
    return family, operation, schema


def _revolution_axis_marker(sketch: NativeSketch | None) -> NativeMarker | None:
    if sketch is None:
        return None
    candidates = tuple(
        marker
        for marker in sketch.markers
        if marker.profile_role == 2
        and marker.semantic == "line"
        and marker.endpoint_indices is not None
        and marker.endpoint_indices[0] != marker.endpoint_indices[1]
    )
    return candidates[0] if len(candidates) == 1 else None


def revolution_axis_direction(
    operation: NativeOperation, sketch: NativeSketch | None
) -> tuple[float, float] | None:
    if sketch is None:
        return None
    if operation.axis_marker_offset is None:
        axis = (
            _revolution_axis_marker(sketch)
            if operation.axis_source_kind is None
            else None
        )
    else:
        axis = next(
            (
                marker
                for marker in sketch.markers
                if marker.offset == operation.axis_marker_offset
            ),
            None,
        )
    if axis is None or axis.endpoint_indices is None:
        return None
    if any(
        not 0 <= endpoint < len(sketch.markers) for endpoint in axis.endpoint_indices
    ):
        return None
    start = sketch.markers[axis.endpoint_indices[0]].coordinates_mm
    end = sketch.markers[axis.endpoint_indices[1]].coordinates_mm
    if start is None or end is None:
        return None
    delta = (end[0] - start[0], end[1] - start[1])
    length = math.hypot(delta[0], delta[1])
    if length <= 0.0:
        return None
    return (_clean(delta[0] / length), _clean(delta[1] / length))


def operation_axis_subelement(
    operation: NativeOperation, sketch: NativeSketch | None
) -> str | None:
    if sketch is None or operation.profile_id != sketch.object_id:
        return None
    if operation.kind in _EXTRUSION_OPERATION_KINDS:
        return NORMAL_AXIS_SUBELEMENT
    if operation.kind not in _REVOLUTION_OPERATION_KINDS:
        return None
    direction = revolution_axis_direction(operation, sketch)
    if direction is None:
        return None
    if direction[0] == 0.0 and direction[1] != 0.0:
        return VERTICAL_AXIS_SUBELEMENT
    if direction[1] == 0.0 and direction[0] != 0.0:
        return HORIZONTAL_AXIS_SUBELEMENT
    return None


def _operation_selections(
    data: bytes,
    start: int,
    end: int,
    feature: NativeFeature,
    features: list[NativeFeature],
) -> tuple[tuple[int, int, int], ...]:
    preceding = {
        item.object_id
        for item in features
        if item.object_id > 25
        and item.native_offset is not None
        and feature.native_offset is not None
        and item.native_offset < feature.native_offset
    }
    result: list[tuple[int, int, int]] = []
    seen: set[tuple[int, int]] = set()
    for selection in _edge_selections(data, start, end):
        identity = selection[1], selection[2]
        if (
            selection[1] not in preceding
            or not 0 < selection[2] < 0x8000
            or identity in seen
        ):
            continue
        seen.add(identity)
        result.append(selection)
    return tuple(result)


def _operation_selections_after_class(
    data: bytes,
    start: int,
    end: int,
    feature: NativeFeature,
    features: list[NativeFeature],
    class_name: str,
) -> tuple[tuple[int, int, int], ...]:
    declarations = tuple(
        item
        for item in _parse_classes(data)
        if item.name == class_name and start <= item.offset < end
    )
    if len(declarations) != 1:
        return ()
    declaration = declarations[0]
    class_end = declaration.offset + 6 + len(class_name.encode("ascii"))
    return _operation_selections(data, class_end, end, feature, features)


def _native_translation(
    dimensions: tuple[NativeDimension, ...],
) -> tuple[float, float, float] | None:
    by_name = {
        dimension.name.casefold(): dimension
        for dimension in dimensions
        if dimension.name.casefold() in {"d1", "d2", "d3"}
    }
    if set(by_name) != {"d1", "d2", "d3"} or any(
        item.native_offset is None for item in by_name.values()
    ):
        return None
    return tuple(by_name[f"d{index}"].value_mm for index in range(1, 4))


def _native_scale_factors(
    data: bytes, start: int, end: int
) -> tuple[float, float, float] | None:
    if end - start < 38:
        return None
    block = data[end - 38 : end]
    if (
        block[:4] != struct.pack("<I", 1)
        or block[28:36] != b"\0" * 8
        or struct.unpack_from("<H", block, 36)[0] < 0x8000
    ):
        return None
    factors = struct.unpack_from("<3d", block, 4)
    if not all(math.isfinite(value) and value > 0.0 for value in factors):
        return None
    return factors


def _resolve_profile_operation(
    operation: NativeOperation,
    sketches: dict[int, NativeSketch],
    data: bytes,
    features: list[NativeFeature],
) -> NativeOperation:
    if operation.kind != "hole" or operation.profile_id not in sketches:
        return operation
    sketch = sketches[operation.profile_id]
    circles = tuple(profile for profile in sketch.profiles if profile.kind == "circle")
    feature = next(
        (item for item in features if item.object_id == operation.object_id), None
    )
    selections = (
        _operation_selections(
            data,
            sketch.native_offset,
            sketch.native_end,
            feature,
            features,
        )
        if feature is not None
        else ()
    )
    return replace(
        operation,
        diameter_mm=(circles[0].coordinates[2] * 2.0 if len(circles) == 1 else None),
        selection_offsets=tuple(selection[0] for selection in selections),
        selected_local_ids=tuple(selection[2] for selection in selections),
        selection_references=tuple(
            (selection[1], selection[2]) for selection in selections
        ),
    )


def _end_spec(
    data: bytes,
    start: int,
    end: int,
    classes: tuple[NativeClass, ...] = (),
) -> NativeEndSpec | None:
    mirrored_offset, mirrored_code = _mirrored_direction(data, classes, start, end)
    for offset in range(start, max(start, end - 26 + 1) + 1):
        prefix = data[offset : offset + 2]
        if prefix != b"_c" and not (
            len(prefix) == 2
            and struct.unpack("<H", prefix)[0] & 0x8000
            and prefix != b"\xff\xff"
        ):
            continue
        if data[offset + 2 : offset + 4] != b"\0\0":
            continue
        if struct.unpack_from("<I", data, offset + 4)[0] != 1:
            continue
        if struct.unpack_from("<I", data, offset + 8)[0] not in {0, 1}:
            continue
        direction = struct.unpack_from("<I", data, offset + 12)[0]
        if direction not in {0, 1} or data[offset + 16 : offset + 18] != b"\0\0":
            continue
        termination = struct.unpack_from("<I", data, offset + 18)[0]
        second = struct.unpack_from("<I", data, offset + 22)[0]
        if termination > 64 or second > 1:
            continue
        return NativeEndSpec(
            offset,
            termination,
            direction,
            second,
            mirrored_offset,
            mirrored_code,
        )
    return None


def _edge_selections(
    data: bytes, start: int, end: int
) -> tuple[tuple[int, int, int], ...]:
    selections: list[tuple[int, int, int]] = []
    for offset in _find_all(data, _EDGE_SELECTION_IDENTITY, start, end):
        if offset + 38 > end:
            continue
        producer = struct.unpack_from("<I", data, offset + 26)[0]
        local_id = struct.unpack_from("<I", data, offset + 34)[0]
        if producer and local_id:
            selections.append((offset, producer, local_id))
    return tuple(selections)


def _operation_dimension(
    dimensions: tuple[NativeDimension, ...], semantic: str
) -> float | None:
    return next(
        (dimension.value_mm for dimension in dimensions if dimension.kind == semantic),
        None,
    )


def _operation_dimension_offset(
    dimensions: tuple[NativeDimension, ...], semantic: str
) -> int | None:
    return next(
        (
            dimension.native_offset
            for dimension in dimensions
            if dimension.kind == semantic and dimension.native_offset is not None
        ),
        None,
    )


def _integer_property(value: str | None) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _find_all(
    data: bytes, marker: bytes, start: int = 0, end: int | None = None
) -> list[int]:
    result: list[int] = []
    cursor = start
    limit = len(data) if end is None else end
    while True:
        offset = data.find(marker, cursor, limit)
        if offset < 0:
            return result
        result.append(offset)
        cursor = offset + 1


def _matches(value: float, candidates: list[float]) -> bool:
    return any(math.isclose(value, candidate, abs_tol=1e-6) for candidate in candidates)


def _norm(vector: tuple[float, float, float]) -> float:
    return math.sqrt(sum(value * value for value in vector))


def _dot(left: tuple[float, float, float], right: tuple[float, float, float]) -> float:
    return sum(a * b for a, b in zip(left, right, strict=True))


def _cross(
    left: tuple[float, float, float], right: tuple[float, float, float]
) -> tuple[float, float, float]:
    return (
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    )


def _clean(value: float) -> float:
    return 0.0 if abs(value) <= 1e-12 else value
