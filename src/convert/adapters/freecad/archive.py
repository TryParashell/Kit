from __future__ import annotations

import base64
import copy
from dataclasses import dataclass, field
import hashlib
import io
import json
import math
from pathlib import PurePosixPath
import re
import struct
import uuid
import xml.etree.ElementTree as ET
import zipfile
import zlib
from typing import Any, Mapping

from .brep import triangle_mesh_brep


MANIFEST_ENTRY = "interchange/document.json"
MANIFEST_DATA_PROPERTY = "KitManifestData"
MANIFEST_ENCODING_PROPERTY = "KitManifestEncoding"
MANIFEST_SHA256_PROPERTY = "KitManifestSHA256"
MANIFEST_ENCODING = "zlib+base64+utf-8"


def _enum(value: Any) -> Any:
    if isinstance(value, Mapping) and "$enum" in value:
        return value.get("value")
    return value


def _items(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, Mapping):
        for marker in ("$tuple", "$frozenset", "$set"):
            if marker in value:
                return _items(value[marker])
        if "$type" in value:
            return [dict(value)]
        return [dict(item) for item in value.values() if isinstance(item, Mapping)]
    if isinstance(value, (list, tuple)):
        return [dict(item) for item in value if isinstance(item, Mapping)]
    return []


def _sequence(value: Any) -> list[Any]:
    if isinstance(value, Mapping):
        for marker in ("$tuple", "$frozenset", "$set"):
            if marker in value:
                return _sequence(value[marker])
        return []
    if isinstance(value, (list, tuple)):
        return list(value)
    return []


def _number(value: Any, default: float = 0.0) -> float:
    value = _enum(value)
    if isinstance(value, Mapping):
        for key in ("value", "value_mm", "length_mm", "radius", "radius_mm"):
            if key in value:
                return _number(value[key], default)
        return default
    if isinstance(value, bool):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _text(value: Any, default: str = "") -> str:
    value = _enum(value)
    if value is None:
        return default
    return str(value)


def _fmt(value: Any) -> str:
    return f"{_number(value):.16f}"


def _safe(value: Any, prefix: str = "Object") -> str:
    name = re.sub(r"[^A-Za-z0-9_]", "_", _text(value)).strip("_")
    if not name:
        name = prefix
    if name[0].isdigit():
        name = f"{prefix}_{name}"
    return name


def _vector(
    value: Any, default: tuple[float, float, float]
) -> tuple[float, float, float]:
    if isinstance(value, Mapping):
        if "origin" in value and not any(key in value for key in ("x", "y", "z")):
            return _vector(value["origin"], default)
        return (
            _number(value.get("x"), default[0]),
            _number(value.get("y"), default[1]),
            _number(value.get("z"), default[2]),
        )
    if isinstance(value, (list, tuple)) and len(value) >= 3:
        return (_number(value[0]), _number(value[1]), _number(value[2]))
    return default


def _point2(value: Any) -> tuple[float, float]:
    if isinstance(value, Mapping):
        return (_number(value.get("x")), _number(value.get("y")))
    if isinstance(value, (list, tuple)) and len(value) >= 2:
        return (_number(value[0]), _number(value[1]))
    return (0.0, 0.0)


def _normalize(value: tuple[float, float, float]) -> tuple[float, float, float]:
    length = math.sqrt(sum(component * component for component in value))
    if length <= 1e-15:
        return (0.0, 0.0, 1.0)
    return tuple(component / length for component in value)


def _quaternion(transform: Mapping[str, Any]) -> tuple[float, float, float, float]:
    x_axis = _normalize(_vector(transform.get("x_axis"), (1.0, 0.0, 0.0)))
    y_axis = _normalize(_vector(transform.get("y_axis"), (0.0, 1.0, 0.0)))
    z_axis = _normalize(_vector(transform.get("z_axis"), (0.0, 0.0, 1.0)))
    matrix = (
        (x_axis[0], y_axis[0], z_axis[0]),
        (x_axis[1], y_axis[1], z_axis[1]),
        (x_axis[2], y_axis[2], z_axis[2]),
    )
    trace = matrix[0][0] + matrix[1][1] + matrix[2][2]
    if trace > 0.0:
        scale = math.sqrt(trace + 1.0) * 2.0
        w = 0.25 * scale
        x = (matrix[2][1] - matrix[1][2]) / scale
        y = (matrix[0][2] - matrix[2][0]) / scale
        z = (matrix[1][0] - matrix[0][1]) / scale
    elif matrix[0][0] > matrix[1][1] and matrix[0][0] > matrix[2][2]:
        scale = math.sqrt(1.0 + matrix[0][0] - matrix[1][1] - matrix[2][2]) * 2.0
        w = (matrix[2][1] - matrix[1][2]) / scale
        x = 0.25 * scale
        y = (matrix[0][1] + matrix[1][0]) / scale
        z = (matrix[0][2] + matrix[2][0]) / scale
    elif matrix[1][1] > matrix[2][2]:
        scale = math.sqrt(1.0 + matrix[1][1] - matrix[0][0] - matrix[2][2]) * 2.0
        w = (matrix[0][2] - matrix[2][0]) / scale
        x = (matrix[0][1] + matrix[1][0]) / scale
        y = 0.25 * scale
        z = (matrix[1][2] + matrix[2][1]) / scale
    else:
        scale = math.sqrt(1.0 + matrix[2][2] - matrix[0][0] - matrix[1][1]) * 2.0
        w = (matrix[1][0] - matrix[0][1]) / scale
        x = (matrix[0][2] + matrix[2][0]) / scale
        y = (matrix[1][2] + matrix[2][1]) / scale
        z = 0.25 * scale
    norm = math.sqrt(x * x + y * y + z * z + w * w)
    return (x / norm, y / norm, z / norm, w / norm)


def _property(
    name: str, property_type: str, *, dynamic: bool = False, status: str | None = None
) -> ET.Element:
    attributes = {"name": name, "type": property_type}
    if dynamic:
        attributes.update(
            {
                "group": "Kit",
                "doc": "",
                "attr": "0",
                "ro": "0",
                "hide": "0",
                "status": "2097152",
            }
        )
    elif status is not None:
        attributes["status"] = status
    return ET.Element("Property", attributes)


def _string_property(name: str, value: Any, *, dynamic: bool = False) -> ET.Element:
    result = _property(name, "App::PropertyString", dynamic=dynamic)
    ET.SubElement(result, "String", {"value": _text(value)})
    return result


def _string_list_property(
    name: str, values: list[str], *, dynamic: bool = False
) -> ET.Element:
    result = _property(name, "App::PropertyStringList", dynamic=dynamic)
    child = ET.SubElement(result, "StringList", {"count": str(len(values))})
    for value in values:
        ET.SubElement(child, "String", {"value": value})
    return result


def _bool_property(name: str, value: Any, *, dynamic: bool = False) -> ET.Element:
    result = _property(name, "App::PropertyBool", dynamic=dynamic)
    ET.SubElement(result, "Bool", {"value": "true" if bool(value) else "false"})
    return result


def _float_property(
    name: str,
    value: Any,
    property_type: str = "App::PropertyFloat",
    *,
    dynamic: bool = False,
) -> ET.Element:
    result = _property(name, property_type, dynamic=dynamic)
    ET.SubElement(result, "Float", {"value": _fmt(value)})
    return result


def _integer_property(name: str, value: Any, *, dynamic: bool = False) -> ET.Element:
    result = _property(name, "App::PropertyInteger", dynamic=dynamic)
    ET.SubElement(result, "Integer", {"value": str(int(_number(value)))})
    return result


def _enumeration_property(name: str, value: Any) -> ET.Element:
    result = _property(name, "App::PropertyEnumeration")
    ET.SubElement(result, "Integer", {"value": str(int(_number(value)))})
    return result


def _vector_property(
    name: str, value: tuple[float, float, float], *, dynamic: bool = False
) -> ET.Element:
    result = _property(name, "App::PropertyVector", dynamic=dynamic)
    ET.SubElement(
        result,
        "PropertyVector",
        {"valueX": _fmt(value[0]), "valueY": _fmt(value[1]), "valueZ": _fmt(value[2])},
    )
    return result


def _placement_property(
    name: str,
    transform: Mapping[str, Any],
    *,
    dynamic: bool = False,
    status: str | None = None,
) -> ET.Element:
    result = _property(name, "App::PropertyPlacement", dynamic=dynamic, status=status)
    origin = _vector(transform.get("origin"), (0.0, 0.0, 0.0))
    x, y, z, w = _quaternion(transform)
    angle = 2.0 * math.acos(max(-1.0, min(1.0, w)))
    sine = math.sqrt(max(0.0, 1.0 - w * w))
    axis = (0.0, 0.0, 1.0) if sine <= 1e-12 else (x / sine, y / sine, z / sine)
    ET.SubElement(
        result,
        "PropertyPlacement",
        {
            "Px": _fmt(origin[0]),
            "Py": _fmt(origin[1]),
            "Pz": _fmt(origin[2]),
            "Q0": _fmt(x),
            "Q1": _fmt(y),
            "Q2": _fmt(z),
            "Q3": _fmt(w),
            "A": _fmt(angle),
            "Ox": _fmt(axis[0]),
            "Oy": _fmt(axis[1]),
            "Oz": _fmt(axis[2]),
        },
    )
    return result


def _link_property(name: str, target: str, *, dynamic: bool = False) -> ET.Element:
    result = _property(name, "App::PropertyLink", dynamic=dynamic)
    ET.SubElement(result, "Link", {"value": target})
    return result


def _link_list_property(
    name: str, targets: list[str], *, dynamic: bool = False
) -> ET.Element:
    result = _property(name, "App::PropertyLinkList", dynamic=dynamic)
    child = ET.SubElement(result, "LinkList", {"count": str(len(targets))})
    for target in targets:
        ET.SubElement(child, "Link", {"value": target})
    return result


def _xlink_property(
    name: str,
    target: str,
    *,
    file: str = "",
    stamp: str = "",
    status: str | None = "256",
) -> ET.Element:
    result = _property(name, "App::PropertyXLink", status=status)
    ET.SubElement(result, "XLink", {"file": file, "stamp": stamp, "name": target})
    return result


def _python_proxy_property(module: str, class_name: str) -> ET.Element:
    result = _property("Proxy", "App::PropertyPythonObject")
    ET.SubElement(
        result,
        "Python",
        {
            "value": "bnVsbA==",
            "encoded": "yes",
            "module": module,
            "class": class_name,
        },
    )
    return result


def _xlink_sub_property(
    name: str, target: str, subelements: list[str], *, dynamic: bool = False
) -> ET.Element:
    result = _property(name, "App::PropertyXLinkSub", dynamic=dynamic)
    child = ET.SubElement(
        result,
        "XLink",
        {
            "file": "",
            "stamp": "",
            "name": target,
            "count": str(len(subelements)),
        },
    )
    for subelement in subelements:
        ET.SubElement(child, "Sub", {"value": subelement})
    return result


def _enumeration_choices_property(
    name: str, choices: list[str], selected: int, *, dynamic: bool = False
) -> ET.Element:
    result = _property(name, "App::PropertyEnumeration", dynamic=dynamic)
    ET.SubElement(
        result,
        "Integer",
        {"value": str(selected), "CustomEnum": "true"},
    )
    values = ET.SubElement(result, "CustomEnumList", {"count": str(len(choices))})
    for choice in choices:
        ET.SubElement(values, "Enum", {"value": choice})
    return result


def _expression_property(expressions: list[tuple[str, str]]) -> ET.Element:
    result = _property(
        "ExpressionEngine", "App::PropertyExpressionEngine", status="67108864"
    )
    child = ET.SubElement(result, "ExpressionEngine", {"count": str(len(expressions))})
    for path, expression in expressions:
        ET.SubElement(child, "Expression", {"path": path, "expression": expression})
    return result


def _json_property(name: str, value: Any) -> ET.Element:
    return _string_property(
        name,
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
        dynamic=True,
    )


@dataclass
class _Object:
    type_id: str
    name: str
    properties: list[ET.Element] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    touched: bool = False
    extensions: tuple[str, ...] = ()


class _Graph:
    def __init__(self) -> None:
        self.objects: list[_Object] = []
        self.names: set[str] = set()

    def unique(self, requested: Any, prefix: str = "Object") -> str:
        base = _safe(requested, prefix)
        value = base
        suffix = 2
        while value in self.names:
            value = f"{base}_{suffix}"
            suffix += 1
        self.names.add(value)
        return value

    def add(
        self,
        type_id: str,
        requested: Any,
        prefix: str = "Object",
        *,
        touched: bool = False,
        extensions: tuple[str, ...] = (),
    ) -> _Object:
        result = _Object(
            type_id,
            self.unique(requested, prefix),
            touched=touched,
            extensions=extensions,
        )
        self.objects.append(result)
        return result


class _Parameters:
    def __init__(self, parameters: list[dict[str, Any]]) -> None:
        self.parameters = parameters
        self.by_id = {_text(item.get("id")): item for item in parameters}
        self.aliases: dict[str, str] = {}
        used: set[str] = set()
        for index, item in enumerate(parameters, start=1):
            parameter_id = _text(item.get("id"), f"parameter_{index}")
            base = _safe(parameter_id, "p")
            if base[0].isdigit():
                base = f"p_{base}"
            alias = base
            suffix = 2
            while alias in used:
                alias = f"{base}_{suffix}"
                suffix += 1
            used.add(alias)
            self.aliases[parameter_id] = alias

    def expression(self, parameter_id: str, divisor: float | None = None) -> str | None:
        alias = self.aliases.get(parameter_id)
        if not alias:
            return None
        result = f"Parameters.{alias}"
        if divisor and divisor != 1.0:
            result += f" / {_number(divisor):.16g}"
        return result

    def value(self, parameter_id: str, default: float = 0.0) -> float:
        parameter = self.by_id.get(parameter_id)
        if not parameter:
            return default
        value = parameter.get("value", {})
        if isinstance(value, Mapping):
            return _number(value.get("value"), default)
        return _number(value, default)

    def kind(self, parameter_id: str) -> str:
        parameter = self.by_id.get(parameter_id, {})
        value = parameter.get("value", {}) if isinstance(parameter, Mapping) else {}
        return _text(
            _enum(value.get("kind")) if isinstance(value, Mapping) else "number",
            "number",
        )

    def sheet_properties(self) -> list[ET.Element]:
        result = [
            _string_property("Label", "Parameters"),
            _expression_property([]),
            _bool_property("Visibility", False),
        ]
        sheet = _property("cells", "Spreadsheet::PropertySheet", status="67108864")
        cells = ET.SubElement(
            sheet, "Cells", {"Count": str(len(self.parameters) * 2), "xlink": "1"}
        )
        ET.SubElement(cells, "XLinks", {"count": "0"})
        for row, item in enumerate(self.parameters, start=1):
            parameter_id = _text(item.get("id"), f"parameter_{row}")
            name = _text(item.get("name"), parameter_id)
            value_data = item.get("value", {})
            raw = (
                value_data.get("value")
                if isinstance(value_data, Mapping)
                else value_data
            )
            unit = (
                _text(value_data.get("unit")) if isinstance(value_data, Mapping) else ""
            )
            kind = (
                _text(_enum(value_data.get("kind")))
                if isinstance(value_data, Mapping)
                else "number"
            )
            if isinstance(raw, bool):
                content = "=TRUE" if raw else "=FALSE"
            elif isinstance(raw, (int, float)):
                content = "=" + (f"{raw:.17g}" if isinstance(raw, float) else str(raw))
                if unit and kind in {"length", "angle"}:
                    content += f" {unit}"
            else:
                content = "'" + _text(raw)
            ET.SubElement(cells, "Cell", {"address": f"A{row}", "content": "'" + name})
            ET.SubElement(
                cells,
                "Cell",
                {
                    "address": f"B{row}",
                    "content": content,
                    "alias": self.aliases[parameter_id],
                },
            )
        result.append(sheet)
        widths = _property(
            "columnWidths", "Spreadsheet::PropertyColumnWidths", status="218103808"
        )
        ET.SubElement(widths, "ColumnInfo", {"Count": "0"})
        result.append(widths)
        heights = _property(
            "rowHeights", "Spreadsheet::PropertyRowHeights", status="218103808"
        )
        ET.SubElement(heights, "RowInfo", {"Count": "0"})
        result.append(heights)
        return result


def _geometry_property(sketch: Mapping[str, Any]) -> tuple[ET.Element, dict[str, int]]:
    entities = _items(sketch.get("entities", []))
    result = _property("Geometry", "Part::PropertyGeometryList", status="8192")
    geometry_list = ET.SubElement(result, "GeometryList", {"count": str(len(entities))})
    indices: dict[str, int] = {}
    for index, entity in enumerate(entities):
        entity_id = _text(entity.get("id"), str(index))
        indices[entity_id] = index
        kind = _text(_enum(entity.get("kind"))).lower()
        geometry = entity.get("geometry", {})
        if not isinstance(geometry, Mapping):
            geometry = {}
        type_id = {
            "line": "Part::GeomLineSegment",
            "circle": "Part::GeomCircle",
            "arc": "Part::GeomArcOfCircle",
            "point": "Part::GeomPoint",
        }.get(kind, "Part::GeomPoint")
        item = ET.SubElement(
            geometry_list,
            "Geometry",
            {"type": type_id, "id": str(index + 1), "migrated": "1"},
        )
        extensions = ET.SubElement(item, "GeoExtensions", {"count": "1"})
        construction = bool(entity.get("construction"))
        flags = (
            "00000000000000000000000000000010"
            if construction
            else "00000000000000000000000000000000"
        )
        ET.SubElement(
            extensions,
            "GeoExtension",
            {
                "type": "Sketcher::SketchGeometryExtension",
                "id": str(index + 1),
                "internalGeometryType": "0",
                "geometryModeFlags": flags,
                "geometryLayer": "0",
            },
        )
        if kind == "line":
            start = _point2(geometry.get("start"))
            end = _point2(geometry.get("end"))
            ET.SubElement(
                item,
                "LineSegment",
                {
                    "StartX": _fmt(start[0]),
                    "StartY": _fmt(start[1]),
                    "StartZ": _fmt(0),
                    "EndX": _fmt(end[0]),
                    "EndY": _fmt(end[1]),
                    "EndZ": _fmt(0),
                },
            )
        elif kind in {"circle", "arc"}:
            center = _point2(geometry.get("center"))
            attributes = {
                "CenterX": _fmt(center[0]),
                "CenterY": _fmt(center[1]),
                "CenterZ": _fmt(0),
                "NormalX": _fmt(0),
                "NormalY": _fmt(0),
                "NormalZ": _fmt(1),
                "AngleXU": _fmt(0),
                "Radius": _fmt(geometry.get("radius")),
            }
            if kind == "arc":
                attributes["StartAngle"] = _fmt(geometry.get("start_angle"))
                attributes["EndAngle"] = _fmt(geometry.get("end_angle"))
                ET.SubElement(item, "ArcOfCircle", attributes)
            else:
                ET.SubElement(item, "Circle", attributes)
        else:
            point = _point2(geometry.get("point", geometry.get("center")))
            ET.SubElement(
                item,
                "GeomPoint",
                {"X": _fmt(point[0]), "Y": _fmt(point[1]), "Z": _fmt(0)},
            )
        ET.SubElement(item, "Construction", {"value": "1" if construction else "0"})
    return result, indices


def _reference_point(value: Any) -> int:
    point = _text(value).lower()
    return {
        "start": 1,
        "startpoint": 1,
        "end": 2,
        "endpoint": 2,
        "center": 3,
        "centre": 3,
        "midpoint": 3,
    }.get(point, 0)


def _constraints_property(
    sketch: Mapping[str, Any], indices: Mapping[str, int], parameters: _Parameters
) -> tuple[ET.Element, list[tuple[str, str]], list[str]]:
    source_constraints = _items(sketch.get("constraints", []))
    encoded: list[dict[str, Any]] = []
    expressions: list[tuple[str, str]] = []
    dependencies: list[str] = []
    constraint_names: set[str] = set()
    type_codes = {
        "coincident": 1,
        "horizontal": 2,
        "vertical": 3,
        "parallel": 4,
        "tangent": 5,
        "distance": 6,
        "distance_x": 7,
        "distance_y": 8,
        "angle": 9,
        "perpendicular": 10,
        "radius": 11,
        "equal": 12,
        "concentric": 1,
        "midpoint": 13,
        "symmetric": 14,
        "fixed": 17,
        "block": 17,
        "diameter": 18,
    }
    for constraint in source_constraints:
        if bool(constraint.get("suppressed")):
            continue
        kind = _text(_enum(constraint.get("kind"))).lower()
        code = type_codes.get(kind)
        references = _items(constraint.get("references", []))
        resolved = [
            (
                indices.get(_text(ref.get("entity_id"))),
                _reference_point(ref.get("point")),
            )
            for ref in references
        ]
        resolved = [(index, point) for index, point in resolved if index is not None]
        if code is None or not resolved:
            continue
        if kind == "concentric" and len(resolved) >= 2:
            resolved = [(resolved[0][0], 3), (resolved[1][0], 3)]
        parameter_id = _text(constraint.get("parameter_id"))
        value = parameters.value(parameter_id, _number(constraint.get("value")))
        values = resolved[:3] + [(-2000, 0)] * (3 - len(resolved[:3]))
        name_base = _safe(constraint.get("id"), "Constraint")
        name = name_base
        suffix = 2
        while name in constraint_names:
            name = f"{name_base}_{suffix}"
            suffix += 1
        constraint_names.add(name)
        encoded.append(
            {
                "name": name,
                "type": code,
                "value": value,
                "driving": bool(constraint.get("driving", True)),
                "active": not bool(constraint.get("suppressed")),
                "first": values[0],
                "second": values[1],
                "third": values[2],
            }
        )
        expression = parameters.expression(parameter_id)
        if (
            expression
            and bool(constraint.get("driving", True))
            and code in {6, 7, 8, 9, 11, 18}
        ):
            expressions.append((f".Constraints.{name}", expression))
            dependencies.append("Parameters")
    fixed_entities = {
        _text(ref.get("entity_id"))
        for item in source_constraints
        if _text(_enum(item.get("kind"))).lower() in {"fixed", "block"}
        for ref in _items(item.get("references", []))
    }
    for entity in _items(sketch.get("entities", [])):
        entity_id = _text(entity.get("id"))
        if (
            bool(entity.get("fixed"))
            and entity_id not in fixed_entities
            and entity_id in indices
        ):
            encoded.append(
                {
                    "name": f"fixed_{entity_id}",
                    "type": 17,
                    "value": 0.0,
                    "driving": True,
                    "active": True,
                    "first": (indices[entity_id], 0),
                    "second": (-2000, 0),
                    "third": (-2000, 0),
                }
            )
    result = _property("Constraints", "Sketcher::PropertyConstraintList")
    constraint_list = ET.SubElement(
        result, "ConstraintList", {"count": str(len(encoded))}
    )
    for item in encoded:
        first, second, third = item["first"], item["second"], item["third"]
        ET.SubElement(
            constraint_list,
            "Constrain",
            {
                "Name": item["name"],
                "MetaData": "",
                "Type": str(item["type"]),
                "Orientation": "0",
                "Value": _fmt(item["value"]),
                "LabelDistance": _fmt(10),
                "LabelPosition": _fmt(0),
                "IsDriving": "1" if item["driving"] else "0",
                "IsInVirtualSpace": "0",
                "IsVisible": "1",
                "IsActive": "1" if item["active"] else "0",
                "First": str(first[0]),
                "FirstPos": str(first[1]),
                "Second": str(second[0]),
                "SecondPos": str(second[1]),
                "Third": str(third[0]),
                "ThirdPos": str(third[1]),
                "ElementIds": f"{first[0]} {second[0]} {third[0]}",
                "ElementPositions": f"{first[1]} {second[1]} {third[1]}",
            },
        )
    return result, expressions, dependencies


def _sketch_properties(
    sketch: Mapping[str, Any],
    plane: Mapping[str, Any],
    plane_name: str,
    parameters: _Parameters,
) -> tuple[list[ET.Element], list[str]]:
    transform = (
        plane.get("transform", {})
        if isinstance(plane.get("transform"), Mapping)
        else {}
    )
    geometry, indices = _geometry_property(sketch)
    constraints, expressions, dependencies = _constraints_property(
        sketch, indices, parameters
    )
    expressions.append(("Placement", f"{plane_name}.Placement"))
    dependencies.append(plane_name)
    properties = [
        _string_property("Label", sketch.get("name", sketch.get("id", "Sketch"))),
        _placement_property("Placement", transform),
        geometry,
        constraints,
        _expression_property(expressions),
        _shape_property("", "InternalShape"),
        _shape_property(),
        _link_property("SupportPlane", plane_name, dynamic=True),
        _string_property("KitId", sketch.get("id"), dynamic=True),
        _json_property(
            "ClosedProfilesJSON", sketch.get("closed_profile_entity_ids", [])
        ),
        _json_property("SourceSketchJSON", sketch),
        _bool_property("Visibility", False),
    ]
    return properties, dependencies


def _feature_parameter(
    feature: Mapping[str, Any], parameters: _Parameters, expected: float
) -> str:
    ids = [_text(value) for value in _sequence(feature.get("parameter_ids", []))]
    if not ids:
        ids = [
            parameter_id
            for parameter_id, item in parameters.by_id.items()
            if _text(item.get("owner_id")) == _text(feature.get("id"))
        ]
    length_ids = [
        parameter_id
        for parameter_id in ids
        if parameters.kind(parameter_id) == "length"
    ]
    for parameter_id in length_ids:
        if math.isclose(
            abs(parameters.value(parameter_id)),
            abs(expected),
            rel_tol=1e-9,
            abs_tol=1e-9,
        ):
            return parameter_id
    return length_ids[0] if length_ids else (ids[0] if ids else "")


def _feature_metadata(feature: Mapping[str, Any], role: str) -> list[ET.Element]:
    return [
        _string_property("KitId", feature.get("id"), dynamic=True),
        _string_property("KitRole", role, dynamic=True),
        _integer_property("TimelineOrder", feature.get("order", 0), dynamic=True),
        _json_property("SourceFeatureJSON", feature),
    ]


def _shape_property(filename: str = "", name: str = "Shape") -> ET.Element:
    result = _property(name, "Part::PropertyPartShape")
    attributes = {"file": filename} if filename else {}
    ET.SubElement(result, "Part", attributes)
    if filename:
        ET.SubElement(result, "ElementMap")
    return result


def _fillet_edges_property(filename: str) -> ET.Element:
    result = _property("Edges", "Part::PropertyFilletEdges")
    ET.SubElement(result, "FilletEdges", {"file": filename})
    return result


def _edge_link_property(base: str, edge_indices: list[int]) -> ET.Element:
    result = _property("EdgeLinks", "App::PropertyLinkSub")
    child = ET.SubElement(
        result, "LinkSub", {"value": base, "count": str(len(edge_indices))}
    )
    for edge_index in edge_indices:
        ET.SubElement(child, "Sub", {"value": f"Edge{edge_index}"})
    return result


def _fillet_edges_data(edge_indices: list[int], radius: float) -> bytes:
    return struct.pack("<I", len(edge_indices)) + b"".join(
        struct.pack("<idd", edge_index, radius, radius) for edge_index in edge_indices
    )


def _payload_bytes(payload: Mapping[str, Any]) -> bytes | None:
    data = payload.get("data")
    if isinstance(data, Mapping):
        if "$bytes" in data:
            try:
                return base64.b64decode(_text(data["$bytes"]), validate=True)
            except ValueError:
                return None
        if data.get("encoding") == "base64" and "data" in data:
            try:
                return base64.b64decode(_text(data["data"]), validate=True)
            except ValueError:
                return None
    if isinstance(data, str):
        try:
            return base64.b64decode(data, validate=True)
        except ValueError:
            return data.encode("utf-8")
    return bytes(data) if isinstance(data, (bytes, bytearray)) else None


def _payload_extension(payload: Mapping[str, Any]) -> str:
    format_id = _text(payload.get("format_id")).lower()
    if "parasolid" in format_id:
        return ".x_b"
    if "step" in format_id:
        return ".step"
    if "brep" in format_id or "opencascade" in format_id or format_id == "occ":
        return ".brp"
    return ".bin"


_IDENTITY_MATRIX = (
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
_JOINT_TYPES = [
    "Fixed",
    "Revolute",
    "Cylindrical",
    "Slider",
    "Ball",
    "Distance",
    "Parallel",
    "Perpendicular",
    "Angle",
    "RackPinion",
    "Screw",
    "Gears",
    "Belt",
]
_JOINT_TYPE_BY_MATE = {
    "lock": "Fixed",
    "fixed": "Fixed",
    "coincident": "Fixed",
    "hinge": "Revolute",
    "revolute": "Revolute",
    "concentric": "Cylindrical",
    "cylindrical": "Cylindrical",
    "slot": "Slider",
    "slider": "Slider",
    "ball": "Ball",
    "distance": "Distance",
    "parallel": "Parallel",
    "perpendicular": "Perpendicular",
    "angle": "Angle",
    "rack_pinion": "RackPinion",
    "rackpinion": "RackPinion",
    "screw": "Screw",
    "gear": "Gears",
    "gears": "Gears",
    "belt": "Belt",
}


def _assembly_data(manifest: Mapping[str, Any]) -> Mapping[str, Any] | None:
    value = manifest.get("assembly")
    if isinstance(value, Mapping):
        return value
    metadata = manifest.get("metadata", {})
    if isinstance(metadata, Mapping):
        value = metadata.get("assembly")
        if isinstance(value, Mapping):
            return value
    return None


def _matrix_values(value: Any) -> tuple[float, ...]:
    if isinstance(value, Mapping):
        value = value.get("values", value.get("matrix", value))
    values = tuple(_number(item) for item in _sequence(value))
    return values if len(values) == 16 else _IDENTITY_MATRIX


def _matrix_product(
    left: tuple[float, ...], right: tuple[float, ...]
) -> tuple[float, ...]:
    return tuple(
        sum(left[row * 4 + index] * right[index * 4 + column] for index in range(4))
        for row in range(4)
        for column in range(4)
    )


def _matrix_transform(values: tuple[float, ...]) -> dict[str, Any]:
    return {
        "origin": {"x": values[3], "y": values[7], "z": values[11]},
        "x_axis": {"x": values[0], "y": values[4], "z": values[8]},
        "y_axis": {"x": values[1], "y": values[5], "z": values[9]},
        "z_axis": {"x": values[2], "y": values[6], "z": values[10]},
    }


def _matrix_scale(values: tuple[float, ...]) -> tuple[float, float, float]:
    return tuple(
        math.sqrt(sum(values[row * 4 + column] ** 2 for row in range(3)))
        for column in range(3)
    )


def _expanded_instances(
    assembly: Mapping[str, Any],
) -> list[tuple[dict[str, Any], tuple[str, ...], tuple[float, ...], bool]]:
    instances = _items(assembly.get("instances", assembly.get("components", [])))
    children: dict[str, list[dict[str, Any]]] = {}
    for instance in instances:
        owner = _text(instance.get("owner_definition_id"))
        children.setdefault(owner, []).append(instance)
    for values in children.values():
        values.sort(
            key=lambda item: (int(_number(item.get("order"))), _text(item.get("id")))
        )
    root_id = _text(assembly.get("root_definition_id"))
    result: list[tuple[dict[str, Any], tuple[str, ...], tuple[float, ...], bool]] = []

    def visit(
        owner_id: str,
        parent: tuple[float, ...],
        path: tuple[str, ...],
        inherited_suppression: bool,
        active: frozenset[str],
    ) -> None:
        if owner_id in active:
            return
        next_active = active | {owner_id}
        for instance in children.get(owner_id, []):
            instance_id = _text(instance.get("id"))
            definition_id = _text(instance.get("definition_id"))
            matrix = _matrix_values(instance.get("transform", {}))
            world = _matrix_product(parent, matrix)
            instance_path = (*path, instance_id)
            suppressed = inherited_suppression or bool(instance.get("suppressed"))
            result.append((instance, instance_path, world, suppressed))
            visit(definition_id, world, instance_path, suppressed, next_active)

    visit(root_id, _IDENTITY_MATRIX, (), False, frozenset())
    return result


def _mesh_property(filename: str) -> ET.Element:
    result = _property("Mesh", "Mesh::PropertyMeshKernel")
    ET.SubElement(result, "Mesh", {"file": filename})
    return result


def _points(value: Any) -> list[tuple[float, float, float]]:
    values = _sequence(value)
    if values and all(isinstance(item, (int, float)) for item in values):
        return [
            (
                _number(values[index]),
                _number(values[index + 1]),
                _number(values[index + 2]),
            )
            for index in range(0, len(values) - 2, 3)
        ]
    return [_vector(item, (0.0, 0.0, 0.0)) for item in values]


def _triangle_indices(value: Any) -> tuple[int, int, int] | None:
    marked = _sequence(value)
    if marked:
        values = marked
    elif isinstance(value, Mapping):
        source = value.get("indices", value.get("vertices", value.get("points", [])))
        values = _sequence(source)
        if not values:
            values = [value.get("a"), value.get("b"), value.get("c")]
    else:
        values = _sequence(value)
    if len(values) < 3:
        return None
    return tuple(int(_number(item)) for item in values[:3])


def _triangle_is_valid(
    vertices: list[tuple[float, float, float]], triangle: tuple[int, int, int]
) -> bool:
    if len(set(triangle)) != 3 or any(
        index < 0 or index >= len(vertices) for index in triangle
    ):
        return False
    first, second, third = (vertices[index] for index in triangle)
    left = tuple(second[index] - first[index] for index in range(3))
    right = tuple(third[index] - first[index] for index in range(3))
    cross = (
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    )
    return sum(value * value for value in cross) > 1e-24


def _tessellation_data(
    value: Any,
) -> tuple[list[tuple[float, float, float]], list[tuple[int, int, int]]]:
    if not isinstance(value, Mapping):
        return [], []
    vertices = _points(value.get("vertices", value.get("positions_mm", [])))
    triangles = [
        triangle
        for item in _sequence(value.get("triangles", []))
        if (triangle := _triangle_indices(item)) is not None
    ]
    if vertices and triangles:
        return vertices, [
            triangle for triangle in triangles if _triangle_is_valid(vertices, triangle)
        ]
    vertices = []
    triangles = []
    faces = _items(value.get("faces", []))
    for face in faces:
        face_vertices = _points(face.get("positions_mm", face.get("vertices", [])))
        base = len(vertices)
        vertices.extend(face_vertices)
        cursor = 0
        strip_lengths = [
            int(_number(item)) for item in _sequence(face.get("strip_lengths", []))
        ]
        if not strip_lengths and face_vertices:
            strip_lengths = [len(face_vertices)]
        for strip_length in strip_lengths:
            for offset in range(max(0, strip_length - 2)):
                if offset % 2:
                    triangle = (
                        base + cursor + offset + 1,
                        base + cursor + offset,
                        base + cursor + offset + 2,
                    )
                else:
                    triangle = (
                        base + cursor + offset,
                        base + cursor + offset + 1,
                        base + cursor + offset + 2,
                    )
                if _triangle_is_valid(vertices, triangle):
                    triangles.append(triangle)
            cursor += strip_length
    return vertices, triangles


def _definition_tessellation(definition: Mapping[str, Any]) -> Any:
    direct = definition.get("tessellation")
    if isinstance(direct, Mapping):
        return direct
    attributes = definition.get("attributes", {})
    if isinstance(attributes, Mapping):
        return attributes.get("tessellation", {})
    return {}


def _definition_mesh_sources(
    manifest: Mapping[str, Any], definition: Mapping[str, Any]
) -> list[Mapping[str, Any]]:
    meshes = {
        _text(item.get("id")): item for item in _items(manifest.get("meshes", []))
    }
    result = [
        meshes[mesh_id]
        for mesh_id in (
            _text(value) for value in _sequence(definition.get("mesh_ids", []))
        )
        if mesh_id in meshes
    ]
    inline = _definition_tessellation(definition)
    if isinstance(inline, Mapping) and inline:
        result.append(inline)
    return result


def _mesh_kernel_data(
    vertices: list[tuple[float, float, float]], triangles: list[tuple[int, int, int]]
) -> bytes:
    neighbors = [[-1, -1, -1] for _ in triangles]
    edge_uses: dict[tuple[int, int], tuple[int, ...] | None] = {}
    for triangle_index, triangle in enumerate(triangles):
        for edge_index, edge in enumerate(
            (
                (triangle[0], triangle[1]),
                (triangle[1], triangle[2]),
                (triangle[2], triangle[0]),
            )
        ):
            key = tuple(sorted(edge))
            previous = edge_uses.get(key, ())
            if previous == ():
                edge_uses[key] = (triangle_index, edge_index)
            elif previous is None:
                continue
            elif len(previous) == 2:
                previous_triangle, previous_edge = previous
                neighbors[previous_triangle][previous_edge] = triangle_index
                neighbors[triangle_index][edge_index] = previous_triangle
                edge_uses[key] = (
                    previous_triangle,
                    previous_edge,
                    triangle_index,
                    edge_index,
                )
            else:
                first_triangle, first_edge, second_triangle, second_edge = previous
                neighbors[first_triangle][first_edge] = -1
                neighbors[second_triangle][second_edge] = -1
                edge_uses[key] = None
    banner = (b"MESH-" * 52)[:255] + b"\n"
    result = bytearray(struct.pack("<II", 0xA0B0C0D0, 0x00010000))
    result.extend(banner)
    result.extend(struct.pack("<II", len(vertices), len(triangles)))
    for vertex in vertices:
        result.extend(struct.pack("<fff", *vertex))
    for triangle, adjacent in zip(triangles, neighbors):
        result.extend(struct.pack("<iiiiii", *triangle, *adjacent))
    if vertices:
        minimum = tuple(min(vertex[index] for vertex in vertices) for index in range(3))
        maximum = tuple(max(vertex[index] for vertex in vertices) for index in range(3))
    else:
        minimum = maximum = (0.0, 0.0, 0.0)
    result.extend(struct.pack("<ffffff", *minimum, *maximum))
    return bytes(result)


def _unique_payload_name(payload_entries: Mapping[str, bytes], requested: str) -> str:
    path = PurePosixPath(requested)
    stem = path.stem
    suffix = path.suffix
    parent = path.parent
    candidate = str(path)
    index = 2
    while candidate in payload_entries:
        candidate = str(parent / f"{stem}_{index}{suffix}")
        index += 1
    return candidate


def _rename_property_links(
    property_element: ET.Element,
    names: Mapping[str, str],
    files: Mapping[str, str],
) -> None:
    for element in property_element.iter():
        if element.tag == "Link" and element.get("value") in names:
            element.set("value", names[element.get("value", "")])
        elif element.tag == "XLink" and element.get("name") in names:
            element.set("name", names[element.get("name", "")])
        elif element.tag == "LinkSub" and element.get("value") in names:
            element.set("value", names[element.get("value", "")])
        filename = element.get("file")
        if filename in files:
            element.set("file", files[filename])
        expression = element.get("expression")
        if expression:
            for old, new in sorted(
                names.items(), key=lambda item: len(item[0]), reverse=True
            ):
                expression = re.sub(rf"\b{re.escape(old)}\b", new, expression)
            element.set("expression", expression)


def _import_component_document(
    graph: _Graph,
    document: Mapping[str, Any],
    prefix: str,
    payload_entries: dict[str, bytes],
) -> tuple[str, list[str]]:
    canonical = json.dumps(
        document, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    document_xml, child_payloads = _document_xml(document, "", digest)
    root = ET.fromstring(document_xml)
    object_nodes = root.findall("./Objects/Object")
    data_nodes = {
        node.get("name", ""): node for node in root.findall("./ObjectData/Object")
    }
    dependencies = {
        node.get("Name", ""): [child.get("Name", "") for child in node.findall("./Dep")]
        for node in root.findall("./Objects/ObjectDeps")
    }
    metadata_node = data_nodes.get("KitMetadata")
    final_old = ""
    if metadata_node is not None:
        final = metadata_node.find("./Properties/Property[@name='FinalFeature']/String")
        final_old = final.get("value", "") if final is not None else ""
    included = [node for node in object_nodes if node.get("name") != "KitMetadata"]
    names = {
        node.get("name", ""): graph.unique(
            f"{prefix}_{node.get('name', '')}", "Component"
        )
        for node in included
    }
    files: dict[str, str] = {}
    for filename, data in sorted(child_payloads.items()):
        if filename.startswith("interchange/native/"):
            requested = str(
                PurePosixPath(
                    "interchange", "components", prefix, PurePosixPath(filename).name
                )
            )
        else:
            requested = f"{prefix}_{PurePosixPath(filename).name}"
        renamed = _unique_payload_name(payload_entries, requested)
        payload_entries[renamed] = data
        files[filename] = renamed
    imported: list[str] = []
    for node in included:
        old_name = node.get("name", "")
        data_node = data_nodes.get(old_name)
        if data_node is None:
            continue
        properties = [
            copy.deepcopy(value) for value in data_node.findall("./Properties/Property")
        ]
        for property_element in properties:
            _rename_property_links(property_element, names, files)
        extensions = tuple(
            value.get("type", "")
            for value in data_node.findall("./Extensions/Extension")
            if value.get("type")
        )
        imported_object = _Object(
            node.get("type", "App::FeaturePython"),
            names[old_name],
            properties,
            [
                names[value]
                for value in dependencies.get(old_name, [])
                if value in names
            ],
            node.get("Touched") == "1",
            extensions,
        )
        graph.objects.append(imported_object)
        imported.append(imported_object.name)
    target = names.get(final_old, "")
    if not target:
        for node in reversed(included):
            old_name = node.get("name", "")
            data_node = data_nodes.get(old_name)
            if (
                data_node is not None
                and data_node.find("./Properties/Property[@name='Shape']") is not None
            ):
                target = names.get(old_name, "")
                break
    return target, imported


def _mate_joint_type(kind: Any) -> str:
    return _JOINT_TYPE_BY_MATE.get(_text(_enum(kind)).lower(), "Fixed")


def _mate_value(value: Any) -> float:
    if isinstance(value, Mapping):
        return _number(value.get("value"))
    return _number(value)


def _mate_subelements(entity: Mapping[str, Any]) -> list[str]:
    for value in (
        _text(entity.get("source_entity_id")),
        _text(entity.get("selection_id")),
    ):
        if re.fullmatch(r"(?:Face|Edge|Vertex)\d+", value):
            return [value, value]
    return []


def _without_tessellation(value: Mapping[str, Any]) -> dict[str, Any]:
    result = dict(value)
    result.pop("tessellation", None)
    attributes = result.get("attributes")
    if isinstance(attributes, Mapping):
        cleaned = dict(attributes)
        cleaned.pop("tessellation", None)
        result["attributes"] = cleaned
    return result


def _add_assembly_origin(graph: _Graph, assembly: _Object) -> str:
    origin = graph.add(
        "App::Origin",
        f"{assembly.name}_Origin",
        "Origin",
        extensions=("App::GeoFeatureGroupExtension",),
    )
    definitions = [
        (
            "App::Line",
            "X_Axis",
            "X-axis",
            "X_Axis",
            _IDENTITY_MATRIX,
        ),
        (
            "App::Line",
            "Y_Axis",
            "Y-axis",
            "Y_Axis",
            (
                0.0,
                0.0,
                1.0,
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
                0.0,
                1.0,
            ),
        ),
        (
            "App::Line",
            "Z_Axis",
            "Z-axis",
            "Z_Axis",
            (
                0.0,
                -1.0,
                0.0,
                0.0,
                0.0,
                0.0,
                -1.0,
                0.0,
                1.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                1.0,
            ),
        ),
        (
            "App::Plane",
            "XY_Plane",
            "XY-plane",
            "XY_Plane",
            _IDENTITY_MATRIX,
        ),
        (
            "App::Plane",
            "XZ_Plane",
            "XZ-plane",
            "XZ_Plane",
            (
                1.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                -1.0,
                0.0,
                0.0,
                1.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                1.0,
            ),
        ),
        (
            "App::Plane",
            "YZ_Plane",
            "YZ-plane",
            "YZ_Plane",
            (
                0.0,
                0.0,
                1.0,
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
                0.0,
                1.0,
            ),
        ),
        (
            "App::Point",
            "Origin_Point",
            "Origin-Point",
            "Origin",
            _IDENTITY_MATRIX,
        ),
    ]
    features: list[str] = []
    for type_id, suffix, label, role, matrix in definitions:
        feature = graph.add(type_id, f"{assembly.name}_{suffix}", suffix)
        feature.properties.extend(
            [
                _string_property("Label", label),
                _placement_property("Placement", _matrix_transform(matrix)),
                _string_property("Role", role),
                _bool_property("Visibility", False),
            ]
        )
        features.append(feature.name)
    origin.properties.extend(
        [
            _string_property("Label", "Origin"),
            _link_list_property("OriginFeatures", features),
            _placement_property("Placement", _matrix_transform(_IDENTITY_MATRIX)),
            _bool_property("Visibility", False),
        ]
    )
    origin.dependencies.extend(features)
    assembly.properties.append(_link_property("Origin", origin.name))
    assembly.dependencies.append(origin.name)
    return origin.name


def _grounded_joint(graph: _Graph, component: str, label: str) -> _Object:
    joint = graph.add("App::FeaturePython", f"Grounded_{label}", "GroundedJoint")
    target = _property("ObjectToGround", "App::PropertyLinkGlobal", dynamic=True)
    ET.SubElement(target, "Link", {"value": component})
    joint.properties.extend(
        [
            _string_property("Label", f"Grounded {label}"),
            target,
            _python_proxy_property("JointObject", "GroundedJoint"),
            _bool_property("Visibility", False),
        ]
    )
    joint.dependencies.append(component)
    return joint


def _replace_named_property(
    properties: list[ET.Element], name: str, replacement: ET.Element
) -> None:
    for index, property_element in enumerate(properties):
        if property_element.get("name") == name:
            properties[index] = replacement
            return
    properties.append(replacement)


def _add_assembly(
    graph: _Graph,
    manifest: Mapping[str, Any],
    payload_entries: dict[str, bytes],
    external_links: Mapping[str, Mapping[str, Any]],
) -> tuple[str, int, int]:
    assembly = _assembly_data(manifest)
    if assembly is None:
        return "", 0, 0
    definitions = _items(assembly.get("definitions", []))
    documents = {
        _text(item.get("id")): item.get("document")
        for item in _items(assembly.get("documents", []))
        if isinstance(item.get("document"), Mapping)
    }
    root_definition_id = _text(assembly.get("root_definition_id"))
    definitions_by_id = {_text(item.get("id")): item for item in definitions}
    instances_by_id = {
        _text(item.get("id")): item
        for item in _items(assembly.get("instances", assembly.get("components", [])))
    }
    root_definition = definitions_by_id.get(root_definition_id, {})
    root_label = _text(root_definition.get("name"), "Assembly")
    root = graph.add(
        "Assembly::AssemblyObject",
        root_label,
        "Assembly",
        extensions=("App::OriginGroupExtension",),
    )
    root_origin = _add_assembly_origin(graph, root)
    definitions_group = graph.add(
        "App::DocumentObjectGroup", f"{root_label}_Definitions", "Definitions"
    )
    components_group = graph.add(
        "App::DocumentObjectGroup", f"{root_label}_Components", "Components"
    )
    entities_group = graph.add(
        "App::DocumentObjectGroup", f"{root_label}_MateEntities", "MateEntities"
    )
    mates_group = graph.add(
        "Assembly::JointGroup",
        f"{root_label}_Joints",
        "Joints",
        extensions=("App::GroupExtension",),
    )
    definition_objects: list[str] = []
    definition_targets: dict[str, str] = {}
    definition_external: dict[str, Mapping[str, Any]] = {}
    for definition in definitions:
        definition_id = _text(definition.get("id"))
        definition_name = _text(definition.get("name"), definition_id)
        definition_prefix = _safe(f"Definition_{definition_id}", "Definition")
        imported: list[str] = []
        imported_target = ""
        document_id = _text(definition.get("document_id"))
        document = documents.get(document_id)
        component_kind = _text(_enum(definition.get("kind"))).lower()
        external = external_links.get(definition_id)
        if external is not None:
            definition_external[definition_id] = external
        elif isinstance(document, Mapping):
            imported_document = document
            if component_kind == "assembly":
                imported_document = dict(document)
                imported_document["assembly"] = None
            imported_target, imported = _import_component_document(
                graph, imported_document, definition_prefix, payload_entries
            )
            if imported_target:
                target_object = next(
                    (item for item in graph.objects if item.name == imported_target),
                    None,
                )
                if target_object is not None:
                    _replace_named_property(
                        target_object.properties,
                        "Visibility",
                        _bool_property("Visibility", False),
                    )
        vertices: list[tuple[float, float, float]] = []
        triangles: list[tuple[int, int, int]] = []
        for mesh_source in (
            []
            if external is not None
            else _definition_mesh_sources(manifest, definition)
        ):
            mesh_vertices, mesh_triangles = _tessellation_data(mesh_source)
            offset = len(vertices)
            vertices.extend(mesh_vertices)
            triangles.extend(
                tuple(index + offset for index in triangle)
                for triangle in mesh_triangles
            )
        mesh_name = ""
        if vertices and triangles:
            mesh = graph.add(
                "Mesh::Feature", f"{definition_name}_Mesh", "ComponentMesh"
            )
            filename = _unique_payload_name(
                payload_entries, f"{mesh.name}.MeshKernel.bms"
            )
            payload_entries[filename] = _mesh_kernel_data(vertices, triangles)
            mesh.properties.extend(
                [
                    _string_property("Label", f"{definition_name} geometry"),
                    _mesh_property(filename),
                    _placement_property(
                        "Placement", _matrix_transform(_IDENTITY_MATRIX)
                    ),
                    _string_property("DefinitionId", definition_id, dynamic=True),
                    _bool_property("Visibility", False),
                ]
            )
            mesh_name = mesh.name
        definition_object = graph.add(
            "App::DocumentObjectGroup",
            f"{definition_name}_Definition",
            "ComponentDefinition",
        )
        children = [*imported, *([mesh_name] if mesh_name else [])]
        definition_object.properties.extend(
            [
                _string_property("Label", definition_name),
                _link_list_property("Group", children),
                _string_property("DefinitionId", definition_id, dynamic=True),
                _string_property(
                    "ComponentKind", _text(_enum(definition.get("kind"))), dynamic=True
                ),
                _string_property("DocumentId", document_id, dynamic=True),
                _string_property(
                    "ConfigurationName",
                    definition.get("configuration_name", ""),
                    dynamic=True,
                ),
                _string_property(
                    "ConfigurationId",
                    definition.get("configuration_id", ""),
                    dynamic=True,
                ),
                _string_property(
                    "SourcePath", definition.get("source_path", ""), dynamic=True
                ),
                _string_property(
                    "SourceFormat",
                    definition.get("source_format_id", ""),
                    dynamic=True,
                ),
                _string_property(
                    "SourceSHA256",
                    definition.get("source_sha256", ""),
                    dynamic=True,
                ),
                _json_property("DefinitionDataJSON", _without_tessellation(definition)),
                _bool_property("Visibility", False),
            ]
        )
        definition_object.dependencies.extend(children)
        definition_objects.append(definition_object.name)
        definition_targets[definition_id] = (
            mesh_name or imported_target or definition_object.name
        )
    direct_instances = sorted(
        (
            instance
            for instance in _items(
                assembly.get("instances", assembly.get("components", []))
            )
            if _text(instance.get("owner_definition_id")) == root_definition_id
        ),
        key=lambda item: (int(_number(item.get("order"))), _text(item.get("id"))),
    )
    occurrence_objects: list[str] = []
    occurrence_by_path: dict[tuple[str, ...], str] = {}
    proxy_chain_by_path: dict[tuple[str, ...], tuple[str, ...]] = {}
    assembly_link_records: list[tuple[tuple[str, ...], _Object, Mapping[str, Any]]] = []
    rigid_subassembly_ids: set[str] = set()
    grounded_objects: list[str] = []
    for instance in direct_instances:
        instance_id = _text(instance.get("id"))
        path = (instance_id,)
        definition_id = _text(instance.get("definition_id"))
        target = definition_targets.get(definition_id)
        external = definition_external.get(definition_id)
        if not target and external is None:
            continue
        label = _text(instance.get("name"), instance_id)
        component_kind = _text(
            _enum(definitions_by_id.get(definition_id, {}).get("kind"))
        ).lower()
        is_assembly_link = external is not None and component_kind == "assembly"
        placement_matrix = _matrix_values(instance.get("transform", {}))
        component = graph.add(
            "Assembly::AssemblyLink" if is_assembly_link else "App::Link",
            f"{label}_{'_'.join(path)}",
            "Component",
            touched=is_assembly_link,
            extensions=(
                ("App::OriginGroupExtension",)
                if is_assembly_link
                else ("App::LinkExtension",)
            ),
        )
        if is_assembly_link:
            _add_assembly_origin(graph, component)
        if component_kind == "assembly" and not bool(instance.get("flexible")):
            rigid_subassembly_ids.add(instance_id)
        suppressed = bool(instance.get("suppressed"))
        hidden = bool(instance.get("hidden")) or suppressed
        linked_object = (
            _xlink_property(
                "LinkedObject",
                _text(external.get("target")),
                file=_text(external.get("file")),
                stamp=_text(external.get("stamp")),
                status=None if is_assembly_link else "256",
            )
            if external is not None
            else _xlink_property("LinkedObject", target)
        )
        placement = _placement_property(
            "Placement",
            _matrix_transform(placement_matrix),
            status="8388608" if is_assembly_link else "264",
        )
        native_link_properties = (
            [
                _bool_property("Rigid", not bool(instance.get("flexible"))),
                _link_list_property("Group", []),
                _string_property("Type", ""),
            ]
            if is_assembly_link
            else [
                _placement_property(
                    "LinkPlacement", _matrix_transform(placement_matrix), status="256"
                ),
                _bool_property("LinkTransform", True),
                _vector_property("ScaleVector", _matrix_scale(placement_matrix)),
            ]
        )
        component.properties.extend(
            [
                _string_property("Label", label),
                linked_object,
                placement,
                *native_link_properties,
                _string_property("InstanceId", instance_id, dynamic=True),
                _string_property("DefinitionId", definition_id, dynamic=True),
                _string_property(
                    "OwnerDefinitionId",
                    instance.get("owner_definition_id", ""),
                    dynamic=True,
                ),
                _string_list_property("InstancePath", list(path), dynamic=True),
                _string_property(
                    "ReferenceNumber",
                    instance.get("reference_number", ""),
                    dynamic=True,
                ),
                _string_property(
                    "ConfigurationName",
                    instance.get("configuration_name", ""),
                    dynamic=True,
                ),
                _string_property(
                    "ConfigurationId",
                    instance.get("configuration_id", ""),
                    dynamic=True,
                ),
                _bool_property("Suppressed", suppressed, dynamic=True),
                _bool_property("Hidden", bool(instance.get("hidden")), dynamic=True),
                _bool_property("Fixed", bool(instance.get("fixed")), dynamic=True),
                _bool_property(
                    "Flexible", bool(instance.get("flexible")), dynamic=True
                ),
                _bool_property(
                    "ExcludeFromBOM",
                    bool(instance.get("exclude_from_bom")),
                    dynamic=True,
                ),
                _json_property("InstanceDataJSON", instance),
                _bool_property("Visibility", not hidden),
            ]
        )
        if external is None and target:
            component.dependencies.append(target)
        occurrence_objects.append(component.name)
        occurrence_by_path[path] = component.name
        if is_assembly_link and external is not None:
            assembly_link_records.append((path, component, external))
        if bool(instance.get("fixed")) and not suppressed:
            grounded = _grounded_joint(graph, component.name, label)
            grounded_objects.append(grounded.name)

    def add_external_occurrences(
        root_path: tuple[str, ...],
        parent: _Object,
        external: Mapping[str, Any],
        records: Any,
        parent_source_path: tuple[str, ...] = (),
        parent_chain: tuple[str, ...] = (),
    ) -> list[str]:
        children: list[str] = []
        for record in _items(records):
            target = _text(record.get("target"))
            type_id = _text(record.get("type_id"))
            instance_id = _text(record.get("instance_id"))
            if (
                not target
                or not instance_id
                or type_id not in {"App::Link", "Assembly::AssemblyLink"}
            ):
                continue
            source_path = tuple(
                _text(value)
                for value in _sequence(record.get("instance_path", []))
                if _text(value)
            )
            if not source_path:
                source_path = (*parent_source_path, instance_id)
            elif parent_source_path and source_path[: len(parent_source_path)] != (
                parent_source_path
            ):
                source_path = (*parent_source_path, *source_path)
            full_path = (*root_path, *source_path)
            neutral = instances_by_id.get(instance_id, {})

            def value(name: str, default: Any = "") -> Any:
                if name in record:
                    return record.get(name)
                return neutral.get(name, default)

            label = _text(value("label", value("name", instance_id)), instance_id)
            placement_matrix = _matrix_values(value("transform", {}))
            is_assembly_link = type_id == "Assembly::AssemblyLink"
            proxy = graph.add(
                type_id,
                f"{parent.name}_{target}",
                "Component",
                touched=is_assembly_link,
                extensions=(
                    ("App::OriginGroupExtension",)
                    if is_assembly_link
                    else ("App::LinkExtension",)
                ),
            )
            if is_assembly_link:
                _add_assembly_origin(graph, proxy)
            linked_object = _xlink_property(
                "LinkedObject",
                target,
                file=_text(external.get("file")),
                stamp=_text(external.get("stamp")),
                status=None if is_assembly_link else "256",
            )
            native_link_properties = (
                [
                    _bool_property(
                        "Rigid", bool(value("rigid", not bool(value("flexible"))))
                    ),
                    _link_list_property("Group", []),
                    _string_property("Type", ""),
                ]
                if is_assembly_link
                else [
                    _placement_property(
                        "LinkPlacement",
                        _matrix_transform(placement_matrix),
                        status="256",
                    ),
                    _bool_property("LinkTransform", True),
                    _vector_property(
                        "ScaleVector",
                        _vector(
                            value("scale", _matrix_scale(placement_matrix)),
                            _matrix_scale(placement_matrix),
                        ),
                    ),
                ]
            )
            instance_data = value("instance_data", neutral)
            proxy.properties.extend(
                [
                    _string_property("Label", label),
                    linked_object,
                    _placement_property(
                        "Placement",
                        _matrix_transform(placement_matrix),
                        status="8388608" if is_assembly_link else "264",
                    ),
                    *native_link_properties,
                    _string_property("InstanceId", instance_id, dynamic=True),
                    _string_property(
                        "DefinitionId", value("definition_id"), dynamic=True
                    ),
                    _string_property(
                        "OwnerDefinitionId",
                        value("owner_definition_id"),
                        dynamic=True,
                    ),
                    _string_list_property(
                        "InstancePath", list(full_path), dynamic=True
                    ),
                    _string_property(
                        "ReferenceNumber", value("reference_number"), dynamic=True
                    ),
                    _string_property(
                        "ConfigurationName",
                        value("configuration_name"),
                        dynamic=True,
                    ),
                    _string_property(
                        "ConfigurationId", value("configuration_id"), dynamic=True
                    ),
                    _bool_property(
                        "Suppressed", bool(value("suppressed")), dynamic=True
                    ),
                    _bool_property("Hidden", bool(value("hidden")), dynamic=True),
                    _bool_property("Fixed", bool(value("fixed")), dynamic=True),
                    _bool_property("Flexible", bool(value("flexible")), dynamic=True),
                    _bool_property(
                        "ExcludeFromBOM",
                        bool(value("exclude_from_bom")),
                        dynamic=True,
                    ),
                    _json_property("InstanceDataJSON", instance_data),
                    _bool_property(
                        "Visibility",
                        bool(
                            value(
                                "visibility",
                                not bool(value("hidden"))
                                and not bool(value("suppressed")),
                            )
                        ),
                    ),
                ]
            )
            children.append(proxy.name)
            occurrence_by_path[full_path] = proxy.name
            chain = (*parent_chain, proxy.name)
            proxy_chain_by_path[full_path] = chain
            if is_assembly_link:
                add_external_occurrences(
                    root_path,
                    proxy,
                    external,
                    record.get("occurrences", []),
                    source_path,
                    chain,
                )
        _replace_named_property(
            parent.properties, "Group", _link_list_property("Group", children)
        )
        parent.dependencies.extend(children)
        return children

    for root_path, component, external in assembly_link_records:
        add_external_occurrences(
            root_path,
            component,
            external,
            external.get("occurrences", []),
        )
    entity_items = [
        entity
        for entity in _items(
            assembly.get("mate_entities", assembly.get("entities", []))
        )
        if _text(entity.get("owner_definition_id")) == root_definition_id
    ]
    entity_objects: list[str] = []
    entity_names: dict[str, str] = {}
    entity_components: dict[str, str] = {}
    entity_prefixes: dict[str, str] = {}

    def component_for_path(path: tuple[str, ...]) -> str:
        if not path:
            return root_origin
        direct = occurrence_by_path.get((path[0],), "")
        if len(path) == 1 or path[0] in rigid_subassembly_ids:
            return direct
        return ""

    def prefix_for_path(path: tuple[str, ...]) -> str:
        if len(path) <= 1 or path[0] not in rigid_subassembly_ids:
            return ""
        for length in range(len(path), 1, -1):
            chain = proxy_chain_by_path.get(path[:length])
            if chain:
                return ".".join(chain)
        return ""

    for entity in entity_items:
        entity_id = _text(entity.get("id"))
        owner_id = _text(entity.get("owner_definition_id"))
        path = tuple(
            _text(value) for value in _sequence(entity.get("instance_path", []))
        )
        component_name = component_for_path(path)
        component_prefix = prefix_for_path(path)
        obj = graph.add("App::FeaturePython", entity_id, "MateEntity")
        properties = [
            _string_property("Label", entity_id),
            _string_property("EntityId", entity_id, dynamic=True),
            _string_property(
                "OwnerDefinitionId",
                owner_id,
                dynamic=True,
            ),
            _string_list_property("OwnerOccurrencePath", [], dynamic=True),
            _string_list_property("InstancePath", list(path), dynamic=True),
            _string_property(
                "EntityKind", _text(_enum(entity.get("kind"))), dynamic=True
            ),
            _string_property(
                "SourceEntityId", entity.get("source_entity_id", ""), dynamic=True
            ),
            _string_property(
                "SelectionId", entity.get("selection_id", ""), dynamic=True
            ),
            _json_property("EntityDataJSON", entity),
            _bool_property("Visibility", False),
        ]
        frame = entity.get("frame")
        if isinstance(frame, Mapping):
            properties.append(
                _placement_property(
                    "ConnectorFrame",
                    _matrix_transform(_matrix_values(frame)),
                    dynamic=True,
                )
            )
        if entity.get("radius") is not None:
            properties.append(
                _float_property(
                    "Radius",
                    entity.get("radius"),
                    "App::PropertyLength",
                    dynamic=True,
                )
            )
        if component_name:
            properties.append(
                _string_property("ComponentName", component_name, dynamic=True)
            )
            entity_components[entity_id] = component_name
        if component_prefix:
            properties.append(
                _string_property("ComponentSubpath", component_prefix, dynamic=True)
            )
            entity_prefixes[entity_id] = component_prefix
        obj.properties.extend(properties)
        entity_objects.append(obj.name)
        entity_names[entity_id] = obj.name
    mate_items = sorted(
        (
            mate
            for mate in _items(assembly.get("mates", assembly.get("constraints", [])))
            if _text(mate.get("owner_definition_id")) == root_definition_id
        ),
        key=lambda item: (int(_number(item.get("order"))), _text(item.get("id"))),
    )
    mate_objects: list[str] = []
    mate_names: dict[str, str] = {}
    entity_by_id = {_text(item.get("id")): item for item in entity_items}

    def connector_target(entity_id: str) -> str:
        target = entity_components.get(entity_id, "")
        if target:
            return target
        return component_for_path(
            tuple(
                _text(value)
                for value in _sequence(
                    entity_by_id.get(entity_id, {}).get("instance_path", [])
                )
            )
        )

    for mate in mate_items:
        mate_id = _text(mate.get("id"))
        mate_name = _text(mate.get("name"), mate_id)
        owner_id = _text(mate.get("owner_definition_id"))
        entity_ids = [_text(value) for value in _sequence(mate.get("entity_ids", []))]
        linked_entities = [
            entity_names[value] for value in entity_ids if value in entity_names
        ]
        linked_components = list(
            dict.fromkeys(
                entity_components[value]
                for value in entity_ids
                if value in entity_components
            )
        )
        connector_targets = [connector_target(value) for value in entity_ids[:2]]
        has_connector_pair = len(connector_targets) == 2 and all(connector_targets)
        joint_type = _mate_joint_type(mate.get("kind"))
        obj = graph.add(
            "App::FeaturePython",
            mate_name,
            "Mate",
            extensions=("App::SuppressibleExtensionPython",),
        )
        connector_properties: list[ET.Element] = []
        for index in range(1, 3):
            entity_id = entity_ids[index - 1] if index <= len(entity_ids) else ""
            component_name = (
                connector_targets[index - 1] if index <= len(connector_targets) else ""
            )
            entity = entity_by_id.get(entity_id, {})
            subelements = _mate_subelements(entity)
            has_real_subelements = bool(subelements)
            component_prefix = entity_prefixes.get(entity_id, "")
            if component_prefix:
                subelements = [
                    f"{component_prefix}.{value}" if value else f"{component_prefix}."
                    for value in (subelements or ["", ""])
                ]
            elif component_name and not subelements:
                subelements = ["", ""]
            connector_properties.append(
                _xlink_sub_property(
                    f"Reference{index}", component_name, subelements, dynamic=True
                )
            )
            frame = entity.get("frame")
            matrix = (
                _matrix_values(frame)
                if isinstance(frame, Mapping)
                else _IDENTITY_MATRIX
            )
            connector_properties.extend(
                [
                    _placement_property(
                        f"Placement{index}",
                        _matrix_transform(matrix),
                        dynamic=True,
                    ),
                    _placement_property(
                        f"Offset{index}",
                        _matrix_transform(_IDENTITY_MATRIX),
                        dynamic=True,
                    ),
                    _bool_property(
                        f"Detach{index}",
                        isinstance(frame, Mapping) and not has_real_subelements,
                        dynamic=True,
                    ),
                ]
            )
        properties = [
            _string_property("Label", mate_name),
            _string_property("MateId", mate_id, dynamic=True),
            _string_list_property("OwnerOccurrencePath", [], dynamic=True),
            _string_property("MateType", _text(_enum(mate.get("kind"))), dynamic=True),
            _enumeration_choices_property(
                "JointType", _JOINT_TYPES, _JOINT_TYPES.index(joint_type), dynamic=True
            ),
            _string_property(
                "OwnerDefinitionId",
                owner_id,
                dynamic=True,
            ),
            _string_list_property("EntityLinks", linked_entities, dynamic=True),
            _string_list_property("ComponentLinks", linked_components, dynamic=True),
            _string_list_property("EntityIds", entity_ids, dynamic=True),
            _string_list_property(
                "ParameterIds",
                [_text(value) for value in _sequence(mate.get("parameter_ids", []))],
                dynamic=True,
            ),
            _string_property(
                "Alignment", _text(_enum(mate.get("alignment"))), dynamic=True
            ),
            _bool_property(
                "SourceSuppressed", bool(mate.get("suppressed")), dynamic=True
            ),
            _bool_property(
                "Suppressed",
                bool(mate.get("suppressed")) or not has_connector_pair,
            ),
            _bool_property("Driving", bool(mate.get("driving", True)), dynamic=True),
            _json_property("MateValueJSON", mate.get("value")),
            _json_property("MateDataJSON", mate),
        ]
        numeric_value = _mate_value(mate.get("value"))
        properties.extend(
            [
                _float_property(
                    "Angle",
                    numeric_value if joint_type == "Angle" else 0.0,
                    "App::PropertyAngle",
                    dynamic=True,
                ),
                _float_property(
                    "Distance",
                    numeric_value if joint_type == "Distance" else 0.0,
                    "App::PropertyLength",
                    dynamic=True,
                ),
                _float_property("Distance2", 0.0, "App::PropertyLength", dynamic=True),
                _float_property("LengthMin", 0.0, "App::PropertyLength", dynamic=True),
                _float_property("LengthMax", 0.0, "App::PropertyLength", dynamic=True),
                _float_property("AngleMin", 0.0, "App::PropertyAngle", dynamic=True),
                _float_property("AngleMax", 0.0, "App::PropertyAngle", dynamic=True),
                _bool_property("EnableLengthMin", False, dynamic=True),
                _bool_property("EnableLengthMax", False, dynamic=True),
                _bool_property("EnableAngleMin", False, dynamic=True),
                _bool_property("EnableAngleMax", False, dynamic=True),
                *connector_properties,
                _python_proxy_property("JointObject", "Joint"),
                _bool_property("Visibility", False),
            ]
        )
        obj.properties.extend(properties)
        obj.dependencies.extend(connector_targets)
        mate_objects.append(obj.name)
        mate_names[mate_id] = obj.name
    group_items = sorted(
        (
            group
            for group in _items(assembly.get("mate_groups", assembly.get("groups", [])))
            if _text(group.get("owner_definition_id")) == root_definition_id
        ),
        key=lambda item: (int(_number(item.get("order"))), _text(item.get("id"))),
    )
    group_names: dict[str, str] = {}
    group_objects: list[_Object] = []
    for group in group_items:
        group_id = _text(group.get("id"))
        obj = graph.add(
            "App::DocumentObjectGroup",
            group.get("name", group_id),
            "MateGroup",
        )
        group_names[group_id] = obj.name
        group_objects.append(obj)
    grouped_mates: set[str] = set()
    child_groups: set[str] = set()
    for group, obj in zip(group_items, group_objects):
        members = [
            mate_names[value]
            for value in (_text(item) for item in _sequence(group.get("mate_ids", [])))
            if value in mate_names
        ]
        grouped_mates.update(members)
        nested = [
            name
            for group_id, name in group_names.items()
            if _text(
                next(
                    (
                        item.get("parent_group_id")
                        for item in group_items
                        if _text(item.get("id")) == group_id
                    ),
                    "",
                )
            )
            == _text(group.get("id"))
        ]
        child_groups.update(nested)
        children = [*nested, *members]
        obj.properties.extend(
            [
                _string_property("Label", group.get("name", group.get("id", ""))),
                _link_list_property("Group", children),
                _string_property("MateGroupId", group.get("id", ""), dynamic=True),
                _bool_property("Visibility", False),
            ]
        )
        obj.dependencies.extend(children)
    top_groups = [obj.name for obj in group_objects if obj.name not in child_groups]
    definitions_group.properties.extend(
        [
            _string_property("Label", "Component Definitions"),
            _link_list_property("Group", definition_objects),
            _bool_property("Visibility", False),
        ]
    )
    definitions_group.dependencies.extend(definition_objects)
    components_group.properties.extend(
        [
            _string_property("Label", "Components"),
            _link_list_property("Group", []),
            _string_list_property("ComponentObjects", occurrence_objects, dynamic=True),
            _bool_property("Visibility", True),
        ]
    )
    entities_group.properties.extend(
        [
            _string_property("Label", "Mate Entities"),
            _link_list_property("Group", entity_objects),
            _bool_property("Visibility", False),
        ]
    )
    entities_group.dependencies.extend(entity_objects)
    mate_children = [*top_groups, *grounded_objects, *mate_objects]
    mates_group.properties.extend(
        [
            _string_property("Label", "Joints"),
            _link_list_property("Group", mate_children),
            _bool_property("Visibility", False),
        ]
    )
    mates_group.dependencies.extend(mate_children)
    root_children = [
        mates_group.name,
        *occurrence_objects,
        *top_groups,
        *grounded_objects,
        *mate_objects,
    ]
    root.properties.extend(
        [
            _string_property("Label", root_label),
            _string_property("Type", "Assembly"),
            _link_list_property("Group", root_children),
            _placement_property("Placement", _matrix_transform(_IDENTITY_MATRIX)),
            _string_property("RootDefinitionId", root_definition_id, dynamic=True),
            _integer_property("DefinitionCount", len(definitions), dynamic=True),
            _integer_property("OccurrenceCount", len(direct_instances), dynamic=True),
            _integer_property("MateCount", len(mate_objects), dynamic=True),
            _bool_property("Visibility", True),
        ]
    )
    root.dependencies.extend(root_children)
    return root.name, len(direct_instances), len(mate_objects)


def _add_document_meshes(
    graph: _Graph,
    manifest: Mapping[str, Any],
    payload_entries: dict[str, bytes],
    parametric_target: str,
) -> list[str]:
    if _assembly_data(manifest) is not None:
        return []
    result: list[str] = []
    for index, mesh_source in enumerate(_items(manifest.get("meshes", []))):
        vertices, triangles = _tessellation_data(mesh_source)
        if not vertices or not triangles:
            continue
        requested = "DisplayMesh" if index == 0 else f"DisplayMesh_{index + 1}"
        brep_requested = "BRep" if index == 0 else f"BRep_{index + 1}"
        brep = graph.add("Part::Feature", brep_requested, "FacetedBRep")
        brep_filename = _unique_payload_name(payload_entries, f"{brep.name}.Shape.brp")
        payload_entries[brep_filename] = triangle_mesh_brep(vertices, triangles)
        brep.properties.extend(
            [
                _string_property(
                    "Label",
                    f"{mesh_source.get('name', mesh_source.get('id', requested))} BRep",
                ),
                _shape_property(brep_filename),
                _placement_property("Placement", _matrix_transform(_IDENTITY_MATRIX)),
                _string_property("KitMeshId", mesh_source.get("id", ""), dynamic=True),
                _string_property("Representation", "faceted", dynamic=True),
                _bool_property("Visibility", False),
            ]
        )
        mesh = graph.add("Mesh::Feature", requested, "DocumentMesh")
        filename = _unique_payload_name(payload_entries, f"{mesh.name}.MeshKernel.bms")
        payload_entries[filename] = _mesh_kernel_data(vertices, triangles)
        mesh.properties.extend(
            [
                _string_property(
                    "Label", mesh_source.get("name", mesh_source.get("id", requested))
                ),
                _mesh_property(filename),
                _placement_property("Placement", _matrix_transform(_IDENTITY_MATRIX)),
                _string_property("KitMeshId", mesh_source.get("id", ""), dynamic=True),
                _link_property("BRep", brep.name, dynamic=True),
                _bool_property("Visibility", True),
            ]
        )
        mesh.dependencies.append(brep.name)
        if parametric_target:
            brep.properties.append(
                _link_property("ParametricSource", parametric_target, dynamic=True)
            )
            brep.dependencies.append(parametric_target)
            mesh.properties.append(
                _link_property("ParametricSource", parametric_target, dynamic=True)
            )
            mesh.dependencies.append(parametric_target)
        result.append(brep.name)
    if result and parametric_target:
        target = next(
            (item for item in graph.objects if item.name == parametric_target), None
        )
        if target is not None:
            _replace_named_property(
                target.properties, "Visibility", _bool_property("Visibility", False)
            )
    return result


def _document_properties(
    label: str, document_id: str, document_timestamp: str
) -> ET.Element:
    properties = ET.Element("Properties", {"Count": "8", "TransientCount": "0"})
    properties.extend(
        [
            _string_property("Label", label),
            _string_property("Comment", "Kit by Parashell interchange document"),
            _string_property("CreatedBy", "Kit by Parashell"),
            _string_property("Id", document_id),
            _string_property("License", ""),
        ]
    )
    for name in ("CreationDate", "LastModifiedDate"):
        timestamp = _property(name, "App::PropertyString", status="16777217")
        ET.SubElement(timestamp, "String", {"value": document_timestamp})
        properties.append(timestamp)
    uid = _property("Uid", "App::PropertyUUID", status="16777217")
    ET.SubElement(
        uid, "Uuid", {"value": str(uuid.uuid5(uuid.NAMESPACE_URL, document_id))}
    )
    properties.append(uid)
    return properties


def _serialize_object_data(parent: ET.Element, obj: _Object) -> None:
    attributes = {"name": obj.name}
    if obj.extensions:
        attributes["Extensions"] = "True"
    element = ET.SubElement(parent, "Object", attributes)
    if obj.extensions:
        extensions = ET.SubElement(
            element, "Extensions", {"Count": str(len(obj.extensions))}
        )
        for extension in obj.extensions:
            ET.SubElement(
                extensions,
                "Extension",
                {"type": extension, "name": extension.rsplit("::", 1)[-1]},
            )
    properties = ET.SubElement(
        element,
        "Properties",
        {"Count": str(len(obj.properties)), "TransientCount": "0"},
    )
    properties.extend(obj.properties)


def _document_xml(
    manifest: Mapping[str, Any],
    manifest_data: str,
    manifest_sha256: str,
    external_links: Mapping[str, Mapping[str, Any]] | None = None,
    document_timestamp: str = "1980-01-01T00:00:00Z",
) -> tuple[bytes, dict[str, bytes]]:
    external_links = external_links or {}
    graph = _Graph()
    parameters_data = _items(manifest.get("parameters", []))
    parameters = _Parameters(parameters_data)
    parameter_sheet = graph.add("Spreadsheet::Sheet", "Parameters", "Parameters")
    parameter_sheet.properties.extend(parameters.sheet_properties())
    metadata = graph.add("App::FeaturePython", "KitMetadata", "Metadata")
    metadata.properties.extend(
        [
            _string_property("Label", "Kit Metadata"),
            _string_property(
                MANIFEST_ENCODING_PROPERTY, MANIFEST_ENCODING, dynamic=True
            ),
            _string_property(MANIFEST_SHA256_PROPERTY, manifest_sha256, dynamic=True),
            _string_property(MANIFEST_DATA_PROPERTY, manifest_data, dynamic=True),
            _string_property(
                "SchemaVersion", manifest.get("schema_version", "1.0"), dynamic=True
            ),
            _json_property("ParameterAliasesJSON", parameters.aliases),
            _bool_property("Visibility", False),
        ]
    )
    planes_group = graph.add("App::DocumentObjectGroup", "SupportPlanes", "Group")
    sketches_group = graph.add("App::DocumentObjectGroup", "Sketches", "Group")
    timeline_group = graph.add("App::DocumentObjectGroup", "FeatureTimeline", "Group")
    bodies_group = graph.add("App::DocumentObjectGroup", "Bodies", "Group")
    plane_items = _items(manifest.get("support_planes", manifest.get("planes", [])))
    plane_by_id = {_text(item.get("id")): item for item in plane_items}
    plane_names: dict[str, str] = {}
    plane_objects: list[str] = []
    for plane in plane_items:
        plane_id = _text(plane.get("id"))
        obj = graph.add("App::FeaturePython", plane.get("name", plane_id), "Plane")
        plane_names[plane_id] = obj.name
        plane_objects.append(obj.name)
        transform = (
            plane.get("transform", {})
            if isinstance(plane.get("transform"), Mapping)
            else {}
        )
        expressions: list[tuple[str, str]] = []
        offset_parameter_id = _text(plane.get("offset_parameter_id"))
        if offset_parameter_id:
            expression = parameters.expression(offset_parameter_id)
            origin = _vector(transform.get("origin"), (0.0, 0.0, 0.0))
            normal = _normalize(_vector(transform.get("z_axis"), (0.0, 0.0, 1.0)))
            value = parameters.value(offset_parameter_id)
            for coordinate, component, origin_value in zip(
                ("x", "y", "z"), normal, origin
            ):
                if abs(component) > 0.999999 and math.isclose(
                    abs(origin_value), abs(value), rel_tol=1e-9, abs_tol=1e-9
                ):
                    sign = "-" if origin_value * value < 0 else ""
                    expressions.append(
                        (f"Placement.Base.{coordinate}", sign + _text(expression))
                    )
        obj.properties.extend(
            [
                _string_property("Label", plane.get("name", plane_id)),
                _placement_property("Placement", transform, dynamic=True),
                _expression_property(expressions),
                _string_property("KitId", plane_id, dynamic=True),
                _json_property("SourcePlaneJSON", plane),
                _bool_property("Visibility", False),
            ]
        )
        if expressions:
            obj.dependencies.append(parameter_sheet.name)
    sketch_items = _items(manifest.get("sketches", []))
    sketch_names: dict[str, str] = {}
    sketch_objects: list[str] = []
    for sketch in sketch_items:
        sketch_id = _text(sketch.get("id"))
        plane_id = _text(sketch.get("support_plane_id"))
        plane = plane_by_id.get(plane_id, {"transform": {}})
        plane_name = plane_names.get(plane_id, "")
        obj = graph.add(
            "Sketcher::SketchObject",
            sketch.get("name", sketch_id),
            "Sketch",
            touched=True,
            extensions=("Part::AttachExtension",),
        )
        sketch_names[sketch_id] = obj.name
        sketch_objects.append(obj.name)
        properties, dependencies = _sketch_properties(
            sketch, plane, plane_name, parameters
        )
        obj.properties.extend(properties)
        obj.dependencies.extend(dependency for dependency in dependencies if dependency)
    selection_items = {
        _text(item.get("id")): item for item in _items(manifest.get("selections", []))
    }
    feature_items = sorted(
        _items(manifest.get("feature_timeline", manifest.get("timeline", []))),
        key=lambda item: int(_number(item.get("order"))),
    )
    feature_names: dict[str, str] = {}
    solid_feature_names: dict[str, str] = {}
    feature_objects: list[str] = []
    current_name = ""
    final_shape_filename = ""
    payload_entries: dict[str, bytes] = {}
    for feature in feature_items:
        if bool(feature.get("suppressed")):
            continue
        feature_id = _text(feature.get("id"))
        feature_name = _text(feature.get("name"), feature_id)
        kind = _text(_enum(feature.get("kind"))).lower()
        operation = _text(_enum(feature.get("operation"))).lower()
        attributes = (
            feature.get("attributes", {})
            if isinstance(feature.get("attributes"), Mapping)
            else {}
        )
        definition = (
            feature.get("definition", {})
            if isinstance(feature.get("definition"), Mapping)
            else {}
        )
        inputs = [
            _text(value) for value in _sequence(feature.get("input_feature_ids", []))
        ]
        base_name = next(
            (
                solid_feature_names[value]
                for value in reversed(inputs)
                if value in solid_feature_names
            ),
            current_name,
        )
        if kind == "extrusion":
            sketch_id = _text(feature.get("sketch_id"))
            sketch_name = sketch_names.get(sketch_id, "")
            plane_id = _text(
                next(
                    (
                        item.get("support_plane_id")
                        for item in sketch_items
                        if _text(item.get("id")) == sketch_id
                    ),
                    "",
                )
            )
            plane = plane_by_id.get(plane_id, {})
            transform = (
                plane.get("transform", {})
                if isinstance(plane.get("transform"), Mapping)
                else {}
            )
            normal = _normalize(_vector(transform.get("z_axis"), (0.0, 0.0, 1.0)))
            reversed_direction = bool(
                definition.get(
                    "reversed",
                    _number(
                        attributes.get("direction_multiplier"),
                        -1.0 if operation == "cut" else 1.0,
                    )
                    < 0,
                )
            )
            explicit_direction = definition.get("direction")
            direction = (
                _normalize(_vector(explicit_direction, normal))
                if explicit_direction is not None
                else tuple(
                    component * (-1.0 if reversed_direction else 1.0)
                    for component in normal
                )
            )
            length = abs(
                _number(
                    definition.get("length"),
                    _number(attributes.get("length_mm")),
                )
            )
            second_length = abs(_number(definition.get("second_length")))
            symmetric = bool(definition.get("symmetric"))
            parameter_id = _feature_parameter(feature, parameters, length)
            expression = parameters.expression(parameter_id)
            tool_requested = (
                feature_name
                if not base_name and operation in {"", "create", "join"}
                else f"{feature_name}_Profile"
            )
            tool = graph.add(
                "Part::Extrusion", tool_requested, "Extrusion", touched=True
            )
            tool.properties.extend(
                [
                    _string_property(
                        "Label",
                        (
                            feature_name
                            if tool_requested == feature_name
                            else f"{feature_name} profile extrusion"
                        ),
                    ),
                    _link_property("Base", sketch_name),
                    _vector_property("Dir", direction),
                    _enumeration_property("DirMode", 0),
                    _float_property("LengthFwd", length, "App::PropertyDistance"),
                    _float_property(
                        "LengthRev", second_length, "App::PropertyDistance"
                    ),
                    _bool_property("Solid", True),
                    _bool_property("Reversed", False),
                    _bool_property("Symmetric", symmetric),
                    _string_property(
                        "EndCondition",
                        _text(_enum(definition.get("end_condition")), "blind"),
                        dynamic=True,
                    ),
                    _expression_property(
                        [("LengthFwd", expression)] if expression else []
                    ),
                    _shape_property(),
                    *_feature_metadata(
                        feature, "profile-extrusion" if base_name else "feature"
                    ),
                    _bool_property("Visibility", not base_name),
                ]
            )
            tool.dependencies.append(sketch_name)
            if expression:
                tool.dependencies.append(parameter_sheet.name)
            if not base_name:
                final = tool
            elif operation == "cut":
                final = graph.add("Part::Cut", feature_name, "Cut", touched=True)
                final.properties.extend(
                    [
                        _string_property("Label", feature_name),
                        _link_property("Base", base_name),
                        _link_property("Tool", tool.name),
                        _bool_property("Refine", True),
                        _expression_property([]),
                        _shape_property(),
                        *_feature_metadata(feature, "feature"),
                        _bool_property("Visibility", True),
                    ]
                )
                final.dependencies.extend([base_name, tool.name])
                tool.properties[-1] = _bool_property("Visibility", False)
            elif operation in {"join", "create", ""}:
                final = graph.add("Part::MultiFuse", feature_name, "Fuse", touched=True)
                final.properties.extend(
                    [
                        _string_property("Label", feature_name),
                        _link_list_property("Shapes", [base_name, tool.name]),
                        _bool_property("Refine", True),
                        _expression_property([]),
                        _shape_property(),
                        *_feature_metadata(feature, "feature"),
                        _bool_property("Visibility", True),
                    ]
                )
                final.dependencies.extend([base_name, tool.name])
                tool.properties[-1] = _bool_property("Visibility", False)
            else:
                final = tool
            feature_names[feature_id] = final.name
            solid_feature_names[feature_id] = final.name
            feature_objects.append(final.name)
            current_name = final.name
        elif kind == "fillet" and base_name:
            radius = abs(
                _number(
                    definition.get("radius"),
                    _number(attributes.get("radius_mm")),
                )
            )
            parameter_id = _feature_parameter(feature, parameters, radius)
            expression = parameters.expression(parameter_id)
            edge_indices: list[int] = []
            semantic_edge_indices: list[int] = []
            for key in (
                "selected_native_local_edge_ids",
                "native_local_edge_ids",
                "edge_ids",
                "edges",
            ):
                values = attributes.get(key, [])
                edge_indices.extend(
                    int(_number(value))
                    for value in _sequence(values)
                    if _number(value) > 0
                )
            for selection_id in _sequence(feature.get("selection_ids", [])):
                selection = selection_items.get(_text(selection_id), {})
                for path_item in _items(selection.get("path", [])):
                    subelement = _text(path_item.get("subelement"))
                    match = re.fullmatch(
                        r"(?:Edge|edge:)(\d+)", subelement, re.IGNORECASE
                    )
                    if match:
                        edge_indices.append(int(match.group(1)))
                query = (
                    selection.get("query", {})
                    if isinstance(selection.get("query"), Mapping)
                    else {}
                )
                if (
                    _text(query.get("topology_role"))
                    == "extrusion_terminal_profile_boundary"
                ):
                    semantic_edge_indices.append(3)
                for key in ("edge_index", "native_local_id", "index"):
                    if _number(query.get(key)) > 0:
                        edge_indices.append(int(_number(query.get(key))))
            if semantic_edge_indices:
                edge_indices = semantic_edge_indices
            edge_indices = list(dict.fromkeys(edge_indices)) or [1]
            final = graph.add("Part::Fillet", feature_name, "Fillet", touched=True)
            edge_filename = f"{final.name}.Edges"
            payload_entries[edge_filename] = _fillet_edges_data(edge_indices, radius)
            expressions = [("DrivingRadius", expression)] if expression else []
            final.properties.extend(
                [
                    _string_property("Label", feature_name),
                    _link_property("Base", base_name),
                    _fillet_edges_property(edge_filename),
                    _edge_link_property(base_name, edge_indices),
                    _expression_property(expressions),
                    _float_property(
                        "DrivingRadius", radius, "App::PropertyLength", dynamic=True
                    ),
                    _shape_property(),
                    *_feature_metadata(feature, "feature"),
                    _bool_property("Visibility", True),
                ]
            )
            final.dependencies.extend(
                [base_name] + ([parameter_sheet.name] if expression else [])
            )
            feature_names[feature_id] = final.name
            solid_feature_names[feature_id] = final.name
            feature_objects.append(final.name)
            current_name = final.name
        else:
            final = graph.add(
                "App::FeaturePython", feature_name, "Feature", touched=True
            )
            final.properties.extend(
                [
                    _string_property("Label", feature_name),
                    _expression_property([]),
                    *_feature_metadata(feature, "unsupported-native"),
                    _bool_property("Visibility", False),
                ]
            )
            if base_name:
                final.properties.append(
                    _link_property("InputFeature", base_name, dynamic=True)
                )
                final.dependencies.append(base_name)
            feature_names[feature_id] = final.name
            feature_objects.append(final.name)
    body_objects: list[str] = []
    for body in _items(manifest.get("bodies", [])):
        body_id = _text(body.get("id"))
        final_feature = feature_names.get(
            _text(body.get("final_feature_id")), current_name
        )
        obj = graph.add("App::DocumentObjectGroup", body.get("name", body_id), "Body")
        obj.properties.extend(
            [
                _string_property("Label", body.get("name", body_id)),
                _link_list_property("Group", [final_feature] if final_feature else []),
                _string_property("KitId", body_id, dynamic=True),
                _json_property("TopologyJSON", body.get("topology", {})),
                _json_property("SourceBodyJSON", body),
                _bool_property("Visibility", True),
            ]
        )
        if final_feature:
            obj.dependencies.append(final_feature)
        body_objects.append(obj.name)
    payloads = _items(
        manifest.get("brep_payloads", manifest.get("native_payloads", []))
    )
    for index, payload in enumerate(payloads, start=1):
        data = _payload_bytes(payload)
        if data is None:
            continue
        payload_id = _safe(payload.get("id", f"payload_{index}"), "payload")
        entry = str(
            PurePosixPath(
                "interchange", "native", payload_id + _payload_extension(payload)
            )
        )
        payload_entries[entry] = data
        format_id = _text(payload.get("format_id")).lower()
        attributes = (
            payload.get("attributes", {})
            if isinstance(payload.get("attributes"), Mapping)
            else {}
        )
        target_feature_id = _text(
            attributes.get("feature_id", attributes.get("final_feature_id"))
        )
        target_name = feature_names.get(target_feature_id, current_name)
        if target_name and (
            "brep" in format_id or "opencascade" in format_id or format_id == "occ"
        ):
            target = next(
                (item for item in graph.objects if item.name == target_name), None
            )
            if target is not None:
                shape_entry = f"{target.name}.Shape.brp"
                payload_entries[shape_entry] = data
                target.properties.append(_shape_property(shape_entry))
                final_shape_filename = shape_entry
    document_meshes = _add_document_meshes(
        graph, manifest, payload_entries, current_name
    )
    assembly_root, occurrence_count, mate_count = _add_assembly(
        graph, manifest, payload_entries, external_links
    )
    planes_group.properties.extend(
        [
            _string_property("Label", "Support Planes"),
            _link_list_property("Group", plane_objects),
            _bool_property("Visibility", False),
        ]
    )
    planes_group.dependencies.extend(plane_objects)
    sketches_group.properties.extend(
        [
            _string_property("Label", "Sketches"),
            _link_list_property("Group", sketch_objects),
            _bool_property("Visibility", False),
        ]
    )
    sketches_group.dependencies.extend(sketch_objects)
    timeline_group.properties.extend(
        [
            _string_property("Label", "Feature Timeline"),
            _link_list_property("Group", feature_objects),
            _bool_property("Visibility", True),
        ]
    )
    timeline_group.dependencies.extend(feature_objects)
    bodies_group.properties.extend(
        [
            _string_property("Label", "Bodies"),
            _link_list_property("Group", body_objects),
            _bool_property("Visibility", True),
        ]
    )
    bodies_group.dependencies.extend(body_objects)
    external_target = (
        document_meshes[0] if document_meshes else assembly_root or current_name
    )
    target_object = next(
        (item for item in graph.objects if item.name == external_target), None
    )
    if target_object is not None:
        target_object.properties.append(
            _link_property("Sketches", sketches_group.name, dynamic=True)
        )
        target_object.dependencies.append(sketches_group.name)
        if external_target not in feature_objects:
            target_object.properties.append(
                _link_property("FeatureTimeline", timeline_group.name, dynamic=True)
            )
            target_object.dependencies.append(timeline_group.name)
    metadata.properties.extend(
        [
            _string_property("FinalFeature", current_name, dynamic=True),
            _string_property(
                "ExternalLinkTarget",
                external_target,
                dynamic=True,
            ),
            _string_property("CachedShapeEntry", final_shape_filename, dynamic=True),
            _string_property("AssemblyRoot", assembly_root, dynamic=True),
            _integer_property(
                "AssemblyOccurrenceCount", occurrence_count, dynamic=True
            ),
            _integer_property("AssemblyMateCount", mate_count, dynamic=True),
            _string_list_property(
                "NativePayloadEntries", sorted(payload_entries), dynamic=True
            ),
        ]
    )
    source = (
        manifest.get("source", {})
        if isinstance(manifest.get("source"), Mapping)
        else {}
    )
    label = PurePosixPath(_text(source.get("path"), "Kit")).stem or "Kit"
    document_id = _text(source.get("sha256"), manifest_sha256)
    root = ET.Element(
        "Document",
        {"SchemaVersion": "4", "ProgramVersion": "1.0.2", "FileVersion": "1"},
    )
    root.append(_document_properties(label, document_id, document_timestamp))
    objects = ET.SubElement(
        root, "Objects", {"Count": str(len(graph.objects)), "Dependencies": "1"}
    )
    for obj in graph.objects:
        dependencies = [value for value in dict.fromkeys(obj.dependencies) if value]
        dependency = ET.SubElement(
            objects, "ObjectDeps", {"Name": obj.name, "Count": str(len(dependencies))}
        )
        for target in dependencies:
            ET.SubElement(dependency, "Dep", {"Name": target})
    for index, obj in enumerate(graph.objects, start=1):
        attributes = {"type": obj.type_id, "name": obj.name, "id": str(index)}
        if obj.touched:
            attributes["Touched"] = "1"
        ET.SubElement(objects, "Object", attributes)
    object_data = ET.SubElement(root, "ObjectData", {"Count": str(len(graph.objects))})
    for obj in graph.objects:
        _serialize_object_data(object_data, obj)
    ET.indent(root, space="  ")
    xml = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    return xml + b"\n", payload_entries


def _zip_entry(name: str, data: bytes) -> tuple[zipfile.ZipInfo, bytes]:
    info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o600 << 16
    info.create_system = 3
    return info, data


def build_fcstd_archive(
    manifest: Mapping[str, Any],
    external_links: Mapping[str, Mapping[str, Any]] | None = None,
    document_timestamp: str | None = None,
) -> bytes:
    canonical = json.dumps(
        manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    digest = hashlib.sha256(canonical).hexdigest()
    embedded = base64.b64encode(zlib.compress(canonical, 9)).decode("ascii")
    document_xml, payload_entries = _document_xml(
        manifest,
        embedded,
        digest,
        external_links,
        document_timestamp or "1980-01-01T00:00:00Z",
    )
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", allowZip64=True) as archive:
        for name, data in [
            _zip_entry("Document.xml", document_xml),
            _zip_entry(MANIFEST_ENTRY, canonical + b"\n"),
        ]:
            archive.writestr(name, data)
        for entry, data in sorted(payload_entries.items()):
            archive.writestr(*_zip_entry(entry, data))
    return output.getvalue()


def extract_manifest_from_fcstd(data: bytes) -> dict[str, Any]:
    try:
        archive = zipfile.ZipFile(io.BytesIO(data))
    except (zipfile.BadZipFile, OSError) as exc:
        raise ValueError("source is not an FCStd ZIP archive") from exc
    with archive:
        if MANIFEST_ENTRY in archive.namelist():
            value = json.loads(archive.read(MANIFEST_ENTRY).decode("utf-8"))
            if not isinstance(value, dict):
                raise ValueError("embedded Kit document is not a mapping")
            return value
        try:
            root = ET.fromstring(archive.read("Document.xml"))
        except (KeyError, ET.ParseError) as exc:
            raise ValueError("FCStd archive has no readable Document.xml") from exc
        encoded = ""
        digest = ""
        encoding = ""
        for property_element in root.findall(".//Property"):
            name = property_element.get("name")
            string = property_element.find("String")
            value = string.get("value", "") if string is not None else ""
            if name == MANIFEST_DATA_PROPERTY:
                encoded = value
            elif name == MANIFEST_SHA256_PROPERTY:
                digest = value
            elif name == MANIFEST_ENCODING_PROPERTY:
                encoding = value
        if not encoded or encoding != MANIFEST_ENCODING:
            raise ValueError("FCStd archive has no embedded Kit interchange document")
        try:
            canonical = zlib.decompress(base64.b64decode(encoded, validate=True))
        except (ValueError, zlib.error) as exc:
            raise ValueError("embedded Kit interchange document is corrupt") from exc
        if digest and hashlib.sha256(canonical).hexdigest() != digest:
            raise ValueError("embedded Kit interchange document hash mismatch")
        value = json.loads(canonical.decode("utf-8"))
        if not isinstance(value, dict):
            raise ValueError("embedded Kit document is not a mapping")
        return value
