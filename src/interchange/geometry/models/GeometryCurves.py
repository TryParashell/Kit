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

    @property
    def Point(self) -> PlaneVector:
        return self.point


# line geometry preserves finite sketch segments independently from support lines
@ModelDataMut
class LineGeometry(ModelBase):
    start: PlaneVector
    end: PlaneVector

    @property
    def Start(self) -> PlaneVector:
        return self.start

    @property
    def EndPoint(self) -> PlaneVector:
        return self.end


# circle geometry retains exact centers and radii instead of sampled approximations
@ModelDataMut
class CircleGeometry(ModelBase):
    center: PlaneVector
    radius: float

    @property
    def Center(self) -> PlaneVector:
        return self.center

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

    @property
    def Center(self) -> PlaneVector:
        return self.center

    @property
    def Radius(self) -> float:
        return self.radius

    @property
    def StartAngle(self) -> float:
        return self.start_angle

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

    @property
    def ControlPoints(self) -> tuple[PlaneVector, ...]:
        return self.control_points

    @property
    def Degree(self) -> int:
        return self.degree

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


# native geometry preserves unsupported entities without pretending they are portable
@ModelDataMut
class NativeGeometry(ModelBase):
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
