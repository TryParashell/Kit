# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

import base64
from dataclasses import dataclass, field, replace
import hashlib
import itertools
import math
import re
import struct
from types import MappingProxyType
from typing import Any, Mapping, Sequence
import xml.etree.ElementTree as ET
import zlib

from interchange import (
    BooleanOperation,
    CadDocument,
    Capability,
    CircleGeometry,
    ExtrusionEndCondition,
    ExtrusionFeature,
    FeatureKind,
    FeatureStep,
    FilletFeature,
    LineGeometry,
    Parameter,
    ParameterRole,
    ParameterValue,
    Sketch,
    SupportPlane,
    ValueKind,
)

from .container import SldprtFormatError
from .format import (
    ASSEMBLY_SUFFIX,
    CANONICAL_PLANE_FEATURE_TYPE,
    CLASS_MARKER,
    CONFIGURATION_STREAM,
    DIMENSION_SCALAR_HEADERS,
    DISPLAY_LISTS_STREAM,
    KIT_RESOLVED_STREAM,
    PART_SUFFIX,
    PLANE_FEATURE_TYPES,
    RESOLVED_FEATURES_STREAM,
    SERIALIZED_STRING_MARKER,
    dimension_scalar_value_offset,
)
from .parasolid import encode_blank_partition_stream
from .resolved import (
    ANGLE_COPY_DELTAS,
    DEPTH_COPY_DELTAS,
    DEPTH_COPY_SIGNS,
    FROM_END_SPEC_CLASS,
    FROM_REVERSE_RELATIVE,
    REVOLUTION_AXIS_SKETCH,
    SKETCH_CHAIN_CLASS,
    circle_radius_mm,
    locate_features,
    patch_rectangle_pad,
)

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
_SCALAR_HEADER = DIMENSION_SCALAR_HEADERS[0]
_SOLIDWORKS_XML_NAMESPACE = "http://www.solidworks.com/sw2003/schema"
_SOLIDWORKS_CONFIGURATION_FLAGS = -2143288960
_CREATION_STAMP_LOW = 1577836800
_CREATION_STAMP_HIGH = 1893456000
_BASE_BODY_COUNTERS = {
    0: 0x6B,
    4: 0x12,
    1495: 0x80,
    1690: 0x81,
    1724: 0x83,
    2315: 0x46,
    3483: 0x94,
    3806: 0x97,
    4049: 0x94,
    4376: 0x97,
    5128: 0x52,
    5302: 0x52,
}
_RECTANGLE_BOSS_POINT_OFFSETS = (6119, 6297, 6459, 6621)
_RECTANGLE_BOSS_DEPTH_OFFSET = 10092
_RECTANGLE_BOSS_NATIVE_WRITE_PROFILE = MappingProxyType(
    {
        "application": "SOLIDWORKS 2025",
        "support_plane_object_id": 2,
        "sketch_name": "Sketch1",
        "sketch_geometry": "closed-axis-aligned-four-line-rectangle",
        "sketch_variable_parameters": frozenset(
            {"minimum_x_mm", "minimum_y_mm", "maximum_x_mm", "maximum_y_mm"}
        ),
        "sketch_constraints": frozenset(),
        "feature_name": "Boss-Extrude1",
        "feature_operation": "blind-unreversed-join",
        "feature_variable_parameters": frozenset({"D1_mm"}),
        "cache_bounds_mm": (-20.0, -10.0, 20.0, 10.0),
        "cache_depth_mm": 10.0,
        "resolved_features_size": 11285,
        "resolved_features_variable_ranges": (
            (6119, 16),
            (6297, 16),
            (6459, 16),
            (6621, 16),
            (10092, 8),
        ),
        "resolved_features_fixed_bytes": 11213,
        "oracle_partition": (
            3790,
            "56df5b4e4ccac3158b60ea75dd57959b991660d6d9c7bc05cbff795e56f44439",
        ),
        "envelope_streams": MappingProxyType(
            {
                "Contents/CMgr": (
                    1985,
                    "79d8327f0ec9965500ac044320d9054666d1685cc9b294d766998ba75b654e16",
                ),
                "Contents/Config-0": (
                    25248,
                    "7a9117f55f6a3b4f790b8438940cc3e54d9b3125daeea7b8492e5f840eb86429",
                ),
                "Contents/Config-0-LWDATA": (
                    1437,
                    "570d1a2ee4895160fdee5c4731eb0fffe0868dd99798e6868eb3c6e432009c17",
                ),
                "Contents/Config-0-ModelHeader": (
                    2347,
                    "311de5a2f1e2abe699ffbe87f545525caa8fc7f48303c25ff07ff4d18043d7d3",
                ),
                "Contents/Definition": (
                    3810,
                    "1de1a4f10c22851eb4b7925b7cc73f8e4534217c544c20cded6f49644bce4e94",
                ),
                DISPLAY_LISTS_STREAM: (
                    6270,
                    "0003781d79ee5e4bbcf52b57fc375b6b3644bc87eda2db1956a63d0d3dcde211",
                ),
                "Header2": (
                    2347,
                    "311de5a2f1e2abe699ffbe87f545525caa8fc7f48303c25ff07ff4d18043d7d3",
                ),
            }
        ),
    }
)
_BLIND_END_SPEC = bytes.fromhex(
    "ffff01000b006d6f456e64537065635f63000001000000000000000000000000000000000000000000"
)
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
_ASSEMBLY_VERSION_PREFIX = "_MO_VERSION_13000"
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


def encode_native_part(document: CadDocument, model_name: str) -> NativePartStreams:
    object_ids = _write_object_ids(document)
    authored = _write_objects(document, object_ids)
    if not authored and document.brep is not None:
        authored = (
            _WriteObject(
                "brep:imported",
                26,
                "Imported1",
                "Feature",
                "Imported",
                "moBaseBody_c",
            ),
        )
    authored = _canonical_rectangle_boss_objects(authored, object_ids, document)
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
    blank_native = not authored and not document.sketches
    keywords = _keywords_payload(
        document,
        model_name,
        (*objects, *keyword_only),
        object_ids,
        identity,
    )
    features = _features_payload(document, model_name, object_ids, identity)
    if blank_native or _is_native_resolved_objects(authored):
        resolved = (
            _base_record(_BASE_RESOLVED_FEATURES)
            if blank_native
            else _resolved_payload(objects)
        )
        kit_resolved: bytes | None = None
    else:
        resolved = _base_record(_BASE_RESOLVED_FEATURES)
        kit_resolved = _resolved_payload(objects)
    envelope_streams = _native_envelope_streams(
        document,
        model_name,
        identity,
        rectangle_boss=_is_rectangle_boss_objects(authored),
    )
    configuration_data = envelope_streams.get(CONFIGURATION_STREAM, b"")
    parsed = (
        decode_native_model(keywords, resolved, configuration_data)
        if kit_resolved is None
        else decode_native_model(
            keywords,
            kit_resolved,
            configuration_data,
            resolved_stream=KIT_RESOLVED_STREAM,
        )
    )
    capabilities = _proved_write_capabilities(document, authored, parsed, object_ids)
    freecad_rectangle = _freecad_rectangle_boss_objects(document, authored)
    mixed_capabilities: frozenset[Capability] = frozenset()
    partition: bytes | None = None
    application_usable = False
    vendor_loadable = False
    if freecad_rectangle:
        capabilities = frozenset(
            (
                *capabilities,
                Capability.EDITABLE_SKETCHES,
                Capability.PARAMETRIC_HISTORY,
                Capability.BODY_STRUCTURE,
            )
        )
        mixed_capabilities = frozenset({Capability.PARAMETERS})
        bounds = _write_rectangle_bounds(authored[0])
        if bounds is None:
            raise SldprtFormatError("native rectangle record requires one rectangle")
        partition = encode_blank_partition_stream()
        vendor_loadable = True
        application_usable = True
        capabilities = capabilities | {Capability.BREP}
    lanes = tuple(
        (
            object_ids[f"configuration:{configuration.id}"],
            resolved,
        )
        for configuration in document.configurations
    )
    if not lanes:
        lanes = ((0, resolved),)
    return NativePartStreams(
        keywords,
        features,
        resolved,
        kit_resolved,
        lanes,
        capabilities,
        mixed_capabilities,
        MappingProxyType(object_ids),
        envelope_streams,
        partition,
        application_usable,
        vendor_loadable,
    )


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
        values = (
            (transform.origin.x, transform.origin.y, transform.origin.z),
            (transform.x_axis.x, transform.x_axis.y, transform.x_axis.z),
            (transform.y_axis.x, transform.y_axis.y, transform.y_axis.z),
            (transform.z_axis.x, transform.z_axis.y, transform.z_axis.z),
        )
        for object_id, *frame in frames:
            if object_id in claimed:
                continue
            if all(
                math.isclose(left, right, rel_tol=0.0, abs_tol=1e-9)
                for left_vector, right_vector in zip(values, frame, strict=True)
                for left, right in zip(left_vector, right_vector, strict=True)
            ):
                result[plane.id] = object_id
                claimed.add(object_id)
                break
    return result


def _write_objects(
    document: CadDocument, object_ids: dict[str, int]
) -> tuple[_WriteObject, ...]:
    parameters = {parameter.id: parameter for parameter in document.parameters}
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


def _canonical_rectangle_boss_objects(
    objects: tuple[_WriteObject, ...],
    object_ids: dict[str, int],
    document: CadDocument,
) -> tuple[_WriteObject, ...]:
    if len(objects) != 2:
        return objects
    sketch, extrusion = objects
    bounds = _write_rectangle_bounds(sketch)
    source_sketch = next(
        (item for item in document.sketches if item.id == sketch.source_id), None
    )
    source_feature = next(
        (item for item in document.feature_timeline if item.id == extrusion.source_id),
        None,
    )
    if (
        len(sketch.payload) < 4
        or struct.unpack_from("<I", sketch.payload)[0] != 2
        or sketch.class_name != "moProfileFeature_c"
        or sketch.dimensions
        or extrusion.class_name != "moExtrusion_c"
        or extrusion.payload != _BLIND_END_SPEC
        or bounds is None
        or source_sketch is None
        or source_sketch.suppressed
        or len(source_sketch.entities) != 4
        or any(
            item.construction
            or item.fixed
            or not isinstance(item.geometry, LineGeometry)
            for item in source_sketch.entities
        )
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
    freecad_dimension = _freecad_rectangle_boss_dimension(
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
    object_ids[f"sketch:{sketch.source_id}"] = 26
    object_ids[f"feature:{extrusion.source_id}"] = 32
    return (
        replace(sketch, object_id=26, name="Sketch1"),
        replace(
            extrusion,
            object_id=32,
            name="Boss-Extrude1",
            dimensions=(dimension,),
        ),
    )


def _freecad_rectangle_boss_dimension(
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
    if (
        str(definition.end_condition).casefold() != ExtrusionEndCondition.BLIND.value
        or definition.reversed
        or definition.symmetric
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
        or not math.isclose(definition.direction.x, 0.0, abs_tol=1e-12)
        or not math.isclose(definition.direction.y, 0.0, abs_tol=1e-12)
        or not math.isclose(definition.direction.z, 1.0, abs_tol=1e-12)
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
        "Midplane": (ValueKind.BOOLEAN, False),
        "Offset": (ValueKind.LENGTH, 0.0),
        "Offset2": (ValueKind.LENGTH, 0.0),
        "Refine": (ValueKind.BOOLEAN, True),
        "Reversed": (ValueKind.BOOLEAN, False),
        "SideType": (ValueKind.INTEGER, 0),
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
    elif kind == "Fillet":
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
        FeatureKind.CHAMFER.value: ("Chamfer", "moChamfer_c"),
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


def _extrusion_payload(feature: FeatureStep) -> bytes:
    definition = feature.definition
    direction = int(isinstance(definition, ExtrusionFeature) and definition.reversed)
    condition = (
        definition.end_condition if isinstance(definition, ExtrusionFeature) else None
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
            record = bytearray(38)
            record[:16] = _EDGE_SELECTION_IDENTITY
            struct.pack_into("<I", record, 26, producer)
            struct.pack_into("<I", record, 34, local_id)
            result.extend(record)
    return bytes(result)


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


def _resolved_payload(objects: tuple[_WriteObject, ...]) -> bytes:
    authored = objects[len(_BASE_OBJECTS) :]
    if _is_rectangle_boss_objects(authored):
        return _base_rectangle_boss_payload(authored[0], authored[1])
    if _is_base_body_objects(authored):
        return _base_body_payload()
    output = bytearray(struct.pack("<IH", len(objects), max(0, len(objects) - 1)))
    for item in objects:
        output.extend(_class_declaration(item.class_name))
        operation = item.kind == "Extrusion"
        operation_code = 2 if item.class_name == "moCut_c" else 0
        output.extend(
            _name_record(
                item.name,
                item.object_id,
                operation=operation,
                operation_code=operation_code,
            )
        )
        output.extend(item.payload)
        for dimension in item.dimensions:
            output.extend(_scalar_record(dimension))
    return bytes(output)


def _is_base_body_objects(authored: tuple[_WriteObject, ...]) -> bool:
    return (
        len(authored) == 1
        and authored[0].object_id == 26
        and authored[0].name == "Imported1"
        and authored[0].class_name == "moBaseBody_c"
        and not authored[0].dimensions
        and not authored[0].payload
    )


def _is_native_resolved_objects(authored: tuple[_WriteObject, ...]) -> bool:
    return _is_rectangle_boss_objects(authored) or _is_base_body_objects(authored)


def _is_rectangle_boss_objects(authored: tuple[_WriteObject, ...]) -> bool:
    return (
        len(authored) == 2
        and authored[0].object_id == 26
        and authored[0].name == "Sketch1"
        and authored[0].class_name == "moProfileFeature_c"
        and authored[1].object_id == 32
        and authored[1].name == "Boss-Extrude1"
        and authored[1].class_name == "moExtrusion_c"
        and len(authored[1].dimensions) == 1
    )


def _freecad_rectangle_boss_objects(
    document: CadDocument,
    authored: tuple[_WriteObject, ...],
) -> bool:
    if not _is_rectangle_boss_objects(authored):
        return False
    source_sketch = next(
        (item for item in document.sketches if item.id == authored[0].source_id), None
    )
    source_feature = next(
        (
            item
            for item in document.feature_timeline
            if item.id == authored[1].source_id
        ),
        None,
    )
    return (
        source_sketch is not None
        and source_feature is not None
        and _freecad_rectangle_boss_dimension(
            document,
            source_sketch,
            source_feature,
        )
        is not None
    )


def _base_body_payload() -> bytes:
    output = bytearray(_base_record(_BASE_RESOLVED_FEATURES))
    for offset, value in _BASE_BODY_COUNTERS.items():
        output[offset] = value
    return bytes(output[:-4]) + _base_record(_BASE_BODY_FEATURE) + bytes(output[-4:])


def _base_rectangle_boss_payload(
    sketch: _WriteObject, extrusion: _WriteObject
) -> bytes:
    bounds = _write_rectangle_bounds(sketch)
    if bounds is None:
        raise SldprtFormatError("native rectangle record requires one closed rectangle")
    minimum_x, minimum_y, maximum_x, maximum_y = bounds
    return patch_rectangle_pad(
        _base_record(_BASE_RECTANGLE_BOSS_FEATURES),
        minimum_x_mm=minimum_x,
        minimum_y_mm=minimum_y,
        maximum_x_mm=maximum_x,
        maximum_y_mm=maximum_y,
        depth_mm=extrusion.dimensions[0].value_mm,
    )


def _class_declaration(name: str) -> bytes:
    encoded = name.encode("ascii")
    return CLASS_MARKER + struct.pack("<H", len(encoded)) + encoded


def _name_record(
    name: str, object_id: int, *, operation: bool = False, operation_code: int = 0
) -> bytes:
    encoded = name.encode("utf-16le")
    units = len(encoded) // 2
    if not 1 <= units <= 255:
        raise SldprtFormatError(
            "native SOLIDWORKS object name exceeds 255 UTF-16 units"
        )
    fields = (
        b"\0" * 4 + struct.pack("<HBBI", 0x0140, operation_code, 0x40, object_id)
        if operation
        else struct.pack("<dI", 2.0, object_id)
    )
    return _NAME_PREFIX + bytes((units,)) + encoded + fields + b"\0" * 16


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
    last_modified_stamp = 101 + authored * 4 + len(document.sketches) * 2
    return _NativeIdentity(
        creation_stamp,
        last_modified_stamp,
        101,
        (creation_stamp + authored * 7 + len(document.sketches) * 3 + 5) & 0x7FFFFFFF,
        _SOLIDWORKS_CONFIGURATION_FLAGS,
        "Part1",
    )


def _native_envelope_streams(
    document: CadDocument,
    model_name: str,
    identity: _NativeIdentity,
    *,
    rectangle_boss: bool = False,
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
    if rectangle_boss:
        streams.update(_rectangle_boss_envelope_streams())
    else:
        model_header = _model_header_payload(identity, configuration_name)
        streams.update(
            {
                "Contents/CMgr": _base_record(_BASE_CONFIGURATION_MANAGER),
                "Contents/Config-0": _base_record(_BASE_CONFIGURATION),
                "Contents/Config-0-LWDATA": _base_record(_BASE_LIGHTWEIGHT_DATA),
                "Contents/Config-0-ModelHeader": model_header,
                "Contents/Definition": _base_record(_BASE_DEFINITION),
                "Header2": model_header,
            }
        )
    return MappingProxyType(streams)


def _rectangle_boss_envelope_streams() -> Mapping[str, bytes]:
    model_header = _base_record(_BASE_RECTANGLE_BOSS_MODEL_HEADER)
    return MappingProxyType(
        {
            "Contents/CMgr": _base_record(_BASE_RECTANGLE_BOSS_CONFIGURATION_MANAGER),
            "Contents/Config-0": _base_record(_BASE_RECTANGLE_BOSS_CONFIGURATION),
            "Contents/Config-0-LWDATA": _base_record(
                _BASE_RECTANGLE_BOSS_LIGHTWEIGHT_DATA
            ),
            "Contents/Config-0-ModelHeader": model_header,
            "Contents/Definition": _base_record(_BASE_RECTANGLE_BOSS_DEFINITION),
            DISPLAY_LISTS_STREAM: _base_record(_BASE_RECTANGLE_BOSS_DISPLAY_LISTS),
            "Header2": model_header,
        }
    )


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
    offset = _expect_bytes(data, offset, bytes.fromhex("4180"))
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
        _ASSEMBLY_REFERENCE_NAME,
    )


def _base_record(chunks: bytes | tuple[bytes, ...]) -> bytes:
    encoded = chunks if isinstance(chunks, bytes) else b"".join(chunks)
    return zlib.decompress(base64.b85decode(encoded))


def _model_header_payload(
    identity: _NativeIdentity,
    configuration_name: str,
    user_name: str = "Kit",
) -> bytes:
    return _header_payload(identity, configuration_name, _HEADER_OBJECTS, "", user_name)


def _header_payload(
    identity: _NativeIdentity,
    configuration_name: str,
    objects: Sequence[tuple[int, str, bool]],
    document_path: str,
    user_name: str = "Kit",
) -> bytes:
    legacy_stamp = bytes.fromhex("f65a1a69")
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
    for object_id, name, modified in objects:
        actions = ("Created", "Modified") if modified else ("Created",)
        output.extend(bytes.fromhex("0880") + struct.pack("<H", len(actions)))
        stamp = (
            legacy_stamp
            if object_id <= 16
            else struct.pack("<I", identity.creation_stamp)
        )
        for index, action in enumerate(actions):
            output.extend(
                bytes.fromhex("0a80") + struct.pack("<I", index) + b"\0\0" + stamp
            )
            output.extend(_serialized_string(action))
        output.extend(struct.pack("<I", object_id))
        output.extend(_serialized_string(name))
    output.extend(
        legacy_stamp
        + struct.pack("<IH", max(item[0] for item in objects) + 1, 0)
        + struct.pack("<I", identity.last_modified_stamp)
    )
    output.extend(_class_declaration("moExtObject_c"))
    output.extend(_class_declaration("moCStringHandle_c"))
    output.extend(_serialized_string(document_path))
    output.extend(bytes.fromhex("4180"))
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
    output.extend(b"\0" * 14 + b"\xff" * 10)
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
        + bytes.fromhex(
            "020000005046000034e71e0001000000090000000c000000020000000a00000000000000f4650000"
        )
    )
    for _ in range(7):
        output.extend(_serialized_string(""))
        output.extend(b"\0" * (14 if len(output) == 63 else 12))
    output.extend(struct.pack("<QI", filetime, 0x29310000))
    for path in first_paths:
        output.extend(_serialized_string(path))
        output.extend(bytes.fromhex("0300000000404f4505000000"))
    output.extend(
        bytes.fromhex(
            "5046000034e71e0001000000090000000c000000020000000a0000000000000058660000"
        )
    )
    output.extend(_serialized_string(""))
    output.extend(struct.pack("<HQI", 0x1809, filetime, 0x6BAA7000))
    for path in second_paths:
        output.extend(_serialized_string(path))
        output.extend(bytes.fromhex("030000000050af0c05000000"))
    output.extend(struct.pack("<QI", filetime, 0x55820000))
    for value in ("*", "*", "C:\\", "*", "*"):
        output.extend(_serialized_string(value))
        output.extend(bytes.fromhex("030000000090a20c05000000"))
    output.extend(_serialized_string(f"C:\\{model_name}{document_suffix}"))
    output.extend(bytes.fromhex("030000000090a20c05000000"))
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
        object_ids[f"plane:{plane.id}"]: (
            plane.name,
            _frame_vector(
                (
                    plane.transform.origin.x,
                    plane.transform.origin.y,
                    plane.transform.origin.z,
                )
            ),
            _frame_vector(
                (
                    plane.transform.x_axis.x,
                    plane.transform.x_axis.y,
                    plane.transform.x_axis.z,
                )
            ),
            _frame_vector(
                (
                    plane.transform.y_axis.x,
                    plane.transform.y_axis.y,
                    plane.transform.y_axis.z,
                )
            ),
            _frame_vector(
                (
                    plane.transform.z_axis.x,
                    plane.transform.z_axis.y,
                    plane.transform.z_axis.z,
                )
            ),
        )
        for plane in document.support_planes
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
        object_id in actual_planes and actual_planes[object_id] == frame[1:]
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
    return frozenset(result)


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
        math.radians(dimension.value_mm)
        if dimension.kind == "angle"
        else dimension.value_mm / 1000.0
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
    semantic = {
        "extrusion": "length",
        "fillet": "radius",
        "cut": "depth",
        "revolve": "angle",
        "revolution": "angle",
        "cut-revolve": "angle",
        "revcut": "angle",
        "chamfer": "distance",
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
    for center in centers:
        following = next(
            (
                marker
                for marker in markers
                if marker.offset > center.offset
                and marker.coordinates_mm is not None
                and not _same_point(marker.coordinates_mm, center.coordinates_mm)
            ),
            None,
        )
        if following is None:
            continue
        radius = _marker_radius_mm(center, following)
        if radius is None:
            continue
        start_angle = _marker_start_angle_degrees(center, following)
        for index, dimension in enumerate(dimensions):
            semantic = None
            normalized_radius = radius
            if math.isclose(dimension.value_mm, radius, rel_tol=1e-7, abs_tol=1e-7):
                semantic = "radius"
                normalized_radius = dimension.value_mm
            elif math.isclose(
                dimension.value_mm, radius * 2.0, rel_tol=1e-7, abs_tol=1e-7
            ):
                semantic = "diameter"
                normalized_radius = dimension.value_mm / 2.0
            if semantic is None:
                continue
            geometry = (
                center.coordinates_mm[0],
                center.coordinates_mm[1],
                normalized_radius,
            )
            candidates.setdefault(index, {}).setdefault(geometry, []).append(
                (center, following, semantic, start_angle)
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
