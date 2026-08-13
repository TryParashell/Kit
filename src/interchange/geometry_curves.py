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

from .common import FreezeMapping
from .model_base import ModelBase, ModelDataMut
from .vector_plane import PlaneVector


# point geometry represents isolated sketch locations without degenerate curves
@ModelDataMut
class PointGeometry(ModelBase):
    Point: PlaneVector


# line geometry preserves finite sketch segments independently from support lines
@ModelDataMut
class LineGeometry(ModelBase):
    Start: PlaneVector
    EndPoint: PlaneVector


# circle geometry retains exact centers and radii instead of sampled approximations
@ModelDataMut
class CircleGeometry(ModelBase):
    Center: PlaneVector
    Radius: float


# arc geometry preserves angular trimming on an exact circular support curve
@ModelDataMut
class ArcGeometry(ModelBase):
    Center: PlaneVector
    Radius: float
    StartAngle: float
    EndAngle: float


# splines retain control data needed for editable and exact reconstruction
@ModelDataMut(
    DefaultMap={
        "KnotValues": (),
        "Multiplicities": (),
        "Weights": (),
        "IsPeriodic": False,
    }
)
class SplineGeometry(ModelBase):
    ControlPoints: tuple[PlaneVector, ...]
    Degree: int
    KnotValues: tuple[float, ...]
    Multiplicities: tuple[int, ...]
    Weights: tuple[float, ...]
    IsPeriodic: bool


# native geometry preserves unsupported entities without pretending they are portable
@ModelDataMut(FactoryMap={"PayloadData": FreezeMapping})
class NativeGeometry(ModelBase):
    FormatId: str
    EntityType: str
    PayloadData: TypeMap[str, AnyValue]
