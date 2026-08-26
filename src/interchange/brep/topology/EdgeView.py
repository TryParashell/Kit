# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from typing import cast as CastValue


# edge walkers read trim ranges and endpoints through one typed view
class EdgeView:
    __slots__ = ()

    # endpoint links keep edge traversal possible without geometric matching
    @property
    def StartVertexId(self) -> str:
        return CastValue(str, getattr(self, "start_vertex_id"))

    # closing endpoint keeps edge ranges complete without geometric matching
    @property
    def EndVertexId(self) -> str:
        return CastValue(str, getattr(self, "end_vertex_id"))

    # curve link keeps edges defined once and shared across faces
    @property
    def CurveId(self) -> str:
        return CastValue(str, getattr(self, "curve_id"))

    # trim range bounds the used portion so shared curves stay reusable
    @property
    def StartParameter(self) -> float:
        return CastValue(float, getattr(self, "start_parameter"))

    # trim end completes the range so trimming needs no heuristics
    @property
    def EndParameter(self) -> float:
        return CastValue(float, getattr(self, "end_parameter"))

    # tolerance bounds approximation error so consumers can trust comparisons
    @property
    def Tolerance(self) -> float:
        return CastValue(float, getattr(self, "tolerance"))

    # degeneracy flag protects downstream math from zero length edges
    @property
    def IsDegenerate(self) -> bool:
        return CastValue(bool, getattr(self, "degenerate"))
