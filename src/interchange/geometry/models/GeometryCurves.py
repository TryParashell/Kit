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
from interchange.geometry.models.VectorPlane import PlaneVector


# point geometry represents isolated sketch locations without degenerate curves
@ModelDataMut
class PointGeometry(ModelBase):
    point: PlaneVector

     # stored position keeps vertices self contained without coordinate lookups
    @property
    def Point(self) -> PlaneVector:
        return self.point


# line geometry preserves finite sketch segments independently from support lines
@ModelDataMut
class LineGeometry(ModelBase):
    start: PlaneVector
    end: PlaneVector

     # start point anchors line segments without deriving endpoints repeatedly
    @property
    def Start(self) -> PlaneVector:
        return self.start

     # end point completes segment geometry so consumers need no inference
    @property
    def EndPoint(self) -> PlaneVector:
        return self.end


# circle geometry retains exact centers and radii instead of sampled approximations
@ModelDataMut
class CircleGeometry(ModelBase):
    center: PlaneVector
    radius: float

     # center point keeps circular geometry positioned without deriving it repeatedly
    @property
    def Center(self) -> PlaneVector:
        return self.center

     # radius keeps circles arcs and cylinders sized without sampling geometry
    @property
    def Radius(self) -> float:
        return self.radius


# arc geometry preserves angular trimming on an exact circular support curve
@ModelDataMut
class ArcGeometry(ModelBase):
    center: PlaneVector
    radius: float
    start_angle: float
    end_angle: float

     # center point keeps circular geometry positioned without deriving it repeatedly
    @property
    def Center(self) -> PlaneVector:
        return self.center

     # radius keeps circles arcs and cylinders sized without sampling geometry
    @property
    def Radius(self) -> float:
        return self.radius

     # angular start keeps arc extents exact without sampling geometry
    @property
    def StartAngle(self) -> float:
        return self.start_angle

     # angular end completes arc extents without sampling geometry
    @property
    def EndAngle(self) -> float:
        return self.end_angle


# splines retain control data needed for editable and exact reconstruction
@ModelDataMut
class SplineGeometry(ModelBase):
    control_points: tuple[PlaneVector, ...]
    degree: int
    knots: tuple[float, ...] = ()
    multiplicities: tuple[int, ...] = ()
    weights: tuple[float, ...] = ()
    periodic: bool = False

     # hull points define spline shape so evaluation never needs vendor kernels
    @property
    def ControlPoints(self) -> tuple[PlaneVector, ...]:
        return self.control_points

     # spline degree controls smoothness and must survive round trips intact
    @property
    def Degree(self) -> int:
        return self.degree

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


# native geometry preserves unsupported entities without pretending they are portable
@ModelDataMut
class NativeGeometry(ModelBase):
    format_id: str
    entity_type: str
    data: TypeMap[str, object] = MakeDataField(default_factory=FreezeMapping)

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
