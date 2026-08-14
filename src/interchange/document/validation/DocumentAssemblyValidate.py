# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from typing import Any as AnyValue
from typing import Mapping as TypeMap

from interchange.document.models.DocumentIdentity import GetIdGroups


# assembly validation composes focused graph link mesh and mate checks deterministically
def GetAssemblyErrs(
    DocumentValue: AnyValue, IdentitySets: TypeMap[str, set[str]]
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

    AssemblyValue = DocumentValue.Assembly
    if AssemblyValue is None:
        return ()
    ErrorValues: list[str] = []
    for UnusedName, LabelText, ItemValues in GetIdGroups(AssemblyValue):
        IdValues = [ItemValue.EntityId for ItemValue in ItemValues]
        if len(IdValues) != len(set(IdValues)):
            ErrorValues.append(f"duplicate {LabelText} id")
    Definitions = {
        ItemValue.EntityId: ItemValue for ItemValue in AssemblyValue.Definitions
    }
    Instances = {ItemValue.EntityId: ItemValue for ItemValue in AssemblyValue.Instances}
    DocumentValues = {
        ItemValue.EntityId: ItemValue.Document for ItemValue in AssemblyValue.Documents
    }
    Entities = {
        ItemValue.EntityId: ItemValue for ItemValue in AssemblyValue.MateEntities
    }
    MateValues = {ItemValue.EntityId: ItemValue for ItemValue in AssemblyValue.Mates}
    GroupById = {
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
