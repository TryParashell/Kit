# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from math import isfinite as IsFiniteNum

from interchange.brep.curves.BrepCurves import BrepCurve, CircleCurve, EllipseCurve, IntersectCurve, LineCurve, NativeCurve, NurbsCurve
from interchange.brep.topology.BrepMath import IsFiniteSpace, IsNonzeroSpace, IsValidSpline, IsValidTol


# curve validation protects exact geometry consumers from malformed analytic data
def GetCurveErrors(
    CurveValue: BrepCurve, SurfaceIds: frozenset[str]
) -> tuple[str, ...]:
    IsValid = False
    if isinstance(CurveValue, LineCurve):
        IsValid = IsFiniteSpace(CurveValue.Origin) and IsNonzeroSpace(
            CurveValue.Direction
        )
    elif isinstance(CurveValue, CircleCurve):
        IsValid = (
            IsFiniteSpace(CurveValue.Center)
            and IsNonzeroSpace(CurveValue.AxisVector)
            and IsNonzeroSpace(CurveValue.RefDirection)
            and IsFiniteNum(CurveValue.Radius)
            and CurveValue.Radius > 0.0
        )
    elif isinstance(CurveValue, EllipseCurve):
        IsValid = (
            IsFiniteSpace(CurveValue.Center)
            and IsNonzeroSpace(CurveValue.AxisVector)
            and IsNonzeroSpace(CurveValue.RefDirection)
            and IsFiniteNum(CurveValue.MajorRadius)
            and IsFiniteNum(CurveValue.MinorRadius)
            and CurveValue.MajorRadius >= CurveValue.MinorRadius > 0.0
        )
    elif isinstance(CurveValue, NurbsCurve):
        IsValid = all(
            IsFiniteSpace(PointValue) for PointValue in CurveValue.ControlPoints
        ) and IsValidSpline(
            CurveValue.Degree,
            len(CurveValue.ControlPoints),
            CurveValue.KnotValues,
            CurveValue.Multiplicities,
            CurveValue.Weights,
            CurveValue.IsPeriodic,
        )
    elif isinstance(CurveValue, IntersectCurve):
        IsValid = (
            CurveValue.FirstSurfaceId in SurfaceIds
            and CurveValue.SecondSurfaceId in SurfaceIds
            and CurveValue.FirstSurfaceId != CurveValue.SecondSurfaceId
            and all(IsFiniteSpace(PointValue) for PointValue in CurveValue.Samples)
            and IsValidTol(CurveValue.Tolerance)
        )
    elif isinstance(CurveValue, NativeCurve):
        IsValid = bool(CurveValue.FormatId and CurveValue.EntityType)
    return () if IsValid else (f"B-rep curve {CurveValue.EntityId} is invalid",)
