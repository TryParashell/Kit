from __future__ import annotations

from dataclasses import dataclass, field
from math import isfinite
from pathlib import Path
from typing import Any, Mapping

from .assembly import AssemblyData, ComponentKind
from .geometry import Selection, Sketch, SupportPlane
from .history import Body, BrepPayload, FeatureStep
from .mesh import Mesh
from .serialization import dumps, from_data, loads, to_data
from .types import (
    CadSource,
    Capability,
    Configuration,
    Diagnostic,
    Parameter,
    UnitSystem,
    frozen_mapping,
)


class CadDocumentValidationError(ValueError):
    __slots__ = ()


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
        groups = {
            "configuration": self.configurations,
            "parameter": self.parameters,
            "plane": self.support_planes,
            "sketch": self.sketches,
            "selection": self.selections,
            "feature": self.feature_timeline,
            "body": self.bodies,
            "brep": self.brep_payloads,
            "mesh": self.meshes,
        }
        ids: dict[str, set[str]] = {}
        for label, items in groups.items():
            values = [item.id for item in items]
            if len(values) != len(set(values)):
                errors.append(f"duplicate {label} id")
            ids[label] = set(values)
        for configuration in self.configurations:
            if (
                configuration.parent_id
                and configuration.parent_id not in ids["configuration"]
            ):
                errors.append(f"configuration {configuration.id} has missing parent")
            for override in configuration.overrides:
                if override.parameter_id not in ids["parameter"]:
                    errors.append(
                        f"configuration {configuration.id} references missing parameter {override.parameter_id}"
                    )
        for parameter in self.parameters:
            if parameter.expression:
                for reference in parameter.expression.parameter_ids:
                    if reference not in ids["parameter"]:
                        errors.append(
                            f"parameter {parameter.id} references missing parameter {reference}"
                        )
        for plane in self.support_planes:
            if (
                plane.support_selection_id
                and plane.support_selection_id not in ids["selection"]
            ):
                errors.append(f"plane {plane.id} references missing selection")
            if (
                plane.offset_parameter_id
                and plane.offset_parameter_id not in ids["parameter"]
            ):
                errors.append(f"plane {plane.id} references missing offset parameter")
        for sketch in self.sketches:
            if sketch.support_plane_id not in ids["plane"]:
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
                    and constraint.parameter_id not in ids["parameter"]
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
            if feature.sketch_id and feature.sketch_id not in ids["sketch"]:
                errors.append(f"feature {feature.id} references missing sketch")
            for input_id in feature.input_feature_ids:
                if input_id not in order_by_feature:
                    errors.append(
                        f"feature {feature.id} references missing input {input_id}"
                    )
                elif order_by_feature[input_id] >= feature.order:
                    errors.append(f"feature {feature.id} has a forward dependency")
            for parameter_id in feature.parameter_ids:
                if parameter_id not in ids["parameter"]:
                    errors.append(f"feature {feature.id} references missing parameter")
            for selection_id in feature.selection_ids:
                if selection_id not in ids["selection"]:
                    errors.append(f"feature {feature.id} references missing selection")
        for body in self.bodies:
            if body.final_feature_id not in ids["feature"]:
                errors.append(f"body {body.id} references missing final feature")
        if self.assembly is not None:
            errors.extend(self._validate_assembly(ids))
        if not self.configurations:
            errors.append("document has no configuration")
        if (
            not self.feature_timeline
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
        groups = {
            "component definition": assembly.definitions,
            "component instance": assembly.instances,
            "component document": assembly.documents,
            "mate entity": assembly.mate_entities,
            "mate": assembly.mates,
            "mate group": assembly.mate_groups,
        }
        for label, items in groups.items():
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
                    ids["selection"]
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
                    ids["parameter"]
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
