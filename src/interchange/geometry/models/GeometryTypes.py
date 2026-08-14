# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from functools import reduce as ReduceValues
from operator import or_ as UnionValues

from interchange.geometry.models.GeometryConics import ArcEllipseGeom, ArcHyperGeom, ArcParabGeom, EllipseGeometry, HyperbolaGeom, ParabolaGeom
from interchange.geometry.models.GeometryCurves import ArcGeometry, CircleGeometry, LineGeometry, NativeGeometry, PointGeometry, SplineGeometry


# exhaustive geometry typing prevents new classes from escaping sketch validation
KGeometryTypes = ReduceValues(
    UnionValues,
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
    ),
)
