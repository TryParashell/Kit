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

from interchange.brep.curves.BrepCurves import BrepEntity, ValidateBrepId
from interchange.core.Common import FreezeMapping
from interchange.core.ModelBase import ModelDataMut
from interchange.geometry.models.VectorSpace import SpaceVector


# surface identity checks reject malformed records before topology validation
@ModelDataMut
class BrepSurface(BrepEntity):

    # invalid identifiers must fail before surfaces enter topology collections
    def __post_init__(self) -> None:
        ValidateBrepId(self.id)


# planes retain exact spatial frames for analytic reconstruction
@ModelDataMut
class PlaneSurface(BrepSurface):
    origin: SpaceVector
    normal: SpaceVector
    reference_direction: SpaceVector

    @property
    def Origin(self) -> SpaceVector:
        return self.origin

    @property
    def Normal(self) -> SpaceVector:
        return self.normal

    @property
    def RefDirection(self) -> SpaceVector:
        return self.reference_direction


# cylinders retain exact axes reference directions and radii
@ModelDataMut
class CylinderSurface(BrepSurface):
    origin: SpaceVector
    axis: SpaceVector
    reference_direction: SpaceVector
    radius: float

    @property
    def Origin(self) -> SpaceVector:
        return self.origin

    @property
    def AxisVector(self) -> SpaceVector:
        return self.axis

    @property
    def RefDirection(self) -> SpaceVector:
        return self.reference_direction

    @property
    def Radius(self) -> float:
        return self.radius


# cones retain exact axes base radii and half angles
@ModelDataMut
class ConeSurface(BrepSurface):
    origin: SpaceVector
    axis: SpaceVector
    reference_direction: SpaceVector
    radius: float
    half_angle: float

    @property
    def Origin(self) -> SpaceVector:
        return self.origin

    @property
    def AxisVector(self) -> SpaceVector:
        return self.axis

    @property
    def RefDirection(self) -> SpaceVector:
        return self.reference_direction

    @property
    def Radius(self) -> float:
        return self.radius

    @property
    def HalfAngle(self) -> float:
        return self.half_angle


# spheres retain exact centers orientation frames and radii
@ModelDataMut
class SphereSurface(BrepSurface):
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


# tori retain exact centers orientation frames and both radii
@ModelDataMut
class TorusSurface(BrepSurface):
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


# spline surfaces retain complete tensor basis data for exact reconstruction
@ModelDataMut
class NurbsSurface(BrepSurface):
    degree_u: int
    degree_v: int
    control_points: tuple[tuple[SpaceVector, ...], ...]
    knots_u: tuple[float, ...]
    knots_v: tuple[float, ...]
    multiplicities_u: tuple[int, ...]
    multiplicities_v: tuple[int, ...]
    weights: tuple[tuple[float, ...], ...] = ()
    periodic_u: bool = False
    periodic_v: bool = False

    @property
    def DegreeU(self) -> int:
        return self.degree_u

    @property
    def DegreeV(self) -> int:
        return self.degree_v

    @property
    def ControlPoints(self) -> tuple[tuple[SpaceVector, ...], ...]:
        return self.control_points

    @property
    def KnotValuesU(self) -> tuple[float, ...]:
        return self.knots_u

    @property
    def KnotValuesV(self) -> tuple[float, ...]:
        return self.knots_v

    @property
    def MultiplicitiesU(self) -> tuple[int, ...]:
        return self.multiplicities_u

    @property
    def MultiplicitiesV(self) -> tuple[int, ...]:
        return self.multiplicities_v

    @property
    def Weights(self) -> tuple[tuple[float, ...], ...]:
        return self.weights

    @property
    def IsPeriodicU(self) -> bool:
        return self.periodic_u

    @property
    def IsPeriodicV(self) -> bool:
        return self.periodic_v


# offset surfaces preserve analytic relationships instead of flattening to splines
@ModelDataMut
class OffsetSurface(BrepSurface):
    base_surface_id: str
    distance: float

    @property
    def BaseSurfaceId(self) -> str:
        return self.base_surface_id

    @property
    def Distance(self) -> float:
        return self.distance


# native surfaces preserve unsupported kernel data without false portable semantics
@ModelDataMut
class NativeSurface(BrepSurface):
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
