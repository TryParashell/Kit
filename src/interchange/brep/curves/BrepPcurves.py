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

    @property
    def Origin(self) -> PlaneVector:
        return self.origin

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

    @property
    def Center(self) -> PlaneVector:
        return self.center

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

    @property
    def Degree(self) -> int:
        return self.degree

    @property
    def ControlPoints(self) -> tuple[PlaneVector, ...]:
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


# native parameter curves preserve unsupported kernel specific trimming data
@ModelDataMut
class NativePcurve(BrepPcurve):
    id: str
    format_id: str
    entity_type: str
    data: TypeMap[str, object] = MakeDataField(default_factory=FreezeMapping)
    provenance: Provenance | None = None
    attributes: TypeMap[str, object] = MakeDataField(default_factory=FreezeMapping)

    @property
    def FormatId(self) -> str:
        return self.format_id

    @property
    def EntityType(self) -> str:
        return self.entity_type

    @property
    def PayloadData(self) -> TypeMap[str, object]:
        return self.data
