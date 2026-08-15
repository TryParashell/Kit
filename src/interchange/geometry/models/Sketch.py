# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from typing import ClassVar, TYPE_CHECKING
from typing import Mapping as TypeMap

from interchange.core.Common import FreezeMapping
from interchange.enums.EnumGeometry import GeometryKind
from interchange.geometry.models.GeometryTypes import KGeometryTypes
from interchange.core.ModelBase import ModelBase, ModelDataMut
from interchange.records.RecordProvenance import Provenance


# sketch entities pair semantic kinds with exact geometry and source state
@ModelDataMut(
    DefaultMap={"construction": False, "fixed": False, "provenance": None},
    FactoryMap={"attributes": FreezeMapping},
)
class SketchEntity(ModelBase):
    id: str
    kind: GeometryKind | str
    geometry: KGeometryTypes
    construction: bool
    fixed: bool
    provenance: Provenance | None
    attributes: TypeMap[str, object]
    if TYPE_CHECKING:
        EntityId: ClassVar[str]
        EntityKind: ClassVar[GeometryKind | str]
        Geometry: ClassVar[KGeometryTypes]
        IsConstruction: ClassVar[bool]
        IsFixed: ClassVar[bool]
        Provenance: ClassVar[Provenance | None]
        Attributes: ClassVar[TypeMap[str, object]]


# constraint references preserve the participating subelement of each entity
@ModelDataMut(DefaultMap={"point": ""})
class ConstraintRef(ModelBase):
    entity_id: str
    point: str
    if TYPE_CHECKING:
        EntityId: ClassVar[str]
        PointName: ClassVar[str]


# sketch relations retain solver intent and parameter bindings across formats
@ModelDataMut(
    DefaultMap={
        "parameter_id": None,
        "driving": True,
        "suppressed": False,
        "provenance": None,
    },
    FactoryMap={"attributes": FreezeMapping},
)
class SketchRelation(ModelBase):
    id: str
    kind: str
    references: tuple[ConstraintRef, ...]
    parameter_id: str | None
    driving: bool
    suppressed: bool
    provenance: Provenance | None
    attributes: TypeMap[str, object]
    if TYPE_CHECKING:
        EntityId: ClassVar[str]
        EntityKind: ClassVar[str]
        References: ClassVar[tuple[ConstraintRef, ...]]
        ParameterId: ClassVar[str | None]
        IsDriving: ClassVar[bool]
        IsSuppressed: ClassVar[bool]
        Provenance: ClassVar[Provenance | None]
        Attributes: ClassVar[TypeMap[str, object]]


# sketches group geometry relations and profile identity into editable inputs
@ModelDataMut(
    DefaultMap={
        "constraints": (),
        "parameter_ids": (),
        "closed_profile_entity_ids": (),
        "suppressed": False,
        "provenance": None,
    },
    FactoryMap={"attributes": FreezeMapping},
)
class Sketch(ModelBase):
    id: str
    name: str
    support_plane_id: str
    entities: tuple[SketchEntity, ...]
    constraints: tuple[SketchRelation, ...]
    parameter_ids: tuple[str, ...]
    closed_profile_entity_ids: tuple[tuple[str, ...], ...]
    suppressed: bool
    provenance: Provenance | None
    attributes: TypeMap[str, object]
    if TYPE_CHECKING:
        EntityId: ClassVar[str]
        EntityName: ClassVar[str]
        SupportPlaneId: ClassVar[str]
        Entities: ClassVar[tuple[SketchEntity, ...]]
        Constraints: ClassVar[tuple[SketchRelation, ...]]
        ParameterIds: ClassVar[tuple[str, ...]]
        ClosedProfileEntityIds: ClassVar[tuple[tuple[str, ...], ...]]
        IsSuppressed: ClassVar[bool]
        Provenance: ClassVar[Provenance | None]
        Attributes: ClassVar[TypeMap[str, object]]
