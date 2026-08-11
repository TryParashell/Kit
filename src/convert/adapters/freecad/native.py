# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re
import struct
from typing import Any
import xml.etree.ElementTree as ET
import zipfile

from interchange import (
    ArcEllipseGeometry,
    ArcGeometry,
    ArcHyperbolaGeometry,
    ArcParabolaGeometry,
    AssemblyData,
    Body,
    BooleanOperation,
    BrepModel,
    BrepPayload,
    CadDocument,
    CadSource,
    Capability,
    ChamferFeature,
    CircleGeometry,
    CircularPatternFeature,
    ComponentDefinition,
    ComponentDocument,
    ComponentInstance,
    ComponentKind,
    Configuration,
    ConstraintKind,
    ConstraintReference,
    Diagnostic,
    EllipseGeometry,
    Expression,
    ExtrusionEndCondition,
    ExtrusionFeature,
    FeatureDefinition,
    FeatureKind,
    FeatureStep,
    FilletFeature,
    GeometryKind,
    HyperbolaGeometry,
    LineGeometry,
    LinearPatternFeature,
    MateConstraint,
    MateEntity,
    MateEntityKind,
    MateGroup,
    MateKind,
    Matrix4,
    Mesh,
    NativeGeometry,
    NativeFeatureDefinition,
    Parameter,
    ParameterValue,
    ParabolaGeometry,
    PayloadRole,
    PointGeometry,
    Provenance,
    ProvenanceSpan,
    Selection,
    SelectionPathElement,
    Severity,
    ShellFeature,
    Sketch,
    SketchConstraint,
    SketchEntity,
    SplineGeometry,
    SupportPlane,
    TopologySummary,
    Transform,
    ValueKind,
    Vector2,
    Vector3,
    infer_capabilities,
)

from convert.opencascade import decode_ascii_brep

from .archive import (
    DOCUMENT_ENTRY,
    NATIVE_DOCUMENT_SHA256_ATTRIBUTE,
    _MAX_ENTRY_SIZE,
    _MAX_EXTERNAL_FILES,
    _MAX_TOTAL_SIZE,
    _validated_archive_members,
    _validated_document_xml,
    _validated_entry_name,
    _validated_object_name,
    extract_manifest_from_fcstd,
)
from .format import FORMAT_ID, SUFFIX
from .protocol import (
    ASSEMBLY_JOINT_GROUP_TYPE_ID,
    ASSEMBLY_OBJECT_TYPE_PREFIX,
    ASSEMBLY_ROOT_TYPE_ID,
    BODY_CONTAINER_TYPE_IDS,
    CONSTRAINT_KIND_BY_CODE,
    CONSTRAINT_POINT_BY_INDEX,
    CONSTRAINT_VALUE_KIND_BY_CODE,
    DIMENSIONAL_CONSTRAINT_CODES,
    EXTRUSION_TYPE_BY_CODE,
    FEATURE_KIND_BY_TYPE_ID,
    GEOMETRY_KIND_BY_TYPE_ID,
    JOINT_GROUND_PROPERTY,
    JOINT_REFERENCE_PROPERTIES,
    JOINT_RESERVED_LINK_PROPERTIES,
    JOINT_TYPE_PROPERTIES,
    MATE_KIND_BY_JOINT_TYPE,
    MATE_KINDS_USING_DISTANCE,
    MATE_KINDS_USING_SECOND_DISTANCE,
    NON_FEATURE_OBJECT_TYPE_IDS,
    PERMISSIVE_TRUE_VALUES,
    POCKET_TYPE_ID,
    PRIMITIVE_FEATURE_TYPE_IDS,
    SCALAR_PROPERTY_KINDS,
    SKETCH_TYPE_ID,
    SPLINE_GEOMETRY_TYPE_IDS,
    STRING_HASHER_TAGS,
    SUBELEMENT_KIND_BY_PREFIX,
    SUPPORT_PLANE_TYPE_IDS,
    XML_TRUE_VALUES,
)

_MAX_EXTERNAL_DEPTH = 16
_MIN_OBJECT_GRAPH_SCHEMA_VERSION = 2
_GROOVE_TYPE_ID = "PartDesign::Groove"
_SUBTRACTIVE_TYPE_IDS = frozenset({POCKET_TYPE_ID, _GROOVE_TYPE_ID})
_SUBTRACTIVE_CAPABLE_KINDS = frozenset({FeatureKind.EXTRUSION, FeatureKind.REVOLUTION})


class NativeFreeCADError(ValueError):
    __slots__ = ()


@dataclass(slots=True)
class _NativeObject:
    name: str
    type_id: str
    index: int
    object_id: str
    touched: bool
    dependencies: tuple[str, ...]
    extensions: tuple[ET.Element, ...]
    transient_properties: tuple[ET.Element, ...]
    properties: dict[str, ET.Element]


@dataclass(slots=True)
class _NativeArchive:
    root: ET.Element
    objects: tuple[_NativeObject, ...]
    entries: dict[str, bytes]
    document_xml: bytes
    entry_order: tuple[str, ...]


@dataclass(slots=True)
class _ExternalState:
    root: Path
    cache: dict[Path, CadDocument]
    active: set[Path]
    file_count: int
    total_bytes: int


def _entry_name(name: str) -> str:
    try:
        return _validated_entry_name(name)
    except ValueError as exc:
        raise NativeFreeCADError(str(exc)) from exc


def _declared_count(node: ET.Element, actual: int, label: str) -> None:
    value = node.get("Count", node.get("count"))
    if value is None:
        return
    try:
        expected = int(value)
    except ValueError as exc:
        raise NativeFreeCADError(f"FreeCAD {label} count is invalid") from exc
    if expected != actual:
        raise NativeFreeCADError(f"FreeCAD {label} count does not match its data")


def _archive_members(data: bytes) -> tuple[zipfile.ZipFile, dict[str, zipfile.ZipInfo]]:
    try:
        return _validated_archive_members(data)
    except ValueError as exc:
        raise NativeFreeCADError(str(exc)) from exc


def _stored_count(node: ET.Element, name: str, actual: int, label: str) -> None:
    value = node.get(name)
    if value is None:
        return
    try:
        expected = int(value)
    except ValueError as exc:
        raise NativeFreeCADError(f"FreeCAD {label} count is invalid") from exc
    if expected != actual:
        raise NativeFreeCADError(f"FreeCAD {label} count does not match its data")


def _parse_objects(root: ET.Element) -> tuple[_NativeObject, ...]:
    objects_node = root.find("./Objects")
    data_node = root.find("./ObjectData")
    if objects_node is None or data_node is None:
        raise NativeFreeCADError("FreeCAD Document.xml has no object graph")
    declarations = objects_node.findall("./Object")
    object_data = data_node.findall("./Object")
    _declared_count(objects_node, len(declarations), "object")
    _declared_count(data_node, len(object_data), "object data")
    declaration_by_name: dict[str, tuple[str, int, str, bool]] = {}
    ids: set[str] = set()
    for index, node in enumerate(declarations):
        name = node.get("name", "")
        type_id = node.get("type", "")
        object_id = node.get("id", "")
        if not name or not type_id or name in declaration_by_name:
            raise NativeFreeCADError("FreeCAD object declarations are malformed")
        try:
            _validated_object_name(name)
        except ValueError as exc:
            raise NativeFreeCADError(str(exc)) from exc
        if object_id and object_id in ids:
            raise NativeFreeCADError(
                "FreeCAD object declarations contain duplicate ids"
            )
        if object_id:
            ids.add(object_id)
        declaration_by_name[name] = (
            type_id,
            index,
            object_id,
            node.get("Touched") == "1",
        )
    data_by_name: dict[str, ET.Element] = {}
    for node in object_data:
        name = node.get("name", "")
        if not name or name in data_by_name:
            raise NativeFreeCADError("FreeCAD object data contains duplicate names")
        data_by_name[name] = node
    if set(declaration_by_name) != set(data_by_name):
        raise NativeFreeCADError("FreeCAD object declarations and data do not match")
    dependencies: dict[str, tuple[str, ...]] = {}
    for node in objects_node.findall("./ObjectDeps"):
        name = node.get("Name", "")
        if not name or name in dependencies or name not in declaration_by_name:
            raise NativeFreeCADError("FreeCAD dependency graph is malformed")
        values = tuple(item.get("Name", "") for item in node.findall("./Dep"))
        if any(not value or value not in declaration_by_name for value in values):
            raise NativeFreeCADError("FreeCAD dependency graph has missing objects")
        _declared_count(node, len(values), "dependency")
        dependencies[name] = values
    result: list[_NativeObject] = []
    for name, (type_id, index, object_id, touched) in declaration_by_name.items():
        property_nodes: dict[str, ET.Element] = {}
        object_element = data_by_name[name]
        properties_element = object_element.find("./Properties")
        if properties_element is None:
            raise NativeFreeCADError(f"FreeCAD object {name!r} has no properties")
        properties = properties_element.findall("./Property")
        transient_properties = tuple(properties_element.findall("./_Property"))
        _stored_count(properties_element, "Count", len(properties), "property")
        _stored_count(
            properties_element,
            "TransientCount",
            len(transient_properties),
            "transient property",
        )
        for node in properties:
            property_name = node.get("name", "")
            if not property_name or property_name in property_nodes:
                raise NativeFreeCADError(
                    f"FreeCAD object {name!r} has malformed properties"
                )
            property_nodes[property_name] = node
        result.append(
            _NativeObject(
                name,
                type_id,
                index,
                object_id,
                touched,
                dependencies.get(name, ()),
                tuple(object_element.findall("./Extensions/Extension")),
                transient_properties,
                property_nodes,
            )
        )
    return tuple(result)


def _load_native_archive(data: bytes, *, load_entries: bool = True) -> _NativeArchive:
    archive, members = _archive_members(data)
    with archive:
        try:
            root, document_xml = _validated_document_xml(archive, members)
        except ValueError as exc:
            raise NativeFreeCADError(str(exc)) from exc
        try:
            schema_version = int(root.get("SchemaVersion", ""))
        except ValueError as exc:
            raise NativeFreeCADError("FreeCAD schema version is invalid") from exc
        if schema_version < _MIN_OBJECT_GRAPH_SCHEMA_VERSION:
            raise NativeFreeCADError("FreeCAD schema version is not supported")
        objects = _parse_objects(root)
        referenced: set[str] = set()
        for node in root.findall(".//*[@file]"):
            if node.tag == "XLink":
                continue
            filename = node.get("file", "")
            if filename:
                referenced.add(_entry_name(filename))
        missing = sorted(referenced.difference(members))
        if missing:
            raise NativeFreeCADError(
                "FCStd archive is missing referenced data: " + ", ".join(missing)
            )
        entries: dict[str, bytes] = {}
        if load_entries:
            try:
                entries = {name: archive.read(members[name]) for name in referenced}
            except (
                OSError,
                RuntimeError,
                NotImplementedError,
                zipfile.BadZipFile,
            ) as exc:
                raise NativeFreeCADError(
                    "FCStd archive contains unreadable referenced data"
                ) from exc
    return _NativeArchive(
        root,
        objects,
        entries,
        document_xml,
        tuple(name for name in members if name in referenced),
    )


def probe_native_fcstd(data: bytes) -> tuple[float, str]:
    try:
        native = _load_native_archive(data, load_entries=False)
    except NativeFreeCADError as exc:
        return 0.0, str(exc)
    return (
        0.95,
        f"native FreeCAD schema {native.root.get('SchemaVersion')} document",
    )


def _element_data(node: ET.Element) -> dict[str, Any]:
    result: dict[str, Any] = {
        "tag": node.tag,
        "attributes": dict(sorted(node.attrib.items())),
    }
    text = (node.text or "").strip()
    if text:
        result["text"] = text
    children = [_element_data(child) for child in node]
    if children:
        result["children"] = children
    return result


def _native_object_data(obj: _NativeObject) -> dict[str, Any]:
    return {
        "name": obj.name,
        "type_id": obj.type_id,
        "order": obj.index,
        "object_id": obj.object_id,
        "touched": obj.touched,
        "dependencies": list(obj.dependencies),
        "extensions": [_element_data(node) for node in obj.extensions],
        "transient_properties": [
            _element_data(node) for node in obj.transient_properties
        ],
        "property_order": list(obj.properties),
        "properties": {
            name: _element_data(node) for name, node in obj.properties.items()
        },
    }


def _string_hasher_data(native: _NativeArchive) -> dict[str, Any] | None:
    nodes = [
        _element_data(node) for node in native.root if node.tag in STRING_HASHER_TAGS
    ]
    entries: list[dict[str, Any]] = []
    for node in native.root:
        if node.tag not in STRING_HASHER_TAGS:
            continue
        for child in node.iter():
            filename = child.get("file", "")
            if filename and filename in native.entries:
                entries.append(
                    {
                        "source_stream": filename,
                        "data": native.entries[filename],
                    }
                )
    attribute = native.root.get("StringHasher", "")
    if not attribute and not nodes and not entries:
        return None
    return {
        "attribute": attribute,
        "nodes": nodes,
        "entries": entries,
    }


def _other_entry_data(native: _NativeArchive) -> list[dict[str, Any]]:
    represented: set[str] = set()
    for obj in native.objects:
        for node in obj.properties.values():
            if node.find("./Part") is None:
                continue
            represented.update(
                filename
                for child in node.findall(".//*[@file]")
                if (filename := child.get("file", ""))
            )
    for node in native.root:
        if node.tag not in STRING_HASHER_TAGS:
            continue
        represented.update(
            filename for child in node.iter() if (filename := child.get("file", ""))
        )
    return [
        {"source_stream": name, "data": native.entries[name]}
        for name in native.entry_order
        if name in native.entries and name not in represented
    ]


def _native_document_payloads(
    native: _NativeArchive, data: bytes, source_path: str
) -> tuple[BrepPayload, BrepPayload]:
    native_digest = hashlib.sha256(data).digest()
    native_name = Path(source_path).name if source_path else f"Document{SUFFIX}"
    document = BrepPayload(
        "freecad:native-document",
        FORMAT_ID,
        "native_document",
        f"FreeCAD Schema {native.root.get('SchemaVersion', '')}",
        native_digest.hex(),
        data=data,
        source_stream=native_name,
        provenance=Provenance(
            FORMAT_ID,
            DOCUMENT_ENTRY,
            spans=(ProvenanceSpan(DOCUMENT_ENTRY, 0, len(native.document_xml), "xml"),),
        ),
        attributes={
            "object_count": len(native.objects),
            "entry_order": list(native.entry_order),
        },
        role=PayloadRole.DOCUMENT,
        file_extension=SUFFIX,
    )
    binding = BrepPayload(
        "freecad:native-document-binding",
        f"{FORMAT_ID}.sha256",
        "native_document_binding",
        "sha256",
        hashlib.sha256(native_digest).hexdigest(),
        data=native_digest,
        source_stream=native_name,
        provenance=Provenance(FORMAT_ID, native_digest.hex()),
        role=PayloadRole.VERIFICATION,
        file_extension=".sha256",
    )
    return document, binding


def _child(obj: _NativeObject, name: str, tag: str | None = None) -> ET.Element | None:
    node = obj.properties.get(name)
    if node is None:
        return None
    if tag is not None:
        return node.find(f"./{tag}")
    return next(iter(node), None)


def _number(value: str | None, default: float = 0.0) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default
    return result if math.isfinite(result) else default


def _integer(value: str | None, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _string(obj: _NativeObject, name: str, default: str = "") -> str:
    node = _child(obj, name, "String")
    return default if node is None else node.get("value", default)


def _bool(obj: _NativeObject, name: str, default: bool = False) -> bool:
    node = _child(obj, name, "Bool")
    if node is None:
        return default
    return node.get("value", "false").casefold() in PERMISSIVE_TRUE_VALUES


def _float(obj: _NativeObject, name: str, default: float = 0.0) -> float:
    node = _child(obj, name, "Float")
    return default if node is None else _number(node.get("value"), default)


def _enum(obj: _NativeObject, name: str, default: int = 0) -> int:
    node = _child(obj, name, "Integer")
    return default if node is None else _integer(node.get("value"), default)


def _link(obj: _NativeObject, name: str) -> str:
    node = obj.properties.get(name)
    if node is None:
        return ""
    child = node.find("./Link")
    if child is not None:
        return child.get("value", "")
    child = node.find("./LinkSub")
    if child is not None:
        return child.get("value", "")
    child = node.find("./XLink")
    if child is not None:
        return child.get("name", "")
    return ""


def _link_list(obj: _NativeObject, name: str) -> tuple[str, ...]:
    node = obj.properties.get(name)
    if node is None:
        return ()
    values: list[str] = []
    for path, attribute in (
        ("./LinkList/Link", "value"),
        ("./XLinkList/XLink", "name"),
        ("./LinkSubList/Link", "obj"),
    ):
        values.extend(
            value for child in node.findall(path) if (value := child.get(attribute, ""))
        )
    return tuple(values)


def _placement_element(obj: _NativeObject, name: str) -> ET.Element | None:
    return _child(obj, name, "PropertyPlacement")


def _placement_matrix(node: ET.Element | None) -> tuple[float, ...]:
    if node is None:
        return (
            1.0,
            0.0,
            0.0,
            0.0,
            0.0,
            1.0,
            0.0,
            0.0,
            0.0,
            0.0,
            1.0,
            0.0,
            0.0,
            0.0,
            0.0,
            1.0,
        )
    x = _number(node.get("Q0"))
    y = _number(node.get("Q1"))
    z = _number(node.get("Q2"))
    w = _number(node.get("Q3"), 1.0)
    norm = math.sqrt(x * x + y * y + z * z + w * w)
    if norm <= 1e-15:
        x, y, z, w = 0.0, 0.0, 0.0, 1.0
    else:
        x, y, z, w = x / norm, y / norm, z / norm, w / norm
    return (
        1.0 - 2.0 * (y * y + z * z),
        2.0 * (x * y - z * w),
        2.0 * (x * z + y * w),
        _number(node.get("Px")),
        2.0 * (x * y + z * w),
        1.0 - 2.0 * (x * x + z * z),
        2.0 * (y * z - x * w),
        _number(node.get("Py")),
        2.0 * (x * z - y * w),
        2.0 * (y * z + x * w),
        1.0 - 2.0 * (x * x + y * y),
        _number(node.get("Pz")),
        0.0,
        0.0,
        0.0,
        1.0,
    )


def _transform(node: ET.Element | None) -> Transform:
    values = _placement_matrix(node)
    return Transform(
        origin=Vector3(values[3], values[7], values[11]),
        x_axis=Vector3(values[0], values[4], values[8]),
        y_axis=Vector3(values[1], values[5], values[9]),
        z_axis=Vector3(values[2], values[6], values[10]),
    )


def _expressions(obj: _NativeObject) -> dict[str, str]:
    node = obj.properties.get("ExpressionEngine")
    if node is None:
        return {}
    values: dict[str, str] = {}
    for child in node.findall("./ExpressionEngine/Expression"):
        path = child.get("path", "").lstrip(".")
        expression = child.get("expression", "")
        if path and expression:
            values[path] = expression
    return values


def _property_parameter_value(node: ET.Element) -> ParameterValue | None:
    type_id = node.get("type", "")
    if type_id == "App::PropertyEnumeration":
        child = node.find("./Integer")
        if child is None:
            return None
        choices = [
            item.get("value", "") for item in node.findall("./CustomEnumList/Enum")
        ]
        index = _integer(child.get("value"))
        value: str | int = choices[index] if 0 <= index < len(choices) else index
        return ParameterValue(value, ValueKind.STRING if choices else ValueKind.INTEGER)
    kind_and_unit = SCALAR_PROPERTY_KINDS.get(type_id)
    if kind_and_unit is None:
        return None
    kind, unit, tag = kind_and_unit
    child = node.find(f"./{tag}")
    if child is None:
        return None
    if kind == ValueKind.BOOLEAN:
        value = child.get("value", "false").casefold() in PERMISSIVE_TRUE_VALUES
    elif kind == ValueKind.INTEGER:
        value = _integer(child.get("value"))
    elif kind == ValueKind.STRING:
        value = child.get("value", "")
    elif tag == "Integer":
        value = _integer(child.get("value"))
    else:
        value = _number(child.get("value"))
    return ParameterValue(value, kind, unit)


def _geometry(node: ET.Element, entity_id: str) -> tuple[GeometryKind, Any]:
    type_id = node.get("type", "")
    if type_id == "Part::GeomLineSegment":
        value = node.find("./LineSegment")
        if value is not None:
            return GeometryKind.LINE, LineGeometry(
                Vector2(_number(value.get("StartX")), _number(value.get("StartY"))),
                Vector2(_number(value.get("EndX")), _number(value.get("EndY"))),
            )
    if type_id == "Part::GeomCircle":
        value = node.find("./Circle")
        if value is not None:
            return GeometryKind.CIRCLE, CircleGeometry(
                Vector2(_number(value.get("CenterX")), _number(value.get("CenterY"))),
                abs(_number(value.get("Radius"))),
            )
    if type_id == "Part::GeomArcOfCircle":
        value = node.find("./ArcOfCircle")
        if value is not None:
            return GeometryKind.ARC, ArcGeometry(
                Vector2(_number(value.get("CenterX")), _number(value.get("CenterY"))),
                abs(_number(value.get("Radius"))),
                _number(value.get("StartAngle")),
                _number(value.get("EndAngle")),
            )
    if type_id == "Part::GeomPoint":
        value = node.find("./GeomPoint")
        if value is None:
            value = node.find("./Point")
        if value is not None:
            return GeometryKind.POINT, PointGeometry(
                Vector2(_number(value.get("X")), _number(value.get("Y")))
            )
    if type_id == "Part::GeomEllipse":
        value = node.find("./Ellipse")
        if value is not None:
            center = Vector2(
                _number(value.get("CenterX")), _number(value.get("CenterY"))
            )
            axis = _geometry_axis(value)
            return GeometryKind.ELLIPSE, EllipseGeometry(
                center,
                axis,
                abs(_number(value.get("MajorRadius"))),
                abs(_number(value.get("MinorRadius"))),
            )
    if type_id == "Part::GeomArcOfEllipse":
        value = node.find("./ArcOfEllipse")
        if value is not None:
            return GeometryKind.ARC_ELLIPSE, ArcEllipseGeometry(
                Vector2(_number(value.get("CenterX")), _number(value.get("CenterY"))),
                _geometry_axis(value),
                abs(_number(value.get("MajorRadius"))),
                abs(_number(value.get("MinorRadius"))),
                _number(value.get("StartAngle")),
                _number(value.get("EndAngle")),
            )
    if type_id in {"Part::GeomHyperbola", "Part::GeomArcOfHyperbola"}:
        tag = "Hyperbola" if type_id == "Part::GeomHyperbola" else "ArcOfHyperbola"
        value = node.find(f"./{tag}")
        if value is not None:
            arguments = (
                Vector2(_number(value.get("CenterX")), _number(value.get("CenterY"))),
                _geometry_axis(value),
                abs(_number(value.get("MajorRadius"))),
                abs(_number(value.get("MinorRadius"))),
            )
            if type_id == "Part::GeomHyperbola":
                return GeometryKind.HYPERBOLA, HyperbolaGeometry(*arguments)
            return GeometryKind.ARC_HYPERBOLA, ArcHyperbolaGeometry(
                *arguments,
                _number(value.get("StartAngle")),
                _number(value.get("EndAngle")),
            )
    if type_id in {"Part::GeomParabola", "Part::GeomArcOfParabola"}:
        tag = "Parabola" if type_id == "Part::GeomParabola" else "ArcOfParabola"
        value = node.find(f"./{tag}")
        if value is not None:
            arguments = (
                Vector2(_number(value.get("CenterX")), _number(value.get("CenterY"))),
                _geometry_axis(value),
                abs(_number(value.get("Focal"))),
            )
            if type_id == "Part::GeomParabola":
                return GeometryKind.PARABOLA, ParabolaGeometry(*arguments)
            return GeometryKind.ARC_PARABOLA, ArcParabolaGeometry(
                *arguments,
                _number(value.get("StartAngle")),
                _number(value.get("EndAngle")),
            )
    if type_id in SPLINE_GEOMETRY_TYPE_IDS:
        value = node.find("./BSplineCurve")
        if value is None:
            value = node.find("./BezierCurve")
        if value is not None:
            points = tuple(
                Vector2(_number(item.get("X")), _number(item.get("Y")))
                for item in value.findall(".//*[@X][@Y]")
            )
            if points:
                return GEOMETRY_KIND_BY_TYPE_ID[type_id], SplineGeometry(
                    points,
                    (
                        max(1, len(points) - 1)
                        if type_id == "Part::GeomBezierCurve"
                        else max(1, _integer(value.get("Degree"), 3))
                    ),
                    knots=tuple(
                        _number(item.get("Value")) for item in value.findall("./Knot")
                    ),
                    multiplicities=tuple(
                        _integer(item.get("Mult"), 1)
                        for item in value.findall("./Knot")
                    ),
                    weights=tuple(
                        _number(item.get("Weight"), 1.0)
                        for item in value.findall("./Pole")
                    ),
                    periodic=value.get(
                        "IsPeriodic", value.get("Periodic", "false")
                    ).casefold()
                    in XML_TRUE_VALUES,
                )
    return GEOMETRY_KIND_BY_TYPE_ID.get(type_id, GeometryKind.NATIVE), NativeGeometry(
        FORMAT_ID, type_id or "unknown", _element_data(node)
    )


def _geometry_axis(value: ET.Element) -> Vector2:
    if value.get("MajorAxisX") is not None:
        return Vector2(
            _number(value.get("MajorAxisX"), 1.0),
            _number(value.get("MajorAxisY")),
        )
    angle = _number(value.get("AngleXU"))
    return Vector2(math.cos(angle), math.sin(angle))


def _points_close(first: Vector2, second: Vector2, tolerance: float = 1e-7) -> bool:
    return math.hypot(first.x - second.x, first.y - second.y) <= tolerance


def _segment_orientation(first: Vector2, second: Vector2, third: Vector2) -> float:
    return (second.x - first.x) * (third.y - first.y) - (second.y - first.y) * (
        third.x - first.x
    )


def _point_on_segment(
    point: Vector2,
    first: Vector2,
    second: Vector2,
    tolerance: float = 1e-7,
) -> bool:
    return (
        abs(_segment_orientation(first, second, point)) <= tolerance
        and min(first.x, second.x) - tolerance
        <= point.x
        <= max(first.x, second.x) + tolerance
        and min(first.y, second.y) - tolerance
        <= point.y
        <= max(first.y, second.y) + tolerance
    )


def _segments_intersect_or_touch(
    first_start: Vector2,
    first_end: Vector2,
    second_start: Vector2,
    second_end: Vector2,
    tolerance: float = 1e-7,
) -> bool:
    first_a = _segment_orientation(first_start, first_end, second_start)
    first_b = _segment_orientation(first_start, first_end, second_end)
    second_a = _segment_orientation(second_start, second_end, first_start)
    second_b = _segment_orientation(second_start, second_end, first_end)
    if (
        (first_a > tolerance and first_b < -tolerance)
        or (first_a < -tolerance and first_b > tolerance)
    ) and (
        (second_a > tolerance and second_b < -tolerance)
        or (second_a < -tolerance and second_b > tolerance)
    ):
        return True
    return any(
        abs(value) <= tolerance and _point_on_segment(point, start, end, tolerance)
        for value, point, start, end in (
            (first_a, second_start, first_start, first_end),
            (first_b, second_end, first_start, first_end),
            (second_a, first_start, second_start, second_end),
            (second_b, first_end, second_start, second_end),
        )
    )


def _closed_profile_entity_ids(
    entities: tuple[SketchEntity, ...],
) -> tuple[tuple[str, ...], ...]:
    candidates = tuple(entity for entity in entities if not entity.construction)
    if not candidates:
        return ()
    closed = tuple(
        entity
        for entity in candidates
        if isinstance(entity.geometry, (CircleGeometry, EllipseGeometry))
    )
    lines = tuple(
        (index, entity)
        for index, entity in enumerate(candidates)
        if isinstance(entity.geometry, LineGeometry)
    )
    if len(closed) + len(lines) != len(candidates):
        return ()
    if closed:
        if lines or any(
            (
                isinstance(entity.geometry, CircleGeometry)
                and entity.geometry.radius <= 1e-9
            )
            or (
                isinstance(entity.geometry, EllipseGeometry)
                and min(
                    entity.geometry.major_radius,
                    entity.geometry.minor_radius,
                )
                <= 1e-9
            )
            for entity in closed
        ):
            return ()
        return tuple((entity.id,) for entity in closed)
    endpoints = tuple(
        point
        for _, entity in lines
        for point in (entity.geometry.start, entity.geometry.end)
    )
    parents = list(range(len(endpoints)))

    def root(index: int) -> int:
        while parents[index] != index:
            parents[index] = parents[parents[index]]
            index = parents[index]
        return index

    def union(first: int, second: int) -> None:
        first_root = root(first)
        second_root = root(second)
        if first_root != second_root:
            parents[max(first_root, second_root)] = min(first_root, second_root)

    for first in range(len(endpoints)):
        for second in range(first + 1, len(endpoints)):
            if _points_close(endpoints[first], endpoints[second]):
                union(first, second)
    clusters: dict[int, list[int]] = {}
    for index in range(len(endpoints)):
        clusters.setdefault(root(index), []).append(index)
    if any(
        not _points_close(endpoints[first], endpoints[second])
        for members in clusters.values()
        for position, first in enumerate(members)
        for second in members[position + 1 :]
    ):
        return ()
    roots = tuple(root(index) for index in range(len(endpoints)))
    incident: dict[int, list[int]] = {}
    for edge_index in range(len(lines)):
        start = roots[edge_index * 2]
        end = roots[edge_index * 2 + 1]
        if start == end:
            return ()
        incident.setdefault(start, []).append(edge_index)
        incident.setdefault(end, []).append(edge_index)
    if any(len(values) != 2 for values in incident.values()):
        return ()
    remaining = set(range(len(lines)))
    profiles: list[tuple[int, tuple[str, ...], tuple[Vector2, ...]]] = []
    while remaining:
        first_edge = min(remaining, key=lambda value: lines[value][0])
        start_vertex = roots[first_edge * 2]
        current_vertex = roots[first_edge * 2 + 1]
        ordered = [first_edge]
        vertices = [endpoints[first_edge * 2], endpoints[first_edge * 2 + 1]]
        remaining.remove(first_edge)
        while current_vertex != start_vertex:
            next_edges = [
                value for value in incident[current_vertex] if value in remaining
            ]
            if len(next_edges) != 1:
                return ()
            edge_index = next_edges[0]
            edge_start = roots[edge_index * 2]
            edge_end = roots[edge_index * 2 + 1]
            if current_vertex == edge_start:
                current_vertex = edge_end
                vertices.append(endpoints[edge_index * 2 + 1])
            elif current_vertex == edge_end:
                current_vertex = edge_start
                vertices.append(endpoints[edge_index * 2])
            else:
                return ()
            ordered.append(edge_index)
            remaining.remove(edge_index)
        if len(ordered) < 3 or len(set(vertices[:-1])) != len(vertices) - 1:
            return ()
        area = abs(
            sum(
                first.x * second.y - second.x * first.y
                for first, second in zip(vertices[:-1], vertices[1:], strict=True)
            )
        )
        if area <= 1e-9:
            return ()
        segments = list(zip(vertices[:-1], vertices[1:], strict=True))
        for first_index, first_segment in enumerate(segments):
            for second_index in range(first_index + 1, len(segments)):
                if second_index in {
                    first_index + 1,
                    (first_index - 1) % len(segments),
                }:
                    continue
                if _segments_intersect_or_touch(
                    *first_segment,
                    *segments[second_index],
                ):
                    return ()
        profiles.append(
            (
                min(lines[index][0] for index in ordered),
                tuple(lines[index][1].id for index in ordered),
                tuple(vertices[:-1]),
            )
        )
    for first_index, (_, _, first_vertices) in enumerate(profiles):
        first_segments = tuple(
            zip(
                first_vertices,
                (*first_vertices[1:], first_vertices[0]),
                strict=True,
            )
        )
        for _, _, second_vertices in profiles[first_index + 1 :]:
            second_segments = tuple(
                zip(
                    second_vertices,
                    (*second_vertices[1:], second_vertices[0]),
                    strict=True,
                )
            )
            if any(
                _segments_intersect_or_touch(*first_segment, *second_segment)
                for first_segment in first_segments
                for second_segment in second_segments
            ):
                return ()
    return tuple(profile for _, profile, _ in sorted(profiles))


_ORIGIN_PLANE_FRAMES = {
    "XY_Plane": (
        0,
        Transform(),
        Transform(),
    ),
    "XZ_Plane": (
        1,
        Transform(
            x_axis=Vector3(1.0, 0.0, 0.0),
            y_axis=Vector3(0.0, 0.0, 1.0),
            z_axis=Vector3(0.0, -1.0, 0.0),
        ),
        Transform(
            x_axis=Vector3(1.0, 0.0, 0.0),
            y_axis=Vector3(0.0, 0.0, -1.0),
            z_axis=Vector3(0.0, 1.0, 0.0),
        ),
    ),
    "YZ_Plane": (
        2,
        Transform(
            x_axis=Vector3(0.0, 1.0, 0.0),
            y_axis=Vector3(0.0, 0.0, 1.0),
            z_axis=Vector3(1.0, 0.0, 0.0),
        ),
        Transform(
            x_axis=Vector3(0.0, 0.0, -1.0),
            y_axis=Vector3(0.0, 1.0, 0.0),
            z_axis=Vector3(1.0, 0.0, 0.0),
        ),
    ),
}


def _transform_close(
    first: Transform,
    second: Transform,
    tolerance: float = 1e-9,
) -> bool:
    return all(
        math.isclose(left, right, rel_tol=0.0, abs_tol=tolerance)
        for first_vector, second_vector in (
            (first.origin, second.origin),
            (first.x_axis, second.x_axis),
            (first.y_axis, second.y_axis),
            (first.z_axis, second.z_axis),
        )
        for left, right in zip(
            (first_vector.x, first_vector.y, first_vector.z),
            (second_vector.x, second_vector.y, second_vector.z),
            strict=True,
        )
    )


def _origin_plane_frame(
    obj: _NativeObject,
    transform: Transform,
) -> tuple[int, Transform] | None:
    value = _ORIGIN_PLANE_FRAMES.get(obj.name)
    if (
        value is None
        or obj.type_id != "App::Plane"
        or _string(obj, "Role") != obj.name
        or not _transform_close(transform, value[1])
    ):
        return None
    return value[0], value[2]


def _dot(first: Vector3, second: Vector3) -> float:
    return first.x * second.x + first.y * second.y + first.z * second.z


def _plane_reframe(
    source: Transform,
    target: Transform,
) -> tuple[float, float, float, float, float, float]:
    delta = Vector3(
        source.origin.x - target.origin.x,
        source.origin.y - target.origin.y,
        source.origin.z - target.origin.z,
    )
    return (
        _dot(source.x_axis, target.x_axis),
        _dot(source.y_axis, target.x_axis),
        _dot(delta, target.x_axis),
        _dot(source.x_axis, target.y_axis),
        _dot(source.y_axis, target.y_axis),
        _dot(delta, target.y_axis),
    )


def _reframe_geometry(
    geometry: Any,
    reframe: tuple[float, float, float, float, float, float],
) -> Any:
    xx, xy, tx, yx, yy, ty = reframe

    def point(value: Vector2) -> Vector2:
        return Vector2(
            xx * value.x + xy * value.y + tx,
            yx * value.x + yy * value.y + ty,
        )

    def direction(value: Vector2) -> Vector2:
        return Vector2(
            xx * value.x + xy * value.y,
            yx * value.x + yy * value.y,
        )

    determinant = xx * yy - xy * yx
    rotation = math.atan2(yx, xx)

    def circular_angles(start: float, end: float) -> tuple[float, float]:
        if determinant < 0.0:
            return rotation - end, rotation - start
        return start + rotation, end + rotation

    def conic_angles(start: float, end: float) -> tuple[float, float]:
        return (-end, -start) if determinant < 0.0 else (start, end)

    if isinstance(geometry, PointGeometry):
        return replace(geometry, point=point(geometry.point))
    if isinstance(geometry, LineGeometry):
        return replace(
            geometry,
            start=point(geometry.start),
            end=point(geometry.end),
        )
    if isinstance(geometry, CircleGeometry):
        return replace(geometry, center=point(geometry.center))
    if isinstance(geometry, ArcGeometry):
        start, end = circular_angles(geometry.start_angle, geometry.end_angle)
        return replace(
            geometry,
            center=point(geometry.center),
            start_angle=start,
            end_angle=end,
        )
    if isinstance(geometry, EllipseGeometry):
        return replace(
            geometry,
            center=point(geometry.center),
            major_axis=direction(geometry.major_axis),
        )
    if isinstance(geometry, (ArcEllipseGeometry, ArcHyperbolaGeometry)):
        start, end = conic_angles(geometry.start_angle, geometry.end_angle)
        return replace(
            geometry,
            center=point(geometry.center),
            major_axis=direction(geometry.major_axis),
            start_angle=start,
            end_angle=end,
        )
    if isinstance(geometry, HyperbolaGeometry):
        return replace(
            geometry,
            center=point(geometry.center),
            major_axis=direction(geometry.major_axis),
        )
    if isinstance(geometry, ParabolaGeometry):
        return replace(
            geometry,
            center=point(geometry.center),
            axis=direction(geometry.axis),
        )
    if isinstance(geometry, ArcParabolaGeometry):
        start, end = conic_angles(geometry.start_angle, geometry.end_angle)
        return replace(
            geometry,
            center=point(geometry.center),
            axis=direction(geometry.axis),
            start_angle=start,
            end_angle=end,
        )
    if isinstance(geometry, SplineGeometry):
        return replace(
            geometry,
            control_points=tuple(point(value) for value in geometry.control_points),
        )
    return geometry


def _support_target(obj: _NativeObject) -> str:
    for name in ("AttachmentSupport", "Support"):
        node = obj.properties.get(name)
        if node is None:
            continue
        for path, attribute in (
            ("./LinkSubList/Link", "obj"),
            ("./LinkSub", "value"),
            ("./Link", "value"),
            ("./XLink", "name"),
        ):
            link = node.find(path)
            if link is not None and link.get(attribute, ""):
                return link.get(attribute, "")
    return ""


def _is_support_plane_object(obj: _NativeObject, support_targets: set[str]) -> bool:
    if obj.type_id in SUPPORT_PLANE_TYPE_IDS or obj.name in support_targets:
        return True
    marker = f"{obj.type_id} {_proxy_class(obj)}".casefold()
    properties = set(obj.properties)
    return (
        "plane" in marker
        and bool({"Placement", "AttachmentOffset"} & properties)
        and bool(
            {"Support", "AttachmentSupport", "AttachmentOffset", "MapMode"} & properties
        )
    )


def _constraint_expression(expressions: dict[str, str], index: int, name: str) -> str:
    candidates = [f"Constraints[{index}]", f"Constraints.{name}"]
    return next(
        (expressions[value] for value in candidates if value in expressions), ""
    )


def _constraint_element_slots(node: ET.Element) -> tuple[tuple[int, int], ...]:
    element_ids = node.get("ElementIds")
    element_positions = node.get("ElementPositions")
    values: list[tuple[int, int]] = []
    if element_ids is not None and element_positions is not None:
        ids = element_ids.split()
        positions = element_positions.split()
        if len(ids) == len(positions):
            values = [
                (_integer(entity_id, -2000), _integer(position))
                for entity_id, position in zip(ids, positions, strict=True)
            ]
    while len(values) < 3:
        values.append((-2000, 0))
    for index, prefix in enumerate(("First", "Second", "Third")):
        if node.get(prefix) is not None:
            values[index] = (
                _integer(node.get(prefix), -2000),
                _integer(node.get(prefix + "Pos")),
            )
    return tuple(values)


def _parse_sketches(
    objects: tuple[_NativeObject, ...],
    parameters: list[Parameter],
    consumed_expressions: set[tuple[str, str]],
) -> tuple[tuple[SupportPlane, ...], tuple[Sketch, ...]]:
    planes: list[SupportPlane] = []
    plane_ids: dict[str, str] = {}
    source_plane_transforms: dict[str, Transform] = {}
    plane_transforms: dict[str, Transform] = {}
    support_targets = {
        target
        for obj in objects
        if obj.type_id == SKETCH_TYPE_ID and (target := _support_target(obj))
    }
    plane_objects = {
        obj.name: obj
        for obj in objects
        if _is_support_plane_object(obj, support_targets)
    }
    origin_frames: dict[str, tuple[int, Transform]] = {}
    for name, obj in plane_objects.items():
        transform = _transform(_placement_element(obj, "Placement"))
        source_plane_transforms[name] = transform
        frame = _origin_plane_frame(obj, transform)
        if frame is not None:
            origin_frames[name] = frame
    blocked_origin_frames: set[str] = set()
    for obj in objects:
        if obj.type_id != SKETCH_TYPE_ID:
            continue
        support_name = _support_target(obj)
        frame = origin_frames.get(support_name)
        source_transform = source_plane_transforms.get(support_name)
        if (
            frame is None
            or source_transform is None
            or _transform_close(source_transform, frame[1])
        ):
            continue
        constraint_list = _child(obj, "Constraints", "ConstraintList")
        if constraint_list is not None and constraint_list.findall("./Constrain"):
            blocked_origin_frames.add(support_name)
            continue
        geometry_list = _child(obj, "Geometry", "GeometryList")
        geometry_nodes = (
            [] if geometry_list is None else geometry_list.findall("./Geometry")
        )
        if any(
            isinstance(_geometry(node, "")[1], NativeGeometry)
            for node in geometry_nodes
        ):
            blocked_origin_frames.add(support_name)
    for obj in objects:
        if not _is_support_plane_object(obj, support_targets):
            continue
        plane_id = f"freecad:plane:{obj.name}"
        plane_ids[obj.name] = plane_id
        source_transform = source_plane_transforms[obj.name]
        frame = origin_frames.get(obj.name)
        principal = frame is not None and obj.name not in blocked_origin_frames
        transform = frame[1] if principal else source_transform
        plane_transforms[obj.name] = transform
        attributes: dict[str, Any] = {"freecad": _native_object_data(obj)}
        if principal and frame is not None:
            attributes.update(
                {
                    "principal_index": frame[0],
                    "principal_role": obj.name,
                }
            )
        planes.append(
            SupportPlane(
                plane_id,
                _string(obj, "Label", obj.name),
                transform,
                attributes=attributes,
            )
        )
    sketches: list[Sketch] = []
    for obj in objects:
        if obj.type_id != SKETCH_TYPE_ID:
            continue
        sketch_id = f"freecad:sketch:{obj.name}"
        support_name = _support_target(obj)
        support_id = plane_ids.get(support_name)
        if support_id is None:
            support_id = f"freecad:plane:{obj.name}:support"
            plane_ids[f"{obj.name}:support"] = support_id
            planes.append(
                SupportPlane(
                    support_id,
                    support_name or f"{obj.name} support",
                    _transform(_placement_element(obj, "Placement")),
                    attributes={
                        "freecad_support": support_name,
                        "freecad_attachment_offset": (
                            _element_data(obj.properties["AttachmentOffset"])
                            if "AttachmentOffset" in obj.properties
                            else {}
                        ),
                    },
                )
            )
        geometry_list = _child(obj, "Geometry", "GeometryList")
        geometry_nodes = (
            [] if geometry_list is None else geometry_list.findall("./Geometry")
        )
        constraint_list = _child(obj, "Constraints", "ConstraintList")
        constraint_nodes = (
            [] if constraint_list is None else constraint_list.findall("./Constrain")
        )
        source_transform = source_plane_transforms.get(support_name)
        target_transform = plane_transforms.get(support_name)
        reframe = (
            _plane_reframe(source_transform, target_transform)
            if source_transform is not None
            and target_transform is not None
            and not _transform_close(source_transform, target_transform)
            else None
        )
        fixed_indices = {
            _constraint_element_slots(node)[0][0]
            for node in constraint_nodes
            if _integer(node.get("Type"), -1) == 17
        }
        entities: list[SketchEntity] = []
        for index, node in enumerate(geometry_nodes):
            entity_id = f"{sketch_id}:entity:{index}"
            kind, geometry = _geometry(node, entity_id)
            if reframe is not None:
                geometry = _reframe_geometry(geometry, reframe)
            construction_node = node.find("./Construction")
            construction = (
                construction_node is not None
                and construction_node.get("value", "0").casefold() in XML_TRUE_VALUES
            )
            if not construction:
                extension = node.find(
                    "./GeoExtensions/GeoExtension[@type='Sketcher::SketchGeometryExtension']"
                )
                flags = (
                    "" if extension is None else extension.get("geometryModeFlags", "")
                )
                construction = bool(flags and flags[-2:] == "10")
            entities.append(
                SketchEntity(
                    entity_id,
                    kind,
                    geometry,
                    construction=construction,
                    fixed=index in fixed_indices,
                    attributes={
                        "freecad_geometry_id": node.get("id", ""),
                        "freecad": _element_data(node),
                    },
                )
            )
        expressions = _expressions(obj)
        constraints: list[SketchConstraint] = []
        sketch_parameter_ids: list[str] = []
        for index, node in enumerate(constraint_nodes):
            code = _integer(node.get("Type"), -1)
            name = node.get("Name", "") or str(index)
            constraint_id = f"{sketch_id}:constraint:{index}"
            references: list[ConstraintReference] = []
            reference_slots: list[dict[str, Any]] = []
            for slot_index, (entity_index, point_index) in enumerate(
                _constraint_element_slots(node)
            ):
                point = CONSTRAINT_POINT_BY_INDEX.get(point_index, "")
                entity_id = (
                    entities[entity_index].id
                    if 0 <= entity_index < len(entities)
                    else ""
                )
                reference_slots.append(
                    {
                        "slot": (
                            ("first", "second", "third")[slot_index]
                            if slot_index < 3
                            else f"element_{slot_index}"
                        ),
                        "entity_id": entity_id,
                        "point": point,
                        "freecad_geometry_index": entity_index,
                        "freecad_point_index": point_index,
                    }
                )
                if 0 <= entity_index < len(entities):
                    references.append(ConstraintReference(entity_id, point))
            parameter_id: str | None = None
            if code in DIMENSIONAL_CONSTRAINT_CODES:
                parameter_id = f"freecad:parameter:{obj.name}:constraint:{index}"
                value_kind, unit = CONSTRAINT_VALUE_KIND_BY_CODE[code]
                expression_source = _constraint_expression(expressions, index, name)
                if expression_source:
                    for path, source in expressions.items():
                        if source == expression_source and path in {
                            f"Constraints[{index}]",
                            f"Constraints.{name}",
                        }:
                            consumed_expressions.add((obj.name, path))
                parameters.append(
                    Parameter(
                        parameter_id,
                        f"{_string(obj, 'Label', obj.name)}.{name}",
                        ParameterValue(_number(node.get("Value")), value_kind, unit),
                        expression=(
                            Expression(expression_source, language="freecad")
                            if expression_source
                            else None
                        ),
                        owner_id=sketch_id,
                        attributes={
                            "freecad_path": f"Constraints[{index}]",
                            "freecad_constraint": dict(node.attrib),
                        },
                    )
                )
                sketch_parameter_ids.append(parameter_id)
            constraints.append(
                SketchConstraint(
                    constraint_id,
                    CONSTRAINT_KIND_BY_CODE.get(code, ConstraintKind.NATIVE),
                    tuple(references),
                    parameter_id=parameter_id,
                    driving=node.get("IsDriving", "1") != "0",
                    suppressed=node.get("IsActive", "1") == "0",
                    attributes={
                        "freecad_type_code": code,
                        "freecad": dict(node.attrib),
                        "freecad_reference_slots": reference_slots,
                    },
                )
            )
        entity_values = tuple(entities)
        sketches.append(
            Sketch(
                sketch_id,
                _string(obj, "Label", obj.name),
                support_id,
                entity_values,
                constraints=tuple(constraints),
                parameter_ids=tuple(sketch_parameter_ids),
                closed_profile_entity_ids=_closed_profile_entity_ids(entity_values),
                suppressed=not _bool(obj, "Visibility", True),
                attributes={
                    "freecad": _native_object_data(obj),
                    "fully_constrained": _bool(obj, "FullyConstrained"),
                    "external_geometry": (
                        _element_data(obj.properties["ExternalGeometry"])
                        if "ExternalGeometry" in obj.properties
                        else {}
                    ),
                },
            )
        )
    return tuple(planes), tuple(sketches)


def _has_shape_property(obj: _NativeObject) -> bool:
    return any(node.find("./Part") is not None for node in obj.properties.values())


def _is_feature_object(obj: _NativeObject) -> bool:
    if obj.type_id in NON_FEATURE_OBJECT_TYPE_IDS or obj.type_id.startswith(
        ASSEMBLY_OBJECT_TYPE_PREFIX
    ):
        return False
    if (
        obj.type_id in FEATURE_KIND_BY_TYPE_ID
        or obj.type_id in PRIMITIVE_FEATURE_TYPE_IDS
    ):
        return True
    return _has_shape_property(obj)


def _ordered_features(objects: tuple[_NativeObject, ...]) -> tuple[_NativeObject, ...]:
    candidates = [obj for obj in objects if _is_feature_object(obj)]
    names = {obj.name for obj in candidates}
    remaining = list(candidates)
    result: list[_NativeObject] = []
    resolved: set[str] = set()
    while remaining:
        ready = [
            obj
            for obj in remaining
            if not ({value for value in obj.dependencies if value in names} - resolved)
        ]
        if not ready:
            raise NativeFreeCADError(
                "FreeCAD feature dependency graph contains a cycle"
            )
        ready.sort(key=lambda item: item.index)
        for obj in ready:
            result.append(obj)
            resolved.add(obj.name)
            remaining.remove(obj)
    return tuple(result)


def _is_body_container(obj: _NativeObject) -> bool:
    return obj.type_id in BODY_CONTAINER_TYPE_IDS or (
        obj.type_id == "App::DocumentObjectGroup"
        and "SourceBodyJSON" in obj.properties
        and "Tip" in obj.properties
    )


def _feature_kind(obj: _NativeObject) -> FeatureKind:
    declared = _string(obj, "FeatureKind").casefold()
    if declared:
        try:
            declared_kind = FeatureKind(declared)
        except ValueError:
            declared_kind = None
        if declared_kind is not None:
            return declared_kind
    if obj.type_id == "Part::Feature":
        return FeatureKind.IMPORTED
    if obj.type_id in PRIMITIVE_FEATURE_TYPE_IDS:
        return FeatureKind.PRIMITIVE
    return FEATURE_KIND_BY_TYPE_ID.get(obj.type_id, FeatureKind.NATIVE)


def _feature_selections(obj: _NativeObject) -> tuple[Selection, ...]:
    values: list[tuple[str, str, str]] = []
    for property_name, property_element in obj.properties.items():
        for link in property_element.findall("./LinkSub"):
            target = link.get("value", "")
            values.extend(
                (property_name, target, subelement)
                for child in link.findall("./Sub")
                if (subelement := child.get("value", ""))
            )
        for link in property_element.findall("./XLink"):
            target = link.get("name", "")
            values.extend(
                (property_name, target, subelement)
                for child in link.findall("./Sub")
                if (subelement := child.get("value", ""))
            )
        for link in property_element.findall("./LinkSubList/Link"):
            target = link.get("obj", link.get("value", ""))
            subelements = [child.get("value", "") for child in link.findall("./Sub")]
            if link.get("sub", ""):
                subelements.append(link.get("sub", ""))
            values.extend(
                (property_name, target, subelement)
                for subelement in subelements
                if subelement
            )
        for link in property_element.findall("./XLinkSubList/XLink"):
            target = link.get("name", "")
            values.extend(
                (property_name, target, subelement)
                for child in link.findall("./Sub")
                if (subelement := child.get("value", ""))
            )
    result: list[Selection] = []
    for index, (property_name, target, subelement) in enumerate(values):
        token = subelement.rsplit(".", 1)[-1]
        entity_kind = next(
            (
                kind.value
                for prefix, kind in SUBELEMENT_KIND_BY_PREFIX.items()
                if token.startswith(prefix)
            ),
            MateEntityKind.NATIVE.value,
        )
        selection_id = f"freecad:selection:{obj.name}:{property_name}:{index}"
        result.append(
            Selection(
                selection_id,
                f"{_string(obj, 'Label', obj.name)}.{property_name}.{subelement}",
                (SelectionPathElement(entity_kind, target, subelement),),
                provenance=Provenance(
                    FORMAT_ID, f"{obj.name}.{property_name}.{subelement}"
                ),
                attributes={
                    "freecad_object": obj.name,
                    "freecad_property": property_name,
                    "freecad_target": target,
                    "freecad_subelement": subelement,
                },
            )
        )
    return tuple(result)


def _explicit_selections(objects: tuple[_NativeObject, ...]) -> tuple[Selection, ...]:
    result: list[Selection] = []
    for obj in objects:
        selection_id = _string(obj, "KitSelectionId")
        node = obj.properties.get("Selection")
        if not selection_id or node is None:
            continue
        kinds_node = obj.properties.get("EntityKinds")
        kinds = (
            [
                child.get("value", "")
                for child in kinds_node.findall("./StringList/String")
            ]
            if kinds_node is not None
            else []
        )
        paths: list[SelectionPathElement] = []
        for index, link in enumerate(node.findall("./LinkSubList/Link")):
            target = link.get("obj", link.get("value", ""))
            subelements = [
                value
                for child in link.findall("./Sub")
                if (value := child.get("value", ""))
            ]
            if link.get("sub") is not None:
                subelements.insert(0, link.get("sub", ""))
            if not subelements:
                subelements.append("")
            for subelement in subelements:
                token = subelement.rsplit(".", 1)[-1]
                inferred = next(
                    (
                        kind.value
                        for prefix, kind in SUBELEMENT_KIND_BY_PREFIX.items()
                        if token.startswith(prefix)
                    ),
                    MateEntityKind.NATIVE.value,
                )
                paths.append(
                    SelectionPathElement(
                        (
                            kinds[index]
                            if index < len(kinds) and kinds[index]
                            else inferred
                        ),
                        target,
                        subelement,
                    )
                )
        point_node = _child(obj, "SelectionPoint", "PropertyVector")
        point = (
            Vector3(
                _number(point_node.get("valueX")),
                _number(point_node.get("valueY")),
                _number(point_node.get("valueZ")),
            )
            if point_node is not None
            else None
        )
        result.append(
            Selection(
                selection_id,
                _string(obj, "Label", obj.name),
                tuple(paths),
                point=point,
                provenance=Provenance(FORMAT_ID, obj.name),
                attributes={"freecad": _native_object_data(obj)},
            )
        )
    return tuple(result)


def _feature_parameters(
    obj: _NativeObject,
    feature_id: str,
    parameters: list[Parameter],
    consumed_expressions: set[tuple[str, str]],
) -> tuple[str, ...]:
    result: list[str] = []
    expressions = _expressions(obj)
    for name, node in obj.properties.items():
        value = _property_parameter_value(node)
        if value is None:
            continue
        parameter_id = f"freecad:parameter:{obj.name}:{name}"
        expression_source = expressions.get(name, "")
        if expression_source:
            consumed_expressions.add((obj.name, name))
        parameters.append(
            Parameter(
                parameter_id,
                f"{_string(obj, 'Label', obj.name)}.{name}",
                value,
                expression=(
                    Expression(expression_source, language="freecad")
                    if expression_source
                    else None
                ),
                owner_id=feature_id,
                attributes={
                    "freecad_path": name,
                    "freecad_property_type": node.get("type", ""),
                    "freecad_property": _element_data(node),
                },
            )
        )
        result.append(parameter_id)
    return tuple(result)


def _extrusion_end_condition(
    type_code: int, object_type_id: str
) -> ExtrusionEndCondition:
    extrusion_type = EXTRUSION_TYPE_BY_CODE.get(type_code)
    if extrusion_type is None:
        return ExtrusionEndCondition.NATIVE
    if (
        object_type_id == POCKET_TYPE_ID
        and extrusion_type.pocket_end_condition is not None
    ):
        return extrusion_type.pocket_end_condition
    return extrusion_type.end_condition


def _extrusion_definition(obj: _NativeObject) -> ExtrusionFeature:
    end_condition = _extrusion_end_condition(_enum(obj, "Type"), obj.type_id)
    side_type = _enum(obj, "SideType", -1)
    second_end_condition = (
        _extrusion_end_condition(_enum(obj, "Type2"), obj.type_id)
        if side_type == 1
        else None
    )
    direction_node = _child(obj, "Direction", "PropertyVector")
    direction = None
    if direction_node is not None:
        direction = Vector3(
            _number(direction_node.get("valueX")),
            _number(direction_node.get("valueY")),
            _number(direction_node.get("valueZ")),
        )
    return ExtrusionFeature(
        ParameterValue(_float(obj, "Length"), ValueKind.LENGTH, "mm"),
        end_condition=end_condition,
        reversed=_bool(obj, "Reversed"),
        symmetric=side_type == 2 or _bool(obj, "Midplane"),
        direction=direction,
        second_length=(
            ParameterValue(_float(obj, "Length2"), ValueKind.LENGTH, "mm")
            if "Length2" in obj.properties
            else None
        ),
        second_end_condition=second_end_condition,
        offset=(
            ParameterValue(_float(obj, "Offset"), ValueKind.LENGTH, "mm")
            if "Offset" in obj.properties
            else None
        ),
        second_offset=(
            ParameterValue(_float(obj, "Offset2"), ValueKind.LENGTH, "mm")
            if "Offset2" in obj.properties
            else None
        ),
        draft_angle=(
            ParameterValue(_float(obj, "TaperAngle"), ValueKind.ANGLE, "deg")
            if "TaperAngle" in obj.properties
            else None
        ),
        second_draft_angle=(
            ParameterValue(_float(obj, "TaperAngle2"), ValueKind.ANGLE, "deg")
            if "TaperAngle2" in obj.properties
            else None
        ),
        up_to_reference=_link(obj, "UpToFace") or _link(obj, "UpToShape"),
        second_up_to_reference=_link(obj, "UpToFace2") or _link(obj, "UpToShape2"),
    )


def _part_extrusion_definition(obj: _NativeObject) -> ExtrusionFeature:
    direction_node = _child(obj, "Dir", "PropertyVector")
    direction = None
    if direction_node is not None:
        direction = Vector3(
            _number(direction_node.get("valueX")),
            _number(direction_node.get("valueY")),
            _number(direction_node.get("valueZ")),
        )
    forward = _float(obj, "LengthFwd")
    reverse = _float(obj, "LengthRev")
    return ExtrusionFeature(
        ParameterValue(forward, ValueKind.LENGTH, "mm"),
        end_condition=ExtrusionEndCondition.BLIND,
        reversed=False,
        symmetric=forward > 0.0 and reverse > 0.0 and abs(forward - reverse) <= 1e-12,
        direction=direction,
        second_length=ParameterValue(reverse, ValueKind.LENGTH, "mm"),
    )


def _build_brep_payloads(
    native: _NativeArchive, feature_ids: dict[str, str], body_ids: dict[str, str]
) -> tuple[tuple[BrepPayload, ...], dict[str, list[str]]]:
    payloads: list[BrepPayload] = []
    owner_payloads: dict[str, list[str]] = {}
    for obj in native.objects:
        for property_name, node in obj.properties.items():
            part = node.find("./Part")
            if part is None:
                continue
            filename = "" if part is None else part.get("file", "")
            if not filename:
                continue
            data = native.entries.get(filename)
            if data is None:
                continue
            payload_id = f"freecad:brep:{obj.name}:{property_name}"
            header = data[:256].decode("ascii", "ignore")
            match = re.search(r"CASCADE Topology V\d+", header)
            attributes: dict[str, Any] = {
                "freecad_object": obj.name,
                "freecad_object_type": obj.type_id,
                "freecad_property": property_name,
                "freecad_property_data": _element_data(node),
                "freecad_part_attributes": (
                    dict(part.attrib) if part is not None else {}
                ),
            }
            sidecars = []
            for child in node.findall(".//*[@file]"):
                sidecar_name = child.get("file", "")
                if not sidecar_name or sidecar_name == filename:
                    continue
                sidecar_data = native.entries.get(sidecar_name)
                if sidecar_data is not None:
                    sidecars.append(
                        {"source_stream": sidecar_name, "data": sidecar_data}
                    )
            if sidecars:
                attributes["freecad_sidecars"] = sidecars
            if property_name == "Shape" and obj.name in feature_ids:
                attributes["feature_id"] = feature_ids[obj.name]
            if property_name == "Shape" and obj.name in body_ids:
                attributes["body_id"] = body_ids[obj.name]
            payloads.append(
                BrepPayload(
                    payload_id,
                    "opencascade",
                    "shape",
                    match.group(0) if match else "FreeCAD PartShape",
                    hashlib.sha256(data).hexdigest(),
                    data=data,
                    source_stream=filename,
                    provenance=Provenance(FORMAT_ID, f"{obj.name}.{property_name}"),
                    attributes=attributes,
                    role=PayloadRole.BREP,
                    file_extension=".brep",
                )
            )
            owner_payloads.setdefault(obj.name, []).append(payload_id)
    return tuple(payloads), owner_payloads


def _decoded_document_brep(
    payloads: tuple[BrepPayload, ...], bodies: tuple[Body, ...]
) -> BrepModel | None:
    if not bodies:
        return None
    selected: set[str] = set()
    models: list[BrepModel] = []
    for body in bodies:
        BodyMatches = tuple(
            payload
            for payload in payloads
            if payload.role == PayloadRole.BREP
            and payload.data is not None
            and payload.attributes.get("body_id") == body.id
        )
        FeatureMatches = tuple(
            payload
            for payload in payloads
            if payload.role == PayloadRole.BREP
            and payload.data is not None
            and payload.attributes.get("feature_id") == body.final_feature_id
        )
        Matches = BodyMatches or FeatureMatches
        if len(Matches) != 1 or Matches[0].id in selected:
            return None
        payload = Matches[0]
        selected.add(payload.id)
        digest = hashlib.sha256(payload.id.encode("utf-8")).hexdigest()[:20]
        model = decode_ascii_brep(
            payload.data,
            id_prefix=f"freecad:occ:{digest}",
            design_body_id=body.id,
            attributes={
                "brep_payload_id": payload.id,
                "feature_id": body.final_feature_id,
            },
        )
        if model is None:
            return None
        models.append(model)
    return BrepModel(
        curves=tuple(value for model in models for value in model.curves),
        pcurves=tuple(value for model in models for value in model.pcurves),
        surfaces=tuple(value for model in models for value in model.surfaces),
        vertices=tuple(value for model in models for value in model.vertices),
        edges=tuple(value for model in models for value in model.edges),
        coedges=tuple(value for model in models for value in model.coedges),
        loops=tuple(value for model in models for value in model.loops),
        wires=tuple(value for model in models for value in model.wires),
        faces=tuple(value for model in models for value in model.faces),
        face_uses=tuple(value for model in models for value in model.face_uses),
        shells=tuple(value for model in models for value in model.shells),
        shell_uses=tuple(value for model in models for value in model.shell_uses),
        regions=tuple(value for model in models for value in model.regions),
        bodies=tuple(value for model in models for value in model.bodies),
    )


def _parse_meshes(native: _NativeArchive) -> tuple[Mesh, ...]:
    result: list[Mesh] = []
    for obj in native.objects:
        for property_name, property_element in obj.properties.items():
            value = property_element.find("./Mesh")
            if value is None:
                continue
            filename = value.get("file", "")
            data = native.entries.get(filename)
            vertices: tuple[Vector3, ...] = ()
            triangles: tuple[tuple[int, int, int], ...] = ()
            if data is not None and len(data) >= 296:
                try:
                    endian = "<"
                    magic, version = struct.unpack_from("<II", data)
                    if (magic, version) != (0xA0B0C0D0, 0x00010000):
                        magic, version = struct.unpack_from(">II", data)
                        endian = ">"
                    vertex_count, triangle_count = struct.unpack_from(
                        f"{endian}II", data, 264
                    )
                    expected = 272 + vertex_count * 12 + triangle_count * 24 + 24
                    if (
                        magic == 0xA0B0C0D0
                        and version == 0x00010000
                        and expected <= len(data)
                    ):
                        vertices = tuple(
                            Vector3(
                                *struct.unpack_from(
                                    f"{endian}fff", data, 272 + index * 12
                                )
                            )
                            for index in range(vertex_count)
                        )
                        triangle_offset = 272 + vertex_count * 12
                        triangles = tuple(
                            struct.unpack_from(
                                f"{endian}III",
                                data,
                                triangle_offset + index * 24,
                            )
                            for index in range(triangle_count)
                        )
                except struct.error:
                    vertices = ()
                    triangles = ()
            elif value.find("./Points") is not None:
                vertices = tuple(
                    Vector3(
                        _number(point.get("x")),
                        _number(point.get("y")),
                        _number(point.get("z")),
                    )
                    for point in value.findall("./Points/P")
                )
                triangles = tuple(
                    (
                        _integer(face.get("p0"), -1),
                        _integer(face.get("p1"), -1),
                        _integer(face.get("p2"), -1),
                    )
                    for face in value.findall("./Faces/F")
                )
            if not vertices and not triangles:
                continue
            if any(
                any(index < 0 or index >= len(vertices) for index in triangle)
                for triangle in triangles
            ):
                continue
            result.append(
                Mesh(
                    f"freecad:mesh:{obj.name}:{property_name}",
                    _string(obj, "Label", obj.name),
                    vertices,
                    triangles,
                    provenance=Provenance(FORMAT_ID, f"{obj.name}.{property_name}"),
                    attributes={
                        "freecad": _native_object_data(obj),
                        "source_stream": filename,
                    },
                )
            )
    return tuple(result)


def _proxy_class(obj: _NativeObject) -> str:
    node = obj.properties.get("Proxy")
    if node is None:
        return ""
    value = node.find("./Python")
    return "" if value is None else value.get("class", "")


def _enumeration_choice(obj: _NativeObject, name: str) -> str:
    node = obj.properties.get(name)
    if node is None:
        return ""
    selected = node.find("./Integer")
    if selected is None:
        return ""
    index = _integer(selected.get("value"), -1)
    choices = [
        child.get("value", "") for child in node.findall("./CustomEnumList/Enum")
    ]
    return choices[index] if 0 <= index < len(choices) else str(index)


def _xlink_data(obj: _NativeObject, name: str) -> dict[str, Any]:
    node = obj.properties.get(name)
    if node is None:
        return {"file": "", "stamp": "", "name": "", "subelements": []}
    value = node.find("./XLink")
    if value is None:
        return {"file": "", "stamp": "", "name": "", "subelements": []}
    subelements = [child.get("value", "") for child in value.findall("./Sub")]
    if not subelements and value.get("name", ""):
        subelements.append("")
    return {
        "file": value.get("file", ""),
        "stamp": value.get("stamp", ""),
        "name": value.get("name", ""),
        "subelements": subelements,
    }


def _linked_object_property(obj: _NativeObject) -> str:
    linked = obj.properties.get("LinkedObject")
    if linked is not None and linked.find("./XLink") is not None:
        return "LinkedObject"
    marker = " ".join(
        (
            obj.type_id,
            _proxy_class(obj),
            *(extension.get("type", "") for extension in obj.extensions),
        )
    ).casefold()
    if "link" not in marker:
        return ""
    candidates = [
        name
        for name, node in obj.properties.items()
        if node.find("./XLink") is not None
        and name not in JOINT_RESERVED_LINK_PROPERTIES
    ]
    named = next(
        (name for name in candidates if "link" in name.casefold()),
        "",
    )
    return named or (candidates[0] if len(candidates) == 1 else "")


def _linked_object_data(obj: _NativeObject) -> dict[str, Any]:
    property_name = _linked_object_property(obj)
    return _xlink_data(obj, property_name) if property_name else _xlink_data(obj, "")


def _is_link_object(obj: _NativeObject) -> bool:
    return bool(_linked_object_property(obj))


def _is_assembly_link_object(obj: _NativeObject) -> bool:
    return _is_link_object(obj) and {"Group", "Rigid"}.issubset(obj.properties)


def _is_grounded_joint_object(obj: _NativeObject) -> bool:
    proxy = _proxy_class(obj).casefold()
    return "groundedjoint" in proxy or JOINT_GROUND_PROPERTY in obj.properties


def _is_joint_object(obj: _NativeObject) -> bool:
    if _is_grounded_joint_object(obj):
        return True
    marker = f"{obj.type_id} {_proxy_class(obj)}".casefold()
    has_reference = bool(set(JOINT_REFERENCE_PROPERTIES) & set(obj.properties))
    return (
        ("joint" in marker and has_reference)
        or has_reference
        and bool(JOINT_TYPE_PROPERTIES & set(obj.properties))
    )


def _joint_group_object(
    objects: tuple[_NativeObject, ...], by_name: dict[str, _NativeObject]
) -> _NativeObject | None:
    exact = next(
        (obj for obj in objects if obj.type_id == ASSEMBLY_JOINT_GROUP_TYPE_ID),
        None,
    )
    if exact is not None:
        return exact
    candidates: list[_NativeObject] = []
    for obj in objects:
        members = [
            by_name[name] for name in _link_list(obj, "Group") if name in by_name
        ]
        joint_members = [member for member in members if _is_joint_object(member)]
        marker = f"{obj.type_id} {_proxy_class(obj)}".casefold()
        if joint_members and (
            "jointgroup" in marker or len(joint_members) == len(members)
        ):
            candidates.append(obj)
    return candidates[0] if len(candidates) == 1 else None


def _assembly_root_object(objects: tuple[_NativeObject, ...]) -> _NativeObject | None:
    exact = next(
        (obj for obj in objects if obj.type_id == ASSEMBLY_ROOT_TYPE_ID),
        None,
    )
    if exact is not None:
        return exact
    by_name = {obj.name: obj for obj in objects}
    grouped_names = {
        name for obj in objects for name in _link_list(obj, "Group") if name in by_name
    }
    candidates: list[tuple[tuple[int, int, int, int], _NativeObject]] = []
    for obj in objects:
        if _is_link_object(obj) or _is_joint_object(obj):
            continue
        links = [
            by_name[name]
            for name in _link_list(obj, "Group")
            if name in by_name and _is_link_object(by_name[name])
        ]
        if not links:
            continue
        marker = f"{obj.type_id} {_proxy_class(obj)} {_string(obj, 'Type')}".casefold()
        score = (
            int("assembly" in marker),
            int(obj.name not in grouped_names),
            sum(_is_assembly_link_object(link) for link in links),
            len(links),
        )
        candidates.append((score, obj))
    if not candidates:
        return None
    return max(candidates, key=lambda value: (value[0], -value[1].index))[1]


def _mate_entity_kind(value: str) -> MateEntityKind:
    token = value.rsplit(".", 1)[-1]
    for prefix, kind in SUBELEMENT_KIND_BY_PREFIX.items():
        if token.startswith(prefix):
            return kind
    return MateEntityKind.NATIVE


def _mate_values(
    obj: _NativeObject,
    kind: MateKind | str,
    mate_id: str,
    parameters: list[Parameter],
    consumed_expressions: set[tuple[str, str]],
) -> tuple[ParameterValue | None, tuple[str, ...]]:
    value_properties: list[tuple[str, ValueKind, str]] = []
    primary_property = ""
    if kind == MateKind.ANGLE:
        primary_property = "Angle"
        value_properties.append(("Angle", ValueKind.ANGLE, "deg"))
    elif kind in MATE_KINDS_USING_DISTANCE:
        primary_property = "Distance"
        value_properties.append(("Distance", ValueKind.LENGTH, "mm"))
    if kind in MATE_KINDS_USING_SECOND_DISTANCE:
        value_properties.append(("Distance2", ValueKind.LENGTH, "mm"))
    for enable_name, property_name, value_kind, unit in (
        ("EnableLengthMin", "LengthMin", ValueKind.LENGTH, "mm"),
        ("EnableLengthMax", "LengthMax", ValueKind.LENGTH, "mm"),
        ("EnableAngleMin", "AngleMin", ValueKind.ANGLE, "deg"),
        ("EnableAngleMax", "AngleMax", ValueKind.ANGLE, "deg"),
    ):
        if _bool(obj, enable_name):
            value_properties.append((property_name, value_kind, unit))
    expressions = _expressions(obj)
    primary_value: ParameterValue | None = None
    parameter_ids: list[str] = []
    for property_name, value_kind, unit in value_properties:
        if property_name not in obj.properties:
            continue
        value = ParameterValue(_float(obj, property_name), value_kind, unit)
        if property_name == primary_property:
            primary_value = value
        parameter_id = f"freecad:parameter:{obj.name}:{property_name}"
        expression_source = expressions.get(property_name, "")
        if expression_source:
            consumed_expressions.add((obj.name, property_name))
        parameters.append(
            Parameter(
                parameter_id,
                f"{_string(obj, 'Label', obj.name)}.{property_name}",
                value,
                expression=(
                    Expression(expression_source, language="freecad")
                    if expression_source
                    else None
                ),
                owner_id=mate_id,
                attributes={
                    "freecad_path": property_name,
                    "freecad_property": _element_data(obj.properties[property_name]),
                },
            )
        )
        parameter_ids.append(parameter_id)
    return primary_value, tuple(parameter_ids)


def _stored_mate_value(obj: _NativeObject) -> ParameterValue | None:
    source = _string(obj, "MateValueJSON")
    if not source:
        return None
    try:
        value = json.loads(source)
    except (json.JSONDecodeError, RecursionError):
        return None
    if not isinstance(value, dict) or "value" not in value:
        return None
    kind_value = value.get("kind", ValueKind.NUMBER)
    if isinstance(kind_value, dict):
        kind_value = kind_value.get("value", ValueKind.NUMBER)
    try:
        kind = ValueKind(str(kind_value))
    except ValueError:
        kind = ValueKind.NUMBER
    raw = value.get("value")
    if not isinstance(raw, (str, int, float, bool)):
        return None
    return ParameterValue(raw, kind, str(value.get("unit", "")))


def _embedded_component_document(
    target: str,
    target_obj: _NativeObject | None,
    identity: str,
    payloads: tuple[BrepPayload, ...],
) -> tuple[str, CadDocument, tuple[str, ...]]:
    digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:20]
    document_id = f"freecad:component-document:{digest}"
    feature_id = f"freecad:component-feature:{digest}"
    component_payloads = tuple(
        replace(
            payload,
            id=f"{payload.id}:component:{digest}",
            attributes={**dict(payload.attributes), "feature_id": feature_id},
        )
        for payload in payloads
    )
    label = _string(target_obj, "Label", target) if target_obj is not None else target
    feature = FeatureStep(
        feature_id,
        label,
        FeatureKind.IMPORTED if component_payloads else FeatureKind.NATIVE,
        0,
        provenance=Provenance(FORMAT_ID, target),
        attributes={
            "freecad": (
                _native_object_data(target_obj) if target_obj is not None else {}
            ),
            "brep_payload_ids": [payload.id for payload in component_payloads],
        },
    )
    component = CadDocument(
        CadSource(
            FORMAT_ID,
            identity,
            hashlib.sha256(
                "".join(payload.sha256 for payload in component_payloads).encode(
                    "ascii"
                )
            ).hexdigest(),
        ),
        (Configuration(f"{document_id}:configuration", "Default", active=True),),
        (),
        (),
        (),
        (),
        (feature,),
        (),
        brep_payloads=component_payloads,
        metadata={"freecad_component_target": target, "freecad_identity": identity},
    )
    component = replace(
        component,
        capabilities=infer_capabilities(component, roundtrip_metadata=True),
    )
    component.assert_valid()
    return document_id, component, ()


def _resolved_source_path(source_path: str) -> Path | None:
    if not source_path:
        return None
    try:
        path = Path(source_path).expanduser().resolve(strict=True)
    except (OSError, RuntimeError):
        return None
    return path if path.is_file() else None


def _is_reparse_path(path: Path, root: Path) -> bool:
    current = path
    while True:
        try:
            details = current.lstat()
        except OSError:
            return True
        if current.is_symlink() or getattr(details, "st_file_attributes", 0) & 0x400:
            return True
        if current == root:
            return False
        if root not in current.parents:
            return True
        current = current.parent


def _external_documents(
    native: _NativeArchive,
    source_path: str,
    state: _ExternalState | None,
    depth: int,
) -> tuple[dict[str, tuple[str, CadDocument]], list[dict[str, str]]]:
    source = _resolved_source_path(source_path)
    files = sorted(
        {
            str(linked["file"])
            for obj in native.objects
            if _is_link_object(obj) and (linked := _linked_object_data(obj))["file"]
        }
    )
    resolved: dict[str, tuple[str, CadDocument]] = {}
    unresolved: list[dict[str, str]] = []
    for filename in files:
        reason = ""
        candidate: Path | None = None
        if source is None or state is None:
            reason = "source location is unavailable"
        elif depth >= _MAX_EXTERNAL_DEPTH:
            reason = "external reference depth exceeds safe limits"
        elif Path(filename).is_absolute():
            reason = "absolute external paths are not allowed"
        else:
            try:
                candidate = (source.parent / filename).resolve(strict=True)
                candidate.relative_to(state.root)
            except (OSError, RuntimeError, ValueError):
                reason = "external reference is missing or outside the document root"
        if (
            not reason
            and candidate is not None
            and _is_reparse_path(candidate, state.root)
        ):
            reason = "external reference traverses a reparse point"
        if (
            not reason
            and candidate is not None
            and candidate.suffix.casefold() != SUFFIX.casefold()
        ):
            reason = "external reference is not an FCStd document"
        if not reason and candidate is not None and candidate in state.active:
            reason = "external reference cycle detected"
        if reason:
            unresolved.append({"file": filename, "reason": reason})
            continue
        if candidate is None:
            unresolved.append(
                {"file": filename, "reason": "external reference is invalid"}
            )
            continue
        identity = candidate.relative_to(state.root).as_posix()
        cached = state.cache.get(candidate)
        if cached is not None:
            resolved[filename] = (identity, cached)
            continue
        try:
            size = candidate.stat().st_size
        except OSError:
            unresolved.append(
                {"file": filename, "reason": "external reference is unreadable"}
            )
            continue
        if (
            size < 0
            or size > _MAX_ENTRY_SIZE
            or state.file_count >= _MAX_EXTERNAL_FILES
            or state.total_bytes + size > _MAX_TOTAL_SIZE
        ):
            unresolved.append(
                {"file": filename, "reason": "external reference exceeds safe limits"}
            )
            continue
        try:
            child_data = candidate.read_bytes()
        except OSError:
            unresolved.append(
                {"file": filename, "reason": "external reference is unreadable"}
            )
            continue
        state.file_count += 1
        state.total_bytes += len(child_data)
        state.active.add(candidate)
        try:
            try:
                manifest = extract_manifest_from_fcstd(child_data)
            except ValueError as exc:
                if str(exc) != "FCStd archive has no embedded Kit interchange document":
                    raise NativeFreeCADError(str(exc)) from exc
                child = read_native_fcstd(
                    child_data,
                    str(candidate),
                    _external_state=state,
                    _external_depth=depth + 1,
                )
            else:
                child = CadDocument.from_dict(manifest)
        except (NativeFreeCADError, TypeError, ValueError, RecursionError) as exc:
            unresolved.append({"file": filename, "reason": str(exc)})
            continue
        finally:
            state.active.discard(candidate)
        state.cache[candidate] = child
        resolved[filename] = (identity, child)
    return resolved, unresolved


def _parse_assembly(
    native: _NativeArchive,
    owner_payloads: dict[str, list[str]],
    brep_payloads: tuple[BrepPayload, ...],
    external_documents: dict[str, tuple[str, CadDocument]],
    unresolved_external: list[dict[str, str]],
    parameters: list[Parameter],
    consumed_expressions: set[tuple[str, str]],
) -> AssemblyData | None:
    root = _assembly_root_object(native.objects)
    if root is None:
        return None
    objects = {obj.name: obj for obj in native.objects}
    root_definition_id = f"freecad:definition:{root.name}"
    root_group = _link_list(root, "Group")
    links = [
        objects[name]
        for name in root_group
        if name in objects and _is_link_object(objects[name])
    ]
    if links:
        grouped_names = {obj.name for obj in links}
        links.extend(
            obj
            for obj in native.objects
            if obj.name not in grouped_names
            and _is_link_object(obj)
            and _linked_object_data(obj)["file"]
        )
    else:
        links = [obj for obj in native.objects if _is_link_object(obj)]
    joint_group = _joint_group_object(native.objects, objects)
    joint_names = _link_list(joint_group, "Group") if joint_group is not None else ()
    if not joint_names:
        joint_names = tuple(obj.name for obj in native.objects if _is_joint_object(obj))
    joint_objects = [objects[name] for name in joint_names if name in objects]
    grounded_by_target = {
        target: obj
        for obj in joint_objects
        if _is_grounded_joint_object(obj)
        and (target := _link(obj, JOINT_GROUND_PROPERTY))
    }
    grounded_targets = set(grounded_by_target)
    definitions: list[ComponentDefinition] = [
        ComponentDefinition(
            root_definition_id,
            _string(root, "Label", root.name),
            ComponentKind.ASSEMBLY,
            provenance=Provenance(FORMAT_ID, root.name),
            attributes={"freecad": _native_object_data(root)},
        )
    ]
    definition_ids: dict[tuple[str, str], str] = {}
    documents: list[ComponentDocument] = []
    instances: list[ComponentInstance] = []
    instance_ids: dict[str, str] = {}
    for order, link_obj in enumerate(links):
        linked = _linked_object_data(link_obj)
        target = str(linked["name"]) or link_obj.name
        source_file = str(linked["file"]).replace("\\", "/")
        external = external_documents.get(str(linked["file"]))
        source_identity = (
            external[0]
            if external is not None
            else PurePosixPath(source_file).as_posix() if source_file else ""
        )
        definition_key = (source_identity, target)
        definition_id = definition_ids.get(definition_key)
        if definition_id is None:
            identity = f"{source_identity}#{target}"
            digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:20]
            definition_id = f"freecad:definition:{digest}"
            definition_ids[definition_key] = definition_id
            target_obj = objects.get(target)
            target_payload_ids = set(owner_payloads.get(target, []))
            target_payloads = tuple(
                payload
                for payload in brep_payloads
                if payload.id in target_payload_ids
                and payload.attributes.get("freecad_property") == "Shape"
            )
            if external is not None:
                component = external[1]
                document_id = f"freecad:component-document:{digest}"
                body_ids = tuple(body.id for body in component.bodies)
            else:
                document_id, component, body_ids = _embedded_component_document(
                    target, target_obj, identity, target_payloads
                )
            documents.append(ComponentDocument(document_id, component))
            definitions.append(
                ComponentDefinition(
                    definition_id,
                    (
                        _string(target_obj, "Label", target)
                        if target_obj is not None
                        else target
                    ),
                    (
                        ComponentKind.ASSEMBLY
                        if _is_assembly_link_object(link_obj)
                        or component.assembly is not None
                        else ComponentKind.PART
                    ),
                    document_id=document_id,
                    body_ids=body_ids,
                    source_path=source_file,
                    source_format_id=FORMAT_ID,
                    source_sha256=component.source.sha256,
                    provenance=Provenance(FORMAT_ID, target),
                    attributes={
                        "freecad": (
                            _native_object_data(target_obj)
                            if target_obj is not None
                            else {}
                        ),
                        "brep_payload_ids": owner_payloads.get(target, []),
                        "linked_object": linked,
                    },
                )
            )
        instance_id = f"freecad:instance:{link_obj.name}"
        instance_ids[link_obj.name] = instance_id
        instances.append(
            ComponentInstance(
                instance_id,
                _string(link_obj, "Label", link_obj.name),
                definition_id,
                root_definition_id,
                Matrix4(_placement_matrix(_placement_element(link_obj, "Placement"))),
                order=order,
                reference_number=str(order + 1),
                hidden=not _bool(link_obj, "Visibility", True),
                fixed=link_obj.name in grounded_targets,
                provenance=Provenance(FORMAT_ID, link_obj.name),
                attributes={
                    "freecad": _native_object_data(link_obj),
                    "linked_object": linked,
                    "link_placement": list(
                        _placement_matrix(_placement_element(link_obj, "LinkPlacement"))
                    ),
                    "grounded_joint": (
                        _native_object_data(grounded_by_target[link_obj.name])
                        if link_obj.name in grounded_by_target
                        else {}
                    ),
                },
            )
        )
    mate_entities: list[MateEntity] = []
    mates: list[MateConstraint] = []
    mate_ids_by_name: dict[str, str] = {}
    for order, obj in enumerate(joint_objects):
        if _is_grounded_joint_object(obj):
            continue
        mate_id = f"freecad:mate:{obj.name}"
        mate_ids_by_name[obj.name] = mate_id
        entity_ids: list[str] = []
        references: list[dict[str, Any]] = []
        joint_type = _enumeration_choice(obj, "JointType")
        stored_kind = _string(obj, "MateType")
        if stored_kind:
            try:
                kind: MateKind | str = MateKind(stored_kind)
            except ValueError:
                kind = stored_kind
        else:
            kind = MATE_KIND_BY_JOINT_TYPE.get(joint_type, MateKind.NATIVE)
        for reference_index, property_name in enumerate(
            JOINT_REFERENCE_PROPERTIES, start=1
        ):
            reference = _xlink_data(obj, property_name)
            references.append(reference)
            placement = _placement_element(obj, f"Placement{reference_index}")
            frame = None if placement is None else Matrix4(_placement_matrix(placement))
            for sub_index, subelement in enumerate(reference["subelements"]):
                component_name, separator, source_entity_id = str(subelement).partition(
                    "."
                )
                if not separator:
                    source_entity_id = component_name
                    component_name = ""
                entity_id = (
                    f"freecad:mate-entity:{obj.name}:{reference_index}:{sub_index}"
                )
                entity_ids.append(entity_id)
                mate_entities.append(
                    MateEntity(
                        entity_id,
                        root_definition_id,
                        (
                            (instance_ids[component_name],)
                            if component_name in instance_ids
                            else ()
                        ),
                        _mate_entity_kind(source_entity_id),
                        source_entity_id=source_entity_id,
                        frame=frame,
                        provenance=Provenance(FORMAT_ID, f"{obj.name}.{property_name}"),
                        attributes={
                            "freecad_reference": reference,
                            "freecad_subelement": subelement,
                            "reference_property": property_name,
                        },
                    )
                )
        value, parameter_ids = _mate_values(
            obj, kind, mate_id, parameters, consumed_expressions
        )
        stored_value = _stored_mate_value(obj)
        if stored_value is not None:
            value = stored_value
        if not entity_ids:
            continue
        mates.append(
            MateConstraint(
                mate_id,
                _string(obj, "Label", obj.name),
                kind,
                root_definition_id,
                tuple(entity_ids),
                order=order,
                value=value,
                parameter_ids=parameter_ids,
                alignment=_string(obj, "Alignment", "unknown"),
                suppressed=_bool(obj, "SourceSuppressed", _bool(obj, "Suppressed")),
                driving=_bool(obj, "Driving", True),
                provenance=Provenance(FORMAT_ID, obj.name),
                attributes={
                    "freecad": _native_object_data(obj),
                    "joint_type": _enumeration_choice(obj, "JointType"),
                    "references": references,
                },
            )
        )
    groups: tuple[MateGroup, ...] = ()
    if mates and joint_group is not None:
        group_id = f"freecad:mate-group:{joint_group.name}"
        ordered_mate_ids = tuple(
            mate_ids_by_name[name]
            for name in joint_names
            if name in mate_ids_by_name
            and any(mate.id == mate_ids_by_name[name] for mate in mates)
        )
        groups = (
            MateGroup(
                group_id,
                _string(joint_group, "Label", joint_group.name),
                root_definition_id,
                ordered_mate_ids,
                provenance=Provenance(FORMAT_ID, joint_group.name),
                attributes={"freecad": _native_object_data(joint_group)},
            ),
        )
    return AssemblyData(
        root_definition_id,
        tuple(definitions),
        tuple(instances),
        documents=tuple(documents),
        mate_entities=tuple(mate_entities),
        mates=tuple(mates),
        mate_groups=groups,
        attributes={
            "freecad": _native_object_data(root),
            "unresolved_external_documents": unresolved_external,
        },
    )


def _remaining_expressions(
    objects: tuple[_NativeObject, ...],
    parameters: list[Parameter],
    consumed: set[tuple[str, str]],
) -> None:
    existing_ids = {parameter.id for parameter in parameters}
    for obj in objects:
        for path, source in _expressions(obj).items():
            if (obj.name, path) in consumed:
                continue
            base = re.sub(r"[^A-Za-z0-9_.:-]+", "_", path).strip("_") or "expression"
            parameter_id = f"freecad:parameter:{obj.name}:expression:{base}"
            suffix = 2
            while parameter_id in existing_ids:
                parameter_id = (
                    f"freecad:parameter:{obj.name}:expression:{base}:{suffix}"
                )
                suffix += 1
            existing_ids.add(parameter_id)
            parameters.append(
                Parameter(
                    parameter_id,
                    f"{_string(obj, 'Label', obj.name)}.{path}",
                    ParameterValue(0.0, ValueKind.NUMBER),
                    expression=Expression(source, language="freecad"),
                    owner_id=f"freecad:object:{obj.name}",
                    attributes={"freecad_path": path},
                )
            )


def _native_configurations(
    objects: tuple[_NativeObject, ...], feature_ids: dict[str, str]
) -> tuple[Configuration, ...]:
    values = [obj for obj in objects if _string(obj, "KitConfigurationId")]
    if not values:
        return (Configuration("freecad:configuration:default", "Default", active=True),)
    ids = {obj.name: _string(obj, "KitConfigurationId") for obj in values}
    return tuple(
        Configuration(
            ids[obj.name],
            _string(obj, "Label", obj.name),
            active=_bool(obj, "Active"),
            parent_id=ids.get(_link(obj, "ParentConfiguration")),
            suppressed_feature_ids=tuple(
                feature_ids[name]
                for name in _link_list(obj, "SuppressedFeatures")
                if name in feature_ids
            ),
            attributes={"freecad": _native_object_data(obj)},
        )
        for obj in values
    )


def read_native_fcstd(
    data: bytes,
    source_path: str = "",
    *,
    _external_state: _ExternalState | None = None,
    _external_depth: int = 0,
) -> CadDocument:
    native = _load_native_archive(data)
    source_file = _resolved_source_path(source_path)
    external_state = _external_state
    if external_state is None and source_file is not None:
        external_state = _ExternalState(
            source_file.parent,
            {},
            {source_file},
            1,
            len(data),
        )
    resolved_external, unresolved_external = _external_documents(
        native, source_path, external_state, _external_depth
    )
    parameters: list[Parameter] = []
    consumed_expressions: set[tuple[str, str]] = set()
    support_planes, sketches = _parse_sketches(
        native.objects, parameters, consumed_expressions
    )
    sketch_ids = {
        obj.name: f"freecad:sketch:{obj.name}"
        for obj in native.objects
        if obj.type_id == SKETCH_TYPE_ID
    }
    feature_objects = _ordered_features(native.objects)
    feature_ids = {obj.name: f"freecad:feature:{obj.name}" for obj in feature_objects}
    body_ids = {
        obj.name: f"freecad:body:{obj.name}"
        for obj in native.objects
        if _is_body_container(obj)
    }
    brep_payloads, owner_payloads = _build_brep_payloads(native, feature_ids, body_ids)
    native_document_sha256 = hashlib.sha256(data).hexdigest()
    brep_payloads = tuple(
        replace(
            payload,
            attributes={
                **payload.attributes,
                NATIVE_DOCUMENT_SHA256_ATTRIBUTE: native_document_sha256,
            },
        )
        for payload in brep_payloads
    )
    meshes = _parse_meshes(native)
    features: list[FeatureStep] = []
    selections: list[Selection] = list(_explicit_selections(native.objects))
    for order, obj in enumerate(feature_objects):
        feature_id = feature_ids[obj.name]
        kind = _feature_kind(obj)
        feature_selections = _feature_selections(obj)
        selections.extend(feature_selections)
        parameter_ids = _feature_parameters(
            obj, feature_id, parameters, consumed_expressions
        )
        dependencies = tuple(
            feature_ids[value]
            for value in dict.fromkeys(obj.dependencies)
            if value in feature_ids
            and feature_objects.index(
                next(item for item in feature_objects if item.name == value)
            )
            < order
        )
        profile = _link(obj, "Profile") or _link(obj, "Base")
        sketch_id = sketch_ids.get(profile)
        operation: BooleanOperation | str | None = None
        declared_operation = _string(obj, "Operation").casefold()
        if declared_operation:
            try:
                operation = BooleanOperation(declared_operation)
            except ValueError:
                operation = declared_operation
        definition: FeatureDefinition | None = None
        if kind in _SUBTRACTIVE_CAPABLE_KINDS:
            if obj.type_id in _SUBTRACTIVE_TYPE_IDS:
                operation = BooleanOperation.CUT
            elif dependencies:
                operation = BooleanOperation.JOIN
            else:
                operation = BooleanOperation.CREATE
        if kind == FeatureKind.EXTRUSION:
            definition = (
                _part_extrusion_definition(obj)
                if obj.type_id == "Part::Extrusion"
                else _extrusion_definition(obj)
            )
        elif kind == FeatureKind.FILLET:
            radius = _float(obj, "Radius", _float(obj, "DrivingRadius"))
            definition = FilletFeature(
                ParameterValue(abs(radius), ValueKind.LENGTH, "mm")
            )
        elif kind == FeatureKind.CHAMFER:
            ChamferType = _enum(obj, "ChamferType")
            ChamferMode = {
                0: "equal_distance",
                1: "two_distances",
                2: "distance_angle",
            }.get(ChamferType, f"native:{ChamferType}")
            definition = ChamferFeature(
                distance=ParameterValue(
                    abs(_float(obj, "Size")), ValueKind.LENGTH, "mm"
                ),
                mode=ChamferMode,
                second_distance=(
                    ParameterValue(abs(_float(obj, "Size2")), ValueKind.LENGTH, "mm")
                    if ChamferType == 1
                    else None
                ),
                angle=(
                    ParameterValue(abs(_float(obj, "Angle")), ValueKind.ANGLE, "deg")
                    if ChamferType == 2
                    else None
                ),
            )
        elif kind == FeatureKind.SHELL:
            definition = ShellFeature(
                thickness=ParameterValue(
                    abs(_float(obj, "Value")), ValueKind.LENGTH, "mm"
                ),
                outward=not _bool(obj, "Reversed"),
            )
        elif obj.type_id == "PartDesign::LinearPattern":
            OccurrenceCount = _enum(obj, "Occurrences", 1)
            LengthValue = abs(_float(obj, "Length"))
            OffsetValue = abs(_float(obj, "Offset"))
            SpacingValue = (
                LengthValue / (OccurrenceCount - 1)
                if _enum(obj, "Mode") == 0 and OccurrenceCount > 1
                else OffsetValue
            )
            definition = LinearPatternFeature(
                spacing=ParameterValue(SpacingValue, ValueKind.LENGTH, "mm"),
                instance_count=OccurrenceCount,
                direction_selection_id=(
                    feature_selections[0].id if feature_selections else ""
                ),
                reversed=_bool(obj, "Reversed"),
            )
        elif obj.type_id == "PartDesign::PolarPattern":
            definition = CircularPatternFeature(
                angle=ParameterValue(
                    abs(_float(obj, "Angle")),
                    ValueKind.ANGLE,
                    "deg",
                ),
                instance_count=_enum(obj, "Occurrences", 1),
                axis_selection_id=(
                    feature_selections[0].id if feature_selections else ""
                ),
                reversed=_bool(obj, "Reversed"),
            )
        else:
            definition = NativeFeatureDefinition(
                FORMAT_ID, obj.type_id, _native_object_data(obj)
            )
        features.append(
            FeatureStep(
                feature_id,
                _string(obj, "Label", obj.name),
                kind,
                order,
                input_feature_ids=dependencies,
                sketch_id=sketch_id,
                parameter_ids=parameter_ids,
                operation=operation,
                definition=definition,
                selection_ids=tuple(selection.id for selection in feature_selections),
                suppressed=_bool(obj, "Suppressed"),
                provenance=Provenance(FORMAT_ID, obj.name),
                attributes={
                    "freecad": _native_object_data(obj),
                    "brep_payload_ids": owner_payloads.get(obj.name, []),
                },
            )
        )
    bodies: list[Body] = []
    for obj in native.objects:
        if not _is_body_container(obj):
            continue
        final_name = _link(obj, "Tip")
        if final_name not in feature_ids:
            final_name = next(
                (
                    value
                    for value in reversed(_link_list(obj, "Group"))
                    if value in feature_ids
                ),
                "",
            )
        if not final_name:
            continue
        bodies.append(
            Body(
                body_ids[obj.name],
                _string(obj, "Label", obj.name),
                feature_ids[final_name],
                TopologySummary(),
                material_id=_string(obj, "MaterialId") or None,
                provenance=Provenance(FORMAT_ID, obj.name),
                attributes={
                    "freecad": _native_object_data(obj),
                    "tip": final_name,
                    "brep_payload_ids": owner_payloads.get(obj.name, []),
                },
            )
        )
    has_assembly = _assembly_root_object(native.objects) is not None
    if not bodies and features and not has_assembly:
        final = features[-1]
        bodies.append(
            Body(
                "freecad:body:default",
                "Body",
                final.id,
                attributes={"freecad_generated": True},
            )
        )
    decoded_brep = _decoded_document_brep(brep_payloads, tuple(bodies))
    assembly = _parse_assembly(
        native,
        owner_payloads,
        brep_payloads,
        resolved_external,
        unresolved_external,
        parameters,
        consumed_expressions,
    )
    native_document, native_binding = _native_document_payloads(
        native, data, source_path
    )
    brep_payloads = (*brep_payloads, native_document, native_binding)
    _remaining_expressions(native.objects, parameters, consumed_expressions)
    native_feature_types = sorted(
        {
            obj.type_id
            for obj in feature_objects
            if _feature_kind(obj) == FeatureKind.NATIVE
        }
    )
    diagnostics: tuple[Diagnostic, ...] = (
        (
            Diagnostic(
                "freecad.native_features_preserved",
                "FreeCAD feature types were preserved as native operations",
                Severity.INFO,
                attributes={"type_ids": native_feature_types},
            ),
        )
        if native_feature_types
        else ()
    )
    mesh_property_count = sum(
        1
        for obj in native.objects
        for node in obj.properties.values()
        if node.find("./Mesh") is not None
    )
    if mesh_property_count > len(meshes):
        diagnostics += (
            Diagnostic(
                "freecad.unparsed_mesh_data",
                "FreeCAD mesh data was preserved but could not be normalized",
                Severity.WARNING,
                attributes={
                    "property_count": mesh_property_count,
                    "normalized_count": len(meshes),
                },
            ),
        )
    if unresolved_external:
        diagnostics += (
            Diagnostic(
                "freecad.unresolved_external_documents",
                "FreeCAD external component documents could not be resolved",
                Severity.WARNING,
                attributes={"references": unresolved_external},
            ),
        )
    source = CadSource(
        FORMAT_ID,
        source_path,
        hashlib.sha256(data).hexdigest(),
        container_version=native.root.get("FileVersion", ""),
        application_version=native.root.get("ProgramVersion", ""),
        attributes={"freecad_schema_version": native.root.get("SchemaVersion", "")},
    )
    freecad_metadata: dict[str, Any] = {
        "schema_version": native.root.get("SchemaVersion", ""),
        "file_version": native.root.get("FileVersion", ""),
        "program_version": native.root.get("ProgramVersion", ""),
        "entry_order": list(native.entry_order),
        "objects": [_native_object_data(obj) for obj in native.objects],
    }
    document_properties = native.root.find("./Properties")
    if document_properties is not None:
        freecad_metadata["document_properties"] = _element_data(document_properties)
    string_hasher = _string_hasher_data(native)
    if string_hasher is not None:
        freecad_metadata["string_hasher"] = string_hasher
    other_entries = _other_entry_data(native)
    if other_entries:
        freecad_metadata["entries"] = other_entries
    if assembly is None and resolved_external:
        freecad_metadata["external_documents"] = [
            {
                "file": filename,
                "identity": identity,
                "document": linked_document,
            }
            for filename, (identity, linked_document) in resolved_external.items()
        ]
    configurations = _native_configurations(native.objects, feature_ids)
    document = CadDocument(
        source,
        configurations,
        tuple(parameters),
        support_planes,
        sketches,
        tuple(selections),
        tuple(features),
        tuple(bodies),
        meshes=meshes,
        brep=decoded_brep,
        brep_payloads=brep_payloads,
        diagnostics=diagnostics,
        metadata={"freecad": freecad_metadata},
        assembly=assembly,
    )
    capabilities = infer_capabilities(document, roundtrip_metadata=True)
    if resolved_external or unresolved_external:
        capabilities |= {Capability.EXTERNAL_REFERENCES}
    document = replace(document, capabilities=capabilities)
    document.assert_valid()
    return document
