# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from typing import Mapping as TypeMap

from interchange.assembly.AssemblyData import AssemblyData
from interchange.document.models.DocumentModel import CadDocument
from interchange.document.validation.DocumentBoundary import GetDocument


# embedded document checks prevent invalid recursive ownership and surface child failures
def GetDocLinkErrs(
    DocumentValue: CadDocument, AssemblyValue: AssemblyData
) -> tuple[str, ...]:
    ErrorValues: list[str] = []
    for ItemValue in AssemblyValue.Documents:
        NestedDocument = GetDocument(ItemValue.Document)
        if NestedDocument is None:
            ErrorValues.append(
                f"component document {ItemValue.EntityId} does not contain a CadDocument"
            )
        elif NestedDocument is DocumentValue:
            ErrorValues.append(
                f"component document {ItemValue.EntityId} contains its owner"
            )
        else:
            ErrorValues.extend(
                f"component document {ItemValue.EntityId}: {ErrorText}"
                for ErrorText in NestedDocument.GetErrors()
            )
    return tuple(ErrorValues)


# definition checks protect mesh document and body references across component boundaries
def GetDefLinkErrs(
    DocumentValue: CadDocument,
    AssemblyValue: AssemblyData,
    DocumentValues: TypeMap[str, CadDocument],
) -> tuple[str, ...]:
    ErrorValues: list[str] = []
    MeshById = {ItemValue.EntityId: ItemValue for ItemValue in DocumentValue.meshes}
    for DefinitionValue in AssemblyValue.Definitions:
        for MeshEntityId in DefinitionValue.MeshIds:
            if MeshEntityId not in MeshById:
                ErrorValues.append(
                    f"component definition {DefinitionValue.EntityId} references missing mesh {MeshEntityId}"
                )
        if (
            DefinitionValue.DocumentId
            and DefinitionValue.DocumentId not in DocumentValues
        ):
            ErrorValues.append(
                f"component definition {DefinitionValue.EntityId} references missing document"
            )
            continue
        TargetDocument = DocumentValues.get(DefinitionValue.DocumentId, DocumentValue)
        TargetBodyIds = {BodyValue.EntityId for BodyValue in TargetDocument.bodies}
        for BodyId in DefinitionValue.BodyIds:
            if BodyId not in TargetBodyIds:
                ErrorValues.append(
                    f"component definition {DefinitionValue.EntityId} references missing body {BodyId}"
                )
    return tuple(ErrorValues)
