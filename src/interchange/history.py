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
    UP_TO_FIRST = "up_to_first"
    UP_TO_LAST = "up_to_last"
    UP_TO_FACE = "up_to_face"
    UP_TO_SHAPE = "up_to_shape"
    UP_TO_VERTEX = "up_to_vertex"
    TWO_LENGTHS = "two_lengths"
    MID_PLANE = "mid_plane"
    OFFSET_FROM_SURFACE = "offset_from_surface"
    NATIVE = "native"


class PayloadRole(StrEnum):
    BREP = "brep"
    TESSELLATION = "tessellation"
    FEATURE_HISTORY = "feature_history"
    ASSEMBLY_STRUCTURE = "assembly_structure"
    DOCUMENT = "document"
    VERIFICATION = "verification"
    AUXILIARY = "auxiliary"


@dataclass(frozen=True, slots=True)
class _PayloadFieldRule:
    role: PayloadRole
    file_extension: str
    format_ids: frozenset[str] = frozenset()
    kinds: frozenset[str] = frozenset()
    schemas: frozenset[str] = frozenset()
    source_suffixes: frozenset[str] = frozenset()


_LEGACY_PAYLOAD_RULES = (
    _PayloadFieldRule(
        PayloadRole.DOCUMENT,
        ".catpart",
        frozenset({"catia.v5", "catia.v5.cfv2"}),
        frozenset({"native_document"}),
        frozenset({"catpart", "catprtcont"}),
    ),
    _PayloadFieldRule(
        PayloadRole.DOCUMENT,
        ".catproduct",
        frozenset({"catia.v5", "catia.v5.cfv2"}),
        frozenset({"native_document"}),
        frozenset({"catproduct", "catprodcont"}),
    ),
    _PayloadFieldRule(
        PayloadRole.DOCUMENT,
        ".FCStd",
        frozenset({"freecad.fcstd"}),
        frozenset({"native_document"}),
    ),
    _PayloadFieldRule(
        PayloadRole.DOCUMENT,
        ".sldprt",
        frozenset({"solidworks.sldprt"}),
        frozenset({"native_document"}),
    ),
    _PayloadFieldRule(
        PayloadRole.DOCUMENT,
        ".sldasm",
        frozenset({"solidworks.sldasm"}),
        frozenset({"native_document"}),
    ),
    _PayloadFieldRule(
        PayloadRole.VERIFICATION,
        ".sha256",
        kinds=frozenset({"native_document_binding"}),
        schemas=frozenset({"sha256"}),
    ),
    _PayloadFieldRule(
        PayloadRole.FEATURE_HISTORY,
        ".osmx",
        frozenset({"catia.v5.osmx"}),
        frozenset({"native_feature_graph"}),
    ),
    _PayloadFieldRule(
        PayloadRole.ASSEMBLY_STRUCTURE,
        ".osmx",
        frozenset({"catia.v5.osmx"}),
        frozenset({"native_product_graph"}),
    ),
    _PayloadFieldRule(
        PayloadRole.ASSEMBLY_STRUCTURE,
        ".bin",
        frozenset({"solidworks.mates"}),
    ),
    _PayloadFieldRule(
        PayloadRole.BREP,
        ".x_b",
        frozenset({"parasolid", "parasolid.x_b"}),
    ),
    _PayloadFieldRule(
        PayloadRole.BREP,
        ".x_t",
        frozenset({"parasolid.x_t"}),
    ),
    _PayloadFieldRule(
        PayloadRole.BREP,
        ".sat",
        frozenset({"acis.sat"}),
    ),
    _PayloadFieldRule(
        PayloadRole.BREP,
        ".sab",
        frozenset({"acis.sab"}),
    ),
    _PayloadFieldRule(
        PayloadRole.BREP,
        "",
        frozenset({"acis"}),
    ),
    _PayloadFieldRule(
        PayloadRole.BREP,
        ".brep",
        frozenset({"freecad.brep", "opencascade", "opencascade.brep"}),
    ),
    _PayloadFieldRule(
        PayloadRole.BREP,
        ".cgm",
        frozenset({"catia.cgm"}),
    ),
    _PayloadFieldRule(
        PayloadRole.BREP,
        ".mfbrp",
        frozenset({"catia.v5.mfbrp"}),
    ),
    _PayloadFieldRule(
        PayloadRole.BREP,
        ".bin",
        frozenset({"catia.v5.brep-mode"}),
    ),
    _PayloadFieldRule(
        PayloadRole.TESSELLATION,
        ".cgr",
        frozenset({"catia.cgr"}),
    ),
    _PayloadFieldRule(
        PayloadRole.FEATURE_HISTORY,
        ".osmx",
        schemas=frozenset({"catprtcont"}),
    ),
    _PayloadFieldRule(
        PayloadRole.ASSEMBLY_STRUCTURE,
        ".osmx",
        schemas=frozenset({"catprodcont"}),
    ),
    _PayloadFieldRule(
        PayloadRole.BREP,
        ".cgm",
        schemas=frozenset({"cgmgeom"}),
    ),
    _PayloadFieldRule(
        PayloadRole.BREP,
        ".mfbrp",
        schemas=frozenset({"catmfbrp"}),
    ),
    _PayloadFieldRule(
        PayloadRole.TESSELLATION,
        ".cgr",
        schemas=frozenset({"catcgrcont"}),
    ),
    _PayloadFieldRule(
        PayloadRole.BREP,
        "",
        kinds=frozenset({"brep", "brep_mode", "brep_topology", "native_brep", "shape"}),
    ),
    _PayloadFieldRule(
        PayloadRole.BREP,
        "",
        kinds=frozenset({"resolved-assembly"}),
    ),
    _PayloadFieldRule(
        PayloadRole.TESSELLATION,
        "",
        kinds=frozenset({"native_tessellation", "tessellation"}),
    ),
    _PayloadFieldRule(
        PayloadRole.FEATURE_HISTORY,
        "",
        kinds=frozenset({"feature-records", "feature_history", "native_feature_graph"}),
    ),
    _PayloadFieldRule(
        PayloadRole.ASSEMBLY_STRUCTURE,
        "",
        kinds=frozenset({"assembly_structure", "mate-list", "native_product_graph"}),
    ),
    _PayloadFieldRule(
        PayloadRole.DOCUMENT,
        "",
        kinds=frozenset({"native_document"}),
    ),
    _PayloadFieldRule(
        PayloadRole.BREP,
        ".brep",
        source_suffixes=frozenset({".brep"}),
    ),
    _PayloadFieldRule(
        PayloadRole.BREP,
        ".brp",
        source_suffixes=frozenset({".brp"}),
    ),
    _PayloadFieldRule(
        PayloadRole.BREP,
        ".x_b",
        source_suffixes=frozenset({".x_b"}),
    ),
    _PayloadFieldRule(
        PayloadRole.BREP,
        ".x_t",
        source_suffixes=frozenset({".x_t"}),
    ),
    _PayloadFieldRule(
        PayloadRole.BREP,
        ".sat",
        source_suffixes=frozenset({".sat"}),
    ),
    _PayloadFieldRule(
        PayloadRole.BREP,
        ".sab",
        source_suffixes=frozenset({".sab"}),
    ),
    _PayloadFieldRule(
        PayloadRole.BREP,
        ".cgm",
        source_suffixes=frozenset({".cgm"}),
    ),
    _PayloadFieldRule(
        PayloadRole.BREP,
        ".mfbrp",
        source_suffixes=frozenset({".mfbrp"}),
    ),
    _PayloadFieldRule(
        PayloadRole.TESSELLATION,
        ".cgr",
        source_suffixes=frozenset({".cgr"}),
    ),
    _PayloadFieldRule(
        PayloadRole.VERIFICATION,
        ".sha256",
        source_suffixes=frozenset({".sha256"}),
    ),
    _PayloadFieldRule(
        PayloadRole.DOCUMENT,
        ".FCStd",
        source_suffixes=frozenset({".fcstd"}),
    ),
    _PayloadFieldRule(
        PayloadRole.DOCUMENT,
        ".sldprt",
        source_suffixes=frozenset({".sldprt"}),
    ),
    _PayloadFieldRule(
        PayloadRole.DOCUMENT,
        ".sldasm",
        source_suffixes=frozenset({".sldasm"}),
    ),
    _PayloadFieldRule(
        PayloadRole.DOCUMENT,
        ".catpart",
        source_suffixes=frozenset({".catpart"}),
    ),
    _PayloadFieldRule(
        PayloadRole.DOCUMENT,
        ".catproduct",
        source_suffixes=frozenset({".catproduct"}),
    ),
)


def _payload_extension_error(extension: Any) -> str:
    if not isinstance(extension, str):
        return "payload file extension must start with a period"
    name = extension[1:] if extension.startswith(".") else ""
    if not name or not name[0].isascii() or not name[0].isalnum():
        return "payload file extension must start with a period"
    if any(
        not character.isascii() or not (character.isalnum() or character in "._-")
        for character in name
    ) or name.endswith("."):
        return "payload file extension contains an invalid character"
    return ""


class FeatureDefinition:
    __slots__ = ()


@dataclass(frozen=True, slots=True)
class ExtrusionFeature(FeatureDefinition):
    length: ParameterValue
    end_condition: ExtrusionEndCondition | str = ExtrusionEndCondition.BLIND
    reversed: bool = False
    symmetric: bool = False
    direction: Vector3 | None = None
    second_length: ParameterValue | None = None
    second_end_condition: ExtrusionEndCondition | str | None = None
    offset: ParameterValue | None = None
    second_offset: ParameterValue | None = None
    draft_angle: ParameterValue | None = None
    second_draft_angle: ParameterValue | None = None
    up_to_reference: str = ""
    second_up_to_reference: str = ""


@dataclass(frozen=True, slots=True)
class FilletFeature(FeatureDefinition):
    radius: ParameterValue
    variable_radius_parameter_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class NativeFeatureDefinition(FeatureDefinition):
    format_id: str
    type_id: str
    object_data: Mapping[str, Any] = field(default_factory=frozen_mapping)


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
    definition: FeatureDefinition | None = None
    selection_ids: tuple[str, ...] = ()
    suppressed: bool = False
    configuration_states: tuple[FeatureConfigurationState, ...] = ()
    provenance: Provenance | None = None
    attributes: Mapping[str, Any] = field(default_factory=frozen_mapping)

    def __post_init__(self) -> None:
        if self.definition is not None and not isinstance(
            self.definition, FeatureDefinition
        ):
            raise TypeError("feature definition must implement FeatureDefinition")


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
    role: PayloadRole = PayloadRole.AUXILIARY
    file_extension: str = ".bin"

    def __post_init__(self) -> None:
        if not isinstance(self.role, PayloadRole):
            raise TypeError("payload role must be a PayloadRole")
        if error := _payload_extension_error(self.file_extension):
            raise ValueError(error)


def _payload_field_text(values: Mapping[str, Any], name: str) -> str:
    value = values.get(name)
    return value.casefold().strip() if isinstance(value, str) else ""


def _payload_source_suffix(values: Mapping[str, Any]) -> str:
    source = _payload_field_text(values, "source_stream").replace("\\", "/")
    name = source.rsplit("/", 1)[-1]
    index = name.rfind(".")
    return name[index:] if index >= 0 else ""


def _payload_rule_matches(
    rule: _PayloadFieldRule,
    format_id: str,
    kind: str,
    schema: str,
    source_suffix: str,
) -> bool:
    return (
        (not rule.format_ids or format_id in rule.format_ids)
        and (not rule.kinds or kind in rule.kinds)
        and (not rule.schemas or schema in rule.schemas)
        and (not rule.source_suffixes or source_suffix in rule.source_suffixes)
    )


def _legacy_payload_fields(values: Mapping[str, Any]) -> tuple[PayloadRole, str]:
    format_id = _payload_field_text(values, "format_id")
    kind = _payload_field_text(values, "kind")
    schema = _payload_field_text(values, "schema")
    source_suffix = _payload_source_suffix(values)
    selected = next(
        (
            rule
            for rule in _LEGACY_PAYLOAD_RULES
            if _payload_rule_matches(
                rule,
                format_id,
                kind,
                schema,
                source_suffix,
            )
        ),
        None,
    )
    if selected is None:
        return (
            PayloadRole.AUXILIARY,
            source_suffix if not _payload_extension_error(source_suffix) else ".bin",
        )
    if selected.file_extension:
        return selected.role, selected.file_extension
    source_rule = next(
        (
            rule
            for rule in _LEGACY_PAYLOAD_RULES
            if rule.role == selected.role
            and rule.source_suffixes
            and _payload_rule_matches(
                rule,
                format_id,
                kind,
                schema,
                source_suffix,
            )
        ),
        None,
    )
    return (
        selected.role,
        (
            source_rule.file_extension
            if source_rule
            else (
                source_suffix if not _payload_extension_error(source_suffix) else ".bin"
            )
        ),
    )


def _migrate_brep_payload(values: Mapping[str, Any]) -> Mapping[str, Any]:
    missing_role = "role" not in values
    missing_extension = "file_extension" not in values
    if not missing_role and not missing_extension:
        return values
    role, file_extension = _legacy_payload_fields(values)
    migrated = dict(values)
    if missing_role:
        migrated["role"] = role
    if missing_extension:
        migrated["file_extension"] = file_extension
    return migrated


@dataclass(frozen=True, slots=True)
class AdapterCapabilities:
    values: frozenset[Capability] = frozenset()

    def supports(self, capability: Capability) -> bool:
        return capability in self.values
