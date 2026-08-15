# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from math import isfinite as IsFiniteNum

from interchange.core.ModelBase import ModelBase, ModelDataMut


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
    def GetRows(self) -> tuple[tuple[float, float, float, float], ...]:
        if len(self.Values) != 16:
            raise ValueError("matrix does not contain 16 values")
        return (
            self.Values[0:4],
            self.Values[4:8],
            self.Values[8:12],
            self.Values[12:16],
        )

    # invalid placement numbers must be rejected before geometry reaches targets
    def IsFinite(self) -> bool:
        return len(self.Values) == 16 and all(
            IsFiniteNum(NumberValue) for NumberValue in self.Values
        )

    # point transformation centralizes the canonical row major placement convention
    def TransformPoint(
        self, PointValue: tuple[float, float, float]
    ) -> tuple[float, float, float]:
        MatrixRows = self.GetRows()
        XCoord, YCoord, ZCoord = PointValue
        return (
            MatrixRows[0][0] * XCoord
            + MatrixRows[0][1] * YCoord
            + MatrixRows[0][2] * ZCoord
            + MatrixRows[0][3],
            MatrixRows[1][0] * XCoord
            + MatrixRows[1][1] * YCoord
            + MatrixRows[1][2] * ZCoord
            + MatrixRows[1][3],
            MatrixRows[2][0] * XCoord
            + MatrixRows[2][1] * YCoord
            + MatrixRows[2][2] * ZCoord
            + MatrixRows[2][3],
        )
