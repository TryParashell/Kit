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

from interchange.brep.curves.BrepCurves import BrepEntity
from interchange.core.Common import FreezeMapping
from interchange.core.ModelBase import ModelDataMut
from interchange.geometry.models.VectorPlane import PlaneVector


# parameter curve identity checks reject malformed topology records early
@ModelDataMut
class BrepPcurve(BrepEntity):

    # invalid identifiers must fail before parameter curves enter collections
    def __post_init__(self) -> None:
        if not isinstance(self.EntityId, str):
            raise TypeError("B-rep pcurve id must be a string")


# planar line curves retain exact parameter space origin and direction
@ModelDataMut
class LinePcurve(BrepPcurve):
    Origin: PlaneVector
    Direction: PlaneVector
    if TYPE_CHECKING:
        origin: ClassVar[PlaneVector]
        direction: ClassVar[PlaneVector]


# planar circle curves preserve exact parameter space centers and radii
@ModelDataMut
class CirclePcurve(BrepPcurve):
    Center: PlaneVector
    Radius: float
    if TYPE_CHECKING:
        center: ClassVar[PlaneVector]
        radius: ClassVar[float]


# planar spline curves retain full basis data required for trimming
@ModelDataMut(DefaultMap={"Weights": (), "IsPeriodic": False})
class NurbsPcurve(BrepPcurve):
    Degree: int
    ControlPoints: tuple[PlaneVector, ...]
    KnotValues: tuple[float, ...]
    Multiplicities: tuple[int, ...]
    Weights: tuple[float, ...]
    IsPeriodic: bool
    if TYPE_CHECKING:
        degree: ClassVar[int]
        control_points: ClassVar[tuple[PlaneVector, ...]]
        knots: ClassVar[tuple[float, ...]]
        multiplicities: ClassVar[tuple[int, ...]]
        weights: ClassVar[tuple[float, ...]]
        periodic: ClassVar[bool]


# native parameter curves preserve unsupported kernel specific trimming data
@ModelDataMut(FactoryMap={"PayloadData": FreezeMapping})
class NativePcurve(BrepPcurve):
    FormatId: str
    EntityType: str
    PayloadData: TypeMap[str, object]
    if TYPE_CHECKING:
        format_id: ClassVar[str]
        entity_type: ClassVar[str]
        payload: ClassVar[TypeMap[str, object]]
