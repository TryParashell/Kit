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
from interchange.geometry.models.VectorSpace import SpaceVector


# surface identity checks reject malformed records before topology validation
@ModelDataMut
class BrepSurface(BrepEntity):

    # invalid identifiers must fail before surfaces enter topology collections
    def __post_init__(self) -> None:
        if not isinstance(self.EntityId, str):
            raise TypeError("B-rep surface id must be a string")


# planes retain exact spatial frames for analytic reconstruction
@ModelDataMut
class PlaneSurface(BrepSurface):
    Origin: SpaceVector
    Normal: SpaceVector
    RefDirection: SpaceVector
    if TYPE_CHECKING:
        origin: ClassVar[SpaceVector]
        normal: ClassVar[SpaceVector]
        reference_direction: ClassVar[SpaceVector]


# cylinders retain exact axes reference directions and radii
@ModelDataMut
class CylinderSurface(BrepSurface):
    Origin: SpaceVector
    AxisVector: SpaceVector
    RefDirection: SpaceVector
    Radius: float
    if TYPE_CHECKING:
        origin: ClassVar[SpaceVector]
        axis: ClassVar[SpaceVector]
        reference_direction: ClassVar[SpaceVector]
        radius: ClassVar[float]


# cones retain exact axes base radii and half angles
@ModelDataMut
class ConeSurface(BrepSurface):
    Origin: SpaceVector
    AxisVector: SpaceVector
    RefDirection: SpaceVector
    Radius: float
    HalfAngle: float
    if TYPE_CHECKING:
        origin: ClassVar[SpaceVector]
        axis: ClassVar[SpaceVector]
        reference_direction: ClassVar[SpaceVector]
        radius: ClassVar[float]
        half_angle: ClassVar[float]


# spheres retain exact centers orientation frames and radii
@ModelDataMut
class SphereSurface(BrepSurface):
    Center: SpaceVector
    AxisVector: SpaceVector
    RefDirection: SpaceVector
    Radius: float
    if TYPE_CHECKING:
        center: ClassVar[SpaceVector]
        axis: ClassVar[SpaceVector]
        reference_direction: ClassVar[SpaceVector]
        radius: ClassVar[float]


# tori retain exact centers orientation frames and both radii
@ModelDataMut
class TorusSurface(BrepSurface):
    Center: SpaceVector
    AxisVector: SpaceVector
    RefDirection: SpaceVector
    MajorRadius: float
    MinorRadius: float
    if TYPE_CHECKING:
        center: ClassVar[SpaceVector]
        axis: ClassVar[SpaceVector]
        reference_direction: ClassVar[SpaceVector]
        major_radius: ClassVar[float]
        minor_radius: ClassVar[float]


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
    if TYPE_CHECKING:
        degree_u: ClassVar[int]
        degree_v: ClassVar[int]
        control_points: ClassVar[tuple[tuple[SpaceVector, ...], ...]]
        knots_u: ClassVar[tuple[float, ...]]
        knots_v: ClassVar[tuple[float, ...]]
        multiplicities_u: ClassVar[tuple[int, ...]]
        multiplicities_v: ClassVar[tuple[int, ...]]
        weights: ClassVar[tuple[tuple[float, ...], ...]]
        periodic_u: ClassVar[bool]
        periodic_v: ClassVar[bool]


# offset surfaces preserve analytic relationships instead of flattening to splines
@ModelDataMut
class OffsetSurface(BrepSurface):
    BaseSurfaceId: str
    Distance: float
    if TYPE_CHECKING:
        base_surface_id: ClassVar[str]
        distance: ClassVar[float]


# native surfaces preserve unsupported kernel data without false portable semantics
@ModelDataMut(FactoryMap={"PayloadData": FreezeMapping})
class NativeSurface(BrepSurface):
    FormatId: str
    EntityType: str
    PayloadData: TypeMap[str, object]
    if TYPE_CHECKING:
        format_id: ClassVar[str]
        entity_type: ClassVar[str]
        payload: ClassVar[TypeMap[str, object]]
