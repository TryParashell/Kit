# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from math import isfinite as IsFiniteNum

from .model_base import ModelBase, ModelDataMut


# homogeneous matrices preserve assembly placement without assuming vendor conventions
@ModelDataMut(
    DefaultMap={
        "Values": (
            1.0,
            0.0,
            0.0,
            0.0,
            0.0,
            1.0,
            0.0,
            0.0,
            0.0,
            0.0,
            1.0,
            0.0,
            0.0,
            0.0,
            0.0,
            1.0,
        )
    }
)
class TransformMatrix(ModelBase):
    Values: tuple[float, ...]

    # matrix consumers need validated rows before indexing the homogeneous layout
    def GetRows(SelfValue) -> tuple[tuple[float, float, float, float], ...]:
        if len(SelfValue.Values) != 16:
            raise ValueError("matrix does not contain 16 values")
        return tuple(
            tuple(SelfValue.Values[OffsetValue : OffsetValue + 4])
            for OffsetValue in range(0, 16, 4)
        )

    # invalid placement numbers must be rejected before geometry reaches targets
    def IsFinite(SelfValue) -> bool:
        return len(SelfValue.Values) == 16 and all(
            IsFiniteNum(NumberValue) for NumberValue in SelfValue.Values
        )

    # point transformation centralizes the canonical row major placement convention
    def TransformPoint(
        SelfValue, PointValue: tuple[float, float, float]
    ) -> tuple[float, float, float]:
        MatrixRows = SelfValue.GetRows()
        XCoord, YCoord, ZCoord = PointValue
        return tuple(
            MatrixRow[0] * XCoord
            + MatrixRow[1] * YCoord
            + MatrixRow[2] * ZCoord
            + MatrixRow[3]
            for MatrixRow in MatrixRows[:3]
        )
