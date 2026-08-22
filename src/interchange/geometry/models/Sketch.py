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

    @property
    def EntityId(self) -> str:
        return self.id

    @property
    def EntityKind(self) -> GeometryKind | str:
        return self.kind

    @property
    def Geometry(self) -> KGeometryTypes:
        return self.geometry

    @property
    def IsConstruction(self) -> bool:
        return self.construction

    @property
    def IsFixed(self) -> bool:
        return self.fixed

    @property
    def Provenance(self) -> Provenance | None:
        return self.provenance

    @property
    def Attributes(self) -> TypeMap[str, object]:
        return self.attributes


# constraint references preserve the participating subelement of each entity
@ModelDataMut
class ConstraintRef(ModelBase):
    entity_id: str
    point: str = ""

    @property
    def EntityId(self) -> str:
        return self.entity_id

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

    @property
    def EntityId(self) -> str:
        return self.id

    @property
    def EntityKind(self) -> str:
        return self.kind

    @property
    def References(self) -> tuple[ConstraintRef, ...]:
        return self.references

    @property
    def ParameterId(self) -> str | None:
        return self.parameter_id

    @property
    def IsDriving(self) -> bool:
        return self.driving

    @property
    def IsSuppressed(self) -> bool:
        return self.suppressed

    @property
    def Provenance(self) -> Provenance | None:
        return self.provenance

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

    @property
    def EntityId(self) -> str:
        return self.id

    @property
    def EntityName(self) -> str:
        return self.name

    @property
    def SupportPlaneId(self) -> str:
        return self.support_plane_id

    @property
    def Entities(self) -> tuple[SketchEntity, ...]:
        return self.entities

    @property
    def Constraints(self) -> tuple[SketchRelation, ...]:
        return self.constraints

    @property
    def ParameterIds(self) -> tuple[str, ...]:
        return self.parameter_ids

    @property
    def ClosedProfileEntityIds(self) -> tuple[tuple[str, ...], ...]:
        return self.closed_profile_entity_ids

    @property
    def IsSuppressed(self) -> bool:
        return self.suppressed

    @property
    def Provenance(self) -> Provenance | None:
        return self.provenance

    @property
    def Attributes(self) -> TypeMap[str, object]:
        return self.attributes
