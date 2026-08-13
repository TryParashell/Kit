# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from typing import Mapping as TypeMap

from .brep_topology import BrepCoedge, BrepEdge


# connectivity checks ensure loops and wires traverse incident vertices consistently
def IsCoedgeLink(
    CoedgeIds: tuple[str, ...],
    CoedgeById: TypeMap[str, BrepCoedge],
    EdgeById: TypeMap[str, BrepEdge],
    IsClosed: bool,
) -> bool:
    CoedgeUses: list[tuple[str, str]] = []
    for CoedgeId in CoedgeIds:
        CoedgeValue = CoedgeById.get(CoedgeId)
        if CoedgeValue is None:
            return False
        EdgeValue = EdgeById.get(CoedgeValue.EdgeId)
        if EdgeValue is None:
            return False
        StartId, EndId = EdgeValue.StartVertexId, EdgeValue.EndVertexId
        DirectedUse = (EndId, StartId) if CoedgeValue.IsReversed else (StartId, EndId)
        CoedgeUses.append(DirectedUse)
    if not CoedgeUses:
        return False
    LinkPairs = zip(CoedgeUses, CoedgeUses[1:])
    if any(LeftUse[1] != RightUse[0] for LeftUse, RightUse in LinkPairs):
        return False
    return not IsClosed or CoedgeUses[-1][1] == CoedgeUses[0][0]
