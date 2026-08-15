# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from collections.abc import Mapping
import math as MathLib
from typing import Any as AnyValue

from convert.adapters.solidworks.container.Container import SldprtFormatError
from convert.adapters.solidworks.programs.Common.FieldEncoder import (
    KPrimitiveFormats,
    ReplayResolved,
)

from .Registry import (
    KFieldOwners,
    KResolvedOps,
)


# six unique vertices drive the closed line chain without duplicated endpoints
KPointOffsets = (
    6119,
    6127,
    6297,
    6305,
    6924,
    6932,
    7086,
    7094,
    7248,
    7256,
    7410,
    7418,
)

# the extrusion parameter remains independent from sketch geometry
KDepthOffset = 11090


# segment orientation is needed to reject topology changing source profiles
def CrossValue(
    FirstStart: tuple[float, float],
    FirstEnd: tuple[float, float],
    PointData: tuple[float, float],
) -> float:
    return (FirstEnd[0] - FirstStart[0]) * (PointData[1] - FirstStart[1]) - (
        FirstEnd[1] - FirstStart[1]
    ) * (PointData[0] - FirstStart[0])


# collinear contacts must be detected before accepting a fixed sketch topology
def IsOnSegment(
    FirstStart: tuple[float, float],
    FirstEnd: tuple[float, float],
    PointData: tuple[float, float],
) -> bool:
    return min(FirstStart[0], FirstEnd[0]) <= PointData[0] <= max(
        FirstStart[0], FirstEnd[0]
    ) and min(FirstStart[1], FirstEnd[1]) <= PointData[1] <= max(
        FirstStart[1], FirstEnd[1]
    )


# fixed chain references cannot represent crossing edges without changing semantics
def HasSegCross(
    FirstStart: tuple[float, float],
    FirstEnd: tuple[float, float],
    SecondStart: tuple[float, float],
    SecondEnd: tuple[float, float],
) -> bool:
    CrossFirst = CrossValue(FirstStart, FirstEnd, SecondStart)
    CrossSecond = CrossValue(FirstStart, FirstEnd, SecondEnd)
    CrossThird = CrossValue(SecondStart, SecondEnd, FirstStart)
    CrossFourth = CrossValue(SecondStart, SecondEnd, FirstEnd)
    if CrossFirst == 0.0 and IsOnSegment(FirstStart, FirstEnd, SecondStart):
        return True
    if CrossSecond == 0.0 and IsOnSegment(FirstStart, FirstEnd, SecondEnd):
        return True
    if CrossThird == 0.0 and IsOnSegment(SecondStart, SecondEnd, FirstStart):
        return True
    if CrossFourth == 0.0 and IsOnSegment(SecondStart, SecondEnd, FirstEnd):
        return True
    return (CrossFirst > 0.0) != (CrossSecond > 0.0) and (CrossThird > 0.0) != (
        CrossFourth > 0.0
    )


# simple polygon validation prevents silently emitting a different solid topology
def HasPolygonCross(PointsMm: tuple[tuple[float, float], ...]) -> bool:
    PointCount = len(PointsMm)
    for FirstIndex in range(PointCount):
        FirstNext = (FirstIndex + 1) % PointCount
        for SecondIndex in range(FirstIndex + 1, PointCount):
            SecondNext = (SecondIndex + 1) % PointCount
            if FirstNext == SecondIndex or SecondNext == FirstIndex:
                continue
            if HasSegCross(
                PointsMm[FirstIndex],
                PointsMm[FirstNext],
                PointsMm[SecondIndex],
                PointsMm[SecondNext],
            ):
                return True
    return False


# callers need one validated mapping from source millimetres into native metres
def PadFieldMap(
    PointsMm: tuple[tuple[float, float], ...], DepthMm: float
) -> dict[int, float]:
    if len(PointsMm) != 6 or any(len(PointPair) != 2 for PointPair in PointsMm):
        raise SldprtFormatError("polyline program requires exactly six vertices")
    PointValues = tuple(
        Coordinate for PointPair in PointsMm for Coordinate in PointPair
    )
    if not all(MathLib.isfinite(ValueItem) for ValueItem in PointValues):
        raise SldprtFormatError("polyline vertices must be finite")
    if len(set(PointsMm)) != len(PointsMm):
        raise SldprtFormatError("polyline vertices must be unique")
    if HasPolygonCross(PointsMm):
        raise SldprtFormatError("polyline edges must not intersect")
    AreaTwice = sum(
        PointsMm[IndexPos][0] * PointsMm[(IndexPos + 1) % 6][1]
        - PointsMm[(IndexPos + 1) % 6][0] * PointsMm[IndexPos][1]
        for IndexPos in range(6)
    )
    if AreaTwice == 0.0:
        raise SldprtFormatError("polyline area must be nonzero")
    if not MathLib.isfinite(DepthMm) or DepthMm <= 0.0:
        raise SldprtFormatError("polyline depth must be finite and positive")
    FieldValues = {
        OffsetPos: ValueMeters / 1000.0
        for OffsetPos, ValueMeters in zip(KPointOffsets, PointValues, strict=True)
    }
    FieldValues[KDepthOffset] = DepthMm / 1000.0
    return FieldValues


# callers can replace semantic fields while retaining recovered object framing
def EncodeProgram(Overrides: Mapping[int, AnyValue] | None = None) -> bytes:
    ExpectedLength = KResolvedOps[-1][0] + KResolvedOps[-1][1]
    return ReplayResolved(KResolvedOps, ExpectedLength, Overrides, KPrimitiveFormats)
