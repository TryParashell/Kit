# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from typing import TYPE_CHECKING as IsTypeCheck
from math import pi as CirclePi

if IsTypeCheck:
    from convert.adapters.solidworks.resolved.Core import FeatureLayout

# degree conversion stays centralized because recovered angles arrive in radians
KRadiansToDegrees = 180.0 / CirclePi


# callers need one angle read because raw records store rotation in radians only
def GetAngleDegrees(SelfData: FeatureLayout) -> float | None:
    if SelfData.angle_radians is None:
        return None
    return SelfData.angle_radians * KRadiansToDegrees


# sketch corners expose profile shape without exposing storage offsets to writers
def GetCornersMm(SelfData: FeatureLayout) -> tuple[tuple[float, float], ...]:
    return tuple((Point.x_mm, Point.y_mm) for Point in SelfData.points)


# arc radii summarize swept profiles so writers validate recoverable circle geometry
def GetRadiiMm(SelfData: FeatureLayout) -> tuple[float, ...]:
    return tuple(ArcValue.radius_mm for ArcValue in SelfData.arcs)


# bounds checks need one extent view across points before arc fallbacks apply
def GetBoundsMm(
    SelfData: FeatureLayout,
) -> tuple[float, float, float, float] | None:
    if SelfData.points:
        XsValue = tuple(Point.x_mm for Point in SelfData.points)
        YsValue = tuple(Point.y_mm for Point in SelfData.points)
        return (min(XsValue), min(YsValue), max(XsValue), max(YsValue))
    if SelfData.arcs:
        XsValue = tuple(
            (
                Value
                for ArcValue in SelfData.arcs
                for Value in (
                    ArcValue.centre_x_mm - ArcValue.radius_mm,
                    ArcValue.centre_x_mm + ArcValue.radius_mm,
                )
            )
        )
        YsValue = tuple(
            (
                Value
                for ArcValue in SelfData.arcs
                for Value in (
                    ArcValue.centre_y_mm - ArcValue.radius_mm,
                    ArcValue.centre_y_mm + ArcValue.radius_mm,
                )
            )
        )
        return (min(XsValue), min(YsValue), max(XsValue), max(YsValue))
    return None
