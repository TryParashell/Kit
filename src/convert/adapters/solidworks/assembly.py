# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from pathlib import PureWindowsPath
import math
import re
import struct
from types import MappingProxyType
from typing import Any, Iterable, Mapping, Sequence
import xml.etree.ElementTree as ET

from interchange import (
    AssemblyData,
    ComponentDefinition,
    ComponentInstance,
    ComponentKind,
    Configuration,
    MateAlignment,
    MateConstraint,
    MateEntity,
    MateGroup,
    Matrix4,
    ValueKind,
)

from .container import SldprtArchive, SldprtFormatError
from .display import (
    NativeDisplayComponent,
    NativeTessellationFace as NativeTessellationFace,
    decode_display_lists,
    decode_tessellation_faces as decode_tessellation_faces,
)
from .format import (
    CLASS_MARKER,
    COMPONENT_TREE_STREAM,
    DIMENSION_SCALAR_HEADERS,
    DISPLAY_LISTS_STREAM,
    MATES_STREAM_NAME,
    MATES_STREAM_SUFFIX,
    SERIALIZED_STRING_MARKER,
    dimension_scalar_value_offset,
    is_cad_path,
    is_component_path,
)

_WIDE_TEXT = re.compile(rb"(?:[ -~\xa1-\xff]\x00){4,}")
_MATE_ALIGNMENT_OFFSET = 159
_MATE_ENTITY_COUNT_OFFSET = 164
_MATE_RECORD_BODY_SIZE = 168
_MATE_OBJECT_PREFIX = 0x8001
_MATE_LIST_NATIVE_ID_FLAG = 0x10000
_MATE_GROUP_END_SUFFIX = "___EndTag___"

MATE_LOSS_EXPRESSION = "expression_resolved_to_value"
MATE_LOSS_ENTITY_FRAME = "mate_entity_frame"
MATE_LOSS_ENTITY_RADIUS = "mate_entity_radius"
MATE_LOSS_VALUE = "mate_value_unrepresentable"
MATE_LOSS_VALUE_MISSING = "mate_value_missing"
MATE_LOSS_GROUP_NESTING = "mate_group_nesting"
MATE_LOSS_GROUP_MEMBERSHIP = "mate_group_membership"
MATE_LOSS_ORPHAN_ENTITY = "unreferenced_mate_entity"
MATE_LOSS_SUPPRESSED = "mate_suppressed_state"
MATE_LOSS_NOT_DRIVING = "mate_not_driving"
MATE_LOSS_KIND = "mate_kind_has_no_native_class"
MATE_LOSS_ALIGNMENT = "mate_alignment_has_no_native_code"
MATE_LOSS_ENTITY_MISSING = "mate_entity_missing"
MATE_LOSS_ENTITY_SELECTION = "mate_entity_carries_selection_id"
MATE_LOSS_ENTITY_REFERENCE = "mate_entity_reference_is_not_a_persistent_token"
MATE_LOSS_ENTITY_COMPONENT_PATH = "mate_entity_component_path_unresolved"
MATE_LOSS_NAME = "mate_name_exceeds_native_string_limit"
MATE_LOSS_RECORD_VERIFICATION = "mate_record_failed_redecode"
MATE_LOSS_LANE_CAPACITY = "mate_lane_record_capacity"
MATE_BLOCKING_LOSS_REASONS = frozenset(
    {
        MATE_LOSS_VALUE,
        MATE_LOSS_VALUE_MISSING,
    }
)
MATE_ADVISORY_LOSS_REASONS = frozenset(
    {
        MATE_LOSS_EXPRESSION,
        MATE_LOSS_ENTITY_FRAME,
        MATE_LOSS_ENTITY_RADIUS,
        MATE_LOSS_GROUP_NESTING,
        MATE_LOSS_GROUP_MEMBERSHIP,
        MATE_LOSS_ORPHAN_ENTITY,
    }
)
MATE_REJECTION_REASONS = frozenset(
    {
        MATE_LOSS_SUPPRESSED,
        MATE_LOSS_NOT_DRIVING,
        MATE_LOSS_KIND,
        MATE_LOSS_ALIGNMENT,
        MATE_LOSS_ENTITY_MISSING,
        MATE_LOSS_ENTITY_SELECTION,
        MATE_LOSS_ENTITY_REFERENCE,
        MATE_LOSS_ENTITY_COMPONENT_PATH,
        MATE_LOSS_NAME,
        MATE_LOSS_RECORD_VERIFICATION,
        MATE_LOSS_LANE_CAPACITY,
    }
)
MATE_LOSS_REASONS = (
    MATE_BLOCKING_LOSS_REASONS | MATE_ADVISORY_LOSS_REASONS | MATE_REJECTION_REASONS
)


@dataclass(frozen=True, slots=True)
class NativeMateType:
    code: int | None
    api_name: str
    kind: str
    class_names: tuple[str, ...] = ()
    name_prefixes: tuple[str, ...] = ()
    value_semantic: str = ""
    neutral_kind: str = ""


class NativeMateAlignmentCode(IntEnum):
    ANY = 0
    ALIGNED = 1
    ANTI_ALIGNED = 2
    CLOSEST = 3


@dataclass(frozen=True, slots=True)
class NativeMateAlignment:
    code: NativeMateAlignmentCode
    api_name: str
    kind: str


@dataclass(frozen=True, slots=True)
class NativeMateEntityType:
    code: int | None
    api_name: str
    kind: str
    markers: tuple[str, ...] = ()


NATIVE_MATE_TYPES = (
    NativeMateType(
        0,
        "swMateCOINCIDENT",
        "coincident",
        ("MateCoincident", "moMateCoincident"),
        ("coincident",),
    ),
    NativeMateType(
        1,
        "swMateCONCENTRIC",
        "concentric",
        ("MateConcentric", "moMateConcentric"),
        ("concentric",),
    ),
    NativeMateType(
        2,
        "swMatePERPENDICULAR",
        "perpendicular",
        ("MatePerpendicular", "moMatePerpendicular"),
        ("perpendicular",),
    ),
    NativeMateType(
        3,
        "swMatePARALLEL",
        "parallel",
        ("MateParallel", "moMateParallel"),
        ("parallel",),
    ),
    NativeMateType(
        4,
        "swMateTANGENT",
        "tangent",
        ("MateTangent", "moMateTangent"),
        ("tangent",),
    ),
    NativeMateType(
        5,
        "swMateDISTANCE",
        "distance",
        (
            "MateDistanceDim",
            "MateLimitDistanceDim",
            "moMateDistanceDim",
            "moMateDistanceDim_c",
            "moMateLimitDistanceDim",
            "moMateLimitDistanceDim_c",
        ),
        ("distance", "limitdistance"),
        "length",
    ),
    NativeMateType(
        6,
        "swMateANGLE",
        "angle",
        (
            "MateLimitAngleDim",
            "MatePlanarAngleDim",
            "moMateAngleDim_c",
            "moMateLimitAngleDim",
            "moMateLimitAngleDim_c",
            "moMatePlanarAngleDim",
            "moMatePlanarAngleDim_c",
        ),
        ("angle", "limitangle"),
        "angle",
    ),
    NativeMateType(7, "swMateUNKNOWN", "native"),
    NativeMateType(
        8,
        "swMateSYMMETRIC",
        "symmetric",
        ("MateSymmetric", "moMateSymmetric"),
        ("symmetric",),
    ),
    NativeMateType(
        9,
        "swMateCAMFOLLOWER",
        "cam_tangent",
        ("MateCamTangent", "moMateCamTangent"),
        ("cam", "cammatetangent", "camfollower"),
        neutral_kind="cam",
    ),
    NativeMateType(
        10,
        "swMateGEAR",
        "gear",
        ("MateGearDim", "moMateGearDim", "moMateGearDim_c"),
        ("gear", "gearmate"),
        "ratio",
    ),
    NativeMateType(
        11,
        "swMateWIDTH",
        "width",
        ("MateWidth", "moMateWidth"),
        ("width", "widthmate"),
    ),
    NativeMateType(
        12,
        "swMateLOCKTOSKETCH",
        "lock_to_sketch",
        ("moLockToSketchMate",),
        ("locktosketch", "locktosketchmate"),
        neutral_kind="lock",
    ),
    NativeMateType(
        13,
        "swMateRACKPINION",
        "rack_pinion",
        ("MateRackPinionDim", "moMateRackPinionDim", "moMateRackPinionDim_c"),
        ("rackpinion",),
        "length",
    ),
    NativeMateType(14, "swMateMAXMATES", "native"),
    NativeMateType(
        15,
        "swMatePATH",
        "path",
        ("MatePath", "moMatePath"),
        ("path", "pathmate"),
    ),
    NativeMateType(
        16,
        "swMateLOCK",
        "lock",
        ("MateInPlace", "MateLock", "moMateInPlace", "moMateLock"),
        ("inplace", "lock", "lockmate"),
    ),
    NativeMateType(
        17,
        "swMateSCREW",
        "screw",
        ("MateScrew", "moMateScrew", "moMateScrewDim_c"),
        ("screw", "screwmate"),
        "length",
    ),
    NativeMateType(
        18,
        "swMateLINEARCOUPLER",
        "linear_coupler",
        ("MateLinearCoupler", "moMateLinearCoupler"),
        ("linearcoupler",),
        "ratio",
    ),
    NativeMateType(
        19,
        "swMateUNIVERSALJOINT",
        "universal_joint",
        ("MateUniversalJoint", "moMateUniversalJoint"),
        ("universaljoint", "universalmate"),
    ),
    NativeMateType(
        20,
        "swMateCOORDINATE",
        "coordinate",
        ("MateCoordinate", "moMateCoordinate"),
        ("coordinate",),
    ),
    NativeMateType(
        21,
        "swMateSLOT",
        "slot",
        ("MateSlot", "moMateSlot"),
        ("slot", "slotmate"),
    ),
    NativeMateType(
        22,
        "swMateHINGE",
        "hinge",
        ("MateHinge", "moMateHinge"),
        ("hinge",),
    ),
    NativeMateType(
        23,
        "swMateSLIDER",
        "slider",
        ("MateSlider", "moMateSlider"),
        ("slider",),
    ),
    NativeMateType(
        24,
        "swMatePROFILECENTER",
        "profile_center",
        ("MateProfileCenter", "moMateProfileCenter"),
        ("profilecenter",),
    ),
    NativeMateType(
        25,
        "swMateMAGNETIC",
        "magnetic",
        ("MateMagnetic", "moMateMagnetic"),
        ("magnetic", "magneticmate"),
    ),
)
NATIVE_MATE_TYPE_EXTENSIONS = (
    NativeMateType(
        None,
        "BELT",
        "belt",
        ("moMateBeltDim_c",),
        ("beltmate",),
        "ratio",
    ),
    NativeMateType(
        None,
        "BELT_GROUP",
        "group",
        ("moBeltMateFolder_c",),
        ("beltmates",),
    ),
    NativeMateType(
        None,
        "MATE_REFERENCE_GROUP_FOLDER",
        "group",
        ("MateReferenceGroupFolder",),
    ),
)
NATIVE_MATE_TYPE_RECORDS = (*NATIVE_MATE_TYPES, *NATIVE_MATE_TYPE_EXTENSIONS)


def _classifier_map(
    records: Iterable[NativeMateType | NativeMateEntityType], attribute: str
) -> Mapping[str, str]:
    result: dict[str, str] = {}
    for record in records:
        for value in getattr(record, attribute):
            key = value.casefold()
            previous = result.get(key)
            if previous is not None and previous != record.kind:
                raise RuntimeError(f"conflicting classifier {value!r}")
            result[key] = record.kind
    return MappingProxyType(result)


_MATE_KIND_BY_CLASS = _classifier_map(NATIVE_MATE_TYPE_RECORDS, "class_names")
_MATE_KIND_BY_NAME = _classifier_map(NATIVE_MATE_TYPE_RECORDS, "name_prefixes")
MATE_VALUE_SEMANTICS = MappingProxyType(
    {
        record.kind: record.value_semantic
        for record in NATIVE_MATE_TYPE_RECORDS
        if record.value_semantic
    }
)
NATIVE_MATE_NEUTRAL_KIND_ALIASES = MappingProxyType(
    {
        record.kind: record.neutral_kind
        for record in NATIVE_MATE_TYPE_RECORDS
        if record.neutral_kind
    }
)

NATIVE_MATE_ALIGNMENTS = (
    NativeMateAlignment(
        NativeMateAlignmentCode.ANY,
        "swMateReferenceAlignment_Any",
        "unknown",
    ),
    NativeMateAlignment(
        NativeMateAlignmentCode.ALIGNED,
        "swMateReferenceAlignment_Aligned",
        "aligned",
    ),
    NativeMateAlignment(
        NativeMateAlignmentCode.ANTI_ALIGNED,
        "swMateReferenceAlignment_AntiAligned",
        "anti_aligned",
    ),
    NativeMateAlignment(
        NativeMateAlignmentCode.CLOSEST,
        "swMateReferenceAlignment_Closest",
        "closest",
    ),
)
NATIVE_MATE_ALIGNMENT_BY_CODE = {
    int(record.code): record for record in NATIVE_MATE_ALIGNMENTS
}

NATIVE_MATE_ENTITY_GEOMETRY_TYPES = (
    NativeMateEntityType(0, "swMateUnsupported", "native"),
    NativeMateEntityType(1, "swMatePoint", "point"),
    NativeMateEntityType(2, "swMateLine", "line"),
    NativeMateEntityType(3, "swMatePlane", "plane"),
    NativeMateEntityType(4, "swMateCylinder", "cylinder"),
    NativeMateEntityType(5, "swMateCone", "cone"),
    NativeMateEntityType(6, "swMateSphere", "sphere"),
    NativeMateEntityType(7, "swMateCircle", "circle"),
)

NATIVE_MATE_ENTITY_REFERENCE_TYPES = (
    NativeMateEntityType(
        0,
        "swMateEntity2ReferenceType_Point",
        "point",
        ("refpoint", "point"),
    ),
    NativeMateEntityType(1, "swMateEntity2ReferenceType_Line", "line", ("line",)),
    NativeMateEntityType(
        2,
        "swMateEntity2ReferenceType_Circle",
        "circle",
        ("circle",),
    ),
    NativeMateEntityType(
        3,
        "swMateEntity2ReferenceType_Plane",
        "plane",
        ("plane",),
    ),
    NativeMateEntityType(
        4,
        "swMateEntity2ReferenceType_Cylinder",
        "cylinder",
        ("cylinder", "wzdhole", "sweepside"),
    ),
    NativeMateEntityType(
        5,
        "swMateEntity2ReferenceType_Sphere",
        "sphere",
        ("sphere",),
    ),
    NativeMateEntityType(6, "swMateEntity2ReferenceType_Set", "native"),
    NativeMateEntityType(
        7,
        "swMateEntity2ReferenceType_Cone",
        "cone",
        ("cone",),
    ),
    NativeMateEntityType(
        8,
        "swMateEntity2ReferenceType_SweptSurface",
        "surface",
        ("sweptsurface",),
    ),
    NativeMateEntityType(
        9,
        "swMateEntity2ReferenceType_MultipleSurface",
        "surface",
        ("multiplesurface",),
    ),
    NativeMateEntityType(
        10,
        "swMateEntity2ReferenceType_GenSurface",
        "surface",
        ("gensurface", "generalsurface", "surface"),
    ),
    NativeMateEntityType(
        11,
        "swMateEntity2ReferenceType_Ellipse",
        "curve",
        ("ellipse",),
    ),
    NativeMateEntityType(
        12,
        "swMateEntity2ReferenceType_GeneralCurve",
        "curve",
        ("generalcurve", "curve"),
    ),
    NativeMateEntityType(13, "swMateEntity2ReferenceType_UNKNOWN", "native"),
)
NATIVE_MATE_ENTITY_TYPE_EXTENSIONS = (
    NativeMateEntityType(None, "SketchEntity", "sketch_entity", ("^",)),
    NativeMateEntityType(
        None, "CoordinateSystem", "coordinate_system", ("coordinatesystem", "coordsys")
    ),
    NativeMateEntityType(None, "Vertex", "vertex", ("vertex",)),
    NativeMateEntityType(None, "Axis", "axis", ("axis",)),
    NativeMateEntityType(None, "Edge", "edge", ("edge",)),
    NativeMateEntityType(None, "Face", "face", ("face", "surfidrep")),
)
NATIVE_MATE_ENTITY_TYPE_RECORDS = (
    NATIVE_MATE_ENTITY_TYPE_EXTENSIONS[0],
    *NATIVE_MATE_ENTITY_REFERENCE_TYPES,
    *NATIVE_MATE_ENTITY_TYPE_EXTENSIONS[1:],
)
NATIVE_MATE_ENTITY_KIND_BY_MARKER = _classifier_map(
    NATIVE_MATE_ENTITY_TYPE_RECORDS, "markers"
)
NATIVE_MATE_ENTITY_MARKERS = tuple(
    (marker.casefold(), record.kind)
    for record in NATIVE_MATE_ENTITY_TYPE_RECORDS
    for marker in record.markers
)


@dataclass(frozen=True, slots=True)
class NativeAssemblyFile:
    object_id: int
    document_type: str
    creation_time: int
    source_path: str


@dataclass(frozen=True, slots=True)
class NativeAssemblyDefinition:
    object_id: int
    name: str
    document_type: str
    file_id: int
    source_path: str
    configuration_name: str
    configuration_id: int
    alternate_configuration_name: str
    last_modified_stamp: int
    configuration_flags: int
    bounding_box_m: tuple[float, float, float, float, float, float] | None
    child_occurrence_ids: tuple[int, ...]
    attributes: tuple[tuple[str, str], ...]


@dataclass(frozen=True, slots=True)
class NativeAssemblyOccurrence:
    object_id: int
    feature_id: int
    owner_definition_id: int
    definition_id: int
    name: str
    reference_number: int
    component_reference: str
    configuration_name: str
    configuration_id: int
    transform: tuple[float, ...]
    transform_stamp: int
    suppressed: bool
    hidden: bool
    flexible: bool
    virtual: bool
    exclude_from_bom: bool
    zone: bool
    display_mode: int
    display_quality: int
    edges_in_shaded_mode: bool
    order: int
    attributes: tuple[tuple[str, str], ...]


@dataclass(frozen=True, slots=True)
class NativeAssemblyConfiguration:
    object_id: int
    configuration_id: int
    name: str
    reference: str
    model_id: int
    most_recent: bool
    needs_update: bool
    attributes: tuple[tuple[str, str], ...]


@dataclass(frozen=True, slots=True)
class NativeDisplayState:
    object_id: int
    name: str
    configuration_id: int | None
    attributes: tuple[tuple[str, str], ...]


@dataclass(frozen=True, slots=True)
class NativeMateEntity:
    component_path: str
    persistent_references: tuple[str, ...]
    source_path: str
    configuration_name: str


@dataclass(frozen=True, slots=True)
class NativeMateDimension:
    name: str
    value: float
    value_offset: int


@dataclass(frozen=True, slots=True)
class NativeMate:
    name: str
    kind: str
    owner_definition_id: int
    order: int
    entities: tuple[NativeMateEntity, ...]
    record_offset: int
    record_length: int
    class_name: str
    class_token: int | None
    serialized_strings: tuple[str, ...]
    alignment_code: int | None
    dimensions: tuple[NativeMateDimension, ...]

    @property
    def value_m(self) -> float | None:
        return (
            self.dimensions[0].value
            if self.kind == "distance" and self.dimensions
            else None
        )

    @property
    def value_offset(self) -> int | None:
        return (
            self.dimensions[0].value_offset
            if self.kind == "distance" and self.dimensions
            else None
        )


@dataclass(frozen=True, slots=True)
class NativeMateList:
    native_id: int
    declared_count: int
    owner_definition_id: int
    mates: tuple[NativeMate, ...]
    stream: str


@dataclass(frozen=True, slots=True)
class _MateRecord:
    name: str
    name_end: int
    start: int
    end: int
    class_name: str
    class_token: int | None
    strings: tuple[str, ...]
    alignment_code: int | None
    dimensions: tuple[NativeMateDimension, ...]


@dataclass(frozen=True, slots=True)
class NativeOccurrencePath:
    occurrence_id: int
    definition_id: int
    path: str
    depth: int


@dataclass(frozen=True, slots=True)
class NativeAssembly:
    name: str
    root_definition_id: int
    files: tuple[NativeAssemblyFile, ...]
    definitions: tuple[NativeAssemblyDefinition, ...]
    occurrences: tuple[NativeAssemblyOccurrence, ...]
    configurations: tuple[NativeAssemblyConfiguration, ...]
    display_states: tuple[NativeDisplayState, ...]
    occurrence_paths: tuple[NativeOccurrencePath, ...]
    mate_lists: tuple[NativeMateList, ...]
    display_components: tuple[NativeDisplayComponent, ...]
    application_version: int


@dataclass(frozen=True, slots=True)
class NativeMateStreamReport:
    streams: Mapping[str, bytes]
    complete: bool
    encoded_mate_ids: tuple[str, ...]
    unsupported_mate_ids: tuple[str, ...]
    losses: Mapping[str, tuple[str, ...]]
    unsupported_reasons: Mapping[str, tuple[str, ...]] = MappingProxyType({})


@dataclass(frozen=True, slots=True)
class NativeAssemblyEncoding:
    component_tree: bytes
    mate_streams: Mapping[str, bytes]
    definition_ids: Mapping[str, int]
    occurrence_ids: Mapping[str, int]
    structure_complete: bool
    mates_complete: bool
    unsupported_mate_ids: tuple[str, ...]
    generated_mate_ids: tuple[str, ...] = ()
    generated_mate_losses: Mapping[str, tuple[str, ...]] = MappingProxyType({})
    unsupported_mate_reasons: Mapping[str, tuple[str, ...]] = MappingProxyType({})


def encode_native_assembly(
    assembly: AssemblyData,
    configurations: Sequence[Configuration],
    model_name: str,
    bundle_names: Mapping[str, str] | None = None,
) -> NativeAssemblyEncoding:
    definitions = tuple(assembly.definitions)
    instances = tuple(assembly.instances)
    definition_by_id = {item.id: item for item in definitions}
    if assembly.root_definition_id not in definition_by_id:
        raise SldprtFormatError("assembly root definition is missing")
    selected_configurations = tuple(
        sorted(
            configurations,
            key=lambda item: (not item.active, configurations.index(item)),
        )
    )
    if not selected_configurations:
        raise SldprtFormatError("assembly contains no configuration")
    names = bundle_names or {}
    source_paths = {
        definition.id: _definition_source_path(
            definition,
            definition.id == assembly.root_definition_id,
            model_name,
            names,
        )
        for definition in definitions
    }
    file_keys = {
        definition.id: _definition_file_key(definition, source_paths[definition.id])
        for definition in definitions
    }
    unique_file_keys = tuple(dict.fromkeys(file_keys.values()))
    file_preferred = {
        key: next(
            (
                _positive_integer(definition.attributes.get("native_file_id"))
                for definition in definitions
                if file_keys[definition.id] == key
                and _positive_integer(definition.attributes.get("native_file_id"))
                is not None
            ),
            None,
        )
        for key in unique_file_keys
    }
    object_preferred: dict[tuple[str, str], int | None] = {}
    for configuration in selected_configurations:
        object_preferred[("configuration", configuration.id)] = _positive_integer(
            configuration.attributes.get("native_object_id")
        )
    for definition in definitions:
        object_preferred[("definition", definition.id)] = _preferred_native_id(
            definition.id,
            "sldasm:definition:",
            definition.attributes.get("native_object_id"),
        )
    for key in unique_file_keys:
        object_preferred[("file", repr(key))] = file_preferred[key]
    for instance in instances:
        object_preferred[("occurrence", instance.id)] = _preferred_native_id(
            instance.id,
            "sldasm:instance:",
            instance.attributes.get("native_object_id"),
        )
    object_ids = _allocate_object_ids(object_preferred)
    definition_ids = {
        definition.id: object_ids[("definition", definition.id)]
        for definition in definitions
    }
    file_ids = {key: object_ids[("file", repr(key))] for key in unique_file_keys}
    occurrence_ids = {
        instance.id: object_ids[("occurrence", instance.id)] for instance in instances
    }
    configuration_ids = {
        configuration.id: object_ids[("configuration", configuration.id)]
        for configuration in selected_configurations
    }
    root = ET.Element(
        "swSolidWorks",
        {
            "xmlns": "http://www.solidworks.com/sw2003/schema",
            "swObjCount": str(max(object_ids.values(), default=0)),
            "swVersion": "13000",
        },
    )
    header = ET.SubElement(
        root,
        "swHeader",
        {"swObjCount": str(len(unique_file_keys))},
    )
    for key in unique_file_keys:
        definition = next(item for item in definitions if file_keys[item.id] == key)
        ET.SubElement(
            header,
            "swFile",
            {
                "id": str(file_ids[key]),
                "swDocType": _definition_document_type(definition),
                "swCreationTime": str(
                    _integer_attribute(definition, "native_creation_time", 0)
                ),
                "swPath": source_paths[definition.id],
            },
        )
    model_list = ET.SubElement(
        root,
        "swModelList",
        {"swObjCount": str(len(definitions))},
    )
    children: dict[str, list[tuple[int, ComponentInstance]]] = {}
    for index, instance in enumerate(instances):
        children.setdefault(instance.owner_definition_id, []).append((index, instance))
    for definition in definitions:
        attributes = {
            "id": str(definition_ids[definition.id]),
            "swName": definition.name,
            "swConfigurationName": definition.configuration_name or "Default",
            "swConfigurationId": str(
                _configuration_integer(definition.configuration_id)
            ),
            "swLastModifiedStamp": str(
                _integer_attribute(definition, "last_modified_stamp", 0)
            ),
            "swConfigurationFlags": str(
                _integer_attribute(definition, "configuration_flags", 0)
            ),
            "swFileRef": str(file_ids[file_keys[definition.id]]),
        }
        alternate = definition.attributes.get("alternate_configuration_name")
        if isinstance(alternate, str) and alternate:
            attributes["swConfigurationAlternateName"] = alternate
        bounding_box = _native_bounding_box(definition)
        if bounding_box:
            attributes["swBoundingBox"] = bounding_box
        if definition.id == assembly.root_definition_id:
            attributes["swAssemblyFeatureEffectedComponents"] = ""
        model = ET.SubElement(model_list, "swModel", attributes)
        owned = sorted(
            children.get(definition.id, ()),
            key=lambda item: (item[1].order, item[0]),
        )
        for index, instance in owned:
            target = definition_by_id.get(instance.definition_id)
            if target is None:
                continue
            reference_number = _reference_number(instance, index + 1)
            ET.SubElement(
                model,
                "swReference",
                {
                    "id": str(occurrence_ids[instance.id]),
                    "swName": _instance_base_name(instance, reference_number),
                    "swReferenceNumber": str(reference_number),
                    "swComponentReference": str(
                        instance.attributes.get("component_reference", "")
                    ),
                    "swID": str(_native_feature_id(instance, index)),
                    "swIsVirtualComponent": _yes_text(
                        bool(instance.attributes.get("virtual", False))
                    ),
                    "swConfigurationId": str(
                        _configuration_integer(instance.configuration_id)
                    ),
                    "swConfigurationName": instance.configuration_name
                    or target.configuration_name
                    or "Default",
                    "swDisplayMode": str(
                        _integer_attribute(instance, "display_mode", 6)
                    ),
                    "swHlrDisplayQuality": str(
                        _integer_attribute(instance, "display_quality", 1)
                    ),
                    "swSuppressed": _yes_text(instance.suppressed),
                    "swHidden": _yes_text(instance.hidden),
                    "swEdgesInShadedMode": _yes_text(
                        bool(instance.attributes.get("edges_in_shaded_mode", False))
                    ),
                    "swFlexible": _yes_text(instance.flexible),
                    "swExcludeFromBOM": _yes_text(instance.exclude_from_bom),
                    "swZone": _yes_text(bool(instance.attributes.get("zone", False))),
                    "swModelRef": str(definition_ids[target.id]),
                    "swTransform": " ".join(
                        format(value, ".17g")
                        for value in _native_matrix(instance.transform)
                    ),
                    "swTransformStamp": str(
                        _integer_attribute(instance, "transform_stamp", 0)
                    ),
                },
            )
    configuration_list = ET.SubElement(
        root,
        "swConfigurationList",
        {"swObjCount": str(len(selected_configurations))},
    )
    for configuration in selected_configurations:
        ET.SubElement(
            configuration_list,
            "swConfiguration",
            {
                "id": str(configuration_ids[configuration.id]),
                "swName": configuration.name,
                "swID": str(
                    _configuration_integer(
                        configuration.attributes.get("native_configuration_id", 0)
                    )
                ),
                "swReference": definition_by_id[assembly.root_definition_id].name,
                "swMostRecentConfiguration": _yes_text(configuration.active),
                "swConfigurationNeedsUpdate": "NO",
                "swModelRef": str(definition_ids[assembly.root_definition_id]),
            },
        )
    ET.SubElement(root, "swExtFeatureList", {"swObjCount": "0"})
    mates = _encode_mate_streams(
        assembly,
        definitions,
        definition_by_id,
        definition_ids,
    )
    component_tree = ET.tostring(
        root,
        encoding="utf-8",
        xml_declaration=True,
        short_empty_elements=True,
    )
    structure_complete = all(
        _definition_supported(definition) for definition in definitions
    ) and all(
        instance.definition_id in definition_by_id
        and instance.owner_definition_id in definition_by_id
        for instance in instances
    )
    return NativeAssemblyEncoding(
        component_tree=component_tree,
        mate_streams=mates.streams,
        definition_ids=MappingProxyType(definition_ids),
        occurrence_ids=MappingProxyType(occurrence_ids),
        structure_complete=structure_complete,
        mates_complete=mates.complete,
        unsupported_mate_ids=mates.unsupported_mate_ids,
        generated_mate_ids=mates.encoded_mate_ids,
        generated_mate_losses=mates.losses,
        unsupported_mate_reasons=mates.unsupported_reasons,
    )


def _definition_supported(definition: ComponentDefinition) -> bool:
    return str(definition.kind) in {
        ComponentKind.PART.value,
        ComponentKind.ASSEMBLY.value,
    }


def _definition_document_type(definition: ComponentDefinition) -> str:
    return (
        "ASSEMBLY" if str(definition.kind) == ComponentKind.ASSEMBLY.value else "PART"
    )


def _definition_source_path(
    definition: ComponentDefinition,
    root: bool,
    model_name: str,
    bundle_names: Mapping[str, str],
) -> str:
    suffix = (
        ".SLDASM"
        if root or _definition_document_type(definition) == "ASSEMBLY"
        else ".SLDPRT"
    )
    if root:
        stem = PureWindowsPath(model_name).stem or definition.name or "Assembly"
        return f"{_file_stem(stem)}{suffix}"
    bundled = bundle_names.get(definition.document_id) or bundle_names.get(
        definition.id
    )
    if isinstance(bundled, str) and bundled:
        return bundled
    for candidate in (
        definition.attributes.get("native_source_path"),
        definition.source_path,
    ):
        if not isinstance(candidate, str) or not candidate:
            continue
        if PureWindowsPath(candidate).suffix.casefold() == suffix.casefold():
            return candidate
    return f"{_file_stem(definition.name or definition.id)}{suffix}"


def _file_stem(value: str) -> str:
    result = "".join(
        "_" if character in '<>:"/\\|?*' else character for character in value
    ).strip(" .")
    return result or "Component"


def _definition_file_key(
    definition: ComponentDefinition, source_path: str
) -> tuple[str, str | int, str]:
    native_id = _positive_integer(definition.attributes.get("native_file_id"))
    if native_id is not None:
        return "native", native_id, _definition_document_type(definition)
    return (
        "path",
        source_path.casefold(),
        _definition_document_type(definition),
    )


def _preferred_native_id(value: str, prefix: str, attribute: Any) -> int | None:
    native = _positive_integer(attribute)
    if native is not None:
        return native
    if not value.startswith(prefix):
        return None
    return _positive_integer(value.removeprefix(prefix).split(":", 1)[0])


def _positive_integer(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    try:
        result = int(value)
    except (TypeError, ValueError):
        return None
    return result if 0 < result <= 0x7FFFFFFF else None


def _allocate_object_ids(
    preferred: Mapping[tuple[str, str], int | None],
) -> dict[tuple[str, str], int]:
    counts: dict[int, int] = {}
    for value in preferred.values():
        if value is not None:
            counts[value] = counts.get(value, 0) + 1
    reserved = {value for value, count in counts.items() if count == 1}
    result: dict[tuple[str, str], int] = {}
    used: set[int] = set()
    candidate = 1
    for key, value in preferred.items():
        if value in reserved:
            result[key] = value
            used.add(value)
            continue
        while candidate in used or candidate in reserved:
            candidate += 1
        result[key] = candidate
        used.add(candidate)
        candidate += 1
    return result


def _integer_attribute(
    item: ComponentDefinition | ComponentInstance,
    name: str,
    default: int,
) -> int:
    value = item.attributes.get(name, default)
    if isinstance(value, bool):
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _configuration_integer(value: Any) -> int:
    if isinstance(value, bool):
        return 0
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _native_bounding_box(definition: ComponentDefinition) -> str:
    box = definition.bounding_box
    if box is None:
        return ""
    values = (
        box.minimum.x,
        box.minimum.y,
        box.minimum.z,
        box.maximum.x,
        box.maximum.y,
        box.maximum.z,
    )
    if not all(math.isfinite(value) for value in values):
        raise SldprtFormatError("component bounding box contains a non-finite value")
    return " ".join(format(value / 1000.0, ".17g") for value in values)


def _reference_number(instance: ComponentInstance, fallback: int) -> int:
    value = _positive_integer(instance.reference_number)
    if value is not None:
        return value
    match = re.search(r"-(\d+)$", instance.name)
    if match is not None:
        value = _positive_integer(match.group(1))
        if value is not None:
            return value
    native = _positive_integer(instance.attributes.get("native_reference_number"))
    return native or fallback


def _instance_base_name(instance: ComponentInstance, reference_number: int) -> str:
    suffix = f"-{reference_number}"
    return (
        instance.name[: -len(suffix)]
        if instance.name.endswith(suffix)
        else instance.name
    )


def _native_feature_id(instance: ComponentInstance, index: int) -> int:
    value = _positive_integer(instance.attributes.get("native_feature_id"))
    if value is not None:
        return value
    return 24 if instance.fixed else 25 + index


def _native_matrix(matrix: Matrix4) -> tuple[float, ...]:
    values = matrix.values
    if len(values) != 16 or not all(math.isfinite(value) for value in values):
        raise SldprtFormatError("component transform contains a non-finite value")
    return (
        values[0],
        values[4],
        values[8],
        values[12],
        values[1],
        values[5],
        values[9],
        values[13],
        values[2],
        values[6],
        values[10],
        values[14],
        values[3] / 1000.0,
        values[7] / 1000.0,
        values[11] / 1000.0,
        values[15],
    )


def _yes_text(value: bool) -> str:
    return "YES" if value else "NO"


def _encode_mate_streams(
    assembly: AssemblyData,
    ordered_definitions: Sequence[ComponentDefinition],
    definitions: Mapping[str, ComponentDefinition],
    definition_ids: Mapping[str, int],
) -> NativeMateStreamReport:
    if not assembly.mates and not assembly.mate_entities and not assembly.mate_groups:
        return NativeMateStreamReport(
            MappingProxyType({}), True, (), (), MappingProxyType({})
        )
    entities = {entity.id: entity for entity in assembly.mate_entities}
    losses: dict[str, tuple[str, ...]] = {}
    rejections: dict[str, tuple[str, ...]] = {}
    referenced = {entity_id for mate in assembly.mates for entity_id in mate.entity_ids}
    for entity_id in sorted(set(entities) - referenced):
        losses[entity_id] = (MATE_LOSS_ORPHAN_ENTITY,)
    lanes = _mate_stream_lanes(assembly, ordered_definitions, definitions)
    streams: dict[str, bytes] = {}
    encoded: list[str] = []
    unsupported: list[str] = []
    for owner_id, lane in lanes.items():
        records: list[bytes] = []
        layout: list[tuple[str, MateConstraint | MateGroup]] = []
        for item in _mate_owner_plan(assembly, owner_id, losses):
            if isinstance(item, MateGroup):
                pair = _encode_group_records(item)
                if pair is None:
                    losses[item.id] = _with_reason(
                        losses.get(item.id, ()), MATE_LOSS_GROUP_MEMBERSHIP
                    )
                    continue
                records.extend(pair)
                layout.extend((("group_start", item), ("group_end", item)))
                continue
            record, reasons = _encode_mate_record(item, entities, assembly, definitions)
            if record is None:
                unsupported.append(item.id)
                rejections[item.id] = reasons
                continue
            records.append(record)
            layout.append(("mate", item))
            if reasons:
                losses[item.id] = _merged_reasons(losses.get(item.id, ()), reasons)
        planned = tuple(item.id for role, item in layout if role == "mate")
        if not planned or len(records) > 0xFFFF:
            unsupported.extend(planned)
            for mate_id in planned:
                rejections[mate_id] = (MATE_LOSS_LANE_CAPACITY,)
            continue
        stream_name = f"Contents/Config-{lane}-MatesList"
        native_id = (definition_ids[owner_id] | _MATE_LIST_NATIVE_ID_FLAG) & 0xFFFFFFFF
        stream = struct.pack("<IH", native_id, len(records)) + b"".join(records)
        if not _verify_mate_stream(
            stream,
            stream_name,
            definition_ids[owner_id],
            layout,
            entities,
            assembly,
            definitions,
            losses,
        ):
            unsupported.extend(planned)
            for mate_id in planned:
                rejections[mate_id] = (MATE_LOSS_RECORD_VERIFICATION,)
            continue
        streams[stream_name] = stream
        encoded.extend(planned)
    blocking = any(
        reason in MATE_BLOCKING_LOSS_REASONS
        for reasons in losses.values()
        for reason in reasons
    )
    complete = (
        not unsupported
        and not blocking
        and len(encoded) == len(assembly.mates)
        and bool(assembly.mates) == bool(streams)
    )
    return NativeMateStreamReport(
        MappingProxyType(streams),
        complete,
        tuple(encoded),
        tuple(dict.fromkeys(unsupported)),
        MappingProxyType(dict(sorted(losses.items()))),
        MappingProxyType(dict(sorted(rejections.items()))),
    )


def _with_reason(reasons: tuple[str, ...], reason: str) -> tuple[str, ...]:
    return tuple(dict.fromkeys((*reasons, reason)))


def _merged_reasons(reasons: tuple[str, ...], added: Iterable[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys((*reasons, *added)))


def _mate_stream_lanes(
    assembly: AssemblyData,
    ordered_definitions: Sequence[ComponentDefinition],
    definitions: Mapping[str, ComponentDefinition],
) -> dict[str, int]:
    owners = [
        owner
        for owner in dict.fromkeys(
            (
                assembly.root_definition_id,
                *(mate.owner_definition_id for mate in assembly.mates),
                *(group.owner_definition_id for group in assembly.mate_groups),
            )
        )
        if owner in definitions
    ]
    order = {
        definition.id: index for index, definition in enumerate(ordered_definitions)
    }
    remaining = sorted(
        (owner for owner in owners if owner != assembly.root_definition_id),
        key=lambda value: (order.get(value, len(order)), value),
    )
    result = {assembly.root_definition_id: 0}
    for lane, owner in enumerate(remaining, start=1):
        result[owner] = lane
    return result


def _mate_owner_plan(
    assembly: AssemblyData,
    owner_id: str,
    losses: dict[str, tuple[str, ...]],
) -> tuple[MateConstraint | MateGroup, ...]:
    mates = {
        mate.id: mate for mate in assembly.mates if mate.owner_definition_id == owner_id
    }
    ordered_mates = tuple(
        item[1]
        for item in sorted(
            enumerate(mates.values()),
            key=lambda item: (item[1].order, item[0]),
        )
    )
    groups = tuple(
        item[1]
        for item in sorted(
            enumerate(
                group
                for group in assembly.mate_groups
                if group.owner_definition_id == owner_id
            ),
            key=lambda item: (item[1].order, item[0]),
        )
    )
    assigned: dict[str, list[str]] = {}
    claimed: set[str] = set()
    for group in groups:
        if group.parent_group_id:
            losses[group.id] = _with_reason(
                losses.get(group.id, ()), MATE_LOSS_GROUP_NESTING
            )
        members: list[str] = []
        for mate_id in group.mate_ids:
            if mate_id not in mates or mate_id in claimed:
                losses[group.id] = _with_reason(
                    losses.get(group.id, ()), MATE_LOSS_GROUP_MEMBERSHIP
                )
                continue
            claimed.add(mate_id)
            members.append(mate_id)
        assigned[group.id] = members
    plan: list[MateConstraint | MateGroup] = [
        mate for mate in ordered_mates if mate.id not in claimed
    ]
    for group in groups:
        plan.append(group)
        plan.extend(mates[mate_id] for mate_id in assigned[group.id])
    return tuple(plan)


def _verify_mate_stream(
    stream: bytes,
    stream_name: str,
    owner_native_id: int,
    layout: Sequence[tuple[str, MateConstraint | MateGroup]],
    entities: Mapping[str, MateEntity],
    assembly: AssemblyData,
    definitions: Mapping[str, ComponentDefinition],
    losses: dict[str, tuple[str, ...]],
) -> bool:
    try:
        decoded = decode_mate_list(stream, stream_name, owner_native_id)
    except SldprtFormatError:
        return False
    if len(decoded.mates) != len(layout):
        return False
    for (role, source), target in zip(layout, decoded.mates):
        if role == "mate":
            if not isinstance(source, MateConstraint) or not _encoded_mate_matches(
                source, target, entities, assembly, definitions
            ):
                return False
            continue
        expected_name = (
            source.name
            if role == "group_start"
            else f"{source.name}{_MATE_GROUP_END_SUFFIX}"
        )
        if target.kind != "group" or target.name != expected_name:
            return False
    expected = _expected_group_members(layout)
    actual = _decoded_group_members(decoded)
    for order, group in expected.items():
        if actual.get(order, ()) != group[1]:
            losses[group[0].id] = _with_reason(
                losses.get(group[0].id, ()), MATE_LOSS_GROUP_MEMBERSHIP
            )
    return True


def _expected_group_members(
    layout: Sequence[tuple[str, MateConstraint | MateGroup]],
) -> dict[int, tuple[MateGroup, tuple[int, ...]]]:
    result: dict[int, tuple[MateGroup, tuple[int, ...]]] = {}
    starts = [index for index, (role, _) in enumerate(layout) if role == "group_start"]
    for position, index in enumerate(starts):
        group = layout[index][1]
        if not isinstance(group, MateGroup):
            continue
        limit = starts[position + 1] if position + 1 < len(starts) else len(layout)
        result[index] = (
            group,
            tuple(range(index + 2, limit)),
        )
    return result


def _decoded_group_members(decoded: NativeMateList) -> dict[int, tuple[int, ...]]:
    records = decoded.mates
    markers = tuple(record for record in records if record.kind == "group")
    result: dict[int, tuple[int, ...]] = {}
    for pair_index in range(0, len(markers) - 1, 2):
        marker = markers[pair_index]
        end = markers[pair_index + 1]
        limit = (
            markers[pair_index + 2].order
            if pair_index + 2 < len(markers)
            else len(records)
        )
        members: list[int] = []
        for candidate in records:
            if (
                candidate.order <= end.order
                or candidate.order >= limit
                or candidate.kind == "group"
            ):
                continue
            members.append(candidate.order)
            if candidate.kind == "lock_to_sketch":
                break
        result[marker.order] = tuple(members)
    return result


def _encode_group_records(group: MateGroup) -> tuple[bytes, bytes] | None:
    class_name = _native_group_class(group)
    start = _encode_record_body(group.name, class_name, 0)
    end = _encode_record_body(f"{group.name}{_MATE_GROUP_END_SUFFIX}", class_name, 0)
    if start is None or end is None:
        return None
    return start, end


def _native_group_class(group: MateGroup) -> str:
    candidates = tuple(
        record
        for record in NATIVE_MATE_TYPE_RECORDS
        if record.kind == "group" and record.class_names
    )
    requested = group.attributes.get("native_class_name")
    if isinstance(requested, str):
        for record in candidates:
            if requested in record.class_names:
                return requested
    lowered = group.name.casefold()
    for record in candidates:
        if any(lowered.startswith(prefix) for prefix in record.name_prefixes):
            return record.class_names[0]
    return candidates[0].class_names[0]


def _encode_record_body(name: str, class_name: str, entity_count: int) -> bytes | None:
    serialized_name = _serialized_string(name)
    if serialized_name is None:
        return None
    try:
        encoded_class = class_name.encode("ascii")
    except UnicodeEncodeError:
        return None
    record = bytearray(
        CLASS_MARKER
        + struct.pack("<H", len(encoded_class))
        + encoded_class
        + struct.pack("<H", _MATE_OBJECT_PREFIX)
        + serialized_name
    )
    body = bytearray(_MATE_RECORD_BODY_SIZE)
    struct.pack_into("<I", body, _MATE_ENTITY_COUNT_OFFSET, entity_count)
    record.extend(body)
    return bytes(record)


def _encode_mate_record(
    mate: MateConstraint,
    entities: Mapping[str, MateEntity],
    assembly: AssemblyData,
    definitions: Mapping[str, ComponentDefinition],
) -> tuple[bytes | None, tuple[str, ...]]:
    if mate.suppressed:
        return None, (MATE_LOSS_SUPPRESSED,)
    if not mate.driving:
        return None, (MATE_LOSS_NOT_DRIVING,)
    native_kind, class_name = _native_mate_class(mate)
    if not class_name:
        return None, (MATE_LOSS_KIND,)
    reasons: list[str] = [MATE_LOSS_EXPRESSION] if mate.parameter_ids else []
    entity_values: list[str] = []
    for entity_id in mate.entity_ids:
        entity = entities.get(entity_id)
        if entity is None or entity.owner_definition_id != mate.owner_definition_id:
            return None, (MATE_LOSS_ENTITY_MISSING,)
        values, entity_reasons = _mate_entity_strings(entity, assembly, definitions)
        if values is None:
            return None, entity_reasons
        entity_values.extend(values)
        reasons.extend(entity_reasons)
    alignment_code = _mate_alignment_code(mate.alignment)
    if alignment_code is None:
        return None, (MATE_LOSS_ALIGNMENT,)
    dimensions, value_reasons = _mate_dimension_values(mate, native_kind)
    reasons.extend(value_reasons)
    record = bytearray(
        _encode_record_body(mate.name, class_name, len(mate.entity_ids)) or b""
    )
    if not record:
        return None, (MATE_LOSS_NAME,)
    struct.pack_into(
        "<H",
        record,
        len(record) - _MATE_RECORD_BODY_SIZE + _MATE_ALIGNMENT_OFFSET,
        alignment_code,
    )
    for value in entity_values:
        serialized = _serialized_string(value)
        if serialized is None:
            return None, (MATE_LOSS_ENTITY_REFERENCE,)
        record.extend(serialized)
    for name, value in dimensions:
        serialized = _serialized_string(name)
        if serialized is None:
            return None, (MATE_LOSS_NAME,)
        record.extend(serialized)
        record.extend(DIMENSION_SCALAR_HEADERS[0])
        record.extend(struct.pack("<d", value))
    return bytes(record), tuple(dict.fromkeys(reasons))


def _native_mate_class(mate: MateConstraint) -> tuple[str, str]:
    neutral = str(mate.kind)
    requested = mate.attributes.get("native_kind")
    candidates = tuple(
        record
        for record in NATIVE_MATE_TYPE_RECORDS
        if record.class_names and (record.neutral_kind or record.kind) == neutral
    )
    if isinstance(requested, str):
        selected = next(
            (record for record in candidates if record.kind == requested), None
        )
        if selected is not None:
            class_name = mate.attributes.get("native_class_name")
            if isinstance(class_name, str) and class_name in selected.class_names:
                return selected.kind, class_name
            return selected.kind, selected.class_names[0]
    if not candidates:
        return "", ""
    return candidates[0].kind, candidates[0].class_names[0]


def _mate_entity_strings(
    entity: MateEntity,
    assembly: AssemblyData,
    definitions: Mapping[str, ComponentDefinition],
) -> tuple[tuple[str, ...] | None, tuple[str, ...]]:
    if entity.selection_id:
        return None, (MATE_LOSS_ENTITY_SELECTION,)
    reasons: list[str] = []
    if entity.frame is not None and not _is_identity_matrix(entity.frame):
        reasons.append(MATE_LOSS_ENTITY_FRAME)
    if entity.radius is not None:
        reasons.append(MATE_LOSS_ENTITY_RADIUS)
    persistent = entity.attributes.get("persistent_references")
    if isinstance(persistent, tuple) and all(
        isinstance(value, str) for value in persistent
    ):
        references = persistent
    elif entity.source_entity_id:
        references = (entity.source_entity_id,)
    else:
        return None, (MATE_LOSS_ENTITY_REFERENCE,)
    if not references or references[-1] != entity.source_entity_id:
        return None, (MATE_LOSS_ENTITY_REFERENCE,)
    component_path = _native_component_path(
        entity.instance_path,
        assembly,
        definitions,
        entity.owner_definition_id,
    )
    if component_path is None:
        return None, (MATE_LOSS_ENTITY_COMPONENT_PATH,)
    values: list[str] = []
    if component_path:
        if all(value.casefold().startswith("mo") for value in references):
            values.extend(references)
            values.append(component_path)
        elif all("@" in value and "^" not in value for value in references):
            values.append(component_path)
            values.extend(references)
        else:
            return None, (MATE_LOSS_ENTITY_REFERENCE,)
    else:
        if not all(
            value.casefold().startswith("mo") or ("^" in value and "@" in value)
            for value in references
        ):
            return None, (MATE_LOSS_ENTITY_REFERENCE,)
        values.extend(references)
    source_path = entity.attributes.get("source_path")
    if isinstance(source_path, str) and source_path:
        values.append(source_path)
    return tuple(values), tuple(dict.fromkeys(reasons))


def _is_identity_matrix(matrix: Matrix4) -> bool:
    return matrix.values == Matrix4().values


def _native_component_path(
    path: Sequence[str],
    assembly: AssemblyData,
    definitions: Mapping[str, ComponentDefinition],
    owner_definition_id: str = "",
) -> str | None:
    if not path:
        return ""
    instances = {instance.id: instance for instance in assembly.instances}
    result: list[str] = []
    owner_id = owner_definition_id or assembly.root_definition_id
    for index, instance_id in enumerate(path):
        instance = instances.get(instance_id)
        owner = definitions.get(owner_id)
        if (
            instance is None
            or owner is None
            or instance.owner_definition_id != owner_id
        ):
            return None
        reference_number = _reference_number(instance, index + 1)
        result.append(
            f"{_instance_base_name(instance, reference_number)}-{reference_number}@{owner.name}"
        )
        owner_id = instance.definition_id
    return "/".join(result)


def _mate_alignment_code(value: MateAlignment | str) -> int | None:
    kind = str(value)
    return next(
        (int(record.code) for record in NATIVE_MATE_ALIGNMENTS if record.kind == kind),
        None,
    )


def _mate_dimension_values(
    mate: MateConstraint, native_kind: str
) -> tuple[tuple[tuple[str, float], ...], tuple[str, ...]]:
    if MATE_VALUE_SEMANTICS.get(native_kind) is not None and mate.value is None:
        return (), (MATE_LOSS_VALUE_MISSING,)
    resolved = _resolved_mate_dimensions(mate, native_kind)
    if resolved is None:
        return (), (MATE_LOSS_VALUE,)
    return resolved, ()


def _resolved_mate_dimensions(
    mate: MateConstraint, native_kind: str
) -> tuple[tuple[str, float], ...] | None:
    semantic = MATE_VALUE_SEMANTICS.get(native_kind)
    if semantic is None:
        return () if mate.value is None else None
    value = mate.value
    if (
        value is None
        or isinstance(value.value, bool)
        or not isinstance(value.value, (int, float))
    ):
        return None
    number = float(value.value)
    if not math.isfinite(number):
        return None
    dimensions = mate.attributes.get("native_dimensions")
    names = (
        tuple(
            item.get("name", "")
            for item in dimensions
            if isinstance(item, Mapping) and isinstance(item.get("name", ""), str)
        )
        if isinstance(dimensions, tuple)
        else ()
    )
    first_name = names[0] if names and names[0] else "D1"
    if semantic == "length" and value.kind is ValueKind.LENGTH:
        factor = {"": 1.0, "mm": 1.0, "cm": 10.0, "m": 1000.0, "in": 25.4}.get(
            value.unit.casefold()
        )
        return ((first_name, number * factor / 1000.0),) if factor is not None else None
    if semantic == "angle" and value.kind is ValueKind.ANGLE:
        factor = {"": 1.0, "rad": 1.0, "deg": math.pi / 180.0}.get(
            value.unit.casefold()
        )
        return ((first_name, number * factor),) if factor is not None else None
    if semantic == "ratio" and value.kind is ValueKind.NUMBER:
        denominator = 1.0
        if isinstance(dimensions, tuple) and len(dimensions) >= 2:
            candidate = dimensions[1]
            if isinstance(candidate, Mapping) and isinstance(
                candidate.get("value"), (int, float)
            ):
                denominator = float(candidate["value"])
        if not math.isfinite(denominator) or denominator == 0.0:
            return None
        second_name = names[1] if len(names) > 1 and names[1] else "D2"
        return ((first_name, number * denominator), (second_name, denominator))
    return None


def _serialized_string(value: str) -> bytes | None:
    encoded = value.encode("utf-16le")
    units = len(encoded) // 2
    if units > 0xFE:
        return None
    return SERIALIZED_STRING_MARKER + bytes((units,)) + encoded


def _encoded_mate_matches(
    source: MateConstraint,
    target: NativeMate,
    entities: Mapping[str, MateEntity],
    assembly: AssemblyData,
    definitions: Mapping[str, ComponentDefinition],
) -> bool:
    native_kind, _ = _native_mate_class(source)
    if target.name != source.name or target.kind != native_kind:
        return False
    expected_entities: list[tuple[str, str]] = []
    for entity_id in source.entity_ids:
        entity = entities.get(entity_id)
        if entity is None:
            return False
        component_path = _native_component_path(
            entity.instance_path,
            assembly,
            definitions,
            entity.owner_definition_id,
        )
        expected_entities.append((component_path or "", entity.source_entity_id))
    actual_entities = [
        (
            entity.component_path,
            entity.persistent_references[-1] if entity.persistent_references else "",
        )
        for entity in target.entities
    ]
    if actual_entities != expected_entities:
        return False
    expected_alignment = _mate_alignment_code(source.alignment)
    if len(source.entity_ids) == 2 and target.alignment_code != expected_alignment:
        return False
    dimensions, _ = _mate_dimension_values(source, native_kind)
    if len(dimensions) != len(target.dimensions):
        return False
    return all(
        expected_name == actual.name
        and math.isclose(expected_value, actual.value, rel_tol=1e-12, abs_tol=1e-12)
        for (expected_name, expected_value), actual in zip(
            dimensions, target.dimensions
        )
    )


def decode_native_assembly(
    archive: SldprtArchive, *, include_tessellation: bool = False
) -> NativeAssembly:
    root = _xml_root(archive.require(COMPONENT_TREE_STREAM))
    files = _files(root)
    file_by_id = {item.object_id: item for item in files}
    definitions, occurrences = _models(root, file_by_id)
    configurations = _configurations(root)
    if not configurations:
        raise SldprtFormatError("assembly contains no configuration")
    root_definition_id = configurations[0].model_id
    definition_by_id = {item.object_id: item for item in definitions}
    if root_definition_id not in definition_by_id:
        raise SldprtFormatError("assembly configuration references a missing model")
    occurrence_paths = expand_occurrence_paths(
        root_definition_id, definitions, occurrences
    )
    mate_lists = _mate_lists(archive, root_definition_id)
    display_components: tuple[NativeDisplayComponent, ...] = ()
    display = archive.get(DISPLAY_LISTS_STREAM)
    if include_tessellation and display:
        display_components = decode_display_lists(display)
    return NativeAssembly(
        name=definition_by_id[root_definition_id].name,
        root_definition_id=root_definition_id,
        files=files,
        definitions=definitions,
        occurrences=occurrences,
        configurations=configurations,
        display_states=_display_states(root),
        occurrence_paths=occurrence_paths,
        mate_lists=mate_lists,
        display_components=display_components,
        application_version=_integer(root.attrib.get("swVersion")),
    )


def decode_mate_list(
    data: bytes, stream: str = "", owner_definition_id: int = 0
) -> NativeMateList:
    if len(data) < 6:
        raise SldprtFormatError(f"mate stream is truncated: {stream}")
    native_id, declared_count = struct.unpack_from("<IH", data, 0)
    class_offset = data.find(CLASS_MARKER, 6)
    if class_offset < 0 or class_offset + 6 > len(data):
        raise SldprtFormatError(f"mate stream has no class table: {stream}")
    class_size = struct.unpack_from("<H", data, class_offset + 4)[0]
    class_end = class_offset + 6 + class_size
    if class_end + 5 > len(data):
        raise SldprtFormatError(f"mate class record is truncated: {stream}")
    object_prefix = data[class_end : class_end + 2]
    name_prefix = object_prefix + SERIALIZED_STRING_MARKER
    serialized = _prefixed_strings(data, name_prefix)
    scalar_tokens = {
        token
        for offset, _, name_end in serialized
        if dimension_scalar_value_offset(data, name_end, len(data)) is not None
        for token in (_class_reference_token(data, offset - 2),)
        if token is not None
    }
    candidates = [
        item
        for item in serialized
        if dimension_scalar_value_offset(data, item[2], len(data)) is None
        and _class_reference_token(data, item[0] - 2) not in scalar_tokens
    ]
    if len(candidates) != declared_count:
        raise SldprtFormatError(
            f"mate count mismatch in {stream}: expected {declared_count}, decoded {len(candidates)}"
        )
    starts = [_mate_record_start(data, offset) for offset, _, _ in candidates]
    records: list[_MateRecord] = []
    for order, ((_, name, name_end), start) in enumerate(zip(candidates, starts)):
        end = starts[order + 1] if order + 1 < len(starts) else len(data)
        strings = _record_strings(data, start, end)
        class_name = _inline_class_name(data, start)
        records.append(
            _MateRecord(
                name=name,
                name_end=name_end,
                start=start,
                end=end,
                class_name=class_name,
                class_token=(
                    None if class_name else _class_reference_token(data, start)
                ),
                strings=strings,
                alignment_code=_mate_alignment(data, end, name_end),
                dimensions=_mate_dimensions(data, start, end),
            )
        )
    token_kinds = _mate_token_kinds(records)
    classes_by_kind: dict[str, set[str]] = {}
    for record in records:
        if not record.class_name:
            continue
        kind = _mate_kind(record.name, record.class_name)
        if kind != "native":
            classes_by_kind.setdefault(kind, set()).add(record.class_name)
    mates: list[NativeMate] = []
    for order, record in enumerate(records):
        if record.class_name:
            kind = _mate_kind(record.name, record.class_name)
            class_name = record.class_name
        else:
            kind = token_kinds.get(record.class_token, _mate_kind(record.name))
            inferred_classes = classes_by_kind.get(kind, set())
            class_name = (
                next(iter(inferred_classes)) if len(inferred_classes) == 1 else ""
            )
        mates.append(
            NativeMate(
                name=record.name,
                kind=kind,
                owner_definition_id=owner_definition_id,
                order=order,
                entities=_mate_entities(record.strings),
                record_offset=record.start,
                record_length=record.end - record.start,
                class_name=class_name,
                class_token=record.class_token,
                serialized_strings=record.strings,
                alignment_code=record.alignment_code,
                dimensions=record.dimensions,
            )
        )
    return NativeMateList(
        native_id=native_id,
        declared_count=declared_count,
        owner_definition_id=owner_definition_id,
        mates=tuple(mates),
        stream=stream,
    )


def _mate_lists(
    archive: SldprtArchive, owner_definition_id: int
) -> tuple[NativeMateList, ...]:
    result: list[NativeMateList] = []
    for record in archive.records:
        named = _mate_stream_name(record.name)
        if not named and not _mate_stream_structure(record.data):
            continue
        try:
            decoded = decode_mate_list(record.data, record.name, owner_definition_id)
        except SldprtFormatError:
            if named:
                raise
            continue
        result.append(decoded)
    return tuple(result)


def _mate_stream_name(name: str) -> bool:
    leaf = name.replace("\\", "/").rsplit("/", 1)[-1].casefold()
    return leaf == MATES_STREAM_NAME.casefold() or leaf.endswith(
        MATES_STREAM_SUFFIX.casefold()
    )


def _mate_stream_structure(data: bytes) -> bool:
    if len(data) < 12 or data[6:10] != CLASS_MARKER:
        return False
    class_size = struct.unpack_from("<H", data, 10)[0]
    class_end = 12 + class_size
    if not 1 <= class_size <= 128 or class_end + 5 > len(data):
        return False
    object_prefix = struct.unpack_from("<H", data, class_end)[0]
    return (
        object_prefix & 0x8000 != 0
        and data[class_end + 2 : class_end + 5] == SERIALIZED_STRING_MARKER
    )


def expand_occurrence_paths(
    root_definition_id: int,
    definitions: Iterable[NativeAssemblyDefinition],
    occurrences: Iterable[NativeAssemblyOccurrence],
) -> tuple[NativeOccurrencePath, ...]:
    definition_by_id = {item.object_id: item for item in definitions}
    children: dict[int, list[NativeAssemblyOccurrence]] = {}
    for occurrence in occurrences:
        children.setdefault(occurrence.owner_definition_id, []).append(occurrence)
    result: list[NativeOccurrencePath] = []

    def visit(
        definition_id: int, prefix: str, depth: int, stack: frozenset[int]
    ) -> None:
        if definition_id in stack:
            raise SldprtFormatError("cyclic assembly definition hierarchy")
        owner = definition_by_id[definition_id]
        for occurrence in children.get(definition_id, []):
            segment = f"{occurrence.name}-{occurrence.reference_number}@{owner.name}"
            path = f"{prefix}/{segment}" if prefix else segment
            result.append(
                NativeOccurrencePath(
                    occurrence_id=occurrence.object_id,
                    definition_id=occurrence.definition_id,
                    path=path,
                    depth=depth,
                )
            )
            target = definition_by_id[occurrence.definition_id]
            if target.document_type == "ASSEMBLY":
                visit(
                    target.object_id,
                    path,
                    depth + 1,
                    stack | {definition_id},
                )

    visit(root_definition_id, "", 0, frozenset())
    return tuple(result)


def _xml_root(data: bytes) -> ET.Element:
    marker = data.find(b"<?xml")
    if marker >= 0:
        data = data[marker:]
    try:
        return ET.fromstring(data)
    except ET.ParseError as exc:
        raise SldprtFormatError(f"invalid assembly component XML: {exc}") from exc


def _local_name(element: ET.Element) -> str:
    return element.tag.rsplit("}", 1)[-1]


def _elements(root: ET.Element, name: str) -> tuple[ET.Element, ...]:
    return tuple(item for item in root.iter() if _local_name(item) == name)


def _files(root: ET.Element) -> tuple[NativeAssemblyFile, ...]:
    return tuple(
        NativeAssemblyFile(
            object_id=_integer(item.attrib.get("id")),
            document_type=item.attrib.get("swDocType", ""),
            creation_time=_integer(item.attrib.get("swCreationTime")),
            source_path=item.attrib.get("swPath", ""),
        )
        for item in _elements(root, "swFile")
    )


def _models(
    root: ET.Element, files: dict[int, NativeAssemblyFile]
) -> tuple[tuple[NativeAssemblyDefinition, ...], tuple[NativeAssemblyOccurrence, ...]]:
    definitions: list[NativeAssemblyDefinition] = []
    occurrences: list[NativeAssemblyOccurrence] = []
    order = 0
    for item in _elements(root, "swModel"):
        file_id = _integer(item.attrib.get("swFileRef"))
        source = files.get(file_id)
        if source is None:
            raise SldprtFormatError(f"assembly model references missing file {file_id}")
        child_elements = tuple(
            child for child in item if _local_name(child) == "swReference"
        )
        definition_id = _integer(item.attrib.get("id"))
        definitions.append(
            NativeAssemblyDefinition(
                object_id=definition_id,
                name=item.attrib.get("swName", ""),
                document_type=source.document_type,
                file_id=file_id,
                source_path=source.source_path,
                configuration_name=item.attrib.get("swConfigurationName", ""),
                configuration_id=_integer(item.attrib.get("swConfigurationId")),
                alternate_configuration_name=item.attrib.get(
                    "swConfigurationAlternateName", ""
                ),
                last_modified_stamp=_integer(item.attrib.get("swLastModifiedStamp")),
                configuration_flags=_integer(item.attrib.get("swConfigurationFlags")),
                bounding_box_m=_bounding_box(item.attrib.get("swBoundingBox")),
                child_occurrence_ids=tuple(
                    _integer(child.attrib.get("id")) for child in child_elements
                ),
                attributes=tuple(sorted(item.attrib.items())),
            )
        )
        for child in child_elements:
            transform = _float_tuple(child.attrib.get("swTransform"), 16)
            occurrences.append(
                NativeAssemblyOccurrence(
                    object_id=_integer(child.attrib.get("id")),
                    feature_id=_integer(child.attrib.get("swID")),
                    owner_definition_id=definition_id,
                    definition_id=_integer(child.attrib.get("swModelRef")),
                    name=child.attrib.get("swName", ""),
                    reference_number=_integer(child.attrib.get("swReferenceNumber"), 1),
                    component_reference=child.attrib.get("swComponentReference", ""),
                    configuration_name=child.attrib.get("swConfigurationName", ""),
                    configuration_id=_integer(child.attrib.get("swConfigurationId")),
                    transform=transform,
                    transform_stamp=_integer(child.attrib.get("swTransformStamp")),
                    suppressed=_yes(child.attrib.get("swSuppressed")),
                    hidden=_yes(child.attrib.get("swHidden")),
                    flexible=_yes(child.attrib.get("swFlexible")),
                    virtual=_yes(child.attrib.get("swIsVirtualComponent")),
                    exclude_from_bom=_yes(child.attrib.get("swExcludeFromBOM")),
                    zone=_yes(child.attrib.get("swZone")),
                    display_mode=_integer(child.attrib.get("swDisplayMode")),
                    display_quality=_integer(child.attrib.get("swHlrDisplayQuality")),
                    edges_in_shaded_mode=_yes(child.attrib.get("swEdgesInShadedMode")),
                    order=order,
                    attributes=tuple(sorted(child.attrib.items())),
                )
            )
            order += 1
    definition_ids = {item.object_id for item in definitions}
    for occurrence in occurrences:
        if occurrence.definition_id not in definition_ids:
            raise SldprtFormatError(
                f"component {occurrence.object_id} references missing model {occurrence.definition_id}"
            )
    return tuple(definitions), tuple(occurrences)


def _configurations(root: ET.Element) -> tuple[NativeAssemblyConfiguration, ...]:
    return tuple(
        NativeAssemblyConfiguration(
            object_id=_integer(item.attrib.get("id")),
            configuration_id=_integer(item.attrib.get("swID")),
            name=item.attrib.get("swName", ""),
            reference=item.attrib.get("swReference", ""),
            model_id=_integer(item.attrib.get("swModelRef")),
            most_recent=_yes(item.attrib.get("swMostRecentConfiguration")),
            needs_update=_yes(item.attrib.get("swConfigurationNeedsUpdate")),
            attributes=tuple(sorted(item.attrib.items())),
        )
        for item in _elements(root, "swConfiguration")
    )


def _display_states(root: ET.Element) -> tuple[NativeDisplayState, ...]:
    return tuple(
        NativeDisplayState(
            object_id=_integer(item.attrib.get("id")),
            name=item.attrib.get("swName", ""),
            configuration_id=(
                _integer(item.attrib.get("swConfigurationId"))
                if "swConfigurationId" in item.attrib
                else None
            ),
            attributes=tuple(sorted(item.attrib.items())),
        )
        for item in _elements(root, "swDisplayState")
    )


def _prefixed_strings(data: bytes, prefix: bytes) -> tuple[tuple[int, str, int], ...]:
    result: list[tuple[int, str, int]] = []
    cursor = 0
    while True:
        offset = data.find(prefix, cursor)
        if offset < 0:
            break
        cursor = offset + 1
        length_offset = offset + len(prefix)
        decoded = _utf16_string(data, length_offset)
        if decoded is not None:
            value, end = decoded
            result.append((offset, value, end))
    return tuple(result)


def _serialized_strings(
    data: bytes, start: int = 0, end: int | None = None
) -> tuple[tuple[int, str, int], ...]:
    limit = len(data) if end is None else min(end, len(data))
    result: list[tuple[int, str, int]] = []
    cursor = max(start, 0)
    while True:
        offset = data.find(SERIALIZED_STRING_MARKER, cursor, limit)
        if offset < 0:
            break
        cursor = offset + 1
        decoded = _utf16_string(data, offset + len(SERIALIZED_STRING_MARKER), limit)
        if decoded is not None:
            value, string_end = decoded
            result.append((offset, value, string_end))
    return tuple(result)


def _utf16_string(
    data: bytes, length_offset: int, end: int | None = None
) -> tuple[str, int] | None:
    limit = len(data) if end is None else end
    if length_offset >= limit:
        return None
    length = data[length_offset]
    if length == 0xFF:
        return None
    string_start = length_offset + 1
    string_end = string_start + length * 2
    if string_end > limit:
        return None
    try:
        value = data[string_start:string_end].decode("utf-16le")
    except UnicodeDecodeError:
        return None
    if any(ord(character) < 0x20 for character in value):
        return None
    return value, string_end


def _mate_record_start(data: bytes, name_prefix_offset: int) -> int:
    inline = data.rfind(CLASS_MARKER, 0, name_prefix_offset)
    if inline >= 0 and inline + 6 <= name_prefix_offset:
        size = struct.unpack_from("<H", data, inline + 4)[0]
        if inline + 6 + size == name_prefix_offset:
            return inline
    return max(6, name_prefix_offset - 2)


def _inline_class_name(data: bytes, start: int) -> str:
    if data[start : start + 4] != CLASS_MARKER:
        return ""
    if start + 6 > len(data):
        return ""
    size = struct.unpack_from("<H", data, start + 4)[0]
    try:
        return data[start + 6 : start + 6 + size].decode("ascii")
    except UnicodeDecodeError:
        return ""


def _class_reference_token(data: bytes, offset: int) -> int | None:
    if offset < 0 or offset + 2 > len(data):
        return None
    token = struct.unpack_from("<H", data, offset)[0]
    return token if token & 0x8000 and token != 0xFFFF else None


def _mate_token_kinds(records: list[_MateRecord]) -> dict[int | None, str]:
    candidates: dict[int, set[str]] = {}
    for record in records:
        if record.class_name or record.class_token is None:
            continue
        kind = _mate_kind(record.name)
        if kind != "native":
            candidates.setdefault(record.class_token, set()).add(kind)
    return {
        token: next(iter(kinds))
        for token, kinds in candidates.items()
        if len(kinds) == 1
    }


def _mate_entities(strings: tuple[str, ...]) -> tuple[NativeMateEntity, ...]:
    source_paths = tuple(value for value in strings if is_cad_path(value))
    entity_values: list[tuple[str, list[str]]] = []
    persistent: list[str] = []
    for value in strings:
        if "^" in value and "@" in value:
            continue
        if value.casefold().startswith("mo"):
            persistent.append(value)
            continue
        if is_component_path(value):
            entity_values.append((value, persistent))
            persistent = []
            continue
        if "@" in value and entity_values:
            entity_values[-1][1].append(value)
            continue
        if "@" in value:
            persistent.append(value)
    entities: list[NativeMateEntity] = []
    for component_path, references in entity_values:
        leaf = component_path.rsplit("/", 1)[-1].split("@", 1)[0]
        source_name = re.sub(r"-\d+$", "", leaf).casefold()
        source_path = next(
            (
                value
                for value in source_paths
                if PureWindowsPath(value).stem.casefold() == source_name
            ),
            "",
        )
        entities.append(
            NativeMateEntity(
                component_path=component_path,
                persistent_references=tuple(references),
                source_path=source_path,
                configuration_name="",
            )
        )
    synthetic = tuple(value for value in strings if "^" in value and "@" in value)
    entities.extend(
        NativeMateEntity(
            component_path="",
            persistent_references=(value,),
            source_path="",
            configuration_name="",
        )
        for value in synthetic
    )
    if persistent:
        entities.append(NativeMateEntity("", tuple(persistent), "", ""))
    return tuple(entities)


def _mate_kind(name: str, class_name: str = "") -> str:
    normalized_class = class_name.casefold().strip()
    if normalized_class:
        return _MATE_KIND_BY_CLASS.get(normalized_class, "native")
    lowered = name.casefold().strip()
    match = re.fullmatch(r"([a-z]+)(\d+)(?:___endtag___)?", lowered)
    return _MATE_KIND_BY_NAME.get(match.group(1), "native") if match else "native"


def _mate_alignment(data: bytes, end: int, name_end: int) -> int | None:
    alignment_offset = name_end + _MATE_ALIGNMENT_OFFSET
    entity_count_offset = name_end + _MATE_ENTITY_COUNT_OFFSET
    if entity_count_offset + 4 > end:
        return None
    entity_count = struct.unpack_from("<I", data, entity_count_offset)[0]
    if entity_count != 2:
        return None
    try:
        alignment_code = struct.unpack_from("<H", data, alignment_offset)[0]
    except struct.error:
        return None
    return alignment_code if alignment_code in NATIVE_MATE_ALIGNMENT_BY_CODE else None


def _mate_dimensions(
    data: bytes, start: int, end: int
) -> tuple[NativeMateDimension, ...]:
    result: list[NativeMateDimension] = []
    for _, name, string_end in _serialized_strings(data, start, end):
        value_offset = dimension_scalar_value_offset(data, string_end, end)
        if value_offset is None:
            continue
        value = struct.unpack_from("<d", data, value_offset)[0]
        if math.isfinite(value):
            result.append(NativeMateDimension(name, value, value_offset))
    return tuple(result)


def _record_strings(data: bytes, start: int, end: int) -> tuple[str, ...]:
    values = [
        (offset, value)
        for offset, value, _ in _serialized_strings(data, start, end)
        if value
    ]
    for match in _WIDE_TEXT.finditer(data, start, end):
        values.append((match.start(), match.group().decode("utf-16le")))
    values.sort(key=lambda item: item[0])
    result: list[str] = []
    for _, value in values:
        if not result or result[-1] != value:
            result.append(value)
    return tuple(result)


def _bounding_box(
    value: str | None,
) -> tuple[float, float, float, float, float, float] | None:
    if not value:
        return None
    return _float_tuple(value, 6)


def _float_tuple(value: str | None, count: int) -> tuple[float, ...]:
    if value is None:
        raise SldprtFormatError("required floating-point tuple is missing")
    result = tuple(float(item) for item in value.split())
    if len(result) != count or not all(math.isfinite(item) for item in result):
        raise SldprtFormatError(
            f"expected {count} finite floating-point values, found {len(result)}"
        )
    return result


def _integer(value: str | None, default: int = 0) -> int:
    try:
        return int(value) if value is not None else default
    except ValueError as exc:
        raise SldprtFormatError(f"invalid integer value {value!r}") from exc


def _yes(value: str | None) -> bool:
    return value == "YES"
