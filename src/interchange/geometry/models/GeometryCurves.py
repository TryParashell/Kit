# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from typing import ClassVar, TYPE_CHECKING
from typing import Mapping as TypeMap

from interchange.core.Common import FreezeMapping
from interchange.core.ModelBase import ModelBase, ModelDataMut
from interchange.geometry.models.VectorPlane import PlaneVector


# point geometry represents isolated sketch locations without degenerate curves
@ModelDataMut
class PointGeometry(ModelBase):
    point: PlaneVector
    if TYPE_CHECKING:
        Point: ClassVar[PlaneVector]


# line geometry preserves finite sketch segments independently from support lines
@ModelDataMut
class LineGeometry(ModelBase):
    start: PlaneVector
    end: PlaneVector
    if TYPE_CHECKING:
        Start: ClassVar[PlaneVector]
        EndPoint: ClassVar[PlaneVector]


# circle geometry retains exact centers and radii instead of sampled approximations
@ModelDataMut
class CircleGeometry(ModelBase):
    center: PlaneVector
    radius: float
    if TYPE_CHECKING:
        Center: ClassVar[PlaneVector]
        Radius: ClassVar[float]


# arc geometry preserves angular trimming on an exact circular support curve
@ModelDataMut
class ArcGeometry(ModelBase):
    center: PlaneVector
    radius: float
    start_angle: float
    end_angle: float
    if TYPE_CHECKING:
        Center: ClassVar[PlaneVector]
        Radius: ClassVar[float]
        StartAngle: ClassVar[float]
        EndAngle: ClassVar[float]


# splines retain control data needed for editable and exact reconstruction
@ModelDataMut(
    DefaultMap={
        "knots": (),
        "multiplicities": (),
        "weights": (),
        "periodic": False,
    }
)
class SplineGeometry(ModelBase):
    control_points: tuple[PlaneVector, ...]
    degree: int
    knots: tuple[float, ...]
    multiplicities: tuple[int, ...]
    weights: tuple[float, ...]
    periodic: bool
    if TYPE_CHECKING:
        ControlPoints: ClassVar[tuple[PlaneVector, ...]]
        Degree: ClassVar[int]
        KnotValues: ClassVar[tuple[float, ...]]
        Multiplicities: ClassVar[tuple[int, ...]]
        Weights: ClassVar[tuple[float, ...]]
        IsPeriodic: ClassVar[bool]


# native geometry preserves unsupported entities without pretending they are portable
@ModelDataMut(FactoryMap={"data": FreezeMapping})
class NativeGeometry(ModelBase):
    format_id: str
    entity_type: str
    data: TypeMap[str, object]
    if TYPE_CHECKING:
        FormatId: ClassVar[str]
        EntityType: ClassVar[str]
        PayloadData: ClassVar[TypeMap[str, object]]
