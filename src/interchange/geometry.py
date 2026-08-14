# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from .geometry_conics import (
    ArcEllipseGeom,
    ArcHyperGeom,
    ArcParabGeom,
    EllipseGeometry,
    HyperbolaGeom,
    ParabolaGeom,
)
from .geometry_curves import (
    ArcGeometry,
    CircleGeometry,
    LineGeometry,
    NativeGeometry,
    PointGeometry,
    SplineGeometry,
)
from .geometry_types import KGeometryTypes
from .python_compat import BindCompatMut
from .selection import Selection, SelectPathElem
from .sketch import ConstraintRef, Sketch, SketchEntity, SketchRelation
from .support_plane import SupportPlane

# historical geometry typing remains available because consumers inspect union coverage
globals()["Geometry"] = KGeometryTypes

# historical defining module identity preserves direct imports and existing pickle payloads
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
    "Selection",
    "SelectionPathElement",
    "Sketch",
    "SketchConstraint",
    "SketchEntity",
    "SplineGeometry",
    "SupportPlane",
)
