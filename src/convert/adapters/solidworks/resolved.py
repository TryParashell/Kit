# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

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
REVOLUTION_CLASS = "moRevolution_c"
REVOLUTION_CUT_CLASS = "moRevCut_c"
REVOLUTION_END_SPEC_CLASS = "moRevEndSpec_c"
ANGLE_PARAMETER_CLASS = "moAngleParameter_c"

DEPTH_RELATIVE = 57
REVERSE_RELATIVE = 27
END_CONDITION_RELATIVE = 33
FROM_REVERSE_RELATIVE = 29
RECTANGLE_POINT_RELATIVE = (283, 461, 623, 785)

BLIND_END_CONDITION = 0
MID_PLANE_END_CONDITION = 6
SUPPORTED_END_CONDITIONS = frozenset({BLIND_END_CONDITION, MID_PLANE_END_CONDITION})

FEATURE_FLAGS_MASK = 0x7FFFFFFF

BOSS_FLAGS = 0x40000140
CUT_FLAGS = 0x400201CA
SKETCH_FLAGS = 0x40000000
PLANE_FLAGS = 0xC0000000
ROUND_FLAGS = 0x40000001
SWEEP_FLAGS = 0x40004003
SWEEP_SINGLE_PROFILE_FLAGS = 0x40004002
LOFT_FLAGS = 0x40004404
BOSS_KIND = "boss"
CUT_KIND = "cut"
ROUND_KIND = "round"
SWEEP_KIND = "sweep"
LOFT_KIND = "loft"
REVOLVE_KIND = "revolve"
REVOLVE_CUT_KIND = "revolve-cut"
REVOLVE_KINDS = frozenset({REVOLVE_KIND, REVOLVE_CUT_KIND})
FEATURE_KIND_BY_FLAGS = MappingProxyType(
    {
        BOSS_FLAGS: BOSS_KIND,
        CUT_FLAGS: CUT_KIND,
        ROUND_FLAGS: ROUND_KIND,
        SWEEP_FLAGS: SWEEP_KIND,
        SWEEP_SINGLE_PROFILE_FLAGS: SWEEP_KIND,
        LOFT_FLAGS: LOFT_KIND,
    }
)
TREE_NODE_FLAGS = frozenset(FEATURE_KIND_BY_FLAGS) | {SKETCH_FLAGS, PLANE_FLAGS}

REVOLUTION_END_SPEC_DATA = (
    struct.pack("<I", 1)
    + bytes(24)
    + struct.pack("<d", 0.01)
    + struct.pack("<d", 0.01)
    + bytes(8)
)
REVOLUTION_END_SPEC_HEADER = (
    CLASS_MARKER
    + struct.pack("<H", len(REVOLUTION_END_SPEC_CLASS))
    + REVOLUTION_END_SPEC_CLASS.encode("ascii")
)
REVOLUTION_END_SPEC_CLASS_BYTES = len(REVOLUTION_END_SPEC_HEADER)
REVOLUTION_CLASS_REFERENCE_BYTES = 2
REVOLUTION_AXIS_SKETCH_RELATIVE = -145
REVOLUTION_AXIS_REFERENCE_RELATIVE = -131
REVOLUTION_AXIS_SKETCH = "sketch"
REVOLUTION_AXIS_REFERENCE = "reference-axis"
REVOLUTION_STAMP_LOW = 1_000_000_000
REVOLUTION_STAMP_HIGH = 2_000_000_000
ANGLE_COPY_DELTAS = (0, 513, 537)
FULL_REVOLUTION_RADIANS = 2.0 * math.pi
_ANGLE_TOLERANCE_RADIANS = 1.0e-9
REVOLVE_CUT_NAME_STEMS = ("cut-revolve", "cortar-revolucion", "cortar-revolución")
REVOLVE_NAME_STEMS = ("revolve", "revolucion", "revolución")
_RADIANS_TO_DEGREES = 180.0 / math.pi

SKETCH_COORDINATE_PREFIX = bytes.fromhex("000000000000f03f00000000000000001e00")
SKETCH_POINT_PREFIX = SKETCH_COORDINATE_PREFIX
SKETCH_FREE_ROLE = 0
SKETCH_ON_CURVE_ROLE = 2
SKETCH_POINT_CLASS = 2
SKETCH_POINT_SUFFIX = bytes((SKETCH_FREE_ROLE, 0, SKETCH_POINT_CLASS, 0))
SKETCH_NAME_PREFIX = "Sketch"
DEPTH_SCALAR_NAME_PREFIX = "D"

DEPTH_COPY_DELTAS = (0, 72, 398, 422, 560, 584)
DEPTH_COPY_SIGNS = (1, 1, -1, -1, 1, 1)

FIRST_FEATURE_REVERSE_DISTANCE = 824
FIRST_FEATURE_END_CONDITION_DISTANCE = 818
LATER_FEATURE_REVERSE_DISTANCE = 721
LATER_FEATURE_END_CONDITION_DISTANCE = 715

CIRCLE_POINT_ANGLE_DEGREES = 17.0
CIRCLE_POINT_ANGLE_TOLERANCE_DEGREES = 1.0e-6
FULL_CIRCLE_DEGREES = 360.0

SKETCH_ARC_CENTRE_CLASS = 1
_ARC_RADIUS_TOLERANCE_MM = 1.0e-6

_NAME_MARKER_CLASS_TOKEN = 0x8004
_MAX_CLASS_NAME = 64
_MAX_NAME_UNITS = 128
_MAX_FEATURE_ID = 4096
_NAME_TRAILER_BYTES = 12
_METRES = 1000.0
_COORDINATE_TRAILER_BYTES = 4
_MINIMUM_RADIUS_MM = 1.0e-9


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
class SketchCoordinate:
    offset: int
    x_mm: float
    y_mm: float
    role: int
    geometry_class: int


@dataclass(frozen=True, slots=True)
class SketchArc:
    centre_offset: int
    point_offset: int
    centre_x_mm: float
    centre_y_mm: float
    radius_mm: float
    start_angle_degrees: float
    sweep_angle_degrees: float

    @property
    def centre_mm(self) -> tuple[float, float]:
        return self.centre_x_mm, self.centre_y_mm

    @property
    def full_circle(self) -> bool:
        return self.sweep_angle_degrees == FULL_CIRCLE_DEGREES


@dataclass(frozen=True, slots=True)
class SweptArc:
    centre_offset: int
    start_offset: int
    end_offset: int
    centre_x_mm: float
    centre_y_mm: float
    start_x_mm: float
    start_y_mm: float
    end_x_mm: float
    end_y_mm: float

    @property
    def centre_mm(self) -> tuple[float, float]:
        return self.centre_x_mm, self.centre_y_mm

    @property
    def start_mm(self) -> tuple[float, float]:
        return self.start_x_mm, self.start_y_mm

    @property
    def end_mm(self) -> tuple[float, float]:
        return self.end_x_mm, self.end_y_mm

    @property
    def radius_mm(self) -> float:
        return math.hypot(
            self.start_x_mm - self.centre_x_mm, self.start_y_mm - self.centre_y_mm
        )

    @property
    def end_radius_mm(self) -> float:
        return math.hypot(
            self.end_x_mm - self.centre_x_mm, self.end_y_mm - self.centre_y_mm
        )

    @property
    def consistent(self) -> bool:
        radius = self.radius_mm
        if radius <= _MINIMUM_RADIUS_MM:
            return False
        return abs(self.end_radius_mm - radius) <= max(
            _ARC_RADIUS_TOLERANCE_MM, radius * 1.0e-9
        )

    @property
    def start_angle_degrees(self) -> float:
        return math.degrees(
            math.atan2(
                self.start_y_mm - self.centre_y_mm, self.start_x_mm - self.centre_x_mm
            )
        )

    @property
    def end_angle_degrees(self) -> float:
        return math.degrees(
            math.atan2(
                self.end_y_mm - self.centre_y_mm, self.end_x_mm - self.centre_x_mm
            )
        )

    def sweep_angle_degrees(self, counterclockwise: bool) -> float:
        span = self.end_angle_degrees - self.start_angle_degrees
        if not counterclockwise:
            span = -span
        while span <= 0.0:
            span += FULL_CIRCLE_DEGREES
        while span > FULL_CIRCLE_DEGREES:
            span -= FULL_CIRCLE_DEGREES
        return span


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
    arcs: tuple[SketchArc, ...]
    depth_offset: int | None
    depth_mm: float | None
    depth_copy_offsets: tuple[int, ...]
    reverse_offset: int | None
    end_condition_offset: int | None
    reversed: bool | None
    end_condition_code: int | None
    from_reverse_offset: int | None = None
    angle_offset: int | None = None
    angle_radians: float | None = None
    angle_copy_offsets: tuple[int, ...] = ()
    end_spec_offset: int | None = None
    axis_kind: str | None = None
    axis_offset: int | None = None
    axis_feature_id: int | None = None
    swept_arcs: tuple[SweptArc, ...] = ()

    @property
    def is_revolution(self) -> bool:
        return self.kind in REVOLVE_KINDS

    @property
    def angle_degrees(self) -> float | None:
        if self.angle_radians is None:
            return None
        return self.angle_radians * _RADIANS_TO_DEGREES

    @property
    def corners_mm(self) -> tuple[tuple[float, float], ...]:
        return tuple((point.x_mm, point.y_mm) for point in self.points)

    @property
    def radii_mm(self) -> tuple[float, ...]:
        return tuple(arc.radius_mm for arc in self.arcs)

    @property
    def bounds_mm(self) -> tuple[float, float, float, float] | None:
        if self.points:
            xs = tuple(point.x_mm for point in self.points)
            ys = tuple(point.y_mm for point in self.points)
            return min(xs), min(ys), max(xs), max(ys)
        if self.arcs:
            xs = tuple(
                value
                for arc in self.arcs
                for value in (
                    arc.centre_x_mm - arc.radius_mm,
                    arc.centre_x_mm + arc.radius_mm,
                )
            )
            ys = tuple(
                value
                for arc in self.arcs
                for value in (
                    arc.centre_y_mm - arc.radius_mm,
                    arc.centre_y_mm + arc.radius_mm,
                )
            )
            return min(xs), min(ys), max(xs), max(ys)
        return None


@dataclass(frozen=True, slots=True)
class FeatureEdit:
    corners_mm: Sequence[tuple[float, float]] | None = None
    depth_mm: float | None = None
    reversed: bool | None = None
    end_condition_code: int | None = None
    update_depth_copies: bool = False
    radii_mm: Sequence[float] | None = None
    arc_centres_mm: Sequence[tuple[float, float]] | None = None
    angle_radians: float | None = None
    swept_arc_centres_mm: Sequence[tuple[float, float]] | None = None


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


def feature_kind(flags: int) -> str | None:
    return FEATURE_KIND_BY_FLAGS.get(flags & FEATURE_FLAGS_MASK)


def revolution_end_spec_objects(data: bytes | bytearray) -> tuple[int, ...]:
    blob = bytes(data)
    result: list[int] = []
    cursor = 0
    while True:
        found = blob.find(REVOLUTION_END_SPEC_DATA, cursor)
        if found < 0:
            break
        cursor = found + 1
        header = found - REVOLUTION_END_SPEC_CLASS_BYTES
        if header >= 0 and blob[header:found] == REVOLUTION_END_SPEC_HEADER:
            result.append(header)
            continue
        result.append(found - REVOLUTION_CLASS_REFERENCE_BYTES)
    return tuple(result)


def revolution_axis_source(
    data: bytes | bytearray, token: int, feature_ids: frozenset[int]
) -> tuple[str, int, int] | None:
    blob = bytes(data)
    for kind, relative in (
        (REVOLUTION_AXIS_SKETCH, REVOLUTION_AXIS_SKETCH_RELATIVE),
        (REVOLUTION_AXIS_REFERENCE, REVOLUTION_AXIS_REFERENCE_RELATIVE),
    ):
        offset = token + relative
        if offset < 0 or offset + 8 > len(blob):
            continue
        identifier = struct.unpack_from("<I", blob, offset)[0]
        stamp = struct.unpack_from("<I", blob, offset + 4)[0]
        if identifier not in feature_ids:
            continue
        if not REVOLUTION_STAMP_LOW <= stamp <= REVOLUTION_STAMP_HIGH:
            continue
        return kind, offset, identifier
    return None


def revolution_kind_by_name(name: str, boss: bool, cut: bool) -> str:
    folded = name.casefold()
    if cut and any(folded.startswith(stem) for stem in REVOLVE_CUT_NAME_STEMS):
        return REVOLVE_CUT_KIND
    if boss and any(folded.startswith(stem) for stem in REVOLVE_NAME_STEMS):
        return REVOLVE_KIND
    if cut and not boss:
        return REVOLVE_CUT_KIND
    return REVOLVE_KIND


def is_tree_node_flags(flags: int) -> bool:
    return flags & FEATURE_FLAGS_MASK in TREE_NODE_FLAGS


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


def sketch_coordinates(data: bytes | bytearray) -> tuple[SketchCoordinate, ...]:
    blob = bytes(data)
    result: list[SketchCoordinate] = []
    cursor = 0
    while True:
        offset = blob.find(SKETCH_COORDINATE_PREFIX, cursor)
        if offset < 0:
            break
        cursor = offset + 1
        start = offset + len(SKETCH_COORDINATE_PREFIX)
        trailer_end = start + 16 + _COORDINATE_TRAILER_BYTES
        if trailer_end > len(blob):
            continue
        trailer = blob[start + 16 : trailer_end]
        if trailer[1] or trailer[3]:
            continue
        x = _read_double(blob, start)
        y = _read_double(blob, start + 8)
        if x is None or y is None:
            continue
        result.append(
            SketchCoordinate(
                offset=start,
                x_mm=x * _METRES,
                y_mm=y * _METRES,
                role=trailer[0],
                geometry_class=trailer[2],
            )
        )
    return tuple(result)


def sketch_points(data: bytes | bytearray) -> tuple[SketchPoint, ...]:
    return tuple(
        SketchPoint(
            offset=coordinate.offset, x_mm=coordinate.x_mm, y_mm=coordinate.y_mm
        )
        for coordinate in sketch_coordinates(data)
        if coordinate.role == SKETCH_FREE_ROLE
        and coordinate.geometry_class == SKETCH_POINT_CLASS
    )


def sketch_arcs(data: bytes | bytearray) -> tuple[SketchArc, ...]:
    coordinates = sketch_coordinates(data)
    result: list[SketchArc] = []
    for centre, point in zip(coordinates, coordinates[1:], strict=False):
        if (
            point.role != SKETCH_ON_CURVE_ROLE
            or point.geometry_class != SKETCH_POINT_CLASS
        ):
            continue
        arc = _sketch_arc(centre, point)
        if arc is not None:
            result.append(arc)
    return tuple(result)


def swept_arcs(data: bytes | bytearray) -> tuple[SweptArc, ...]:
    coordinates = sketch_coordinates(data)
    circle_centres = {arc.centre_offset for arc in sketch_arcs(data)}
    result: list[SweptArc] = []
    for index, centre in enumerate(coordinates):
        if (
            centre.role != SKETCH_FREE_ROLE
            or centre.geometry_class != SKETCH_ARC_CENTRE_CLASS
            or centre.offset in circle_centres
        ):
            continue
        run: list[SketchCoordinate] = []
        cursor = index - 1
        while cursor >= 0:
            candidate = coordinates[cursor]
            if (
                candidate.role != SKETCH_FREE_ROLE
                or candidate.geometry_class != SKETCH_POINT_CLASS
            ):
                break
            run.append(candidate)
            cursor -= 1
        if len(run) < 2:
            continue
        start = run[0]
        end = run[-1]
        arc = SweptArc(
            centre_offset=centre.offset,
            start_offset=start.offset,
            end_offset=end.offset,
            centre_x_mm=centre.x_mm,
            centre_y_mm=centre.y_mm,
            start_x_mm=start.x_mm,
            start_y_mm=start.y_mm,
            end_x_mm=end.x_mm,
            end_y_mm=end.y_mm,
        )
        if arc.consistent:
            result.append(arc)
    return tuple(result)


def patch_sketch_arcs(data: bytes | bytearray, radii_mm: Mapping[int, float]) -> bytes:
    arcs = sketch_arcs(data)
    unknown = sorted(set(radii_mm) - set(range(len(arcs))))
    if unknown:
        raise SldprtFormatError(
            f"resolved-features stream has no sketch arc at indices {unknown}"
        )
    output = bytearray(data)
    for index in sorted(radii_mm):
        _write_arc_radius(output, arcs[index], radii_mm[index])
    patched = bytes(output)
    verification = sketch_arcs(patched)
    if len(verification) != len(arcs):
        raise SldprtFormatError("patched resolved-features stream cannot be relocated")
    for index, radius_mm in sorted(radii_mm.items()):
        _verify_arc(verification[index], arcs[index], radius_mm, index)
    return patched


def locate_features(data: bytes | bytearray) -> tuple[FeatureLayout, ...]:
    blob = bytes(data)
    records = name_records(blob)
    nodes = _tree_nodes(blob, records)
    classes = class_records(blob)
    revolutions = _revolution_nodes(blob, nodes, classes)
    features = tuple(
        node
        for node in nodes
        if feature_kind(node.flags) is not None or node.offset in revolutions
    )
    profiles = tuple(
        node
        for node in nodes
        if feature_kind(node.flags) is None and node.offset not in revolutions
    )
    from_end_spec = first_class_offset(classes, FROM_END_SPEC_CLASS)
    from_reverse = (
        None if from_end_spec is None else from_end_spec + FROM_REVERSE_RELATIVE
    )
    if from_reverse is not None and from_reverse >= len(blob):
        from_reverse = None
    points = sketch_points(blob)
    arcs = sketch_arcs(blob)
    swept = swept_arcs(blob)
    scalars = tuple(
        scalar
        for scalar in _dimension_scalars(blob, records)
        if scalar.name.startswith(DEPTH_SCALAR_NAME_PREFIX)
    )
    result: list[FeatureLayout] = []
    extrusions = 0
    for ordinal, feature in enumerate(features):
        start = features[ordinal - 1].offset if ordinal else 0
        limit = (
            features[ordinal + 1].offset if ordinal + 1 < len(features) else len(blob)
        )
        sketch = _last_node_in_range(profiles, start, feature.offset)
        scalar = next(
            (
                candidate
                for candidate in scalars
                if feature.offset < candidate.value_offset < limit
            ),
            None,
        )
        revolution = revolutions.get(feature.offset)
        if revolution is not None:
            result.append(
                _revolution_layout(
                    blob,
                    ordinal,
                    feature,
                    sketch,
                    scalar,
                    revolution,
                    () if sketch is None else _points_in_range(points, sketch, feature),
                    () if sketch is None else _arcs_in_range(arcs, sketch, feature),
                    swept_arcs=(
                        ()
                        if sketch is None
                        else _swept_in_range(swept, sketch, feature)
                    ),
                )
            )
            continue
        result.append(
            _feature_layout(
                blob,
                ordinal,
                extrusions,
                feature,
                sketch,
                () if sketch is None else _points_in_range(points, sketch, feature),
                () if sketch is None else _arcs_in_range(arcs, sketch, feature),
                scalar,
                from_reverse if extrusions == 0 else None,
                swept_arcs=(
                    () if sketch is None else _swept_in_range(swept, sketch, feature)
                ),
            )
        )
        extrusions += 1
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
        if edit.arc_centres_mm is not None:
            for arc, (x, y) in zip(feature.arcs, edit.arc_centres_mm, strict=True):
                struct.pack_into("<d", output, arc.centre_offset, x / _METRES)
                struct.pack_into("<d", output, arc.centre_offset + 8, y / _METRES)
        if edit.radii_mm is not None:
            for arc, radius_mm in zip(feature.arcs, edit.radii_mm, strict=True):
                _write_arc_radius(output, arc, radius_mm)
        if edit.swept_arc_centres_mm is not None:
            for arc, centre in zip(
                feature.swept_arcs, edit.swept_arc_centres_mm, strict=True
            ):
                struct.pack_into("<d", output, arc.centre_offset, centre[0] / _METRES)
                struct.pack_into(
                    "<d", output, arc.centre_offset + 8, centre[1] / _METRES
                )
        if edit.angle_radians is not None:
            struct.pack_into("<d", output, feature.angle_offset, edit.angle_radians)
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
            if feature.from_reverse_offset is not None:
                output[feature.from_reverse_offset] = 1 if edit.reversed else 0
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
        and is_tree_node_flags(record.flags)
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


def _sketch_arc(centre: SketchCoordinate, point: SketchCoordinate) -> SketchArc | None:
    dx = point.x_mm - centre.x_mm
    dy = point.y_mm - centre.y_mm
    radius = math.hypot(dx, dy)
    if radius <= _MINIMUM_RADIUS_MM:
        return None
    angle = math.degrees(math.atan2(dy, dx))
    if abs(angle - CIRCLE_POINT_ANGLE_DEGREES) > CIRCLE_POINT_ANGLE_TOLERANCE_DEGREES:
        return None
    return SketchArc(
        centre_offset=centre.offset,
        point_offset=point.offset,
        centre_x_mm=centre.x_mm,
        centre_y_mm=centre.y_mm,
        radius_mm=radius,
        start_angle_degrees=angle,
        sweep_angle_degrees=FULL_CIRCLE_DEGREES,
    )


def _write_arc_radius(output: bytearray, arc: SketchArc, radius_mm: float) -> None:
    if not math.isfinite(radius_mm) or radius_mm <= 0.0:
        raise SldprtFormatError("circular profile requires a positive finite radius")
    x_mm, y_mm = circle_circumference_point_mm(radius_mm)
    centre_x = struct.unpack_from("<d", output, arc.centre_offset)[0]
    centre_y = struct.unpack_from("<d", output, arc.centre_offset + 8)[0]
    struct.pack_into("<d", output, arc.point_offset, centre_x + x_mm / _METRES)
    struct.pack_into("<d", output, arc.point_offset + 8, centre_y + y_mm / _METRES)


def _verify_arc(
    after: SketchArc, before: SketchArc, radius_mm: float, index: int
) -> None:
    if (
        after.centre_offset != before.centre_offset
        or after.point_offset != before.point_offset
    ):
        raise SldprtFormatError(
            f"patched sketch arc {index} does not relocate to the same layout"
        )
    if not math.isclose(after.radius_mm, radius_mm, rel_tol=1e-12, abs_tol=1e-9):
        raise SldprtFormatError(f"patched sketch arc {index} radius does not verify")


def _last_node_in_range(
    nodes: tuple[NameRecord, ...], start: int, limit: int
) -> NameRecord | None:
    candidates = tuple(node for node in nodes if start < node.offset < limit)
    return candidates[-1] if candidates else None


def _points_in_range(
    points: tuple[SketchPoint, ...], sketch: NameRecord, feature: NameRecord
) -> tuple[SketchPoint, ...]:
    return tuple(
        point for point in points if sketch.offset < point.offset < feature.offset
    )


def _arcs_in_range(
    arcs: tuple[SketchArc, ...], sketch: NameRecord, feature: NameRecord
) -> tuple[SketchArc, ...]:
    return tuple(
        arc for arc in arcs if sketch.offset < arc.centre_offset < feature.offset
    )


def _swept_in_range(
    arcs: tuple[SweptArc, ...], sketch: NameRecord, feature: NameRecord
) -> tuple[SweptArc, ...]:
    return tuple(
        arc
        for arc in arcs
        if sketch.offset < arc.centre_offset < feature.offset
        and sketch.offset < arc.start_offset < feature.offset
        and sketch.offset < arc.end_offset < feature.offset
    )


def _revolution_nodes(
    blob: bytes,
    nodes: tuple[NameRecord, ...],
    classes: tuple[ClassRecord, ...],
) -> dict[int, tuple[str, int, tuple[str, int, int] | None]]:
    names = {record.name for record in classes}
    boss = REVOLUTION_CLASS in names
    cut = REVOLUTION_CUT_CLASS in names
    if not boss and not cut:
        return {}
    tokens = revolution_end_spec_objects(blob)
    if not tokens:
        return {}
    feature_ids = frozenset(node.feature_id for node in nodes)
    candidates = tuple(
        node
        for node in nodes
        if feature_kind(node.flags) is None
        and node.flags & FEATURE_FLAGS_MASK == SKETCH_FLAGS
    )
    result: dict[int, tuple[str, int, tuple[str, int, int] | None]] = {}
    for token in sorted(tokens):
        node = _last_node_in_range(candidates, -1, token)
        if node is None or node.offset in result:
            continue
        result[node.offset] = (
            revolution_kind_by_name(node.name, boss, cut),
            token,
            revolution_axis_source(blob, token, feature_ids),
        )
    return result


def _revolution_layout(
    blob: bytes,
    ordinal: int,
    feature: NameRecord,
    sketch: NameRecord | None,
    scalar: DimensionScalar | None,
    revolution: tuple[str, int, tuple[str, int, int] | None],
    points: tuple[SketchPoint, ...],
    arcs: tuple[SketchArc, ...],
    *,
    swept_arcs: tuple[SweptArc, ...] = (),
) -> FeatureLayout:
    kind, token, axis = revolution
    angle_offset = None if scalar is None else scalar.value_offset
    return FeatureLayout(
        ordinal=ordinal,
        name=feature.name,
        kind=kind,
        feature_id=feature.feature_id,
        flags=feature.flags,
        flags_offset=feature.text_end + 4,
        sketch_name=None if sketch is None else sketch.name,
        sketch_id=None if sketch is None else sketch.feature_id,
        points=points,
        arcs=arcs,
        swept_arcs=swept_arcs,
        depth_offset=None,
        depth_mm=None,
        depth_copy_offsets=(),
        reverse_offset=None,
        end_condition_offset=None,
        reversed=None,
        end_condition_code=None,
        angle_offset=angle_offset,
        angle_radians=(
            None if angle_offset is None else _read_double(blob, angle_offset)
        ),
        angle_copy_offsets=(
            ()
            if angle_offset is None
            else tuple(
                angle_offset + delta
                for delta in ANGLE_COPY_DELTAS
                if angle_offset + delta + 8 <= len(blob)
            )
        ),
        end_spec_offset=token,
        axis_kind=None if axis is None else axis[0],
        axis_offset=None if axis is None else axis[1],
        axis_feature_id=None if axis is None else axis[2],
    )


def _feature_layout(
    blob: bytes,
    ordinal: int,
    extrusion_ordinal: int,
    feature: NameRecord,
    sketch: NameRecord | None,
    points: tuple[SketchPoint, ...],
    arcs: tuple[SketchArc, ...],
    scalar: DimensionScalar | None,
    from_reverse_offset: int | None,
    *,
    swept_arcs: tuple[SweptArc, ...] = (),
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
            if extrusion_ordinal == 0
            else (LATER_FEATURE_REVERSE_DISTANCE, LATER_FEATURE_END_CONDITION_DISTANCE)
        )
        reverse_offset = _flag_offset(blob, depth_offset - reverse_distance)
        end_condition_offset = _flag_offset(blob, depth_offset - end_condition_distance)
    kind = feature_kind(feature.flags)
    if kind is None:
        raise SldprtFormatError(
            f"tree node {feature.name!r} is not a recognised feature"
        )
    return FeatureLayout(
        ordinal=ordinal,
        name=feature.name,
        kind=kind,
        feature_id=feature.feature_id,
        flags=feature.flags,
        flags_offset=feature.text_end + 4,
        sketch_name=None if sketch is None else sketch.name,
        sketch_id=None if sketch is None else sketch.feature_id,
        points=points,
        arcs=arcs,
        depth_offset=depth_offset,
        depth_mm=depth_mm,
        depth_copy_offsets=copies,
        reverse_offset=reverse_offset,
        end_condition_offset=end_condition_offset,
        reversed=None if reverse_offset is None else bool(blob[reverse_offset]),
        end_condition_code=(
            None if end_condition_offset is None else blob[end_condition_offset]
        ),
        from_reverse_offset=from_reverse_offset,
        swept_arcs=swept_arcs,
    )


def _flag_offset(blob: bytes, offset: int) -> int | None:
    return offset if 0 <= offset < len(blob) else None


def _validate_revolution_edit(feature: FeatureLayout, edit: FeatureEdit) -> None:
    if edit.depth_mm is not None or edit.update_depth_copies:
        raise SldprtFormatError(
            f"feature {feature.ordinal} is a {feature.kind} and carries an angle, "
            f"not a depth"
        )
    if edit.reversed is not None:
        raise SldprtFormatError(
            f"feature {feature.ordinal} is a {feature.kind} and its direction flag "
            f"is not located, so a direction cannot be written"
        )
    if edit.end_condition_code is not None:
        raise SldprtFormatError(
            f"feature {feature.ordinal} is a {feature.kind} and its end "
            f"specification is a constant, so an end condition cannot be written"
        )
    if edit.angle_radians is None:
        return
    if feature.angle_offset is None:
        raise SldprtFormatError(
            f"feature {feature.ordinal} has no dimension scalar to hold an angle"
        )
    if (
        not math.isfinite(edit.angle_radians)
        or edit.angle_radians <= 0.0
        or edit.angle_radians > FULL_REVOLUTION_RADIANS + _ANGLE_TOLERANCE_RADIANS
    ):
        raise SldprtFormatError(
            "revolution angle must be finite and inside (0, 2*pi] radians"
        )


def _validate_edit(feature: FeatureLayout, edit: FeatureEdit) -> None:
    if feature.is_revolution:
        _validate_revolution_edit(feature, edit)
    elif edit.angle_radians is not None:
        raise SldprtFormatError(
            f"feature {feature.ordinal} is a {feature.kind} and carries a depth, "
            f"not a revolution angle"
        )
    if edit.reversed is not None and feature.reverse_offset is None:
        raise SldprtFormatError(
            f"feature {feature.ordinal} has no locatable direction flag"
        )
    if edit.end_condition_code is not None and feature.end_condition_offset is None:
        raise SldprtFormatError(
            f"feature {feature.ordinal} has no locatable end condition"
        )
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
    if edit.radii_mm is not None:
        if not feature.arcs:
            raise SldprtFormatError(
                f"feature {feature.ordinal} has no locatable sketch arcs"
            )
        if len(edit.radii_mm) != len(feature.arcs):
            raise SldprtFormatError(
                f"feature {feature.ordinal} has {len(feature.arcs)} sketch arcs "
                f"and {len(edit.radii_mm)} radii were supplied"
            )
        if not all(math.isfinite(radius) and radius > 0.0 for radius in edit.radii_mm):
            raise SldprtFormatError("sketch radii must be finite and positive")
    if edit.arc_centres_mm is not None:
        if edit.radii_mm is None:
            raise SldprtFormatError(
                "sketch arc centres can only be moved together with their radii"
            )
        if len(edit.arc_centres_mm) != len(feature.arcs):
            raise SldprtFormatError(
                f"feature {feature.ordinal} has {len(feature.arcs)} sketch arcs "
                f"and {len(edit.arc_centres_mm)} centres were supplied"
            )
        if not all(
            math.isfinite(value) for centre in edit.arc_centres_mm for value in centre
        ):
            raise SldprtFormatError("sketch arc centre values must be finite")
    if edit.swept_arc_centres_mm is not None:
        if not feature.swept_arcs:
            raise SldprtFormatError(
                f"feature {feature.ordinal} has no locatable swept sketch arcs"
            )
        if len(edit.swept_arc_centres_mm) != len(feature.swept_arcs):
            raise SldprtFormatError(
                f"feature {feature.ordinal} has {len(feature.swept_arcs)} swept "
                f"sketch arcs and {len(edit.swept_arc_centres_mm)} centres were "
                f"supplied"
            )
        if not all(
            math.isfinite(value)
            for centre in edit.swept_arc_centres_mm
            for value in centre
        ):
            raise SldprtFormatError("swept sketch arc centre values must be finite")
        if edit.corners_mm is None:
            raise SldprtFormatError(
                "swept sketch arc centres can only be moved together with the "
                "profile vertices that carry their endpoints"
            )
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
            or after.angle_offset != before.angle_offset
            or tuple(point.offset for point in after.points)
            != tuple(point.offset for point in before.points)
            or tuple(arc.centre_offset for arc in after.arcs)
            != tuple(arc.centre_offset for arc in before.arcs)
            or tuple(arc.centre_offset for arc in after.swept_arcs)
            != tuple(arc.centre_offset for arc in before.swept_arcs)
        ):
            raise SldprtFormatError(
                f"patched feature {ordinal} does not relocate to the same layout"
            )
        if edit.swept_arc_centres_mm is not None:
            if not _matches(
                tuple(arc.centre_mm for arc in after.swept_arcs),
                tuple(edit.swept_arc_centres_mm),
            ):
                raise SldprtFormatError(
                    f"patched feature {ordinal} swept arc centres do not verify"
                )
            for index, arc in enumerate(after.swept_arcs):
                if not arc.consistent:
                    raise SldprtFormatError(
                        f"patched feature {ordinal} swept arc {index} endpoints are "
                        f"not equidistant from its centre"
                    )
        if edit.corners_mm is not None and not _matches(
            after.corners_mm, tuple(edit.corners_mm)
        ):
            raise SldprtFormatError(f"patched feature {ordinal} corners do not verify")
        if edit.radii_mm is not None:
            for index, (arc, radius_mm) in enumerate(
                zip(after.arcs, edit.radii_mm, strict=True)
            ):
                _verify_arc(arc, before.arcs[index], radius_mm, index)
        if edit.arc_centres_mm is not None and not _matches(
            tuple(arc.centre_mm for arc in after.arcs), tuple(edit.arc_centres_mm)
        ):
            raise SldprtFormatError(
                f"patched feature {ordinal} arc centres do not verify"
            )
        if edit.angle_radians is not None and (
            after.angle_radians is None
            or not math.isclose(
                after.angle_radians, edit.angle_radians, rel_tol=1e-12, abs_tol=1e-12
            )
        ):
            raise SldprtFormatError(f"patched feature {ordinal} angle does not verify")
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
        if edit.reversed is not None:
            if after.reversed is not bool(edit.reversed):
                raise SldprtFormatError(
                    f"patched feature {ordinal} direction does not verify"
                )
            mirror = after.from_reverse_offset
            if mirror is not None and bool(patched[mirror]) is not bool(edit.reversed):
                raise SldprtFormatError(
                    f"patched feature {ordinal} mirrored direction does not verify"
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
