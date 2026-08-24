# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from typing import cast as CastValue

from interchange.geometry.models.VectorSpace import SpaceVector


# spline evaluators read tensor basis inputs through one typed view
class SplineBasisView:
    __slots__ = ()

    # u degree controls surface smoothness along one parametric direction
    @property
    def DegreeU(self) -> int:
        return CastValue(int, getattr(self, "degree_u"))

    # v degree completes bidirectional smoothness control for reconstruction
    @property
    def DegreeV(self) -> int:
        return CastValue(int, getattr(self, "degree_v"))

    # hull points define spline shape so evaluation never needs vendor kernels
    @property
    def ControlPoints(self) -> tuple[tuple[SpaceVector, ...], ...]:
        return CastValue(
            tuple[tuple[SpaceVector, ...], ...],
            getattr(self, "control_points"),
        )

    # u knots define segment joins so surfaces evaluate identically everywhere
    @property
    def KnotValuesU(self) -> tuple[float, ...]:
        return CastValue(tuple[float, ...], getattr(self, "knots_u"))

    # v knots define cross direction joins without vendor reevaluation
    @property
    def KnotValuesV(self) -> tuple[float, ...]:
        return CastValue(tuple[float, ...], getattr(self, "knots_v"))

    # u multiplicities preserve continuity breaks across one parametric direction
    @property
    def MultiplicitiesU(self) -> tuple[int, ...]:
        return CastValue(tuple[int, ...], getattr(self, "multiplicities_u"))

    # v multiplicities preserve continuity breaks across the other direction
    @property
    def MultiplicitiesV(self) -> tuple[int, ...]:
        return CastValue(tuple[int, ...], getattr(self, "multiplicities_v"))
