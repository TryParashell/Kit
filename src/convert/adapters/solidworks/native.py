from __future__ import annotations

from dataclasses import dataclass, field, replace
import itertools
import math
import re
import struct
from types import MappingProxyType
import xml.etree.ElementTree as ET

from .container import SldprtFormatError
from .format import (
    CANONICAL_PLANE_FEATURE_TYPE,
    CLASS_MARKER,
    PLANE_FEATURE_TYPES,
    dimension_scalar_value_offset,
)


_CURRENT_MARKER = bytes.fromhex("ffff1f0003")
_LEGACY_MARKER = bytes.fromhex("ffff070001")
_EXTENDED_MARKER = bytes.fromhex("ffff1f0001")
_MARKERS = (_CURRENT_MARKER, _LEGACY_MARKER, _EXTENDED_MARKER)
_COORDINATE_TAG = bytes.fromhex("1e00")
_POINT_LOCUS = bytes.fromhex("04000200")
_CIRCLE_LOCUS = bytes.fromhex("05000100")
_NUMBER = re.compile(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?")
_EDGE_SELECTION_IDENTITY = bytes.fromhex("7dc39425ad49b2547dc39425ad49b254")
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


@dataclass(frozen=True, slots=True)
class NativeEndSpec:
    offset: int
    termination_code: int
    direction_code: int
    second_direction_code: int


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


@dataclass(frozen=True, slots=True)
class NativeConfiguration:
    object_id: int
    name: str
    configuration_id: int
    properties: dict[str, str]


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


@dataclass(slots=True)
class _XmlFeature:
    object_id: int
    name: str
    kind: str
    xml_tag: str
    properties: dict[str, str]
    dimensions: list[NativeDimension]


def decode_native_model(keywords: bytes, resolved: bytes) -> NativeModel:
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
        dimensions = _semantic_dimensions(
            feature.kind,
            tuple(_bind_dimension(item, owned) for item in feature.dimensions),
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
            )
        )
    planes = _decode_planes(resolved, native_features)
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
    sketches: list[NativeSketch] = []
    operations: list[NativeOperation] = []
    native_index_by_id = {
        feature.object_id: index for index, feature in enumerate(native_features)
    }
    latest_sketch: NativeSketch | None = None
    latest_operation: NativeOperation | None = None
    latest_plane_id = next(iter(principal_plane_frames), next(iter(plane_by_id), 0))
    for feature in author:
        if _is_plane_feature(feature):
            latest_plane_id = feature.object_id
            continue
        if feature.kind.casefold() == "sketch":
            support = _support_plane_id(
                resolved,
                feature.native_offset or 0,
                feature.native_end or len(resolved),
                latest_plane_id,
                plane_by_id,
            )
            latest_sketch = _decode_sketch(resolved, feature, support)
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
            end_spec = _end_spec(
                resolved,
                feature.native_offset or 0,
                feature.native_end or len(resolved),
            )
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
                native_offset=feature.native_offset or 0,
                native_end=feature.native_end or len(resolved),
                length_mm=_operation_dimension(feature.dimensions, "length"),
                radius_mm=None,
                family_code=family,
                operation_code=operation_code,
                schema_code=schema,
                direction_code=end_spec.direction_code if end_spec else None,
                termination_code=end_spec.termination_code if end_spec else None,
                selection_offsets=(),
                selected_local_ids=(),
            )
            operations.append(operation)
            latest_operation = operation
            continue
        if feature.kind.casefold() == "fillet":
            selections = _edge_selections(
                resolved,
                feature.native_offset or 0,
                feature.native_end or len(resolved),
            )
            selections = tuple(
                selection
                for selection in selections
                if selection[1] != feature.object_id
            )
            producer_ids = tuple(
                dict.fromkeys(selection[1] for selection in selections)
            )
            dependencies = producer_ids or (
                (latest_operation.object_id,) if latest_operation else ()
            )
            operation = NativeOperation(
                object_id=feature.object_id,
                name=feature.name,
                kind="fillet",
                profile_id=None,
                dependencies=dependencies,
                native_offset=feature.native_offset or 0,
                native_end=feature.native_end or len(resolved),
                length_mm=None,
                radius_mm=_operation_dimension(feature.dimensions, "radius"),
                family_code=None,
                operation_code=None,
                schema_code=None,
                direction_code=None,
                termination_code=None,
                selection_offsets=tuple(selection[0] for selection in selections),
                selected_local_ids=tuple(
                    dict.fromkeys(selection[2] for selection in selections)
                ),
            )
            operations.append(operation)
            latest_operation = operation
    diagnostics = []
    unresolved = [
        feature
        for feature in native_features
        if feature.native_offset is None and feature.object_id > 0
    ]
    if unresolved:
        diagnostics.append(
            "native name records unavailable for "
            + ", ".join(f"{feature.object_id}:{feature.name}" for feature in unresolved)
        )
    return NativeModel(
        configurations=configurations,
        features=tuple(
            sorted(
                native_features,
                key=lambda feature: (
                    feature.native_offset is None,
                    (
                        feature.native_offset
                        if feature.native_offset is not None
                        else feature.object_id
                    ),
                ),
            )
        ),
        planes=tuple(planes),
        sketches=tuple(sketches),
        operations=tuple(operations),
        names=names,
        classes=classes,
        scalars=scalars,
        diagnostics=tuple(diagnostics),
    )


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
        else "radius" if text.lstrip().startswith("R") else "length"
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
    target = dimension.value_mm / 1000.0
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
    semantic = {
        "extrusion": "length",
        "fillet": "radius",
    }.get(feature_kind.casefold())
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


def _decode_planes(data: bytes, features: list[NativeFeature]) -> list[NativePlane]:
    principal = _principal_plane_frames(features)
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


def _support_plane_id(
    data: bytes,
    start: int,
    end: int,
    fallback: int,
    planes: dict[int, NativePlane],
) -> int:
    sources = _component_plane_sources(data, start, end)
    known = [source for source in sources if source in planes]
    return known[-1] if known else fallback


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
    data: bytes, feature: NativeFeature, support_plane_id: int
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
        coordinates = _marker_coordinates(data, offset, end)
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
            )
        )
    return tuple(markers)


def _marker_coordinates(
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
            return _clean(round(x * 1000.0, 12)), _clean(round(y * 1000.0, 12))
    return None


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
        return "relation"
    if locus == _CIRCLE_LOCUS and coordinates is not None:
        return "circle"
    if locus == _POINT_LOCUS:
        if coordinates is not None:
            return "point"
        if endpoints is not None and endpoints[0] != endpoints[1]:
            return "line"
        return "reference"
    return "native"


def _profiles(
    markers: list[NativeMarker], dimensions: tuple[NativeDimension, ...]
) -> tuple[tuple[NativeProfile, ...], set[int], tuple[NativeDimension, ...]]:
    circle = _circle_profile(markers, dimensions)
    if circle is not None:
        profile, selected_index, semantic = circle
        normalized = tuple(
            replace(dimension, kind=semantic) if index == selected_index else dimension
            for index, dimension in enumerate(dimensions)
        )
        return (profile,), set(profile.marker_offsets), normalized
    points = [
        marker
        for marker in markers
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
        for marker in markers
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
    profiles: list[NativeProfile] = []
    used: set[int] = set()
    for index, rectangle in enumerate(selected):
        span = tuple(
            marker.offset
            for marker in (profile_lines[index] if index < len(profile_lines) else ())
        )
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
    return tuple(profiles), used, dimensions


def _circle_profile(
    markers: list[NativeMarker], dimensions: tuple[NativeDimension, ...]
) -> tuple[NativeProfile, int, str] | None:
    centers = [
        marker
        for marker in markers
        if marker.semantic == "circle" and marker.coordinates_mm is not None
    ]
    if not centers:
        return None
    preferred = next(
        (
            marker
            for marker in reversed(centers)
            if marker.native_kind != 0
            and any(
                candidate.offset > marker.offset
                and candidate.native_kind == 0
                and candidate.semantic == "circle"
                for candidate in centers
            )
        ),
        centers[-1],
    )
    ordered_centers = (
        preferred,
        *tuple(marker for marker in centers if marker != preferred),
    )
    candidates: list[
        tuple[tuple[bool, bool, bool, bool, int, int], NativeProfile, int, str]
    ] = []
    for center_order, center in enumerate(ordered_centers):
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
        radius = math.dist(center.coordinates_mm, following.coordinates_mm)
        if not math.isfinite(radius) or radius <= 1e-12:
            continue
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
            profile = NativeProfile(
                "circle",
                (
                    center.coordinates_mm[0],
                    center.coordinates_mm[1],
                    normalized_radius,
                ),
                (center.offset, following.offset),
                dimension.name,
                semantic,
            )
            rank = (
                center_order != 0,
                len(dimension.operands) != 1,
                dimension.kind not in {"radius", "diameter"},
                dimension.native_role == "display",
                (
                    dimension.native_offset
                    if dimension.native_offset is not None
                    else index
                ),
                index,
            )
            candidates.append((rank, profile, index, semantic))
    if candidates:
        _, profile, index, semantic = min(candidates, key=lambda item: item[0])
        return profile, index, semantic
    diameter = next(
        (
            (index, dimension)
            for index, dimension in enumerate(dimensions)
            if dimension.kind == "diameter"
        ),
        None,
    )
    if diameter is None:
        return None
    index, dimension = diameter
    center = preferred
    following = next(
        (
            marker
            for marker in markers
            if marker.offset > center.offset and marker.coordinates_mm is not None
        ),
        center,
    )
    return (
        NativeProfile(
            "circle",
            (
                center.coordinates_mm[0],
                center.coordinates_mm[1],
                dimension.value_mm / 2.0,
            ),
            (center.offset, following.offset),
            dimension.name,
            "diameter",
        ),
        index,
        "diameter",
    )


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


def _end_spec(data: bytes, start: int, end: int) -> NativeEndSpec | None:
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
        return NativeEndSpec(offset, termination, direction, second)
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
