# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from typing import TYPE_CHECKING as IsTypeCheck

import math as MathValue

if IsTypeCheck:
    from convert.adapters.solidworks.resolved.Core import SweptArc

# sweep math needs one full turn constant because arcs wrap across zero degrees
KFullCircleDegrees = 360.0

# radius agreement below this tolerance counts as numerically identical for arcs
KArcRadiusToleranceMm = 1e-06

# degenerate slivers below this radius cannot bound reliable geometry
KMinimumRadiusMm = 1e-09


# callers need the arc centre without unpacking coordinate offsets themselves
def GetCentreMm(SelfData: SweptArc) -> tuple[float, float]:
    return (SelfData.centre_x_mm, SelfData.centre_y_mm)


# callers need the swept start point without unpacking coordinate offsets themselves
def GetStartMm(SelfData: SweptArc) -> tuple[float, float]:
    return (SelfData.start_x_mm, SelfData.start_y_mm)


# callers need the swept end point without unpacking coordinate offsets themselves
def GetEndMm(SelfData: SweptArc) -> tuple[float, float]:
    return (SelfData.end_x_mm, SelfData.end_y_mm)


# start radius anchors arc size because recovered records never store radii directly
def GetRadiusMm(SelfData: SweptArc) -> float:
    return MathValue.hypot(
        SelfData.start_x_mm - SelfData.centre_x_mm,
        SelfData.start_y_mm - SelfData.centre_y_mm,
    )


# end radius comparison exposes recovered arcs that drift away from true circles
def GetEndRadiusMm(SelfData: SweptArc) -> float:
    return MathValue.hypot(
        SelfData.end_x_mm - SelfData.centre_x_mm,
        SelfData.end_y_mm - SelfData.centre_y_mm,
    )


# radii must agree within tolerance before an arc can round trip losslessly
def HasEqualRadii(SelfData: SweptArc) -> bool:
    Radius = GetRadiusMm(SelfData)
    if Radius <= KMinimumRadiusMm:
        return False
    return abs(GetEndRadiusMm(SelfData) - Radius) <= max(
        KArcRadiusToleranceMm,
        Radius * 1e-09,
    )


# start bearing fixes parametrization so downstream writers reproduce orientation
def GetStartAngle(SelfData: SweptArc) -> float:
    return MathValue.degrees(
        MathValue.atan2(
            SelfData.start_y_mm - SelfData.centre_y_mm,
            SelfData.start_x_mm - SelfData.centre_x_mm,
        )
    )


# end bearing completes angular span so sweep direction stays unambiguous
def GetEndAngle(SelfData: SweptArc) -> float:
    return MathValue.degrees(
        MathValue.atan2(
            SelfData.end_y_mm - SelfData.centre_y_mm,
            SelfData.end_x_mm - SelfData.centre_x_mm,
        )
    )


# clockwise recovery flips span sign because native records encode direction implicitly
def GetSweepAngle(SelfData: SweptArc, Counterclockwise: bool) -> float:
    SpanValue = GetEndAngle(SelfData) - GetStartAngle(SelfData)
    if not Counterclockwise:
        SpanValue = -SpanValue
    while SpanValue <= 0.0:
        SpanValue += KFullCircleDegrees
    while SpanValue > KFullCircleDegrees:
        SpanValue -= KFullCircleDegrees
    return SpanValue
