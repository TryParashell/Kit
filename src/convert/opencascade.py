from __future__ import annotations

from dataclasses import dataclass
from math import isclose, isfinite, sqrt
import re
from sys import float_info
from typing import Any, Mapping

from interchange import (
    BrepBody,
    BrepCoedge,
    BrepEdge,
    BrepFace,
    BrepFaceUse,
    BrepLoop,
    BrepModel,
    BrepRegion,
    BrepShell,
    BrepShellUse,
    BrepVertex,
    LineCurve,
    PlaneSurface,
    Vector3,
)


_MAX_BYTES = 128 * 1024 * 1024
_MAX_GEOMETRY = 300_000
_MAX_SHAPES = 500_000
_MAX_TOKENS = 12_000_000
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

    def peek_starts_next_line(self) -> bool:
        if self.peek() is None or self._lookahead is None:
            return False
        separation = self._data[self._last_end : self._lookahead.start()]
        return re.fullmatch(rb"[ \t]*\r?\n[ \t]*", separation) is not None

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


@dataclass(frozen=True, slots=True)
class _VertexData:
    tolerance: float
    point: Vector3


@dataclass(frozen=True, slots=True)
class _EdgeData:
    tolerance: float
    curve: int
    first: float
    last: float


@dataclass(frozen=True, slots=True)
class _FaceData:
    natural: bool
    tolerance: float
    surface: int


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


def _frame(normal: Vector3, x_direction: Vector3, y_direction: Vector3) -> bool:
    expected_y = _cross(normal, x_direction)
    return (
        _unit(normal)
        and _unit(x_direction)
        and _unit(y_direction)
        and isclose(_dot(normal, x_direction), 0.0, abs_tol=1e-10)
        and isclose(_dot(normal, y_direction), 0.0, abs_tol=1e-10)
        and isclose(_dot(x_direction, y_direction), 0.0, abs_tol=1e-10)
        and isclose(expected_y.x, y_direction.x, abs_tol=1e-10)
        and isclose(expected_y.y, y_direction.y, abs_tol=1e-10)
        and isclose(expected_y.z, y_direction.z, abs_tol=1e-10)
    )


def _count(tokens: _Tokens, label: bytes, maximum: int) -> int:
    tokens.expect(label)
    return tokens.integer(0, maximum)


def _zero_table(tokens: _Tokens, label: bytes) -> None:
    if _count(tokens, label, 0) != 0:
        raise _DecodeFailure("unsupported BRep table")


def _reference(tokens: _Tokens, shape_count: int) -> _Reference | None:
    token = tokens.take()
    if token == b"*":
        return None
    if len(token) < 2 or token[:1] not in {b"+", b"-", b"i", b"e"}:
        raise _DecodeFailure("invalid BRep shape reference")
    number = token[1:]
    if _INTEGER_PATTERN.fullmatch(number) is None:
        raise _DecodeFailure("invalid BRep shape reference")
    record = int(number)
    if record < 1 or record > shape_count or tokens.integer(0, 0) != 0:
        raise _DecodeFailure("unsupported BRep shape location")
    return _Reference(token[:1].decode("ascii"), record)


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
    for datum, power in (*right, *left):
        if result and result[-1][0] == datum:
            combined = result[-1][1] + power
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


def _location_transform(tokens: _Tokens) -> None:
    values = tuple(tokens.number() for _ in range(12))
    determinant = (
        values[0] * (values[5] * values[10] - values[6] * values[9])
        - values[1] * (values[4] * values[10] - values[6] * values[8])
        + values[2] * (values[4] * values[9] - values[5] * values[8])
    )
    if not isfinite(determinant) or abs(determinant) < float_info.min:
        raise _DecodeFailure("singular BRep location transform")


def _locations(tokens: _Tokens) -> int:
    count = _count(tokens, b"Locations", _MAX_GEOMETRY)
    locations: list[tuple[tuple[int, int], ...]] = []
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
        if not location or location in locations:
            raise _DecodeFailure("invalid BRep location record")
        locations.append(location)
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
        node_values = tuple(
            tokens.integer(1, _MAX_GEOMETRY) for _ in range(nodes)
        )
        maximum_nodes.append(max(node_values))
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
        if tokens.peek() == b"2" and tokens.peek_starts_next_line():
            tokens.take()
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
        kinds[record] = kind
    root = _structural_reference(tokens, count, locations)
    if root is None or root[0].record not in kinds or tokens.peek() is not None:
        raise _DecodeFailure("invalid BRep root shape")


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


def _edge_geometry(tokens: _Tokens, curve_count: int) -> _EdgeData:
    tolerance = tokens.number()
    same_parameter = tokens.integer(0, 1)
    same_range = tokens.integer(0, 1)
    degenerate = tokens.integer(0, 1)
    if tolerance < 0.0 or not same_parameter or not same_range or degenerate:
        raise _DecodeFailure("unsupported BRep edge state")
    representations: list[tuple[int, float, float]] = []
    while True:
        representation = tokens.integer(0, 7)
        if representation == 0:
            break
        if representation != 1:
            raise _DecodeFailure("unsupported BRep edge representation")
        curve = tokens.integer(1, curve_count)
        if tokens.integer(0, 0) != 0:
            raise _DecodeFailure("unsupported BRep edge location")
        representations.append((curve, tokens.number(), tokens.number()))
    if len(representations) != 1:
        raise _DecodeFailure("ambiguous BRep edge geometry")
    curve, first, last = representations[0]
    return _EdgeData(tolerance, curve, first, last)


def _face_geometry(tokens: _Tokens, surface_count: int) -> _FaceData:
    natural = tokens.integer(0, 1)
    tolerance = tokens.number()
    surface = tokens.integer(1, surface_count)
    if tolerance < 0.0 or tokens.integer(0, 0) != 0:
        raise _DecodeFailure("unsupported BRep face geometry")
    return _FaceData(bool(natural), tolerance, surface)


def _shape_records(
    tokens: _Tokens, shape_count: int, curve_count: int, surface_count: int
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
            geometry = _edge_geometry(tokens, curve_count)
        elif kind == b"Fa":
            geometry = _face_geometry(tokens, surface_count)
        flag_token = tokens.take()
        if _FLAGS_PATTERN.fullmatch(flag_token) is None:
            raise _DecodeFailure("invalid BRep shape flags")
        children: list[_Reference] = []
        while True:
            child = _reference(tokens, shape_count)
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


def _model(
    curves: tuple[LineCurve, ...],
    surfaces: tuple[PlaneSurface, ...],
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
        if (
            not isinstance(geometry, _FaceData)
            or len(record.children) != 1
            or record.children[0].orientation not in {"+", "-"}
        ):
            raise _DecodeFailure("ambiguous BRep face boundary")
        wire_reference = record.children[0]
        wire = records[wire_reference.record]
        if wire.kind != b"Wi" or not wire.children:
            raise _DecodeFailure("BRep face references an invalid wire")
        uses = list(wire.children)
        if wire_reference.orientation == "-":
            uses = [
                _Reference(_opposite(use.orientation), use.record)
                for use in reversed(uses)
            ]
        coedge_ids: list[str] = []
        for index, use in enumerate(uses, 1):
            if use.orientation not in {"+", "-"}:
                raise _DecodeFailure("unsupported BRep coedge orientation")
            if records[use.record].kind != b"Ed":
                raise _DecodeFailure("BRep wire references a non-edge")
            identifier = f"{id_prefix}:coedge:{number}:{index}"
            coedges.append(
                BrepCoedge(
                    identifier,
                    edge_ids[use.record],
                    reversed=use.orientation == "-",
                )
            )
            coedge_ids.append(identifier)
        loop_id = f"{id_prefix}:loop:{number}"
        loops.append(BrepLoop(loop_id, tuple(coedge_ids), True))
        face_id = f"{id_prefix}:face:{number}"
        face_ids[number] = face_id
        faces.append(
            BrepFace(
                face_id,
                f"{id_prefix}:surface:{geometry.surface}",
                (loop_id,),
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
        _zero_table(tokens, b"Locations")
        _zero_table(tokens, b"Curve2ds")
        curve_count = _count(tokens, b"Curves", _MAX_GEOMETRY)
        curves: list[LineCurve] = []
        for index in range(1, curve_count + 1):
            if tokens.integer(1, 9) != 1:
                raise _DecodeFailure("unsupported BRep curve type")
            origin = _vector(tokens)
            direction = _vector(tokens)
            if not _unit(direction):
                raise _DecodeFailure("invalid BRep line direction")
            curves.append(
                LineCurve(
                    f"{id_prefix}:curve:{index}",
                    origin,
                    direction,
                    attributes={"opencascade_index": index},
                )
            )
        _zero_table(tokens, b"Polygon3D")
        _zero_table(tokens, b"PolygonOnTriangulations")
        surface_count = _count(tokens, b"Surfaces", _MAX_GEOMETRY)
        surfaces: list[PlaneSurface] = []
        for index in range(1, surface_count + 1):
            if tokens.integer(1, 11) != 1:
                raise _DecodeFailure("unsupported BRep surface type")
            origin = _vector(tokens)
            normal = _vector(tokens)
            x_direction = _vector(tokens)
            y_direction = _vector(tokens)
            if not _frame(normal, x_direction, y_direction):
                raise _DecodeFailure("invalid BRep surface frame")
            surfaces.append(
                PlaneSurface(
                    f"{id_prefix}:surface:{index}",
                    origin,
                    normal,
                    x_direction,
                    attributes={
                        "opencascade_index": index,
                        "reference_y": (
                            y_direction.x,
                            y_direction.y,
                            y_direction.z,
                        ),
                    },
                )
            )
        _zero_table(tokens, b"Triangulations")
        shape_count = _count(tokens, b"TShapes", _MAX_SHAPES)
        if shape_count == 0:
            raise _DecodeFailure("empty BRep topology")
        records = _shape_records(tokens, shape_count, curve_count, surface_count)
        root = _reference(tokens, shape_count)
        if root is None or root.orientation != "+" or tokens.peek() is not None:
            raise _DecodeFailure("unsupported BRep root")
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
        for line in data.splitlines(keepends=True):
            body = line[:-1] if line.endswith(b"\n") else line
            body = body[:-1] if body.endswith(b"\r") else body
            if len(body) > 99:
                break
            if body in _VERSION_LINES:
                if body != _VERSION_LINE:
                    raise _DecodeFailure("unsupported BRep version line")
                payload = data[offset:]
                break
            offset += len(line)
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
