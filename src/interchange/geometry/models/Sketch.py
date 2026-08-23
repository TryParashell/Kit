# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from dataclasses import field as MakeDataField
from typing import Mapping as TypeMap

from interchange.core.Common import FreezeMapping
from interchange.enums.EnumGeometry import GeometryKind
from interchange.geometry.models.GeometryTypes import KGeometryTypes
from interchange.core.ModelBase import ModelBase, ModelDataMut
from interchange.records.RecordProvenance import Provenance


# sketch entities pair semantic kinds with exact geometry and source state
@ModelDataMut
class SketchEntity(ModelBase):
    id: str
    kind: GeometryKind | str
    geometry: KGeometryTypes
    construction: bool = False
    fixed: bool = False
    provenance: Provenance | None = None
    attributes: TypeMap[str, object] = MakeDataField(default_factory=FreezeMapping)

     # stable identity lets records reference each other without holding full objects
    @property
    def EntityId(self) -> str:
        return self.id

     # kind tag lets consumers branch on semantics without importing concrete classes
    @property
    def EntityKind(self) -> GeometryKind | str:
        return self.kind

     # typed payload keeps every sketch element shape accessible uniformly
    @property
    def Geometry(self) -> KGeometryTypes:
        return self.geometry

     # construction flag hides helper curves from profile detection quietly
    @property
    def IsConstruction(self) -> bool:
        return self.construction

     # fixed lock protects user pinned geometry from solver drift
    @property
    def IsFixed(self) -> bool:
        return self.fixed

     # origin details stay optional so synthesized records can omit source facts safely
    @property
    def Provenance(self) -> Provenance | None:
        return self.provenance

     # open attribute bag preserves vendor extras that typed fields cannot express yet
    @property
    def Attributes(self) -> TypeMap[str, object]:
        return self.attributes


# constraint references preserve the participating subelement of each entity
@ModelDataMut
class ConstraintRef(ModelBase):
    entity_id: str
    point: str = ""

     # stable identity lets records reference each other without holding full objects
    @property
    def EntityId(self) -> str:
        return self.entity_id

     # named points let constraints reference vertices without indices drifting
    @property
    def PointName(self) -> str:
        return self.point


# sketch relations retain solver intent and parameter bindings across formats
@ModelDataMut
class SketchRelation(ModelBase):
    id: str
    kind: str
    references: tuple[ConstraintRef, ...]
    parameter_id: str | None = None
    driving: bool = True
    suppressed: bool = False
    provenance: Provenance | None = None
    attributes: TypeMap[str, object] = MakeDataField(default_factory=FreezeMapping)

     # stable identity lets records reference each other without holding full objects
    @property
    def EntityId(self) -> str:
        return self.id

     # kind tag lets consumers branch on semantics without importing concrete classes
    @property
    def EntityKind(self) -> str:
        return self.kind

     # reference list ties each relation to the entities it constrains
    @property
    def References(self) -> tuple[ConstraintRef, ...]:
        return self.references

     # optional parameter link makes dimensions editable through records
    @property
    def ParameterId(self) -> str | None:
        return self.parameter_id

     # driving flag splits real constraints from reference measurements
    @property
    def IsDriving(self) -> bool:
        return self.driving

     # suppression state keeps feature trees honest about what contributes geometry
    @property
    def IsSuppressed(self) -> bool:
        return self.suppressed

     # origin details stay optional so synthesized records can omit source facts safely
    @property
    def Provenance(self) -> Provenance | None:
        return self.provenance

     # open attribute bag preserves vendor extras that typed fields cannot express yet
    @property
    def Attributes(self) -> TypeMap[str, object]:
        return self.attributes


# sketches group geometry relations and profile identity into editable inputs
@ModelDataMut
class Sketch(ModelBase):
    id: str
    name: str
    support_plane_id: str
    entities: tuple[SketchEntity, ...]
    constraints: tuple[SketchRelation, ...] = ()
    parameter_ids: tuple[str, ...] = ()
    closed_profile_entity_ids: tuple[tuple[str, ...], ...] = ()
    suppressed: bool = False
    provenance: Provenance | None = None
    attributes: TypeMap[str, object] = MakeDataField(default_factory=FreezeMapping)

     # stable identity lets records reference each other without holding full objects
    @property
    def EntityId(self) -> str:
        return self.id

     # human readable label keeps diagnostics and diffs meaningful for reviewers
    @property
    def EntityName(self) -> str:
        return self.name

     # plane anchor locates the sketch in space without embedding transforms
    @property
    def SupportPlaneId(self) -> str:
        return self.support_plane_id

     # element list keeps sketch contents enumerable in draw order
    @property
    def Entities(self) -> tuple[SketchEntity, ...]:
        return self.entities

     # relation list keeps sketch intent inspectable without solving
    @property
    def Constraints(self) -> tuple[SketchRelation, ...]:
        return self.constraints

     # parameter links keep mate values driven by configurable expressions
    @property
    def ParameterIds(self) -> tuple[str, ...]:
        return self.parameter_ids

     # loop groups identify closed profiles so features can consume sketches directly
    @property
    def ClosedProfileEntityIds(self) -> tuple[tuple[str, ...], ...]:
        return self.closed_profile_entity_ids

     # suppression state keeps feature trees honest about what contributes geometry
    @property
    def IsSuppressed(self) -> bool:
        return self.suppressed

     # origin details stay optional so synthesized records can omit source facts safely
    @property
    def Provenance(self) -> Provenance | None:
        return self.provenance

     # open attribute bag preserves vendor extras that typed fields cannot express yet
    @property
    def Attributes(self) -> TypeMap[str, object]:
        return self.attributes
