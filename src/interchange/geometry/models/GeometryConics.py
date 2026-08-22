# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from interchange.core.ModelBase import ModelBase, ModelDataMut
from interchange.geometry.models.VectorPlane import PlaneVector


# ellipse geometry retains principal direction and radii for editable reconstruction
@ModelDataMut
class EllipseGeometry(ModelBase):
    center: PlaneVector
    major_axis: PlaneVector
    major_radius: float
    minor_radius: float

    @property
    def Center(self) -> PlaneVector:
        return self.center

    @property
    def MajorAxis(self) -> PlaneVector:
        return self.major_axis

    @property
    def MajorRadius(self) -> float:
        return self.major_radius

    @property
    def MinorRadius(self) -> float:
        return self.minor_radius


# elliptical arcs preserve exact support plus source trimming parameters
@ModelDataMut
class ArcEllipseGeom(ModelBase):
    center: PlaneVector
    major_axis: PlaneVector
    major_radius: float
    minor_radius: float
    start_angle: float
    end_angle: float

    @property
    def Center(self) -> PlaneVector:
        return self.center

    @property
    def MajorAxis(self) -> PlaneVector:
        return self.major_axis

    @property
    def MajorRadius(self) -> float:
        return self.major_radius

    @property
    def MinorRadius(self) -> float:
        return self.minor_radius

    @property
    def StartAngle(self) -> float:
        return self.start_angle

    @property
    def EndAngle(self) -> float:
        return self.end_angle


# hyperbolas retain exact conic parameters when target sketchers support them
@ModelDataMut
class HyperbolaGeom(ModelBase):
    center: PlaneVector
    major_axis: PlaneVector
    major_radius: float
    minor_radius: float

    @property
    def Center(self) -> PlaneVector:
        return self.center

    @property
    def MajorAxis(self) -> PlaneVector:
        return self.major_axis

    @property
    def MajorRadius(self) -> float:
        return self.major_radius

    @property
    def MinorRadius(self) -> float:
        return self.minor_radius


# hyperbolic arcs preserve conic identity while retaining finite source bounds
@ModelDataMut
class ArcHyperGeom(ModelBase):
    center: PlaneVector
    major_axis: PlaneVector
    major_radius: float
    minor_radius: float
    start_angle: float
    end_angle: float

    @property
    def Center(self) -> PlaneVector:
        return self.center

    @property
    def MajorAxis(self) -> PlaneVector:
        return self.major_axis

    @property
    def MajorRadius(self) -> float:
        return self.major_radius

    @property
    def MinorRadius(self) -> float:
        return self.minor_radius

    @property
    def StartAngle(self) -> float:
        return self.start_angle

    @property
    def EndAngle(self) -> float:
        return self.end_angle


# parabolas retain focus geometry instead of relying on lossy spline conversion
@ModelDataMut
class ParabolaGeom(ModelBase):
    center: PlaneVector
    axis: PlaneVector
    focal_length: float

    @property
    def Center(self) -> PlaneVector:
        return self.center

    @property
    def AxisVector(self) -> PlaneVector:
        return self.axis

    @property
    def FocalLength(self) -> float:
        return self.focal_length


# parabolic arcs preserve exact support geometry and finite parameter bounds
@ModelDataMut
class ArcParabGeom(ModelBase):
    center: PlaneVector
    axis: PlaneVector
    focal_length: float
    start_angle: float
    end_angle: float

    @property
    def Center(self) -> PlaneVector:
        return self.center

    @property
    def AxisVector(self) -> PlaneVector:
        return self.axis

    @property
    def FocalLength(self) -> float:
        return self.focal_length

    @property
    def StartAngle(self) -> float:
        return self.start_angle

    @property
    def EndAngle(self) -> float:
        return self.end_angle
