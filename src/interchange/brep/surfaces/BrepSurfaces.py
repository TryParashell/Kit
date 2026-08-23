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
from interchange.records.RecordProvenance import Provenance
from interchange.core.Common import FreezeMapping
from interchange.core.ModelBase import ModelDataMut
from interchange.geometry.models.VectorSpace import SpaceVector


# surface identity checks reject malformed records before topology validation
@ModelDataMut
class BrepSurface(BrepEntity):
    id: str

    # invalid identifiers must fail before surfaces enter topology collections
    def __post_init__(self) -> None:
        ValidateBrepId(self.id)


# planes retain exact spatial frames for analytic reconstruction
@ModelDataMut
class PlaneSurface(BrepSurface):
    id: str
    origin: SpaceVector
    normal: SpaceVector
    reference_direction: SpaceVector
    provenance: Provenance | None = None
    attributes: TypeMap[str, object] = MakeDataField(default_factory=FreezeMapping)

     # anchor point keeps curve placement absolute without extra context
    @property
    def Origin(self) -> SpaceVector:
        return self.origin

     # surface normal keeps side semantics unambiguous during trimming operations
    @property
    def Normal(self) -> SpaceVector:
        return self.normal

     # reference direction fixes parametrization start so rotations stay reproducible
    @property
    def RefDirection(self) -> SpaceVector:
        return self.reference_direction


# cylinders retain exact axes reference directions and radii
@ModelDataMut
class CylinderSurface(BrepSurface):
    id: str
    origin: SpaceVector
    axis: SpaceVector
    reference_direction: SpaceVector
    radius: float
    provenance: Provenance | None = None
    attributes: TypeMap[str, object] = MakeDataField(default_factory=FreezeMapping)

     # anchor point keeps curve placement absolute without extra context
    @property
    def Origin(self) -> SpaceVector:
        return self.origin

     # axis direction keeps rotational geometry oriented consistently across formats
    @property
    def AxisVector(self) -> SpaceVector:
        return self.axis

     # reference direction fixes parametrization start so rotations stay reproducible
    @property
    def RefDirection(self) -> SpaceVector:
        return self.reference_direction

     # radius keeps circles arcs and cylinders sized without sampling geometry
    @property
    def Radius(self) -> float:
        return self.radius


# cones retain exact axes base radii and half angles
@ModelDataMut
class ConeSurface(BrepSurface):
    id: str
    origin: SpaceVector
    axis: SpaceVector
    reference_direction: SpaceVector
    radius: float
    half_angle: float
    provenance: Provenance | None = None
    attributes: TypeMap[str, object] = MakeDataField(default_factory=FreezeMapping)

     # anchor point keeps curve placement absolute without extra context
    @property
    def Origin(self) -> SpaceVector:
        return self.origin

     # axis direction keeps rotational geometry oriented consistently across formats
    @property
    def AxisVector(self) -> SpaceVector:
        return self.axis

     # reference direction fixes parametrization start so rotations stay reproducible
    @property
    def RefDirection(self) -> SpaceVector:
        return self.reference_direction

     # radius keeps circles arcs and cylinders sized without sampling geometry
    @property
    def Radius(self) -> float:
        return self.radius

     # half angle defines cone spread without trigonometry at read time
    @property
    def HalfAngle(self) -> float:
        return self.half_angle


# spheres retain exact centers orientation frames and radii
@ModelDataMut
class SphereSurface(BrepSurface):
    id: str
    center: SpaceVector
    axis: SpaceVector
    reference_direction: SpaceVector
    radius: float
    provenance: Provenance | None = None
    attributes: TypeMap[str, object] = MakeDataField(default_factory=FreezeMapping)

     # center point keeps circular geometry positioned without deriving it repeatedly
    @property
    def Center(self) -> SpaceVector:
        return self.center

     # axis direction keeps rotational geometry oriented consistently across formats
    @property
    def AxisVector(self) -> SpaceVector:
        return self.axis

     # reference direction fixes parametrization start so rotations stay reproducible
    @property
    def RefDirection(self) -> SpaceVector:
        return self.reference_direction

     # radius keeps circles arcs and cylinders sized without sampling geometry
    @property
    def Radius(self) -> float:
        return self.radius


# tori retain exact centers orientation frames and both radii
@ModelDataMut
class TorusSurface(BrepSurface):
    id: str
    center: SpaceVector
    axis: SpaceVector
    reference_direction: SpaceVector
    major_radius: float
    minor_radius: float
    provenance: Provenance | None = None
    attributes: TypeMap[str, object] = MakeDataField(default_factory=FreezeMapping)

     # center point keeps circular geometry positioned without deriving it repeatedly
    @property
    def Center(self) -> SpaceVector:
        return self.center

     # axis direction keeps rotational geometry oriented consistently across formats
    @property
    def AxisVector(self) -> SpaceVector:
        return self.axis

     # reference direction fixes parametrization start so rotations stay reproducible
    @property
    def RefDirection(self) -> SpaceVector:
        return self.reference_direction

     # major extent keeps ellipse sizing exact without control point inference
    @property
    def MajorRadius(self) -> float:
        return self.major_radius

     # minor extent completes ellipse shape so reconstruction never guesses
    @property
    def MinorRadius(self) -> float:
        return self.minor_radius


# spline surfaces retain complete tensor basis data for exact reconstruction
@ModelDataMut
class NurbsSurface(BrepSurface):
    id: str
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
    provenance: Provenance | None = None
    attributes: TypeMap[str, object] = MakeDataField(default_factory=FreezeMapping)

     # u degree controls surface smoothness along one parametric direction
    @property
    def DegreeU(self) -> int:
        return self.degree_u

     # v degree completes bidirectional smoothness control for reconstruction
    @property
    def DegreeV(self) -> int:
        return self.degree_v

     # hull points define spline shape so evaluation never needs vendor kernels
    @property
    def ControlPoints(self) -> tuple[tuple[SpaceVector, ...], ...]:
        return self.control_points

     # u knots define segment joins so surfaces evaluate identically everywhere
    @property
    def KnotValuesU(self) -> tuple[float, ...]:
        return self.knots_u

     # v knots define cross direction joins without vendor reevaluation
    @property
    def KnotValuesV(self) -> tuple[float, ...]:
        return self.knots_v

     # u multiplicities preserve continuity breaks across one parametric direction
    @property
    def MultiplicitiesU(self) -> tuple[int, ...]:
        return self.multiplicities_u

     # v multiplicities preserve continuity breaks across the other direction
    @property
    def MultiplicitiesV(self) -> tuple[int, ...]:
        return self.multiplicities_v

     # rational weights keep conic splines representable exactly rather than approximately
    @property
    def Weights(self) -> tuple[tuple[float, ...], ...]:
        return self.weights

     # u periodicity tells evaluators whether seam closure can be assumed
    @property
    def IsPeriodicU(self) -> bool:
        return self.periodic_u

     # v periodicity completes seam handling for closed surfaces
    @property
    def IsPeriodicV(self) -> bool:
        return self.periodic_v


# offset surfaces preserve analytic relationships instead of flattening to splines
@ModelDataMut
class OffsetSurface(BrepSurface):
    id: str
    base_surface_id: str
    distance: float
    provenance: Provenance | None = None
    attributes: TypeMap[str, object] = MakeDataField(default_factory=FreezeMapping)

     # base surface link keeps offset geometry dependent on its parent
    @property
    def BaseSurfaceId(self) -> str:
        return self.base_surface_id

     # offset distance keeps derived surfaces reproducible without measuring geometry
    @property
    def Distance(self) -> float:
        return self.distance


# native surfaces preserve unsupported kernel data without false portable semantics
@ModelDataMut
class NativeSurface(BrepSurface):
    id: str
    format_id: str
    entity_type: str
    data: TypeMap[str, object] = MakeDataField(default_factory=FreezeMapping)
    provenance: Provenance | None = None
    attributes: TypeMap[str, object] = MakeDataField(default_factory=FreezeMapping)

     # format id keeps payload interpretation tied to its producing dialect
    @property
    def FormatId(self) -> str:
        return self.format_id

     # native type string preserves vendor vocabulary that enums cannot fully cover
    @property
    def EntityType(self) -> str:
        return self.entity_type

     # raw bytes keep vendor specifics recoverable even when schema parsing fails
    @property
    def PayloadData(self) -> TypeMap[str, object]:
        return self.data
