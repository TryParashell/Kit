# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from math import isfinite as IsFiniteNum

from interchange.geometry.models.Transform import Transform
from interchange.geometry.models.VectorPlane import PlaneVector
from interchange.geometry.models.VectorSpace import SpaceVector


# finite planar checks prevent invalid numbers from entering analytic geometry
def IsFinitePlane(SourceValue: PlaneVector) -> bool:
    return all(
        IsFiniteNum(ComponentValue)
        for ComponentValue in (SourceValue.XCoord, SourceValue.YCoord)
    )


# finite spatial checks prevent invalid numbers from entering analytic geometry
def IsFiniteSpace(SourceValue: SpaceVector) -> bool:
    return all(
        IsFiniteNum(ComponentValue)
        for ComponentValue in (
            SourceValue.XCoord,
            SourceValue.YCoord,
            SourceValue.ZCoord,
        )
    )


# frame checks protect topology consumers from invalid transforms
def IsFiniteFrame(SourceValue: Transform) -> bool:
    return all(
        IsFiniteSpace(VectorValue)
        for VectorValue in (
            SourceValue.Origin,
            SourceValue.XAxis,
            SourceValue.YAxis,
            SourceValue.ZAxis,
        )
    )


# nonzero planar checks prevent degenerate analytic directions
def IsNonzeroPlane(SourceValue: PlaneVector) -> bool:
    return IsFinitePlane(SourceValue) and any(
        ComponentValue != 0.0
        for ComponentValue in (SourceValue.XCoord, SourceValue.YCoord)
    )


# nonzero spatial checks prevent degenerate analytic directions
def IsNonzeroSpace(SourceValue: SpaceVector) -> bool:
    return IsFiniteSpace(SourceValue) and any(
        ComponentValue != 0.0
        for ComponentValue in (
            SourceValue.XCoord,
            SourceValue.YCoord,
            SourceValue.ZCoord,
        )
    )


# tolerance checks reject negative and nonfinite model accuracy values
def IsValidTol(SourceValue: float) -> bool:
    return IsFiniteNum(SourceValue) and SourceValue >= 0.0


# spline checks enforce basis invariants shared by curves and surfaces
def IsValidSpline(
    Degree: int,
    PointCount: int,
    KnotValues: tuple[float, ...],
    Multiplicities: tuple[int, ...],
    Weights: tuple[float, ...],
    IsPeriodic: bool,
) -> bool:
    return (
        type(Degree) is int
        and Degree >= 1
        and PointCount > Degree
        and len(KnotValues) == len(Multiplicities)
        and bool(KnotValues)
        and all(IsFiniteNum(SourceValue) for SourceValue in KnotValues)
        and all(
            LeftValue < RightValue
            for LeftValue, RightValue in zip(KnotValues, KnotValues[1:])
        )
        and all(
            type(SourceValue) is int and SourceValue > 0
            for SourceValue in Multiplicities
        )
        and (IsPeriodic or sum(Multiplicities) == PointCount + Degree + 1)
        and (not Weights or len(Weights) == PointCount)
        and all(
            IsFiniteNum(SourceValue) and SourceValue > 0.0 for SourceValue in Weights
        )
    )
