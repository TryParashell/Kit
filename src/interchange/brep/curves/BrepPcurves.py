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

from interchange.brep.curves.BrepCurves import BrepEntity, ValidateBrepId
from interchange.core.Common import FreezeMapping
from interchange.core.ModelBase import ModelDataMut
from interchange.geometry.models.VectorPlane import PlaneVector


# parameter curve identity checks reject malformed topology records early
@ModelDataMut
class BrepPcurve(BrepEntity):

    # invalid identifiers must fail before parameter curves enter collections
    def __post_init__(self) -> None:
        ValidateBrepId(self.id)


# planar line curves retain exact parameter space origin and direction
@ModelDataMut
class LinePcurve(BrepPcurve):
    origin: PlaneVector
    direction: PlaneVector
    if TYPE_CHECKING:
        Origin: ClassVar[PlaneVector]
        Direction: ClassVar[PlaneVector]


# planar circle curves preserve exact parameter space centers and radii
@ModelDataMut
class CirclePcurve(BrepPcurve):
    center: PlaneVector
    radius: float
    if TYPE_CHECKING:
        Center: ClassVar[PlaneVector]
        Radius: ClassVar[float]


# planar spline curves retain full basis data required for trimming
@ModelDataMut(DefaultMap={"weights": (), "periodic": False})
class NurbsPcurve(BrepPcurve):
    degree: int
    control_points: tuple[PlaneVector, ...]
    knots: tuple[float, ...]
    multiplicities: tuple[int, ...]
    weights: tuple[float, ...]
    periodic: bool
    if TYPE_CHECKING:
        Degree: ClassVar[int]
        ControlPoints: ClassVar[tuple[PlaneVector, ...]]
        KnotValues: ClassVar[tuple[float, ...]]
        Multiplicities: ClassVar[tuple[int, ...]]
        Weights: ClassVar[tuple[float, ...]]
        IsPeriodic: ClassVar[bool]


# native parameter curves preserve unsupported kernel specific trimming data
@ModelDataMut(FactoryMap={"data": FreezeMapping})
class NativePcurve(BrepPcurve):
    format_id: str
    entity_type: str
    data: TypeMap[str, object]
    if TYPE_CHECKING:
        FormatId: ClassVar[str]
        EntityType: ClassVar[str]
        PayloadData: ClassVar[TypeMap[str, object]]
