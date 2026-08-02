from __future__ import annotations

from collections import deque
from collections.abc import Sequence
from dataclasses import dataclass
import math
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
    BrepWire,
    CircleCurve,
    CirclePcurve,
    ConeSurface,
    CylinderSurface,
    EllipseCurve,
    IntersectionCurve,
    LineCurve,
    LinePcurve,
    NativeCurve,
    NativePcurve,
    NativeSurface,
    NurbsCurve,
    NurbsPcurve,
    NurbsSurface,
    OffsetSurface,
    PlaneSurface,
    SphereSurface,
    TorusSurface,
    Transform,
    Vector2,
    Vector3,
)


Point = tuple[float, float, float]
Triangle = tuple[int, int, int]
Geometry = tuple[
    tuple[Point, Point, Point],
    tuple[float, float, float],
    Point,
    Point,
    Point,
]


class FreeCADBrepWriteError(ValueError):
    __slots__ = ()

    reason = "writer_unimplemented"


@dataclass(frozen=True, slots=True)
class _ShapeRecord:
    key: str
    kind: str
    geometry: tuple[str, ...]
    flags: str
    children: tuple[tuple[str, bool], ...]


@dataclass(frozen=True, slots=True)
class _EdgePcurve:
    index: int
    first: float
    last: float


@dataclass(frozen=True, slots=True)
class _GeneratedPcurve:
    record: str
    first: float
    last: float
    start: tuple[float, float]
    end: tuple[float, float]


@dataclass(frozen=True, slots=True)
class _SeamBand:
    face_id: str
    loop_ids: tuple[str, str]
    low_coedge_id: str
    high_coedge_id: str
    low_reversed: bool
    high_reversed: bool
    low_vertex_id: str
    high_vertex_id: str
    curve_record: str
    length: float
    first_pcurve_index: int
    second_pcurve_index: int


class _ModelGraph:
    __slots__ = (
        "bodies",
        "coedge_owner",
        "coedges",
        "curves",
        "edge_uses",
        "edges",
        "face_uses",
        "faces",
        "loop_face",
        "loops",
        "pcurves",
        "region_body",
        "regions",
        "shell_owners",
        "shell_uses",
        "shells",
        "surfaces",
        "vertices",
        "wire_body",
        "wires",
    )

    def __init__(self, model: BrepModel) -> None:
        self.vertices = {value.id: value for value in model.vertices}
        self.curves = {value.id: value for value in model.curves}
        self.edges = {value.id: value for value in model.edges}
        self.coedges = {value.id: value for value in model.coedges}
        self.loops = {value.id: value for value in model.loops}
        self.wires = {value.id: value for value in model.wires}
        self.faces = {value.id: value for value in model.faces}
        self.face_uses = {value.id: value for value in model.face_uses}
        self.shells = {value.id: value for value in model.shells}
        self.shell_uses = {value.id: value for value in model.shell_uses}
        self.regions = {value.id: value for value in model.regions}
        self.bodies = {value.id: value for value in model.bodies}
        self.pcurves = {value.id: value for value in model.pcurves}
        self.surfaces = {value.id: value for value in model.surfaces}
        self.coedge_owner: dict[str, tuple[str, str]] = {}
        self.loop_face: dict[str, str] = {}
        self.shell_owners: dict[str, list[tuple[str, str]]] = {
            value.id: [] for value in model.shells
        }
        self.region_body: dict[str, str] = {}
        self.wire_body: dict[str, str] = {}
        self.edge_uses: dict[str, list[str]] = {value.id: [] for value in model.edges}
        for loop in model.loops:
            for coedge_id in loop.coedge_ids:
                self._bind_coedge(coedge_id, "loop", loop.id)
        for wire in model.wires:
            for coedge_id in wire.coedge_ids:
                self._bind_coedge(coedge_id, "wire", wire.id)
        for face in model.faces:
            for loop_id in face.loop_ids:
                _bind_once(self.loop_face, loop_id, face.id, "loop", "face")
        face_use_owner: dict[str, str] = {}
        for shell in model.shells:
            for face_use_id in shell.face_use_ids:
                _bind_once(
                    face_use_owner,
                    face_use_id,
                    shell.id,
                    "face use",
                    "shell",
                )
                face_use = self.face_uses[face_use_id]
                self.shell_owners.setdefault(shell.id, []).append(
                    (face_use.id, face_use.face_id)
                )
        shell_use_owner: dict[str, str] = {}
        for region in model.regions:
            for shell_use_id in region.shell_use_ids:
                _bind_once(
                    shell_use_owner,
                    shell_use_id,
                    region.id,
                    "shell use",
                    "region",
                )
        for body in model.bodies:
            for region_id in body.region_ids:
                _bind_once(
                    self.region_body,
                    region_id,
                    body.id,
                    "region",
                    "body",
                )
            for wire_id in body.wire_ids:
                _bind_once(
                    self.wire_body,
                    wire_id,
                    body.id,
                    "wire",
                    "body",
                )
        _require_owned(self.coedge_owner, self.coedges, "coedge", "loop or wire")
        _require_owned(self.loop_face, self.loops, "loop", "face")
        _require_owned(face_use_owner, self.face_uses, "face use", "shell")
        _require_owned(shell_use_owner, self.shell_uses, "shell use", "region")
        _require_owned(self.region_body, self.regions, "region", "body")
        _require_owned(self.wire_body, self.wires, "wire", "body")
        used_faces = {face_use.face_id for face_use in model.face_uses}
        unused_face = next(
            (face_id for face_id in self.faces if face_id not in used_faces), None
        )
        if unused_face is not None:
            _unsupported(f"B-rep face {unused_face} has no face use")
        used_shells = {shell_use.shell_id for shell_use in model.shell_uses}
        unused_shell = next(
            (shell_id for shell_id in self.shells if shell_id not in used_shells), None
        )
        if unused_shell is not None:
            _unsupported(f"B-rep shell {unused_shell} has no shell use")
        for coedge in model.coedges:
            self.edge_uses[coedge.edge_id].append(coedge.id)
        for edge_id, uses in self.edge_uses.items():
            if not uses:
                _unsupported(f"B-rep edge {edge_id} has no coedge use")
            if len(uses) > 2:
                _unsupported(f"B-rep edge {edge_id} is non-manifold")

    def _bind_coedge(self, coedge_id: str, kind: str, owner_id: str) -> None:
        if coedge_id in self.coedge_owner:
            _unsupported(
                f"B-rep coedge {coedge_id} belongs to multiple loop or wire values"
            )
        self.coedge_owner[coedge_id] = (kind, owner_id)

    def face_for_coedge(self, coedge_id: str) -> BrepFace | None:
        kind, owner_id = self.coedge_owner[coedge_id]
        if kind == "wire":
            return None
        return self.faces[self.loop_face[owner_id]]


def _unsupported(message: str) -> None:
    raise FreeCADBrepWriteError(f"writer_unimplemented: {message}")


def _bind_once(
    owners: dict[str, str],
    value_id: str,
    owner_id: str,
    value_name: str,
    owner_name: str,
) -> None:
    if value_id in owners:
        _unsupported(
            f"B-rep {value_name} {value_id} belongs to multiple {owner_name} values"
        )
    owners[value_id] = owner_id


def _require_owned(
    owners: Mapping[str, object],
    values: Mapping[str, object],
    value_name: str,
    owner_name: str,
) -> None:
    missing = next((value_id for value_id in values if value_id not in owners), None)
    if missing is not None:
        _unsupported(f"B-rep {value_name} {missing} has no {owner_name}")


def _number(value: float) -> str:
    if value == 0.0:
        return "0"
    return format(value, ".17g")


def _point(value: Any) -> Point:
    if all(hasattr(value, axis) for axis in ("x", "y", "z")):
        point = (float(value.x), float(value.y), float(value.z))
    else:
        try:
            point = tuple(float(component) for component in value)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "each vertex must contain three finite coordinates"
            ) from exc
        if len(point) != 3:
            raise ValueError("each vertex must contain three finite coordinates")
    if not all(math.isfinite(component) for component in point):
        raise ValueError("each vertex must contain three finite coordinates")
    return point


def _subtract(left: Point, right: Point) -> Point:
    return tuple(left[index] - right[index] for index in range(3))


def _cross(left: Point, right: Point) -> Point:
    return (
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    )


def _dot(left: Point, right: Point) -> float:
    return sum(left[index] * right[index] for index in range(3))


def _length(vector: Point) -> float:
    return math.sqrt(_dot(vector, vector))


def _scale(vector: Point, factor: float) -> Point:
    return tuple(component * factor for component in vector)


def _values(values: Sequence[float]) -> str:
    return " ".join(_number(value) for value in values)


def _triangle(value: Any, vertex_count: int) -> Triangle:
    try:
        indices = tuple(value)
    except TypeError as exc:
        raise ValueError("each triangle must contain three vertex indices") from exc
    if len(indices) != 3 or any(
        isinstance(index, bool) or not isinstance(index, int) for index in indices
    ):
        raise ValueError("each triangle must contain three vertex indices")
    if len(set(indices)) != 3 or any(
        index < 0 or index >= vertex_count for index in indices
    ):
        raise ValueError("triangle vertex indices must be distinct and in range")
    return indices


def _geometry(
    points: tuple[Point, ...], facets: tuple[Triangle, ...], tolerance: float
):
    result: list[Geometry] = []
    for triangle in facets:
        corners = tuple(points[index] for index in triangle)
        edges = tuple(
            _subtract(corners[(index + 1) % 3], corners[index]) for index in range(3)
        )
        lengths = tuple(_length(edge) for edge in edges)
        if min(lengths) <= tolerance:
            raise ValueError("triangle edges must exceed the BRep tolerance")
        normal_vector = _cross(edges[0], _subtract(corners[2], corners[0]))
        normal_length = _length(normal_vector)
        if normal_length <= tolerance * max(lengths):
            raise ValueError("triangle area must exceed the BRep tolerance")
        normal = _scale(normal_vector, 1.0 / normal_length)
        x_direction = _scale(edges[0], 1.0 / lengths[0])
        y_direction = _cross(normal, x_direction)
        result.append((corners, lengths, normal, x_direction, y_direction))
    return tuple(result)


def _edge_uses(facets: tuple[Triangle, ...]):
    result: dict[tuple[int, int], list[tuple[int, int]]] = {}
    for facet_index, facet in enumerate(facets):
        for index in range(3):
            pair = (facet[index], facet[(index + 1) % 3])
            key = tuple(sorted(pair))
            result.setdefault(key, []).append((facet_index, 1 if pair == key else -1))
    return result


def _oriented_components(
    points: tuple[Point, ...], facets: tuple[Triangle, ...], tolerance: float
):
    uses = _edge_uses(facets)
    if any(len(edge_faces) > 2 for edge_faces in uses.values()):
        return None
    neighbors: dict[int, list[tuple[int, int]]] = {
        index: [] for index in range(len(facets))
    }
    for edge_faces in uses.values():
        if len(edge_faces) != 2:
            continue
        (left, left_sign), (right, right_sign) = edge_faces
        relation = -left_sign * right_sign
        neighbors[left].append((right, relation))
        neighbors[right].append((left, relation))
    flips = [0] * len(facets)
    components = []
    for start in range(len(facets)):
        if flips[start]:
            continue
        flips[start] = 1
        queue = deque([start])
        component = []
        while queue:
            current = queue.popleft()
            component.append(current)
            for neighbor, relation in neighbors[current]:
                expected = flips[current] * relation
                if flips[neighbor] and flips[neighbor] != expected:
                    return None
                if not flips[neighbor]:
                    flips[neighbor] = expected
                    queue.append(neighbor)
        components.append(tuple(sorted(component)))
    oriented = list(facets)
    for index, flip in enumerate(flips):
        if flip < 0:
            left, middle, right = oriented[index]
            oriented[index] = (left, right, middle)
    oriented_tuple = tuple(oriented)
    oriented_uses = _edge_uses(oriented_tuple)
    component_by_facet = [0] * len(facets)
    for component_index, component in enumerate(components):
        for facet_index in component:
            component_by_facet[facet_index] = component_index
    closed = [True] * len(components)
    for edge_faces in oriented_uses.values():
        if len(edge_faces) != 2:
            for facet_index, _ in edge_faces:
                closed[component_by_facet[facet_index]] = False
    for component_index, component in enumerate(components):
        is_closed = closed[component_index]
        if is_closed:
            volume = (
                sum(
                    _dot(
                        points[oriented_tuple[index][0]],
                        _cross(
                            points[oriented_tuple[index][1]],
                            points[oriented_tuple[index][2]],
                        ),
                    )
                    for index in component
                )
                / 6.0
            )
            if abs(volume) <= tolerance**3:
                is_closed = False
            elif volume < 0.0:
                for index in component:
                    left, middle, right = oriented[index]
                    oriented[index] = (left, right, middle)
        closed[component_index] = is_closed
    return tuple(oriented), tuple(components), tuple(closed)


def _header(
    points: tuple[Point, ...],
    facets: tuple[Triangle, ...],
    edges: tuple[tuple[int, int], ...],
    geometry: tuple[Geometry, ...],
):
    lines = [
        "DBRep_DrawableShape",
        "",
        "CASCADE Topology V1, (c) Matra-Datavision",
        "Locations 0",
        "Curve2ds 0",
        f"Curves {len(edges)}",
    ]
    for start, end in edges:
        vector = _subtract(points[end], points[start])
        direction = _scale(vector, 1.0 / _length(vector))
        lines.append(f"1 {_values(points[start] + direction)} ")
    lines.extend(
        [
            "Polygon3D 0",
            "PolygonOnTriangulations 0",
            f"Surfaces {len(facets)}",
        ]
    )
    for corners, _, normal, x_direction, y_direction in geometry:
        lines.append(f"1 {_values(corners[0] + normal + x_direction + y_direction)} ")
    lines.extend(["Triangulations 0", ""])
    return lines


def _vertex_record(point: Point, tolerance: str) -> list[str]:
    return ["Ve", tolerance, _values(point), "0 0", "", "0101101", "*"]


def _edge_record(
    tolerance: str,
    curve_index: int,
    length: float,
    start: int,
    end: int,
) -> list[str]:
    return [
        "Ed",
        f" {tolerance} 1 1 0",
        f"1  {curve_index} 0 0 {_number(length)}",
        "0",
        "",
        "0101000",
        f"+{start} 0 -{end} 0 *",
    ]


def _shared_brep(
    points: tuple[Point, ...],
    facets: tuple[Triangle, ...],
    components: tuple[tuple[int, ...], ...],
    closed: tuple[bool, ...],
    tolerance: float,
) -> bytes:
    geometry = _geometry(points, facets, tolerance)
    vertex_indices = tuple(sorted({index for facet in facets for index in facet}))
    edges = tuple(sorted(_edge_uses(facets)))
    component_count = len(components)
    solid_count = sum(closed)
    root_count = 1 if component_count > 1 else 0
    shape_count = (
        len(vertex_indices)
        + len(edges)
        + 2 * len(facets)
        + component_count
        + solid_count
        + root_count
    )
    ordinal = 1
    vertex_ordinals = {}
    for index in vertex_indices:
        vertex_ordinals[index] = ordinal
        ordinal += 1
    edge_ordinals = {}
    for edge in edges:
        edge_ordinals[edge] = ordinal
        ordinal += 1
    wire_ordinals = []
    face_ordinals = []
    for _ in facets:
        wire_ordinals.append(ordinal)
        face_ordinals.append(ordinal + 1)
        ordinal += 2
    shell_ordinals = []
    for _ in components:
        shell_ordinals.append(ordinal)
        ordinal += 1
    solid_ordinals: dict[int, int] = {}
    for component_index, is_closed in enumerate(closed):
        if is_closed:
            solid_ordinals[component_index] = ordinal
            ordinal += 1
    if component_count > 1:
        ordinal += 1
    if ordinal != shape_count + 1:
        raise ValueError("BRep topology record count is inconsistent")
    reference = lambda record: shape_count - record + 1
    tolerance_text = _number(tolerance)
    lines = _header(points, facets, edges, geometry)
    lines.append(f"TShapes {shape_count}")
    for index in vertex_indices:
        lines.extend(_vertex_record(points[index], tolerance_text))
    for curve_index, edge in enumerate(edges, 1):
        start, end = edge
        lines.extend(
            _edge_record(
                tolerance_text,
                curve_index,
                _length(_subtract(points[end], points[start])),
                reference(vertex_ordinals[start]),
                reference(vertex_ordinals[end]),
            )
        )
    for facet_index, facet in enumerate(facets):
        edge_values = []
        for index in range(3):
            pair = (facet[index], facet[(index + 1) % 3])
            edge = tuple(sorted(pair))
            sign = "+" if pair == edge else "-"
            edge_values.append(f"{sign}{reference(edge_ordinals[edge])} 0")
        lines.extend(
            [
                "Wi",
                "",
                "0101100",
                " ".join(edge_values) + " *",
                "Fa",
                f"0  {tolerance_text} {facet_index + 1} 0",
                "",
                "0101000",
                f"+{reference(wire_ordinals[facet_index])} 0 *",
            ]
        )
    for component_index, component in enumerate(components):
        lines.extend(
            [
                "Sh",
                "",
                "0101100" if closed[component_index] else "0101000",
                " ".join(f"+{reference(face_ordinals[index])} 0" for index in component)
                + " *",
            ]
        )
    for component_index, solid_ordinal in solid_ordinals.items():
        lines.extend(
            [
                "So",
                "",
                "1100000" if component_count == 1 else "0100000",
                f"+{reference(shell_ordinals[component_index])} 0 *",
            ]
        )
    if component_count > 1:
        roots = [
            solid_ordinals.get(index, shell_ordinals[index])
            for index in range(component_count)
        ]
        lines.extend(
            [
                "Co",
                "",
                "1100000",
                " ".join(f"+{reference(record)} 0" for record in roots) + " *",
            ]
        )
    lines.extend(["", "+1 0 "])
    return ("\n".join(lines) + "\n").encode("ascii")


def _independent_brep(
    points: tuple[Point, ...], facets: tuple[Triangle, ...], tolerance: float
) -> bytes:
    geometry = _geometry(points, facets, tolerance)
    directed_edges = tuple(
        (facet[index], facet[(index + 1) % 3]) for facet in facets for index in range(3)
    )
    lines = _header(points, facets, directed_edges, geometry)
    shape_count = len(facets) * 8 + 1
    lines.append(f"TShapes {shape_count}")
    tolerance_text = _number(tolerance)
    face_references = []
    curve_index = 1
    record_index = 1
    for facet, facet_geometry in zip(facets, geometry):
        corners, lengths, _, _, _ = facet_geometry
        references = tuple(
            shape_count - (record_index + offset) + 1 for offset in range(8)
        )
        vertex_references = (references[0], references[1], references[3])
        lines.extend(_vertex_record(corners[0], tolerance_text))
        lines.extend(_vertex_record(corners[1], tolerance_text))
        lines.extend(
            _edge_record(
                tolerance_text,
                curve_index,
                lengths[0],
                vertex_references[0],
                vertex_references[1],
            )
        )
        curve_index += 1
        lines.extend(_vertex_record(corners[2], tolerance_text))
        for edge_index in (1, 2):
            lines.extend(
                _edge_record(
                    tolerance_text,
                    curve_index,
                    lengths[edge_index],
                    vertex_references[edge_index],
                    vertex_references[(edge_index + 1) % 3],
                )
            )
            curve_index += 1
        lines.extend(
            [
                "Wi",
                "",
                "0101100",
                f"+{references[2]} 0 +{references[4]} 0 +{references[5]} 0 *",
                "Fa",
                f"0  {tolerance_text} {(record_index - 1) // 8 + 1} 0",
                "",
                "0101000",
                f"+{references[6]} 0 *",
            ]
        )
        face_references.append(references[7])
        record_index += 8
    lines.extend(
        [
            "Co",
            "",
            "1100000",
            " ".join(f"+{reference} 0" for reference in face_references) + " *",
            "",
            "+1 0 ",
        ]
    )
    return ("\n".join(lines) + "\n").encode("ascii")


def _vector2(value: Vector2) -> tuple[float, float]:
    return value.x, value.y


def _vector3(value: Vector3) -> Point:
    return value.x, value.y, value.z


def _unit2(value: Vector2, label: str) -> tuple[tuple[float, float], float]:
    length = math.hypot(value.x, value.y)
    if not math.isfinite(length) or length <= 0.0:
        _unsupported(f"{label} has an invalid direction")
    return (value.x / length, value.y / length), length


def _unit3(value: Vector3, label: str) -> tuple[Point, float]:
    raw = _vector3(value)
    length = _length(raw)
    if not math.isfinite(length) or length <= 0.0:
        _unsupported(f"{label} has an invalid direction")
    return _scale(raw, 1.0 / length), length


def _frame(axis: Vector3, reference: Vector3, label: str) -> tuple[Point, Point, Point]:
    normalized_axis, _ = _unit3(axis, label)
    normalized_reference, _ = _unit3(reference, label)
    if abs(_dot(normalized_axis, normalized_reference)) > 1e-9:
        _unsupported(f"{label} axis and reference direction are not orthogonal")
    y_direction = _cross(normalized_axis, normalized_reference)
    if abs(_length(y_direction) - 1.0) > 1e-9:
        _unsupported(f"{label} has an invalid coordinate frame")
    return normalized_axis, normalized_reference, y_direction


def _bspline_layout(
    degree: int,
    pole_count: int,
    knots: Sequence[float],
    multiplicities: Sequence[int],
    periodic: bool,
    label: str,
) -> None:
    if (
        type(degree) is not int
        or not 0 < degree <= 25
        or pole_count < 2
        or len(knots) != len(multiplicities)
        or len(knots) < 2
        or any(not math.isfinite(value) for value in knots)
        or any(left >= right for left, right in zip(knots, knots[1:]))
    ):
        _unsupported(f"{label} has an invalid B-spline layout")
    for index, value in enumerate(multiplicities):
        maximum = degree
        if not periodic and index in {0, len(multiplicities) - 1}:
            maximum = degree + 1
        if type(value) is not int or not 1 <= value <= maximum:
            _unsupported(f"{label} has an invalid knot multiplicity")
    if periodic:
        if multiplicities[0] != multiplicities[-1]:
            _unsupported(f"{label} has inconsistent periodic multiplicities")
        expected = sum(multiplicities[:-1])
    else:
        expected = sum(multiplicities) - degree - 1
    if expected != pole_count:
        _unsupported(f"{label} pole and knot counts are inconsistent")


def _curve_record(value: object) -> tuple[str, float]:
    if isinstance(value, LineCurve):
        direction, scale = _unit3(value.direction, f"line curve {value.id}")
        return f"1 {_values(_vector3(value.origin) + direction)} ", scale
    if isinstance(value, CircleCurve):
        axis, reference, y_direction = _frame(
            value.axis,
            value.reference_direction,
            f"circle curve {value.id}",
        )
        return (
            f"2 {_values(_vector3(value.center) + axis + reference + y_direction + (value.radius,))} ",
            1.0,
        )
    if isinstance(value, EllipseCurve):
        axis, reference, y_direction = _frame(
            value.axis,
            value.reference_direction,
            f"ellipse curve {value.id}",
        )
        return (
            f"3 {_values(_vector3(value.center) + axis + reference + y_direction + (value.major_radius, value.minor_radius))} ",
            1.0,
        )
    if isinstance(value, NurbsCurve):
        _bspline_layout(
            value.degree,
            len(value.control_points),
            value.knots,
            value.multiplicities,
            value.periodic,
            f"NURBS curve {value.id}",
        )
        rational = bool(value.weights)
        if rational and (
            len(value.weights) != len(value.control_points)
            or any(
                not math.isfinite(weight) or weight <= 0.0 for weight in value.weights
            )
        ):
            _unsupported(f"NURBS curve {value.id} has invalid weights")
        fields = [
            "7",
            "1" if rational else "0",
            "1" if value.periodic else "0",
            str(value.degree),
            str(len(value.control_points)),
            str(len(value.knots)),
        ]
        for index, point in enumerate(value.control_points):
            fields.extend(_number(component) for component in _vector3(point))
            if rational:
                fields.append(_number(value.weights[index]))
        for knot, multiplicity in zip(value.knots, value.multiplicities):
            fields.extend((_number(knot), str(multiplicity)))
        return " ".join(fields) + " ", 1.0
    if isinstance(value, (IntersectionCurve, NativeCurve)):
        _unsupported(f"curve {value.id} of type {type(value).__name__} is unsupported")
    _unsupported(f"curve type {type(value).__name__} is unsupported")


def _pcurve_record(value: object) -> tuple[str, float]:
    if isinstance(value, LinePcurve):
        direction, scale = _unit2(value.direction, f"line pcurve {value.id}")
        return f"1 {_values(_vector2(value.origin) + direction)} ", scale
    if isinstance(value, CirclePcurve):
        return (
            f"2 {_values(_vector2(value.center) + (1.0, 0.0, 0.0, 1.0, value.radius))} ",
            1.0,
        )
    if isinstance(value, NurbsPcurve):
        _bspline_layout(
            value.degree,
            len(value.control_points),
            value.knots,
            value.multiplicities,
            value.periodic,
            f"NURBS pcurve {value.id}",
        )
        rational = bool(value.weights)
        if rational and (
            len(value.weights) != len(value.control_points)
            or any(
                not math.isfinite(weight) or weight <= 0.0 for weight in value.weights
            )
        ):
            _unsupported(f"NURBS pcurve {value.id} has invalid weights")
        fields = [
            "7",
            "1" if rational else "0",
            "1" if value.periodic else "0",
            str(value.degree),
            str(len(value.control_points)),
            str(len(value.knots)),
        ]
        for index, point in enumerate(value.control_points):
            fields.extend(_number(component) for component in _vector2(point))
            if rational:
                fields.append(_number(value.weights[index]))
        for knot, multiplicity in zip(value.knots, value.multiplicities):
            fields.extend((_number(knot), str(multiplicity)))
        return " ".join(fields) + " ", 1.0
    if isinstance(value, NativePcurve):
        _unsupported(f"pcurve {value.id} of type NativePcurve is unsupported")
    _unsupported(f"pcurve type {type(value).__name__} is unsupported")


def _surface_record(
    value: object,
    surfaces: Mapping[str, object],
    active: frozenset[str] = frozenset(),
) -> str:
    if isinstance(value, PlaneSurface):
        axis, reference, y_direction = _frame(
            value.normal,
            value.reference_direction,
            f"plane surface {value.id}",
        )
        return f"1 {_values(_vector3(value.origin) + axis + reference + y_direction)} "
    if isinstance(value, CylinderSurface):
        axis, reference, y_direction = _frame(
            value.axis,
            value.reference_direction,
            f"cylinder surface {value.id}",
        )
        return f"2 {_values(_vector3(value.origin) + axis + reference + y_direction + (value.radius,))} "
    if isinstance(value, ConeSurface):
        axis, reference, y_direction = _frame(
            value.axis,
            value.reference_direction,
            f"cone surface {value.id}",
        )
        if not 0.0 < abs(value.half_angle) < math.pi / 2.0:
            _unsupported(f"cone surface {value.id} has an invalid half angle")
        return f"3 {_values(_vector3(value.origin) + axis + reference + y_direction + (value.radius, value.half_angle))} "
    if isinstance(value, SphereSurface):
        axis, reference, y_direction = _frame(
            value.axis,
            value.reference_direction,
            f"sphere surface {value.id}",
        )
        return f"4 {_values(_vector3(value.center) + axis + reference + y_direction + (value.radius,))} "
    if isinstance(value, TorusSurface):
        axis, reference, y_direction = _frame(
            value.axis,
            value.reference_direction,
            f"torus surface {value.id}",
        )
        if value.major_radius < 0.0:
            _unsupported(f"torus surface {value.id} has a negative major radius")
        return f"5 {_values(_vector3(value.center) + axis + reference + y_direction + (value.major_radius, value.minor_radius))} "
    if isinstance(value, NurbsSurface):
        u_count = len(value.control_points)
        v_count = len(value.control_points[0]) if value.control_points else 0
        if (
            not u_count
            or not v_count
            or any(len(row) != v_count for row in value.control_points)
        ):
            _unsupported(f"NURBS surface {value.id} has an invalid pole grid")
        _bspline_layout(
            value.degree_u,
            u_count,
            value.knots_u,
            value.multiplicities_u,
            value.periodic_u,
            f"NURBS surface {value.id} U direction",
        )
        _bspline_layout(
            value.degree_v,
            v_count,
            value.knots_v,
            value.multiplicities_v,
            value.periodic_v,
            f"NURBS surface {value.id} V direction",
        )
        rational = bool(value.weights)
        if rational and (
            len(value.weights) != u_count
            or any(len(row) != v_count for row in value.weights)
            or any(
                not math.isfinite(weight) or weight <= 0.0
                for row in value.weights
                for weight in row
            )
        ):
            _unsupported(f"NURBS surface {value.id} has invalid weights")
        fields = [
            "9",
            "1" if rational else "0",
            "1" if rational else "0",
            "1" if value.periodic_u else "0",
            "1" if value.periodic_v else "0",
            str(value.degree_u),
            str(value.degree_v),
            str(u_count),
            str(v_count),
            str(len(value.knots_u)),
            str(len(value.knots_v)),
        ]
        for u_index, row in enumerate(value.control_points):
            for v_index, point in enumerate(row):
                fields.extend(_number(component) for component in _vector3(point))
                if rational:
                    fields.append(_number(value.weights[u_index][v_index]))
        for knot, multiplicity in zip(value.knots_u, value.multiplicities_u):
            fields.extend((_number(knot), str(multiplicity)))
        for knot, multiplicity in zip(value.knots_v, value.multiplicities_v):
            fields.extend((_number(knot), str(multiplicity)))
        return " ".join(fields) + " "
    if isinstance(value, OffsetSurface):
        if value.id in active:
            _unsupported(f"offset surface {value.id} has a cyclic basis")
        base = surfaces.get(value.base_surface_id)
        if base is None:
            _unsupported(f"offset surface {value.id} has no basis surface")
        nested = _surface_record(base, surfaces, active | {value.id})
        return f"11 {_number(value.distance)} {nested}"
    if isinstance(value, NativeSurface):
        _unsupported(f"surface {value.id} of type NativeSurface is unsupported")
    _unsupported(f"surface type {type(value).__name__} is unsupported")


def _curve_point(value: object, parameter: float) -> Point | None:
    if isinstance(value, LineCurve):
        return tuple(
            origin + parameter * direction
            for origin, direction in zip(
                _vector3(value.origin), _vector3(value.direction)
            )
        )
    if isinstance(value, (CircleCurve, EllipseCurve)):
        axis, reference, y_direction = _frame(
            value.axis,
            value.reference_direction,
            f"curve {value.id}",
        )
        major = value.radius if isinstance(value, CircleCurve) else value.major_radius
        minor = value.radius if isinstance(value, CircleCurve) else value.minor_radius
        center = _vector3(value.center)
        return tuple(
            center[index]
            + major * math.cos(parameter) * reference[index]
            + minor * math.sin(parameter) * y_direction[index]
            for index in range(3)
        )
    return None


def _surface_periods(value: object) -> tuple[float | None, float | None]:
    if isinstance(value, (CylinderSurface, ConeSurface, SphereSurface)):
        return math.tau, None
    if isinstance(value, TorusSurface):
        return math.tau, math.tau
    return None, None


def _unwrap_periodic(
    values: Sequence[tuple[float, float]],
    periods: tuple[float | None, float | None],
) -> tuple[tuple[float, float], ...]:
    if not values:
        return ()
    result = [values[0]]
    for value in values[1:]:
        adjusted = list(value)
        previous = result[-1]
        for axis, period in enumerate(periods):
            if period is None:
                continue
            adjusted[axis] += round((previous[axis] - adjusted[axis]) / period) * period
        result.append((adjusted[0], adjusted[1]))
    return tuple(result)


def _unwrap_surface_uv(
    values: Sequence[tuple[float, float]],
    surface: object,
) -> tuple[tuple[float, float], ...]:
    if not isinstance(surface, SphereSurface) or not values:
        return _unwrap_periodic(values, _surface_periods(surface))
    resolved = list(values)
    for index, (u_value, v_value) in enumerate(resolved):
        if abs(abs(v_value) - math.pi / 2.0) > 1e-10:
            continue
        neighbor = next(
            (
                resolved[candidate][0]
                for distance in range(1, len(resolved))
                for candidate in (index - distance, index + distance)
                if 0 <= candidate < len(resolved)
                and abs(abs(resolved[candidate][1]) - math.pi / 2.0) > 1e-10
            ),
            u_value,
        )
        resolved[index] = neighbor, v_value
    result = [resolved[0]]
    for u_value, v_value in resolved[1:]:
        candidates = []
        for u_turn in range(-3, 4):
            candidate_u = u_value + u_turn * math.pi
            base_v = v_value if u_turn % 2 == 0 else math.pi - v_value
            for v_turn in range(-2, 3):
                candidates.append((candidate_u, base_v + v_turn * math.tau))
        previous = result[-1]
        result.append(
            min(
                candidates,
                key=lambda value: (value[0] - previous[0]) ** 2
                + (value[1] - previous[1]) ** 2,
            )
        )
    return tuple(result)


def _surface_uv(value: object, point: Point) -> tuple[float, float] | None:
    if isinstance(value, PlaneSurface):
        axis, reference, y_direction = _frame(
            value.normal,
            value.reference_direction,
            f"plane surface {value.id}",
        )
        delta = _subtract(point, _vector3(value.origin))
        return _dot(delta, reference), _dot(delta, y_direction)
    if isinstance(value, (CylinderSurface, ConeSurface)):
        axis, reference, y_direction = _frame(
            value.axis,
            value.reference_direction,
            f"surface {value.id}",
        )
        delta = _subtract(point, _vector3(value.origin))
        u = math.atan2(_dot(delta, y_direction), _dot(delta, reference))
        if isinstance(value, CylinderSurface):
            return u, _dot(delta, axis)
        cosine = math.cos(value.half_angle)
        if abs(cosine) <= 1e-15:
            return None
        return u, _dot(delta, axis) / cosine
    if isinstance(value, SphereSurface):
        axis, reference, y_direction = _frame(
            value.axis,
            value.reference_direction,
            f"sphere surface {value.id}",
        )
        delta = _subtract(point, _vector3(value.center))
        return (
            math.atan2(_dot(delta, y_direction), _dot(delta, reference)),
            math.atan2(
                _dot(delta, axis),
                math.hypot(_dot(delta, reference), _dot(delta, y_direction)),
            ),
        )
    if isinstance(value, TorusSurface):
        axis, reference, y_direction = _frame(
            value.axis,
            value.reference_direction,
            f"torus surface {value.id}",
        )
        delta = _subtract(point, _vector3(value.center))
        x_value = _dot(delta, reference)
        y_value = _dot(delta, y_direction)
        z_value = _dot(delta, axis)
        return (
            math.atan2(y_value, x_value),
            math.atan2(z_value, math.hypot(x_value, y_value) - value.major_radius),
        )
    return None


def _surface_residual(value: object, point: Point) -> float | None:
    if isinstance(value, PlaneSurface):
        axis, _, _ = _frame(
            value.normal,
            value.reference_direction,
            f"plane surface {value.id}",
        )
        return abs(_dot(_subtract(point, _vector3(value.origin)), axis))
    if isinstance(value, (CylinderSurface, ConeSurface)):
        axis, reference, y_direction = _frame(
            value.axis,
            value.reference_direction,
            f"surface {value.id}",
        )
        delta = _subtract(point, _vector3(value.origin))
        radial = math.hypot(_dot(delta, reference), _dot(delta, y_direction))
        axial = _dot(delta, axis)
        if isinstance(value, CylinderSurface):
            return abs(radial - value.radius)
        cosine = math.cos(value.half_angle)
        if abs(cosine) <= 1e-15:
            return None
        expected = value.radius + axial / cosine * math.sin(value.half_angle)
        return abs(radial - abs(expected))
    if isinstance(value, SphereSurface):
        return abs(_length(_subtract(point, _vector3(value.center))) - value.radius)
    if isinstance(value, TorusSurface):
        axis, reference, y_direction = _frame(
            value.axis,
            value.reference_direction,
            f"torus surface {value.id}",
        )
        delta = _subtract(point, _vector3(value.center))
        radial = math.hypot(_dot(delta, reference), _dot(delta, y_direction))
        axial = _dot(delta, axis)
        return abs(math.hypot(radial - value.major_radius, axial) - value.minor_radius)
    return None


def _plane_conic_pcurve(
    curve: object,
    surface: PlaneSurface,
    edge: BrepEdge,
    tolerance: float,
) -> _GeneratedPcurve | None:
    if not isinstance(curve, (CircleCurve, EllipseCurve)):
        return None
    normal, surface_x, surface_y = _frame(
        surface.normal,
        surface.reference_direction,
        f"plane surface {surface.id}",
    )
    curve_axis, curve_x, curve_y = _frame(
        curve.axis,
        curve.reference_direction,
        f"curve {curve.id}",
    )
    allowed = max(tolerance, edge.tolerance, 1e-7) * 10.0
    if abs(abs(_dot(normal, curve_axis)) - 1.0) > allowed:
        return None
    center = _surface_uv(surface, _vector3(curve.center))
    if center is None:
        return None
    x_direction = (_dot(curve_x, surface_x), _dot(curve_x, surface_y))
    y_direction = (_dot(curve_y, surface_x), _dot(curve_y, surface_y))
    if (
        abs(math.hypot(*x_direction) - 1.0) > allowed
        or abs(math.hypot(*y_direction) - 1.0) > allowed
        or abs(x_direction[0] * y_direction[0] + x_direction[1] * y_direction[1])
        > allowed
    ):
        return None
    first, last = sorted((edge.start_parameter, edge.end_parameter))
    kind = "2" if isinstance(curve, CircleCurve) else "3"
    radii = (
        (curve.radius,)
        if isinstance(curve, CircleCurve)
        else (curve.major_radius, curve.minor_radius)
    )
    start = (
        center[0]
        + radii[0] * math.cos(first) * x_direction[0]
        + radii[-1] * math.sin(first) * y_direction[0],
        center[1]
        + radii[0] * math.cos(first) * x_direction[1]
        + radii[-1] * math.sin(first) * y_direction[1],
    )
    end = (
        center[0]
        + radii[0] * math.cos(last) * x_direction[0]
        + radii[-1] * math.sin(last) * y_direction[0],
        center[1]
        + radii[0] * math.cos(last) * x_direction[1]
        + radii[-1] * math.sin(last) * y_direction[1],
    )
    return _GeneratedPcurve(
        f"{kind} {_values(center + x_direction + y_direction + radii)} ",
        first,
        last,
        start,
        end,
    )


def _linear_surface_pcurve(
    curve: object,
    surface: object,
    edge: BrepEdge,
    tolerance: float,
    offset: tuple[float, float],
) -> _GeneratedPcurve | None:
    low, high = sorted((edge.start_parameter, edge.end_parameter))
    if high == low:
        return None
    parameters = tuple(low + (high - low) * index / 8.0 for index in range(9))
    points = tuple(_curve_point(curve, parameter) for parameter in parameters)
    if any(point is None for point in points):
        return None
    concrete_points = tuple(point for point in points if point is not None)
    allowed = max(tolerance, edge.tolerance, 1e-7) * 10.0
    residuals = tuple(_surface_residual(surface, point) for point in concrete_points)
    if any(value is None or value > allowed for value in residuals):
        return None
    raw_uv = tuple(_surface_uv(surface, point) for point in concrete_points)
    if any(value is None for value in raw_uv):
        return None
    uv = _unwrap_surface_uv(
        tuple(value for value in raw_uv if value is not None),
        surface,
    )
    delta_parameter = high - low
    direction = (
        (uv[-1][0] - uv[0][0]) / delta_parameter,
        (uv[-1][1] - uv[0][1]) / delta_parameter,
    )
    magnitude = math.hypot(*direction)
    if magnitude <= 1e-15:
        return None
    origin = (
        uv[0][0] - low * direction[0],
        uv[0][1] - low * direction[1],
    )
    for parameter, value in zip(parameters, uv, strict=True):
        expected = (
            origin[0] + parameter * direction[0],
            origin[1] + parameter * direction[1],
        )
        if math.hypot(value[0] - expected[0], value[1] - expected[1]) > allowed:
            return None
    origin = origin[0] + offset[0], origin[1] + offset[1]
    unit = direction[0] / magnitude, direction[1] / magnitude
    first = low * magnitude
    last = high * magnitude
    return _GeneratedPcurve(
        f"1 {_values(origin + unit)} ",
        first,
        last,
        (origin[0] + unit[0] * first, origin[1] + unit[1] * first),
        (origin[0] + unit[0] * last, origin[1] + unit[1] * last),
    )


def _generated_pcurve(
    curve: object,
    surface: object,
    edge: BrepEdge,
    tolerance: float,
    offset: tuple[float, float],
) -> _GeneratedPcurve:
    result = (
        _plane_conic_pcurve(curve, surface, edge, tolerance)
        if isinstance(surface, PlaneSurface)
        else None
    )
    if result is None:
        result = _linear_surface_pcurve(
            curve,
            surface,
            edge,
            tolerance,
            offset,
        )
    if result is None:
        _unsupported(
            f"edge {edge.id} has no exact pcurve on surface {getattr(surface, 'id', '')}"
        )
    return result


def _seam_band(
    face: BrepFace,
    graph: _ModelGraph,
    tolerance: float,
) -> (
    tuple[
        BrepCoedge,
        BrepCoedge,
        _GeneratedPcurve,
        _GeneratedPcurve,
        bool,
        bool,
        Point,
        Point,
        float,
    ]
    | None
):
    surface = graph.surfaces[face.surface_id]
    if not isinstance(surface, (CylinderSurface, ConeSurface)):
        return None
    if len(face.loop_ids) != 2:
        return None
    loops = tuple(graph.loops[loop_id] for loop_id in face.loop_ids)
    if any(len(loop.coedge_ids) != 1 for loop in loops):
        return None
    coedges = tuple(graph.coedges[loop.coedge_ids[0]] for loop in loops)
    if any(coedge.pcurve_id for coedge in coedges):
        return None
    edges = tuple(graph.edges[coedge.edge_id] for coedge in coedges)
    curves = tuple(graph.curves[edge.curve_id] for edge in edges)
    if any(not isinstance(curve, CircleCurve) for curve in curves):
        return None
    allowed = (
        max(
            tolerance,
            *(edge.tolerance for edge in edges),
            *(graph.vertices[edge.start_vertex_id].tolerance for edge in edges),
            1e-7,
        )
        * 10.0
    )
    if any(
        edge.start_vertex_id != edge.end_vertex_id
        or abs(abs(edge.end_parameter - edge.start_parameter) - math.tau) > allowed
        for edge in edges
    ):
        return None
    generated = tuple(
        _generated_pcurve(curve, surface, edge, tolerance, (0.0, 0.0))
        for curve, edge in zip(curves, edges, strict=True)
    )
    if any(
        abs(abs(value.end[0] - value.start[0]) - math.tau) > allowed
        or abs(value.end[1] - value.start[1]) > allowed
        for value in generated
    ):
        return None
    means = tuple((value.start[1] + value.end[1]) / 2.0 for value in generated)
    if abs(means[0] - means[1]) <= allowed:
        return None
    low_index = 0 if means[0] < means[1] else 1
    high_index = 1 - low_index
    low_coedge = coedges[low_index]
    high_coedge = coedges[high_index]
    low_edge = edges[low_index]
    high_edge = edges[high_index]
    low_generated = generated[low_index]
    high_generated = generated[high_index]
    low_reversed = low_generated.end[0] < low_generated.start[0]
    high_reversed = high_generated.end[0] > high_generated.start[0]
    low_start = low_generated.end if low_reversed else low_generated.start
    low_end = low_generated.start if low_reversed else low_generated.end
    high_start = high_generated.end if high_reversed else high_generated.start
    offset = round((low_end[0] - high_start[0]) / math.tau) * math.tau
    high_generated = _generated_pcurve(
        curves[high_index],
        surface,
        high_edge,
        tolerance,
        (offset, 0.0),
    )
    high_start = high_generated.end if high_reversed else high_generated.start
    high_end = high_generated.start if high_reversed else high_generated.end
    if (
        abs(low_end[0] - high_start[0]) > allowed
        or abs(high_end[0] - low_start[0]) > allowed
    ):
        return None
    low_point = _vector3(graph.vertices[low_edge.start_vertex_id].point)
    high_point = _vector3(graph.vertices[high_edge.start_vertex_id].point)
    vector = _subtract(high_point, low_point)
    length = _length(vector)
    if (
        length <= allowed
        or abs(length - (means[high_index] - means[low_index])) > allowed
    ):
        return None
    if any(
        (
            _surface_residual(
                surface,
                tuple(low_point[axis] + vector[axis] * ratio for axis in range(3)),
            )
            or 0.0
        )
        > allowed
        for ratio in (0.25, 0.5, 0.75)
    ):
        return None
    return (
        low_coedge,
        high_coedge,
        low_generated,
        high_generated,
        low_reversed,
        high_reversed,
        low_point,
        high_point,
        length,
    )


def _edge_pcurve_records(
    model: BrepModel,
    graph: _ModelGraph,
    tolerance: float,
) -> tuple[
    tuple[str, ...],
    Mapping[str, _EdgePcurve],
    Mapping[str, _SeamBand],
]:
    records = [value[0] for value in (_pcurve_record(item) for item in model.pcurves)]
    explicit_indexes = {item.id: index for index, item in enumerate(model.pcurves, 1)}
    explicit_scales = {item.id: _pcurve_record(item)[1] for item in model.pcurves}
    result: dict[str, _EdgePcurve] = {}
    seam_bands: dict[str, _SeamBand] = {}
    for face in model.faces:
        surface = graph.surfaces[face.surface_id]
        periods = _surface_periods(surface)
        seam = _seam_band(face, graph, tolerance)
        if seam is not None:
            (
                low_coedge,
                high_coedge,
                low_generated,
                high_generated,
                low_reversed,
                high_reversed,
                low_point,
                high_point,
                length,
            ) = seam
            for coedge, generated in (
                (low_coedge, low_generated),
                (high_coedge, high_generated),
            ):
                records.append(generated.record)
                result[coedge.id] = _EdgePcurve(
                    len(records), generated.first, generated.last
                )
            low_start = low_generated.end if low_reversed else low_generated.start
            low_end = low_generated.start if low_reversed else low_generated.end
            records.append(f"1 {_values((low_end[0], low_start[1], 0.0, 1.0))} ")
            first_pcurve_index = len(records)
            records.append(f"1 {_values((low_start[0], low_start[1], 0.0, 1.0))} ")
            second_pcurve_index = len(records)
            direction = _scale(_subtract(high_point, low_point), 1.0 / length)
            seam_bands[face.id] = _SeamBand(
                face.id,
                (face.loop_ids[0], face.loop_ids[1]),
                low_coedge.id,
                high_coedge.id,
                low_reversed,
                high_reversed,
                graph.edges[low_coedge.edge_id].start_vertex_id,
                graph.edges[high_coedge.edge_id].start_vertex_id,
                f"1 {_values(low_point + direction)} ",
                length,
                first_pcurve_index,
                second_pcurve_index,
            )
            continue
        for loop_id in face.loop_ids:
            previous_end: tuple[float, float] | None = None
            for coedge_id in graph.loops[loop_id].coedge_ids:
                coedge = graph.coedges[coedge_id]
                edge = graph.edges[coedge.edge_id]
                if coedge.pcurve_id:
                    scale = explicit_scales[coedge.pcurve_id]
                    first, last = sorted(
                        (edge.start_parameter * scale, edge.end_parameter * scale)
                    )
                    result[coedge.id] = _EdgePcurve(
                        explicit_indexes[coedge.pcurve_id],
                        first,
                        last,
                    )
                    previous_end = None
                    continue
                generated = _generated_pcurve(
                    graph.curves[edge.curve_id],
                    surface,
                    edge,
                    tolerance,
                    (0.0, 0.0),
                )
                reversed_value = coedge.reversed != (
                    edge.end_parameter < edge.start_parameter
                )
                start = generated.end if reversed_value else generated.start
                end = generated.start if reversed_value else generated.end
                offset = [0.0, 0.0]
                if previous_end is not None:
                    for axis, period in enumerate(periods):
                        if period is not None:
                            offset[axis] = (
                                round((previous_end[axis] - start[axis]) / period)
                                * period
                            )
                if offset != [0.0, 0.0]:
                    generated = _generated_pcurve(
                        graph.curves[edge.curve_id],
                        surface,
                        edge,
                        tolerance,
                        (offset[0], offset[1]),
                    )
                    start = generated.end if reversed_value else generated.start
                    end = generated.start if reversed_value else generated.end
                records.append(generated.record)
                result[coedge.id] = _EdgePcurve(
                    len(records), generated.first, generated.last
                )
                previous_end = end
    return tuple(records), result, seam_bands


def _loop_uv_points(
    graph: _ModelGraph,
    face: BrepFace,
    loop: BrepLoop,
) -> tuple[tuple[float, float], ...] | None:
    surface = graph.surfaces[face.surface_id]
    values: list[tuple[float, float]] = []
    for coedge_id in loop.coedge_ids:
        coedge = graph.coedges[coedge_id]
        edge = graph.edges[coedge.edge_id]
        geometry = graph.curves.get(edge.curve_id)
        if geometry is None:
            return None
        first, last = edge.start_parameter, edge.end_parameter
        if coedge.reversed:
            first, last = last, first
        for index in range(16):
            point = _curve_point(
                geometry,
                first + (last - first) * index / 16.0,
            )
            if point is None:
                return None
            uv = _surface_uv(surface, point)
            if uv is None:
                return None
            values.append(uv)
    return _unwrap_surface_uv(values, surface)


def _face_loop_reversals(
    graph: _ModelGraph,
    face: BrepFace,
    tolerance: float,
) -> dict[str, bool]:
    area_tolerance = max(tolerance * tolerance, 1e-10)
    loop_points = {
        loop_id: _loop_uv_points(graph, face, graph.loops[loop_id])
        for loop_id in face.loop_ids
    }
    loop_areas = {
        loop_id: (
            None
            if points is None or len(points) < 3
            else sum(
                left[0] * right[1] - right[0] * left[1]
                for left, right in zip(points, (*points[1:], points[0]))
            )
            / 2.0
        )
        for loop_id, points in loop_points.items()
    }
    measurable = {
        loop_id: area
        for loop_id, area in loop_areas.items()
        if area is not None and abs(area) > area_tolerance
    }
    if len(measurable) != len(face.loop_ids):
        _unsupported(f"face {face.id} has an unprovable loop orientation")
    outer_loop_id = max(measurable, key=lambda loop_id: abs(measurable[loop_id]))
    return {
        loop_id: (area > 0.0) != (loop_id == outer_loop_id)
        for loop_id, area in measurable.items()
    }


def _coedge_shape_reversed(coedge: BrepCoedge, edge: BrepEdge) -> bool:
    return coedge.reversed != (edge.end_parameter < edge.start_parameter)


def _planar_line_loop_is_proven(
    graph: _ModelGraph,
    face: BrepFace,
    loop: BrepLoop,
    tolerance: float,
) -> bool:
    if len(loop.coedge_ids) < 3:
        return False
    surface = graph.surfaces[face.surface_id]
    if not isinstance(surface, PlaneSurface):
        return False
    points: list[tuple[float, float]] = []
    allowed = max(tolerance, face.tolerance, 1e-7) * 10.0
    for coedge_id in loop.coedge_ids:
        coedge = graph.coedges[coedge_id]
        edge = graph.edges[coedge.edge_id]
        curve = graph.curves[edge.curve_id]
        if not isinstance(curve, LineCurve):
            return False
        first = edge.end_parameter if coedge.reversed else edge.start_parameter
        last = edge.start_parameter if coedge.reversed else edge.end_parameter
        start = _curve_point(curve, first)
        end = _curve_point(curve, last)
        middle = _curve_point(curve, (first + last) / 2.0)
        if start is None or end is None or middle is None:
            return False
        if any(
            residual is None or residual > allowed
            for residual in (
                _surface_residual(surface, start),
                _surface_residual(surface, middle),
                _surface_residual(surface, end),
            )
        ):
            return False
        uv = _surface_uv(surface, start)
        if uv is None:
            return False
        points.append(uv)
    if len(points) < 3:
        return False
    span = max(
        max(value[axis] for value in points) - min(value[axis] for value in points)
        for axis in (0, 1)
    )
    epsilon = allowed * max(1.0, span)
    turns = []
    for index, middle in enumerate(points):
        left = points[index - 1]
        right = points[(index + 1) % len(points)]
        turn = (middle[0] - left[0]) * (right[1] - middle[1]) - (
            middle[1] - left[1]
        ) * (right[0] - middle[0])
        if abs(turn) <= epsilon:
            return False
        turns.append(turn > 0.0)
    if any(value != turns[0] for value in turns[1:]):
        return False
    for first_index, first_start in enumerate(points):
        first_end = points[(first_index + 1) % len(points)]
        for second_index in range(first_index + 1, len(points)):
            if second_index in {
                first_index,
                (first_index + 1) % len(points),
                (first_index - 1) % len(points),
            }:
                continue
            second_start = points[second_index]
            second_end = points[(second_index + 1) % len(points)]
            crosses = []
            for left, right, point in (
                (first_start, first_end, second_start),
                (first_start, first_end, second_end),
                (second_start, second_end, first_start),
                (second_start, second_end, first_end),
            ):
                value = (right[0] - left[0]) * (point[1] - left[1]) - (
                    right[1] - left[1]
                ) * (point[0] - left[0])
                if abs(value) <= epsilon:
                    return False
                crosses.append(value > 0.0)
            if crosses[0] != crosses[1] and crosses[2] != crosses[3]:
                return False
    return True


def _planar_circle_loop(
    graph: _ModelGraph,
    face: BrepFace,
    loop: BrepLoop,
    tolerance: float,
) -> tuple[tuple[float, float], float] | None:
    if len(loop.coedge_ids) != 1:
        return None
    surface = graph.surfaces[face.surface_id]
    if not isinstance(surface, PlaneSurface):
        return None
    coedge = graph.coedges[loop.coedge_ids[0]]
    edge = graph.edges[coedge.edge_id]
    curve = graph.curves[edge.curve_id]
    if not isinstance(curve, CircleCurve):
        return None
    allowed = max(tolerance, face.tolerance, edge.tolerance, 1e-7) * 10.0
    if (
        edge.start_vertex_id != edge.end_vertex_id
        or abs(abs(edge.end_parameter - edge.start_parameter) - math.tau) > allowed
    ):
        return None
    surface_axis, _, _ = _frame(
        surface.normal,
        surface.reference_direction,
        f"plane surface {surface.id}",
    )
    curve_axis, _, _ = _frame(
        curve.axis,
        curve.reference_direction,
        f"circle curve {curve.id}",
    )
    if abs(abs(_dot(surface_axis, curve_axis)) - 1.0) > allowed:
        return None
    center = _surface_uv(surface, _vector3(curve.center))
    residual = _surface_residual(surface, _vector3(curve.center))
    if center is None or residual is None or residual > allowed:
        return None
    return center, curve.radius


def _face_is_proven(
    graph: _ModelGraph,
    face: BrepFace,
    tolerance: float,
    seam_bands: Mapping[str, _SeamBand],
) -> None:
    if face.id in seam_bands:
        return
    surface = graph.surfaces[face.surface_id]
    if not isinstance(surface, PlaneSurface):
        _unsupported(
            f"face {face.id} on {type(surface).__name__} lacks a proven native topology"
        )
    loops = tuple(graph.loops[loop_id] for loop_id in face.loop_ids)
    if len(loops) == 1 and _planar_line_loop_is_proven(
        graph, face, loops[0], tolerance
    ):
        return
    circles = tuple(_planar_circle_loop(graph, face, loop, tolerance) for loop in loops)
    if len(circles) not in {1, 2} or any(value is None for value in circles):
        _unsupported(f"planar face {face.id} lacks a proven wire arrangement")
    concrete = tuple(value for value in circles if value is not None)
    allowed = max(tolerance, face.tolerance, 1e-7) * 10.0
    if len(concrete) == 2:
        if (
            math.dist(concrete[0][0], concrete[1][0]) > allowed
            or abs(concrete[0][1] - concrete[1][1]) <= allowed
        ):
            _unsupported(f"planar face {face.id} has unproven circle containment")


def _face_edge_orientations(
    graph: _ModelGraph,
    face: BrepFace,
    loop_reversals: Mapping[str, bool],
    seam_bands: Mapping[str, _SeamBand],
) -> tuple[tuple[str, bool], ...]:
    band = seam_bands.get(face.id)
    if band is not None:
        return (
            (graph.coedges[band.low_coedge_id].edge_id, band.low_reversed),
            (graph.coedges[band.high_coedge_id].edge_id, band.high_reversed),
        )
    return tuple(
        (
            graph.coedges[coedge_id].edge_id,
            _coedge_shape_reversed(
                graph.coedges[coedge_id],
                graph.edges[graph.coedges[coedge_id].edge_id],
            )
            != loop_reversals[loop_id],
        )
        for loop_id in face.loop_ids
        for coedge_id in graph.loops[loop_id].coedge_ids
    )


def _shell_face_orientations(
    model: BrepModel,
    graph: _ModelGraph,
    face_edges: Mapping[str, tuple[tuple[str, bool], ...]],
) -> dict[str, bool]:
    result: dict[str, bool] = {}
    for shell in model.shells:
        face_uses = tuple(graph.face_uses[value] for value in shell.face_use_ids)
        face_ids = tuple(value.face_id for value in face_uses)
        if len(face_ids) != len(set(face_ids)):
            _unsupported(f"shell {shell.id} reuses a face")
        by_edge: dict[str, list[tuple[str, bool]]] = {}
        for face_use in face_uses:
            for edge_id, reversed_value in face_edges[face_use.face_id]:
                by_edge.setdefault(edge_id, []).append((face_use.id, reversed_value))
        if any(len(values) > 2 for values in by_edge.values()):
            _unsupported(f"shell {shell.id} is non-manifold")
        if shell.closed and any(len(values) != 2 for values in by_edge.values()):
            _unsupported(f"closed shell {shell.id} has a free edge")
        adjacency: dict[str, list[tuple[str, bool]]] = {
            value.id: [] for value in face_uses
        }
        for values in by_edge.values():
            if len(values) != 2:
                continue
            (left_id, left_value), (right_id, right_value) = values
            parity = left_value != right_value
            required = not parity
            if left_id == right_id:
                if required:
                    _unsupported(f"shell {shell.id} is not orientable")
                continue
            adjacency[left_id].append((right_id, required))
            adjacency[right_id].append((left_id, required))
        assigned: dict[str, bool] = {}
        for start in adjacency:
            if start in assigned:
                continue
            assigned[start] = False
            component = [start]
            pending = deque((start,))
            while pending:
                current = pending.popleft()
                for neighbor, parity in adjacency[current]:
                    expected = assigned[current] != parity
                    if neighbor in assigned:
                        if assigned[neighbor] != expected:
                            _unsupported(f"shell {shell.id} is not orientable")
                        continue
                    assigned[neighbor] = expected
                    component.append(neighbor)
                    pending.append(neighbor)
            preferred = {
                value.id: not (graph.faces[value.face_id].same_sense != value.reversed)
                for value in face_uses
                if value.id in component
            }
            direct_score = sum(
                assigned[value] != preferred[value] for value in component
            )
            reverse_score = sum(
                (not assigned[value]) != preferred[value] for value in component
            )
            if reverse_score < direct_score:
                for value in component:
                    assigned[value] = not assigned[value]
        result.update(assigned)
    return result


def _shell_use_orientations(
    model: BrepModel,
    graph: _ModelGraph,
) -> dict[str, bool]:
    result: dict[str, bool] = {}
    for region in model.regions:
        if region.solid:
            if len(region.shell_use_ids) != 1:
                _unsupported(
                    f"solid region {region.id} has unproven nested shell containment"
                )
            shell_use = graph.shell_uses[region.shell_use_ids[0]]
            if not graph.shells[shell_use.shell_id].closed:
                _unsupported(f"solid region {region.id} contains an open shell")
            result[shell_use.id] = False
            continue
        for shell_use_id in region.shell_use_ids:
            result[shell_use_id] = graph.shell_uses[shell_use_id].reversed
    return result


def _check_edge_geometry(
    edge: BrepEdge,
    curve: object,
    vertices: Mapping[str, BrepVertex],
    tolerance: float,
) -> None:
    start = _curve_point(curve, edge.start_parameter)
    end = _curve_point(curve, edge.end_parameter)
    if start is None or end is None:
        return
    for actual, vertex_id in (
        (start, edge.start_vertex_id),
        (end, edge.end_vertex_id),
    ):
        vertex = vertices[vertex_id]
        allowed = max(tolerance, edge.tolerance, vertex.tolerance)
        if _length(_subtract(actual, _vector3(vertex.point))) > allowed:
            _unsupported(
                f"edge {edge.id} curve endpoint does not match vertex {vertex_id}"
            )


def _edge_geometry(
    edge: BrepEdge,
    graph: _ModelGraph,
    curve_indexes: Mapping[str, int],
    curve_scales: Mapping[str, float],
    edge_pcurves: Mapping[str, _EdgePcurve],
    surface_indexes: Mapping[str, int],
    tolerance: float,
) -> tuple[str, ...]:
    if edge.degenerate:
        _unsupported(f"degenerate edge {edge.id} is unsupported")
    if edge.end_parameter == edge.start_parameter:
        _unsupported(f"edge {edge.id} requires a nonzero parameter range")
    curve_scale = curve_scales[edge.curve_id]
    first, last = sorted(
        (edge.start_parameter * curve_scale, edge.end_parameter * curve_scale)
    )
    grouped: dict[str, list[BrepCoedge]] = {}
    for coedge_id in graph.edge_uses[edge.id]:
        coedge = graph.coedges[coedge_id]
        face = graph.face_for_coedge(coedge_id)
        if face is None:
            if coedge.pcurve_id:
                _unsupported(f"wire coedge {coedge.id} cannot carry a surface pcurve")
            continue
        surface = graph.surfaces[face.surface_id]
        grouped.setdefault(face.surface_id, []).append(coedge)
    representations: list[str] = []
    for surface_id, uses in grouped.items():
        surface_index = surface_indexes[surface_id]
        if len(uses) == 1:
            pcurve = edge_pcurves[uses[0].id]
            representations.append(
                f"2  {pcurve.index} {surface_index} 0 {_number(pcurve.first)} {_number(pcurve.last)}"
            )
            continue
        if len(uses) == 2:
            first_pcurve = edge_pcurves[uses[0].id]
            second_pcurve = edge_pcurves[uses[1].id]
            if (
                abs(first_pcurve.first - second_pcurve.first) > 1e-9
                or abs(first_pcurve.last - second_pcurve.last) > 1e-9
            ):
                _unsupported(
                    f"edge {edge.id} has inconsistent closed-surface pcurve ranges"
                )
            representations.append(
                f"3  {first_pcurve.index} {second_pcurve.index} C0 {surface_index} 0 {_number(first_pcurve.first)} {_number(first_pcurve.last)}"
            )
            continue
        _unsupported(
            f"edge {edge.id} has an unsupported closed-surface pcurve arrangement"
        )
    same_range = all(
        abs(value - expected) <= 1e-9
        for coedge_id in graph.edge_uses[edge.id]
        if coedge_id in edge_pcurves
        for value, expected in (
            (edge_pcurves[coedge_id].first, first),
            (edge_pcurves[coedge_id].last, last),
        )
    )
    lines = [
        f" {_number(max(tolerance, edge.tolerance))} {int(same_range)} {int(same_range)} 0",
        f"1  {curve_indexes[edge.curve_id]} 0 {_number(first)} {_number(last)}",
        *representations,
    ]
    lines.append("0")
    return tuple(lines)


def _shape_lines(records: Sequence[_ShapeRecord], root: tuple[str, bool]) -> list[str]:
    ordinals = {record.key: index for index, record in enumerate(records, 1)}
    count = len(records)

    def reference(key: str) -> int:
        try:
            return count - ordinals[key] + 1
        except KeyError:
            _unsupported(f"native topology references unknown shape {key}")

    lines = [f"TShapes {count}"]
    for record in records:
        lines.append(record.kind)
        lines.extend(record.geometry)
        lines.append("")
        lines.append(record.flags)
        lines.append(
            " ".join(
                f"{'-' if reversed_value else '+'}{reference(key)} 0"
                for key, reversed_value in record.children
            )
            + (" " if record.children else "")
            + "*"
        )
    lines.extend(
        [
            "",
            f"{'-' if root[1] else '+'}{reference(root[0])} 0 ",
        ]
    )
    return lines


def brep_model_brep(model: BrepModel, tolerance: float = 1e-7) -> bytes:
    if not isinstance(model, BrepModel):
        raise TypeError("model must be a BrepModel")
    if not math.isfinite(tolerance) or tolerance <= 0.0:
        raise ValueError("tolerance must be finite and positive")
    errors = model.validate(
        frozenset(body.design_body_id for body in model.bodies if body.design_body_id)
    )
    if errors:
        _unsupported(errors[0])
    if any(body.transform != Transform() for body in model.bodies):
        _unsupported("native FreeCAD B-rep writing requires identity body transforms")
    graph = _ModelGraph(model)
    base_curve_records = tuple(_curve_record(value) for value in model.curves)
    surface_records = tuple(
        _surface_record(value, graph.surfaces) for value in model.surfaces
    )
    pcurve_records, edge_pcurves, seam_bands = _edge_pcurve_records(
        model, graph, tolerance
    )
    loop_reversals: dict[str, bool] = {}
    for face in model.faces:
        _face_is_proven(graph, face, tolerance, seam_bands)
        if face.id not in seam_bands:
            loop_reversals.update(_face_loop_reversals(graph, face, tolerance))
    face_edges = {
        face.id: _face_edge_orientations(
            graph,
            face,
            loop_reversals,
            seam_bands,
        )
        for face in model.faces
    }
    face_use_reversals = _shell_face_orientations(model, graph, face_edges)
    shell_use_reversals = _shell_use_orientations(model, graph)
    curve_records = base_curve_records + tuple(
        (band.curve_record, 1.0) for band in seam_bands.values()
    )
    curve_indexes = {value.id: index for index, value in enumerate(model.curves, 1)}
    curve_scales = {
        value.id: curve_records[index][1] for index, value in enumerate(model.curves)
    }
    surface_indexes = {value.id: index for index, value in enumerate(model.surfaces, 1)}
    lines = [
        "DBRep_DrawableShape",
        "",
        "CASCADE Topology V1, (c) Matra-Datavision",
        "Locations 0",
        f"Curve2ds {len(pcurve_records)}",
        *pcurve_records,
        f"Curves {len(curve_records)}",
        *(value[0] for value in curve_records),
        "Polygon3D 0",
        "PolygonOnTriangulations 0",
        f"Surfaces {len(surface_records)}",
        *surface_records,
        "Triangulations 0",
        "",
    ]
    shapes: list[_ShapeRecord] = []
    for vertex in model.vertices:
        shapes.append(
            _ShapeRecord(
                f"vertex:{vertex.id}",
                "Ve",
                (
                    _number(max(tolerance, vertex.tolerance)),
                    _values(_vector3(vertex.point)),
                    "0 0",
                ),
                "0101101",
                (),
            )
        )
    for edge in model.edges:
        _check_edge_geometry(
            edge,
            next(value for value in model.curves if value.id == edge.curve_id),
            graph.vertices,
            tolerance,
        )
        range_reversed = edge.end_parameter < edge.start_parameter
        first_vertex_id = edge.end_vertex_id if range_reversed else edge.start_vertex_id
        last_vertex_id = edge.start_vertex_id if range_reversed else edge.end_vertex_id
        shapes.append(
            _ShapeRecord(
                f"edge:{edge.id}",
                "Ed",
                _edge_geometry(
                    edge,
                    graph,
                    curve_indexes,
                    curve_scales,
                    edge_pcurves,
                    surface_indexes,
                    tolerance,
                ),
                "0101000",
                (
                    (f"vertex:{first_vertex_id}", False),
                    (f"vertex:{last_vertex_id}", True),
                ),
            )
        )
    for offset, band in enumerate(seam_bands.values(), len(base_curve_records) + 1):
        shapes.append(
            _ShapeRecord(
                f"edge:seam:{band.face_id}",
                "Ed",
                (
                    f" {_number(tolerance)} 1 1 0",
                    f"1  {offset} 0 0 {_number(band.length)}",
                    f"3  {band.first_pcurve_index} {band.second_pcurve_index} CN {surface_indexes[graph.faces[band.face_id].surface_id]} 0 0 {_number(band.length)}",
                    "0",
                ),
                "0101000",
                (
                    (f"vertex:{band.low_vertex_id}", False),
                    (f"vertex:{band.high_vertex_id}", True),
                ),
            )
        )
    for loop in model.loops:
        if any(loop.id in band.loop_ids for band in seam_bands.values()):
            continue
        shapes.append(
            _ShapeRecord(
                f"loop:{loop.id}",
                "Wi",
                (),
                "0101100",
                tuple(
                    (
                        f"edge:{graph.coedges[coedge_id].edge_id}",
                        graph.coedges[coedge_id].reversed
                        != (
                            graph.edges[graph.coedges[coedge_id].edge_id].end_parameter
                            < graph.edges[
                                graph.coedges[coedge_id].edge_id
                            ].start_parameter
                        ),
                    )
                    for coedge_id in loop.coedge_ids
                ),
            )
        )
    for band in seam_bands.values():
        low_edge = graph.edges[graph.coedges[band.low_coedge_id].edge_id]
        high_edge = graph.edges[graph.coedges[band.high_coedge_id].edge_id]
        shapes.append(
            _ShapeRecord(
                f"loop:seam:{band.face_id}",
                "Wi",
                (),
                "0101100",
                (
                    (f"edge:{low_edge.id}", band.low_reversed),
                    (f"edge:seam:{band.face_id}", False),
                    (f"edge:{high_edge.id}", band.high_reversed),
                    (f"edge:seam:{band.face_id}", True),
                ),
            )
        )
    for wire in model.wires:
        shapes.append(
            _ShapeRecord(
                f"wire:{wire.id}",
                "Wi",
                (),
                "0101100" if wire.closed else "0101000",
                tuple(
                    (
                        f"edge:{graph.coedges[coedge_id].edge_id}",
                        graph.coedges[coedge_id].reversed
                        != (
                            graph.edges[graph.coedges[coedge_id].edge_id].end_parameter
                            < graph.edges[
                                graph.coedges[coedge_id].edge_id
                            ].start_parameter
                        ),
                    )
                    for coedge_id in wire.coedge_ids
                ),
            )
        )
    for face in model.faces:
        seam_band = seam_bands.get(face.id)
        if seam_band is not None:
            shapes.append(
                _ShapeRecord(
                    f"face:{face.id}",
                    "Fa",
                    (
                        f"0  {_number(max(tolerance, face.tolerance))} {surface_indexes[face.surface_id]} 0",
                    ),
                    "0101000",
                    ((f"loop:seam:{face.id}", False),),
                )
            )
            continue
        shapes.append(
            _ShapeRecord(
                f"face:{face.id}",
                "Fa",
                (
                    f"0  {_number(max(tolerance, face.tolerance))} {surface_indexes[face.surface_id]} 0",
                ),
                "0101000",
                tuple(
                    (f"loop:{loop_id}", loop_reversals[loop_id])
                    for loop_id in face.loop_ids
                ),
            )
        )
    for shell in model.shells:
        children: list[tuple[str, bool]] = []
        for face_use_id in shell.face_use_ids:
            face_use = graph.face_uses[face_use_id]
            face = graph.faces[face_use.face_id]
            children.append(
                (
                    f"face:{face.id}",
                    face_use_reversals[face_use.id],
                )
            )
        shapes.append(
            _ShapeRecord(
                f"shell:{shell.id}",
                "Sh",
                (),
                "0101100" if shell.closed else "0101000",
                tuple(children),
            )
        )
    region_roots: dict[str, tuple[str, bool]] = {}
    for region in model.regions:
        shell_children = tuple(
            (
                f"shell:{graph.shell_uses[shell_use_id].shell_id}",
                shell_use_reversals[shell_use_id],
            )
            for shell_use_id in region.shell_use_ids
        )
        if region.solid:
            if any(
                not graph.shells[graph.shell_uses[value].shell_id].closed
                for value in region.shell_use_ids
            ):
                _unsupported(f"solid region {region.id} contains an open shell")
            key = f"region:{region.id}"
            shapes.append(_ShapeRecord(key, "So", (), "0100000", shell_children))
            region_roots[region.id] = (key, False)
        elif len(shell_children) == 1:
            region_roots[region.id] = shell_children[0]
        else:
            key = f"region:{region.id}"
            shapes.append(_ShapeRecord(key, "Co", (), "0100000", shell_children))
            region_roots[region.id] = (key, False)
    body_roots: list[tuple[str, bool]] = []
    for body in model.bodies:
        children = [region_roots[value] for value in body.region_ids]
        children.extend((f"wire:{value}", False) for value in body.wire_ids)
        children.extend((f"vertex:{value}", False) for value in body.vertex_ids)
        if len(children) == 1:
            body_roots.append(children[0])
        else:
            key = f"body:{body.id}"
            shapes.append(_ShapeRecord(key, "Co", (), "0100000", tuple(children)))
            body_roots.append((key, False))
    if len(body_roots) == 1:
        root = body_roots[0]
    else:
        root_key = "model:root"
        shapes.append(_ShapeRecord(root_key, "Co", (), "1100000", tuple(body_roots)))
        root = (root_key, False)
    lines.extend(_shape_lines(shapes, root))
    return ("\n".join(lines) + "\n").encode("ascii")


def proven_ascii_brep(data: bytes) -> bytes | None:
    if not isinstance(data, bytes):
        raise TypeError("data must be bytes")
    from convert.opencascade import decode_ascii_brep

    model = decode_ascii_brep(data, id_prefix="freecad:proof")
    if model is None:
        return None
    try:
        return brep_model_brep(model)
    except FreeCADBrepWriteError:
        return None


def triangle_mesh_brep(
    vertices: Sequence[Any],
    triangles: Sequence[Any],
    tolerance: float = 1e-7,
) -> bytes:
    if not math.isfinite(tolerance) or tolerance <= 0.0:
        raise ValueError("tolerance must be finite and positive")
    points = tuple(_point(vertex) for vertex in vertices)
    facets = tuple(_triangle(triangle, len(points)) for triangle in triangles)
    if not facets:
        raise ValueError("at least one triangle is required")
    oriented = _oriented_components(points, facets, tolerance)
    if oriented is None:
        return _independent_brep(points, facets, tolerance)
    oriented_facets, components, closed = oriented
    return _shared_brep(points, oriented_facets, components, closed, tolerance)
