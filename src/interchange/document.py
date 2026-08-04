# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from dataclasses import dataclass, field, fields, is_dataclass, replace
from functools import cache
import hashlib
from math import isfinite
from pathlib import Path
from typing import Any, Iterable, Mapping, get_args, get_origin, get_type_hints

from .assembly import AssemblyData, ComponentKind
from .brep import BrepModel
from .geometry import Selection, Sketch, SupportPlane
from .history import Body, BrepPayload, FeatureStep, PayloadRole
from .mesh import Mesh
from .serialization import dumps, from_data, loads, to_data
from .types import (
    CadSource,
    Capability,
    Configuration,
    Diagnostic,
    Parameter,
    FeatureKind,
    Provenance,
    UnitSystem,
    frozen_mapping,
)


class CadDocumentValidationError(ValueError):
    __slots__ = ()


_WRAPPER_METADATA_KEY = "kit.wrapper_metadata_keys"


def _type_label(value: type[Any]) -> str:
    return "".join(
        (
            f" {character.casefold()}"
            if index and character.isupper()
            else character.casefold()
        )
        for index, character in enumerate(value.__name__)
    )


def _identified_collections(
    value: Any,
) -> tuple[tuple[str, str, tuple[Any, ...]], ...]:
    return tuple(
        (name, label, getattr(value, name))
        for name, label in _identified_collection_fields(type(value))
    )


@cache
def _identified_collection_fields(
    value_type: type[Any],
) -> tuple[tuple[str, str], ...]:
    hints = get_type_hints(value_type)
    result: list[tuple[str, str]] = []
    for item in fields(value_type):
        hint = hints[item.name]
        arguments = get_args(hint)
        if (
            get_origin(hint) is not tuple
            or len(arguments) != 2
            or arguments[1] is not Ellipsis
        ):
            continue
        member_type = arguments[0]
        if (
            not isinstance(member_type, type)
            or not is_dataclass(member_type)
            or not any(member.name == "id" for member in fields(member_type))
        ):
            continue
        result.append((item.name, _type_label(member_type)))
    return tuple(result)


def _contains_provenance(value: Any) -> bool:
    pending = [value]
    seen: set[int] = set()
    while pending:
        item = pending.pop()
        if isinstance(item, Provenance):
            return True
        if item is None or isinstance(item, (str, bytes, int, float, bool)):
            continue
        identity = id(item)
        if identity in seen:
            continue
        seen.add(identity)
        if is_dataclass(item):
            pending.extend(getattr(item, member.name) for member in fields(item))
        elif isinstance(item, Mapping):
            pending.extend(item.values())
        elif isinstance(item, (tuple, list, set, frozenset)):
            pending.extend(item)
    return False


def with_wrapper_metadata(
    metadata: Mapping[str, Any], keys: Iterable[str]
) -> Mapping[str, Any]:
    existing = metadata.get(_WRAPPER_METADATA_KEY, ())
    names = (
        {value for value in existing if isinstance(value, str)}
        if isinstance(existing, (tuple, list, set, frozenset))
        else set()
    )
    names.update(value for value in keys if isinstance(value, str))
    result = dict(metadata)
    result[_WRAPPER_METADATA_KEY] = tuple(sorted(names))
    return frozen_mapping(result)


def semantic_metadata(metadata: Mapping[str, Any]) -> Mapping[str, Any]:
    values = metadata.get(_WRAPPER_METADATA_KEY, ())
    names = (
        frozenset(value for value in values if isinstance(value, str))
        if isinstance(values, (tuple, list, set, frozenset))
        else frozenset()
    )
    return frozen_mapping(
        {
            key: value
            for key, value in metadata.items()
            if key != _WRAPPER_METADATA_KEY and key not in names
        }
    )


def infer_capabilities(
    document: CadDocument, *, roundtrip_metadata: bool = False
) -> frozenset[Capability]:
    documents = tuple(_document_tree(document))
    assemblies = tuple(item.assembly for item in documents if item.assembly is not None)
    conditions = {
        Capability.PARAMETERS: any(item.parameters for item in documents),
        Capability.PARAMETRIC_HISTORY: any(
            feature.kind != FeatureKind.IMPORTED
            for item in documents
            for feature in item.feature_timeline
        ),
        Capability.SUPPORT_PLANES: any(item.support_planes for item in documents),
        Capability.EDITABLE_SKETCHES: any(item.sketches for item in documents),
        Capability.SELECTIONS: any(item.selections for item in documents),
        Capability.BODY_STRUCTURE: any(item.bodies for item in documents),
        Capability.CONFIGURATIONS: any(item.configurations for item in documents),
        Capability.EXPRESSIONS: any(
            parameter.expression is not None
            for item in documents
            for parameter in item.parameters
        ),
        Capability.BREP: any(
            item.brep is not None
            or any(
                payload.role == PayloadRole.BREP and payload.data is not None
                for payload in item.brep_payloads
            )
            for item in documents
        ),
        Capability.TESSELLATION: any(item.meshes for item in documents)
        or any(
            payload.role == PayloadRole.TESSELLATION and payload.data is not None
            for item in documents
            for payload in item.brep_payloads
        ),
        Capability.ASSEMBLIES: bool(assemblies),
        Capability.ASSEMBLY_MATES: any(assembly.mates for assembly in assemblies),
        Capability.COMPONENT_DOCUMENTS: any(
            assembly.documents for assembly in assemblies
        ),
        Capability.EXTERNAL_REFERENCES: any(
            definition.source_path
            for assembly in assemblies
            for definition in assembly.definitions
        ),
        Capability.MATERIALS: any(
            body.material_id for item in documents for body in item.bodies
        ),
        Capability.NATIVE_PAYLOADS: any(item.brep_payloads for item in documents),
        Capability.PROVENANCE: _contains_provenance(document),
        Capability.ROUNDTRIP_METADATA: roundtrip_metadata,
    }
    if conditions.keys() != set(Capability):
        raise RuntimeError("capability inference is not exhaustive")
    return frozenset(
        capability for capability, present in conditions.items() if present
    )


def retained_capabilities(
    document: CadDocument,
    capabilities: frozenset[Capability],
    *,
    include_brep: bool,
    include_tessellation: bool,
) -> frozenset[Capability]:
    retained = set(capabilities)
    if not include_brep:
        retained.discard(Capability.BREP)
    documents = tuple(_document_tree(document))
    if not include_tessellation and not any(
        item.meshes
        or any(
            payload.role == PayloadRole.TESSELLATION and payload.data is not None
            for payload in item.brep_payloads
        )
        for item in documents
    ):
        retained.discard(Capability.TESSELLATION)
    if not any(item.brep_payloads for item in documents):
        retained.discard(Capability.NATIVE_PAYLOADS)
    return frozenset(retained)


def filter_document(
    document: CadDocument,
    *,
    include_brep: bool,
    include_tessellation: bool,
    keep_payload_records: bool,
) -> CadDocument:
    assembly = document.assembly
    if assembly is not None:
        assembly = replace(
            assembly,
            documents=tuple(
                replace(
                    component,
                    document=(
                        filter_document(
                            component.document,
                            include_brep=include_brep,
                            include_tessellation=include_tessellation,
                            keep_payload_records=keep_payload_records,
                        )
                        if isinstance(component.document, CadDocument)
                        else component.document
                    ),
                )
                for component in assembly.documents
            ),
        )
    payloads: list[BrepPayload] = []
    for payload in document.brep_payloads:
        excluded = (payload.role == PayloadRole.BREP and not include_brep) or (
            payload.role == PayloadRole.TESSELLATION and not include_tessellation
        )
        if not excluded:
            payloads.append(payload)
        elif keep_payload_records:
            payloads.append(replace(payload, data=None))
    filtered = replace(
        document,
        meshes=document.meshes if include_tessellation else (),
        brep_payloads=tuple(payloads),
        assembly=assembly,
        brep=document.brep if include_brep else None,
    )
    return replace(
        filtered,
        capabilities=retained_capabilities(
            filtered,
            document.capabilities,
            include_brep=include_brep,
            include_tessellation=include_tessellation,
        ),
    )


def _document_tree(document: CadDocument):
    pending = [document]
    seen: set[int] = set()
    while pending:
        item = pending.pop()
        identity = id(item)
        if identity in seen:
            continue
        seen.add(identity)
        yield item
        if item.assembly is None:
            continue
        pending.extend(
            component.document
            for component in reversed(item.assembly.documents)
            if isinstance(component.document, CadDocument)
        )


def source_payload_indexes(document: CadDocument) -> frozenset[int]:
    try:
        source_digest = bytes.fromhex(document.source.sha256)
    except ValueError:
        return frozenset()
    if len(source_digest) != hashlib.sha256().digest_size:
        return frozenset()
    source_sha256 = document.source.sha256.casefold()
    documents = tuple(
        index
        for index, payload in enumerate(document.brep_payloads)
        if payload.role == PayloadRole.DOCUMENT
        and (
            hashlib.sha256(payload.data).hexdigest()
            if payload.data is not None
            else payload.sha256.casefold()
        )
        == source_sha256
    )
    bindings = tuple(
        index
        for index, payload in enumerate(document.brep_payloads)
        if (
            payload.role == PayloadRole.VERIFICATION
            or payload.role == PayloadRole.DOCUMENT
        )
        and payload.data == source_digest
        and payload.sha256.casefold() == hashlib.sha256(source_digest).hexdigest()
    )
    if len(documents) != 1 or len(bindings) != 1:
        return frozenset()
    return frozenset((*documents, *bindings))


@dataclass(frozen=True, slots=True)
class CadDocument:
    source: CadSource
    configurations: tuple[Configuration, ...]
    parameters: tuple[Parameter, ...]
    support_planes: tuple[SupportPlane, ...]
    sketches: tuple[Sketch, ...]
    selections: tuple[Selection, ...]
    feature_timeline: tuple[FeatureStep, ...]
    bodies: tuple[Body, ...]
    meshes: tuple[Mesh, ...] = ()
    brep_payloads: tuple[BrepPayload, ...] = ()
    diagnostics: tuple[Diagnostic, ...] = ()
    capabilities: frozenset[Capability] = frozenset()
    metadata: Mapping[str, Any] = field(default_factory=frozen_mapping)
    units: UnitSystem = UnitSystem.MILLIMETER
    schema_version: str = "1.0"
    assembly: AssemblyData | None = None
    brep: BrepModel | None = None

    def to_dict(self) -> dict[str, Any]:
        return to_data(self)

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> CadDocument:
        result = from_data(dict(value))
        if not isinstance(result, cls):
            raise TypeError("data does not describe a CadDocument")
        result.assert_valid()
        return result

    def to_json(self, *, indent: int | None = 2) -> str:
        return dumps(self, indent=indent)

    @classmethod
    def from_json(cls, source: str) -> CadDocument:
        result = loads(source)
        if not isinstance(result, cls):
            raise TypeError("JSON does not describe a CadDocument")
        result.assert_valid()
        return result

    def write_json(self, path: str | Path) -> Path:
        output = Path(path).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(self.to_json() + "\n", encoding="utf-8")
        return output

    @classmethod
    def read_json(cls, path: str | Path) -> CadDocument:
        return cls.from_json(Path(path).expanduser().resolve().read_text("utf-8"))

    def validate(self) -> tuple[str, ...]:
        errors: list[str] = []
        if not isinstance(self.capabilities, frozenset) or any(
            not isinstance(capability, Capability) for capability in self.capabilities
        ):
            errors.append("document capabilities must be Capability values")
        groups = _identified_collections(self)
        ids: dict[str, set[str]] = {}
        for name, label, items in groups:
            values = [item.id for item in items]
            if len(values) != len(set(values)):
                errors.append(f"duplicate {label} id")
            ids[name] = set(values)
        for configuration in self.configurations:
            if (
                configuration.parent_id
                and configuration.parent_id not in ids["configurations"]
            ):
                errors.append(f"configuration {configuration.id} has missing parent")
            for override in configuration.overrides:
                if override.parameter_id not in ids["parameters"]:
                    errors.append(
                        f"configuration {configuration.id} references missing parameter {override.parameter_id}"
                    )
        for parameter in self.parameters:
            if parameter.expression:
                for reference in parameter.expression.parameter_ids:
                    if reference not in ids["parameters"]:
                        errors.append(
                            f"parameter {parameter.id} references missing parameter {reference}"
                        )
        for plane in self.support_planes:
            if (
                plane.support_selection_id
                and plane.support_selection_id not in ids["selections"]
            ):
                errors.append(f"plane {plane.id} references missing selection")
            if (
                plane.offset_parameter_id
                and plane.offset_parameter_id not in ids["parameters"]
            ):
                errors.append(f"plane {plane.id} references missing offset parameter")
        for sketch in self.sketches:
            if sketch.support_plane_id not in ids["support_planes"]:
                errors.append(f"sketch {sketch.id} references missing plane")
            entity_ids = {entity.id for entity in sketch.entities}
            for constraint in sketch.constraints:
                for reference in constraint.references:
                    if reference.entity_id not in entity_ids:
                        errors.append(
                            f"constraint {constraint.id} references missing entity {reference.entity_id}"
                        )
                if (
                    constraint.parameter_id
                    and constraint.parameter_id not in ids["parameters"]
                ):
                    errors.append(
                        f"constraint {constraint.id} references missing parameter"
                    )
        order_by_feature = {
            feature.id: feature.order for feature in self.feature_timeline
        }
        if len(order_by_feature) != len(self.feature_timeline):
            errors.append("feature ids are not unique")
        if len({feature.order for feature in self.feature_timeline}) != len(
            self.feature_timeline
        ):
            errors.append("feature order values are not unique")
        for feature in self.feature_timeline:
            if feature.sketch_id and feature.sketch_id not in ids["sketches"]:
                errors.append(f"feature {feature.id} references missing sketch")
            for input_id in feature.input_feature_ids:
                if input_id not in order_by_feature:
                    errors.append(
                        f"feature {feature.id} references missing input {input_id}"
                    )
                elif order_by_feature[input_id] >= feature.order:
                    errors.append(f"feature {feature.id} has a forward dependency")
            for parameter_id in feature.parameter_ids:
                if parameter_id not in ids["parameters"]:
                    errors.append(f"feature {feature.id} references missing parameter")
            for selection_id in feature.selection_ids:
                if selection_id not in ids["selections"]:
                    errors.append(f"feature {feature.id} references missing selection")
        for body in self.bodies:
            if body.final_feature_id not in ids["feature_timeline"]:
                errors.append(f"body {body.id} references missing final feature")
        if self.brep is not None:
            if not isinstance(self.brep, BrepModel):
                errors.append("document B-rep must be a BrepModel")
            else:
                errors.extend(
                    self.brep.validate(frozenset(body.id for body in self.bodies))
                )
        if self.assembly is not None:
            errors.extend(self._validate_assembly(ids))
        if not self.configurations:
            errors.append("document has no configuration")
        if (
            not self.feature_timeline
            and self.brep is None
            and not self.brep_payloads
            and not self.meshes
            and self.assembly is None
        ):
            errors.append(
                "document has neither feature history, B-rep, mesh, nor assembly data"
            )
        return tuple(errors)

    def _validate_assembly(self, ids: Mapping[str, set[str]]) -> tuple[str, ...]:
        assembly = self.assembly
        if assembly is None:
            return ()
        errors: list[str] = []
        for _, label, items in _identified_collections(assembly):
            values = [item.id for item in items]
            if len(values) != len(set(values)):
                errors.append(f"duplicate {label} id")
        definitions = {item.id: item for item in assembly.definitions}
        instances = {item.id: item for item in assembly.instances}
        documents = {item.id: item.document for item in assembly.documents}
        meshes = {item.id: item for item in self.meshes}
        entities = {item.id: item for item in assembly.mate_entities}
        mates = {item.id: item for item in assembly.mates}
        groups_by_id = {item.id: item for item in assembly.mate_groups}
        if assembly.root_definition_id not in definitions:
            errors.append("assembly references missing root component definition")
        elif definitions[assembly.root_definition_id].kind != ComponentKind.ASSEMBLY:
            errors.append("assembly root component definition is not an assembly")
        for item in assembly.documents:
            if not isinstance(item.document, CadDocument):
                errors.append(
                    f"component document {item.id} does not contain a CadDocument"
                )
            elif item.document is self:
                errors.append(f"component document {item.id} contains its owner")
            else:
                errors.extend(
                    f"component document {item.id}: {error}"
                    for error in item.document.validate()
                )
        for definition in assembly.definitions:
            for mesh_id in definition.mesh_ids:
                if mesh_id not in meshes:
                    errors.append(
                        f"component definition {definition.id} references missing mesh {mesh_id}"
                    )
            if definition.document_id and definition.document_id not in documents:
                errors.append(
                    f"component definition {definition.id} references missing document"
                )
                continue
            target = documents.get(definition.document_id, self)
            if isinstance(target, CadDocument):
                target_body_ids = {body.id for body in target.bodies}
                for body_id in definition.body_ids:
                    if body_id not in target_body_ids:
                        errors.append(
                            f"component definition {definition.id} references missing body {body_id}"
                        )
        for mesh in self.meshes:
            if any(
                not all(isfinite(value) for value in (vertex.x, vertex.y, vertex.z))
                for vertex in mesh.vertices
            ):
                errors.append(f"mesh {mesh.id} contains a non-finite vertex")
            if mesh.normals and len(mesh.normals) != len(mesh.vertices):
                errors.append(f"mesh {mesh.id} has a mismatched normal count")
            if any(
                not all(isfinite(value) for value in (normal.x, normal.y, normal.z))
                for normal in mesh.normals
            ):
                errors.append(f"mesh {mesh.id} contains a non-finite normal")
            for triangle in mesh.triangles:
                if (
                    len(triangle) != 3
                    or any(type(index) is not int for index in triangle)
                    or any(
                        index < 0 or index >= len(mesh.vertices) for index in triangle
                    )
                ):
                    errors.append(f"mesh {mesh.id} contains an invalid triangle")
                    break
        graph = {definition_id: set() for definition_id in definitions}
        for instance in assembly.instances:
            if instance.definition_id not in definitions:
                errors.append(
                    f"component instance {instance.id} references missing definition"
                )
            if instance.owner_definition_id not in definitions:
                errors.append(
                    f"component instance {instance.id} references missing owner definition"
                )
            elif (
                definitions[instance.owner_definition_id].kind != ComponentKind.ASSEMBLY
            ):
                errors.append(
                    f"component instance {instance.id} owner is not an assembly"
                )
            if not instance.transform.is_finite():
                errors.append(
                    f"component instance {instance.id} has an invalid transform"
                )
            if (
                instance.owner_definition_id in graph
                and instance.definition_id in definitions
            ):
                graph[instance.owner_definition_id].add(instance.definition_id)
        state: dict[str, int] = {}

        def visit(definition_id: str) -> bool:
            status = state.get(definition_id, 0)
            if status == 1:
                return True
            if status == 2:
                return False
            state[definition_id] = 1
            cyclic = any(visit(child_id) for child_id in graph[definition_id])
            state[definition_id] = 2
            return cyclic

        if any(visit(definition_id) for definition_id in definitions):
            errors.append("component definition graph contains a cycle")
        for entity in assembly.mate_entities:
            if entity.owner_definition_id not in definitions:
                errors.append(
                    f"mate entity {entity.id} references missing owner definition"
                )
                continue
            current_definition_id = entity.owner_definition_id
            valid_path = True
            for instance_id in entity.instance_path:
                instance = instances.get(instance_id)
                if instance is None:
                    errors.append(
                        f"mate entity {entity.id} references missing instance {instance_id}"
                    )
                    valid_path = False
                    break
                if instance.owner_definition_id != current_definition_id:
                    errors.append(
                        f"mate entity {entity.id} has a disconnected instance path"
                    )
                    valid_path = False
                    break
                current_definition_id = instance.definition_id
            if entity.frame is not None and not entity.frame.is_finite():
                errors.append(f"mate entity {entity.id} has an invalid frame")
            if entity.radius is not None and (
                not isinstance(entity.radius, (int, float))
                or not float("-inf") < entity.radius < float("inf")
                or entity.radius < 0.0
            ):
                errors.append(f"mate entity {entity.id} has an invalid radius")
            if entity.selection_id and valid_path:
                target_definition = definitions.get(current_definition_id)
                target_document = self
                if target_definition is not None and target_definition.document_id:
                    target_document = documents.get(target_definition.document_id)
                target_selection_ids = (
                    ids["selections"]
                    if target_document is self
                    else {
                        selection.id
                        for selection in getattr(target_document, "selections", ())
                    }
                )
                if (
                    isinstance(target_document, CadDocument)
                    and entity.selection_id not in target_selection_ids
                ):
                    errors.append(
                        f"mate entity {entity.id} references missing selection"
                    )
        for mate in assembly.mates:
            if mate.owner_definition_id not in definitions:
                errors.append(f"mate {mate.id} references missing owner definition")
            if not mate.entity_ids:
                errors.append(f"mate {mate.id} has no entities")
            for entity_id in mate.entity_ids:
                entity = entities.get(entity_id)
                if entity is None:
                    errors.append(
                        f"mate {mate.id} references missing entity {entity_id}"
                    )
                elif entity.owner_definition_id != mate.owner_definition_id:
                    errors.append(
                        f"mate {mate.id} references entity from another assembly"
                    )
            owner_definition = definitions.get(mate.owner_definition_id)
            target_document = self
            if owner_definition is not None and owner_definition.document_id:
                target_document = documents.get(owner_definition.document_id)
            if isinstance(target_document, CadDocument):
                target_parameter_ids = (
                    ids["parameters"]
                    if target_document is self
                    else {parameter.id for parameter in target_document.parameters}
                )
                for parameter_id in mate.parameter_ids:
                    if parameter_id not in target_parameter_ids:
                        errors.append(
                            f"mate {mate.id} references missing parameter {parameter_id}"
                        )
        for group in assembly.mate_groups:
            if group.owner_definition_id not in definitions:
                errors.append(
                    f"mate group {group.id} references missing owner definition"
                )
            if group.parent_group_id:
                parent = groups_by_id.get(group.parent_group_id)
                if parent is None:
                    errors.append(f"mate group {group.id} references missing parent")
                elif parent.owner_definition_id != group.owner_definition_id:
                    errors.append(
                        f"mate group {group.id} has a parent in another assembly"
                    )
            for mate_id in group.mate_ids:
                mate = mates.get(mate_id)
                if mate is None:
                    errors.append(
                        f"mate group {group.id} references missing mate {mate_id}"
                    )
                elif mate.owner_definition_id != group.owner_definition_id:
                    errors.append(
                        f"mate group {group.id} contains mate from another assembly"
                    )
        for group in assembly.mate_groups:
            seen: set[str] = set()
            current = group
            while current.parent_group_id:
                if current.id in seen:
                    errors.append("mate group graph contains a cycle")
                    break
                seen.add(current.id)
                parent = groups_by_id.get(current.parent_group_id)
                if parent is None:
                    break
                current = parent
        return tuple(errors)

    def assert_valid(self) -> None:
        errors = self.validate()
        if errors:
            raise CadDocumentValidationError("; ".join(errors))

    def parameter(self, entity_id: str) -> Parameter:
        return self._lookup(self.parameters, entity_id, "parameter")

    def sketch(self, entity_id: str) -> Sketch:
        return self._lookup(self.sketches, entity_id, "sketch")

    def feature(self, entity_id: str) -> FeatureStep:
        return self._lookup(self.feature_timeline, entity_id, "feature")

    def plane(self, entity_id: str) -> SupportPlane:
        return self._lookup(self.support_planes, entity_id, "plane")

    @staticmethod
    def _lookup(items: tuple[Any, ...], entity_id: str, label: str) -> Any:
        for item in items:
            if item.id == entity_id:
                return item
        raise KeyError(f"unknown {label} id {entity_id!r}")
