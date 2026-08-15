# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from typing import Mapping as TypeMap

from interchange.assembly.ComponentDefinition import ComponentDef
from interchange.assembly.ComponentInstance import ComponentInst
from interchange.assembly.MateConstraint import MateConstraint
from interchange.assembly.MateEntity import MateEntity
from interchange.assembly.MateGroup import MateGroup
from interchange.document.models.DocumentIdentity import GetIdGroups
from interchange.document.models.DocumentModel import CadDocument
from interchange.document.validation.DocumentBoundary import GetDocument


# assembly validation composes focused graph link mesh and mate checks deterministically
def GetAssemblyErrs(
    DocumentValue: CadDocument, IdentitySets: TypeMap[str, set[str]]
) -> tuple[str, ...]:
    from interchange.document.validation.DocumentComponentValidate import (
        GetDefLinkErrs,
        GetDocLinkErrs,
    )
    from interchange.document.validation.DocumentGraphValidate import GetGraphErrors
    from interchange.document.validation.DocumentMateEntityValidate import (
        GetMateEntErrs,
    )
    from interchange.document.validation.DocumentMateGroupValidate import GetMateGroups
    from interchange.document.validation.DocumentMateValidate import GetMateErrors
    from interchange.document.validation.DocumentMeshValidate import GetMeshErrors

    AssemblyValue = DocumentValue.assembly
    if AssemblyValue is None:
        return ()
    ErrorValues: list[str] = []
    for GroupValue in GetIdGroups(AssemblyValue):
        LabelText = GroupValue[1]
        ItemValues = GroupValue[2]
        IdValues = [ItemValue.EntityId for ItemValue in ItemValues]
        if len(IdValues) != len(set(IdValues)):
            ErrorValues.append(f"duplicate {LabelText} id")
    Definitions: dict[str, ComponentDef] = {
        ItemValue.EntityId: ItemValue for ItemValue in AssemblyValue.Definitions
    }
    Instances: dict[str, ComponentInst] = {
        ItemValue.EntityId: ItemValue for ItemValue in AssemblyValue.Instances
    }
    DocumentValues = {
        ItemValue.EntityId: NestedValue
        for ItemValue in AssemblyValue.Documents
        if (NestedValue := GetDocument(ItemValue.Document)) is not None
    }
    Entities: dict[str, MateEntity] = {
        ItemValue.EntityId: ItemValue for ItemValue in AssemblyValue.MateEntities
    }
    MateValues: dict[str, MateConstraint] = {
        ItemValue.EntityId: ItemValue for ItemValue in AssemblyValue.Mates
    }
    GroupById: dict[str, MateGroup] = {
        ItemValue.EntityId: ItemValue for ItemValue in AssemblyValue.MateGroups
    }
    ErrorValues.extend(GetGraphErrors(AssemblyValue, Definitions))
    ErrorValues.extend(GetDocLinkErrs(DocumentValue, AssemblyValue))
    ErrorValues.extend(GetDefLinkErrs(DocumentValue, AssemblyValue, DocumentValues))
    ErrorValues.extend(GetMeshErrors(DocumentValue))
    ErrorValues.extend(
        GetMateEntErrs(
            DocumentValue,
            AssemblyValue,
            Definitions,
            Instances,
            DocumentValues,
            IdentitySets,
        )
    )
    ErrorValues.extend(
        GetMateErrors(
            DocumentValue,
            AssemblyValue,
            Definitions,
            Entities,
            DocumentValues,
            IdentitySets,
        )
    )
    ErrorValues.extend(
        GetMateGroups(
            AssemblyValue,
            Definitions,
            MateValues,
            GroupById,
        )
    )
    return tuple(ErrorValues)
