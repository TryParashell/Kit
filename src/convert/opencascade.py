# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from dataclasses import dataclass
from itertools import chain
from math import isclose, isfinite, sqrt
import re
from sys import float_info
from typing import Any, Mapping

from interchange import (
    BrepBody,
    BrepCoedge,
    BrepCurve,
    BrepEdge,
    BrepFace,
    BrepFaceUse,
    BrepLoop,
    BrepModel,
    BrepRegion,
    BrepShell,
    BrepShellUse,
    BrepSurface,
    BrepVertex,
    CircleCurve,
    CylinderSurface,
    LineCurve,
    PlaneSurface,
    Vector3,
)

_MAX_BYTES = 128 * 1024 * 1024
_MAX_GEOMETRY = 300_000
_MAX_SHAPES = 500_000
_MAX_TOKENS = 12_000_000
_MIN_INT32 = -(2**31)
_MAX_INT32 = 2**31 - 1
_TOKEN_PATTERN = re.compile(rb"\S+")
_INTEGER_PATTERN = re.compile(rb"[+-]?\d+")
_FLAGS_PATTERN = re.compile(rb"[01]{7}")
_CONTINUITY_PATTERN = re.compile(rb"C0|G1|C1|G2|C2|C3|CN")
_INDEXED_CONTINUITY_PATTERN = re.compile(rb"([1-9]\d*)(C0|G1|C1|G2|C2|C3|CN)")
_VERSION_LINE = b"CASCADE Topology V1, (c) Matra-Datavision"
_VERSION_LINES = frozenset(
    {
        _VERSION_LINE,
        b"CASCADE Topology V2, (c) Matra-Datavision",
        b"CASCADE Topology V3, (c) Open Cascade",
    }
)
_SHAPE_TYPES = frozenset({b"Ve", b"Ed", b"Wi", b"Fa", b"Sh", b"So", b"CS", b"Co"})
_SHAPE_CHILD_TYPES = {
    b"Ve": frozenset(),
    b"Ed": frozenset({b"Ve"}),
    b"Wi": frozenset({b"Ed"}),
    b"Fa": frozenset({b"Wi"}),
    b"Sh": frozenset({b"Fa"}),
    b"So": frozenset({b"Sh"}),
    b"CS": frozenset({b"So"}),
    b"Co": _SHAPE_TYPES,
}
_MAX_RECURSION = 64


class _DecodeFailure(ValueError):
    __slots__ = ()


class _Tokens:
    __slots__ = ("_data", "_iterator", "_lookahead", "_last_end", "count")

    def __init__(self, data: bytes) -> None:
        self._data = data
        self._iterator = iter(_TOKEN_PATTERN.finditer(data))
        self._lookahead: re.Match[bytes] | None = None
        self._last_end = 0
        self.count = 0

    def take(self) -> bytes:
        if self._lookahead is None:
            try:
                match = next(self._iterator)
            except StopIteration as exc:
                raise _DecodeFailure("unexpected end of BRep data") from exc
        else:
            match = self._lookahead
            self._lookahead = None
        token = match.group(0)
        self._last_end = match.end()
        self.count += 1
        if self.count > _MAX_TOKENS or len(token) > 128:
            raise _DecodeFailure("BRep token bounds exceeded")
        return token

    def peek(self) -> bytes | None:
        if self._lookahead is None:
            try:
                self._lookahead = next(self._iterator)
            except StopIteration:
                return None
        return self._lookahead.group(0)

    def face_triangulation_starts_next_line(self) -> bool:
        current_end = self._data.find(b"\n", self._last_end)
        if current_end < 0:
            return False
        current_tail = self._data[self._last_end : current_end]
        if re.fullmatch(rb"[ \t]*\r?", current_tail) is None:
            return False
        next_start = current_end + 1
        next_end = self._data.find(b"\n", next_start)
        if next_end < 0:
            next_end = len(self._data)
        line = self._data[next_start:next_end]
        return re.fullmatch(rb"2[ \t]+[1-9]\d*[ \t]*\r?", line) is not None

    def expect(self, expected: bytes) -> None:
        if self.take() != expected:
            raise _DecodeFailure("unexpected BRep token")

    def integer(self, minimum: int = 0, maximum: int = _MAX_SHAPES) -> int:
        token = self.take()
        if _INTEGER_PATTERN.fullmatch(token) is None:
            raise _DecodeFailure("invalid BRep integer")
        value = int(token)
        if value < minimum or value > maximum:
            raise _DecodeFailure("BRep integer is out of bounds")
        return value

    def signed_integer(
        self, minimum: int = -_MAX_SHAPES, maximum: int = _MAX_SHAPES
    ) -> int:
        token = self.take()
        if _INTEGER_PATTERN.fullmatch(token) is None:
            raise _DecodeFailure("invalid BRep integer")
        value = int(token)
        if value < minimum or value > maximum:
            raise _DecodeFailure("BRep integer is out of bounds")
        return value

    def number(self) -> float:
        token = self.take()
        if len(token) > 30:
            raise _DecodeFailure("BRep number is out of bounds")
        try:
            value = float(token)
        except ValueError as exc:
            raise _DecodeFailure("invalid BRep number") from exc
        if not isfinite(value):
            raise _DecodeFailure("non-finite BRep number")
        return value


@dataclass(frozen=True, slots=True)
class _Reference:
    orientation: str
    record: int
    location: int = 0


@dataclass(frozen=True, slots=True)
class _VertexData:
    tolerance: float
    point: Vector3


# edge records retain curve placements until topology placements are composed
@dataclass(frozen=True, slots=True)
class _EdgeData:
    tolerance: float
    curve: int
    first: float
    last: float
    location: int = 0


# face records retain surface placements until topology placements are composed
@dataclass(frozen=True, slots=True)
class _FaceData:
    natural: bool
    tolerance: float
    surface: int
    location: int = 0


@dataclass(frozen=True, slots=True)
class _ShapeRecord:
    kind: bytes
    flags: str
    children: tuple[_Reference, ...]
    geometry: _VertexData | _EdgeData | _FaceData | None


def _vector(tokens: _Tokens) -> Vector3:
    return Vector3(tokens.number(), tokens.number(), tokens.number())


def _dot(left: Vector3, right: Vector3) -> float:
    return left.x * right.x + left.y * right.y + left.z * right.z


def _length(value: Vector3) -> float:
    return sqrt(_dot(value, value))


def _cross(left: Vector3, right: Vector3) -> Vector3:
    return Vector3(
        left.y * right.z - left.z * right.y,
        left.z * right.x - left.x * right.z,
        left.x * right.y - left.y * right.x,
    )


def _unit(value: Vector3) -> bool:
    return isclose(_length(value), 1.0, rel_tol=1e-10, abs_tol=1e-10)


# analytic axes may use either direct or indirect OpenCascade parameter frames
def _IsFrame(normal: Vector3, x_direction: Vector3, y_direction: Vector3) -> bool:
    expected_y = _cross(normal, x_direction)
    Handedness = _dot(expected_y, y_direction)
    return (
        _unit(normal)
        and _unit(x_direction)
        and _unit(y_direction)
        and isclose(_dot(normal, x_direction), 0.0, abs_tol=1e-10)
        and isclose(_dot(normal, y_direction), 0.0, abs_tol=1e-10)
        and isclose(_dot(x_direction, y_direction), 0.0, abs_tol=1e-10)
        and isclose(abs(Handedness), 1.0, rel_tol=1e-10, abs_tol=1e-10)
    )


def _count(tokens: _Tokens, label: bytes, maximum: int) -> int:
    tokens.expect(label)
    return tokens.integer(0, maximum)


def _zero_table(tokens: _Tokens, label: bytes) -> None:
    if _count(tokens, label, 0) != 0:
        raise _DecodeFailure("unsupported BRep table")


def _reference(
    tokens: _Tokens, shape_count: int, location_count: int = 0
) -> _Reference | None:
    token = tokens.take()
    if token == b"*":
        return None
    if len(token) < 2 or token[:1] not in {b"+", b"-", b"i", b"e"}:
        raise _DecodeFailure("invalid BRep shape reference")
    number = token[1:]
    if _INTEGER_PATTERN.fullmatch(number) is None:
        raise _DecodeFailure("invalid BRep shape reference")
    record = int(number)
    if record < 1 or record > shape_count:
        raise _DecodeFailure("unsupported BRep shape location")
    location = tokens.integer(0, location_count)
    return _Reference(token[:1].decode("ascii"), record, location)


def _boolean(tokens: _Tokens) -> bool:
    return bool(tokens.integer(0, 1))


def _numbers(tokens: _Tokens, count: int) -> None:
    if count < 0 or count > _MAX_GEOMETRY:
        raise _DecodeFailure("BRep numeric record is out of bounds")
    for _ in range(count):
        tokens.number()


def _bounded_product(left: int, right: int) -> int:
    if left < 0 or right < 0 or (left and right > _MAX_GEOMETRY // left):
        raise _DecodeFailure("BRep array dimensions are out of bounds")
    value = left * right
    if value > _MAX_GEOMETRY:
        raise _DecodeFailure("BRep array dimensions are out of bounds")
    return value


def _positive_index(tokens: _Tokens, count: int) -> int:
    if count < 1:
        raise _DecodeFailure("BRep references an empty table")
    return tokens.integer(1, count)


def _location_index(tokens: _Tokens, count: int) -> int:
    return tokens.integer(0, count)


def _continuity(tokens: _Tokens) -> bytes:
    value = tokens.take()
    if _CONTINUITY_PATTERN.fullmatch(value) is None:
        raise _DecodeFailure("invalid BRep continuity")
    return value


def _curve_geometry(tokens: _Tokens, dimension: int, depth: int = 0) -> None:
    if depth > _MAX_RECURSION or dimension not in {2, 3}:
        raise _DecodeFailure("BRep curve recursion is out of bounds")
    kind = tokens.integer(1, 9)
    frame_size = 6 if dimension == 2 else 12
    if kind == 1:
        _numbers(tokens, dimension * 2)
    elif kind in {2, 4}:
        _numbers(tokens, frame_size + 1)
    elif kind in {3, 5}:
        _numbers(tokens, frame_size + 2)
    elif kind == 6:
        rational = _boolean(tokens)
        degree = tokens.integer(1, _MAX_GEOMETRY - 1)
        poles = degree + 1
        _numbers(tokens, _bounded_product(poles, dimension + int(rational)))
    elif kind == 7:
        rational = _boolean(tokens)
        _boolean(tokens)
        tokens.integer(1, _MAX_GEOMETRY)
        poles = tokens.integer(2, _MAX_GEOMETRY)
        knots = tokens.integer(2, _MAX_GEOMETRY)
        _numbers(tokens, _bounded_product(poles, dimension + int(rational)))
        for _ in range(knots):
            tokens.number()
            tokens.integer(1, _MAX_GEOMETRY)
    elif kind == 8:
        _numbers(tokens, 2)
        _curve_geometry(tokens, dimension, depth + 1)
    else:
        tokens.number()
        if dimension == 3:
            _numbers(tokens, 3)
        _curve_geometry(tokens, dimension, depth + 1)


def _surface_geometry(tokens: _Tokens, depth: int = 0) -> None:
    if depth > _MAX_RECURSION:
        raise _DecodeFailure("BRep surface recursion is out of bounds")
    kind = tokens.integer(1, 11)
    if kind == 1:
        _numbers(tokens, 12)
    elif kind in {2, 4}:
        _numbers(tokens, 13)
    elif kind in {3, 5}:
        _numbers(tokens, 14)
    elif kind == 6:
        _numbers(tokens, 3)
        _curve_geometry(tokens, 3, depth + 1)
    elif kind == 7:
        _numbers(tokens, 6)
        _curve_geometry(tokens, 3, depth + 1)
    elif kind == 8:
        u_rational = _boolean(tokens)
        v_rational = _boolean(tokens)
        u_degree = tokens.integer(1, _MAX_GEOMETRY - 1)
        v_degree = tokens.integer(1, _MAX_GEOMETRY - 1)
        poles = _bounded_product(u_degree + 1, v_degree + 1)
        _numbers(tokens, _bounded_product(poles, 3 + int(u_rational or v_rational)))
    elif kind == 9:
        u_rational = _boolean(tokens)
        v_rational = _boolean(tokens)
        _boolean(tokens)
        _boolean(tokens)
        tokens.integer(1, _MAX_GEOMETRY)
        tokens.integer(1, _MAX_GEOMETRY)
        u_poles = tokens.integer(2, _MAX_GEOMETRY)
        v_poles = tokens.integer(2, _MAX_GEOMETRY)
        u_knots = tokens.integer(2, _MAX_GEOMETRY)
        v_knots = tokens.integer(2, _MAX_GEOMETRY)
        poles = _bounded_product(u_poles, v_poles)
        _numbers(tokens, _bounded_product(poles, 3 + int(u_rational or v_rational)))
        for count in (u_knots, v_knots):
            for _ in range(count):
                tokens.number()
                tokens.integer(1, _MAX_GEOMETRY)
    elif kind == 10:
        _numbers(tokens, 4)
        _surface_geometry(tokens, depth + 1)
    else:
        tokens.number()
        _surface_geometry(tokens, depth + 1)


def _location_multiply(
    left: tuple[tuple[int, int], ...], right: tuple[tuple[int, int], ...]
) -> tuple[tuple[int, int], ...]:
    result: list[tuple[int, int]] = []
    for datum, power in chain(right, left):
        if result and result[-1][0] == datum:
            combined = result[-1][1] + power
            if combined < _MIN_INT32 or combined > _MAX_INT32:
                raise _DecodeFailure("BRep location power is out of bounds")
            result.pop()
            if combined:
                result.append((datum, combined))
        else:
            result.append((datum, power))
        if len(result) > _MAX_GEOMETRY:
            raise _DecodeFailure("BRep location chain is out of bounds")
    return tuple(result)


def _location_power(
    value: tuple[tuple[int, int], ...], power: int
) -> tuple[tuple[int, int], ...]:
    if power == 0 or not value:
        return ()
    if power < 0:
        value = tuple((datum, -datum_power) for datum, datum_power in reversed(value))
        power = -power
    result: tuple[tuple[int, int], ...] = ()
    factor = value
    while power:
        if power & 1:
            result = _location_multiply(result, factor)
        power >>= 1
        if power:
            factor = _location_multiply(factor, factor)
    return result


def _normalized_vector(value: tuple[float, float, float]) -> tuple[float, float, float]:
    magnitude = sqrt(sum(component * component for component in value))
    if not isfinite(magnitude) or magnitude <= float_info.min:
        raise _DecodeFailure("invalid BRep location transform")
    result = tuple(component / magnitude for component in value)
    if not all(isfinite(component) for component in result):
        raise _DecodeFailure("invalid BRep location transform")
    return result


def _orthogonalized_vectors(
    values: tuple[tuple[float, float, float], ...],
) -> tuple[tuple[float, float, float], ...]:
    first = _normalized_vector(values[0])
    projection = sum(values[1][index] * first[index] for index in range(3))
    second = _normalized_vector(
        tuple(values[1][index] - projection * first[index] for index in range(3))
    )
    first_projection = sum(values[2][index] * first[index] for index in range(3))
    second_projection = sum(values[2][index] * second[index] for index in range(3))
    third = _normalized_vector(
        tuple(
            values[2][index]
            - first_projection * first[index]
            - second_projection * second[index]
            for index in range(3)
        )
    )
    return first, second, third


def _location_transform(tokens: _Tokens) -> tuple[float, ...]:
    values = tuple(tokens.number() for _ in range(12))
    determinant = (
        values[0] * (values[5] * values[10] - values[6] * values[9])
        - values[1] * (values[4] * values[10] - values[6] * values[8])
        + values[2] * (values[4] * values[9] - values[5] * values[8])
    )
    if not isfinite(determinant) or abs(determinant) < float_info.min:
        raise _DecodeFailure("singular BRep location transform")
    scale = abs(determinant) ** (1.0 / 3.0)
    if determinant < 0.0:
        scale = -scale
    rows = (
        tuple(values[index] / scale for index in (0, 1, 2)),
        tuple(values[index] / scale for index in (4, 5, 6)),
        tuple(values[index] / scale for index in (8, 9, 10)),
    )
    columns = tuple(tuple(rows[row][column] for row in range(3)) for column in range(3))
    columns = _orthogonalized_vectors(columns)
    rows = tuple(tuple(columns[column][row] for column in range(3)) for row in range(3))
    _orthogonalized_vectors(rows)
    return values


_IDENTITY_LOCATION = (
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
)


def _location_product(
    left: tuple[float, ...], right: tuple[float, ...]
) -> tuple[float, ...]:
    result: list[float] = []
    for row in range(3):
        for column in range(3):
            result.append(
                sum(
                    left[row * 4 + inner] * right[inner * 4 + column]
                    for inner in range(3)
                )
            )
        result.append(
            left[row * 4 + 3]
            + sum(left[row * 4 + inner] * right[inner * 4 + 3] for inner in range(3))
        )
    if not all(isfinite(value) for value in result):
        raise _DecodeFailure("invalid BRep location transform")
    return tuple(result)


def _location_inverse(value: tuple[float, ...]) -> tuple[float, ...]:
    a, b, c, tx, d, e, f, ty, g, h, i, tz = value
    determinant = a * (e * i - f * h) - b * (d * i - f * g) + c * (d * h - e * g)
    if not isfinite(determinant) or abs(determinant) < float_info.min:
        raise _DecodeFailure("singular BRep location transform")
    inverse = (
        (e * i - f * h) / determinant,
        (c * h - b * i) / determinant,
        (b * f - c * e) / determinant,
        0.0,
        (f * g - d * i) / determinant,
        (a * i - c * g) / determinant,
        (c * d - a * f) / determinant,
        0.0,
        (d * h - e * g) / determinant,
        (b * g - a * h) / determinant,
        (a * e - b * d) / determinant,
        0.0,
    )
    translated = (
        *inverse[:3],
        -(inverse[0] * tx + inverse[1] * ty + inverse[2] * tz),
        *inverse[4:7],
        -(inverse[4] * tx + inverse[5] * ty + inverse[6] * tz),
        *inverse[8:11],
        -(inverse[8] * tx + inverse[9] * ty + inverse[10] * tz),
    )
    if not all(isfinite(component) for component in translated):
        raise _DecodeFailure("invalid BRep location transform")
    return translated


def _location_matrix_power(value: tuple[float, ...], power: int) -> tuple[float, ...]:
    if power < 0:
        value = _location_inverse(value)
        power = -power
    result = _IDENTITY_LOCATION
    factor = value
    while power:
        if power & 1:
            result = _location_product(result, factor)
        power >>= 1
        if power:
            factor = _location_product(factor, factor)
    return result


def _model_locations(tokens: _Tokens) -> tuple[tuple[float, ...], ...]:
    count = _count(tokens, b"Locations", _MAX_GEOMETRY)
    chains: list[tuple[tuple[int, int], ...]] = []
    direct: dict[int, tuple[float, ...]] = {}
    matrices: list[tuple[float, ...]] = []
    unique_locations: set[tuple[tuple[int, int], ...]] = set()
    for index in range(1, count + 1):
        kind = tokens.integer(1, 2)
        if kind == 1:
            direct[index] = _location_transform(tokens)
            location = ((index, 1),)
        else:
            location = ()
            reference = tokens.integer(0, len(chains))
            while reference:
                power = tokens.signed_integer()
                location = _location_multiply(
                    _location_power(chains[reference - 1], power), location
                )
                reference = tokens.integer(0, len(chains))
        if not location or location in unique_locations:
            raise _DecodeFailure("invalid BRep location record")
        matrix = _IDENTITY_LOCATION
        for datum, power in location:
            base = direct.get(datum)
            if base is None:
                raise _DecodeFailure("invalid BRep location record")
            matrix = _location_product(matrix, _location_matrix_power(base, power))
        chains.append(location)
        matrices.append(matrix)
        unique_locations.add(location)
    return tuple(matrices)


def _location_scale(value: tuple[float, ...]) -> float:
    columns = tuple(
        tuple(value[row * 4 + column] for row in range(3)) for column in range(3)
    )
    lengths = tuple(
        sqrt(sum(component * component for component in item)) for item in columns
    )
    if (
        any(not isfinite(length) or length <= float_info.min for length in lengths)
        or not isclose(lengths[0], lengths[1], rel_tol=1e-10, abs_tol=1e-12)
        or not isclose(lengths[0], lengths[2], rel_tol=1e-10, abs_tol=1e-12)
        or any(
            not isclose(
                sum(left[index] * right[index] for index in range(3)),
                0.0,
                rel_tol=0.0,
                abs_tol=1e-10 * lengths[0] * lengths[0],
            )
            for left, right in (
                (columns[0], columns[1]),
                (columns[0], columns[2]),
                (columns[1], columns[2]),
            )
        )
    ):
        raise _DecodeFailure("unsupported BRep location transform")
    determinant = (
        value[0] * (value[5] * value[10] - value[6] * value[9])
        - value[1] * (value[4] * value[10] - value[6] * value[8])
        + value[2] * (value[4] * value[9] - value[5] * value[8])
    )
    if determinant <= 0.0:
        raise _DecodeFailure("unsupported BRep location transform")
    return lengths[0]


def _location_point(value: tuple[float, ...], point: Vector3) -> Vector3:
    components = (point.x, point.y, point.z)
    return Vector3(
        *(
            value[row * 4 + 3]
            + sum(value[row * 4 + column] * components[column] for column in range(3))
            for row in range(3)
        )
    )


def _location_direction(value: tuple[float, ...], direction: Vector3) -> Vector3:
    components = (direction.x, direction.y, direction.z)
    transformed = tuple(
        sum(value[row * 4 + column] * components[column] for column in range(3))
        for row in range(3)
    )
    normalized = _normalized_vector(transformed)
    return Vector3(*normalized)


def _located_model_inputs(
    curves: tuple[LineCurve, ...],
    surfaces: tuple[PlaneSurface, ...],
    records: Mapping[int, _ShapeRecord],
    location: tuple[float, ...],
) -> tuple[
    tuple[LineCurve, ...],
    tuple[PlaneSurface, ...],
    dict[int, _ShapeRecord],
]:
    scale = _location_scale(location)
    transformed_curves = tuple(
        LineCurve(
            curve.id,
            _location_point(location, curve.origin),
            _location_direction(location, curve.direction),
            provenance=curve.provenance,
            attributes=curve.attributes,
        )
        for curve in curves
    )
    transformed_surfaces = tuple(
        PlaneSurface(
            surface.id,
            _location_point(location, surface.origin),
            _location_direction(location, surface.normal),
            _location_direction(location, surface.reference_direction),
            provenance=surface.provenance,
            attributes=surface.attributes,
        )
        for surface in surfaces
    )
    transformed_records: dict[int, _ShapeRecord] = {}
    for number, record in records.items():
        geometry = record.geometry
        if isinstance(geometry, _VertexData):
            geometry = _VertexData(
                geometry.tolerance * scale,
                _location_point(location, geometry.point),
            )
        elif isinstance(geometry, _EdgeData):
            geometry = _EdgeData(
                geometry.tolerance * scale,
                geometry.curve,
                geometry.first * scale,
                geometry.last * scale,
            )
        elif isinstance(geometry, _FaceData):
            geometry = _FaceData(
                geometry.natural,
                geometry.tolerance * scale,
                geometry.surface,
            )
        transformed_records[number] = _ShapeRecord(
            record.kind,
            record.flags,
            record.children,
            geometry,
        )
    return transformed_curves, transformed_surfaces, transformed_records


def _locations(tokens: _Tokens) -> int:
    count = _count(tokens, b"Locations", _MAX_GEOMETRY)
    locations: list[tuple[tuple[int, int], ...]] = []
    unique_locations: set[tuple[tuple[int, int], ...]] = set()
    for index in range(1, count + 1):
        kind = tokens.integer(1, 2)
        if kind == 1:
            _location_transform(tokens)
            location = ((index, 1),)
        else:
            location = ()
            reference = tokens.integer(0, len(locations))
            while reference:
                power = tokens.signed_integer()
                location = _location_multiply(
                    _location_power(locations[reference - 1], power), location
                )
                reference = tokens.integer(0, len(locations))
        if not location or location in unique_locations:
            raise _DecodeFailure("invalid BRep location record")
        locations.append(location)
        unique_locations.add(location)
    return count


def _curves(tokens: _Tokens, label: bytes, dimension: int) -> int:
    count = _count(tokens, label, _MAX_GEOMETRY)
    for _ in range(count):
        _curve_geometry(tokens, dimension)
    return count


def _polygon3d(tokens: _Tokens) -> int:
    count = _count(tokens, b"Polygon3D", _MAX_GEOMETRY)
    for _ in range(count):
        nodes = tokens.integer(1, _MAX_GEOMETRY)
        parameters = _boolean(tokens)
        if tokens.number() < 0.0:
            raise _DecodeFailure("negative BRep polygon deflection")
        _numbers(tokens, _bounded_product(nodes, 3))
        if parameters:
            _numbers(tokens, nodes)
    return count


def _polygons_on_triangulations(tokens: _Tokens) -> tuple[int, ...]:
    count = _count(tokens, b"PolygonOnTriangulations", _MAX_GEOMETRY)
    maximum_nodes = []
    for _ in range(count):
        nodes = tokens.integer(1, _MAX_GEOMETRY)
        maximum_node = 0
        for _ in range(nodes):
            maximum_node = max(maximum_node, tokens.integer(1, _MAX_GEOMETRY))
        maximum_nodes.append(maximum_node)
        tokens.expect(b"p")
        if tokens.number() < 0.0:
            raise _DecodeFailure("negative BRep polygon deflection")
        if _boolean(tokens):
            _numbers(tokens, nodes)
    return tuple(maximum_nodes)


def _surfaces(tokens: _Tokens) -> int:
    count = _count(tokens, b"Surfaces", _MAX_GEOMETRY)
    for _ in range(count):
        _surface_geometry(tokens)
    return count


def _triangulations(tokens: _Tokens) -> tuple[int, ...]:
    count = _count(tokens, b"Triangulations", _MAX_GEOMETRY)
    node_counts = []
    for _ in range(count):
        nodes = tokens.integer(1, _MAX_GEOMETRY)
        node_counts.append(nodes)
        triangles = tokens.integer(1, _MAX_GEOMETRY)
        parameters = _boolean(tokens)
        if tokens.number() < 0.0:
            raise _DecodeFailure("negative BRep triangulation deflection")
        _numbers(tokens, _bounded_product(nodes, 3))
        if parameters:
            _numbers(tokens, _bounded_product(nodes, 2))
        for _ in range(_bounded_product(triangles, 3)):
            tokens.integer(1, nodes)
    return tuple(node_counts)


def _vertex_structure(
    tokens: _Tokens,
    locations: int,
    curves2d: int,
    curves3d: int,
    surfaces: int,
) -> None:
    if tokens.number() < 0.0:
        raise _DecodeFailure("negative BRep vertex tolerance")
    _numbers(tokens, 3)
    while True:
        parameter = tokens.number()
        kind = tokens.integer(0, 3)
        if kind == 0:
            if parameter != 0.0:
                raise _DecodeFailure("invalid BRep vertex terminator")
            return
        if kind == 1:
            _positive_index(tokens, curves3d)
        elif kind == 2:
            _positive_index(tokens, curves2d)
            _positive_index(tokens, surfaces)
        else:
            tokens.number()
            _positive_index(tokens, surfaces)
        _location_index(tokens, locations)


def _indexed_continuity(tokens: _Tokens, count: int) -> None:
    value = tokens.take()
    match = _INDEXED_CONTINUITY_PATTERN.fullmatch(value)
    if match is not None:
        index = int(match.group(1))
        if index < 1 or index > count:
            raise _DecodeFailure("BRep curve index is out of bounds")
        return
    if _INTEGER_PATTERN.fullmatch(value) is None:
        raise _DecodeFailure("invalid BRep indexed continuity")
    index = int(value)
    if index < 1 or index > count:
        raise _DecodeFailure("BRep curve index is out of bounds")
    _continuity(tokens)


def _edge_structure(
    tokens: _Tokens,
    locations: int,
    curves2d: int,
    curves3d: int,
    polygons3d: int,
    polygons_on_triangulations: tuple[int, ...],
    surfaces: int,
    triangulations: tuple[int, ...],
) -> None:
    if tokens.number() < 0.0:
        raise _DecodeFailure("negative BRep edge tolerance")
    _boolean(tokens)
    _boolean(tokens)
    _boolean(tokens)
    while True:
        kind = tokens.integer(0, 7)
        if kind == 0:
            return
        if kind == 1:
            _positive_index(tokens, curves3d)
            _location_index(tokens, locations)
            _numbers(tokens, 2)
        elif kind == 2:
            _positive_index(tokens, curves2d)
            _positive_index(tokens, surfaces)
            _location_index(tokens, locations)
            _numbers(tokens, 2)
        elif kind == 3:
            _positive_index(tokens, curves2d)
            _indexed_continuity(tokens, curves2d)
            _positive_index(tokens, surfaces)
            _location_index(tokens, locations)
            _numbers(tokens, 2)
        elif kind == 4:
            _continuity(tokens)
            _positive_index(tokens, surfaces)
            _location_index(tokens, locations)
            _positive_index(tokens, surfaces)
            _location_index(tokens, locations)
        elif kind == 5:
            _positive_index(tokens, polygons3d)
            _location_index(tokens, locations)
        elif kind == 6:
            polygon = _positive_index(tokens, len(polygons_on_triangulations))
            triangulation = _positive_index(tokens, len(triangulations))
            if (
                polygons_on_triangulations[polygon - 1]
                > triangulations[triangulation - 1]
            ):
                raise _DecodeFailure("BRep polygon node is out of bounds")
            _location_index(tokens, locations)
        else:
            first_polygon = _positive_index(tokens, len(polygons_on_triangulations))
            second_polygon = _positive_index(tokens, len(polygons_on_triangulations))
            triangulation = _positive_index(tokens, len(triangulations))
            if (
                max(
                    polygons_on_triangulations[first_polygon - 1],
                    polygons_on_triangulations[second_polygon - 1],
                )
                > triangulations[triangulation - 1]
            ):
                raise _DecodeFailure("BRep polygon node is out of bounds")
            _location_index(tokens, locations)


def _face_structure(
    tokens: _Tokens,
    locations: int,
    surfaces: int,
    triangulations: tuple[int, ...],
) -> None:
    kind = tokens.integer(0, 2)
    if kind in {0, 1}:
        if tokens.number() < 0.0:
            raise _DecodeFailure("negative BRep face tolerance")
        surface = tokens.integer(0, surfaces)
        _location_index(tokens, locations)
        has_triangulation = False
        if tokens.face_triangulation_starts_next_line():
            tokens.expect(b"2")
            _positive_index(tokens, len(triangulations))
            has_triangulation = True
        if surface == 0 and not has_triangulation:
            raise _DecodeFailure("BRep face has no geometry")
    else:
        _positive_index(tokens, len(triangulations))


def _structural_reference(
    tokens: _Tokens, shape_count: int, location_count: int
) -> tuple[_Reference, int] | None:
    token = tokens.take()
    if token == b"*":
        return None
    if len(token) < 2 or token[:1] not in {b"+", b"-", b"i", b"e"}:
        raise _DecodeFailure("invalid BRep shape reference")
    number = token[1:]
    if _INTEGER_PATTERN.fullmatch(number) is None:
        raise _DecodeFailure("invalid BRep shape reference")
    record = int(number)
    if record < 1 or record > shape_count:
        raise _DecodeFailure("BRep shape reference is out of bounds")
    location = _location_index(tokens, location_count)
    return _Reference(token[:1].decode("ascii"), record), location


def _shape_structure(
    tokens: _Tokens,
    locations: int,
    curves2d: int,
    curves3d: int,
    polygons3d: int,
    polygons_on_triangulations: tuple[int, ...],
    surfaces: int,
    triangulations: tuple[int, ...],
) -> None:
    count = _count(tokens, b"TShapes", _MAX_SHAPES)
    if count == 0:
        raise _DecodeFailure("empty BRep topology")
    kinds: dict[int, bytes] = {}
    children: dict[int, tuple[int, ...]] = {}
    for ordinal in range(1, count + 1):
        kind = tokens.take()
        if kind not in _SHAPE_TYPES:
            raise _DecodeFailure("unsupported BRep shape type")
        record = count - ordinal + 1
        if kind == b"Ve":
            _vertex_structure(tokens, locations, curves2d, curves3d, surfaces)
        elif kind == b"Ed":
            _edge_structure(
                tokens,
                locations,
                curves2d,
                curves3d,
                polygons3d,
                polygons_on_triangulations,
                surfaces,
                triangulations,
            )
        elif kind == b"Fa":
            _face_structure(tokens, locations, surfaces, triangulations)
        flags = tokens.take()
        if _FLAGS_PATTERN.fullmatch(flags) is None:
            raise _DecodeFailure("invalid BRep shape flags")
        child_records = []
        while True:
            child = _structural_reference(tokens, count, locations)
            if child is None:
                break
            reference, _ = child
            if reference.record <= record:
                raise _DecodeFailure("BRep topology is not ordered bottom-up")
            child_kind = kinds.get(reference.record)
            if child_kind not in _SHAPE_CHILD_TYPES[kind]:
                raise _DecodeFailure("invalid BRep child shape type")
            child_records.append(reference.record)
        kinds[record] = kind
        children[record] = tuple(child_records)
    root = _structural_reference(tokens, count, locations)
    if (
        root is None
        or root[0].record != 1
        or root[0].record not in kinds
        or tokens.peek() is not None
    ):
        raise _DecodeFailure("invalid BRep root shape")
    reachable = set()
    pending = [root[0].record]
    while pending:
        record = pending.pop()
        if record in reachable:
            continue
        reachable.add(record)
        pending.extend(children[record])
    if reachable != set(kinds):
        raise _DecodeFailure("unreachable BRep topology")


def _vertex_geometry(tokens: _Tokens) -> _VertexData:
    tolerance = tokens.number()
    point = _vector(tokens)
    if tolerance < 0.0:
        raise _DecodeFailure("invalid BRep vertex tolerance")
    while True:
        parameter = tokens.number()
        representation = tokens.integer(0, 3)
        if representation == 0:
            if parameter != 0.0:
                raise _DecodeFailure("invalid BRep vertex representation terminator")
            break
        if representation == 1:
            tokens.integer(1, _MAX_GEOMETRY)
        elif representation == 2:
            tokens.integer(1, _MAX_GEOMETRY)
            tokens.integer(1, _MAX_GEOMETRY)
        else:
            tokens.number()
            tokens.integer(1, _MAX_GEOMETRY)
        if tokens.integer(0, 0) != 0:
            raise _DecodeFailure("unsupported BRep vertex location")
    return _VertexData(tolerance, point)


# edge geometry binds one spatial curve while retaining auxiliary pcurves
def _edge_geometry(
    tokens: _Tokens,
    curve_count: int,
    curve2d_count: int,
    surface_count: int,
    location_count: int,
) -> _EdgeData:
    tolerance = tokens.number()
    tokens.integer(0, 1)
    tokens.integer(0, 1)
    degenerate = tokens.integer(0, 1)
    if tolerance < 0.0 or degenerate:
        raise _DecodeFailure("unsupported BRep edge state")
    representations: list[tuple[int, float, float, int]] = []
    while True:
        representation = tokens.integer(0, 7)
        if representation == 0:
            break
        if representation == 1:
            curve = tokens.integer(1, curve_count)
            location = _location_index(tokens, location_count)
            representations.append((curve, tokens.number(), tokens.number(), location))
        elif representation == 2:
            tokens.integer(1, curve2d_count)
            tokens.integer(1, surface_count)
            _location_index(tokens, location_count)
            tokens.number()
            tokens.number()
        elif representation == 3:
            tokens.integer(1, curve2d_count)
            _indexed_continuity(tokens, curve2d_count)
            tokens.integer(1, surface_count)
            _location_index(tokens, location_count)
            tokens.number()
            tokens.number()
        else:
            raise _DecodeFailure("unsupported BRep edge representation")
    if len(representations) != 1:
        raise _DecodeFailure("ambiguous BRep edge geometry")
    curve, first, last, location = representations[0]
    return _EdgeData(tolerance, curve, first, last, location)


# face geometry binds its analytic surface and reusable location
def _face_geometry(
    tokens: _Tokens, surface_count: int, location_count: int
) -> _FaceData:
    natural = tokens.integer(0, 1)
    tolerance = tokens.number()
    surface = tokens.integer(1, surface_count)
    location = _location_index(tokens, location_count)
    if tolerance < 0.0:
        raise _DecodeFailure("unsupported BRep face geometry")
    return _FaceData(bool(natural), tolerance, surface, location)


def _shape_records(
    tokens: _Tokens,
    shape_count: int,
    curve_count: int,
    curve2d_count: int,
    surface_count: int,
    location_count: int = 0,
) -> dict[int, _ShapeRecord]:
    records: dict[int, _ShapeRecord] = {}
    for ordinal in range(1, shape_count + 1):
        kind = tokens.take()
        if kind not in _SHAPE_TYPES:
            raise _DecodeFailure("unsupported BRep shape type")
        geometry: _VertexData | _EdgeData | _FaceData | None = None
        if kind == b"Ve":
            geometry = _vertex_geometry(tokens)
        elif kind == b"Ed":
            geometry = _edge_geometry(
                tokens,
                curve_count,
                curve2d_count,
                surface_count,
                location_count,
            )
        elif kind == b"Fa":
            geometry = _face_geometry(tokens, surface_count, location_count)
        flag_token = tokens.take()
        if _FLAGS_PATTERN.fullmatch(flag_token) is None:
            raise _DecodeFailure("invalid BRep shape flags")
        children: list[_Reference] = []
        while True:
            child = _reference(tokens, shape_count, location_count)
            if child is None:
                break
            children.append(child)
        record_number = shape_count - ordinal + 1
        if any(child.record <= record_number for child in children):
            raise _DecodeFailure("BRep topology is not ordered bottom-up")
        records[record_number] = _ShapeRecord(
            kind,
            flag_token.decode("ascii"),
            tuple(children),
            geometry,
        )
    return records


# required because freecad stores reusable topology under nested shape placements
def _ApplyLocations(
    Curves: tuple[BrepCurve, ...],
    Surfaces: tuple[BrepSurface, ...],
    Records: Mapping[int, _ShapeRecord],
    RootRef: _Reference,
    Locations: tuple[tuple[float, ...], ...],
    NamePrefix: str,
) -> tuple[
    tuple[BrepCurve, ...],
    tuple[BrepSurface, ...],
    dict[int, _ShapeRecord],
    _Reference,
]:
    if (
        not RootRef.location
        and not any(
            ChildRef.location
            for Record in Records.values()
            for ChildRef in Record.children
        )
        and not any(
            isinstance(Record.geometry, (_EdgeData, _FaceData))
            and Record.geometry.location
            for Record in Records.values()
        )
    ):
        return Curves, Surfaces, dict(Records), RootRef

    PlacedCurves: list[BrepCurve] = []
    PlacedSurfaces: list[BrepSurface] = []
    PlacedRecords: dict[int, _ShapeRecord] = {}
    RecordCache: dict[tuple[int, tuple[float, ...]], int] = {}
    CurveCache: dict[tuple[int, tuple[float, ...]], int] = {}
    SurfaceCache: dict[tuple[int, tuple[float, ...]], int] = {}

    # reused curves need distinct coordinates whenever their occurrences move
    def PlaceCurve(CurveIndex: int, Location: tuple[float, ...]) -> int:
        CurveKey = (CurveIndex, Location)
        CachedIndex = CurveCache.get(CurveKey)
        if CachedIndex is not None:
            return CachedIndex
        BaseCurve = Curves[CurveIndex - 1]
        PlacedIndex = len(PlacedCurves) + 1
        if isinstance(BaseCurve, LineCurve):
            PlacedCurve: BrepCurve = LineCurve(
                f"{NamePrefix}:curve:{PlacedIndex}",
                _location_point(Location, BaseCurve.origin),
                _location_direction(Location, BaseCurve.direction),
                provenance=BaseCurve.provenance,
                attributes=BaseCurve.attributes,
            )
        elif isinstance(BaseCurve, CircleCurve):
            PlacedCurve = CircleCurve(
                f"{NamePrefix}:curve:{PlacedIndex}",
                _location_point(Location, BaseCurve.center),
                _location_direction(Location, BaseCurve.axis),
                _location_direction(Location, BaseCurve.reference_direction),
                BaseCurve.radius * _location_scale(Location),
                provenance=BaseCurve.provenance,
                attributes=BaseCurve.attributes,
            )
        else:
            raise _DecodeFailure("unsupported located BRep curve")
        PlacedCurves.append(PlacedCurve)
        CurveCache[CurveKey] = PlacedIndex
        return PlacedIndex

    # reused surfaces need distinct frames whenever their occurrences move
    def PlaceSurface(SurfaceIndex: int, Location: tuple[float, ...]) -> int:
        SurfaceKey = (SurfaceIndex, Location)
        CachedIndex = SurfaceCache.get(SurfaceKey)
        if CachedIndex is not None:
            return CachedIndex
        BaseSurface = Surfaces[SurfaceIndex - 1]
        PlacedIndex = len(PlacedSurfaces) + 1
        if isinstance(BaseSurface, PlaneSurface):
            PlacedSurface: BrepSurface = PlaneSurface(
                f"{NamePrefix}:surface:{PlacedIndex}",
                _location_point(Location, BaseSurface.origin),
                _location_direction(Location, BaseSurface.normal),
                _location_direction(Location, BaseSurface.reference_direction),
                provenance=BaseSurface.provenance,
                attributes=BaseSurface.attributes,
            )
        elif isinstance(BaseSurface, CylinderSurface):
            PlacedSurface = CylinderSurface(
                f"{NamePrefix}:surface:{PlacedIndex}",
                _location_point(Location, BaseSurface.origin),
                _location_direction(Location, BaseSurface.axis),
                _location_direction(Location, BaseSurface.reference_direction),
                BaseSurface.radius * _location_scale(Location),
                provenance=BaseSurface.provenance,
                attributes=BaseSurface.attributes,
            )
        else:
            raise _DecodeFailure("unsupported located BRep surface")
        PlacedSurfaces.append(PlacedSurface)
        SurfaceCache[SurfaceKey] = PlacedIndex
        return PlacedIndex

    # topology occurrences must inherit every placement in their parent chain
    def PlaceRecord(RecordIndex: int, Location: tuple[float, ...]) -> int:
        RecordKey = (RecordIndex, Location)
        CachedIndex = RecordCache.get(RecordKey)
        if CachedIndex is not None:
            return CachedIndex
        if len(PlacedRecords) >= _MAX_SHAPES:
            raise _DecodeFailure("located BRep topology exceeds shape bounds")
        SourceRecord = Records[RecordIndex]
        ChildRefs: list[_Reference] = []
        for ChildRef in SourceRecord.children:
            ChildLoc = (
                _IDENTITY_LOCATION
                if not ChildRef.location
                else Locations[ChildRef.location - 1]
            )
            ChildMatrix = _location_product(ChildLoc, Location)
            ChildRecord = PlaceRecord(ChildRef.record, ChildMatrix)
            ChildRefs.append(_Reference(ChildRef.orientation, ChildRecord))
        ScaleValue = _location_scale(Location)
        Geometry = SourceRecord.geometry
        if isinstance(Geometry, _VertexData):
            Geometry = _VertexData(
                Geometry.tolerance * ScaleValue,
                _location_point(Location, Geometry.point),
            )
        elif isinstance(Geometry, _EdgeData):
            SourceCurve = Curves[Geometry.curve - 1]
            GeometryLoc = (
                _IDENTITY_LOCATION
                if not Geometry.location
                else Locations[Geometry.location - 1]
            )
            CurveLoc = _location_product(GeometryLoc, Location)
            ParameterScale = (
                _location_scale(CurveLoc) if isinstance(SourceCurve, LineCurve) else 1.0
            )
            Geometry = _EdgeData(
                Geometry.tolerance * ScaleValue,
                PlaceCurve(Geometry.curve, CurveLoc),
                Geometry.first * ParameterScale,
                Geometry.last * ParameterScale,
            )
        elif isinstance(Geometry, _FaceData):
            GeometryLoc = (
                _IDENTITY_LOCATION
                if not Geometry.location
                else Locations[Geometry.location - 1]
            )
            Geometry = _FaceData(
                Geometry.natural,
                Geometry.tolerance * ScaleValue,
                PlaceSurface(
                    Geometry.surface, _location_product(GeometryLoc, Location)
                ),
            )
        PlacedIndex = len(PlacedRecords) + 1
        PlacedRecords[PlacedIndex] = _ShapeRecord(
            SourceRecord.kind,
            SourceRecord.flags,
            tuple(ChildRefs),
            Geometry,
        )
        RecordCache[RecordKey] = PlacedIndex
        return PlacedIndex

    RootLoc = (
        _IDENTITY_LOCATION if not RootRef.location else Locations[RootRef.location - 1]
    )
    RootIndex = PlaceRecord(RootRef.record, RootLoc)
    return (
        tuple(PlacedCurves),
        tuple(PlacedSurfaces),
        PlacedRecords,
        _Reference(RootRef.orientation, RootIndex),
    )


def _opposite(orientation: str) -> str:
    if orientation == "+":
        return "-"
    if orientation == "-":
        return "+"
    raise _DecodeFailure("unsupported BRep topology orientation")


def _compose(outer: str, inner: str) -> str:
    if outer == "+":
        return inner
    if outer == "-":
        return _opposite(inner)
    raise _DecodeFailure("unsupported BRep topology orientation")


# Eulerian ordering handles seam edges that occur in both directions in one wire
def _OrderWireUses(
    uses: list[_Reference], edge_vertices: Mapping[int, tuple[int, int]]
) -> list[_Reference]:
    # oriented endpoints expose the directed multigraph consumed by Hierholzer's walk
    def Endpoints(reference: _Reference) -> tuple[int, int]:
        start, end = edge_vertices[reference.record]
        return (end, start) if reference.orientation == "-" else (start, end)

    if not uses:
        raise _DecodeFailure("BRep wire is disconnected or open")
    Adjacency: dict[int, list[tuple[_Reference, int]]] = {}
    for Use in reversed(uses):
        StartVertex, EndVertex = Endpoints(Use)
        Adjacency.setdefault(StartVertex, []).append((Use, EndVertex))
    StartVertex = Endpoints(uses[0])[0]
    VertexStack = [StartVertex]
    EdgeStack: list[_Reference] = []
    Circuit: list[_Reference] = []
    while VertexStack:
        Outgoing = Adjacency.get(VertexStack[-1])
        if Outgoing:
            Use, EndVertex = Outgoing.pop()
            EdgeStack.append(Use)
            VertexStack.append(EndVertex)
            continue
        VertexStack.pop()
        if EdgeStack:
            Circuit.append(EdgeStack.pop())
    Circuit.reverse()
    if (
        len(Circuit) != len(uses)
        or Endpoints(Circuit[0])[0] != Endpoints(Circuit[-1])[1]
        or any(
            Endpoints(LeftUse)[1] != Endpoints(RightUse)[0]
            for LeftUse, RightUse in zip(Circuit, Circuit[1:])
        )
    ):
        raise _DecodeFailure("BRep wire is disconnected or open")
    return Circuit


# parsed analytic records become the format-neutral BREP topology graph
def _model(
    curves: tuple[BrepCurve, ...],
    surfaces: tuple[BrepSurface, ...],
    records: Mapping[int, _ShapeRecord],
    root: _Reference,
    id_prefix: str,
    design_body_id: str,
    attributes: Mapping[str, Any],
) -> BrepModel:
    vertices: list[BrepVertex] = []
    edges: list[BrepEdge] = []
    vertex_ids: dict[int, str] = {}
    edge_ids: dict[int, str] = {}
    edge_vertices: dict[int, tuple[int, int]] = {}
    for number, record in sorted(records.items(), reverse=True):
        if record.kind == b"Ve":
            geometry = record.geometry
            if not isinstance(geometry, _VertexData) or record.children:
                raise _DecodeFailure("invalid BRep vertex topology")
            identifier = f"{id_prefix}:vertex:{number}"
            vertex_ids[number] = identifier
            vertices.append(BrepVertex(identifier, geometry.point, geometry.tolerance))
    for number, record in sorted(records.items(), reverse=True):
        if record.kind != b"Ed":
            continue
        geometry = record.geometry
        if not isinstance(geometry, _EdgeData) or len(record.children) != 2:
            raise _DecodeFailure("invalid BRep edge topology")
        forward = [child for child in record.children if child.orientation == "+"]
        reversed_values = [
            child for child in record.children if child.orientation == "-"
        ]
        if len(forward) != 1 or len(reversed_values) != 1:
            raise _DecodeFailure("ambiguous BRep edge vertices")
        if any(records[child.record].kind != b"Ve" for child in record.children):
            raise _DecodeFailure("BRep edge references a non-vertex")
        identifier = f"{id_prefix}:edge:{number}"
        edge_ids[number] = identifier
        edge_vertices[number] = (forward[0].record, reversed_values[0].record)
        edges.append(
            BrepEdge(
                identifier,
                vertex_ids[forward[0].record],
                vertex_ids[reversed_values[0].record],
                f"{id_prefix}:curve:{geometry.curve}",
                geometry.first,
                geometry.last,
                geometry.tolerance,
            )
        )
    coedges: list[BrepCoedge] = []
    loops: list[BrepLoop] = []
    faces: list[BrepFace] = []
    face_ids: dict[int, str] = {}
    for number, record in sorted(records.items(), reverse=True):
        if record.kind != b"Fa":
            continue
        geometry = record.geometry
        if not isinstance(geometry, _FaceData) or not record.children:
            raise _DecodeFailure("ambiguous BRep face boundary")
        loop_ids: list[str] = []
        for wire_index, wire_reference in enumerate(record.children, 1):
            if wire_reference.orientation not in {"+", "-"}:
                raise _DecodeFailure("unsupported BRep wire orientation")
            wire = records[wire_reference.record]
            if wire.kind != b"Wi" or not wire.children:
                raise _DecodeFailure("BRep face references an invalid wire")
            uses = list(wire.children)
            if wire_reference.orientation == "-":
                uses = [
                    _Reference(_opposite(use.orientation), use.record)
                    for use in reversed(uses)
                ]
            uses = _OrderWireUses(uses, edge_vertices)
            coedge_ids: list[str] = []
            for use_index, use in enumerate(uses, 1):
                if use.orientation not in {"+", "-"}:
                    raise _DecodeFailure("unsupported BRep coedge orientation")
                if records[use.record].kind != b"Ed":
                    raise _DecodeFailure("BRep wire references a non-edge")
                suffix = (
                    f"{wire_index}:{use_index}"
                    if len(record.children) > 1
                    else str(use_index)
                )
                identifier = f"{id_prefix}:coedge:{number}:{suffix}"
                coedges.append(
                    BrepCoedge(
                        identifier,
                        edge_ids[use.record],
                        reversed=use.orientation == "-",
                    )
                )
                coedge_ids.append(identifier)
            suffix = f":{wire_index}" if len(record.children) > 1 else ""
            loop_id = f"{id_prefix}:loop:{number}{suffix}"
            loops.append(BrepLoop(loop_id, tuple(coedge_ids), wire_index == 1))
            loop_ids.append(loop_id)
        face_id = f"{id_prefix}:face:{number}"
        face_ids[number] = face_id
        faces.append(
            BrepFace(
                face_id,
                f"{id_prefix}:surface:{geometry.surface}",
                tuple(loop_ids),
                True,
                geometry.tolerance,
                attributes={"natural_restriction": geometry.natural},
            )
        )
    face_uses: list[BrepFaceUse] = []
    shells: list[BrepShell] = []
    shell_ids: dict[int, str] = {}
    for number, record in sorted(records.items(), reverse=True):
        if record.kind != b"Sh":
            continue
        if not record.children:
            raise _DecodeFailure("empty BRep shell")
        use_ids: list[str] = []
        for index, child in enumerate(record.children, 1):
            if child.orientation not in {"+", "-"}:
                raise _DecodeFailure("unsupported BRep face orientation")
            if records[child.record].kind != b"Fa":
                raise _DecodeFailure("BRep shell references a non-face")
            identifier = f"{id_prefix}:face-use:{number}:{index}"
            face_uses.append(
                BrepFaceUse(
                    identifier,
                    face_ids[child.record],
                    reversed=child.orientation == "-",
                )
            )
            use_ids.append(identifier)
        shell_id = f"{id_prefix}:shell:{number}"
        shell_ids[number] = shell_id
        shells.append(BrepShell(shell_id, tuple(use_ids), record.flags[4] == "1"))
    shell_uses: list[BrepShellUse] = []
    regions: list[BrepRegion] = []
    region_ids: dict[int, str] = {}
    for number, record in sorted(records.items(), reverse=True):
        if record.kind != b"So":
            continue
        if not record.children:
            raise _DecodeFailure("empty BRep solid")
        use_ids: list[str] = []
        for index, child in enumerate(record.children, 1):
            if child.orientation not in {"+", "-"}:
                raise _DecodeFailure("unsupported BRep shell orientation")
            if records[child.record].kind != b"Sh":
                raise _DecodeFailure("BRep solid references a non-shell")
            identifier = f"{id_prefix}:shell-use:{number}:{index}"
            shell_uses.append(
                BrepShellUse(
                    identifier,
                    shell_ids[child.record],
                    reversed=child.orientation == "-",
                )
            )
            use_ids.append(identifier)
        region_id = f"{id_prefix}:region:{number}"
        region_ids[number] = region_id
        regions.append(BrepRegion(region_id, tuple(use_ids), True))
    root_regions: list[str] = []
    root_vertices: list[str] = []
    seen: set[tuple[int, str]] = set()

    def collect(reference: _Reference) -> None:
        key = (reference.record, reference.orientation)
        if key in seen:
            raise _DecodeFailure("ambiguous repeated BRep root topology")
        seen.add(key)
        record = records[reference.record]
        if record.kind in {b"Co", b"CS"}:
            if not record.children:
                raise _DecodeFailure("empty BRep aggregate")
            for child in record.children:
                collect(
                    _Reference(
                        _compose(reference.orientation, child.orientation),
                        child.record,
                    )
                )
            return
        if record.kind == b"So":
            if reference.orientation != "+":
                raise _DecodeFailure("unsupported reversed BRep solid")
            root_regions.append(region_ids[reference.record])
            return
        if record.kind == b"Sh":
            use_id = f"{id_prefix}:shell-use:root:{len(root_regions) + 1}"
            shell_uses.append(
                BrepShellUse(
                    use_id,
                    shell_ids[reference.record],
                    reversed=reference.orientation == "-",
                )
            )
            region_id = f"{id_prefix}:region:root:{len(root_regions) + 1}"
            regions.append(BrepRegion(region_id, (use_id,), False))
            root_regions.append(region_id)
            return
        if record.kind == b"Fa" and reference.orientation in {"+", "-"}:
            ordinal = len(root_regions) + 1
            face_use_id = f"{id_prefix}:face-use:root:{ordinal}"
            face_uses.append(
                BrepFaceUse(
                    face_use_id,
                    face_ids[reference.record],
                    reversed=reference.orientation == "-",
                )
            )
            shell_id = f"{id_prefix}:shell:root:{ordinal}"
            shells.append(BrepShell(shell_id, (face_use_id,), False))
            shell_use_id = f"{id_prefix}:shell-use:root:{ordinal}"
            shell_uses.append(BrepShellUse(shell_use_id, shell_id))
            region_id = f"{id_prefix}:region:root:{ordinal}"
            regions.append(BrepRegion(region_id, (shell_use_id,), False))
            root_regions.append(region_id)
            return
        if record.kind == b"Ve" and reference.orientation == "+":
            root_vertices.append(vertex_ids[reference.record])
            return
        raise _DecodeFailure("unsupported BRep root topology")

    collect(root)
    body = BrepBody(
        f"{id_prefix}:body:1",
        tuple(root_regions),
        design_body_id=design_body_id,
        vertex_ids=tuple(root_vertices),
        attributes=dict(attributes),
    )
    result = BrepModel(
        curves=curves,
        surfaces=surfaces,
        vertices=tuple(vertices),
        edges=tuple(edges),
        coedges=tuple(coedges),
        loops=tuple(loops),
        faces=tuple(faces),
        face_uses=tuple(face_uses),
        shells=tuple(shells),
        shell_uses=tuple(shell_uses),
        regions=tuple(regions),
        bodies=(body,),
    )
    body_ids = frozenset({design_body_id}) if design_body_id else frozenset()
    if result.validate(body_ids):
        raise _DecodeFailure("decoded BRep model is invalid")
    return result


# strict decoding returns typed geometry only when every byte and topology link is proved
def decode_ascii_brep(
    data: bytes,
    *,
    id_prefix: str = "occ",
    design_body_id: str = "",
    attributes: Mapping[str, Any] | None = None,
) -> BrepModel | None:
    if (
        type(data) is not bytes
        or not data
        or len(data) > _MAX_BYTES
        or not isinstance(id_prefix, str)
        or not id_prefix
        or id_prefix != id_prefix.strip()
        or len(id_prefix) > 256
        or not isinstance(design_body_id, str)
        or len(design_body_id) > 512
        or (attributes is not None and not isinstance(attributes, Mapping))
    ):
        return None
    try:
        tokens = _Tokens(data)
        if tokens.peek() == b"DBRep_DrawableShape":
            tokens.take()
        tokens.expect(b"CASCADE")
        tokens.expect(b"Topology")
        tokens.expect(b"V1,")
        tokens.expect(b"(c)")
        tokens.expect(b"Matra-Datavision")
        locations = _model_locations(tokens)
        curve2d_count = _curves(tokens, b"Curve2ds", 2)
        curve_count = _count(tokens, b"Curves", _MAX_GEOMETRY)
        curves: list[BrepCurve] = []
        for index in range(1, curve_count + 1):
            kind = tokens.integer(1, 9)
            if kind not in {1, 2}:
                raise _DecodeFailure("unsupported BRep curve type")
            origin = _vector(tokens)
            axis = _vector(tokens)
            if kind == 1:
                if not _unit(axis):
                    raise _DecodeFailure("invalid BRep line direction")
                curves.append(
                    LineCurve(
                        f"{id_prefix}:curve:{index}",
                        origin,
                        axis,
                        attributes={"opencascade_index": index},
                    )
                )
                continue
            x_direction = _vector(tokens)
            y_direction = _vector(tokens)
            radius = tokens.number()
            if not _IsFrame(axis, x_direction, y_direction) or radius <= 0.0:
                raise _DecodeFailure("invalid BRep circle")
            curves.append(
                CircleCurve(
                    f"{id_prefix}:curve:{index}",
                    origin,
                    axis,
                    x_direction,
                    radius,
                    attributes={"opencascade_index": index},
                )
            )
        _zero_table(tokens, b"Polygon3D")
        _zero_table(tokens, b"PolygonOnTriangulations")
        surface_count = _count(tokens, b"Surfaces", _MAX_GEOMETRY)
        surfaces: list[BrepSurface] = []
        for index in range(1, surface_count + 1):
            kind = tokens.integer(1, 11)
            if kind not in {1, 2}:
                raise _DecodeFailure("unsupported BRep surface type")
            origin = _vector(tokens)
            normal = _vector(tokens)
            x_direction = _vector(tokens)
            y_direction = _vector(tokens)
            if not _IsFrame(normal, x_direction, y_direction):
                raise _DecodeFailure("invalid BRep surface frame")
            properties = {
                "opencascade_index": index,
                "reference_y": (
                    y_direction.x,
                    y_direction.y,
                    y_direction.z,
                ),
            }
            if kind == 1:
                surfaces.append(
                    PlaneSurface(
                        f"{id_prefix}:surface:{index}",
                        origin,
                        normal,
                        x_direction,
                        attributes=properties,
                    )
                )
                continue
            radius = tokens.number()
            if radius <= 0.0:
                raise _DecodeFailure("invalid BRep cylinder")
            surfaces.append(
                CylinderSurface(
                    f"{id_prefix}:surface:{index}",
                    origin,
                    normal,
                    x_direction,
                    radius,
                    attributes=properties,
                )
            )
        _zero_table(tokens, b"Triangulations")
        shape_count = _count(tokens, b"TShapes", _MAX_SHAPES)
        if shape_count == 0:
            raise _DecodeFailure("empty BRep topology")
        records = _shape_records(
            tokens,
            shape_count,
            curve_count,
            curve2d_count,
            surface_count,
            len(locations),
        )
        root = _reference(tokens, shape_count, len(locations))
        if root is None or root.orientation != "+" or tokens.peek() is not None:
            raise _DecodeFailure("unsupported BRep root")
        curves, surfaces, records, root = _ApplyLocations(
            tuple(curves), tuple(surfaces), records, root, locations, id_prefix
        )
        return _model(
            tuple(curves),
            tuple(surfaces),
            records,
            root,
            id_prefix,
            design_body_id,
            attributes or {},
        )
    except (_DecodeFailure, KeyError, TypeError, ValueError, OverflowError):
        return None


def is_structurally_valid_ascii_brep(data: bytes) -> bool:
    if type(data) is not bytes or not data or len(data) > _MAX_BYTES:
        return False
    try:
        offset = 0
        payload = None
        while offset < len(data):
            line_end = data.find(b"\n", offset)
            if line_end < 0:
                line_end = len(data)
            body = data[offset:line_end]
            if len(body) > 99:
                break
            while body.endswith(b"\r"):
                body = body[:-1]
            if body in _VERSION_LINES:
                if body != _VERSION_LINE:
                    raise _DecodeFailure("unsupported BRep version line")
                payload = data[offset:]
                break
            if line_end == len(data):
                break
            offset = line_end + 1
        if payload is None:
            raise _DecodeFailure("invalid BRep version line")
        tokens = _Tokens(payload)
        tokens.expect(b"CASCADE")
        tokens.expect(b"Topology")
        tokens.expect(b"V1,")
        tokens.expect(b"(c)")
        tokens.expect(b"Matra-Datavision")
        locations = _locations(tokens)
        curves2d = _curves(tokens, b"Curve2ds", 2)
        curves3d = _curves(tokens, b"Curves", 3)
        polygons3d = _polygon3d(tokens)
        polygons_on_triangulations = _polygons_on_triangulations(tokens)
        surfaces = _surfaces(tokens)
        triangulations = _triangulations(tokens)
        _shape_structure(
            tokens,
            locations,
            curves2d,
            curves3d,
            polygons3d,
            polygons_on_triangulations,
            surfaces,
            triangulations,
        )
        return True
    except (_DecodeFailure, KeyError, TypeError, ValueError, OverflowError):
        return False
