# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from math import isfinite as IsFiniteNum
from typing import Mapping as TypeMap

from interchange.assembly.AssemblyData import AssemblyData  # lgtm[py/cyclic-import]
from interchange.assembly.ComponentDefinition import ComponentDef
from interchange.assembly.ComponentInstance import ComponentInst
from interchange.assembly.MateEntity import MateEntity
from interchange.document.models.DocumentModel import (
    CadDocument,
)  # lgtm[py/cyclic-import]


# runtime model construction can bypass annotations so radii need an explicit numeric boundary
def IsValidRadius(SourceValue: object) -> bool:
    return (
        isinstance(SourceValue, (int, float))
        and IsFiniteNum(SourceValue)
        and SourceValue >= 0.0
    )


# mate entity checks protect occurrence paths frames radii and selection ownership
def GetMateEntErrs(
    DocumentValue: CadDocument,
    AssemblyValue: AssemblyData,
    Definitions: TypeMap[str, ComponentDef],
    Instances: TypeMap[str, ComponentInst],
    DocumentValues: TypeMap[str, CadDocument],
    IdentitySets: TypeMap[str, set[str]],
) -> tuple[str, ...]:
    ErrorValues: list[str] = []
    for EntityValue in AssemblyValue.mate_entities:
        if EntityValue.owner_definition_id not in Definitions:
            ErrorValues.append(
                f"mate entity {EntityValue.id} references missing owner definition"
            )
            continue
        CurrentDefId = EntityValue.owner_definition_id
        IsValidPath = True
        for InstanceId in EntityValue.instance_path:
            InstanceValue = Instances.get(InstanceId)
            if InstanceValue is None:
                ErrorValues.append(
                    f"mate entity {EntityValue.id} references missing instance {InstanceId}"
                )
                IsValidPath = False
                break
            if InstanceValue.owner_definition_id != CurrentDefId:
                ErrorValues.append(
                    f"mate entity {EntityValue.id} has a disconnected instance path"
                )
                IsValidPath = False
                break
            CurrentDefId = InstanceValue.definition_id
        if EntityValue.frame is not None and not EntityValue.frame.IsFinite():
            ErrorValues.append(f"mate entity {EntityValue.id} has an invalid frame")
        if EntityValue.radius is not None and not IsValidRadius(EntityValue.radius):
            ErrorValues.append(f"mate entity {EntityValue.id} has an invalid radius")
        ErrorValues.extend(
            GetSelectErrors(
                DocumentValue,
                EntityValue,
                Definitions,
                DocumentValues,
                IdentitySets,
                CurrentDefId,
                IsValidPath,
            )
        )
    return tuple(ErrorValues)


# selection checks protect resolved mate geometry from dangling document references
def GetSelectErrors(
    DocumentValue: CadDocument,
    EntityValue: MateEntity,
    Definitions: TypeMap[str, ComponentDef],
    DocumentValues: TypeMap[str, CadDocument],
    IdentitySets: TypeMap[str, set[str]],
    CurrentDefId: str,
    IsValidPath: bool,
) -> tuple[str, ...]:
    if not EntityValue.selection_id or not IsValidPath:
        return ()
    TargetDef = Definitions.get(CurrentDefId)
    TargetDocument: CadDocument | None = DocumentValue
    if TargetDef is not None and TargetDef.document_id:
        TargetDocument = DocumentValues.get(TargetDef.document_id)
    if TargetDocument is None:
        return ()
    TargetSelectIds = (
        IdentitySets["selections"]
        if TargetDocument is DocumentValue
        else {SelectionValue.id for SelectionValue in TargetDocument.selections}
    )
    if EntityValue.selection_id not in TargetSelectIds:
        return (f"mate entity {EntityValue.id} references missing selection",)
    return ()
