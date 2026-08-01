from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from math import isfinite
from typing import Any, Mapping

from .types import (
    BoundingBox,
    ParameterValue,
    Provenance,
    frozen_mapping,
)


class ComponentKind(StrEnum):
    PART = "part"
    ASSEMBLY = "assembly"
    REFERENCE = "reference"
    NATIVE = "native"


class MateKind(StrEnum):
    COINCIDENT = "coincident"
    CONCENTRIC = "concentric"
    PARALLEL = "parallel"
    PERPENDICULAR = "perpendicular"
    TANGENT = "tangent"
    DISTANCE = "distance"
    ANGLE = "angle"
    LOCK = "lock"
    GEAR = "gear"
    RACK_PINION = "rack_pinion"
    SCREW = "screw"
    UNIVERSAL_JOINT = "universal_joint"
    CAM = "cam"
    SLOT = "slot"
    WIDTH = "width"
    SYMMETRIC = "symmetric"
    LINEAR_COUPLER = "linear_coupler"
    BELT = "belt"
    PATH = "path"
    MAGNETIC = "magnetic"
    HINGE = "hinge"
    PROFILE_CENTER = "profile_center"
    NATIVE = "native"


class MateEntityKind(StrEnum):
    VERTEX = "vertex"
    EDGE = "edge"
    FACE = "face"
    POINT = "point"
    LINE = "line"
    AXIS = "axis"
    PLANE = "plane"
    CIRCLE = "circle"
    CYLINDER = "cylinder"
    CONE = "cone"
    SPHERE = "sphere"
    CURVE = "curve"
    SURFACE = "surface"
    SKETCH_ENTITY = "sketch_entity"
    COORDINATE_SYSTEM = "coordinate_system"
    NATIVE = "native"


class MateAlignment(StrEnum):
    ALIGNED = "aligned"
    ANTI_ALIGNED = "anti_aligned"
    CLOSEST = "closest"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class Matrix4:
    values: tuple[float, ...] = (
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

    def rows(self) -> tuple[tuple[float, float, float, float], ...]:
        if len(self.values) != 16:
            raise ValueError("matrix does not contain 16 values")
        return tuple(
            tuple(self.values[offset : offset + 4]) for offset in range(0, 16, 4)
        )

    def is_finite(self) -> bool:
        return len(self.values) == 16 and all(isfinite(value) for value in self.values)

    def transform_point(
        self, point: tuple[float, float, float]
    ) -> tuple[float, float, float]:
        rows = self.rows()
        x, y, z = point
        return tuple(row[0] * x + row[1] * y + row[2] * z + row[3] for row in rows[:3])


@dataclass(frozen=True, slots=True)
class ComponentDocument:
    id: str
    document: Any


@dataclass(frozen=True, slots=True)
class ComponentDefinition:
    id: str
    name: str
    kind: ComponentKind | str
    document_id: str = ""
    configuration_name: str = ""
    configuration_id: str = ""
    bounding_box: BoundingBox | None = None
    body_ids: tuple[str, ...] = ()
    mesh_ids: tuple[str, ...] = ()
    source_path: str = ""
    source_format_id: str = ""
    source_sha256: str = ""
    provenance: Provenance | None = None
    attributes: Mapping[str, Any] = field(default_factory=frozen_mapping)


@dataclass(frozen=True, slots=True)
class ComponentInstance:
    id: str
    name: str
    definition_id: str
    owner_definition_id: str
    transform: Matrix4 = Matrix4()
    order: int = 0
    reference_number: str = ""
    configuration_name: str = ""
    configuration_id: str = ""
    suppressed: bool = False
    hidden: bool = False
    fixed: bool = False
    flexible: bool = False
    exclude_from_bom: bool = False
    provenance: Provenance | None = None
    attributes: Mapping[str, Any] = field(default_factory=frozen_mapping)


@dataclass(frozen=True, slots=True)
class MateEntity:
    id: str
    owner_definition_id: str
    instance_path: tuple[str, ...]
    kind: MateEntityKind | str
    source_entity_id: str = ""
    selection_id: str = ""
    frame: Matrix4 | None = None
    radius: float | None = None
    provenance: Provenance | None = None
    attributes: Mapping[str, Any] = field(default_factory=frozen_mapping)


@dataclass(frozen=True, slots=True)
class MateConstraint:
    id: str
    name: str
    kind: MateKind | str
    owner_definition_id: str
    entity_ids: tuple[str, ...]
    order: int = 0
    value: ParameterValue | None = None
    parameter_ids: tuple[str, ...] = ()
    alignment: MateAlignment | str = MateAlignment.UNKNOWN
    suppressed: bool = False
    driving: bool = True
    provenance: Provenance | None = None
    attributes: Mapping[str, Any] = field(default_factory=frozen_mapping)


@dataclass(frozen=True, slots=True)
class MateGroup:
    id: str
    name: str
    owner_definition_id: str
    mate_ids: tuple[str, ...]
    parent_group_id: str = ""
    order: int = 0
    provenance: Provenance | None = None
    attributes: Mapping[str, Any] = field(default_factory=frozen_mapping)


@dataclass(frozen=True, slots=True)
class AssemblyData:
    root_definition_id: str
    definitions: tuple[ComponentDefinition, ...]
    instances: tuple[ComponentInstance, ...]
    documents: tuple[ComponentDocument, ...] = ()
    mate_entities: tuple[MateEntity, ...] = ()
    mates: tuple[MateConstraint, ...] = ()
    mate_groups: tuple[MateGroup, ...] = ()
    attributes: Mapping[str, Any] = field(default_factory=frozen_mapping)

    def definition(self, entity_id: str) -> ComponentDefinition:
        for definition in self.definitions:
            if definition.id == entity_id:
                return definition
        raise KeyError(f"unknown component definition id {entity_id!r}")

    def document(self, entity_id: str) -> Any:
        for document in self.documents:
            if document.id == entity_id:
                return document.document
        raise KeyError(f"unknown component document id {entity_id!r}")

    def children(self, definition_id: str) -> tuple[ComponentInstance, ...]:
        return tuple(
            instance
            for instance in self.instances
            if instance.owner_definition_id == definition_id
        )
