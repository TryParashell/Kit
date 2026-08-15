# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from typing import ClassVar, TYPE_CHECKING

from interchange.core.ModelBase import ModelBase, ModelDataMut
from interchange.geometry.models.VectorPlane import PlaneVector


# ellipse geometry retains principal direction and radii for editable reconstruction
@ModelDataMut
class EllipseGeometry(ModelBase):
    center: PlaneVector
    major_axis: PlaneVector
    major_radius: float
    minor_radius: float
    if TYPE_CHECKING:
        Center: ClassVar[PlaneVector]
        MajorAxis: ClassVar[PlaneVector]
        MajorRadius: ClassVar[float]
        MinorRadius: ClassVar[float]


# elliptical arcs preserve exact support plus source trimming parameters
@ModelDataMut
class ArcEllipseGeom(ModelBase):
    center: PlaneVector
    major_axis: PlaneVector
    major_radius: float
    minor_radius: float
    start_angle: float
    end_angle: float
    if TYPE_CHECKING:
        Center: ClassVar[PlaneVector]
        MajorAxis: ClassVar[PlaneVector]
        MajorRadius: ClassVar[float]
        MinorRadius: ClassVar[float]
        StartAngle: ClassVar[float]
        EndAngle: ClassVar[float]


# hyperbolas retain exact conic parameters when target sketchers support them
@ModelDataMut
class HyperbolaGeom(ModelBase):
    center: PlaneVector
    major_axis: PlaneVector
    major_radius: float
    minor_radius: float
    if TYPE_CHECKING:
        Center: ClassVar[PlaneVector]
        MajorAxis: ClassVar[PlaneVector]
        MajorRadius: ClassVar[float]
        MinorRadius: ClassVar[float]


# hyperbolic arcs preserve conic identity while retaining finite source bounds
@ModelDataMut
class ArcHyperGeom(ModelBase):
    center: PlaneVector
    major_axis: PlaneVector
    major_radius: float
    minor_radius: float
    start_angle: float
    end_angle: float
    if TYPE_CHECKING:
        Center: ClassVar[PlaneVector]
        MajorAxis: ClassVar[PlaneVector]
        MajorRadius: ClassVar[float]
        MinorRadius: ClassVar[float]
        StartAngle: ClassVar[float]
        EndAngle: ClassVar[float]


# parabolas retain focus geometry instead of relying on lossy spline conversion
@ModelDataMut
class ParabolaGeom(ModelBase):
    center: PlaneVector
    axis: PlaneVector
    focal_length: float
    if TYPE_CHECKING:
        Center: ClassVar[PlaneVector]
        AxisVector: ClassVar[PlaneVector]
        FocalLength: ClassVar[float]


# parabolic arcs preserve exact support geometry and finite parameter bounds
@ModelDataMut
class ArcParabGeom(ModelBase):
    center: PlaneVector
    axis: PlaneVector
    focal_length: float
    start_angle: float
    end_angle: float
    if TYPE_CHECKING:
        Center: ClassVar[PlaneVector]
        AxisVector: ClassVar[PlaneVector]
        FocalLength: ClassVar[float]
        StartAngle: ClassVar[float]
        EndAngle: ClassVar[float]
