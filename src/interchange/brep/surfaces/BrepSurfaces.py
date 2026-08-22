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
    if TYPE_CHECKING:
        Origin: ClassVar[SpaceVector]
        Normal: ClassVar[SpaceVector]
        RefDirection: ClassVar[SpaceVector]


# cylinders retain exact axes reference directions and radii
@ModelDataMut
class CylinderSurface(BrepSurface):
    origin: SpaceVector
    axis: SpaceVector
    reference_direction: SpaceVector
    radius: float
    if TYPE_CHECKING:
        Origin: ClassVar[SpaceVector]
        AxisVector: ClassVar[SpaceVector]
        RefDirection: ClassVar[SpaceVector]
        Radius: ClassVar[float]


# cones retain exact axes base radii and half angles
@ModelDataMut
class ConeSurface(BrepSurface):
    origin: SpaceVector
    axis: SpaceVector
    reference_direction: SpaceVector
    radius: float
    half_angle: float
    if TYPE_CHECKING:
        Origin: ClassVar[SpaceVector]
        AxisVector: ClassVar[SpaceVector]
        RefDirection: ClassVar[SpaceVector]
        Radius: ClassVar[float]
        HalfAngle: ClassVar[float]


# spheres retain exact centers orientation frames and radii
@ModelDataMut
class SphereSurface(BrepSurface):
    center: SpaceVector
    axis: SpaceVector
    reference_direction: SpaceVector
    radius: float
    if TYPE_CHECKING:
        Center: ClassVar[SpaceVector]
        AxisVector: ClassVar[SpaceVector]
        RefDirection: ClassVar[SpaceVector]
        Radius: ClassVar[float]


# tori retain exact centers orientation frames and both radii
@ModelDataMut
class TorusSurface(BrepSurface):
    center: SpaceVector
    axis: SpaceVector
    reference_direction: SpaceVector
    major_radius: float
    minor_radius: float
    if TYPE_CHECKING:
        Center: ClassVar[SpaceVector]
        AxisVector: ClassVar[SpaceVector]
        RefDirection: ClassVar[SpaceVector]
        MajorRadius: ClassVar[float]
        MinorRadius: ClassVar[float]


# spline surfaces retain complete tensor basis data for exact reconstruction
@ModelDataMut(DefaultMap={"weights": (), "periodic_u": False, "periodic_v": False})
class NurbsSurface(BrepSurface):
    degree_u: int
    degree_v: int
    control_points: tuple[tuple[SpaceVector, ...], ...]
    knots_u: tuple[float, ...]
    knots_v: tuple[float, ...]
    multiplicities_u: tuple[int, ...]
    multiplicities_v: tuple[int, ...]
    weights: tuple[tuple[float, ...], ...]
    periodic_u: bool
    periodic_v: bool
    if TYPE_CHECKING:
        DegreeU: ClassVar[int]
        DegreeV: ClassVar[int]
        ControlPoints: ClassVar[tuple[tuple[SpaceVector, ...], ...]]
        KnotValuesU: ClassVar[tuple[float, ...]]
        KnotValuesV: ClassVar[tuple[float, ...]]
        MultiplicitiesU: ClassVar[tuple[int, ...]]
        MultiplicitiesV: ClassVar[tuple[int, ...]]
        Weights: ClassVar[tuple[tuple[float, ...], ...]]
        IsPeriodicU: ClassVar[bool]
        IsPeriodicV: ClassVar[bool]


# offset surfaces preserve analytic relationships instead of flattening to splines
@ModelDataMut
class OffsetSurface(BrepSurface):
    base_surface_id: str
    distance: float
    if TYPE_CHECKING:
        BaseSurfaceId: ClassVar[str]
        Distance: ClassVar[float]


# native surfaces preserve unsupported kernel data without false portable semantics
@ModelDataMut(FactoryMap={"data": FreezeMapping})
class NativeSurface(BrepSurface):
    format_id: str
    entity_type: str
    data: TypeMap[str, object]
    if TYPE_CHECKING:
        FormatId: ClassVar[str]
        EntityType: ClassVar[str]
        PayloadData: ClassVar[TypeMap[str, object]]
