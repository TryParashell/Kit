from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from .types import GeometryKind, Provenance, Transform, Vector2, Vector3, frozen_mapping


@dataclass(frozen=True, slots=True)
class PointGeometry:
    point: Vector2


@dataclass(frozen=True, slots=True)
class LineGeometry:
    start: Vector2
    end: Vector2


@dataclass(frozen=True, slots=True)
class CircleGeometry:
    center: Vector2
    radius: float


@dataclass(frozen=True, slots=True)
class ArcGeometry:
    center: Vector2
    radius: float
    start_angle: float
    end_angle: float


@dataclass(frozen=True, slots=True)
class EllipseGeometry:
    center: Vector2
    major_axis: Vector2
    major_radius: float
    minor_radius: float


@dataclass(frozen=True, slots=True)
class SplineGeometry:
    control_points: tuple[Vector2, ...]
    degree: int
    knots: tuple[float, ...] = ()
    weights: tuple[float, ...] = ()
    periodic: bool = False


@dataclass(frozen=True, slots=True)
class NativeGeometry:
    format_id: str
    entity_type: str
    data: Mapping[str, Any] = field(default_factory=frozen_mapping)


Geometry = (
    PointGeometry
    | LineGeometry
    | CircleGeometry
    | ArcGeometry
    | EllipseGeometry
    | SplineGeometry
    | NativeGeometry
)


@dataclass(frozen=True, slots=True)
class SupportPlane:
    id: str
    name: str
    transform: Transform
    support_selection_id: str | None = None
    offset_parameter_id: str | None = None
    provenance: Provenance | None = None
    attributes: Mapping[str, Any] = field(default_factory=frozen_mapping)


@dataclass(frozen=True, slots=True)
class SketchEntity:
    id: str
    kind: GeometryKind
    geometry: Geometry
    construction: bool = False
    fixed: bool = False
    provenance: Provenance | None = None
    attributes: Mapping[str, Any] = field(default_factory=frozen_mapping)


@dataclass(frozen=True, slots=True)
class ConstraintReference:
    entity_id: str
    point: str = ""


@dataclass(frozen=True, slots=True)
class SketchConstraint:
    id: str
    kind: str
    references: tuple[ConstraintReference, ...]
    parameter_id: str | None = None
    driving: bool = True
    suppressed: bool = False
    provenance: Provenance | None = None
    attributes: Mapping[str, Any] = field(default_factory=frozen_mapping)


@dataclass(frozen=True, slots=True)
class Sketch:
    id: str
    name: str
    support_plane_id: str
    entities: tuple[SketchEntity, ...]
    constraints: tuple[SketchConstraint, ...] = ()
    parameter_ids: tuple[str, ...] = ()
    closed_profile_entity_ids: tuple[tuple[str, ...], ...] = ()
    suppressed: bool = False
    provenance: Provenance | None = None
    attributes: Mapping[str, Any] = field(default_factory=frozen_mapping)


@dataclass(frozen=True, slots=True)
class SelectionPathElement:
    entity_kind: str
    entity_id: str
    subelement: str = ""


@dataclass(frozen=True, slots=True)
class Selection:
    id: str
    name: str
    path: tuple[SelectionPathElement, ...]
    query: Mapping[str, Any] = field(default_factory=frozen_mapping)
    point: Vector3 | None = None
    provenance: Provenance | None = None
