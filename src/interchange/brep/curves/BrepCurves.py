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
    DefaultMap={"Provenance": None},
    FactoryMap={"Attributes": FreezeMapping},
    KeywordOnly=frozenset({"Provenance", "Attributes"}),
)
class BrepEntity(ModelBase):
    EntityId: str
    Provenance: Provenance | None
    Attributes: TypeMap[str, object]
    if TYPE_CHECKING:
        id: ClassVar[str]
        attributes: ClassVar[TypeMap[str, object]]


# curve identity checks reject malformed records before topology validation
@ModelDataMut
class BrepCurve(BrepEntity):

    # invalid identifiers must fail before curves enter topology collections
    def __post_init__(self) -> None:
        ValidateBrepId(self.EntityId)


# line curves retain exact origin and direction without sampled approximation
@ModelDataMut
class LineCurve(BrepCurve):
    Origin: SpaceVector
    Direction: SpaceVector
    if TYPE_CHECKING:
        origin: ClassVar[SpaceVector]
        direction: ClassVar[SpaceVector]


# circle curves preserve exact spatial frames and radii across kernels
@ModelDataMut
class CircleCurve(BrepCurve):
    Center: SpaceVector
    AxisVector: SpaceVector
    RefDirection: SpaceVector
    Radius: float
    if TYPE_CHECKING:
        center: ClassVar[SpaceVector]
        axis: ClassVar[SpaceVector]
        reference_direction: ClassVar[SpaceVector]
        radius: ClassVar[float]


# ellipse curves preserve exact spatial frames and both principal radii
@ModelDataMut
class EllipseCurve(BrepCurve):
    Center: SpaceVector
    AxisVector: SpaceVector
    RefDirection: SpaceVector
    MajorRadius: float
    MinorRadius: float
    if TYPE_CHECKING:
        center: ClassVar[SpaceVector]
        axis: ClassVar[SpaceVector]
        reference_direction: ClassVar[SpaceVector]
        major_radius: ClassVar[float]
        minor_radius: ClassVar[float]


# spline curves retain full basis data needed for exact reconstruction
@ModelDataMut(DefaultMap={"Weights": (), "IsPeriodic": False})
class NurbsCurve(BrepCurve):
    Degree: int
    ControlPoints: tuple[SpaceVector, ...]
    KnotValues: tuple[float, ...]
    Multiplicities: tuple[int, ...]
    Weights: tuple[float, ...]
    IsPeriodic: bool
    if TYPE_CHECKING:
        degree: ClassVar[int]
        control_points: ClassVar[tuple[SpaceVector, ...]]
        knots: ClassVar[tuple[float, ...]]
        multiplicities: ClassVar[tuple[int, ...]]
        weights: ClassVar[tuple[float, ...]]
        periodic: ClassVar[bool]


# intersection curves preserve supporting surfaces and sampled verification evidence
@ModelDataMut(DefaultMap={"Samples": (), "Tolerance": 0.0})
class IntersectCurve(BrepCurve):
    FirstSurfaceId: str
    SecondSurfaceId: str
    Samples: tuple[SpaceVector, ...]
    Tolerance: float
    if TYPE_CHECKING:
        first_surface_id: ClassVar[str]
        second_surface_id: ClassVar[str]
        samples: ClassVar[tuple[SpaceVector, ...]]
        tolerance: ClassVar[float]


# native curves retain unsupported kernel data without claiming portable semantics
@ModelDataMut(FactoryMap={"PayloadData": FreezeMapping})
class NativeCurve(BrepCurve):
    FormatId: str
    EntityType: str
    PayloadData: TypeMap[str, object]
    if TYPE_CHECKING:
        format_id: ClassVar[str]
        entity_type: ClassVar[str]
        payload: ClassVar[TypeMap[str, object]]
