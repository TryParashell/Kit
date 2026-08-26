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

    # center point keeps circular geometry positioned without deriving it repeatedly
    @property
    def Center(self) -> PlaneVector:
        return self.center

    # major axis direction keeps ellipse orientation fixed without inference
    @property
    def MajorAxis(self) -> PlaneVector:
        return self.major_axis

    # major extent keeps ellipse sizing exact without control point inference
    @property
    def MajorRadius(self) -> float:
        return self.major_radius

    # minor extent completes ellipse shape so reconstruction never guesses
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

    # center point keeps circular geometry positioned without deriving it repeatedly
    @property
    def Center(self) -> PlaneVector:
        return self.center

    # major axis direction keeps ellipse orientation fixed without inference
    @property
    def MajorAxis(self) -> PlaneVector:
        return self.major_axis

    # major extent keeps ellipse sizing exact without control point inference
    @property
    def MajorRadius(self) -> float:
        return self.major_radius

    # minor extent completes ellipse shape so reconstruction never guesses
    @property
    def MinorRadius(self) -> float:
        return self.minor_radius

    # angular start keeps arc extents exact without sampling geometry
    @property
    def StartAngle(self) -> float:
        return self.start_angle

    # angular end completes arc extents without sampling geometry
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

    # center point keeps circular geometry positioned without deriving it repeatedly
    @property
    def Center(self) -> PlaneVector:
        return self.center

    # major axis direction keeps ellipse orientation fixed without inference
    @property
    def MajorAxis(self) -> PlaneVector:
        return self.major_axis

    # major extent keeps ellipse sizing exact without control point inference
    @property
    def MajorRadius(self) -> float:
        return self.major_radius

    # minor extent completes ellipse shape so reconstruction never guesses
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

    # center point keeps circular geometry positioned without deriving it repeatedly
    @property
    def Center(self) -> PlaneVector:
        return self.center

    # major axis direction keeps ellipse orientation fixed without inference
    @property
    def MajorAxis(self) -> PlaneVector:
        return self.major_axis

    # major extent keeps ellipse sizing exact without control point inference
    @property
    def MajorRadius(self) -> float:
        return self.major_radius

    # minor extent completes ellipse shape so reconstruction never guesses
    @property
    def MinorRadius(self) -> float:
        return self.minor_radius

    # angular start keeps arc extents exact without sampling geometry
    @property
    def StartAngle(self) -> float:
        return self.start_angle

    # angular end completes arc extents without sampling geometry
    @property
    def EndAngle(self) -> float:
        return self.end_angle


# parabolas retain focus geometry instead of relying on lossy spline conversion
@ModelDataMut
class ParabolaGeom(ModelBase):
    center: PlaneVector
    axis: PlaneVector
    focal_length: float

    # center point keeps circular geometry positioned without deriving it repeatedly
    @property
    def Center(self) -> PlaneVector:
        return self.center

    # axis direction keeps rotational geometry oriented consistently across formats
    @property
    def AxisVector(self) -> PlaneVector:
        return self.axis

    # focal length keeps parabola shape exact without control structures
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

    # center point keeps circular geometry positioned without deriving it repeatedly
    @property
    def Center(self) -> PlaneVector:
        return self.center

    # axis direction keeps rotational geometry oriented consistently across formats
    @property
    def AxisVector(self) -> PlaneVector:
        return self.axis

    # focal length keeps parabola shape exact without control structures
    @property
    def FocalLength(self) -> float:
        return self.focal_length

    # angular start keeps arc extents exact without sampling geometry
    @property
    def StartAngle(self) -> float:
        return self.start_angle

    # angular end completes arc extents without sampling geometry
    @property
    def EndAngle(self) -> float:
        return self.end_angle
