# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from typing import Mapping as TypeMap

from interchange.assembly.AssemblyData import AssemblyData
from interchange.assembly.ComponentDefinition import ComponentDef
from interchange.assembly.MateConstraint import MateConstraint
from interchange.assembly.MateGroup import MateGroup


# group link checks protect assembly ownership parent hierarchy and mate membership
def GetGroupLinks(
    AssemblyValue: AssemblyData,
    Definitions: TypeMap[str, ComponentDef],
    MateValues: TypeMap[str, MateConstraint],
    GroupById: TypeMap[str, MateGroup],
) -> tuple[str, ...]:
    ErrorValues: list[str] = []
    for GroupValue in AssemblyValue.MateGroups:
        if GroupValue.OwnerDefinitionId not in Definitions:
            ErrorValues.append(
                f"mate group {GroupValue.EntityId} references missing owner definition"
            )
        if GroupValue.ParentGroupId:
            ParentGroup = GroupById.get(GroupValue.ParentGroupId)
            if ParentGroup is None:
                ErrorValues.append(
                    f"mate group {GroupValue.EntityId} references missing parent"
                )
            elif ParentGroup.OwnerDefinitionId != GroupValue.OwnerDefinitionId:
                ErrorValues.append(
                    f"mate group {GroupValue.EntityId} has a parent in another assembly"
                )
        for MateId in GroupValue.MateIds:
            MateValue = MateValues.get(MateId)
            if MateValue is None:
                ErrorValues.append(
                    f"mate group {GroupValue.EntityId} references missing mate {MateId}"
                )
            elif MateValue.OwnerDefinitionId != GroupValue.OwnerDefinitionId:
                ErrorValues.append(
                    f"mate group {GroupValue.EntityId} contains mate from another assembly"
                )
    return tuple(ErrorValues)


# group cycle checks prevent recursive organization from becoming unbounded
def GetGroupCycles(
    AssemblyValue: AssemblyData, GroupById: TypeMap[str, MateGroup]
) -> tuple[str, ...]:
    ErrorValues: list[str] = []
    for GroupValue in AssemblyValue.MateGroups:
        SeenValues: set[str] = set()
        CurrentGroup = GroupValue
        while CurrentGroup.ParentGroupId:
            if CurrentGroup.EntityId in SeenValues:
                ErrorValues.append("mate group graph contains a cycle")
                break
            SeenValues.add(CurrentGroup.EntityId)
            ParentGroup = GroupById.get(CurrentGroup.ParentGroupId)
            if ParentGroup is None:
                break
            CurrentGroup = ParentGroup
    return tuple(ErrorValues)


# group validation preserves historical ordering across link and cycle diagnostics
def GetMateGroups(
    AssemblyValue: AssemblyData,
    Definitions: TypeMap[str, ComponentDef],
    MateValues: TypeMap[str, MateConstraint],
    GroupById: TypeMap[str, MateGroup],
) -> tuple[str, ...]:
    return (
        *GetGroupLinks(
            AssemblyValue,
            Definitions,
            MateValues,
            GroupById,
        ),
        *GetGroupCycles(AssemblyValue, GroupById),
    )
