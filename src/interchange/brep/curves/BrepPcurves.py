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
from interchange.geometry.models.VectorPlane import PlaneVector


# parameter curve identity checks reject malformed topology records early
@ModelDataMut
class BrepPcurve(BrepEntity):
    id: str

    # invalid identifiers must fail before parameter curves enter collections
    def __post_init__(self) -> None:
        ValidateBrepId(self.id)


# planar line curves retain exact parameter space origin and direction
@ModelDataMut
class LinePcurve(BrepPcurve):
    id: str
    origin: PlaneVector
    direction: PlaneVector
    provenance: Provenance | None = None
    attributes: TypeMap[str, object] = MakeDataField(default_factory=FreezeMapping)

    # anchor point keeps curve placement absolute without extra context
    @property
    def Origin(self) -> PlaneVector:
        return self.origin

    # unit heading keeps linear geometry orientation explicit for writers
    @property
    def Direction(self) -> PlaneVector:
        return self.direction


# planar circle curves preserve exact parameter space centers and radii
@ModelDataMut
class CirclePcurve(BrepPcurve):
    id: str
    center: PlaneVector
    radius: float
    provenance: Provenance | None = None
    attributes: TypeMap[str, object] = MakeDataField(default_factory=FreezeMapping)

    # center point keeps circular geometry positioned without deriving it repeatedly
    @property
    def Center(self) -> PlaneVector:
        return self.center

    # radius keeps circles arcs and cylinders sized without sampling geometry
    @property
    def Radius(self) -> float:
        return self.radius


# planar spline curves retain full basis data required for trimming
@ModelDataMut
class NurbsPcurve(BrepPcurve):
    id: str
    degree: int
    control_points: tuple[PlaneVector, ...]
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
    def ControlPoints(self) -> tuple[PlaneVector, ...]:
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


# native parameter curves preserve unsupported kernel specific trimming data
@ModelDataMut
class NativePcurve(BrepPcurve):
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
