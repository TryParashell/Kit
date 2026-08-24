# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from dataclasses import dataclass as MakeDataClass
from dataclasses import field as MakeDataField
from typing import Mapping as TypeMap
from typing import cast as CastValue

from interchange.assembly.ComponentDefinition import ComponentDef
from interchange.assembly.ComponentInstance import ComponentInst
from interchange.assembly.GraphView import GraphView
from interchange.assembly.MateConstraint import MateConstraint
from interchange.assembly.MateEntity import MateEntity
from interchange.assembly.MateGroup import MateGroup
from interchange.brep.topology.BrepModel import BrepModel
from interchange.core.Common import FreezeMapping
from interchange.core.ModelBase import ModelBase, ModelDataMut
from interchange.core.ModelExtras import ModelExtras
from interchange.document.behavior.DocumentBehavior import DocumentApi
from interchange.document.models.DocumentRoot import DocumentRoot
from interchange.enums.EnumDocument import Capability
from interchange.enums.EnumUnits import UnitSystem
from interchange.features.FeatureBody import DesignBody
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.Selection import Selection
from interchange.geometry.models.Sketch import Sketch
from interchange.geometry.models.SupportPlane import SupportPlane
from interchange.mesh.SurfaceMesh import SurfaceMesh
from interchange.payloads.PayloadRecord import BrepPayload
from interchange.records.RecordConfig import Configuration
from interchange.records.RecordDiagnostic import Diagnostic
from interchange.records.RecordParameter import Parameter
from interchange.records.RecordSource import CadSource


# portable cad exchange needs one immutable root connecting every neutral model domain
@MakeDataClass(frozen=True, slots=True)
class CadDocument(DocumentRoot, DocumentApi, ModelBase):
    source: CadSource
    configurations: tuple[Configuration, ...]
    parameters: tuple[Parameter, ...]
    support_planes: tuple[SupportPlane, ...]
    sketches: tuple[Sketch, ...]
    selections: tuple[Selection, ...]
    feature_timeline: tuple[FeatureStep, ...]
    bodies: tuple[DesignBody, ...]
    meshes: tuple[SurfaceMesh, ...] = ()
    brep_payloads: tuple[BrepPayload, ...] = ()
    diagnostics: tuple[Diagnostic, ...] = ()
    capabilities: frozenset[Capability] = frozenset()
    metadata: TypeMap[str, object] = MakeDataField(default_factory=FreezeMapping)
    units: UnitSystem = UnitSystem.KMillimeter
    schema_version: str = "1.0"
    assembly: AssemblyData | None = None
    brep: BrepModel | None = None

    # pascal compatibility keeps existing adapters typed during lowercase contract migration
    @property
    def Source(self) -> CadSource:
        return self.source

    # pascal compatibility keeps existing adapters typed during lowercase contract migration
    @property
    def Configurations(self) -> tuple[Configuration, ...]:
        return self.configurations

    # pascal compatibility keeps existing adapters typed during lowercase contract migration
    @property
    def Parameters(self) -> tuple[Parameter, ...]:
        return self.parameters

    # pascal compatibility keeps existing adapters typed during lowercase contract migration
    @property
    def SupportPlanes(self) -> tuple[SupportPlane, ...]:
        return self.support_planes

    # pascal compatibility keeps existing adapters typed during lowercase contract migration
    @property
    def Sketches(self) -> tuple[Sketch, ...]:
        return self.sketches

    # pascal compatibility keeps existing adapters typed during lowercase contract migration
    @property
    def Selections(self) -> tuple[Selection, ...]:
        return self.selections

    # pascal compatibility keeps existing adapters typed during lowercase contract migration
    @property
    def FeatureTimeline(self) -> tuple[FeatureStep, ...]:
        return self.feature_timeline

    # pascal compatibility keeps existing adapters typed during lowercase contract migration
    @property
    def Bodies(self) -> tuple[DesignBody, ...]:
        return self.bodies

    # pascal compatibility keeps existing adapters typed during lowercase contract migration
    @property
    def Meshes(self) -> tuple[SurfaceMesh, ...]:
        return self.meshes

    # pascal compatibility keeps existing adapters typed during lowercase contract migration
    @property
    def BrepPayloads(self) -> tuple[BrepPayload, ...]:
        return self.brep_payloads

    # pascal compatibility keeps existing adapters typed during lowercase contract migration
    @property
    def Diagnostics(self) -> tuple[Diagnostic, ...]:
        return self.diagnostics

    # pascal compatibility keeps existing adapters typed during lowercase contract migration
    @property
    def Capabilities(self) -> frozenset[Capability]:
        return self.capabilities

    # pascal compatibility keeps existing adapters typed during lowercase contract migration
    @property
    def Metadata(self) -> TypeMap[str, object]:
        return self.metadata

    # pascal compatibility keeps existing adapters typed during lowercase contract migration
    @property
    def Units(self) -> UnitSystem:
        return self.units

    # pascal compatibility keeps existing adapters typed during lowercase contract migration
    @property
    def SchemaVersion(self) -> str:
        return self.schema_version

    # pascal compatibility keeps existing adapters typed during lowercase contract migration
    @property
    def Assembly(self) -> AssemblyData | None:
        return self.assembly

    # pascal compatibility keeps existing adapters typed during lowercase contract migration
    @property
    def BrepModel(self) -> BrepModel | None:
        return self.brep


# component documents embed linked portable documents without weakening graph typing
@ModelDataMut
class ComponentDoc(ModelBase):
    id: str
    document: CadDocument

    # stable identity lets records reference each other without holding full objects
    @property
    def EntityId(self) -> str:
        return self.id

    # underlying document access keeps assembly views decoupled from storage internals
    @property
    def Document(self) -> CadDocument:
        return self.document


# assembly definition lookups stay separable because graph views compose without owning storage
class DefLookupView(GraphView):
    locals()["__slots__"] = ()

    # definition lookup gives callers one consistent missing identifier failure mode
    def GetDefinition(self, EntityId: str) -> ComponentDef:
        StoredDefinitions = CastValue(
            tuple[ComponentDef, ...],
            getattr(self, "definitions"),
        )
        for DefinitionValue in StoredDefinitions:
            if DefinitionValue.id == EntityId:
                return DefinitionValue
        raise KeyError(f"unknown component definition id {EntityId!r}")

    # pascal lookup keeps one canonical spelling because compatibility wrappers need twins
    def Definition(self, EntityId: str) -> ComponentDef:
        return self.GetDefinition(EntityId)

    # lowercase lookup stays concrete because static consumers cannot observe runtime aliases
    def definition(self, entity_id: str) -> ComponentDef:
        return self.GetDefinition(entity_id)

    # pascal child ordering keeps one canonical spelling because compatibility wrappers need twins
    def Children(self, DefinitionId: str) -> tuple[ComponentInst, ...]:
        return self.GetChildren(DefinitionId)

    # lowercase child ordering stays concrete because static consumers cannot observe runtime aliases
    def children(self, definition_id: str) -> tuple[ComponentInst, ...]:
        return self.GetChildren(definition_id)


# assembly document lookups stay separable because linked records resolve without storage coupling
class DocLookupView:
    locals()["__slots__"] = ()

    # document list keeps external references inspectable without reopening files
    @property
    def Documents(self) -> "tuple[ComponentDoc, ...]":
        return CastValue("tuple[ComponentDoc, ...]", getattr(self, "documents"))

    # embedded document lookup avoids exposing storage details to assembly consumers
    def GetDocument(self, EntityId: str) -> CadDocument:
        StoredDocuments = CastValue(
            tuple[ComponentDoc, ...],
            getattr(self, "documents"),
        )
        for DocumentValue in StoredDocuments:
            if DocumentValue.id == EntityId:
                return DocumentValue.document
        raise KeyError(f"unknown component document id {EntityId!r}")

    # pascal lookup keeps one canonical spelling because compatibility wrappers need twins
    def Document(self, EntityId: str) -> CadDocument:
        return self.GetDocument(EntityId)

    # lowercase lookup stays concrete because linked document consumers need its exact return type
    def document(self, entity_id: str) -> CadDocument:
        return self.GetDocument(entity_id)


# assembly data composes occurrences documents and mates into one portable graph
@ModelDataMut
class AssemblyData(DefLookupView, DocLookupView, ModelExtras, ModelBase):
    root_definition_id: str
    definitions: tuple[ComponentDef, ...]
    instances: tuple[ComponentInst, ...]
    documents: tuple[ComponentDoc, ...] = ()
    mate_entities: tuple[MateEntity, ...] = ()
    mates: tuple[MateConstraint, ...] = ()
    mate_groups: tuple[MateGroup, ...] = ()
    attributes: TypeMap[str, object] = MakeDataField(default_factory=FreezeMapping)
