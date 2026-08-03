from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import math
import struct
from types import MappingProxyType

from .container import SldprtFormatError
from .format import (
    CLASS_MARKER,
    SERIALIZED_STRING_MARKER,
    dimension_scalar_value_offset,
)

PROFILE_CLASS = "moProfileFeature_c"
LENGTH_PARAMETER_CLASS = "moLengthParameter_c"
END_SPEC_CLASS = "moEndSpec_c"
FROM_END_SPEC_CLASS = "moFromEndSpec_c"
SKETCH_CHAIN_CLASS = "moSketchChain_c"

DEPTH_RELATIVE = 57
REVERSE_RELATIVE = 27
END_CONDITION_RELATIVE = 33
FROM_REVERSE_RELATIVE = 29
RECTANGLE_POINT_RELATIVE = (283, 461, 623, 785)

BLIND_END_CONDITION = 0
MID_PLANE_END_CONDITION = 6
SUPPORTED_END_CONDITIONS = frozenset({BLIND_END_CONDITION, MID_PLANE_END_CONDITION})

BOSS_FLAGS = 0x40000140
CUT_FLAGS = 0x400201CA
SKETCH_FLAGS = 0x40000000
PLANE_FLAGS = 0xC0000000
BOSS_KIND = "boss"
CUT_KIND = "cut"
FEATURE_KIND_BY_FLAGS = MappingProxyType({BOSS_FLAGS: BOSS_KIND, CUT_FLAGS: CUT_KIND})
TREE_NODE_FLAGS = frozenset({BOSS_FLAGS, CUT_FLAGS, SKETCH_FLAGS, PLANE_FLAGS})

SKETCH_POINT_PREFIX = bytes.fromhex("000000000000f03f00000000000000001e00")
SKETCH_POINT_SUFFIX = bytes.fromhex("00000200")
SKETCH_NAME_PREFIX = "Sketch"
DEPTH_SCALAR_NAME_PREFIX = "D"

DEPTH_COPY_DELTAS = (0, 72, 398, 422, 560, 584)
DEPTH_COPY_SIGNS = (1, 1, -1, -1, 1, 1)

FIRST_FEATURE_REVERSE_DISTANCE = 824
FIRST_FEATURE_END_CONDITION_DISTANCE = 818
LATER_FEATURE_REVERSE_DISTANCE = 721
LATER_FEATURE_END_CONDITION_DISTANCE = 715

CIRCLE_POINT_ANGLE_DEGREES = 17.0

_NAME_MARKER_CLASS_TOKEN = 0x8004
_MAX_CLASS_NAME = 64
_MAX_NAME_UNITS = 128
_MAX_FEATURE_ID = 4096
_NAME_TRAILER_BYTES = 12
_METRES = 1000.0


@dataclass(frozen=True, slots=True)
class ClassRecord:
    offset: int
    name: str
    data_offset: int


@dataclass(frozen=True, slots=True)
class NameRecord:
    offset: int
    text_end: int
    name: str
    flags: int
    feature_id: int


@dataclass(frozen=True, slots=True)
class DimensionScalar:
    name: str
    name_offset: int
    value_offset: int
    value_mm: float


@dataclass(frozen=True, slots=True)
class SketchPoint:
    offset: int
    x_mm: float
    y_mm: float


@dataclass(frozen=True, slots=True)
class FeatureLayout:
    ordinal: int
    name: str
    kind: str
    feature_id: int
    flags: int
    flags_offset: int
    sketch_name: str | None
    sketch_id: int | None
    points: tuple[SketchPoint, ...]
    depth_offset: int | None
    depth_mm: float | None
    depth_copy_offsets: tuple[int, ...]
    reverse_offset: int | None
    end_condition_offset: int | None
    reversed: bool | None
    end_condition_code: int | None

    @property
    def corners_mm(self) -> tuple[tuple[float, float], ...]:
        return tuple((point.x_mm, point.y_mm) for point in self.points)

    @property
    def bounds_mm(self) -> tuple[float, float, float, float] | None:
        if not self.points:
            return None
        xs = tuple(point.x_mm for point in self.points)
        ys = tuple(point.y_mm for point in self.points)
        return min(xs), min(ys), max(xs), max(ys)


@dataclass(frozen=True, slots=True)
class FeatureEdit:
    corners_mm: Sequence[tuple[float, float]] | None = None
    depth_mm: float | None = None
    reversed: bool | None = None
    end_condition_code: int | None = None
    update_depth_copies: bool = False


@dataclass(frozen=True, slots=True)
class RectanglePadLayout:
    point_offsets: tuple[tuple[int, int], ...]
    depth_offset: int
    reverse_offset: int
    end_condition_offset: int
    from_reverse_offset: int | None
    corners_mm: tuple[tuple[float, float], ...]
    depth_mm: float
    reversed: bool
    end_condition_code: int

    @property
    def bounds_mm(self) -> tuple[float, float, float, float]:
        xs = tuple(point[0] for point in self.corners_mm)
        ys = tuple(point[1] for point in self.corners_mm)
        return min(xs), min(ys), max(xs), max(ys)


def class_records(data: bytes | bytearray) -> tuple[ClassRecord, ...]:
    blob = bytes(data)
    result: list[ClassRecord] = []
    cursor = 0
    while True:
        offset = blob.find(CLASS_MARKER, cursor)
        if offset < 0:
            break
        cursor = offset + 1
        header_end = offset + len(CLASS_MARKER) + 2
        if header_end > len(blob):
            continue
        length = struct.unpack_from("<H", blob, offset + len(CLASS_MARKER))[0]
        if not 0 < length <= _MAX_CLASS_NAME:
            continue
        start = header_end
        end = start + length
        if end > len(blob):
            continue
        try:
            name = blob[start:end].decode("ascii")
        except UnicodeDecodeError:
            continue
        if not name.replace("_", "").isalnum():
            continue
        result.append(ClassRecord(offset, name, end))
    return tuple(result)


def first_class_offset(records: tuple[ClassRecord, ...], name: str) -> int | None:
    for record in records:
        if record.name == name:
            return record.offset
    return None


def name_marker(data: bytes | bytearray) -> bytes:
    blob = bytes(data)
    for record in class_records(blob):
        end = record.data_offset
        if end + 5 > len(blob):
            continue
        token = struct.unpack_from("<H", blob, end)[0]
        if (
            token & 0x8000
            and token != 0xFFFF
            and blob[end + 2 : end + 5] == SERIALIZED_STRING_MARKER
        ):
            return struct.pack("<H", token) + SERIALIZED_STRING_MARKER
    return struct.pack("<H", _NAME_MARKER_CLASS_TOKEN) + SERIALIZED_STRING_MARKER


def name_records(data: bytes | bytearray) -> tuple[NameRecord, ...]:
    blob = bytes(data)
    return _name_records(blob, name_marker(blob))


def tree_nodes(data: bytes | bytearray) -> tuple[NameRecord, ...]:
    blob = bytes(data)
    return _tree_nodes(blob, name_records(blob))


def dimension_scalars(data: bytes | bytearray) -> tuple[DimensionScalar, ...]:
    blob = bytes(data)
    return _dimension_scalars(blob, name_records(blob))


def sketch_points(data: bytes | bytearray) -> tuple[SketchPoint, ...]:
    blob = bytes(data)
    result: list[SketchPoint] = []
    cursor = 0
    while True:
        offset = blob.find(SKETCH_POINT_PREFIX, cursor)
        if offset < 0:
            break
        cursor = offset + 1
        start = offset + len(SKETCH_POINT_PREFIX)
        suffix_end = start + 16 + len(SKETCH_POINT_SUFFIX)
        if suffix_end > len(blob):
            continue
        if blob[start + 16 : suffix_end] != SKETCH_POINT_SUFFIX:
            continue
        x = _read_double(blob, start)
        y = _read_double(blob, start + 8)
        if x is None or y is None:
            continue
        result.append(SketchPoint(offset=start, x_mm=x * _METRES, y_mm=y * _METRES))
    return tuple(result)


def locate_features(data: bytes | bytearray) -> tuple[FeatureLayout, ...]:
    blob = bytes(data)
    records = name_records(blob)
    nodes = _tree_nodes(blob, records)
    features = tuple(node for node in nodes if node.flags in FEATURE_KIND_BY_FLAGS)
    sketch_points_by_sketch = _sketch_point_groups(blob, nodes)
    scalars = tuple(
        scalar
        for scalar in _dimension_scalars(blob, records)
        if scalar.name.startswith(DEPTH_SCALAR_NAME_PREFIX)
    )
    result: list[FeatureLayout] = []
    cursor = 0
    for ordinal, feature in enumerate(features):
        limit = (
            features[ordinal + 1].offset if ordinal + 1 < len(features) else len(blob)
        )
        scalar: DimensionScalar | None = None
        if cursor < len(scalars) and scalars[cursor].value_offset < limit:
            scalar = scalars[cursor]
            cursor += 1
        sketch, points = (
            sketch_points_by_sketch[ordinal]
            if ordinal < len(sketch_points_by_sketch)
            else (None, ())
        )
        result.append(_feature_layout(blob, ordinal, feature, sketch, points, scalar))
    return tuple(result)


def rectangle_corners_mm(
    minimum_x_mm: float,
    minimum_y_mm: float,
    maximum_x_mm: float,
    maximum_y_mm: float,
) -> tuple[tuple[float, float], ...]:
    return (
        (minimum_x_mm, minimum_y_mm),
        (maximum_x_mm, maximum_y_mm),
        (minimum_x_mm, maximum_y_mm),
        (maximum_x_mm, minimum_y_mm),
    )


def circle_radius_mm(x_mm: float, y_mm: float) -> float:
    return math.hypot(x_mm, y_mm)


def circle_circumference_point_mm(radius_mm: float) -> tuple[float, float]:
    if not math.isfinite(radius_mm) or radius_mm <= 0.0:
        raise SldprtFormatError("circular profile requires a positive finite radius")
    angle = math.radians(CIRCLE_POINT_ANGLE_DEGREES)
    return radius_mm * math.cos(angle), radius_mm * math.sin(angle)


def patch_features(data: bytes | bytearray, edits: Mapping[int, FeatureEdit]) -> bytes:
    features = locate_features(data)
    ordinals = {feature.ordinal for feature in features}
    unknown = sorted(set(edits) - ordinals)
    if unknown:
        raise SldprtFormatError(
            f"resolved-features stream has no feature at ordinals {unknown}"
        )
    output = bytearray(data)
    for ordinal in sorted(edits):
        feature = features[ordinal]
        edit = edits[ordinal]
        _validate_edit(feature, edit)
        if edit.corners_mm is not None:
            for point, (x, y) in zip(feature.points, edit.corners_mm, strict=True):
                struct.pack_into("<d", output, point.offset, x / _METRES)
                struct.pack_into("<d", output, point.offset + 8, y / _METRES)
        if edit.depth_mm is not None:
            struct.pack_into(
                "<d", output, feature.depth_offset, edit.depth_mm / _METRES
            )
            if edit.update_depth_copies:
                for delta, sign in zip(
                    DEPTH_COPY_DELTAS, DEPTH_COPY_SIGNS, strict=True
                ):
                    target = feature.depth_offset + delta
                    if target + 8 <= len(output):
                        struct.pack_into(
                            "<d", output, target, sign * edit.depth_mm / _METRES
                        )
        if edit.reversed is not None:
            output[feature.reverse_offset] = 1 if edit.reversed else 0
        if edit.end_condition_code is not None:
            output[feature.end_condition_offset] = edit.end_condition_code
    patched = bytes(output)
    _verify_features(patched, features, edits)
    return patched


def locate_rectangle_pad(data: bytes | bytearray) -> RectanglePadLayout | None:
    blob = bytes(data)
    records = class_records(blob)
    profile = first_class_offset(records, PROFILE_CLASS)
    parameter = first_class_offset(records, LENGTH_PARAMETER_CLASS)
    end_spec = first_class_offset(records, END_SPEC_CLASS)
    if profile is None or parameter is None or end_spec is None:
        return None
    point_offsets: list[tuple[int, int]] = []
    corners: list[tuple[float, float]] = []
    for relative in RECTANGLE_POINT_RELATIVE:
        x_offset = profile + relative
        y_offset = x_offset + 8
        x = _read_double(blob, x_offset)
        y = _read_double(blob, y_offset)
        if x is None or y is None:
            return None
        point_offsets.append((x_offset, y_offset))
        corners.append((x * _METRES, y * _METRES))
    depth_offset = parameter + DEPTH_RELATIVE
    depth = _read_double(blob, depth_offset)
    if depth is None or depth <= 0.0:
        return None
    reverse_offset = end_spec + REVERSE_RELATIVE
    end_condition_offset = end_spec + END_CONDITION_RELATIVE
    if end_condition_offset >= len(blob):
        return None
    from_end_spec = first_class_offset(records, FROM_END_SPEC_CLASS)
    from_reverse_offset = (
        None if from_end_spec is None else from_end_spec + FROM_REVERSE_RELATIVE
    )
    if from_reverse_offset is not None and from_reverse_offset >= len(blob):
        from_reverse_offset = None
    xs = sorted({round(point[0], 9) for point in corners})
    ys = sorted({round(point[1], 9) for point in corners})
    if len(xs) != 2 or len(ys) != 2:
        return None
    return RectanglePadLayout(
        point_offsets=tuple(point_offsets),
        depth_offset=depth_offset,
        reverse_offset=reverse_offset,
        end_condition_offset=end_condition_offset,
        from_reverse_offset=from_reverse_offset,
        corners_mm=tuple(corners),
        depth_mm=depth * _METRES,
        reversed=bool(blob[reverse_offset]),
        end_condition_code=blob[end_condition_offset],
    )


def sketch_plane_object_id(data: bytes | bytearray) -> int | None:
    blob = bytes(data)
    chain = first_class_offset(class_records(blob), SKETCH_CHAIN_CLASS)
    if chain is None:
        return None
    for offset in range(chain, min(chain + 320, len(blob) - 14)):
        candidate = struct.unpack_from("<I", blob, offset)[0]
        if candidate not in {2, 3, 4}:
            continue
        axis = struct.unpack_from("<I", blob, offset + 10)[0]
        if axis == 5 - candidate:
            return candidate
    return None


def patch_rectangle_pad(
    data: bytes | bytearray,
    *,
    minimum_x_mm: float,
    minimum_y_mm: float,
    maximum_x_mm: float,
    maximum_y_mm: float,
    depth_mm: float,
    reversed: bool = False,
    end_condition_code: int = BLIND_END_CONDITION,
) -> bytes:
    layout = locate_rectangle_pad(data)
    if layout is None:
        raise SldprtFormatError(
            "donor resolved-features stream is not a rectangular pad layout"
        )
    if end_condition_code not in SUPPORTED_END_CONDITIONS:
        raise SldprtFormatError(
            f"unsupported SOLIDWORKS end condition code {end_condition_code}"
        )
    values = (
        minimum_x_mm,
        minimum_y_mm,
        maximum_x_mm,
        maximum_y_mm,
        depth_mm,
    )
    if not all(math.isfinite(value) for value in values):
        raise SldprtFormatError("rectangular pad values must be finite")
    if maximum_x_mm <= minimum_x_mm or maximum_y_mm <= minimum_y_mm:
        raise SldprtFormatError("rectangular pad requires a positive extent")
    if depth_mm <= 0.0:
        raise SldprtFormatError("rectangular pad requires a positive depth")
    corners = rectangle_corners_mm(
        minimum_x_mm, minimum_y_mm, maximum_x_mm, maximum_y_mm
    )
    output = bytearray(data)
    for (x_offset, y_offset), (x, y) in zip(layout.point_offsets, corners, strict=True):
        struct.pack_into("<d", output, x_offset, x / _METRES)
        struct.pack_into("<d", output, y_offset, y / _METRES)
    struct.pack_into("<d", output, layout.depth_offset, depth_mm / _METRES)
    output[layout.reverse_offset] = 1 if reversed else 0
    output[layout.end_condition_offset] = end_condition_code
    if layout.from_reverse_offset is not None:
        output[layout.from_reverse_offset] = 1 if reversed else 0
    patched = bytes(output)
    verification = locate_rectangle_pad(patched)
    if verification is None:
        raise SldprtFormatError("patched resolved-features stream cannot be relocated")
    if not _matches(verification.corners_mm, corners):
        raise SldprtFormatError("patched rectangular pad geometry does not verify")
    if not math.isclose(verification.depth_mm, depth_mm, rel_tol=1e-12, abs_tol=1e-9):
        raise SldprtFormatError("patched rectangular pad depth does not verify")
    if verification.reversed is not bool(reversed):
        raise SldprtFormatError("patched rectangular pad direction does not verify")
    if verification.end_condition_code != end_condition_code:
        raise SldprtFormatError("patched rectangular pad end condition does not verify")
    return patched


def _name_records(blob: bytes, marker: bytes) -> tuple[NameRecord, ...]:
    result: list[NameRecord] = []
    cursor = 0
    while True:
        offset = blob.find(marker, cursor)
        if offset < 0:
            break
        cursor = offset + 1
        units_offset = offset + len(marker)
        if units_offset >= len(blob):
            continue
        units = blob[units_offset]
        text_start = units_offset + 1
        text_end = text_start + units * 2
        if not 1 <= units <= _MAX_NAME_UNITS:
            continue
        if text_end + _NAME_TRAILER_BYTES > len(blob):
            continue
        try:
            text = blob[text_start:text_end].decode("utf-16le")
        except UnicodeDecodeError:
            continue
        if not text or any(not character.isprintable() for character in text):
            continue
        result.append(
            NameRecord(
                offset=offset,
                text_end=text_end,
                name=text,
                flags=struct.unpack_from("<I", blob, text_end + 4)[0],
                feature_id=struct.unpack_from("<I", blob, text_end + 8)[0],
            )
        )
    return tuple(result)


def _tree_nodes(blob: bytes, records: tuple[NameRecord, ...]) -> tuple[NameRecord, ...]:
    return tuple(
        record
        for record in records
        if blob[record.text_end : record.text_end + 4] == bytes(4)
        and 0 < record.feature_id < _MAX_FEATURE_ID
        and record.flags in TREE_NODE_FLAGS
    )


def _dimension_scalars(
    blob: bytes, records: tuple[NameRecord, ...]
) -> tuple[DimensionScalar, ...]:
    result: list[DimensionScalar] = []
    for record in records:
        value_offset = dimension_scalar_value_offset(
            blob, record.text_end, len(blob), trailing_bytes=7
        )
        if value_offset is None:
            continue
        value = _read_double(blob, value_offset)
        if value is None:
            continue
        result.append(
            DimensionScalar(
                name=record.name,
                name_offset=record.offset,
                value_offset=value_offset,
                value_mm=value * _METRES,
            )
        )
    return tuple(result)


def _sketch_point_groups(
    blob: bytes, nodes: tuple[NameRecord, ...]
) -> tuple[tuple[NameRecord, tuple[SketchPoint, ...]], ...]:
    sketches = tuple(
        node
        for node in nodes
        if node.flags == SKETCH_FLAGS and node.name.startswith(SKETCH_NAME_PREFIX)
    )
    points = sketch_points(blob)
    boundaries = tuple(sketch.offset for sketch in sketches[1:]) + (len(blob),)
    return tuple(
        (
            sketch,
            tuple(
                point
                for point in points
                if sketch.offset < point.offset < boundaries[index]
            ),
        )
        for index, sketch in enumerate(sketches)
    )


def _feature_layout(
    blob: bytes,
    ordinal: int,
    feature: NameRecord,
    sketch: NameRecord | None,
    points: tuple[SketchPoint, ...],
    scalar: DimensionScalar | None,
) -> FeatureLayout:
    depth_offset = None if scalar is None else scalar.value_offset
    depth_mm = None if scalar is None else scalar.value_mm
    copies: tuple[int, ...] = ()
    reverse_offset: int | None = None
    end_condition_offset: int | None = None
    if depth_offset is not None:
        copies = tuple(
            depth_offset + delta
            for delta in DEPTH_COPY_DELTAS
            if depth_offset + delta + 8 <= len(blob)
        )
        reverse_distance, end_condition_distance = (
            (FIRST_FEATURE_REVERSE_DISTANCE, FIRST_FEATURE_END_CONDITION_DISTANCE)
            if ordinal == 0
            else (LATER_FEATURE_REVERSE_DISTANCE, LATER_FEATURE_END_CONDITION_DISTANCE)
        )
        reverse_offset = _flag_offset(blob, depth_offset - reverse_distance)
        end_condition_offset = _flag_offset(blob, depth_offset - end_condition_distance)
    return FeatureLayout(
        ordinal=ordinal,
        name=feature.name,
        kind=FEATURE_KIND_BY_FLAGS[feature.flags],
        feature_id=feature.feature_id,
        flags=feature.flags,
        flags_offset=feature.text_end + 4,
        sketch_name=None if sketch is None else sketch.name,
        sketch_id=None if sketch is None else sketch.feature_id,
        points=points,
        depth_offset=depth_offset,
        depth_mm=depth_mm,
        depth_copy_offsets=copies,
        reverse_offset=reverse_offset,
        end_condition_offset=end_condition_offset,
        reversed=None if reverse_offset is None else bool(blob[reverse_offset]),
        end_condition_code=(
            None if end_condition_offset is None else blob[end_condition_offset]
        ),
    )


def _flag_offset(blob: bytes, offset: int) -> int | None:
    return offset if 0 <= offset < len(blob) else None


def _validate_edit(feature: FeatureLayout, edit: FeatureEdit) -> None:
    if edit.corners_mm is not None:
        if len(edit.corners_mm) != len(feature.points):
            raise SldprtFormatError(
                f"feature {feature.ordinal} has {len(feature.points)} sketch points "
                f"and {len(edit.corners_mm)} corners were supplied"
            )
        if not feature.points:
            raise SldprtFormatError(
                f"feature {feature.ordinal} has no locatable sketch points"
            )
        if not all(
            math.isfinite(value) for corner in edit.corners_mm for value in corner
        ):
            raise SldprtFormatError("sketch corner values must be finite")
    if edit.depth_mm is not None:
        if feature.depth_offset is None:
            raise SldprtFormatError(
                f"feature {feature.ordinal} has no dimension scalar to hold a depth"
            )
        if not math.isfinite(edit.depth_mm) or edit.depth_mm <= 0.0:
            raise SldprtFormatError("extrusion depth must be finite and positive")
    if edit.update_depth_copies and edit.depth_mm is None:
        raise SldprtFormatError(
            "depth copies can only be updated together with a depth"
        )
    if edit.reversed is not None and feature.reverse_offset is None:
        raise SldprtFormatError(
            f"feature {feature.ordinal} has no locatable direction flag"
        )
    if edit.end_condition_code is not None:
        if feature.end_condition_offset is None:
            raise SldprtFormatError(
                f"feature {feature.ordinal} has no locatable end condition flag"
            )
        if edit.end_condition_code not in SUPPORTED_END_CONDITIONS:
            raise SldprtFormatError(
                f"unsupported SOLIDWORKS end condition code {edit.end_condition_code}"
            )


def _verify_features(
    patched: bytes,
    features: tuple[FeatureLayout, ...],
    edits: Mapping[int, FeatureEdit],
) -> None:
    verification = locate_features(patched)
    if len(verification) != len(features):
        raise SldprtFormatError("patched resolved-features stream cannot be relocated")
    for ordinal in sorted(edits):
        edit = edits[ordinal]
        before = features[ordinal]
        after = verification[ordinal]
        if (
            after.feature_id != before.feature_id
            or after.kind != before.kind
            or after.depth_offset != before.depth_offset
            or tuple(point.offset for point in after.points)
            != tuple(point.offset for point in before.points)
        ):
            raise SldprtFormatError(
                f"patched feature {ordinal} does not relocate to the same layout"
            )
        if edit.corners_mm is not None and not _matches(
            after.corners_mm, tuple(edit.corners_mm)
        ):
            raise SldprtFormatError(f"patched feature {ordinal} corners do not verify")
        if edit.depth_mm is not None:
            if after.depth_mm is None or not math.isclose(
                after.depth_mm, edit.depth_mm, rel_tol=1e-12, abs_tol=1e-9
            ):
                raise SldprtFormatError(
                    f"patched feature {ordinal} depth does not verify"
                )
            if edit.update_depth_copies and not _depth_copies_verify(
                patched, after, edit.depth_mm
            ):
                raise SldprtFormatError(
                    f"patched feature {ordinal} depth copies do not verify"
                )
        if edit.reversed is not None and after.reversed is not bool(edit.reversed):
            raise SldprtFormatError(
                f"patched feature {ordinal} direction does not verify"
            )
        if (
            edit.end_condition_code is not None
            and after.end_condition_code != edit.end_condition_code
        ):
            raise SldprtFormatError(
                f"patched feature {ordinal} end condition does not verify"
            )


def _depth_copies_verify(
    patched: bytes, feature: FeatureLayout, depth_mm: float
) -> bool:
    for offset, sign in zip(feature.depth_copy_offsets, DEPTH_COPY_SIGNS, strict=False):
        value = _read_double(patched, offset)
        if value is None or not math.isclose(
            value * _METRES, sign * depth_mm, rel_tol=1e-12, abs_tol=1e-9
        ):
            return False
    return True


def _read_double(blob: bytes, offset: int) -> float | None:
    if offset < 0 or offset + 8 > len(blob):
        return None
    value = struct.unpack_from("<d", blob, offset)[0]
    if not math.isfinite(value):
        return None
    return value


def _matches(
    actual: tuple[tuple[float, float], ...],
    expected: tuple[tuple[float, float], ...],
) -> bool:
    if len(actual) != len(expected):
        return False
    return all(
        math.isclose(left, right, rel_tol=1e-12, abs_tol=1e-9)
        for pair, target in zip(actual, expected, strict=True)
        for left, right in zip(pair, target, strict=True)
    )
