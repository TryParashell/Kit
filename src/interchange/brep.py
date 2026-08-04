# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from dataclasses import dataclass, field, fields, is_dataclass
from math import isfinite, pi
from typing import Any, Mapping

from .types import Provenance, Transform, Vector2, Vector3, frozen_mapping


@dataclass(frozen=True, slots=True)
class BrepEntity:
    id: str
    provenance: Provenance | None = field(default=None, kw_only=True)
    attributes: Mapping[str, Any] = field(default_factory=frozen_mapping, kw_only=True)


@dataclass(frozen=True, slots=True)
class BrepCurve(BrepEntity):
    def __post_init__(self) -> None:
        if not isinstance(self.id, str):
            raise TypeError("B-rep curve id must be a string")


@dataclass(frozen=True, slots=True)
class LineCurve(BrepCurve):
    origin: Vector3
    direction: Vector3


@dataclass(frozen=True, slots=True)
class CircleCurve(BrepCurve):
    center: Vector3
    axis: Vector3
    reference_direction: Vector3
    radius: float


@dataclass(frozen=True, slots=True)
class EllipseCurve(BrepCurve):
    center: Vector3
    axis: Vector3
    reference_direction: Vector3
    major_radius: float
    minor_radius: float


@dataclass(frozen=True, slots=True)
class NurbsCurve(BrepCurve):
    degree: int
    control_points: tuple[Vector3, ...]
    knots: tuple[float, ...]
    multiplicities: tuple[int, ...]
    weights: tuple[float, ...] = ()
    periodic: bool = False


@dataclass(frozen=True, slots=True)
class IntersectionCurve(BrepCurve):
    first_surface_id: str
    second_surface_id: str
    samples: tuple[Vector3, ...] = ()
    tolerance: float = 0.0


@dataclass(frozen=True, slots=True)
class NativeCurve(BrepCurve):
    format_id: str
    entity_type: str
    data: Mapping[str, Any] = field(default_factory=frozen_mapping)


@dataclass(frozen=True, slots=True)
class BrepPcurve(BrepEntity):
    def __post_init__(self) -> None:
        if not isinstance(self.id, str):
            raise TypeError("B-rep pcurve id must be a string")


@dataclass(frozen=True, slots=True)
class LinePcurve(BrepPcurve):
    origin: Vector2
    direction: Vector2


@dataclass(frozen=True, slots=True)
class CirclePcurve(BrepPcurve):
    center: Vector2
    radius: float


@dataclass(frozen=True, slots=True)
class NurbsPcurve(BrepPcurve):
    degree: int
    control_points: tuple[Vector2, ...]
    knots: tuple[float, ...]
    multiplicities: tuple[int, ...]
    weights: tuple[float, ...] = ()
    periodic: bool = False


@dataclass(frozen=True, slots=True)
class NativePcurve(BrepPcurve):
    format_id: str
    entity_type: str
    data: Mapping[str, Any] = field(default_factory=frozen_mapping)


@dataclass(frozen=True, slots=True)
class BrepSurface(BrepEntity):
    def __post_init__(self) -> None:
        if not isinstance(self.id, str):
            raise TypeError("B-rep surface id must be a string")


@dataclass(frozen=True, slots=True)
class PlaneSurface(BrepSurface):
    origin: Vector3
    normal: Vector3
    reference_direction: Vector3


@dataclass(frozen=True, slots=True)
class CylinderSurface(BrepSurface):
    origin: Vector3
    axis: Vector3
    reference_direction: Vector3
    radius: float


@dataclass(frozen=True, slots=True)
class ConeSurface(BrepSurface):
    origin: Vector3
    axis: Vector3
    reference_direction: Vector3
    radius: float
    half_angle: float


@dataclass(frozen=True, slots=True)
class SphereSurface(BrepSurface):
    center: Vector3
    axis: Vector3
    reference_direction: Vector3
    radius: float


@dataclass(frozen=True, slots=True)
class TorusSurface(BrepSurface):
    center: Vector3
    axis: Vector3
    reference_direction: Vector3
    major_radius: float
    minor_radius: float


@dataclass(frozen=True, slots=True)
class NurbsSurface(BrepSurface):
    degree_u: int
    degree_v: int
    control_points: tuple[tuple[Vector3, ...], ...]
    knots_u: tuple[float, ...]
    knots_v: tuple[float, ...]
    multiplicities_u: tuple[int, ...]
    multiplicities_v: tuple[int, ...]
    weights: tuple[tuple[float, ...], ...] = ()
    periodic_u: bool = False
    periodic_v: bool = False


@dataclass(frozen=True, slots=True)
class OffsetSurface(BrepSurface):
    base_surface_id: str
    distance: float


@dataclass(frozen=True, slots=True)
class NativeSurface(BrepSurface):
    format_id: str
    entity_type: str
    data: Mapping[str, Any] = field(default_factory=frozen_mapping)


@dataclass(frozen=True, slots=True)
class BrepVertex(BrepEntity):
    point: Vector3
    tolerance: float = 0.0


@dataclass(frozen=True, slots=True)
class BrepEdge(BrepEntity):
    start_vertex_id: str
    end_vertex_id: str
    curve_id: str
    start_parameter: float
    end_parameter: float
    tolerance: float = 0.0
    degenerate: bool = False


@dataclass(frozen=True, slots=True)
class BrepCoedge(BrepEntity):
    edge_id: str
    pcurve_id: str = ""
    reversed: bool = False


@dataclass(frozen=True, slots=True)
class BrepLoop(BrepEntity):
    coedge_ids: tuple[str, ...]
    outer: bool = False


@dataclass(frozen=True, slots=True)
class BrepWire(BrepEntity):
    coedge_ids: tuple[str, ...]
    closed: bool = False


@dataclass(frozen=True, slots=True)
class BrepFace(BrepEntity):
    surface_id: str
    loop_ids: tuple[str, ...]
    same_sense: bool = True
    tolerance: float = 0.0


@dataclass(frozen=True, slots=True)
class BrepFaceUse(BrepEntity):
    face_id: str
    reversed: bool = False


@dataclass(frozen=True, slots=True)
class BrepShell(BrepEntity):
    face_use_ids: tuple[str, ...]
    closed: bool = False


@dataclass(frozen=True, slots=True)
class BrepShellUse(BrepEntity):
    shell_id: str
    reversed: bool = False


@dataclass(frozen=True, slots=True)
class BrepRegion(BrepEntity):
    shell_use_ids: tuple[str, ...]
    solid: bool = True


@dataclass(frozen=True, slots=True)
class BrepBody(BrepEntity):
    region_ids: tuple[str, ...]
    transform: Transform = Transform()
    design_body_id: str = ""
    wire_ids: tuple[str, ...] = ()
    vertex_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class BrepModel:
    curves: tuple[BrepCurve, ...] = ()
    pcurves: tuple[BrepPcurve, ...] = ()
    surfaces: tuple[BrepSurface, ...] = ()
    vertices: tuple[BrepVertex, ...] = ()
    edges: tuple[BrepEdge, ...] = ()
    coedges: tuple[BrepCoedge, ...] = ()
    loops: tuple[BrepLoop, ...] = ()
    wires: tuple[BrepWire, ...] = ()
    faces: tuple[BrepFace, ...] = ()
    face_uses: tuple[BrepFaceUse, ...] = ()
    shells: tuple[BrepShell, ...] = ()
    shell_uses: tuple[BrepShellUse, ...] = ()
    regions: tuple[BrepRegion, ...] = ()
    bodies: tuple[BrepBody, ...] = ()
    schema_version: str = "1.0"

    def validate(
        self, design_body_ids: frozenset[str] = frozenset()
    ) -> tuple[str, ...]:
        errors: list[str] = []
        if (
            not isinstance(self.schema_version, str)
            or not self.schema_version.strip()
            or self.schema_version != self.schema_version.strip()
        ):
            errors.append("B-rep schema version must be a non-empty string")
        collections = {
            item.name: getattr(self, item.name)
            for item in fields(self)
            if item.name != "schema_version"
        }
        ids: dict[str, frozenset[str]] = {}
        for name, values in collections.items():
            identifiers = tuple(value.id for value in values)
            if any(not identifier for identifier in identifiers):
                errors.append(f"B-rep {name} contains an empty id")
            if len(identifiers) != len(set(identifiers)):
                errors.append(f"B-rep {name} contains duplicate ids")
            ids[name] = frozenset(identifiers)
        for curve in self.curves:
            errors.extend(_curve_errors(curve, ids["surfaces"]))
        for pcurve in self.pcurves:
            errors.extend(_pcurve_errors(pcurve))
        for surface in self.surfaces:
            errors.extend(_surface_errors(surface, ids["surfaces"]))
        for vertex in self.vertices:
            if not _finite_vector3(vertex.point) or not _valid_tolerance(
                vertex.tolerance
            ):
                errors.append(f"B-rep vertex {vertex.id} is invalid")
        for edge in self.edges:
            if edge.start_vertex_id not in ids["vertices"]:
                errors.append(f"B-rep edge {edge.id} references a missing start vertex")
            if edge.end_vertex_id not in ids["vertices"]:
                errors.append(f"B-rep edge {edge.id} references a missing end vertex")
            if edge.curve_id not in ids["curves"]:
                errors.append(f"B-rep edge {edge.id} references a missing curve")
            if not all(
                isfinite(value) for value in (edge.start_parameter, edge.end_parameter)
            ) or not _valid_tolerance(edge.tolerance):
                errors.append(f"B-rep edge {edge.id} has an invalid range or tolerance")
        for coedge in self.coedges:
            if coedge.edge_id not in ids["edges"]:
                errors.append(f"B-rep coedge {coedge.id} references a missing edge")
            if coedge.pcurve_id and coedge.pcurve_id not in ids["pcurves"]:
                errors.append(f"B-rep coedge {coedge.id} references a missing pcurve")
        edge_by_id = {edge.id: edge for edge in self.edges}
        coedge_by_id = {coedge.id: coedge for coedge in self.coedges}
        for loop in self.loops:
            if not loop.coedge_ids:
                errors.append(f"B-rep loop {loop.id} is empty")
            for coedge_id in loop.coedge_ids:
                if coedge_id not in ids["coedges"]:
                    errors.append(f"B-rep loop {loop.id} references a missing coedge")
            if not _coedges_connect(loop.coedge_ids, coedge_by_id, edge_by_id, True):
                errors.append(f"B-rep loop {loop.id} is disconnected or open")
        for wire in self.wires:
            if not wire.coedge_ids:
                errors.append(f"B-rep wire {wire.id} is empty")
            for coedge_id in wire.coedge_ids:
                if coedge_id not in ids["coedges"]:
                    errors.append(f"B-rep wire {wire.id} references a missing coedge")
            if not _coedges_connect(
                wire.coedge_ids, coedge_by_id, edge_by_id, wire.closed
            ):
                errors.append(f"B-rep wire {wire.id} has inconsistent connectivity")
        for face in self.faces:
            if face.surface_id not in ids["surfaces"]:
                errors.append(f"B-rep face {face.id} references a missing surface")
            if not face.loop_ids:
                errors.append(f"B-rep face {face.id} has no loops")
            for loop_id in face.loop_ids:
                if loop_id not in ids["loops"]:
                    errors.append(f"B-rep face {face.id} references a missing loop")
            if not _valid_tolerance(face.tolerance):
                errors.append(f"B-rep face {face.id} has an invalid tolerance")
        for face_use in self.face_uses:
            if face_use.face_id not in ids["faces"]:
                errors.append(f"B-rep face use {face_use.id} references a missing face")
        for shell in self.shells:
            if not shell.face_use_ids:
                errors.append(f"B-rep shell {shell.id} is empty")
            for face_use_id in shell.face_use_ids:
                if face_use_id not in ids["face_uses"]:
                    errors.append(
                        f"B-rep shell {shell.id} references a missing face use"
                    )
        for shell_use in self.shell_uses:
            if shell_use.shell_id not in ids["shells"]:
                errors.append(
                    f"B-rep shell use {shell_use.id} references a missing shell"
                )
        for region in self.regions:
            if not region.shell_use_ids:
                errors.append(f"B-rep region {region.id} is empty")
            for shell_use_id in region.shell_use_ids:
                if shell_use_id not in ids["shell_uses"]:
                    errors.append(
                        f"B-rep region {region.id} references a missing shell use"
                    )
        for body in self.bodies:
            if not body.region_ids and not body.wire_ids and not body.vertex_ids:
                errors.append(f"B-rep body {body.id} is empty")
            for region_id in body.region_ids:
                if region_id not in ids["regions"]:
                    errors.append(f"B-rep body {body.id} references a missing region")
            for wire_id in body.wire_ids:
                if wire_id not in ids["wires"]:
                    errors.append(f"B-rep body {body.id} references a missing wire")
            for vertex_id in body.vertex_ids:
                if vertex_id not in ids["vertices"]:
                    errors.append(f"B-rep body {body.id} references a missing vertex")
            if not _finite_transform(body.transform):
                errors.append(f"B-rep body {body.id} has an invalid transform")
            if body.design_body_id and body.design_body_id not in design_body_ids:
                errors.append(f"B-rep body {body.id} references a missing design body")
        if not self.bodies:
            errors.append("B-rep model has no bodies")
        return tuple(errors)


def _finite_vector2(value: Vector2) -> bool:
    return all(isfinite(component) for component in (value.x, value.y))


def _finite_vector3(value: Vector3) -> bool:
    return all(isfinite(component) for component in (value.x, value.y, value.z))


def _finite_transform(value: Transform) -> bool:
    return all(
        _finite_vector3(vector)
        for vector in (value.origin, value.x_axis, value.y_axis, value.z_axis)
    )


def _nonzero_vector2(value: Vector2) -> bool:
    return _finite_vector2(value) and any(
        component != 0.0 for component in (value.x, value.y)
    )


def _nonzero_vector3(value: Vector3) -> bool:
    return _finite_vector3(value) and any(
        component != 0.0 for component in (value.x, value.y, value.z)
    )


def _valid_tolerance(value: float) -> bool:
    return isfinite(value) and value >= 0.0


def _valid_spline(
    degree: int,
    count: int,
    knots: tuple[float, ...],
    multiplicities: tuple[int, ...],
    weights: tuple[float, ...],
    periodic: bool,
) -> bool:
    return (
        type(degree) is int
        and degree >= 1
        and count > degree
        and len(knots) == len(multiplicities)
        and bool(knots)
        and all(isfinite(value) for value in knots)
        and all(left < right for left, right in zip(knots, knots[1:]))
        and all(type(value) is int and value > 0 for value in multiplicities)
        and (periodic or sum(multiplicities) == count + degree + 1)
        and (not weights or len(weights) == count)
        and all(isfinite(value) and value > 0.0 for value in weights)
    )


def _coedges_connect(
    coedge_ids: tuple[str, ...],
    coedge_by_id: Mapping[str, BrepCoedge],
    edge_by_id: Mapping[str, BrepEdge],
    closed: bool,
) -> bool:
    uses: list[tuple[str, str]] = []
    for coedge_id in coedge_ids:
        coedge = coedge_by_id.get(coedge_id)
        if coedge is None:
            return False
        edge = edge_by_id.get(coedge.edge_id)
        if edge is None:
            return False
        start, end = edge.start_vertex_id, edge.end_vertex_id
        uses.append((end, start) if coedge.reversed else (start, end))
    if not uses:
        return False
    if any(left[1] != right[0] for left, right in zip(uses, uses[1:])):
        return False
    return not closed or uses[-1][1] == uses[0][0]


def _curve_errors(curve: BrepCurve, surface_ids: frozenset[str]) -> tuple[str, ...]:
    valid = False
    if isinstance(curve, LineCurve):
        valid = _finite_vector3(curve.origin) and _nonzero_vector3(curve.direction)
    elif isinstance(curve, CircleCurve):
        valid = (
            _finite_vector3(curve.center)
            and _nonzero_vector3(curve.axis)
            and _nonzero_vector3(curve.reference_direction)
            and isfinite(curve.radius)
            and curve.radius > 0.0
        )
    elif isinstance(curve, EllipseCurve):
        valid = (
            _finite_vector3(curve.center)
            and _nonzero_vector3(curve.axis)
            and _nonzero_vector3(curve.reference_direction)
            and isfinite(curve.major_radius)
            and isfinite(curve.minor_radius)
            and curve.major_radius >= curve.minor_radius > 0.0
        )
    elif isinstance(curve, NurbsCurve):
        valid = all(
            _finite_vector3(point) for point in curve.control_points
        ) and _valid_spline(
            curve.degree,
            len(curve.control_points),
            curve.knots,
            curve.multiplicities,
            curve.weights,
            curve.periodic,
        )
    elif isinstance(curve, IntersectionCurve):
        valid = (
            curve.first_surface_id in surface_ids
            and curve.second_surface_id in surface_ids
            and curve.first_surface_id != curve.second_surface_id
            and all(_finite_vector3(point) for point in curve.samples)
            and _valid_tolerance(curve.tolerance)
        )
    elif isinstance(curve, NativeCurve):
        valid = bool(curve.format_id and curve.entity_type)
    return () if valid else (f"B-rep curve {curve.id} is invalid",)


def _pcurve_errors(curve: BrepPcurve) -> tuple[str, ...]:
    valid = False
    if isinstance(curve, LinePcurve):
        valid = _finite_vector2(curve.origin) and _nonzero_vector2(curve.direction)
    elif isinstance(curve, CirclePcurve):
        valid = (
            _finite_vector2(curve.center)
            and isfinite(curve.radius)
            and curve.radius > 0.0
        )
    elif isinstance(curve, NurbsPcurve):
        valid = all(
            _finite_vector2(point) for point in curve.control_points
        ) and _valid_spline(
            curve.degree,
            len(curve.control_points),
            curve.knots,
            curve.multiplicities,
            curve.weights,
            curve.periodic,
        )
    elif isinstance(curve, NativePcurve):
        valid = bool(curve.format_id and curve.entity_type)
    return () if valid else (f"B-rep pcurve {curve.id} is invalid",)


def _surface_errors(
    surface: BrepSurface, surface_ids: frozenset[str]
) -> tuple[str, ...]:
    valid = False
    if isinstance(surface, PlaneSurface):
        valid = (
            _finite_vector3(surface.origin)
            and _nonzero_vector3(surface.normal)
            and _nonzero_vector3(surface.reference_direction)
        )
    elif isinstance(surface, CylinderSurface):
        valid = (
            _finite_vector3(surface.origin)
            and _nonzero_vector3(surface.axis)
            and _nonzero_vector3(surface.reference_direction)
            and isfinite(surface.radius)
            and surface.radius > 0.0
        )
    elif isinstance(surface, ConeSurface):
        valid = (
            _finite_vector3(surface.origin)
            and _nonzero_vector3(surface.axis)
            and _nonzero_vector3(surface.reference_direction)
            and isfinite(surface.radius)
            and surface.radius >= 0.0
            and isfinite(surface.half_angle)
            and 0.0 < abs(surface.half_angle) < pi / 2.0
        )
    elif isinstance(surface, SphereSurface):
        valid = (
            _finite_vector3(surface.center)
            and _nonzero_vector3(surface.axis)
            and _nonzero_vector3(surface.reference_direction)
            and isfinite(surface.radius)
            and surface.radius > 0.0
        )
    elif isinstance(surface, TorusSurface):
        valid = (
            _finite_vector3(surface.center)
            and _nonzero_vector3(surface.axis)
            and _nonzero_vector3(surface.reference_direction)
            and isfinite(surface.major_radius)
            and surface.major_radius != 0.0
            and isfinite(surface.minor_radius)
            and surface.minor_radius > 0.0
        )
    elif isinstance(surface, NurbsSurface):
        rows = surface.control_points
        row_size = len(rows[0]) if rows else 0
        weights = surface.weights
        valid = (
            bool(rows)
            and row_size > 0
            and all(len(row) == row_size for row in rows)
            and all(_finite_vector3(point) for row in rows for point in row)
            and _valid_spline(
                surface.degree_u,
                len(rows),
                surface.knots_u,
                surface.multiplicities_u,
                tuple(1.0 for _ in rows) if weights else (),
                surface.periodic_u,
            )
            and _valid_spline(
                surface.degree_v,
                row_size,
                surface.knots_v,
                surface.multiplicities_v,
                tuple(1.0 for _ in range(row_size)) if weights else (),
                surface.periodic_v,
            )
            and (
                not weights
                or (
                    len(weights) == len(rows)
                    and all(len(row) == row_size for row in weights)
                    and all(
                        isfinite(value) and value > 0.0
                        for row in weights
                        for value in row
                    )
                )
            )
        )
    elif isinstance(surface, OffsetSurface):
        valid = (
            surface.base_surface_id in surface_ids
            and surface.base_surface_id != surface.id
            and isfinite(surface.distance)
        )
    elif isinstance(surface, NativeSurface):
        valid = bool(surface.format_id and surface.entity_type)
    return () if valid else (f"B-rep surface {surface.id} is invalid",)
