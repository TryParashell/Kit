from __future__ import annotations

from dataclasses import dataclass
import hashlib
import io
import math
from pathlib import PurePosixPath
import re
from typing import Any
import xml.etree.ElementTree as ET
import zipfile

from interchange import (
    ArcGeometry,
    AssemblyData,
    Body,
    BooleanOperation,
    BrepPayload,
    CadDocument,
    CadSource,
    Capability,
    CircleGeometry,
    ComponentDefinition,
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
    FeatureKind,
    FeatureStep,
    FilletFeature,
    GeometryKind,
    LineGeometry,
    MateConstraint,
    MateEntity,
    MateEntityKind,
    MateGroup,
    MateKind,
    Matrix4,
    NativeGeometry,
    Parameter,
    ParameterValue,
    PointGeometry,
    Provenance,
    Severity,
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
)


_MAX_ENTRIES = 16384
_MAX_ENTRY_SIZE = 256 * 1024 * 1024
_MAX_TOTAL_SIZE = 1024 * 1024 * 1024
_MAX_DOCUMENT_SIZE = 32 * 1024 * 1024
_MAX_COMPRESSION_RATIO = 500
_SUPPORTED_SCHEMA_VERSIONS = frozenset({4})
_SHAPE_PROPERTY_TYPES = frozenset(
    {"Part::PropertyPartShape", "Part::PropertyPartShapeHidden"}
)
_SCALAR_PROPERTY_KINDS = {
    "App::PropertyAngle": (ValueKind.ANGLE, "deg"),
    "App::PropertyBool": (ValueKind.BOOLEAN, ""),
    "App::PropertyDistance": (ValueKind.LENGTH, "mm"),
    "App::PropertyFloat": (ValueKind.NUMBER, ""),
    "App::PropertyInteger": (ValueKind.INTEGER, ""),
    "App::PropertyIntegerConstraint": (ValueKind.INTEGER, ""),
    "App::PropertyLength": (ValueKind.LENGTH, "mm"),
    "App::PropertyPrecision": (ValueKind.NUMBER, ""),
    "App::PropertyString": (ValueKind.STRING, ""),
}
_CONSTRAINT_KINDS = {
    1: ConstraintKind.COINCIDENT,
    2: ConstraintKind.HORIZONTAL,
    3: ConstraintKind.VERTICAL,
    4: ConstraintKind.PARALLEL,
    5: ConstraintKind.TANGENT,
    6: ConstraintKind.DISTANCE,
    7: ConstraintKind.DISTANCE_X,
    8: ConstraintKind.DISTANCE_Y,
    9: ConstraintKind.ANGLE,
    10: ConstraintKind.PERPENDICULAR,
    11: ConstraintKind.RADIUS,
    12: ConstraintKind.EQUAL,
    14: ConstraintKind.SYMMETRIC,
    17: ConstraintKind.FIXED,
    18: ConstraintKind.DIAMETER,
}
_DIMENSIONAL_CONSTRAINTS = frozenset({6, 7, 8, 9, 11, 18})
_FEATURE_EXCLUDED_TYPES = frozenset(
    {
        "App::Line",
        "App::Link",
        "App::Origin",
        "App::Plane",
        "App::Point",
        "Assembly::AssemblyObject",
        "Assembly::JointGroup",
        "PartDesign::Body",
        "Sketcher::SketchObject",
    }
)
_MATE_KINDS = {
    "Fixed": MateKind.LOCK,
    "Revolute": MateKind.HINGE,
    "Cylindrical": MateKind.CONCENTRIC,
    "Slider": MateKind.SLOT,
    "Ball": MateKind.NATIVE,
    "Distance": MateKind.DISTANCE,
    "Parallel": MateKind.PARALLEL,
    "Perpendicular": MateKind.PERPENDICULAR,
    "Angle": MateKind.ANGLE,
    "RackPinion": MateKind.RACK_PINION,
    "Screw": MateKind.SCREW,
    "Gears": MateKind.GEAR,
    "Belt": MateKind.BELT,
}


class NativeFreeCADError(ValueError):
    __slots__ = ()


@dataclass(slots=True)
class _NativeObject:
    name: str
    type_id: str
    index: int
    dependencies: tuple[str, ...]
    properties: dict[str, ET.Element]


@dataclass(slots=True)
class _NativeArchive:
    root: ET.Element
    objects: tuple[_NativeObject, ...]
    entries: dict[str, bytes]
    document_xml: bytes


def _entry_name(name: str) -> str:
    if not name or "\\" in name or "\x00" in name:
        raise NativeFreeCADError("FCStd archive contains an unsafe entry name")
    path = PurePosixPath(name)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise NativeFreeCADError("FCStd archive contains an unsafe entry name")
    if path.parts and ":" in path.parts[0]:
        raise NativeFreeCADError("FCStd archive contains an unsafe entry name")
    return path.as_posix()


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
        archive = zipfile.ZipFile(io.BytesIO(data))
    except (OSError, zipfile.BadZipFile) as exc:
        raise NativeFreeCADError("source is not an FCStd ZIP archive") from exc
    infos = archive.infolist()
    if not infos or len(infos) > _MAX_ENTRIES:
        archive.close()
        raise NativeFreeCADError("FCStd archive entry count is outside safe limits")
    members: dict[str, zipfile.ZipInfo] = {}
    total = 0
    try:
        for info in infos:
            name = (
                _entry_name(info.filename.rstrip("/"))
                if info.is_dir()
                else _entry_name(info.filename)
            )
            if name in members:
                raise NativeFreeCADError("FCStd archive contains duplicate entries")
            members[name] = info
            if info.is_dir():
                continue
            mode = (info.external_attr >> 16) & 0o170000
            if mode == 0o120000:
                raise NativeFreeCADError("FCStd archive contains a symbolic link")
            if info.file_size < 0 or info.file_size > _MAX_ENTRY_SIZE:
                raise NativeFreeCADError("FCStd archive entry exceeds safe limits")
            total += info.file_size
            if total > _MAX_TOTAL_SIZE:
                raise NativeFreeCADError("FCStd archive exceeds safe limits")
            if info.file_size and info.compress_size <= 0:
                raise NativeFreeCADError(
                    "FCStd archive has an invalid compressed entry"
                )
            if (
                info.compress_size
                and info.file_size / info.compress_size > _MAX_COMPRESSION_RATIO
            ):
                raise NativeFreeCADError("FCStd archive compression ratio is unsafe")
    except BaseException:
        archive.close()
        raise
    return archive, members


def _parse_objects(root: ET.Element) -> tuple[_NativeObject, ...]:
    objects_node = root.find("./Objects")
    data_node = root.find("./ObjectData")
    if objects_node is None or data_node is None:
        raise NativeFreeCADError("FreeCAD Document.xml has no object graph")
    declarations = objects_node.findall("./Object")
    object_data = data_node.findall("./Object")
    if not declarations or not object_data:
        raise NativeFreeCADError("FreeCAD Document.xml has no objects")
    _declared_count(objects_node, len(declarations), "object")
    _declared_count(data_node, len(object_data), "object data")
    declaration_by_name: dict[str, tuple[str, int]] = {}
    ids: set[str] = set()
    for index, node in enumerate(declarations):
        name = node.get("name", "")
        type_id = node.get("type", "")
        object_id = node.get("id", "")
        if not name or not type_id or name in declaration_by_name:
            raise NativeFreeCADError("FreeCAD object declarations are malformed")
        if object_id and object_id in ids:
            raise NativeFreeCADError(
                "FreeCAD object declarations contain duplicate ids"
            )
        if object_id:
            ids.add(object_id)
        declaration_by_name[name] = (type_id, index)
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
    for name, (type_id, index) in declaration_by_name.items():
        property_nodes: dict[str, ET.Element] = {}
        for node in data_by_name[name].findall("./Properties/Property"):
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
                dependencies.get(name, ()),
                property_nodes,
            )
        )
    return tuple(result)


def _load_native_archive(data: bytes) -> _NativeArchive:
    archive, members = _archive_members(data)
    with archive:
        document_info = members.get("Document.xml")
        if document_info is None or document_info.file_size > _MAX_DOCUMENT_SIZE:
            raise NativeFreeCADError("FCStd archive has no safe Document.xml")
        try:
            document_xml = archive.read(document_info)
            root = ET.fromstring(document_xml)
        except (OSError, ET.ParseError, RuntimeError) as exc:
            raise NativeFreeCADError(
                "FCStd archive has no readable Document.xml"
            ) from exc
        if root.tag != "Document":
            raise NativeFreeCADError("FreeCAD Document.xml has an invalid root")
        try:
            schema_version = int(root.get("SchemaVersion", ""))
        except ValueError as exc:
            raise NativeFreeCADError("FreeCAD schema version is invalid") from exc
        if schema_version not in _SUPPORTED_SCHEMA_VERSIONS:
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
        entries = {name: archive.read(members[name]) for name in referenced}
    return _NativeArchive(root, objects, entries, document_xml)


def probe_native_fcstd(data: bytes) -> tuple[float, str]:
    try:
        native = _load_native_archive(data)
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
        "dependencies": list(obj.dependencies),
        "properties": {
            name: _element_data(node) for name, node in obj.properties.items()
        },
    }


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
    return node.get("value", "false").casefold() in {"1", "true", "yes"}


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
    return tuple(
        value
        for child in node.findall("./LinkList/Link")
        if (value := child.get("value", ""))
    )


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
    kind_and_unit = _SCALAR_PROPERTY_KINDS.get(type_id)
    if kind_and_unit is None:
        return None
    kind, unit = kind_and_unit
    if kind == ValueKind.BOOLEAN:
        child = node.find("./Bool")
        if child is None:
            return None
        value = child.get("value", "false").casefold() in {"1", "true", "yes"}
    elif kind == ValueKind.INTEGER:
        child = node.find("./Integer")
        if child is None:
            return None
        value = _integer(child.get("value"))
    elif kind == ValueKind.STRING:
        child = node.find("./String")
        if child is None:
            return None
        value = child.get("value", "")
    else:
        child = node.find("./Float")
        if child is None:
            return None
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
            axis = Vector2(
                _number(value.get("MajorAxisX"), 1.0),
                _number(value.get("MajorAxisY")),
            )
            return GeometryKind.ELLIPSE, EllipseGeometry(
                center,
                axis,
                abs(_number(value.get("MajorRadius"))),
                abs(_number(value.get("MinorRadius"))),
            )
    if type_id in {"Part::GeomBSplineCurve", "Part::GeomBezierCurve"}:
        value = node.find("./BSplineCurve")
        if value is None:
            value = node.find("./BezierCurve")
        if value is not None:
            points = tuple(
                Vector2(_number(item.get("X")), _number(item.get("Y")))
                for item in value.findall(".//*[@X][@Y]")
            )
            if points:
                return GeometryKind.SPLINE, SplineGeometry(
                    points,
                    max(1, _integer(value.get("Degree"), 3)),
                    periodic=value.get("Periodic", "false").casefold() in {"1", "true"},
                )
    return GeometryKind.NATIVE, NativeGeometry(
        "freecad.fcstd", type_id or "unknown", _element_data(node)
    )


def _support_target(obj: _NativeObject) -> str:
    node = obj.properties.get("AttachmentSupport")
    if node is None:
        return ""
    link = node.find("./LinkSubList/Link")
    return "" if link is None else link.get("obj", "")


def _constraint_expression(expressions: dict[str, str], index: int, name: str) -> str:
    candidates = [f"Constraints[{index}]", f"Constraints.{name}"]
    return next(
        (expressions[value] for value in candidates if value in expressions), ""
    )


def _parse_sketches(
    objects: tuple[_NativeObject, ...],
    parameters: list[Parameter],
    consumed_expressions: set[tuple[str, str]],
) -> tuple[tuple[SupportPlane, ...], tuple[Sketch, ...]]:
    planes: list[SupportPlane] = []
    plane_ids: dict[str, str] = {}
    for obj in objects:
        if obj.type_id != "App::Plane":
            continue
        plane_id = f"freecad:plane:{obj.name}"
        plane_ids[obj.name] = plane_id
        planes.append(
            SupportPlane(
                plane_id,
                _string(obj, "Label", obj.name),
                _transform(_placement_element(obj, "Placement")),
                attributes={"freecad": _native_object_data(obj)},
            )
        )
    sketches: list[Sketch] = []
    for obj in objects:
        if obj.type_id != "Sketcher::SketchObject":
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
        fixed_indices = {
            _integer(node.get("First"), -1)
            for node in constraint_nodes
            if _integer(node.get("Type"), -1) == 17
        }
        entities: list[SketchEntity] = []
        for index, node in enumerate(geometry_nodes):
            entity_id = f"{sketch_id}:entity:{index}"
            kind, geometry = _geometry(node, entity_id)
            construction_node = node.find("./Construction")
            construction = construction_node is not None and construction_node.get(
                "value", "0"
            ).casefold() in {"1", "true"}
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
            for prefix in ("First", "Second", "Third"):
                entity_index = _integer(node.get(prefix), -2000)
                if 0 <= entity_index < len(entities):
                    point = {1: "start", 2: "end", 3: "center"}.get(
                        _integer(node.get(prefix + "Pos")), ""
                    )
                    references.append(
                        ConstraintReference(entities[entity_index].id, point)
                    )
            parameter_id: str | None = None
            if code in _DIMENSIONAL_CONSTRAINTS:
                parameter_id = f"freecad:parameter:{obj.name}:constraint:{index}"
                value_kind = ValueKind.ANGLE if code == 9 else ValueKind.LENGTH
                unit = "rad" if code == 9 else "mm"
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
                    _CONSTRAINT_KINDS.get(code, ConstraintKind.NATIVE),
                    tuple(references),
                    parameter_id=parameter_id,
                    driving=node.get("IsDriving", "1") != "0",
                    suppressed=node.get("IsActive", "1") == "0",
                    attributes={
                        "freecad_type_code": code,
                        "freecad": dict(node.attrib),
                    },
                )
            )
        sketches.append(
            Sketch(
                sketch_id,
                _string(obj, "Label", obj.name),
                support_id,
                tuple(entities),
                constraints=tuple(constraints),
                parameter_ids=tuple(sketch_parameter_ids),
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


def _shape_reference(obj: _NativeObject, property_name: str) -> str:
    node = obj.properties.get(property_name)
    if node is None or node.get("type", "") not in _SHAPE_PROPERTY_TYPES:
        return ""
    part = node.find("./Part")
    return "" if part is None else part.get("file", "")


def _is_feature_object(obj: _NativeObject) -> bool:
    if obj.type_id in _FEATURE_EXCLUDED_TYPES:
        return False
    if obj.type_id.startswith("Assembly::"):
        return False
    if obj.type_id == "App::FeaturePython" and "Proxy" in obj.properties:
        return False
    if obj.type_id in {
        "PartDesign::Pad",
        "PartDesign::Pocket",
        "PartDesign::Fillet",
        "Part::Extrusion",
        "Part::Fillet",
    }:
        return True
    return bool(_shape_reference(obj, "Shape"))


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


def _feature_kind(obj: _NativeObject) -> FeatureKind:
    if obj.type_id in {"PartDesign::Pad", "PartDesign::Pocket", "Part::Extrusion"}:
        return FeatureKind.EXTRUSION
    if obj.type_id in {"PartDesign::Fillet", "Part::Fillet"}:
        return FeatureKind.FILLET
    if obj.type_id == "Part::Feature":
        return FeatureKind.IMPORTED
    return FeatureKind.NATIVE


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


def _extrusion_definition(obj: _NativeObject) -> ExtrusionFeature:
    type_code = _enum(obj, "Type")
    end_condition: ExtrusionEndCondition | str = {
        0: ExtrusionEndCondition.BLIND,
        1: ExtrusionEndCondition.THROUGH_ALL,
        2: ExtrusionEndCondition.UP_TO_FACE,
        3: ExtrusionEndCondition.UP_TO_FACE,
        4: ExtrusionEndCondition.UP_TO_FACE,
        5: ExtrusionEndCondition.UP_TO_FACE,
    }.get(type_code, ExtrusionEndCondition.NATIVE)
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
        symmetric=_bool(obj, "Midplane"),
        direction=direction,
        second_length=(
            ParameterValue(_float(obj, "Length2"), ValueKind.LENGTH, "mm")
            if "Length2" in obj.properties
            else None
        ),
        draft_angle=(
            ParameterValue(_float(obj, "TaperAngle"), ValueKind.ANGLE, "deg")
            if "TaperAngle" in obj.properties
            else None
        ),
    )


def _build_brep_payloads(
    native: _NativeArchive, feature_ids: dict[str, str], body_ids: dict[str, str]
) -> tuple[tuple[BrepPayload, ...], dict[str, list[str]]]:
    payloads: list[BrepPayload] = []
    owner_payloads: dict[str, list[str]] = {}
    for obj in native.objects:
        for property_name, node in obj.properties.items():
            if node.get("type", "") not in _SHAPE_PROPERTY_TYPES:
                continue
            part = node.find("./Part")
            filename = "" if part is None else part.get("file", "")
            if not filename:
                continue
            data = native.entries.get(filename)
            if not data:
                continue
            payload_id = f"freecad:brep:{obj.name}:{property_name}"
            header = data[:256].decode("ascii", "ignore")
            match = re.search(r"CASCADE Topology V\d+", header)
            attributes: dict[str, Any] = {
                "freecad_object": obj.name,
                "freecad_object_type": obj.type_id,
                "freecad_property": property_name,
                "freecad_part_attributes": (
                    dict(part.attrib) if part is not None else {}
                ),
            }
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
                    provenance=Provenance(
                        "freecad.fcstd", f"{obj.name}.{property_name}"
                    ),
                    attributes=attributes,
                )
            )
            owner_payloads.setdefault(obj.name, []).append(payload_id)
    return tuple(payloads), owner_payloads


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
    return {
        "file": value.get("file", ""),
        "stamp": value.get("stamp", ""),
        "name": value.get("name", ""),
        "subelements": [
            subelement
            for child in value.findall("./Sub")
            if (subelement := child.get("value", ""))
        ],
    }


def _mate_entity_kind(value: str) -> MateEntityKind:
    token = value.rsplit(".", 1)[-1]
    if token.startswith("Face"):
        return MateEntityKind.FACE
    if token.startswith("Edge"):
        return MateEntityKind.EDGE
    if token.startswith("Vertex"):
        return MateEntityKind.VERTEX
    if token.startswith("Axis"):
        return MateEntityKind.AXIS
    if token.startswith("Plane"):
        return MateEntityKind.PLANE
    return MateEntityKind.NATIVE


def _mate_value(
    obj: _NativeObject,
    kind: MateKind,
    mate_id: str,
    parameters: list[Parameter],
    consumed_expressions: set[tuple[str, str]],
) -> tuple[ParameterValue | None, tuple[str, ...]]:
    if kind == MateKind.ANGLE:
        property_name = "Angle"
        value = ParameterValue(_float(obj, property_name), ValueKind.ANGLE, "deg")
    elif kind in {
        MateKind.DISTANCE,
        MateKind.RACK_PINION,
        MateKind.SCREW,
        MateKind.GEAR,
        MateKind.BELT,
    }:
        property_name = "Distance"
        value = ParameterValue(_float(obj, property_name), ValueKind.LENGTH, "mm")
    else:
        return None, ()
    parameter_id = f"freecad:parameter:{obj.name}:{property_name}"
    expression_source = _expressions(obj).get(property_name, "")
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
    return value, (parameter_id,)


def _parse_assembly(
    native: _NativeArchive,
    owner_payloads: dict[str, list[str]],
    parameters: list[Parameter],
    consumed_expressions: set[tuple[str, str]],
) -> AssemblyData | None:
    root = next(
        (obj for obj in native.objects if obj.type_id == "Assembly::AssemblyObject"),
        None,
    )
    if root is None:
        return None
    objects = {obj.name: obj for obj in native.objects}
    root_definition_id = f"freecad:definition:{root.name}"
    root_group = _link_list(root, "Group")
    links = [
        objects[name]
        for name in root_group
        if name in objects and objects[name].type_id == "App::Link"
    ]
    if not links:
        links = [obj for obj in native.objects if obj.type_id == "App::Link"]
    joint_group = next(
        (obj for obj in native.objects if obj.type_id == "Assembly::JointGroup"),
        None,
    )
    joint_names = _link_list(joint_group, "Group") if joint_group is not None else ()
    if not joint_names:
        joint_names = tuple(
            obj.name
            for obj in native.objects
            if obj.type_id == "App::FeaturePython"
            and _proxy_class(obj) in {"Joint", "GroundedJoint"}
        )
    joint_objects = [objects[name] for name in joint_names if name in objects]
    grounded_targets = {
        target
        for obj in joint_objects
        if _proxy_class(obj) == "GroundedJoint"
        and (target := _link(obj, "ObjectToGround"))
    }
    definitions: list[ComponentDefinition] = [
        ComponentDefinition(
            root_definition_id,
            _string(root, "Label", root.name),
            ComponentKind.ASSEMBLY,
            provenance=Provenance("freecad.fcstd", root.name),
            attributes={"freecad": _native_object_data(root)},
        )
    ]
    definition_ids: dict[str, str] = {}
    instances: list[ComponentInstance] = []
    instance_ids: dict[str, str] = {}
    for order, link_obj in enumerate(links):
        linked = _xlink_data(link_obj, "LinkedObject")
        target = str(linked["name"]) or link_obj.name
        definition_id = definition_ids.get(target)
        if definition_id is None:
            definition_id = f"freecad:definition:{target}"
            definition_ids[target] = definition_id
            target_obj = objects.get(target)
            definitions.append(
                ComponentDefinition(
                    definition_id,
                    (
                        _string(target_obj, "Label", target)
                        if target_obj is not None
                        else target
                    ),
                    ComponentKind.PART,
                    source_path=str(linked["file"]),
                    source_format_id="freecad.fcstd",
                    provenance=Provenance("freecad.fcstd", target),
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
                provenance=Provenance("freecad.fcstd", link_obj.name),
                attributes={
                    "freecad": _native_object_data(link_obj),
                    "linked_object": linked,
                    "link_placement": list(
                        _placement_matrix(_placement_element(link_obj, "LinkPlacement"))
                    ),
                },
            )
        )
    mate_entities: list[MateEntity] = []
    mates: list[MateConstraint] = []
    mate_ids_by_name: dict[str, str] = {}
    for order, obj in enumerate(joint_objects):
        proxy_class = _proxy_class(obj)
        mate_id = f"freecad:mate:{obj.name}"
        mate_ids_by_name[obj.name] = mate_id
        entity_ids: list[str] = []
        references: list[dict[str, Any]] = []
        if proxy_class == "GroundedJoint":
            target = _link(obj, "ObjectToGround")
            entity_id = f"freecad:mate-entity:{obj.name}:ground"
            entity_ids.append(entity_id)
            mate_entities.append(
                MateEntity(
                    entity_id,
                    root_definition_id,
                    (instance_ids[target],) if target in instance_ids else (),
                    MateEntityKind.COORDINATE_SYSTEM,
                    source_entity_id=target,
                    frame=Matrix4(
                        _placement_matrix(_placement_element(obj, "Placement"))
                    ),
                    provenance=Provenance("freecad.fcstd", obj.name),
                    attributes={"object_to_ground": target},
                )
            )
            kind = MateKind.LOCK
            value = None
            parameter_ids: tuple[str, ...] = ()
        else:
            joint_type = _enumeration_choice(obj, "JointType")
            kind = _MATE_KINDS.get(joint_type, MateKind.NATIVE)
            for reference_index, property_name in enumerate(
                ("Reference1", "Reference2"), start=1
            ):
                reference = _xlink_data(obj, property_name)
                references.append(reference)
                for sub_index, subelement in enumerate(reference["subelements"]):
                    component_name, separator, source_entity_id = str(
                        subelement
                    ).partition(".")
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
                            frame=Matrix4(
                                _placement_matrix(
                                    _placement_element(
                                        obj, f"Placement{reference_index}"
                                    )
                                )
                            ),
                            provenance=Provenance(
                                "freecad.fcstd", f"{obj.name}.{property_name}"
                            ),
                            attributes={
                                "freecad_reference": reference,
                                "freecad_subelement": subelement,
                                "reference_property": property_name,
                            },
                        )
                    )
            value, parameter_ids = _mate_value(
                obj, kind, mate_id, parameters, consumed_expressions
            )
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
                suppressed=_bool(obj, "Suppressed"),
                provenance=Provenance("freecad.fcstd", obj.name),
                attributes={
                    "freecad": _native_object_data(obj),
                    "joint_type": _enumeration_choice(obj, "JointType"),
                    "references": references,
                },
            )
        )
    groups: tuple[MateGroup, ...] = ()
    if mates:
        group_id = (
            f"freecad:mate-group:{joint_group.name}"
            if joint_group is not None
            else "freecad:mate-group:joints"
        )
        ordered_mate_ids = tuple(
            mate_ids_by_name[name]
            for name in joint_names
            if name in mate_ids_by_name
            and any(mate.id == mate_ids_by_name[name] for mate in mates)
        )
        groups = (
            MateGroup(
                group_id,
                (
                    _string(joint_group, "Label", joint_group.name)
                    if joint_group is not None
                    else "Joints"
                ),
                root_definition_id,
                ordered_mate_ids,
                provenance=Provenance(
                    "freecad.fcstd",
                    joint_group.name if joint_group is not None else "Joints",
                ),
                attributes={
                    "freecad": (
                        _native_object_data(joint_group)
                        if joint_group is not None
                        else {}
                    )
                },
            ),
        )
    return AssemblyData(
        root_definition_id,
        tuple(definitions),
        tuple(instances),
        mate_entities=tuple(mate_entities),
        mates=tuple(mates),
        mate_groups=groups,
        attributes={"freecad": _native_object_data(root)},
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


def read_native_fcstd(data: bytes, source_path: str = "") -> CadDocument:
    native = _load_native_archive(data)
    parameters: list[Parameter] = []
    consumed_expressions: set[tuple[str, str]] = set()
    support_planes, sketches = _parse_sketches(
        native.objects, parameters, consumed_expressions
    )
    sketch_ids = {
        obj.name: f"freecad:sketch:{obj.name}"
        for obj in native.objects
        if obj.type_id == "Sketcher::SketchObject"
    }
    feature_objects = _ordered_features(native.objects)
    feature_ids = {obj.name: f"freecad:feature:{obj.name}" for obj in feature_objects}
    body_ids = {
        obj.name: f"freecad:body:{obj.name}"
        for obj in native.objects
        if obj.type_id == "PartDesign::Body"
    }
    brep_payloads, owner_payloads = _build_brep_payloads(native, feature_ids, body_ids)
    features: list[FeatureStep] = []
    for order, obj in enumerate(feature_objects):
        feature_id = feature_ids[obj.name]
        kind = _feature_kind(obj)
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
        definition: ExtrusionFeature | FilletFeature | None = None
        if kind == FeatureKind.EXTRUSION:
            if obj.type_id == "PartDesign::Pocket":
                operation = BooleanOperation.CUT
            elif dependencies:
                operation = BooleanOperation.JOIN
            else:
                operation = BooleanOperation.CREATE
            definition = _extrusion_definition(obj)
        elif kind == FeatureKind.FILLET:
            radius = _float(obj, "Radius", _float(obj, "DrivingRadius"))
            definition = FilletFeature(
                ParameterValue(abs(radius), ValueKind.LENGTH, "mm")
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
                suppressed=_bool(obj, "Suppressed"),
                provenance=Provenance("freecad.fcstd", obj.name),
                attributes={
                    "freecad": _native_object_data(obj),
                    "brep_payload_ids": owner_payloads.get(obj.name, []),
                },
            )
        )
    bodies: list[Body] = []
    for obj in native.objects:
        if obj.type_id != "PartDesign::Body":
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
                provenance=Provenance("freecad.fcstd", obj.name),
                attributes={
                    "freecad": _native_object_data(obj),
                    "tip": final_name,
                    "brep_payload_ids": owner_payloads.get(obj.name, []),
                },
            )
        )
    has_assembly = any(
        obj.type_id == "Assembly::AssemblyObject" for obj in native.objects
    )
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
    assembly = _parse_assembly(native, owner_payloads, parameters, consumed_expressions)
    _remaining_expressions(native.objects, parameters, consumed_expressions)
    capabilities = {Capability.ROUNDTRIP_METADATA}
    if features:
        capabilities.add(Capability.PARAMETRIC_HISTORY)
    if sketches:
        capabilities.add(Capability.EDITABLE_SKETCHES)
    if any(parameter.expression is not None for parameter in parameters):
        capabilities.add(Capability.EXPRESSIONS)
    if brep_payloads:
        capabilities.update({Capability.BREP, Capability.NATIVE_PAYLOADS})
    if assembly is not None:
        capabilities.add(Capability.ASSEMBLIES)
    native_feature_types = sorted(
        {
            obj.type_id
            for obj in feature_objects
            if _feature_kind(obj) == FeatureKind.NATIVE
        }
    )
    diagnostics = (
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
    source = CadSource(
        "freecad.fcstd",
        source_path,
        hashlib.sha256(data).hexdigest(),
        container_version=native.root.get("FileVersion", ""),
        application_version=native.root.get("ProgramVersion", ""),
        attributes={"freecad_schema_version": native.root.get("SchemaVersion", "")},
    )
    document = CadDocument(
        source,
        (Configuration("freecad:configuration:default", "Default", active=True),),
        tuple(parameters),
        support_planes,
        sketches,
        (),
        tuple(features),
        tuple(bodies),
        brep_payloads=brep_payloads,
        diagnostics=diagnostics,
        capabilities=frozenset(capabilities),
        metadata={
            "freecad": {
                "schema_version": native.root.get("SchemaVersion", ""),
                "file_version": native.root.get("FileVersion", ""),
                "program_version": native.root.get("ProgramVersion", ""),
                "objects": [_native_object_data(obj) for obj in native.objects],
            }
        },
        assembly=assembly,
    )
    document.assert_valid()
    return document
