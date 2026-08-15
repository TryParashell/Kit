# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar
from typing import Mapping as TypeMap

from interchange.core.Common import FreezeMapping
from interchange.core.ModelBase import ModelBase, ModelDataMut
from interchange.records.RecordProvenance import Provenance
from interchange.geometry.models.VectorSpace import SpaceVector


# runtime construction can bypass annotations so topology identities need one checked boundary
def ValidateBrepId(SourceValue: object) -> None:
    if not isinstance(SourceValue, str):
        raise TypeError("B-rep entity id must be a string")


# shared topology identity avoids duplicated provenance fields across curve families
@ModelDataMut(
    DefaultMap={"provenance": None},
    FactoryMap={"attributes": FreezeMapping},
    KeywordOnly=frozenset({"provenance", "attributes"}),
)
class BrepEntity(ModelBase):
    id: str
    provenance: Provenance | None
    attributes: TypeMap[str, object]
    if TYPE_CHECKING:
        EntityId: ClassVar[str]
        Provenance: ClassVar[Provenance | None]
        Attributes: ClassVar[TypeMap[str, object]]


# curve identity checks reject malformed records before topology validation
@ModelDataMut
class BrepCurve(BrepEntity):

    # invalid identifiers must fail before curves enter topology collections
    def __post_init__(self) -> None:
        ValidateBrepId(self.id)


# line curves retain exact origin and direction without sampled approximation
@ModelDataMut
class LineCurve(BrepCurve):
    origin: SpaceVector
    direction: SpaceVector
    if TYPE_CHECKING:
        Origin: ClassVar[SpaceVector]
        Direction: ClassVar[SpaceVector]


# circle curves preserve exact spatial frames and radii across kernels
@ModelDataMut
class CircleCurve(BrepCurve):
    center: SpaceVector
    axis: SpaceVector
    reference_direction: SpaceVector
    radius: float
    if TYPE_CHECKING:
        Center: ClassVar[SpaceVector]
        AxisVector: ClassVar[SpaceVector]
        RefDirection: ClassVar[SpaceVector]
        Radius: ClassVar[float]


# ellipse curves preserve exact spatial frames and both principal radii
@ModelDataMut
class EllipseCurve(BrepCurve):
    center: SpaceVector
    axis: SpaceVector
    reference_direction: SpaceVector
    major_radius: float
    minor_radius: float
    if TYPE_CHECKING:
        Center: ClassVar[SpaceVector]
        AxisVector: ClassVar[SpaceVector]
        RefDirection: ClassVar[SpaceVector]
        MajorRadius: ClassVar[float]
        MinorRadius: ClassVar[float]


# spline curves retain full basis data needed for exact reconstruction
@ModelDataMut(DefaultMap={"weights": (), "periodic": False})
class NurbsCurve(BrepCurve):
    degree: int
    control_points: tuple[SpaceVector, ...]
    knots: tuple[float, ...]
    multiplicities: tuple[int, ...]
    weights: tuple[float, ...]
    periodic: bool
    if TYPE_CHECKING:
        Degree: ClassVar[int]
        ControlPoints: ClassVar[tuple[SpaceVector, ...]]
        KnotValues: ClassVar[tuple[float, ...]]
        Multiplicities: ClassVar[tuple[int, ...]]
        Weights: ClassVar[tuple[float, ...]]
        IsPeriodic: ClassVar[bool]


# intersection curves preserve supporting surfaces and sampled verification evidence
@ModelDataMut(DefaultMap={"samples": (), "tolerance": 0.0})
class IntersectCurve(BrepCurve):
    first_surface_id: str
    second_surface_id: str
    samples: tuple[SpaceVector, ...]
    tolerance: float
    if TYPE_CHECKING:
        FirstSurfaceId: ClassVar[str]
        SecondSurfaceId: ClassVar[str]
        Samples: ClassVar[tuple[SpaceVector, ...]]
        Tolerance: ClassVar[float]


# native curves retain unsupported kernel data without claiming portable semantics
@ModelDataMut(FactoryMap={"data": FreezeMapping})
class NativeCurve(BrepCurve):
    format_id: str
    entity_type: str
    data: TypeMap[str, object]
    if TYPE_CHECKING:
        FormatId: ClassVar[str]
        EntityType: ClassVar[str]
        PayloadData: ClassVar[TypeMap[str, object]]
