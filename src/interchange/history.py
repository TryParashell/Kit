from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Mapping

from .types import (
    BooleanOperation,
    BoundingBox,
    Capability,
    FeatureKind,
    ParameterValue,
    Provenance,
    Vector3,
    frozen_mapping,
)


@dataclass(frozen=True, slots=True)
class FeatureConfigurationState:
    configuration_id: str
    suppressed: bool = False
    parameter_override_ids: tuple[str, ...] = ()


class ExtrusionEndCondition(StrEnum):
    BLIND = "blind"
    THROUGH_ALL = "through_all"
    UP_TO_FACE = "up_to_face"
    UP_TO_VERTEX = "up_to_vertex"
    MID_PLANE = "mid_plane"
    OFFSET_FROM_SURFACE = "offset_from_surface"
    NATIVE = "native"


@dataclass(frozen=True, slots=True)
class ExtrusionFeature:
    length: ParameterValue
    end_condition: ExtrusionEndCondition | str = ExtrusionEndCondition.BLIND
    reversed: bool = False
    symmetric: bool = False
    direction: Vector3 | None = None
    second_length: ParameterValue | None = None
    draft_angle: ParameterValue | None = None


@dataclass(frozen=True, slots=True)
class FilletFeature:
    radius: ParameterValue
    variable_radius_parameter_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class FeatureStep:
    id: str
    name: str
    kind: FeatureKind | str
    order: int
    input_feature_ids: tuple[str, ...] = ()
    sketch_id: str | None = None
    parameter_ids: tuple[str, ...] = ()
    operation: BooleanOperation | str | None = None
    definition: ExtrusionFeature | FilletFeature | None = None
    selection_ids: tuple[str, ...] = ()
    suppressed: bool = False
    configuration_states: tuple[FeatureConfigurationState, ...] = ()
    provenance: Provenance | None = None
    attributes: Mapping[str, Any] = field(default_factory=frozen_mapping)


@dataclass(frozen=True, slots=True)
class TopologySummary:
    solid_count: int = 0
    shell_count: int = 0
    face_count: int = 0
    edge_count: int = 0
    vertex_count: int = 0
    volume: float | None = None
    surface_area: float | None = None
    bounding_box: BoundingBox | None = None
    valid: bool | None = None


@dataclass(frozen=True, slots=True)
class Body:
    id: str
    name: str
    final_feature_id: str
    topology: TopologySummary = TopologySummary()
    material_id: str | None = None
    provenance: Provenance | None = None
    attributes: Mapping[str, Any] = field(default_factory=frozen_mapping)


@dataclass(frozen=True, slots=True)
class BrepPayload:
    id: str
    format_id: str
    kind: str
    schema: str
    sha256: str
    data: bytes | None = None
    source_stream: str = ""
    provenance: Provenance | None = None
    attributes: Mapping[str, Any] = field(default_factory=frozen_mapping)


@dataclass(frozen=True, slots=True)
class AdapterCapabilities:
    values: frozenset[Capability] = frozenset()

    def supports(self, capability: Capability) -> bool:
        return capability in self.values
