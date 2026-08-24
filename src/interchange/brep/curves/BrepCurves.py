# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from dataclasses import field as MakeDataField
from typing import cast as CastValue
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
class BrepEntity(ModelBase):

    # storage contracts stay structural so leaf dataclasses own every field declaration
    @property
    def EntityId(self) -> str:
        return CastValue(str, object.__getattribute__(self, "id"))

    # origin details stay optional so synthesized records can omit source facts safely
    @property
    def Provenance(self) -> Provenance | None:
        return CastValue(Provenance | None, object.__getattribute__(self, "provenance"))

    # open attribute bag preserves vendor extras that typed fields cannot express yet
    @property
    def Attributes(self) -> TypeMap[str, object]:
        return CastValue(
            TypeMap[str, object], object.__getattribute__(self, "attributes")
        )


# curve identity checks reject malformed records before topology validation
class BrepCurve(BrepEntity):
    id: str

    # invalid identifiers must fail before curves enter topology collections
    def __post_init__(self) -> None:
        ValidateBrepId(self.id)


# line curves retain exact origin and direction without sampled approximation
@ModelDataMut
class LineCurve(BrepCurve):
    id: str
    origin: SpaceVector
    direction: SpaceVector
    provenance: Provenance | None = None
    attributes: TypeMap[str, object] = MakeDataField(default_factory=FreezeMapping)

    # anchor point keeps curve placement absolute without extra context
    @property
    def Origin(self) -> SpaceVector:
        return self.origin

    # unit heading keeps linear geometry orientation explicit for writers
    @property
    def Direction(self) -> SpaceVector:
        return self.direction


# circle curves preserve exact spatial frames and radii across kernels
@ModelDataMut
class CircleCurve(BrepCurve):
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


# ellipse curves preserve exact spatial frames and both principal radii
@ModelDataMut
class EllipseCurve(BrepCurve):
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


# spline curves retain full basis data needed for exact reconstruction
@ModelDataMut
class NurbsCurve(BrepCurve):
    id: str
    degree: int
    control_points: tuple[SpaceVector, ...]
    knots: tuple[float, ...]
    multiplicities: tuple[int, ...]
    weights: tuple[float, ...] = ()
    periodic: bool = False
    provenance: Provenance | None = None
    attributes: TypeMap[str, object] = MakeDataField(default_factory=FreezeMapping)

    # spline degree controls smoothness and must survive round trips intact
    @property
    def Degree(self) -> int:
        return self.degree

    # hull points define spline shape so evaluation never needs vendor kernels
    @property
    def ControlPoints(self) -> tuple[SpaceVector, ...]:
        return self.control_points

    # knot vector defines segment joins so splines evaluate identically everywhere
    @property
    def KnotValues(self) -> tuple[float, ...]:
        return self.knots

    # knot multiplicities preserve continuity breaks that plain knots cannot encode
    @property
    def Multiplicities(self) -> tuple[int, ...]:
        return self.multiplicities

    # rational weights keep conic splines representable exactly rather than approximately
    @property
    def Weights(self) -> tuple[float, ...]:
        return self.weights

    # periodicity tells evaluators whether seam continuity can be assumed safely
    @property
    def IsPeriodic(self) -> bool:
        return self.periodic


# intersection curves preserve supporting surfaces and sampled verification evidence
@ModelDataMut
class IntersectCurve(BrepCurve):
    id: str
    first_surface_id: str
    second_surface_id: str
    samples: tuple[SpaceVector, ...] = ()
    tolerance: float = 0.0
    provenance: Provenance | None = None
    attributes: TypeMap[str, object] = MakeDataField(default_factory=FreezeMapping)

    # first surface link keeps intersection curves anchored to real faces
    @property
    def FirstSurfaceId(self) -> str:
        return self.first_surface_id

    # second surface link completes the intersection pairing for validation
    @property
    def SecondSurfaceId(self) -> str:
        return self.second_surface_id

    # sampled points keep intersection curves verifiable without implicit evaluation
    @property
    def Samples(self) -> tuple[SpaceVector, ...]:
        return self.samples

    # tolerance bounds approximation error so consumers can trust comparisons
    @property
    def Tolerance(self) -> float:
        return self.tolerance


# native curves retain unsupported kernel data without claiming portable semantics
@ModelDataMut
class NativeCurve(BrepCurve):
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
