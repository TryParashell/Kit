# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from typing import Any as AnyValue
from typing import Mapping as TypeMap

from .common import FreezeMapping
from .enum_geometry import GeometryKind
from .geometry_types import KGeometryTypes
from .model_base import ModelBase, ModelDataMut
from .record_provenance import Provenance


# sketch entities pair semantic kinds with exact geometry and source state
@ModelDataMut(
    DefaultMap={"IsConstruction": False, "IsFixed": False, "Provenance": None},
    FactoryMap={"Attributes": FreezeMapping},
)
class SketchEntity(ModelBase):
    EntityId: str
    EntityKind: GeometryKind | str
    Geometry: KGeometryTypes
    IsConstruction: bool
    IsFixed: bool
    Provenance: Provenance | None
    Attributes: TypeMap[str, AnyValue]


# constraint references preserve the participating subelement of each entity
@ModelDataMut(DefaultMap={"PointName": ""})
class ConstraintRef(ModelBase):
    EntityId: str
    PointName: str


# sketch relations retain solver intent and parameter bindings across formats
@ModelDataMut(
    DefaultMap={
        "ParameterId": None,
        "IsDriving": True,
        "IsSuppressed": False,
        "Provenance": None,
    },
    FactoryMap={"Attributes": FreezeMapping},
)
class SketchRelation(ModelBase):
    EntityId: str
    EntityKind: str
    References: tuple[ConstraintRef, ...]
    ParameterId: str | None
    IsDriving: bool
    IsSuppressed: bool
    Provenance: Provenance | None
    Attributes: TypeMap[str, AnyValue]


# sketches group geometry relations and profile identity into editable inputs
@ModelDataMut(
    DefaultMap={
        "Constraints": (),
        "ParameterIds": (),
        "ClosedProfileEntityIds": (),
        "IsSuppressed": False,
        "Provenance": None,
    },
    FactoryMap={"Attributes": FreezeMapping},
)
class Sketch(ModelBase):
    EntityId: str
    EntityName: str
    SupportPlaneId: str
    Entities: tuple[SketchEntity, ...]
    Constraints: tuple[SketchRelation, ...]
    ParameterIds: tuple[str, ...]
    ClosedProfileEntityIds: tuple[tuple[str, ...], ...]
    IsSuppressed: bool
    Provenance: Provenance | None
    Attributes: TypeMap[str, AnyValue]
