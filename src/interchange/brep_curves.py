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
from .record_provenance import Provenance
from .vector_space import SpaceVector


# shared topology identity avoids duplicated provenance fields across curve families
@ModelDataMut(
    DefaultMap={"Provenance": None},
    FactoryMap={"Attributes": FreezeMapping},
    KeywordOnly=frozenset({"Provenance", "Attributes"}),
)
class BrepEntity(ModelBase):
    EntityId: str
    Provenance: Provenance | None
    Attributes: TypeMap[str, AnyValue]


# curve identity checks reject malformed records before topology validation
@ModelDataMut
class BrepCurve(BrepEntity):

    # invalid identifiers must fail before curves enter topology collections
    def __post_init__(SelfValue) -> None:
        if not isinstance(SelfValue.EntityId, str):
            raise TypeError("B-rep curve id must be a string")


# line curves retain exact origin and direction without sampled approximation
@ModelDataMut
class LineCurve(BrepCurve):
    Origin: SpaceVector
    Direction: SpaceVector


# circle curves preserve exact spatial frames and radii across kernels
@ModelDataMut
class CircleCurve(BrepCurve):
    Center: SpaceVector
    AxisVector: SpaceVector
    RefDirection: SpaceVector
    Radius: float


# ellipse curves preserve exact spatial frames and both principal radii
@ModelDataMut
class EllipseCurve(BrepCurve):
    Center: SpaceVector
    AxisVector: SpaceVector
    RefDirection: SpaceVector
    MajorRadius: float
    MinorRadius: float


# spline curves retain full basis data needed for exact reconstruction
@ModelDataMut(DefaultMap={"Weights": (), "IsPeriodic": False})
class NurbsCurve(BrepCurve):
    Degree: int
    ControlPoints: tuple[SpaceVector, ...]
    KnotValues: tuple[float, ...]
    Multiplicities: tuple[int, ...]
    Weights: tuple[float, ...]
    IsPeriodic: bool


# intersection curves preserve supporting surfaces and sampled verification evidence
@ModelDataMut(DefaultMap={"Samples": (), "Tolerance": 0.0})
class IntersectCurve(BrepCurve):
    FirstSurfaceId: str
    SecondSurfaceId: str
    Samples: tuple[SpaceVector, ...]
    Tolerance: float


# native curves retain unsupported kernel data without claiming portable semantics
@ModelDataMut(FactoryMap={"PayloadData": FreezeMapping})
class NativeCurve(BrepCurve):
    FormatId: str
    EntityType: str
    PayloadData: TypeMap[str, AnyValue]
