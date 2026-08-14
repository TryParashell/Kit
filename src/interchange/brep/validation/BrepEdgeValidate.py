# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from math import isfinite as IsFiniteNum

from interchange.brep.topology.BrepMath import IsFiniteSpace, IsValidTol
from interchange.brep.topology.BrepModel import BrepModel


# vertex and edge validation protects incidence and parameter ranges together
def GetEdgeErrors(
    ModelValue: BrepModel, IdentitySets: dict[str, frozenset[str]]
) -> tuple[str, ...]:
    ErrorValues: list[str] = []
    for VertexValue in ModelValue.Vertices:
        if not IsFiniteSpace(VertexValue.Point) or not IsValidTol(
            VertexValue.Tolerance
        ):
            ErrorValues.append(f"B-rep vertex {VertexValue.EntityId} is invalid")
    for EdgeValue in ModelValue.Edges:
        if EdgeValue.StartVertexId not in IdentitySets["Vertices"]:
            ErrorValues.append(
                f"B-rep edge {EdgeValue.EntityId} references a missing start vertex"
            )
        if EdgeValue.EndVertexId not in IdentitySets["Vertices"]:
            ErrorValues.append(
                f"B-rep edge {EdgeValue.EntityId} references a missing end vertex"
            )
        if EdgeValue.CurveId not in IdentitySets["Curves"]:
            ErrorValues.append(
                f"B-rep edge {EdgeValue.EntityId} references a missing curve"
            )
        HasFiniteRange = all(
            IsFiniteNum(SourceValue)
            for SourceValue in (EdgeValue.StartParameter, EdgeValue.EndParameter)
        )
        if not HasFiniteRange or not IsValidTol(EdgeValue.Tolerance):
            ErrorValues.append(
                f"B-rep edge {EdgeValue.EntityId} has an invalid range or tolerance"
            )
    for CoedgeValue in ModelValue.Coedges:
        if CoedgeValue.EdgeId not in IdentitySets["Edges"]:
            ErrorValues.append(
                f"B-rep coedge {CoedgeValue.EntityId} references a missing edge"
            )
        if CoedgeValue.PcurveId and CoedgeValue.PcurveId not in IdentitySets["Pcurves"]:
            ErrorValues.append(
                f"B-rep coedge {CoedgeValue.EntityId} references a missing pcurve"
            )
    return tuple(ErrorValues)
