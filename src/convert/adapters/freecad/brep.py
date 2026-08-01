from __future__ import annotations

from collections import deque
from collections.abc import Sequence
import math
from typing import Any


Point = tuple[float, float, float]
Triangle = tuple[int, int, int]
Geometry = tuple[
    tuple[Point, Point, Point],
    tuple[float, float, float],
    Point,
    Point,
    Point,
]


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
