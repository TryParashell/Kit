# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from interchange.geometry.models.GeometryConics import (
    ArcEllipseGeom,
    ArcHyperGeom,
    ArcParabGeom,
    EllipseGeometry,
    HyperbolaGeom,
    ParabolaGeom,
)
from interchange.geometry.models.GeometryCurves import (
    ArcGeometry,
    CircleGeometry,
    LineGeometry,
    NativeGeometry,
    PointGeometry,
    SplineGeometry,
)
from interchange.geometry.models.GeometryTypes import KGeometryTypes
from interchange.compatibility.PythonCompat import BindCompatMut
from interchange.geometry.models.Selection import Selection, SelectPathElem
from interchange.geometry.models.Sketch import (
    ConstraintRef,
    Sketch,
    SketchEntity,
    SketchRelation,
)
from interchange.geometry.models.SupportPlane import SupportPlane
from interchange.geometry.models.VectorPlane import PlaneVector
from interchange.geometry.models.VectorSpace import SpaceVector

# historical geometry typing remains available because consumers inspect union coverage
Geometry = KGeometryTypes

BindCompatMut(
    (
        PointGeometry,
        LineGeometry,
        CircleGeometry,
        ArcGeometry,
        EllipseGeometry,
        ArcEllipseGeom,
        HyperbolaGeom,
        ArcHyperGeom,
        ParabolaGeom,
        ArcParabGeom,
        SplineGeometry,
        NativeGeometry,
        SupportPlane,
        SketchEntity,
        ConstraintRef,
        SketchRelation,
        Sketch,
        SelectPathElem,
        Selection,
    ),
    {__name__: globals()},
)

ArcEllipseGeometry = ArcEllipseGeom
ArcHyperbolaGeometry = ArcHyperGeom
ArcParabolaGeometry = ArcParabGeom
ConstraintReference = ConstraintRef
HyperbolaGeometry = HyperbolaGeom
ParabolaGeometry = ParabolaGeom
SelectionPathElement = SelectPathElem
SketchConstraint = SketchRelation

# geometry consumers need one intentional historical public contract
__all__ = (
    "ArcEllipseGeometry",
    "ArcGeometry",
    "ArcHyperbolaGeometry",
    "ArcParabolaGeometry",
    "CircleGeometry",
    "ConstraintReference",
    "EllipseGeometry",
    "Geometry",
    "HyperbolaGeometry",
    "LineGeometry",
    "NativeGeometry",
    "ParabolaGeometry",
    "PointGeometry",
    "PlaneVector",
    "Selection",
    "SelectionPathElement",
    "Sketch",
    "SketchConstraint",
    "SketchEntity",
    "SplineGeometry",
    "SupportPlane",
    "SpaceVector",
)
