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
from interchange.assembly.AssemblyEnums import ComponentKind


# graph cycle detection prevents recursive component ownership from becoming unbounded
def HasGraphCycle(DefinitionGraph: TypeMap[str, set[str]]) -> bool:
    VisitState: dict[str, int] = {}

    # recursive visitation is isolated so each definition receives one stable state transition
    def HasCycle(DefinitionId: str) -> bool:
        VisitStatus = VisitState.get(DefinitionId, 0)
        if VisitStatus == 1:
            return True
        if VisitStatus == 2:
            return False
        VisitState[DefinitionId] = 1
        IsCyclic = any(HasCycle(ChildId) for ChildId in DefinitionGraph[DefinitionId])
        VisitState[DefinitionId] = 2
        return IsCyclic

    return any(HasCycle(DefinitionId) for DefinitionId in DefinitionGraph)


# component graph checks protect roots definitions owners transforms and acyclic nesting
def GetGraphErrors(
    AssemblyValue: AssemblyData, Definitions: TypeMap[str, ComponentDef]
) -> tuple[str, ...]:
    ErrorValues: list[str] = []
    if AssemblyValue.RootDefinitionId not in Definitions:
        ErrorValues.append("assembly references missing root component definition")
    elif (
        Definitions[AssemblyValue.RootDefinitionId].EntityKind
        != ComponentKind.KAssembly
    ):
        ErrorValues.append("assembly root component definition is not an assembly")
    DefinitionGraph: dict[str, set[str]] = {
        DefinitionId: set() for DefinitionId in Definitions
    }
    for InstanceValue in AssemblyValue.Instances:
        if InstanceValue.DefinitionId not in Definitions:
            ErrorValues.append(
                f"component instance {InstanceValue.EntityId} references missing definition"
            )
        if InstanceValue.OwnerDefinitionId not in Definitions:
            ErrorValues.append(
                f"component instance {InstanceValue.EntityId} references missing owner definition"
            )
        elif (
            Definitions[InstanceValue.OwnerDefinitionId].EntityKind
            != ComponentKind.KAssembly
        ):
            ErrorValues.append(
                f"component instance {InstanceValue.EntityId} owner is not an assembly"
            )
        if not InstanceValue.Transform.IsFinite():
            ErrorValues.append(
                f"component instance {InstanceValue.EntityId} has an invalid transform"
            )
        if (
            InstanceValue.OwnerDefinitionId in DefinitionGraph
            and InstanceValue.DefinitionId in Definitions
        ):
            DefinitionGraph[InstanceValue.OwnerDefinitionId].add(
                InstanceValue.DefinitionId
            )
    if HasGraphCycle(DefinitionGraph):
        ErrorValues.append("component definition graph contains a cycle")
    return tuple(ErrorValues)
