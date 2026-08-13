# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from .model_base import ModelBase, ModelDataMut
from .vector_plane import PlaneVector


# ellipse geometry retains principal direction and radii for editable reconstruction
@ModelDataMut
class EllipseGeometry(ModelBase):
    Center: PlaneVector
    MajorAxis: PlaneVector
    MajorRadius: float
    MinorRadius: float


# elliptical arcs preserve exact support plus source trimming parameters
@ModelDataMut
class ArcEllipseGeom(ModelBase):
    Center: PlaneVector
    MajorAxis: PlaneVector
    MajorRadius: float
    MinorRadius: float
    StartAngle: float
    EndAngle: float


# hyperbolas retain exact conic parameters when target sketchers support them
@ModelDataMut
class HyperbolaGeom(ModelBase):
    Center: PlaneVector
    MajorAxis: PlaneVector
    MajorRadius: float
    MinorRadius: float


# hyperbolic arcs preserve conic identity while retaining finite source bounds
@ModelDataMut
class ArcHyperGeom(ModelBase):
    Center: PlaneVector
    MajorAxis: PlaneVector
    MajorRadius: float
    MinorRadius: float
    StartAngle: float
    EndAngle: float


# parabolas retain focus geometry instead of relying on lossy spline conversion
@ModelDataMut
class ParabolaGeom(ModelBase):
    Center: PlaneVector
    AxisVector: PlaneVector
    FocalLength: float


# parabolic arcs preserve exact support geometry and finite parameter bounds
@ModelDataMut
class ArcParabGeom(ModelBase):
    Center: PlaneVector
    AxisVector: PlaneVector
    FocalLength: float
    StartAngle: float
    EndAngle: float
