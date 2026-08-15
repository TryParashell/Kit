# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from interchange.brep.topology.BrepMath import IsFiniteFrame
from interchange.brep.validation.BrepView import BrepView


# body validation ensures exported topology has content and valid document ownership
def GetBodyErrors(
    ModelValue: BrepView,
    IdentitySets: dict[str, frozenset[str]],
    DesignBodyIds: frozenset[str],
) -> tuple[str, ...]:
    ErrorValues: list[str] = []
    for RegionValue in ModelValue.Regions:
        if not RegionValue.ShellUseIds:
            ErrorValues.append(f"B-rep region {RegionValue.EntityId} is empty")
        for ShellUseId in RegionValue.ShellUseIds:
            if ShellUseId not in IdentitySets["ShellUses"]:
                ErrorValues.append(
                    f"B-rep region {RegionValue.EntityId} references a missing shell use"
                )
    for BodyValue in ModelValue.Bodies:
        if (
            not BodyValue.RegionIds
            and not BodyValue.WireIds
            and not BodyValue.VertexIds
        ):
            ErrorValues.append(f"B-rep body {BodyValue.EntityId} is empty")
        for RegionId in BodyValue.RegionIds:
            if RegionId not in IdentitySets["Regions"]:
                ErrorValues.append(
                    f"B-rep body {BodyValue.EntityId} references a missing region"
                )
        for WireId in BodyValue.WireIds:
            if WireId not in IdentitySets["Wires"]:
                ErrorValues.append(
                    f"B-rep body {BodyValue.EntityId} references a missing wire"
                )
        for VertexId in BodyValue.VertexIds:
            if VertexId not in IdentitySets["Vertices"]:
                ErrorValues.append(
                    f"B-rep body {BodyValue.EntityId} references a missing vertex"
                )
        if not IsFiniteFrame(BodyValue.Transform):
            ErrorValues.append(
                f"B-rep body {BodyValue.EntityId} has an invalid transform"
            )
        if BodyValue.DesignBodyId and BodyValue.DesignBodyId not in DesignBodyIds:
            ErrorValues.append(
                f"B-rep body {BodyValue.EntityId} references a missing design body"
            )
    if not ModelValue.Bodies:
        ErrorValues.append("B-rep model has no bodies")
    return tuple(ErrorValues)
