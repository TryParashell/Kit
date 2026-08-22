# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from interchange.brep.validation.BrepLinkValidate import IsCoedgeLink
from interchange.brep.validation.BrepView import BrepView


# loop and wire validation enforces nonempty connected edge use sequences
def GetLoopErrors(
    ModelValue: BrepView, IdentitySets: dict[str, frozenset[str]]
) -> tuple[str, ...]:
    ErrorValues: list[str] = []
    EdgeById = {EdgeValue.EntityId: EdgeValue for EdgeValue in ModelValue.edges}
    CoedgeById = {
        CoedgeValue.EntityId: CoedgeValue for CoedgeValue in ModelValue.coedges
    }
    for LoopValue in ModelValue.loops:
        if not LoopValue.CoedgeIds:
            ErrorValues.append(f"B-rep loop {LoopValue.EntityId} is empty")
        if any(
            CoedgeId not in IdentitySets["Coedges"] for CoedgeId in LoopValue.CoedgeIds
        ):
            ErrorValues.append(
                f"B-rep loop {LoopValue.EntityId} references a missing coedge"
            )
        if not IsCoedgeLink(LoopValue.CoedgeIds, CoedgeById, EdgeById, True):
            ErrorValues.append(
                f"B-rep loop {LoopValue.EntityId} is disconnected or open"
            )
    for WireValue in ModelValue.wires:
        if not WireValue.CoedgeIds:
            ErrorValues.append(f"B-rep wire {WireValue.EntityId} is empty")
        if any(
            CoedgeId not in IdentitySets["Coedges"] for CoedgeId in WireValue.CoedgeIds
        ):
            ErrorValues.append(
                f"B-rep wire {WireValue.EntityId} references a missing coedge"
            )
        if not IsCoedgeLink(
            WireValue.CoedgeIds, CoedgeById, EdgeById, WireValue.IsClosed
        ):
            ErrorValues.append(
                f"B-rep wire {WireValue.EntityId} has inconsistent connectivity"
            )
    return tuple(ErrorValues)
