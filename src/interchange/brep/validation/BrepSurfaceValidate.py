# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from math import isfinite as IsFiniteNum
from math import pi as KPiValue

from interchange.brep.topology.BrepMath import (
    IsFiniteSpace,
    IsNonzeroSpace,
    IsValidSpline,
)
from interchange.brep.surfaces.BrepSurfaces import (
    BrepSurface,
    ConeSurface,
    CylinderSurface,
    NativeSurface,
    NurbsSurface,
    OffsetSurface,
    PlaneSurface,
    SphereSurface,
    TorusSurface,
)


# analytic surface checks protect downstream kernels from malformed frames and radii
def IsAnalyticSurf(SurfaceValue: BrepSurface) -> bool:
    if isinstance(SurfaceValue, PlaneSurface):
        return (
            IsFiniteSpace(SurfaceValue.Origin)
            and IsNonzeroSpace(SurfaceValue.Normal)
            and IsNonzeroSpace(SurfaceValue.RefDirection)
        )
    if isinstance(SurfaceValue, CylinderSurface):
        return (
            IsFiniteSpace(SurfaceValue.Origin)
            and IsNonzeroSpace(SurfaceValue.AxisVector)
            and IsNonzeroSpace(SurfaceValue.RefDirection)
            and IsFiniteNum(SurfaceValue.Radius)
            and SurfaceValue.Radius > 0.0
        )
    if isinstance(SurfaceValue, ConeSurface):
        return (
            IsFiniteSpace(SurfaceValue.Origin)
            and IsNonzeroSpace(SurfaceValue.AxisVector)
            and IsNonzeroSpace(SurfaceValue.RefDirection)
            and IsFiniteNum(SurfaceValue.Radius)
            and SurfaceValue.Radius >= 0.0
            and IsFiniteNum(SurfaceValue.HalfAngle)
            and 0.0 < abs(SurfaceValue.HalfAngle) < KPiValue / 2.0
        )
    if isinstance(SurfaceValue, SphereSurface):
        return (
            IsFiniteSpace(SurfaceValue.Center)
            and IsNonzeroSpace(SurfaceValue.AxisVector)
            and IsNonzeroSpace(SurfaceValue.RefDirection)
            and IsFiniteNum(SurfaceValue.Radius)
            and SurfaceValue.Radius > 0.0
        )
    if isinstance(SurfaceValue, TorusSurface):
        return (
            IsFiniteSpace(SurfaceValue.Center)
            and IsNonzeroSpace(SurfaceValue.AxisVector)
            and IsNonzeroSpace(SurfaceValue.RefDirection)
            and IsFiniteNum(SurfaceValue.MajorRadius)
            and SurfaceValue.MajorRadius != 0.0
            and IsFiniteNum(SurfaceValue.MinorRadius)
            and SurfaceValue.MinorRadius > 0.0
        )
    return False


# spline surface checks enforce rectangular control grids and both tensor bases
def IsSplineSurf(SurfaceValue: NurbsSurface) -> bool:
    ControlRows = SurfaceValue.ControlPoints
    RowSize = len(ControlRows[0]) if ControlRows else 0
    WeightRows = SurfaceValue.Weights
    UWeights = (1.0,) * len(ControlRows) if WeightRows else ()
    VWeights = (1.0,) * RowSize if WeightRows else ()
    return (
        bool(ControlRows)
        and RowSize > 0
        and all(len(ControlRow) == RowSize for ControlRow in ControlRows)
        and all(
            IsFiniteSpace(PointValue)
            for ControlRow in ControlRows
            for PointValue in ControlRow
        )
        and IsValidSpline(
            SurfaceValue.DegreeU,
            len(ControlRows),
            SurfaceValue.KnotValuesU,
            SurfaceValue.MultiplicitiesU,
            UWeights,
            SurfaceValue.IsPeriodicU,
        )
        and IsValidSpline(
            SurfaceValue.DegreeV,
            RowSize,
            SurfaceValue.KnotValuesV,
            SurfaceValue.MultiplicitiesV,
            VWeights,
            SurfaceValue.IsPeriodicV,
        )
        and (
            not WeightRows
            or len(WeightRows) == len(ControlRows)
            and all(len(WeightRow) == RowSize for WeightRow in WeightRows)
            and all(
                IsFiniteNum(SourceValue) and SourceValue > 0.0
                for WeightRow in WeightRows
                for SourceValue in WeightRow
            )
        )
    )


# surface validation dispatch preserves exact rules for every neutral representation
def GetSurfErrors(
    SurfaceValue: BrepSurface, SurfaceIds: frozenset[str]
) -> tuple[str, ...]:
    IsValid = IsAnalyticSurf(SurfaceValue)
    if isinstance(SurfaceValue, NurbsSurface):
        IsValid = IsSplineSurf(SurfaceValue)
    elif isinstance(SurfaceValue, OffsetSurface):
        IsValid = (
            SurfaceValue.BaseSurfaceId in SurfaceIds
            and SurfaceValue.BaseSurfaceId != SurfaceValue.EntityId
            and IsFiniteNum(SurfaceValue.Distance)
        )
    elif isinstance(SurfaceValue, NativeSurface):
        IsValid = bool(SurfaceValue.FormatId and SurfaceValue.EntityType)
    return () if IsValid else (f"B-rep surface {SurfaceValue.EntityId} is invalid",)
