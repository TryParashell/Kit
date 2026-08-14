# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from math import isfinite as IsFiniteNum
from typing import Any as AnyValue
from typing import Mapping as TypeMap

from interchange.document.models.DocumentRoot import DocumentRoot


# mate entity checks protect occurrence paths frames radii and selection ownership
def GetMateEntErrs(
    DocumentValue: AnyValue,
    AssemblyValue: AnyValue,
    Definitions: TypeMap[str, AnyValue],
    Instances: TypeMap[str, AnyValue],
    DocumentValues: TypeMap[str, AnyValue],
    IdentitySets: TypeMap[str, set[str]],
) -> tuple[str, ...]:
    ErrorValues: list[str] = []
    for EntityValue in AssemblyValue.MateEntities:
        if EntityValue.OwnerDefinitionId not in Definitions:
            ErrorValues.append(
                f"mate entity {EntityValue.EntityId} references missing owner definition"
            )
            continue
        CurrentDefId = EntityValue.OwnerDefinitionId
        IsValidPath = True
        for InstanceId in EntityValue.InstancePath:
            InstanceValue = Instances.get(InstanceId)
            if InstanceValue is None:
                ErrorValues.append(
                    f"mate entity {EntityValue.EntityId} references missing instance {InstanceId}"
                )
                IsValidPath = False
                break
            if InstanceValue.OwnerDefinitionId != CurrentDefId:
                ErrorValues.append(
                    f"mate entity {EntityValue.EntityId} has a disconnected instance path"
                )
                IsValidPath = False
                break
            CurrentDefId = InstanceValue.DefinitionId
        if EntityValue.Frame is not None and not EntityValue.Frame.IsFinite():
            ErrorValues.append(
                f"mate entity {EntityValue.EntityId} has an invalid frame"
            )
        if EntityValue.Radius is not None and (
            not isinstance(EntityValue.Radius, (int, float))
            or not IsFiniteNum(EntityValue.Radius)
            or EntityValue.Radius < 0.0
        ):
            ErrorValues.append(
                f"mate entity {EntityValue.EntityId} has an invalid radius"
            )
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
    DocumentValue: AnyValue,
    EntityValue: AnyValue,
    Definitions: TypeMap[str, AnyValue],
    DocumentValues: TypeMap[str, AnyValue],
    IdentitySets: TypeMap[str, set[str]],
    CurrentDefId: str,
    IsValidPath: bool,
) -> tuple[str, ...]:
    if not EntityValue.SelectionId or not IsValidPath:
        return ()
    TargetDef = Definitions.get(CurrentDefId)
    TargetDocument = DocumentValue
    if TargetDef is not None and TargetDef.DocumentId:
        TargetDocument = DocumentValues.get(TargetDef.DocumentId)
    TargetSelectIds = (
        IdentitySets["Selections"]
        if TargetDocument is DocumentValue
        else {
            SelectionValue.EntityId
            for SelectionValue in getattr(TargetDocument, "Selections", ())
        }
    )
    if (
        isinstance(TargetDocument, DocumentRoot)
        and EntityValue.SelectionId not in TargetSelectIds
    ):
        return (f"mate entity {EntityValue.EntityId} references missing selection",)
    return ()
