# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from typing import Any as AnyValue
from typing import Mapping as TypeMap

from interchange.brep.curves.BrepCurves import BrepEntity
from interchange.core.Common import FreezeMapping
from interchange.core.ModelBase import ModelDataMut
from interchange.geometry.models.VectorSpace import SpaceVector


# surface identity checks reject malformed records before topology validation
@ModelDataMut
class BrepSurface(BrepEntity):

    # invalid identifiers must fail before surfaces enter topology collections
    def __post_init__(SelfValue) -> None:
        if not isinstance(SelfValue.EntityId, str):
            raise TypeError("B-rep surface id must be a string")


# planes retain exact spatial frames for analytic reconstruction
@ModelDataMut
class PlaneSurface(BrepSurface):
    Origin: SpaceVector
    Normal: SpaceVector
    RefDirection: SpaceVector


# cylinders retain exact axes reference directions and radii
@ModelDataMut
class CylinderSurface(BrepSurface):
    Origin: SpaceVector
    AxisVector: SpaceVector
    RefDirection: SpaceVector
    Radius: float


# cones retain exact axes base radii and half angles
@ModelDataMut
class ConeSurface(BrepSurface):
    Origin: SpaceVector
    AxisVector: SpaceVector
    RefDirection: SpaceVector
    Radius: float
    HalfAngle: float


# spheres retain exact centers orientation frames and radii
@ModelDataMut
class SphereSurface(BrepSurface):
    Center: SpaceVector
    AxisVector: SpaceVector
    RefDirection: SpaceVector
    Radius: float


# tori retain exact centers orientation frames and both radii
@ModelDataMut
class TorusSurface(BrepSurface):
    Center: SpaceVector
    AxisVector: SpaceVector
    RefDirection: SpaceVector
    MajorRadius: float
    MinorRadius: float


# spline surfaces retain complete tensor basis data for exact reconstruction
@ModelDataMut(DefaultMap={"Weights": (), "IsPeriodicU": False, "IsPeriodicV": False})
class NurbsSurface(BrepSurface):
    DegreeU: int
    DegreeV: int
    ControlPoints: tuple[tuple[SpaceVector, ...], ...]
    KnotValuesU: tuple[float, ...]
    KnotValuesV: tuple[float, ...]
    MultiplicitiesU: tuple[int, ...]
    MultiplicitiesV: tuple[int, ...]
    Weights: tuple[tuple[float, ...], ...]
    IsPeriodicU: bool
    IsPeriodicV: bool


# offset surfaces preserve analytic relationships instead of flattening to splines
@ModelDataMut
class OffsetSurface(BrepSurface):
    BaseSurfaceId: str
    Distance: float


# native surfaces preserve unsupported kernel data without false portable semantics
@ModelDataMut(FactoryMap={"PayloadData": FreezeMapping})
class NativeSurface(BrepSurface):
    FormatId: str
    EntityType: str
    PayloadData: TypeMap[str, AnyValue]
