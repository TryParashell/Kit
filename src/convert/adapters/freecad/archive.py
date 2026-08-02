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

from convert.opencascade import is_structurally_valid_ascii_brep
from interchange import CadDocument

from .brep import FreeCADBrepWriteError, brep_model_brep, triangle_mesh_brep
from .format import FORMAT_ID
from .protocol import (
    ASSEMBLY_CONNECTOR_PROPERTY_PREFIXES,
    ASSEMBLY_JOINT_GROUP_TYPE_ID,
    ASSEMBLY_LINK_TYPE_ID,
    ASSEMBLY_ROOT_TYPE_ID,
    APP_LINK_TYPE_ID,
    BOOLEAN_OPERATION_TYPE_BY_KIND,
    CIRCULAR_GEOMETRY_KINDS,
    CONSTRAINT_CODE_BY_KIND,
    CONSTRAINT_POINT_INDEX_BY_NAME,
    CREATE_OPERATION_NAMES,
    DIMENSIONAL_CONSTRAINT_CODES,
    FIXED_CONSTRAINT_KINDS,
    FREECAD_BREP_FORMAT_IDS,
    GEOMETRY_TYPE_IDS_BY_KIND,
    JOINT_GROUND_PROPERTY,
    JOINT_REFERENCE_INDEX_BY_PROPERTY,
    JOINT_RESERVED_LINK_PROPERTIES,
    JOINT_TYPE_BY_MATE_KIND,
    JOINT_TYPES,
    JOINT_TYPES_USING_DISTANCE,
    JOINT_TYPES_USING_SECOND_DISTANCE,
    MIDPOINT_REFERENCE_POINT_NAMES,
    NEUTRAL_GEOMETRY_TYPE_BY_KIND,
    NEUTRAL_GEOMETRY_TYPE_ID_BY_KIND,
    SKETCH_TYPE_ID,
    SPLINE_GEOMETRY_KINDS,
    SPLINE_CONTROL_TAGS,
    STRING_HASHER_TAGS,
)


MANIFEST_ENTRY = "interchange/document.json"
DOCUMENT_ENTRY = "Document.xml"
MANIFEST_DATA_PROPERTY = "KitManifestData"
MANIFEST_ENCODING_PROPERTY = "KitManifestEncoding"
MANIFEST_SHA256_PROPERTY = "KitManifestSHA256"
MANIFEST_ENCODING = "zlib+base64+utf-8"
_MAX_ENTRIES = 16384
_MAX_ENTRY_SIZE = 512 * 1024 * 1024
_MAX_TOTAL_SIZE = 1024 * 1024 * 1024
_MAX_DOCUMENT_SIZE = 512 * 1024 * 1024
_MAX_COMPRESSION_RATIO = 500
_MAX_EXTERNAL_FILES = 256
_MAX_MANIFEST_JSON_DEPTH = 256
_MAX_XML_DEPTH = 256
_MAX_XML_NODES = 2_000_000
_MIN_OBJECT_GRAPH_SCHEMA_VERSION = 2
_TARGET_SCHEMA_VERSION = "4"
_TARGET_PROGRAM_VERSION = "1.0.2"
_TARGET_FILE_VERSION = "1"


def _validated_entry_name(name: str) -> str:
    if not name or "\\" in name or "\x00" in name:
        raise ValueError("FCStd archive contains an unsafe entry name")
    if any(part in {"", ".", ".."} for part in name.split("/")):
        raise ValueError("FCStd archive contains an unsafe entry name")
    path = PurePosixPath(name)
    if path.is_absolute():
        raise ValueError("FCStd archive contains an unsafe entry name")
    if path.parts and ":" in path.parts[0]:
        raise ValueError("FCStd archive contains an unsafe entry name")
    return path.as_posix()


def _validated_object_name(name: str) -> str:
    if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name) is None:
        raise ValueError("FreeCAD object name is unsafe or invalid")
    return name


def _validated_archive_members(
    data: bytes,
) -> tuple[zipfile.ZipFile, dict[str, zipfile.ZipInfo]]:
    try:
        archive = zipfile.ZipFile(io.BytesIO(data))
    except (OSError, zipfile.BadZipFile) as exc:
        raise ValueError("source is not an FCStd ZIP archive") from exc
    infos = archive.infolist()
    if not infos or len(infos) > _MAX_ENTRIES:
        archive.close()
        raise ValueError("FCStd archive entry count is outside safe limits")
    members: dict[str, zipfile.ZipInfo] = {}
    total = 0
    try:
        for info in infos:
            name = _validated_entry_name(
                info.filename.rstrip("/") if info.is_dir() else info.filename
            )
            if name in members:
                raise ValueError("FCStd archive contains duplicate entries")
            members[name] = info
            if info.flag_bits & 0x1:
                raise ValueError("FCStd archive contains an encrypted entry")
            mode = (info.external_attr >> 16) & 0o170000
            if mode == 0o120000:
                raise ValueError("FCStd archive contains a symbolic link")
            if info.is_dir():
                continue
            if info.file_size < 0 or info.file_size > _MAX_ENTRY_SIZE:
                raise ValueError("FCStd archive entry exceeds safe limits")
            total += info.file_size
            if total > _MAX_TOTAL_SIZE:
                raise ValueError("FCStd archive exceeds safe limits")
            if info.file_size and info.compress_size <= 0:
                raise ValueError("FCStd archive has an invalid compressed entry")
            if (
                info.compress_size
                and info.file_size / info.compress_size > _MAX_COMPRESSION_RATIO
            ):
                raise ValueError("FCStd archive compression ratio is unsafe")
        document = members.get(DOCUMENT_ENTRY)
        if document is not None and document.file_size > _MAX_DOCUMENT_SIZE:
            raise ValueError("FCStd archive has no safe Document.xml")
    except BaseException:
        archive.close()
        raise
    return archive, members


def _validated_document_xml(
    archive: zipfile.ZipFile, members: Mapping[str, zipfile.ZipInfo]
) -> tuple[ET.Element, bytes]:
    document_info = members.get(DOCUMENT_ENTRY)
    if document_info is None or document_info.file_size > _MAX_DOCUMENT_SIZE:
        raise ValueError("FCStd archive has no safe Document.xml")
    try:
        document_xml = archive.read(document_info)
        root = ET.fromstring(document_xml)
    except (
        OSError,
        RuntimeError,
        NotImplementedError,
        ET.ParseError,
        zipfile.BadZipFile,
    ) as exc:
        raise ValueError("FCStd archive has no readable Document.xml") from exc
    if root.tag != "Document":
        raise ValueError("FreeCAD Document.xml has an invalid root")
    count = 0
    stack = [(root, 1)]
    while stack:
        node, depth = stack.pop()
        count += 1
        if count > _MAX_XML_NODES:
            raise ValueError("FreeCAD Document.xml node count exceeds safe limits")
        if depth > _MAX_XML_DEPTH:
            raise ValueError("FreeCAD Document.xml nesting exceeds safe limits")
        stack.extend((child, depth + 1) for child in node)
    try:
        schema_version = int(root.get("SchemaVersion", ""))
    except ValueError as exc:
        raise ValueError("FreeCAD Document.xml schema version is invalid") from exc
    if schema_version < _MIN_OBJECT_GRAPH_SCHEMA_VERSION:
        raise ValueError("FreeCAD Document.xml schema version is not supported")

    def stored_count(
        node: ET.Element, names: tuple[str, ...], actual: int, label: str
    ) -> None:
        value = next(
            (node.get(name) for name in names if node.get(name) is not None), None
        )
        if value is None:
            return
        try:
            expected = int(value)
        except ValueError as exc:
            raise ValueError(f"FreeCAD {label} count is invalid") from exc
        if expected != actual:
            raise ValueError(f"FreeCAD {label} count does not match its data")

    if schema_version == 2:
        features_node = root.find("./Features")
        feature_data_node = root.find("./FeatureData")
        if features_node is None or feature_data_node is None:
            raise ValueError("FreeCAD Document.xml has no object graph")
        features = features_node.findall("./Feature")
        feature_data = feature_data_node.findall("./Feature")
        stored_count(features_node, ("Count", "count"), len(features), "feature")
        stored_count(
            feature_data_node,
            ("Count", "count"),
            len(feature_data),
            "feature data",
        )
        objects_node = ET.Element(
            "Objects", {"Count": str(len(features)), "Dependencies": "0"}
        )
        data_node = ET.Element("ObjectData", {"Count": str(len(feature_data))})
        for index, feature in enumerate(features, start=1):
            ET.SubElement(
                objects_node,
                "Object",
                {
                    "type": feature.get("type", ""),
                    "name": feature.get("name", ""),
                    "id": str(index),
                },
            )
        for feature in feature_data:
            item = ET.SubElement(data_node, "Object", {"name": feature.get("name", "")})
            item.extend(copy.deepcopy(list(feature)))
        root.append(objects_node)
        root.append(data_node)
    else:
        objects_node = root.find("./Objects")
        data_node = root.find("./ObjectData")
    if objects_node is None or data_node is None:
        raise ValueError("FreeCAD Document.xml has no object graph")
    declarations = objects_node.findall("./Object")
    object_data = data_node.findall("./Object")

    stored_count(objects_node, ("Count", "count"), len(declarations), "object")
    stored_count(data_node, ("Count", "count"), len(object_data), "object data")
    declared_names: set[str] = set()
    object_ids: set[str] = set()
    for declaration in declarations:
        name = declaration.get("name", "")
        type_id = declaration.get("type", "")
        object_id = declaration.get("id", "")
        if not name or not type_id or name in declared_names:
            raise ValueError("FreeCAD object declarations are malformed")
        _validated_object_name(name)
        if object_id and object_id in object_ids:
            raise ValueError("FreeCAD object declarations contain duplicate ids")
        declared_names.add(name)
        if object_id:
            object_ids.add(object_id)
    data_names: set[str] = set()
    for object_element in object_data:
        name = object_element.get("name", "")
        if not name or name in data_names:
            raise ValueError("FreeCAD object data contains duplicate names")
        data_names.add(name)
        properties = object_element.find("./Properties")
        if properties is None:
            raise ValueError(f"FreeCAD object {name!r} has no properties")
        stored_count(
            properties,
            ("Count", "count"),
            len(properties.findall("./Property")),
            "property",
        )
        stored_count(
            properties,
            ("TransientCount",),
            len(properties.findall("./_Property")),
            "transient property",
        )
    if declared_names != data_names:
        raise ValueError("FreeCAD object declarations and data do not match")
    dependency_names: set[str] = set()
    for dependency in objects_node.findall("./ObjectDeps"):
        name = dependency.get("Name", "")
        values = [item.get("Name", "") for item in dependency.findall("./Dep")]
        if not name or name in dependency_names or name not in declared_names:
            raise ValueError("FreeCAD dependency graph is malformed")
        if any(not value or value not in declared_names for value in values):
            raise ValueError("FreeCAD dependency graph has missing objects")
        stored_count(dependency, ("Count", "count"), len(values), "dependency")
        dependency_names.add(name)
    referenced: set[str] = set()
    for node in root.findall(".//*[@file]"):
        if node.tag == "XLink":
            continue
        filename = node.get("file", "")
        if filename:
            referenced.add(_validated_entry_name(filename))
    missing = sorted(referenced.difference(members))
    if missing:
        raise ValueError(
            "FCStd archive is missing referenced data: " + ", ".join(missing)
        )
    return root, document_xml


def _manifest_mapping(raw: bytes) -> dict[str, Any]:
    try:
        value = json.loads(raw)
    except RecursionError as exc:
        raise ValueError(
            "embedded Kit interchange document JSON nesting exceeds safe limits"
        ) from exc
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("embedded Kit interchange document is corrupt") from exc
    if not isinstance(value, dict):
        raise ValueError("embedded Kit document is not a mapping")
    stack = [(iter((value,)), 0)]
    while stack:
        values, parent_depth = stack[-1]
        try:
            item = next(values)
        except StopIteration:
            stack.pop()
            continue
        if isinstance(item, dict):
            depth = parent_depth + 1
            if depth > _MAX_MANIFEST_JSON_DEPTH:
                raise ValueError(
                    "embedded Kit interchange document JSON nesting exceeds safe limits"
                )
            stack.append((iter(item.values()), depth))
        elif isinstance(item, list):
            depth = parent_depth + 1
            if depth > _MAX_MANIFEST_JSON_DEPTH:
                raise ValueError(
                    "embedded Kit interchange document JSON nesting exceeds safe limits"
                )
            stack.append((iter(item), depth))
    return value


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


def _link_sub_list_property(
    name: str,
    targets: list[tuple[str, str]],
    *,
    dynamic: bool = False,
) -> ET.Element:
    result = _property(name, "App::PropertyLinkSubList", dynamic=dynamic)
    child = ET.SubElement(result, "LinkSubList", {"count": str(len(targets))})
    for target, subelement in targets:
        ET.SubElement(
            child,
            "Link",
            {"obj": target, "sub": subelement},
        )
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
    object_id: str = ""
    properties: list[ET.Element] = field(default_factory=list)
    transient_properties: list[ET.Element] = field(default_factory=list)
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

    def has_source_expression(self, parameter_id: str) -> bool:
        parameter = self.by_id.get(parameter_id, {})
        expression = (
            parameter.get("expression", {}) if isinstance(parameter, Mapping) else {}
        )
        return isinstance(expression, Mapping) and bool(_text(expression.get("source")))

    def source_path(self, parameter_id: str) -> str:
        parameter = self.by_id.get(parameter_id, {})
        attributes = (
            parameter.get("attributes", {}) if isinstance(parameter, Mapping) else {}
        )
        return (
            _text(attributes.get("freecad_path"))
            if isinstance(attributes, Mapping)
            else ""
        )

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

    def native_expression(self, item: Mapping[str, Any]) -> str | None:
        expression = item.get("expression", {})
        if not isinstance(expression, Mapping):
            return None
        source = _text(expression.get("source")).strip()
        if not source or "\n" in source or "\r" in source or ";" in source:
            return None
        language = _text(expression.get("language"), "kit").casefold()
        if language == "freecad":
            return source
        if language != "kit":
            return None
        references = [
            _text(value) for value in _sequence(expression.get("parameter_ids", []))
        ]
        translated = source
        allowed_identifiers = {
            "abs",
            "acos",
            "asin",
            "atan",
            "atan2",
            "ceil",
            "cos",
            "e",
            "exp",
            "false",
            "floor",
            "log",
            "log10",
            "max",
            "min",
            "pi",
            "pow",
            "round",
            "sin",
            "sqrt",
            "tan",
            "true",
        }
        for parameter_id in references:
            alias = self.aliases.get(parameter_id)
            if not alias:
                return None
            parameter = self.by_id.get(parameter_id, {})
            name = (
                _text(parameter.get("name")) if isinstance(parameter, Mapping) else ""
            )
            replaced = False
            for token in (parameter_id, name):
                if token and token in translated:
                    translated = translated.replace(token, alias)
                    replaced = True
            if not replaced and alias not in translated:
                return None
            allowed_identifiers.add(alias)
        translated = translated.replace("^", "**")
        identifiers = set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", translated))
        if identifiers - allowed_identifiers:
            return None
        if re.search(r"[^A-Za-z0-9_.,+\-*/%<>=!&|() \t]", translated):
            return None
        return translated

    def expression_parts(self) -> tuple[int, int]:
        native = 0
        carrier = 0
        for item in self.parameters:
            if not isinstance(item.get("expression"), Mapping):
                continue
            if self.native_expression(item) is None:
                carrier += 1
            else:
                native += 1
        return native, carrier

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
                content = "=true" if raw else "=false"
            elif isinstance(raw, (int, float)):
                content = "=" + (f"{raw:.17g}" if isinstance(raw, float) else str(raw))
                if unit:
                    content += f" {unit}"
            else:
                content = "'" + _text(raw)
            native_expression = self.native_expression(item)
            if native_expression is not None:
                content = "=" + native_expression
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


def native_expression_parts(manifest: Mapping[str, Any]) -> tuple[int, int]:
    return _Parameters(_items(manifest.get("parameters", []))).expression_parts()


def _element_from_data(value: Any) -> ET.Element | None:
    if not isinstance(value, Mapping):
        return None
    tag = value.get("tag")
    attributes = value.get("attributes", {})
    if not isinstance(tag, str) or not tag or not isinstance(attributes, Mapping):
        return None
    element = ET.Element(tag, {str(key): str(item) for key, item in attributes.items()})
    text = value.get("text")
    if isinstance(text, str):
        element.text = text
    children = value.get("children", [])
    if not isinstance(children, (list, tuple)):
        return None
    for child_data in children:
        child = _element_from_data(child_data)
        if child is None:
            return None
        element.append(child)
    return element


def _native_properties(value: Mapping[str, Any]) -> list[ET.Element]:
    properties = value.get("properties", {})
    if not isinstance(properties, Mapping):
        return []
    order = [
        _text(name)
        for name in _sequence(value.get("property_order", []))
        if _text(name) in properties
    ]
    order.extend(str(name) for name in properties if str(name) not in order)
    return [
        element
        for name in order
        if (element := _element_from_data(properties.get(name))) is not None
        and element.tag == "Property"
    ]


def _native_extensions(value: Mapping[str, Any]) -> tuple[str, ...]:
    return tuple(
        extension_type
        for item in _sequence(value.get("extensions", []))
        if (element := _element_from_data(item)) is not None
        and element.tag == "Extension"
        and (extension_type := _text(element.get("type")))
    )


def _native_link_property_name(value: Mapping[str, Any]) -> str:
    properties = value.get("properties", {})
    if not isinstance(properties, Mapping):
        return ""
    if "LinkedObject" in properties:
        return "LinkedObject"
    elements = {
        _text(name): element
        for name, item in properties.items()
        if (element := _element_from_data(item)) is not None
        and element.tag == "Property"
    }
    proxy = elements.get("Proxy")
    proxy_value = proxy.find("./Python") if proxy is not None else None
    marker = " ".join(
        (
            _text(value.get("type_id")),
            "" if proxy_value is None else proxy_value.get("class", ""),
            *_native_extensions(value),
        )
    ).casefold()
    if "link" not in marker:
        return ""
    candidates = [
        name
        for name, element in elements.items()
        if element.find("./XLink") is not None
        and name not in JOINT_RESERVED_LINK_PROPERTIES
    ]
    named = next(
        (name for name in candidates if "link" in name.casefold()),
        "",
    )
    return named or (candidates[0] if len(candidates) == 1 else "")


def _native_object(value: Mapping[str, Any]) -> _Object:
    name = _text(value.get("name"))
    type_id = _text(value.get("type_id"))
    if not name or not type_id:
        raise ValueError("native FreeCAD object metadata requires name and type_id")
    _validated_object_name(name)
    transient_properties = [
        element
        for item in _sequence(value.get("transient_properties", []))
        if (element := _element_from_data(item)) is not None
        and element.tag == "_Property"
    ]
    extensions = _native_extensions(value)
    return _Object(
        type_id,
        name,
        object_id=_text(value.get("object_id")),
        properties=_native_properties(value),
        transient_properties=transient_properties,
        dependencies=[
            _text(item)
            for item in _sequence(value.get("dependencies", []))
            if _text(item)
        ],
        touched=bool(value.get("touched")),
        extensions=extensions,
    )


def _merge_named_property(
    properties: list[ET.Element], replacement: ET.Element
) -> None:
    name = replacement.get("name")
    for current in properties:
        if current.get("name") == name:
            current[:] = [copy.deepcopy(child) for child in replacement]
            return
    properties.append(replacement)


def _native_geometry_element(entity: Mapping[str, Any]) -> ET.Element | None:
    kind = _text(_enum(entity.get("kind"))).lower()
    attributes = entity.get("attributes", {})
    geometry = entity.get("geometry", {})
    if not isinstance(geometry, Mapping):
        geometry = {}
    element = (
        _element_from_data(attributes.get("freecad"))
        if isinstance(attributes, Mapping)
        else None
    )
    native_geometry = _text(geometry.get("$type")) == "NativeGeometry" or all(
        key in geometry for key in ("format_id", "entity_type", "data")
    )
    if element is None and native_geometry:
        format_id = _text(geometry.get("format_id")).casefold()
        entity_type = _text(geometry.get("entity_type"))
        candidate = _element_from_data(geometry.get("data"))
        if (
            format_id == FORMAT_ID
            and candidate is not None
            and candidate.tag == "Geometry"
            and candidate.get("type", "") == entity_type
        ):
            element = candidate
    if element is None or element.tag != "Geometry":
        return None
    expected_type_ids = GEOMETRY_TYPE_IDS_BY_KIND.get(kind)
    if (
        expected_type_ids is not None
        and element.get("type", "") not in expected_type_ids
    ):
        return None
    if kind != "native" and expected_type_ids is None:
        return None
    if not native_geometry and kind == "line":
        value = element.find("./LineSegment")
        if value is not None:
            start = _point2(geometry.get("start"))
            end = _point2(geometry.get("end"))
            value.set("StartX", _fmt(start[0]))
            value.set("StartY", _fmt(start[1]))
            value.set("EndX", _fmt(end[0]))
            value.set("EndY", _fmt(end[1]))
    elif not native_geometry and kind in CIRCULAR_GEOMETRY_KINDS:
        value = element.find("./Circle" if kind == "circle" else "./ArcOfCircle")
        if value is not None:
            center = _point2(geometry.get("center"))
            value.set("CenterX", _fmt(center[0]))
            value.set("CenterY", _fmt(center[1]))
            value.set("Radius", _fmt(geometry.get("radius")))
            if kind == "arc":
                value.set("StartAngle", _fmt(geometry.get("start_angle")))
                value.set("EndAngle", _fmt(geometry.get("end_angle")))
    elif not native_geometry and kind == "point":
        value = element.find("./GeomPoint")
        if value is None:
            value = element.find("./Point")
        if value is not None:
            point = _point2(geometry.get("point"))
            value.set("X", _fmt(point[0]))
            value.set("Y", _fmt(point[1]))
    elif not native_geometry and kind == "ellipse":
        value = element.find("./Ellipse")
        if value is not None:
            center = _point2(geometry.get("center"))
            major_axis = _point2(geometry.get("major_axis"))
            value.set("CenterX", _fmt(center[0]))
            value.set("CenterY", _fmt(center[1]))
            if value.get("AngleXU") is not None:
                value.set("AngleXU", _fmt(math.atan2(major_axis[1], major_axis[0])))
            else:
                value.set("MajorAxisX", _fmt(major_axis[0]))
                value.set("MajorAxisY", _fmt(major_axis[1]))
            value.set("MajorRadius", _fmt(geometry.get("major_radius")))
            value.set("MinorRadius", _fmt(geometry.get("minor_radius")))
    elif not native_geometry and kind in SPLINE_GEOMETRY_KINDS:
        value = element.find("./BezierCurve" if kind == "bezier" else "./BSplineCurve")
        if value is not None:
            points = _items(geometry.get("control_points", []))
            weights = [
                _number(item, 1.0) for item in _sequence(geometry.get("weights", []))
            ]
            if len(weights) != len(points):
                weights = [1.0] * len(points)
            value[:] = [
                child for child in value if child.tag not in SPLINE_CONTROL_TAGS
            ]
            value.set("PolesCount", str(len(points)))
            for point, weight in zip(points, weights, strict=True):
                x, y = _point2(point)
                ET.SubElement(
                    value,
                    "Pole",
                    {
                        "X": _fmt(x),
                        "Y": _fmt(y),
                        "Z": _fmt(0),
                        "Weight": _fmt(weight),
                    },
                )
            if kind == "spline":
                degree = max(
                    1,
                    min(
                        int(_number(geometry.get("degree"), 3)),
                        max(1, len(points) - 1),
                    ),
                )
                knots = [_number(item) for item in _sequence(geometry.get("knots", []))]
                multiplicities = [
                    int(_number(item, 1))
                    for item in _sequence(geometry.get("multiplicities", []))
                ]
                if not knots or len(multiplicities) != len(knots):
                    interior_count = max(0, len(points) - degree - 1)
                    knots = [float(item) for item in range(interior_count + 2)]
                    multiplicities = [degree + 1] + [1] * interior_count + [degree + 1]
                value.set("KnotsCount", str(len(knots)))
                value.set("Degree", str(degree))
                value.set("IsPeriodic", "1" if bool(geometry.get("periodic")) else "0")
                for knot, multiplicity in zip(knots, multiplicities, strict=True):
                    ET.SubElement(
                        value,
                        "Knot",
                        {"Value": _fmt(knot), "Mult": str(multiplicity)},
                    )
    construction = element.find("./Construction")
    if construction is not None:
        construction.set("value", "1" if bool(entity.get("construction")) else "0")
    return element


def _geometry_property(
    sketch: Mapping[str, Any],
) -> tuple[ET.Element, dict[str, int], list[dict[str, Any]]]:
    entities = _items(sketch.get("entities", []))
    result = _property("Geometry", "Part::PropertyGeometryList", status="8192")
    geometry_list = ET.SubElement(result, "GeometryList", {"count": "0"})
    indices: dict[str, int] = {}
    diagnostics: list[dict[str, Any]] = []
    for source_index, entity in enumerate(entities):
        entity_id = _text(entity.get("id"), str(source_index))
        kind = _text(_enum(entity.get("kind"))).lower()
        native_item = _native_geometry_element(entity)
        if native_item is not None:
            indices[entity_id] = len(geometry_list)
            geometry_list.append(native_item)
            continue
        geometry = entity.get("geometry", {})
        if not isinstance(geometry, Mapping):
            geometry = {}
        geometry_type = _text(geometry.get("$type"))
        expected_geometry_type = NEUTRAL_GEOMETRY_TYPE_BY_KIND.get(kind)
        type_id = NEUTRAL_GEOMETRY_TYPE_ID_BY_KIND.get(kind)
        if type_id is None or (
            geometry_type == "NativeGeometry"
            or (geometry_type and geometry_type != expected_geometry_type)
        ):
            carrier_reason = (
                "source_opaque"
                if geometry_type == "NativeGeometry"
                or (geometry_type and geometry_type != expected_geometry_type)
                else "writer_unimplemented"
            )
            diagnostics.append(
                {
                    "carrier_reason": carrier_reason,
                    "code": "freecad.sketch_geometry_carrier_only",
                    "entity_id": entity_id,
                    "kind": kind,
                    "mode": "carrier_only",
                    "reason": "native FreeCAD geometry data is unavailable",
                    "severity": "warning",
                }
            )
            continue
        index = len(geometry_list)
        indices[entity_id] = index
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
        elif kind in CIRCULAR_GEOMETRY_KINDS:
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
        elif kind == "ellipse":
            center = _point2(geometry.get("center"))
            major_axis = _point2(geometry.get("major_axis"))
            ET.SubElement(
                item,
                "Ellipse",
                {
                    "CenterX": _fmt(center[0]),
                    "CenterY": _fmt(center[1]),
                    "CenterZ": _fmt(0),
                    "NormalX": _fmt(0),
                    "NormalY": _fmt(0),
                    "NormalZ": _fmt(1),
                    "MajorRadius": _fmt(geometry.get("major_radius")),
                    "MinorRadius": _fmt(geometry.get("minor_radius")),
                    "AngleXU": _fmt(math.atan2(major_axis[1], major_axis[0])),
                },
            )
        elif kind in SPLINE_GEOMETRY_KINDS:
            points = _items(geometry.get("control_points", []))
            weights = [
                _number(value, 1.0) for value in _sequence(geometry.get("weights", []))
            ]
            if len(weights) != len(points):
                weights = [1.0] * len(points)
            if kind == "bezier":
                curve = ET.SubElement(
                    item, "BezierCurve", {"PolesCount": str(len(points))}
                )
            else:
                degree = max(
                    1,
                    min(
                        int(_number(geometry.get("degree"), 3)),
                        max(1, len(points) - 1),
                    ),
                )
                knots = [
                    _number(value) for value in _sequence(geometry.get("knots", []))
                ]
                multiplicities = [
                    int(_number(value, 1))
                    for value in _sequence(geometry.get("multiplicities", []))
                ]
                if not knots or len(multiplicities) != len(knots):
                    interior_count = max(0, len(points) - degree - 1)
                    knots = [float(value) for value in range(interior_count + 2)]
                    multiplicities = [degree + 1] + [1] * interior_count + [degree + 1]
                curve = ET.SubElement(
                    item,
                    "BSplineCurve",
                    {
                        "PolesCount": str(len(points)),
                        "KnotsCount": str(len(knots)),
                        "Degree": str(degree),
                        "IsPeriodic": ("1" if bool(geometry.get("periodic")) else "0"),
                    },
                )
            for point, weight in zip(points, weights, strict=True):
                x, y = _point2(point)
                ET.SubElement(
                    curve,
                    "Pole",
                    {
                        "X": _fmt(x),
                        "Y": _fmt(y),
                        "Z": _fmt(0),
                        "Weight": _fmt(weight),
                    },
                )
            if kind == "spline":
                for knot, multiplicity in zip(knots, multiplicities, strict=True):
                    ET.SubElement(
                        curve,
                        "Knot",
                        {"Value": _fmt(knot), "Mult": str(multiplicity)},
                    )
        elif kind == "point":
            point = _point2(geometry.get("point", geometry.get("center")))
            ET.SubElement(
                item,
                "GeomPoint",
                {"X": _fmt(point[0]), "Y": _fmt(point[1]), "Z": _fmt(0)},
            )
        ET.SubElement(item, "Construction", {"value": "1" if construction else "0"})
    geometry_list.set("count", str(len(geometry_list)))
    return result, indices, diagnostics


def _reference_point(value: Any) -> int:
    point = _text(value).lower()
    return CONSTRAINT_POINT_INDEX_BY_NAME.get(point, 0)


def _raw_constraint_slots(attributes: Mapping[str, Any]) -> list[tuple[int, int]]:
    element_ids = _text(attributes.get("ElementIds"))
    element_positions = _text(attributes.get("ElementPositions"))
    slots: list[tuple[int, int]] = []
    if element_ids and element_positions:
        ids = element_ids.split()
        positions = element_positions.split()
        if len(ids) == len(positions):
            slots = [
                (int(_number(entity_id, -2000)), int(_number(position)))
                for entity_id, position in zip(ids, positions, strict=True)
            ]
    for index, prefix in enumerate(("First", "Second", "Third")):
        if prefix not in attributes:
            continue
        while len(slots) <= index:
            slots.append((-2000, 0))
        slots[index] = (
            int(_number(attributes.get(prefix), -2000)),
            int(_number(attributes.get(prefix + "Pos"))),
        )
    return slots


def _midpoint_slots(
    constraint: Mapping[str, Any],
    indices: Mapping[str, int],
    entities: Mapping[str, Mapping[str, Any]],
) -> list[tuple[int, int]] | None:
    references = _items(constraint.get("references", []))
    if len(references) == 2:
        for line_reference, point_reference in (
            (references[0], references[1]),
            (references[1], references[0]),
        ):
            line_id = _text(line_reference.get("entity_id"))
            point_id = _text(point_reference.get("entity_id"))
            line = entities.get(line_id, {})
            point = entities.get(point_id, {})
            line_reference_point = _text(line_reference.get("point")).casefold()
            if (
                _text(_enum(line.get("kind"))).casefold() != "line"
                or line_reference_point not in MIDPOINT_REFERENCE_POINT_NAMES
                or line_id == point_id
                or line_id not in indices
                or point_id not in indices
            ):
                continue
            point_position = _reference_point(point_reference.get("point"))
            if (
                point_position == 0
                and _text(_enum(point.get("kind"))).casefold() == "point"
            ):
                point_position = 1
            if point_position:
                return [
                    (indices[line_id], 1),
                    (indices[line_id], 2),
                    (indices[point_id], point_position),
                ]
    if len(references) == 3:
        resolved = [
            (
                _text(reference.get("entity_id")),
                _reference_point(reference.get("point")),
            )
            for reference in references
        ]
        for line_id, line in entities.items():
            if (
                _text(_enum(line.get("kind"))).casefold() != "line"
                or line_id not in indices
            ):
                continue
            line_points = [
                point for entity_id, point in resolved if entity_id == line_id
            ]
            others = [
                (entity_id, point)
                for entity_id, point in resolved
                if entity_id != line_id
            ]
            if sorted(line_points) != [1, 2] or len(others) != 1:
                continue
            point_id, point_position = others[0]
            point = entities.get(point_id, {})
            if (
                point_position == 0
                and _text(_enum(point.get("kind"))).casefold() == "point"
            ):
                point_position = 1
            if point_id in indices and point_position:
                return [
                    (indices[line_id], 1),
                    (indices[line_id], 2),
                    (indices[point_id], point_position),
                ]
    return None


def _constraint_diagnostic(
    constraint: Mapping[str, Any],
    kind: str,
    code: str,
    mode: str,
    reason: str,
    severity: str,
    native_kind: str = "",
    carrier_reason: str = "",
) -> dict[str, Any]:
    result = {
        "code": code,
        "constraint_id": _text(constraint.get("id")),
        "kind": kind,
        "mode": mode,
        "reason": reason,
        "severity": severity,
    }
    if native_kind:
        result["native_kind"] = native_kind
    if carrier_reason:
        result["carrier_reason"] = carrier_reason
    return result


def _constraint_carrier_reason(
    constraint: Mapping[str, Any], native_constraint: bool
) -> str:
    kind = _text(_enum(constraint.get("kind"))).casefold()
    attributes = constraint.get("attributes", {})
    has_native_attributes = isinstance(attributes, Mapping) and any(
        _text(key).casefold().startswith("native_") for key in attributes
    )
    return (
        "source_opaque"
        if native_constraint or kind.startswith("native") or has_native_attributes
        else "writer_unimplemented"
    )


def _constraints_property(
    sketch: Mapping[str, Any], indices: Mapping[str, int], parameters: _Parameters
) -> tuple[
    ET.Element,
    list[tuple[str, str]],
    list[str],
    list[dict[str, Any]],
]:
    source_constraints = _items(sketch.get("constraints", []))
    entity_items = _items(sketch.get("entities", []))
    entities = {_text(entity.get("id")): entity for entity in entity_items}
    encoded: list[dict[str, Any]] = []
    expressions: list[tuple[str, str]] = []
    dependencies: list[str] = []
    diagnostics: list[dict[str, Any]] = []
    constraint_names: set[str] = set()
    fixed_entities: set[str] = set()
    for constraint in source_constraints:
        kind = _text(_enum(constraint.get("kind"))).lower()
        source_attributes = constraint.get("attributes", {})
        if not isinstance(source_attributes, Mapping):
            source_attributes = {}
        raw_attributes = source_attributes.get("freecad", {})
        if not isinstance(raw_attributes, Mapping):
            raw_attributes = {}
        source_code = source_attributes.get(
            "freecad_type_code", raw_attributes.get("Type")
        )
        native_constraint = source_code is not None or bool(raw_attributes)
        composition: tuple[str, str] | None = None
        if kind == "midpoint" and source_code is None:
            code = 14
            resolved = _midpoint_slots(constraint, indices, entities)
            if resolved is not None:
                composition = (
                    "Symmetric",
                    "encoded as symmetry between a line's endpoints and the referenced point",
                )
            else:
                diagnostics.append(
                    _constraint_diagnostic(
                        constraint,
                        kind,
                        "freecad.sketch_constraint_carrier_only",
                        "carrier_only",
                        "the midpoint relationship cannot be expressed as a sound FreeCAD symmetry constraint",
                        "warning",
                        carrier_reason=_constraint_carrier_reason(
                            constraint, native_constraint
                        ),
                    )
                )
                continue
        else:
            code = (
                int(_number(source_code, -1))
                if source_code is not None
                else CONSTRAINT_CODE_BY_KIND.get(kind)
            )
            resolved = None
        if code is None or code < 0:
            diagnostics.append(
                _constraint_diagnostic(
                    constraint,
                    kind,
                    "freecad.sketch_constraint_carrier_only",
                    "carrier_only",
                    "no equivalent FreeCAD constraint type is available",
                    "warning",
                    carrier_reason=_constraint_carrier_reason(
                        constraint, native_constraint
                    ),
                )
            )
            continue
        if resolved is None:
            source_slots = _items(source_attributes.get("freecad_reference_slots", []))
            slot_values: list[tuple[int, int, str]] = []
            if source_slots:
                slot_values = [
                    (
                        int(_number(slot.get("freecad_geometry_index"), -2000)),
                        int(_number(slot.get("freecad_point_index"))),
                        _text(slot.get("entity_id")),
                    )
                    for slot in source_slots
                ]
            elif raw_attributes:
                slot_values = [
                    (entity_index, point_index, "")
                    for entity_index, point_index in _raw_constraint_slots(
                        raw_attributes
                    )
                ]
            unresolved = False
            if slot_values:
                resolved = []
                for entity_index, point_index, entity_id in slot_values:
                    if entity_index < 0:
                        resolved.append((entity_index, point_index))
                        continue
                    target_id = entity_id
                    if not target_id and entity_index < len(entity_items):
                        target_id = _text(entity_items[entity_index].get("id"))
                    target_index = indices.get(target_id)
                    if target_index is None:
                        unresolved = True
                        break
                    resolved.append((target_index, point_index))
                if unresolved:
                    resolved = []
            else:
                references = _items(constraint.get("references", []))
                resolved = []
                for reference in references:
                    entity_id = _text(reference.get("entity_id"))
                    entity_index = indices.get(entity_id)
                    if entity_index is None:
                        unresolved = True
                        break
                    resolved.append(
                        (entity_index, _reference_point(reference.get("point")))
                    )
                if unresolved:
                    resolved = []
            if kind == "concentric" and not native_constraint:
                if len(resolved) == 2:
                    resolved = [(resolved[0][0], 3), (resolved[1][0], 3)]
                    composition = (
                        "Coincident",
                        "encoded as coincidence between the referenced curve centers",
                    )
                else:
                    resolved = []
            elif kind == "fixed" and not native_constraint:
                if len(resolved) == 1 and resolved[0][1] == 0:
                    composition = (
                        "Block",
                        "encoded using FreeCAD's block constraint",
                    )
                else:
                    resolved = []
        if not resolved:
            diagnostics.append(
                _constraint_diagnostic(
                    constraint,
                    kind,
                    "freecad.sketch_constraint_carrier_only",
                    "carrier_only",
                    "the constraint has no sound native reference encoding",
                    "warning",
                    carrier_reason=_constraint_carrier_reason(
                        constraint, native_constraint
                    ),
                )
            )
            continue
        parameter_id = _text(constraint.get("parameter_id"))
        value = parameters.value(
            parameter_id,
            _number(constraint.get("value"), _number(raw_attributes.get("Value"))),
        )
        elements = resolved + [(-2000, 0)] * max(0, 3 - len(resolved))
        values = elements[:3]
        if native_constraint and "Name" in raw_attributes:
            name = _text(raw_attributes.get("Name"))
        else:
            name_base = _safe(constraint.get("id"), "Constraint")
            name = name_base
            suffix = 2
            while name in constraint_names:
                name = f"{name_base}_{suffix}"
                suffix += 1
            constraint_names.add(name)
        if name:
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
                "elements": elements,
                "attributes": raw_attributes,
            }
        )
        if kind in FIXED_CONSTRAINT_KINDS:
            fixed_entities.update(
                _text(reference.get("entity_id"))
                for reference in _items(constraint.get("references", []))
            )
        if composition is not None:
            diagnostics.append(
                _constraint_diagnostic(
                    constraint,
                    kind,
                    "freecad.sketch_constraint_composed",
                    "native_composition",
                    composition[1],
                    "info",
                    composition[0],
                )
            )
        expression = (
            parameters.expression(parameter_id)
            if not native_constraint or parameters.has_source_expression(parameter_id)
            else None
        )
        if (
            expression
            and bool(constraint.get("driving", True))
            and code in DIMENSIONAL_CONSTRAINT_CODES
        ):
            source_path = parameters.source_path(parameter_id)
            path = (
                f".{source_path}"
                if native_constraint and source_path
                else f".Constraints.{name}"
            )
            expressions.append((path, expression))
            dependencies.append("Parameters")
    for entity in entity_items:
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
                    "elements": [(indices[entity_id], 0), (-2000, 0), (-2000, 0)],
                    "attributes": {},
                }
            )
    result = _property("Constraints", "Sketcher::PropertyConstraintList")
    constraint_list = ET.SubElement(
        result, "ConstraintList", {"count": str(len(encoded))}
    )
    for item in encoded:
        first, second, third = item["first"], item["second"], item["third"]
        elements = item["elements"]
        attributes = {str(key): str(value) for key, value in item["attributes"].items()}
        if not attributes:
            attributes.update(
                {
                    "MetaData": "",
                    "Orientation": "0",
                    "LabelDistance": _fmt(10),
                    "LabelPosition": _fmt(0),
                    "IsInVirtualSpace": "0",
                    "IsVisible": "1",
                }
            )
        attributes.update(
            {
                "Name": item["name"],
                "Type": str(item["type"]),
                "Value": _fmt(item["value"]),
                "IsDriving": "1" if item["driving"] else "0",
                "IsActive": "1" if item["active"] else "0",
                "First": str(first[0]),
                "FirstPos": str(first[1]),
                "Second": str(second[0]),
                "SecondPos": str(second[1]),
                "Third": str(third[0]),
                "ThirdPos": str(third[1]),
                "ElementIds": " ".join(str(value[0]) for value in elements),
                "ElementPositions": " ".join(str(value[1]) for value in elements),
            }
        )
        ET.SubElement(constraint_list, "Constrain", attributes)
    return result, expressions, dependencies, diagnostics


def _sketch_properties(
    sketch: Mapping[str, Any],
    plane: Mapping[str, Any],
    plane_name: str,
    parameters: _Parameters,
    preserve_native: bool = False,
) -> tuple[list[ET.Element], list[str]]:
    transform = (
        plane.get("transform", {})
        if isinstance(plane.get("transform"), Mapping)
        else {}
    )
    geometry, indices, geometry_diagnostics = _geometry_property(sketch)
    constraints, expressions, dependencies, constraint_diagnostics = (
        _constraints_property(sketch, indices, parameters)
    )
    sketch_diagnostics = [*geometry_diagnostics, *constraint_diagnostics]
    diagnostics_property = (
        _json_property("KitSketchDiagnosticsJSON", sketch_diagnostics)
        if sketch_diagnostics
        else None
    )
    sketch_attributes = sketch.get("attributes", {})
    native_object = (
        sketch_attributes.get("freecad", {})
        if isinstance(sketch_attributes, Mapping)
        else {}
    )
    native_properties = (
        native_object.get("properties", {})
        if isinstance(native_object, Mapping)
        else {}
    )
    if isinstance(native_properties, Mapping) and native_properties:
        properties = _native_properties(native_object)
        replacements = [
            _string_property("Label", sketch.get("name", sketch.get("id", "Sketch"))),
            geometry,
            constraints,
            _shape_property("", "InternalShape"),
            _shape_property(),
            _bool_property("Visibility", not bool(sketch.get("suppressed"))),
        ]
        if diagnostics_property is not None:
            replacements.append(diagnostics_property)
        if not preserve_native:
            replacements.insert(1, _placement_property("Placement", transform))
        for replacement in replacements:
            _merge_named_property(properties, replacement)
        attachment = next(
            (item for item in properties if item.get("name") == "AttachmentSupport"),
            None,
        )
        if attachment is not None and plane_name:
            for link in attachment.findall(".//Link"):
                link.set("obj", plane_name)
        dependencies = [plane_name]
        external = next(
            (item for item in properties if item.get("name") == "ExternalGeometry"),
            None,
        )
        if external is not None:
            dependencies.extend(
                target
                for link in external.findall(".//Link")
                if (target := _text(link.get("obj")))
            )
        if not preserve_native:
            properties.extend(
                [
                    _link_property("SupportPlane", plane_name, dynamic=True),
                    _string_property("KitId", sketch.get("id"), dynamic=True),
                    _json_property(
                        "ClosedProfilesJSON",
                        sketch.get("closed_profile_entity_ids", []),
                    ),
                    _json_property("SourceSketchJSON", sketch),
                ]
            )
        return properties, dependencies
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
        _link_sub_list_property(
            "AttachmentSupport",
            [(plane_name, "")] if plane_name else [],
        ),
        _link_property("SupportPlane", plane_name, dynamic=True),
        _string_property("KitId", sketch.get("id"), dynamic=True),
        _json_property(
            "ClosedProfilesJSON", sketch.get("closed_profile_entity_ids", [])
        ),
        _json_property("SourceSketchJSON", sketch),
        _bool_property("Visibility", False),
    ]
    if diagnostics_property is not None:
        properties.append(diagnostics_property)
    return properties, dependencies


def _native_sketch_analysis(
    manifest: Mapping[str, Any],
) -> tuple[tuple[int, int, frozenset[str]], ...]:
    parameters = _Parameters(_items(manifest.get("parameters", [])))
    result: list[tuple[int, int, frozenset[str]]] = []
    for sketch in _items(manifest.get("sketches", [])):
        geometry, indices, geometry_diagnostics = _geometry_property(sketch)
        constraints, _, _, constraint_diagnostics = _constraints_property(
            sketch, indices, parameters
        )
        diagnostics = (*geometry_diagnostics, *constraint_diagnostics)
        carrier_diagnostics = tuple(
            item for item in diagnostics if item.get("mode") == "carrier_only"
        )
        result.append(
            (
                1
                + len(geometry.findall("./GeometryList/Geometry"))
                + len(constraints.findall("./ConstraintList/Constrain")),
                len(carrier_diagnostics),
                frozenset(
                    _text(item.get("carrier_reason"), "writer_unimplemented")
                    for item in carrier_diagnostics
                ),
            )
        )
    return tuple(result)


def native_sketch_parts(manifest: Mapping[str, Any]) -> tuple[tuple[int, int], ...]:
    return tuple(
        (native, carrier) for native, carrier, _ in _native_sketch_analysis(manifest)
    )


def native_sketch_carrier_reasons(
    manifest: Mapping[str, Any],
) -> tuple[frozenset[str], ...]:
    return tuple(reasons for _, _, reasons in _native_sketch_analysis(manifest))


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
        _string_property("FeatureKind", _enum(feature.get("kind")), dynamic=True),
        _string_property("Operation", _enum(feature.get("operation")), dynamic=True),
        _integer_property("TimelineOrder", feature.get("order", 0), dynamic=True),
        _bool_property("Suppressed", bool(feature.get("suppressed")), dynamic=True),
        _json_property("SourceFeatureJSON", feature),
    ]


def _definition_property(name: str, value: Any) -> ET.Element | None:
    property_name = "Definition" + _safe(name, "Value")
    if isinstance(value, bool):
        return _bool_property(property_name, value, dynamic=True)
    if isinstance(value, int):
        return _integer_property(property_name, value, dynamic=True)
    if isinstance(value, float):
        return _float_property(property_name, value, dynamic=True)
    if isinstance(value, str):
        return _string_property(property_name, value, dynamic=True)
    if isinstance(value, Mapping):
        value_type = _text(value.get("$type"))
        if value_type == "ParameterValue":
            raw = value.get("value")
            kind = _text(_enum(value.get("kind"))).casefold()
            if isinstance(raw, bool):
                return _bool_property(property_name, raw, dynamic=True)
            if isinstance(raw, int) and kind == "integer":
                return _integer_property(property_name, raw, dynamic=True)
            if isinstance(raw, (int, float)):
                property_type = {
                    "angle": "App::PropertyAngle",
                    "length": "App::PropertyLength",
                }.get(kind, "App::PropertyFloat")
                return _float_property(
                    property_name,
                    raw,
                    property_type,
                    dynamic=True,
                )
            if isinstance(raw, str):
                return _string_property(property_name, raw, dynamic=True)
        keys = set(value)
        if {"x", "y", "z"} <= keys:
            return _vector_property(
                property_name,
                _vector(value, (0.0, 0.0, 0.0)),
                dynamic=True,
            )
    if isinstance(value, (list, tuple)) and all(
        isinstance(item, str) for item in value
    ):
        return _string_list_property(property_name, list(value), dynamic=True)
    return None


def _definition_properties(definition: Mapping[str, Any]) -> list[ET.Element]:
    result: list[ET.Element] = []
    for name, value in definition.items():
        if name in {"$type", "object_data"}:
            continue
        property_element = _definition_property(name, value)
        if property_element is not None:
            result.append(property_element)
    return result


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
    declared = _text(payload.get("file_extension"))
    if re.fullmatch(r"\.[A-Za-z0-9_]{1,16}", declared):
        return declared
    suffix = PurePosixPath(_text(payload.get("source_stream"))).suffix
    if re.fullmatch(r"\.[A-Za-z0-9_]{1,16}", suffix):
        return suffix
    return ".bin"


def _payload_role(payload: Mapping[str, Any]) -> str:
    return _text(_enum(payload.get("role"))).lower()


def _freecad_brep_payload(payload: Mapping[str, Any], data: bytes) -> bool:
    return _text(
        payload.get("format_id")
    ).casefold() in FREECAD_BREP_FORMAT_IDS and is_structurally_valid_ascii_brep(data)


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
        result.extend(
            struct.pack(
                "<IIIIII",
                *(value & 0xFFFFFFFF for value in (*triangle, *adjacent)),
            )
        )
    if vertices:
        minimum = tuple(min(vertex[index] for vertex in vertices) for index in range(3))
        maximum = tuple(max(vertex[index] for vertex in vertices) for index in range(3))
    else:
        minimum = maximum = (0.0, 0.0, 0.0)
    result.extend(
        struct.pack(
            "<ffffff",
            minimum[0],
            maximum[0],
            minimum[1],
            maximum[1],
            minimum[2],
            maximum[2],
        )
    )
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
    external_old = ""
    final_old = ""
    if metadata_node is not None:
        external = metadata_node.find(
            "./Properties/Property[@name='ExternalLinkTarget']/String"
        )
        external_old = external.get("value", "") if external is not None else ""
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
            properties=properties,
            dependencies=[
                names[value]
                for value in dependencies.get(old_name, [])
                if value in names
            ],
            touched=node.get("Touched") == "1",
            extensions=extensions,
        )
        graph.objects.append(imported_object)
        imported.append(imported_object.name)
    target = names.get(external_old, "") or names.get(final_old, "")
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


def _mate_joint_type(kind: Any) -> str | None:
    return JOINT_TYPE_BY_MATE_KIND.get(_text(_enum(kind)).lower())


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


def _grounded_joint(
    graph: _Graph,
    component: str,
    label: str,
    placement: tuple[float, ...],
    source: Mapping[str, Any] | None = None,
) -> _Object:
    source = source if isinstance(source, Mapping) else {}
    joint = graph.add(
        _text(source.get("type_id"), "App::FeaturePython"),
        source.get("name", f"Grounded_{label}"),
        "GroundedJoint",
        touched=bool(source.get("touched")),
        extensions=_native_extensions(source),
    )
    joint.properties.extend(_native_properties(source))
    object_to_ground = next(
        (
            item
            for item in joint.properties
            if item.get("name") == JOINT_GROUND_PROPERTY
        ),
        None,
    )
    if object_to_ground is None:
        object_to_ground = _property(JOINT_GROUND_PROPERTY, "App::PropertyLink")
        object_to_ground.attrib.update(
            {
                "group": "Ground",
                "doc": "The object to ground",
                "attr": "0",
                "ro": "0",
                "hide": "0",
                "status": "2097152",
            }
        )
        joint.properties.append(object_to_ground)
    link = object_to_ground.find("./Link")
    if link is None:
        link = ET.SubElement(object_to_ground, "Link")
    link.set("value", component)
    placement_property = next(
        (item for item in joint.properties if item.get("name") == "Placement"), None
    )
    if placement_property is None:
        placement_property = _property("Placement", "App::PropertyPlacement")
        placement_property.attrib.update(
            {
                "group": "Ground",
                "doc": "This is where the part is grounded.",
                "attr": "0",
                "ro": "0",
                "hide": "0",
                "status": "2097152",
            }
        )
        joint.properties.append(placement_property)
    placement_value = _placement_property(
        "Placement", _matrix_transform(placement)
    ).find("./PropertyPlacement")
    current_placement = placement_property.find("./PropertyPlacement")
    if current_placement is None:
        current_placement = ET.SubElement(placement_property, "PropertyPlacement")
    if placement_value is not None:
        current_placement.attrib.clear()
        current_placement.attrib.update(placement_value.attrib)
    if not joint.properties:
        raise ValueError("grounded joint properties could not be generated")
    if not any(item.get("name") == "ExpressionEngine" for item in joint.properties):
        joint.properties.insert(0, _expression_property([]))
    if not any(item.get("name") == "Label" for item in joint.properties):
        joint.properties.insert(
            1,
            _property("Label", "App::PropertyString", status="134217728"),
        )
        ET.SubElement(joint.properties[1], "String", {"value": "GroundedJoint"})
    if not any(item.get("name") == "Label2" for item in joint.properties):
        label2 = _property("Label2", "App::PropertyString", status="67108992")
        ET.SubElement(label2, "String", {"value": ""})
        joint.properties.append(label2)
    if not any(item.get("name") == "Proxy" for item in joint.properties):
        joint.properties.append(_python_proxy_property("JointObject", "GroundedJoint"))
    if not any(item.get("name") == "Visibility" for item in joint.properties):
        visibility = _property("Visibility", "App::PropertyBool", status="648")
        ET.SubElement(visibility, "Bool", {"value": "true"})
        joint.properties.append(visibility)
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
    parameters = _Parameters(_items(manifest.get("parameters", [])))
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
    assembly_attributes = assembly.get("attributes", {})
    native_root_source = (
        assembly_attributes.get("freecad", {})
        if isinstance(assembly_attributes, Mapping)
        else {}
    )
    if not isinstance(native_root_source, Mapping):
        native_root_source = {}
    group_items = sorted(
        (
            group
            for group in _items(assembly.get("mate_groups", assembly.get("groups", [])))
            if _text(group.get("owner_definition_id")) == root_definition_id
        ),
        key=lambda item: (int(_number(item.get("order"))), _text(item.get("id"))),
    )
    native_joint_group = next(
        (
            group
            for group in group_items
            if isinstance(group.get("attributes"), Mapping)
            and isinstance(group["attributes"].get("freecad"), Mapping)
        ),
        None,
    )
    native_joint_source = (
        native_joint_group["attributes"]["freecad"]
        if native_joint_group is not None
        else {}
    )
    root_extensions = _native_extensions(native_root_source)
    root = graph.add(
        _text(native_root_source.get("type_id"), ASSEMBLY_ROOT_TYPE_ID),
        native_root_source.get("name", root_label),
        "Assembly",
        touched=bool(native_root_source.get("touched")),
        extensions=root_extensions or ("App::OriginGroupExtension",),
    )
    root.properties.extend(_native_properties(native_root_source))
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
    joint_extensions = _native_extensions(native_joint_source)
    mates_group = graph.add(
        _text(native_joint_source.get("type_id"), ASSEMBLY_JOINT_GROUP_TYPE_ID),
        native_joint_source.get("name", f"{root_label}_Joints"),
        "Joints",
        touched=bool(native_joint_source.get("touched")),
        extensions=joint_extensions or ("App::GroupExtension",),
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
    occurrence_by_native_name: dict[str, str] = {}
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
        instance_attributes = instance.get("attributes", {})
        native_instance = (
            instance_attributes.get("freecad", {})
            if isinstance(instance_attributes, Mapping)
            else {}
        )
        native_instance_properties = native_instance.get("properties", {})
        native_link_fields = (
            {_text(name) for name in native_instance_properties if _text(name)}
            if isinstance(native_instance_properties, Mapping)
            else set()
        )
        native_link_property = _native_link_property_name(native_instance)
        has_native_link = bool(native_link_property)
        component_kind = _text(
            _enum(definitions_by_id.get(definition_id, {}).get("kind"))
        ).lower()
        is_assembly_link = external is not None and (
            {"Group", "Rigid"}.issubset(native_link_fields)
            or (not has_native_link and component_kind == "assembly")
        )
        component_type_id = (
            _text(native_instance.get("type_id"))
            if has_native_link and _text(native_instance.get("type_id"))
            else ASSEMBLY_LINK_TYPE_ID if is_assembly_link else APP_LINK_TYPE_ID
        )
        placement_matrix = _matrix_values(instance.get("transform", {}))
        component = graph.add(
            component_type_id,
            f"{label}_{'_'.join(path)}",
            "Component",
            touched=is_assembly_link,
            extensions=(
                _native_extensions(native_instance)
                or (
                    ("App::OriginGroupExtension",)
                    if is_assembly_link
                    else ("App::LinkExtension",)
                )
            ),
        )
        component.properties.extend(_native_properties(native_instance))
        if is_assembly_link:
            _add_assembly_origin(graph, component)
        if component_kind == "assembly" and not bool(instance.get("flexible")):
            rigid_subassembly_ids.add(instance_id)
        suppressed = bool(instance.get("suppressed"))
        hidden = bool(instance.get("hidden")) or suppressed
        fixed = bool(instance.get("fixed")) and not suppressed
        linked_object = (
            _xlink_property(
                native_link_property or "LinkedObject",
                _text(external.get("target")),
                file=_text(external.get("file")),
                stamp=_text(external.get("stamp")),
                status=None if is_assembly_link else "256",
            )
            if external is not None
            else _xlink_property(native_link_property or "LinkedObject", target)
        )
        placement = _placement_property(
            "Placement",
            _matrix_transform(placement_matrix),
            status=(
                "8388612"
                if is_assembly_link and fixed
                else "8388608" if is_assembly_link else "268" if fixed else "264"
            ),
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
                    "LinkPlacement",
                    _matrix_transform(placement_matrix),
                    status="260" if fixed else "256",
                ),
                _bool_property("LinkTransform", True),
                _vector_property("ScaleVector", _matrix_scale(placement_matrix)),
            ]
        )
        for property_element in (
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
            _bool_property("Flexible", bool(instance.get("flexible")), dynamic=True),
            _bool_property(
                "ExcludeFromBOM",
                bool(instance.get("exclude_from_bom")),
                dynamic=True,
            ),
            _json_property("InstanceDataJSON", instance),
            _bool_property("Visibility", not hidden),
        ):
            _replace_named_property(
                component.properties,
                property_element.get("name", ""),
                property_element,
            )
        if external is None and target:
            component.dependencies.append(target)
        occurrence_objects.append(component.name)
        occurrence_by_path[path] = component.name
        native_instance_name = _text(native_instance.get("name"))
        if native_instance_name:
            occurrence_by_native_name[native_instance_name] = component.name
        if is_assembly_link and external is not None:
            assembly_link_records.append((path, component, external))
        if fixed:
            grounded_source = (
                instance_attributes.get("grounded_joint", {})
                if isinstance(instance_attributes, Mapping)
                else {}
            )
            grounded = _grounded_joint(
                graph,
                component.name,
                label,
                placement_matrix,
                grounded_source,
            )
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
            if not target or not instance_id or not type_id:
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
            link_fields = {
                _text(field)
                for field in _sequence(record.get("link_fields", []))
                if _text(field)
            }
            is_assembly_link = {"Group", "Rigid"}.issubset(link_fields)
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
        mate_attributes = mate.get("attributes", {})
        if not isinstance(mate_attributes, Mapping):
            mate_attributes = {}
        native_mate = mate_attributes.get("freecad", {})
        if not isinstance(native_mate, Mapping):
            native_mate = {}
        native_references = _items(mate_attributes.get("references", []))
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
        reference_entity_ids: list[list[str]] = [[], []]
        for entity_id in entity_ids:
            entity = entity_by_id.get(entity_id, {})
            attributes = entity.get("attributes", {})
            property_name = (
                _text(attributes.get("reference_property"))
                if isinstance(attributes, Mapping)
                else ""
            )
            reference_index = JOINT_REFERENCE_INDEX_BY_PROPERTY.get(property_name)
            if reference_index is not None:
                reference_entity_ids[reference_index].append(entity_id)
        if not any(reference_entity_ids):
            for index, entity_id in enumerate(entity_ids[:2]):
                reference_entity_ids[index].append(entity_id)
        connector_targets: list[str] = []
        connector_subelements: list[list[str]] = []
        native_root_name = _text(native_root_source.get("name"))
        for index, grouped_ids in enumerate(reference_entity_ids):
            native_reference = (
                native_references[index] if index < len(native_references) else {}
            )
            if native_reference:
                source_target = _text(native_reference.get("name"))
                target = (
                    root.name
                    if source_target == native_root_name
                    else occurrence_by_native_name.get(source_target, source_target)
                )
                subelements = []
                for value in _sequence(native_reference.get("subelements", [])):
                    source_value = _text(value)
                    prefix, separator, suffix = source_value.partition(".")
                    mapped = occurrence_by_native_name.get(prefix, prefix)
                    subelements.append(f"{mapped}.{suffix}" if separator else mapped)
            else:
                target = connector_target(grouped_ids[0]) if grouped_ids else ""
                subelements = []
                for entity_id in grouped_ids:
                    entity = entity_by_id.get(entity_id, {})
                    values = _mate_subelements(entity)
                    if len(grouped_ids) == 1:
                        subelements.extend(values)
                    elif values:
                        subelements.append(values[0])
            connector_targets.append(target)
            connector_subelements.append(subelements)
        has_connector_pair = len(connector_targets) == 2 and all(connector_targets)
        resolved_joint_type = _mate_joint_type(mate.get("kind"))
        native_joint_supported = resolved_joint_type is not None
        native_mate_extensions = _native_extensions(native_mate)
        obj = graph.add(
            _text(native_mate.get("type_id"), "App::FeaturePython"),
            native_mate.get("name", mate_name),
            "Mate",
            touched=bool(native_mate.get("touched")),
            extensions=(
                native_mate_extensions
                or (
                    ("App::SuppressibleExtensionPython",)
                    if native_joint_supported
                    else ()
                )
            ),
        )
        connector_properties: list[ET.Element] = []
        for index in range(1, 3):
            grouped_ids = reference_entity_ids[index - 1]
            entity_id = grouped_ids[0] if grouped_ids else ""
            component_name = (
                connector_targets[index - 1] if index <= len(connector_targets) else ""
            )
            entity = entity_by_id.get(entity_id, {})
            subelements = connector_subelements[index - 1]
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
        metadata_properties = [
            _string_property("MateId", mate_id, dynamic=True),
            _string_list_property("OwnerOccurrencePath", [], dynamic=True),
            _string_property("MateType", _text(_enum(mate.get("kind"))), dynamic=True),
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
            _bool_property("Driving", bool(mate.get("driving", True)), dynamic=True),
            _json_property("MateValueJSON", mate.get("value")),
            _json_property("MateDataJSON", mate),
        ]
        if not native_joint_supported:
            obj.properties.extend(_native_properties(native_mate))
            for property_element in (
                _string_property("Label", mate_name),
                _bool_property("KitMateCarrier", True, dynamic=True),
                *metadata_properties,
                *connector_properties,
                _bool_property("Visibility", False),
            ):
                _replace_named_property(
                    obj.properties,
                    property_element.get("name", ""),
                    property_element,
                )
            obj.dependencies.extend(connector_targets)
            mate_objects.append(obj.name)
            mate_names[mate_id] = obj.name
            continue
        joint_type = resolved_joint_type
        numeric_value = _mate_value(mate.get("value"))
        parameter_values = {
            path: parameters.value(parameter_id)
            for parameter_id in (
                _text(value) for value in _sequence(mate.get("parameter_ids", []))
            )
            if (path := parameters.source_path(parameter_id))
        }
        angle_value = parameter_values.get(
            "Angle", numeric_value if joint_type == "Angle" else 0.0
        )
        distance_value = parameter_values.get(
            "Distance",
            numeric_value if joint_type in JOINT_TYPES_USING_DISTANCE else 0.0,
        )
        native_mate_properties = native_mate.get("properties", {})
        if isinstance(native_mate_properties, Mapping) and native_mate_properties:
            properties = [
                element
                for value in native_mate_properties.values()
                if (element := _element_from_data(value)) is not None
                and element.tag == "Property"
            ]
            replacements = [
                _string_property("Label", mate_name),
                _enumeration_choices_property(
                    "JointType", JOINT_TYPES, JOINT_TYPES.index(joint_type)
                ),
                _bool_property(
                    "Suppressed",
                    bool(mate.get("suppressed"))
                    or not has_connector_pair
                    or not native_joint_supported,
                ),
                _float_property(
                    "Angle",
                    angle_value,
                    "App::PropertyAngle",
                ),
                _float_property(
                    "Distance",
                    distance_value,
                    "App::PropertyLength",
                ),
                *[
                    item
                    for item in connector_properties
                    if item.get("name", "").startswith(
                        ASSEMBLY_CONNECTOR_PROPERTY_PREFIXES
                    )
                ],
            ]
            for property_name, property_type in (
                ("Distance2", "App::PropertyLength"),
                ("LengthMin", "App::PropertyLength"),
                ("LengthMax", "App::PropertyLength"),
                ("AngleMin", "App::PropertyAngle"),
                ("AngleMax", "App::PropertyAngle"),
            ):
                if property_name in parameter_values:
                    replacements.append(
                        _float_property(
                            property_name,
                            parameter_values[property_name],
                            property_type,
                        )
                    )
            for replacement in replacements:
                _merge_named_property(properties, replacement)
            properties.extend(metadata_properties)
        else:
            properties = [
                _string_property("Label", mate_name),
                *metadata_properties,
                _enumeration_choices_property(
                    "JointType",
                    JOINT_TYPES,
                    JOINT_TYPES.index(joint_type),
                    dynamic=True,
                ),
                _bool_property(
                    "Suppressed",
                    bool(mate.get("suppressed"))
                    or not has_connector_pair
                    or not native_joint_supported,
                ),
                _float_property(
                    "Angle",
                    angle_value,
                    "App::PropertyAngle",
                    dynamic=True,
                ),
                _float_property(
                    "Distance",
                    distance_value,
                    "App::PropertyLength",
                    dynamic=True,
                ),
                _float_property(
                    "Distance2",
                    (
                        parameter_values.get("Distance2", 0.0)
                        if joint_type in JOINT_TYPES_USING_SECOND_DISTANCE
                        else 0.0
                    ),
                    "App::PropertyLength",
                    dynamic=True,
                ),
                _float_property(
                    "LengthMin",
                    parameter_values.get("LengthMin", 0.0),
                    "App::PropertyLength",
                    dynamic=True,
                ),
                _float_property(
                    "LengthMax",
                    parameter_values.get("LengthMax", 0.0),
                    "App::PropertyLength",
                    dynamic=True,
                ),
                _float_property(
                    "AngleMin",
                    parameter_values.get("AngleMin", 0.0),
                    "App::PropertyAngle",
                    dynamic=True,
                ),
                _float_property(
                    "AngleMax",
                    parameter_values.get("AngleMax", 0.0),
                    "App::PropertyAngle",
                    dynamic=True,
                ),
                _bool_property(
                    "EnableLengthMin", "LengthMin" in parameter_values, dynamic=True
                ),
                _bool_property(
                    "EnableLengthMax", "LengthMax" in parameter_values, dynamic=True
                ),
                _bool_property(
                    "EnableAngleMin", "AngleMin" in parameter_values, dynamic=True
                ),
                _bool_property(
                    "EnableAngleMax", "AngleMax" in parameter_values, dynamic=True
                ),
                *connector_properties,
                _python_proxy_property("JointObject", "Joint"),
                _bool_property("Visibility", False),
            ]

        obj.properties.extend(properties)
        obj.dependencies.extend(connector_targets)
        mate_objects.append(obj.name)
        mate_names[mate_id] = obj.name
    group_items = [group for group in group_items if group is not native_joint_group]
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
    for group, obj in zip(group_items, group_objects):
        members = [
            mate_names[value]
            for value in (_text(item) for item in _sequence(group.get("mate_ids", [])))
            if value in mate_names
        ]
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
        children = nested
        obj.properties.extend(
            [
                _string_property("Label", group.get("name", group.get("id", ""))),
                _link_list_property("Group", children),
                _string_list_property("MateObjects", members, dynamic=True),
                _string_property("MateGroupId", group.get("id", ""), dynamic=True),
                _bool_property("Visibility", False),
            ]
        )
        obj.dependencies.extend(children)
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
    mate_children = [*grounded_objects, *mate_objects]
    mates_group.properties.extend(_native_properties(native_joint_source))
    group_property = next(
        (item for item in mates_group.properties if item.get("name") == "Group"), None
    )
    if group_property is None:
        group_property = _link_list_property("Group", mate_children)
        mates_group.properties.append(group_property)
    else:
        link_list = group_property.find("./LinkList")
        if link_list is None:
            link_list = ET.SubElement(group_property, "LinkList")
        link_list.clear()
        link_list.set("count", str(len(mate_children)))
        for target in mate_children:
            ET.SubElement(link_list, "Link", {"value": target})
    if not any(
        item.get("name") == "ExpressionEngine" for item in mates_group.properties
    ):
        mates_group.properties.insert(0, _expression_property([]))
    if not any(item.get("name") == "Label" for item in mates_group.properties):
        label_property = _property("Label", "App::PropertyString", status="134217728")
        ET.SubElement(label_property, "String", {"value": "Joints"})
        mates_group.properties.append(label_property)
    if not any(item.get("name") == "Label2" for item in mates_group.properties):
        label2_property = _property("Label2", "App::PropertyString", status="67108992")
        ET.SubElement(label2_property, "String", {"value": ""})
        mates_group.properties.append(label2_property)
    if not any(item.get("name") == "Visibility" for item in mates_group.properties):
        visibility_property = _property("Visibility", "App::PropertyBool", status="648")
        ET.SubElement(visibility_property, "Bool", {"value": "true"})
        mates_group.properties.append(visibility_property)
    mates_group.transient_properties.append(
        ET.Element(
            "_Property",
            {
                "name": "_GroupTouched",
                "type": "App::PropertyBool",
                "status": "100663424",
            },
        )
    )
    mates_group.dependencies.extend(mate_children)
    root_children = [
        mates_group.name,
        *occurrence_objects,
        *grounded_objects,
        *mate_objects,
    ]
    for property_element in (
        _string_property("Label", root_label),
        _string_property("Type", "Assembly"),
        _link_list_property("Group", root_children),
        _placement_property("Placement", _matrix_transform(_IDENTITY_MATRIX)),
        _string_property("RootDefinitionId", root_definition_id, dynamic=True),
        _integer_property("DefinitionCount", len(definitions), dynamic=True),
        _integer_property("OccurrenceCount", len(direct_instances), dynamic=True),
        _integer_property("MateCount", len(mate_objects), dynamic=True),
        _bool_property("Visibility", True),
    ):
        _replace_named_property(
            root.properties, property_element.get("name", ""), property_element
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


def _add_document_brep(
    graph: _Graph,
    manifest: Mapping[str, Any],
    payload_entries: dict[str, bytes],
    parametric_target: str,
) -> tuple[list[str], str]:
    if manifest.get("brep") is None:
        return [], ""
    try:
        document = CadDocument.from_dict(manifest)
    except (KeyError, TypeError, ValueError, RecursionError) as exc:
        raise ValueError("neutral B-rep manifest data is invalid") from exc
    if document.brep is None:
        return [], ""
    try:
        data = brep_model_brep(document.brep)
    except FreeCADBrepWriteError:
        return [], ""
    obj = graph.add("Part::Feature", "BRep", "NeutralBRep")
    filename = _unique_payload_name(payload_entries, f"{obj.name}.Shape.brp")
    payload_entries[filename] = data
    obj.properties.extend(
        [
            _string_property("Label", "Neutral BRep"),
            _shape_property(filename),
            _placement_property("Placement", _matrix_transform(_IDENTITY_MATRIX)),
            _string_property("Representation", "neutral-brep", dynamic=True),
            _string_property(
                "BRepSchemaVersion", document.brep.schema_version, dynamic=True
            ),
            _bool_property("Visibility", True),
        ]
    )
    if parametric_target:
        obj.properties.append(
            _link_property("ParametricSource", parametric_target, dynamic=True)
        )
        obj.dependencies.append(parametric_target)
    return [obj.name], filename


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
        {
            "Count": str(len(obj.properties)),
            "TransientCount": str(len(obj.transient_properties)),
        },
    )
    properties.extend(obj.transient_properties)
    properties.extend(obj.properties)


def _sanitize_payload_references(
    objects: list[_Object], payload_entries: Mapping[str, bytes]
) -> None:
    for obj in objects:
        for property_element in obj.properties:
            part = property_element.find("./Part")
            if part is not None:
                filename = part.get("file", "")
                if filename and filename not in payload_entries:
                    property_element[:] = [ET.Element("Part")]
                    continue
            stack = [property_element]
            while stack:
                parent = stack.pop()
                filename = parent.get("file", "")
                if parent.tag != "XLink" and filename not in payload_entries:
                    parent.attrib.pop("file", None)
                for child in list(parent):
                    filename = child.get("file", "")
                    if (
                        child.tag != "XLink"
                        and filename
                        and filename not in payload_entries
                    ):
                        parent.remove(child)
                    else:
                        stack.append(child)


def _represented_native_object_names(
    manifest: Mapping[str, Any], assembly: Mapping[str, Any]
) -> set[str]:
    result: set[str] = set()

    def visit(value: Any) -> None:
        if isinstance(value, Mapping):
            attributes = value.get("attributes", {})
            if isinstance(attributes, Mapping):
                for key in ("freecad", "grounded_joint"):
                    native = attributes.get(key, {})
                    if isinstance(native, Mapping):
                        name = _text(native.get("name"))
                        if name:
                            result.add(name)
            for child in value.values():
                visit(child)
        elif isinstance(value, (list, tuple)):
            for child in value:
                visit(child)

    visit(manifest)
    visit(assembly)
    return result


def _document_xml(
    manifest: Mapping[str, Any],
    manifest_data: str,
    manifest_sha256: str,
    external_links: Mapping[str, Mapping[str, Any]] | None = None,
    native_external_links: Mapping[str, str] | None = None,
    document_timestamp: str = "1980-01-01T00:00:00Z",
) -> tuple[bytes, dict[str, bytes]]:
    external_links = external_links or {}
    native_external_links = native_external_links or {}
    manifest_metadata = manifest.get("metadata", {})
    freecad_metadata = (
        manifest_metadata.get("freecad", {})
        if isinstance(manifest_metadata, Mapping)
        else {}
    )
    native_values = (
        _items(freecad_metadata.get("objects", []))
        if isinstance(freecad_metadata, Mapping)
        else []
    )
    assembly = _assembly_data(manifest)
    native_replay = bool(native_values) and assembly is None
    represented_native_names = (
        _represented_native_object_names(manifest, assembly)
        if assembly is not None
        else set()
    )
    replay_values = native_values
    if not native_replay:
        replay_values = [
            value
            for value in native_values
            if _text(value.get("name")) not in represented_native_names
        ]
        while True:
            replay_names = {_text(value.get("name")) for value in replay_values}
            closed_values = [
                value
                for value in replay_values
                if all(
                    _text(dependency) in replay_names
                    for dependency in _sequence(value.get("dependencies", []))
                )
            ]
            if len(closed_values) == len(replay_values):
                break
            replay_values = closed_values
    graph = _Graph()
    native_graph: dict[str, _Object] = {}
    if replay_values:
        for value in sorted(
            replay_values, key=lambda item: int(_number(item.get("order")))
        ):
            obj = _native_object(value)
            if obj.name in native_graph:
                raise ValueError(
                    f"duplicate native FreeCAD object metadata: {obj.name}"
                )
            native_graph[obj.name] = obj
            graph.names.add(obj.name)
            graph.objects.append(obj)
    native_object_targets = {name: obj.name for name, obj in native_graph.items()}
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
    selections_group = graph.add("App::DocumentObjectGroup", "Selections", "Group")
    configurations_group = graph.add(
        "App::DocumentObjectGroup", "Configurations", "Group"
    )
    timeline_group = graph.add("App::DocumentObjectGroup", "FeatureTimeline", "Group")
    bodies_group = graph.add("App::DocumentObjectGroup", "Bodies", "Group")
    plane_items = _items(manifest.get("support_planes", manifest.get("planes", [])))
    plane_by_id = {_text(item.get("id")): item for item in plane_items}
    plane_names: dict[str, str] = {}
    plane_objects: list[str] = []
    for plane in plane_items:
        plane_id = _text(plane.get("id"))
        plane_attributes = plane.get("attributes", {})
        native_plane = (
            plane_attributes.get("freecad", {})
            if isinstance(plane_attributes, Mapping)
            else {}
        )
        native_plane_name = _text(native_plane.get("name"))
        obj = native_graph.get(native_plane_name) if native_replay else None
        if obj is None:
            obj = graph.add(
                _text(native_plane.get("type_id"), "App::Plane"),
                native_plane.get("name", plane.get("name", plane_id)),
                "Plane",
            )
        if native_plane_name:
            native_object_targets[native_plane_name] = obj.name
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
        native_plane_properties = (
            native_plane.get("properties", {})
            if isinstance(native_plane, Mapping)
            else {}
        )
        if isinstance(native_plane_properties, Mapping) and native_plane_properties:
            properties = _native_properties(native_plane)
            replacements = [
                _string_property("Label", plane.get("name", plane_id)),
                _placement_property("Placement", transform),
                _bool_property("Visibility", False),
            ]
            for replacement in replacements:
                _merge_named_property(properties, replacement)
            if not native_replay:
                properties.extend(
                    [
                        _string_property("KitId", plane_id, dynamic=True),
                        _json_property("SourcePlaneJSON", plane),
                    ]
                )
            obj.properties = properties
        else:
            obj.properties.extend(
                [
                    _string_property("Label", plane.get("name", plane_id)),
                    _placement_property("Placement", transform),
                    _expression_property(expressions),
                    _string_property("KitId", plane_id, dynamic=True),
                    _json_property("SourcePlaneJSON", plane),
                    _bool_property("Visibility", False),
                ]
            )
        if expressions and not native_replay:
            obj.dependencies.append(parameter_sheet.name)
    sketch_items = _items(manifest.get("sketches", []))
    sketch_names: dict[str, str] = {}
    sketch_objects: list[str] = []
    for sketch in sketch_items:
        sketch_id = _text(sketch.get("id"))
        plane_id = _text(sketch.get("support_plane_id"))
        plane = plane_by_id.get(plane_id, {"transform": {}})
        plane_name = plane_names.get(plane_id, "")
        sketch_attributes = sketch.get("attributes", {})
        native_sketch = (
            sketch_attributes.get("freecad", {})
            if isinstance(sketch_attributes, Mapping)
            else {}
        )
        native_sketch_name = _text(native_sketch.get("name"))
        obj = native_graph.get(native_sketch_name) if native_replay else None
        if obj is None:
            obj = graph.add(
                _text(native_sketch.get("type_id"), SKETCH_TYPE_ID),
                native_sketch.get("name", sketch.get("name", sketch_id)),
                "Sketch",
                touched=True,
                extensions=("Part::AttachExtension",),
            )
        sketch_names[sketch_id] = obj.name
        if native_sketch_name:
            native_object_targets[native_sketch_name] = obj.name
        sketch_objects.append(obj.name)
        properties, dependencies = _sketch_properties(
            sketch, plane, plane_name, parameters, native_replay
        )
        if native_replay and native_sketch:
            obj.properties = properties
        else:
            obj.properties.extend(properties)
        if native_sketch and not native_replay:
            obj.transient_properties.append(
                ET.Element(
                    "_Property",
                    {
                        "name": "_ElementMapVersion",
                        "type": "App::PropertyString",
                        "status": "234881024",
                    },
                )
            )
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
    replay_entry_names: set[str] | None = None
    if not native_replay:
        replay_entry_names = {
            filename
            for value in replay_values
            for property_element in _native_properties(value)
            for node in property_element.iter()
            if node.tag != "XLink" and (filename := node.get("file", ""))
        }
    if native_values and isinstance(freecad_metadata, Mapping):
        for item in _items(freecad_metadata.get("entries", [])):
            source_stream = _text(item.get("source_stream"))
            data = _payload_bytes(item)
            if not source_stream or data is None:
                raise ValueError("native FreeCAD entry metadata is incomplete")
            if (
                replay_entry_names is not None
                and source_stream not in replay_entry_names
            ):
                continue
            entry = _validated_entry_name(source_stream)
            if entry in {DOCUMENT_ENTRY, MANIFEST_ENTRY} or entry in payload_entries:
                raise ValueError(
                    "native FreeCAD entry metadata conflicts with the archive"
                )
            payload_entries[entry] = data
    for feature in feature_items:
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
        native_definition_data = (
            definition.get("object_data", {})
            if _text(definition.get("$type")) == "NativeFeatureDefinition"
            and _text(definition.get("format_id")) == FORMAT_ID
            and isinstance(definition.get("object_data"), Mapping)
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
        feature_sketch_name = sketch_names.get(_text(feature.get("sketch_id")), "")
        native_feature = attributes.get("freecad", {})
        native_feature_name = (
            _text(native_feature.get("name"))
            if isinstance(native_feature, Mapping)
            else ""
        )
        if native_replay and native_feature_name in native_graph:
            final = native_graph[native_feature_name]
            native_property_source = (
                native_definition_data or native_feature
                if isinstance(native_feature, Mapping)
                else native_definition_data
            )
            properties = _native_properties(native_property_source)
            native_definition_type = _text(definition.get("type_id"))
            if native_definition_data and native_definition_type:
                final.type_id = native_definition_type
            property_names = {item.get("name", "") for item in properties}
            if "Label" in property_names:
                _merge_named_property(
                    properties, _string_property("Label", feature_name)
                )
            if kind == "extrusion":
                length = abs(
                    _number(
                        definition.get("length"),
                        _number(attributes.get("length_mm")),
                    )
                )
                replacements = [
                    _float_property("Length", length, "App::PropertyLength"),
                    _float_property(
                        "Length2",
                        abs(_number(definition.get("second_length"))),
                        "App::PropertyLength",
                    ),
                    _bool_property("Midplane", bool(definition.get("symmetric"))),
                    _bool_property("Reversed", bool(definition.get("reversed"))),
                ]
                direction = definition.get("direction")
                if direction is not None:
                    replacements.append(
                        _vector_property(
                            "Direction", _vector(direction, (0.0, 0.0, 1.0))
                        )
                    )
                for replacement in replacements:
                    if replacement.get("name", "") in property_names:
                        _merge_named_property(properties, replacement)
            elif kind == "fillet":
                radius = abs(
                    _number(
                        definition.get("radius"),
                        _number(attributes.get("radius_mm")),
                    )
                )
                for name in ("Radius", "DrivingRadius"):
                    if name in property_names:
                        _merge_named_property(
                            properties,
                            _float_property(name, radius, "App::PropertyLength"),
                        )
            if "Suppressed" in property_names or bool(feature.get("suppressed")):
                _merge_named_property(
                    properties,
                    _bool_property(
                        "Suppressed",
                        bool(feature.get("suppressed")),
                        dynamic="Suppressed" not in property_names,
                    ),
                )
            final.properties = properties
            feature_names[feature_id] = final.name
            solid_feature_names[feature_id] = final.name
            feature_objects.append(final.name)
            current_name = final.name
            native_object_targets[native_feature_name] = final.name
            continue
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
            operation_kind = (
                "join"
                if base_name and operation in CREATE_OPERATION_NAMES
                else operation or "create"
            )
            operation_type = BOOLEAN_OPERATION_TYPE_BY_KIND.get(operation_kind)
            tool_type = BOOLEAN_OPERATION_TYPE_BY_KIND["create"]
            tool_requested = (
                feature_name if not base_name else f"{feature_name}_Profile"
            )
            tool = graph.add(
                tool_type.type_id,
                tool_requested,
                tool_type.label,
                touched=True,
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
            elif (
                operation_type is not None and operation_type.input_mode == "base_tool"
            ):
                final = graph.add(
                    operation_type.type_id,
                    feature_name,
                    operation_type.label,
                    touched=True,
                )
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
            elif operation_type is not None and operation_type.input_mode == "shapes":
                final = graph.add(
                    operation_type.type_id,
                    feature_name,
                    operation_type.label,
                    touched=True,
                )
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
            imported = kind == "imported"
            final = graph.add(
                "Part::Feature",
                feature_name,
                "Feature",
                touched=True,
            )
            final.properties.extend(
                [
                    _string_property("Label", feature_name),
                    _expression_property([]),
                    *_feature_metadata(
                        feature, "imported" if imported else "feature-data"
                    ),
                    _string_property(
                        "NativeTypeId", definition.get("type_id", ""), dynamic=True
                    ),
                    *_definition_properties(definition),
                    _json_property("NativeDefinitionJSON", definition),
                    _bool_property("Visibility", not bool(feature.get("suppressed"))),
                    _shape_property(),
                ]
            )
            if base_name:
                final.properties.append(
                    _link_property("InputFeature", base_name, dynamic=True)
                )
                final.dependencies.append(base_name)
            if feature_sketch_name:
                final.properties.append(
                    _link_property("Profile", feature_sketch_name, dynamic=True)
                )
                final.dependencies.append(feature_sketch_name)
            if parameters_data:
                final.properties.extend(
                    [
                        _link_property(
                            "Parameters", parameter_sheet.name, dynamic=True
                        ),
                        _string_list_property(
                            "ParameterIds",
                            [
                                _text(value)
                                for value in _sequence(feature.get("parameter_ids", []))
                            ],
                            dynamic=True,
                        ),
                    ]
                )
                final.dependencies.append(parameter_sheet.name)
            feature_names[feature_id] = final.name
            feature_objects.append(final.name)
            solid_feature_names[feature_id] = final.name
            current_name = final.name
        if bool(feature.get("suppressed")) and not native_replay:
            _replace_named_property(
                final.properties,
                "Visibility",
                _bool_property("Visibility", False),
            )
        if isinstance(native_feature, Mapping):
            if native_feature_name:
                native_object_targets[native_feature_name] = final.name
    body_objects: list[str] = []
    body_names: dict[str, str] = {}
    body_shape_targets: dict[str, str] = {}
    feature_by_id = {
        _text(item.get("id")): item for item in feature_items if _text(item.get("id"))
    }

    def body_members(final_feature_id: str) -> list[str]:
        pending = [final_feature_id]
        member_ids: set[str] = set()
        while pending:
            feature_id = pending.pop()
            if feature_id in member_ids or feature_id not in feature_by_id:
                continue
            member_ids.add(feature_id)
            pending.extend(
                _text(value)
                for value in _sequence(
                    feature_by_id[feature_id].get("input_feature_ids", [])
                )
            )
        members: list[str] = []
        for item in feature_items:
            feature_id = _text(item.get("id"))
            if feature_id not in member_ids:
                continue
            sketch_name = sketch_names.get(_text(item.get("sketch_id")), "")
            if sketch_name and sketch_name not in members:
                members.append(sketch_name)
            feature_name = feature_names.get(feature_id, "")
            if feature_name and feature_name not in members:
                members.append(feature_name)
        return members

    for body in _items(manifest.get("bodies", [])):
        body_id = _text(body.get("id"))
        final_feature_id = _text(body.get("final_feature_id"))
        final_feature = feature_names.get(final_feature_id, current_name)
        members = body_members(final_feature_id)
        body_attributes = body.get("attributes", {})
        native_body = (
            body_attributes.get("freecad", {})
            if isinstance(body_attributes, Mapping)
            else {}
        )
        native_body_name = (
            _text(native_body.get("name")) if isinstance(native_body, Mapping) else ""
        )
        obj = native_graph.get(native_body_name) if native_replay else None
        if obj is not None:
            properties = _native_properties(native_body)
            _merge_named_property(
                properties, _string_property("Label", body.get("name", body_id))
            )
            if final_feature:
                _merge_named_property(properties, _link_property("Tip", final_feature))
            obj.properties = properties
            native_object_targets[native_body_name] = obj.name
        else:
            obj = graph.add(
                _text(native_body.get("type_id"), "App::Part"),
                native_body.get("name", body.get("name", body_id)),
                "Body",
            )
            obj.properties.extend(
                [
                    _string_property("Label", body.get("name", body_id)),
                    _link_list_property("Group", members),
                    _link_property("Tip", final_feature, dynamic=True),
                    _placement_property(
                        "Placement", _matrix_transform(_IDENTITY_MATRIX)
                    ),
                    _string_property("KitId", body_id, dynamic=True),
                    _json_property("TopologyJSON", body.get("topology", {})),
                    _json_property("SourceBodyJSON", body),
                    _bool_property("Visibility", True),
                ]
            )
            material_id = _text(body.get("material_id"))
            if material_id:
                obj.properties.append(
                    _string_property("MaterialId", material_id, dynamic=True)
                )
            obj.dependencies.extend(members)
        body_names[body_id] = obj.name
        body_shape_targets[body_id] = final_feature or obj.name
        body_objects.append(obj.name)
    target_by_id = {
        **plane_names,
        **sketch_names,
        **feature_names,
        **body_names,
    }
    target_by_id.update({name: name for name in graph.names})
    selection_names: dict[str, str] = {}
    selection_objects: list[str] = []
    for selection in selection_items.values():
        selection_id = _text(selection.get("id"))
        obj = graph.add(
            "App::FeaturePython",
            selection.get("name", selection_id),
            "Selection",
        )
        targets: list[tuple[str, str]] = []
        entity_kinds: list[str] = []
        for path_item in _items(selection.get("path", [])):
            entity_id = _text(path_item.get("entity_id"))
            target = target_by_id.get(
                entity_id, native_object_targets.get(entity_id, "")
            )
            if not target:
                continue
            targets.append((target, _text(path_item.get("subelement"))))
            entity_kinds.append(_text(path_item.get("entity_kind")))
        obj.properties.extend(
            [
                _string_property("Label", selection.get("name", selection_id)),
                _string_property("KitSelectionId", selection_id, dynamic=True),
                _link_sub_list_property("Selection", targets, dynamic=True),
                _string_list_property("EntityKinds", entity_kinds, dynamic=True),
                _json_property("QueryJSON", selection.get("query", {})),
                _json_property("SourceSelectionJSON", selection),
                _bool_property("Visibility", False),
            ]
        )
        point = selection.get("point")
        if point is not None:
            obj.properties.append(
                _vector_property(
                    "SelectionPoint",
                    _vector(point, (0.0, 0.0, 0.0)),
                    dynamic=True,
                )
            )
        obj.dependencies.extend(target for target, _ in targets)
        selection_names[selection_id] = obj.name
        selection_objects.append(obj.name)
    for feature in feature_items:
        target = next(
            (
                item
                for item in graph.objects
                if item.name == feature_names.get(_text(feature.get("id")), "")
            ),
            None,
        )
        linked_selections = [
            selection_names[selection_id]
            for value in _sequence(feature.get("selection_ids", []))
            if (selection_id := _text(value)) in selection_names
        ]
        if target is not None and linked_selections:
            _merge_named_property(
                target.properties,
                _link_list_property("Selections", linked_selections, dynamic=True),
            )
            target.dependencies.extend(linked_selections)
    for plane in plane_items:
        selection_name = selection_names.get(
            _text(plane.get("support_selection_id")), ""
        )
        target = next(
            (
                item
                for item in graph.objects
                if item.name == plane_names.get(_text(plane.get("id")), "")
            ),
            None,
        )
        if target is not None and selection_name:
            _merge_named_property(
                target.properties,
                _link_property("SupportSelection", selection_name, dynamic=True),
            )
            target.dependencies.append(selection_name)
    configuration_items = _items(manifest.get("configurations", []))
    configuration_names: dict[str, str] = {}
    configuration_objects: list[str] = []
    for configuration in configuration_items:
        configuration_id = _text(configuration.get("id"))
        obj = graph.add(
            "App::FeaturePython",
            configuration.get("name", configuration_id),
            "Configuration",
        )
        configuration_names[configuration_id] = obj.name
        configuration_objects.append(obj.name)
    for configuration, object_name in zip(
        configuration_items, configuration_objects, strict=True
    ):
        obj = next(item for item in graph.objects if item.name == object_name)
        configuration_id = _text(configuration.get("id"))
        parent_name = configuration_names.get(_text(configuration.get("parent_id")), "")
        suppressed_features = [
            feature_names[feature_id]
            for value in _sequence(configuration.get("suppressed_feature_ids", []))
            if (feature_id := _text(value)) in feature_names
        ]
        obj.properties.extend(
            [
                _string_property("Label", configuration.get("name", configuration_id)),
                _string_property("KitConfigurationId", configuration_id, dynamic=True),
                _bool_property(
                    "Active", bool(configuration.get("active")), dynamic=True
                ),
                _link_list_property(
                    "SuppressedFeatures", suppressed_features, dynamic=True
                ),
                _link_property("Parameters", parameter_sheet.name, dynamic=True),
                _json_property(
                    "ParameterOverridesJSON", configuration.get("overrides", [])
                ),
                _json_property("SourceConfigurationJSON", configuration),
                _bool_property("Visibility", False),
            ]
        )
        if parent_name:
            obj.properties.append(
                _link_property("ParentConfiguration", parent_name, dynamic=True)
            )
        obj.dependencies.extend(
            [parameter_sheet.name, *suppressed_features]
            + ([parent_name] if parent_name else [])
        )
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
        attributes = (
            payload.get("attributes", {})
            if isinstance(payload.get("attributes"), Mapping)
            else {}
        )
        target_feature_id = _text(
            attributes.get("feature_id", attributes.get("final_feature_id"))
        )
        target_body_id = _text(attributes.get("body_id"))
        source_object = _text(attributes.get("freecad_object"))
        property_name = _text(attributes.get("freecad_property"), "Shape")
        target_name = native_object_targets.get(source_object, "")
        if not target_name and target_feature_id:
            target_name = feature_names.get(target_feature_id, "")
        if not target_name and target_body_id:
            target_name = body_shape_targets.get(target_body_id, "")
        if not target_name and not source_object:
            target_name = current_name
        native_brep = _payload_role(payload) == "brep" and _freecad_brep_payload(
            payload, data
        )
        if native_brep:
            target = next(
                (item for item in graph.objects if item.name == target_name), None
            )
            if target is None:
                target = graph.add(
                    "Part::Feature",
                    f"NativeBRep_{index}",
                    _text(payload.get("id"), f"Native BRep {index}"),
                )
                target.properties.extend(
                    [
                        _string_property(
                            "Label", _text(payload.get("id"), f"Native BRep {index}")
                        ),
                        _string_property(
                            "KitPayloadId", payload.get("id"), dynamic=True
                        ),
                        _bool_property("Visibility", True),
                    ]
                )
                body_objects.append(target.name)
                target_name = target.name
            if target is not None:
                shape_entry = f"{target.name}.{_safe(property_name, 'Shape')}.brp"
                payload_entries[shape_entry] = data
                sidecar_entries: dict[str, str] = {}
                for sidecar in _items(attributes.get("freecad_sidecars", [])):
                    source_stream = _text(sidecar.get("source_stream"))
                    sidecar_data = _payload_bytes(sidecar)
                    if not source_stream or sidecar_data is None:
                        continue
                    suffix = PurePosixPath(source_stream).name
                    source_prefix = PurePosixPath(
                        _text(payload.get("source_stream"))
                    ).stem
                    if suffix.startswith(source_prefix):
                        suffix = suffix[len(source_prefix) :]
                    sidecar_entry = (
                        f"{target.name}.{_safe(property_name, 'Shape')}{suffix}"
                    )
                    sidecar_entries[source_stream] = sidecar_entry
                    payload_entries[sidecar_entry] = sidecar_data
                property_element = _element_from_data(
                    attributes.get("freecad_property_data")
                )
                if property_element is None or property_element.tag != "Property":
                    property_element = _shape_property(
                        shape_entry, _safe(property_name, "Shape")
                    )
                for child in property_element.findall(".//*[@file]"):
                    source_stream = child.get("file", "")
                    child.set(
                        "file",
                        (
                            shape_entry
                            if child.tag == "Part"
                            else sidecar_entries.get(source_stream, source_stream)
                        ),
                    )
                _merge_named_property(target.properties, property_element)
                if property_name == "Shape" and target.name == current_name:
                    final_shape_filename = shape_entry
    document_breps, neutral_shape_filename = _add_document_brep(
        graph, manifest, payload_entries, current_name
    )
    if neutral_shape_filename:
        final_shape_filename = neutral_shape_filename
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
    selections_group.properties.extend(
        [
            _string_property("Label", "Selections"),
            _link_list_property("Group", selection_objects),
            _bool_property("Visibility", False),
        ]
    )
    selections_group.dependencies.extend(selection_objects)
    configurations_group.properties.extend(
        [
            _string_property("Label", "Configurations"),
            _link_list_property("Group", configuration_objects),
            _bool_property("Visibility", False),
        ]
    )
    configurations_group.dependencies.extend(configuration_objects)
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
            _link_list_property("Group", [*body_objects, *document_breps]),
            _bool_property("Visibility", True),
        ]
    )
    bodies_group.dependencies.extend([*body_objects, *document_breps])
    external_target = (
        document_breps[0]
        if document_breps
        else (
            document_meshes[0]
            if document_meshes
            else assembly_root
            or current_name
            or (bodies_group.name if body_objects else "")
            or (feature_objects[-1] if feature_objects else "")
            or bodies_group.name
        )
    )
    target_object = next(
        (item for item in graph.objects if item.name == external_target), None
    )
    if target_object is not None and not native_replay:
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
    if native_replay and native_external_links:
        for obj in native_graph.values():
            for property_element in obj.properties:
                for xlink in property_element.findall(".//XLink[@file]"):
                    source_file = xlink.get("file", "")
                    if source_file in native_external_links:
                        xlink.set("file", native_external_links[source_file])
    string_hasher = (
        freecad_metadata.get("string_hasher", {})
        if isinstance(freecad_metadata, Mapping)
        else {}
    )
    root_attributes = {
        "SchemaVersion": _TARGET_SCHEMA_VERSION,
        "ProgramVersion": (
            _text(
                freecad_metadata.get("program_version"),
                _TARGET_PROGRAM_VERSION,
            )
            if native_replay and isinstance(freecad_metadata, Mapping)
            else _TARGET_PROGRAM_VERSION
        ),
        "FileVersion": (
            _text(
                freecad_metadata.get("file_version"),
                _TARGET_FILE_VERSION,
            )
            if native_replay and isinstance(freecad_metadata, Mapping)
            else _TARGET_FILE_VERSION
        ),
    }
    if isinstance(string_hasher, Mapping):
        attribute = _text(string_hasher.get("attribute"))
        if attribute:
            root_attributes["StringHasher"] = attribute
    root = ET.Element(
        "Document",
        root_attributes,
    )
    if isinstance(string_hasher, Mapping):
        for value in _items(string_hasher.get("nodes", [])):
            node = _element_from_data(value)
            if node is not None and node.tag in STRING_HASHER_TAGS:
                root.append(node)
        for entry in _items(string_hasher.get("entries", [])):
            source_stream = _text(entry.get("source_stream"))
            data = _payload_bytes(entry)
            path = PurePosixPath(source_stream)
            if (
                source_stream
                and data is not None
                and not path.is_absolute()
                and ".." not in path.parts
            ):
                payload_entries[source_stream] = data
    _sanitize_payload_references(graph.objects, payload_entries)
    native_document_properties = (
        _element_from_data(freecad_metadata.get("document_properties"))
        if native_replay and isinstance(freecad_metadata, Mapping)
        else None
    )
    root.append(
        native_document_properties
        if native_document_properties is not None
        and native_document_properties.tag == "Properties"
        else _document_properties(label, document_id, document_timestamp)
    )
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
    object_ids = {obj.object_id for obj in graph.objects if obj.object_id}
    numeric_ids = [int(value) for value in object_ids if value.isdigit()]
    next_object_id = max(numeric_ids, default=0) + 1
    for obj in graph.objects:
        object_id = obj.object_id
        if not object_id:
            while str(next_object_id) in object_ids:
                next_object_id += 1
            object_id = str(next_object_id)
            object_ids.add(object_id)
            next_object_id += 1
        attributes = {"type": obj.type_id, "name": obj.name, "id": object_id}
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
    native_external_links: Mapping[str, str] | None = None,
    document_timestamp: str | None = None,
) -> bytes:
    canonical = _canonical_manifest(manifest)
    digest = hashlib.sha256(canonical).hexdigest()
    embedded = base64.b64encode(zlib.compress(canonical, 9)).decode("ascii")
    document_xml, payload_entries = _document_xml(
        manifest,
        embedded,
        digest,
        external_links,
        native_external_links,
        document_timestamp or "1980-01-01T00:00:00Z",
    )
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", allowZip64=True) as archive:
        archive.writestr(*_zip_entry(DOCUMENT_ENTRY, document_xml))
        metadata = manifest.get("metadata", {})
        freecad_metadata = (
            metadata.get("freecad", {}) if isinstance(metadata, Mapping) else {}
        )
        entry_order = (
            _sequence(freecad_metadata.get("entry_order", []))
            if isinstance(freecad_metadata, Mapping)
            else []
        )
        written: set[str] = set()
        for value in entry_order:
            entry = _text(value)
            if entry in payload_entries and entry not in written:
                archive.writestr(*_zip_entry(entry, payload_entries[entry]))
                written.add(entry)
        archive.writestr(*_zip_entry(MANIFEST_ENTRY, canonical + b"\n"))
        for entry, data in sorted(payload_entries.items()):
            if entry in written:
                continue
            archive.writestr(*_zip_entry(entry, data))
    return output.getvalue()


def _document_xml_manifest(root: ET.Element) -> bytes | None:
    names = {
        MANIFEST_DATA_PROPERTY,
        MANIFEST_ENCODING_PROPERTY,
        MANIFEST_SHA256_PROPERTY,
    }
    values: dict[str, list[str]] = {name: [] for name in names}
    for property_element in root.findall(".//Property"):
        name = property_element.get("name", "")
        if name not in values:
            continue
        string = property_element.find("String")
        values[name].append(string.get("value", "") if string is not None else "")
    if not any(values.values()):
        return None
    if any(len(items) > 1 for items in values.values()):
        raise ValueError("embedded Kit interchange document is corrupt")
    encoded = next(iter(values[MANIFEST_DATA_PROPERTY]), "")
    encoding = next(iter(values[MANIFEST_ENCODING_PROPERTY]), "")
    digest = next(iter(values[MANIFEST_SHA256_PROPERTY]), "")
    if not encoded or encoding != MANIFEST_ENCODING:
        raise ValueError("embedded Kit interchange document is corrupt")
    try:
        compressed = base64.b64decode(encoded, validate=True)
        decompressor = zlib.decompressobj()
        canonical = decompressor.decompress(compressed, _MAX_ENTRY_SIZE + 1)
        if (
            len(canonical) > _MAX_ENTRY_SIZE
            or decompressor.unconsumed_tail
            or not decompressor.eof
        ):
            raise ValueError
        canonical += decompressor.flush()
        if len(canonical) > _MAX_ENTRY_SIZE or decompressor.unused_data:
            raise ValueError
    except (ValueError, zlib.error) as exc:
        raise ValueError("embedded Kit interchange document is corrupt") from exc
    if digest and hashlib.sha256(canonical).hexdigest() != digest:
        raise ValueError("embedded Kit interchange document hash mismatch")
    return canonical


def _canonical_manifest(value: Mapping[str, Any]) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def extract_manifest_from_fcstd(data: bytes) -> dict[str, Any]:
    archive, members = _validated_archive_members(data)
    with archive:
        root, _ = _validated_document_xml(archive, members)
        xml_manifest = _document_xml_manifest(root)
        if MANIFEST_ENTRY not in members:
            if xml_manifest is None:
                raise ValueError(
                    "FCStd archive has no embedded Kit interchange document"
                )
            return _manifest_mapping(xml_manifest)
        try:
            raw_manifest = archive.read(members[MANIFEST_ENTRY])
        except (
            OSError,
            RuntimeError,
            NotImplementedError,
            zipfile.BadZipFile,
        ) as exc:
            raise ValueError("embedded Kit interchange document is corrupt") from exc
        manifest = _manifest_mapping(raw_manifest)
        if xml_manifest is not None:
            secondary = _manifest_mapping(xml_manifest)
            if _canonical_manifest(manifest) != _canonical_manifest(secondary):
                raise ValueError(
                    "embedded Kit interchange document copies do not match"
                )
        return manifest
