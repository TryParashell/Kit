from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from types import MappingProxyType
from typing import Any, Mapping


JsonScalar = str | int | float | bool | None
JsonValue = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]


def frozen_mapping(value: Mapping[str, Any] | None = None) -> Mapping[str, Any]:
    return MappingProxyType(dict(value or {}))


class UnitSystem(StrEnum):
    MILLIMETER = "mm"
    METER = "m"
    INCH = "in"


class ValueKind(StrEnum):
    LENGTH = "length"
    ANGLE = "angle"
    NUMBER = "number"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    STRING = "string"


class ParameterRole(StrEnum):
    DRIVING = "driving"
    DRIVEN = "driven"
    REFERENCE = "reference"
    DERIVED = "derived"


class FeatureKind(StrEnum):
    EXTRUSION = "extrusion"
    REVOLUTION = "revolution"
    SWEEP = "sweep"
    LOFT = "loft"
    FILLET = "fillet"
    CHAMFER = "chamfer"
    SHELL = "shell"
    DRAFT = "draft"
    PATTERN = "pattern"
    MIRROR = "mirror"
    BOOLEAN = "boolean"
    IMPORTED = "imported"
    REFERENCE = "reference"
    NATIVE = "native"


class BooleanOperation(StrEnum):
    CREATE = "create"
    JOIN = "join"
    CUT = "cut"
    INTERSECT = "intersect"


class GeometryKind(StrEnum):
    POINT = "point"
    LINE = "line"
    CIRCLE = "circle"
    ARC = "arc"
    ELLIPSE = "ellipse"
    SPLINE = "spline"
    NATIVE = "native"


class ConstraintKind(StrEnum):
    COINCIDENT = "coincident"
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"
    PARALLEL = "parallel"
    PERPENDICULAR = "perpendicular"
    TANGENT = "tangent"
    EQUAL = "equal"
    CONCENTRIC = "concentric"
    SYMMETRIC = "symmetric"
    MIDPOINT = "midpoint"
    DISTANCE = "distance"
    DISTANCE_X = "distance_x"
    DISTANCE_Y = "distance_y"
    ANGLE = "angle"
    RADIUS = "radius"
    DIAMETER = "diameter"
    FIXED = "fixed"
    NATIVE = "native"


class Severity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class Capability(StrEnum):
    PARAMETRIC_HISTORY = "parametric_history"
    EDITABLE_SKETCHES = "editable_sketches"
    CONFIGURATIONS = "configurations"
    EXPRESSIONS = "expressions"
    BREP = "brep"
    TESSELLATION = "tessellation"
    ASSEMBLIES = "assemblies"
    MATERIALS = "materials"
    NATIVE_PAYLOADS = "native_payloads"
    ROUNDTRIP_METADATA = "roundtrip_metadata"


@dataclass(frozen=True, slots=True)
class Vector2:
    x: float
    y: float


@dataclass(frozen=True, slots=True)
class Vector3:
    x: float
    y: float
    z: float


@dataclass(frozen=True, slots=True)
class Transform:
    origin: Vector3 = Vector3(0.0, 0.0, 0.0)
    x_axis: Vector3 = Vector3(1.0, 0.0, 0.0)
    y_axis: Vector3 = Vector3(0.0, 1.0, 0.0)
    z_axis: Vector3 = Vector3(0.0, 0.0, 1.0)


@dataclass(frozen=True, slots=True)
class BoundingBox:
    minimum: Vector3
    maximum: Vector3


@dataclass(frozen=True, slots=True)
class ProvenanceSpan:
    stream: str
    offset: int
    length: int
    record_kind: str = ""


@dataclass(frozen=True, slots=True)
class Provenance:
    adapter: str
    native_id: str = ""
    confidence: float = 1.0
    spans: tuple[ProvenanceSpan, ...] = ()
    attributes: Mapping[str, Any] = field(default_factory=frozen_mapping)


@dataclass(frozen=True, slots=True)
class ParameterValue:
    value: str | int | float | bool
    kind: ValueKind = ValueKind.NUMBER
    unit: str = ""


@dataclass(frozen=True, slots=True)
class Expression:
    source: str
    parameter_ids: tuple[str, ...] = ()
    language: str = "kit"


@dataclass(frozen=True, slots=True)
class Parameter:
    id: str
    name: str
    value: ParameterValue
    role: ParameterRole = ParameterRole.DRIVING
    expression: Expression | None = None
    owner_id: str = ""
    provenance: Provenance | None = None
    attributes: Mapping[str, Any] = field(default_factory=frozen_mapping)


@dataclass(frozen=True, slots=True)
class ParameterOverride:
    parameter_id: str
    value: ParameterValue


@dataclass(frozen=True, slots=True)
class Configuration:
    id: str
    name: str
    active: bool = False
    parent_id: str | None = None
    overrides: tuple[ParameterOverride, ...] = ()
    suppressed_feature_ids: tuple[str, ...] = ()
    attributes: Mapping[str, Any] = field(default_factory=frozen_mapping)


@dataclass(frozen=True, slots=True)
class CadSource:
    format_id: str
    path: str
    sha256: str
    container_version: str = ""
    application_version: str = ""
    attributes: Mapping[str, Any] = field(default_factory=frozen_mapping)


@dataclass(frozen=True, slots=True)
class Diagnostic:
    code: str
    message: str
    severity: Severity = Severity.WARNING
    entity_id: str = ""
    provenance: Provenance | None = None
    attributes: Mapping[str, Any] = field(default_factory=frozen_mapping)
