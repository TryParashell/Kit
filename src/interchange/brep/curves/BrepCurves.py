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
from interchange.core.ModelBase import ModelBase, ModelDataMut
from interchange.records.RecordProvenance import Provenance
from interchange.geometry.models.VectorSpace import SpaceVector


# runtime construction can bypass annotations so topology identities need one checked boundary
def ValidateBrepId(SourceValue: object) -> None:
    if not isinstance(SourceValue, str):
        raise TypeError("B-rep entity id must be a string")


# shared topology identity avoids duplicated provenance fields across curve families
@ModelDataMut(
    FieldOverrides={
        "provenance": MakeDataField(default=None, kw_only=True),
        "attributes": MakeDataField(default_factory=FreezeMapping, kw_only=True),
    }
)
class BrepEntity(ModelBase):
    id: str
    provenance: Provenance | None
    attributes: TypeMap[str, object]

    @property
    def EntityId(self) -> str:
        return self.id

    @property
    def Provenance(self) -> Provenance | None:
        return self.provenance

    @property
    def Attributes(self) -> TypeMap[str, object]:
        return self.attributes


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

    @property
    def Origin(self) -> SpaceVector:
        return self.origin

    @property
    def Direction(self) -> SpaceVector:
        return self.direction


# circle curves preserve exact spatial frames and radii across kernels
@ModelDataMut
class CircleCurve(BrepCurve):
    center: SpaceVector
    axis: SpaceVector
    reference_direction: SpaceVector
    radius: float

    @property
    def Center(self) -> SpaceVector:
        return self.center

    @property
    def AxisVector(self) -> SpaceVector:
        return self.axis

    @property
    def RefDirection(self) -> SpaceVector:
        return self.reference_direction

    @property
    def Radius(self) -> float:
        return self.radius


# ellipse curves preserve exact spatial frames and both principal radii
@ModelDataMut
class EllipseCurve(BrepCurve):
    center: SpaceVector
    axis: SpaceVector
    reference_direction: SpaceVector
    major_radius: float
    minor_radius: float

    @property
    def Center(self) -> SpaceVector:
        return self.center

    @property
    def AxisVector(self) -> SpaceVector:
        return self.axis

    @property
    def RefDirection(self) -> SpaceVector:
        return self.reference_direction

    @property
    def MajorRadius(self) -> float:
        return self.major_radius

    @property
    def MinorRadius(self) -> float:
        return self.minor_radius


# spline curves retain full basis data needed for exact reconstruction
@ModelDataMut
class NurbsCurve(BrepCurve):
    degree: int
    control_points: tuple[SpaceVector, ...]
    knots: tuple[float, ...]
    multiplicities: tuple[int, ...]
    weights: tuple[float, ...] = ()
    periodic: bool = False

    @property
    def Degree(self) -> int:
        return self.degree

    @property
    def ControlPoints(self) -> tuple[SpaceVector, ...]:
        return self.control_points

    @property
    def KnotValues(self) -> tuple[float, ...]:
        return self.knots

    @property
    def Multiplicities(self) -> tuple[int, ...]:
        return self.multiplicities

    @property
    def Weights(self) -> tuple[float, ...]:
        return self.weights

    @property
    def IsPeriodic(self) -> bool:
        return self.periodic


# intersection curves preserve supporting surfaces and sampled verification evidence
@ModelDataMut
class IntersectCurve(BrepCurve):
    first_surface_id: str
    second_surface_id: str
    samples: tuple[SpaceVector, ...] = ()
    tolerance: float = 0.0

    @property
    def FirstSurfaceId(self) -> str:
        return self.first_surface_id

    @property
    def SecondSurfaceId(self) -> str:
        return self.second_surface_id

    @property
    def Samples(self) -> tuple[SpaceVector, ...]:
        return self.samples

    @property
    def Tolerance(self) -> float:
        return self.tolerance


# native curves retain unsupported kernel data without claiming portable semantics
@ModelDataMut
class NativeCurve(BrepCurve):
    format_id: str
    entity_type: str
    data: TypeMap[str, object] = MakeDataField(default_factory=FreezeMapping)

    @property
    def FormatId(self) -> str:
        return self.format_id

    @property
    def EntityType(self) -> str:
        return self.entity_type

    @property
    def PayloadData(self) -> TypeMap[str, object]:
        return self.data
