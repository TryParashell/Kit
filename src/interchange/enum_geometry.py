# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from .enum_base import WireEnum


# geometry categories preserve editable sketch entity intent across vendor formats
class GeometryKind(WireEnum):
    KPoint = "point"
    KLine = "line"
    KCircle = "circle"
    KArcGeometry = "arc"
    KEllipse = "ellipse"
    KArcEllipse = "arc_ellipse"
    KHyperbola = "hyperbola"
    KArcHyperbola = "arc_hyperbola"
    KParabola = "parabola"
    KArcParabola = "arc_parabola"
    KBezier = "bezier"
    KSpline = "spline"
    KOffset = "offset"
    KTrimmed = "trimmed"
    KNative = "native"


# constraint categories retain solver semantics without vendor specific identifiers
class ConstraintKind(WireEnum):
    KCoincident = "coincident"
    KHorizontal = "horizontal"
    KVertical = "vertical"
    KParallel = "parallel"
    KPerpendicular = "perpendicular"
    KTangent = "tangent"
    KEqual = "equal"
    KConcentric = "concentric"
    KPointOnObject = "point_on_object"
    KSymmetric = "symmetric"
    KMidpoint = "midpoint"
    KDistance = "distance"
    KDistanceX = "distance_x"
    KDistanceY = "distance_y"
    KAngle = "angle"
    KRadius = "radius"
    KDiameter = "diameter"
    KFixed = "fixed"
    KInternalAlignment = "internal_alignment"
    KSnellsLaw = "snells_law"
    KBlock = "block"
    KWeight = "weight"
    KGroup = "group"
    KText = "text"
    KNative = "native"
