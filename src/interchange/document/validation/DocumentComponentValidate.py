# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from typing import Mapping as TypeMap

from interchange.assembly.AssemblyData import AssemblyData  # lgtm[py/cyclic-import]
from interchange.document.models.DocumentModel import CadDocument  # lgtm[py/cyclic-import]
from interchange.document.validation.DocumentBoundary import GetDocument  # lgtm[py/cyclic-import]


# embedded document checks prevent invalid recursive ownership and surface child failures
def GetDocLinkErrs(
    DocumentValue: CadDocument, AssemblyValue: AssemblyData
) -> tuple[str, ...]:
    ErrorValues: list[str] = []
    for ItemValue in AssemblyValue.documents:
        NestedDocument = GetDocument(ItemValue.document)
        if NestedDocument is None:
            ErrorValues.append(
                f"component document {ItemValue.id} does not contain a CadDocument"
            )
        elif NestedDocument is DocumentValue:
            ErrorValues.append(f"component document {ItemValue.id} contains its owner")
        else:
            ErrorValues.extend(
                f"component document {ItemValue.id}: {ErrorText}"
                for ErrorText in NestedDocument.validate()
            )
    return tuple(ErrorValues)


# definition checks protect mesh document and body references across component boundaries
def GetDefLinkErrs(
    DocumentValue: CadDocument,
    AssemblyValue: AssemblyData,
    DocumentValues: TypeMap[str, CadDocument],
) -> tuple[str, ...]:
    ErrorValues: list[str] = []
    MeshById = {ItemValue.id: ItemValue for ItemValue in DocumentValue.meshes}
    for DefinitionValue in AssemblyValue.definitions:
        for MeshEntityId in DefinitionValue.mesh_ids:
            if MeshEntityId not in MeshById:
                ErrorValues.append(
                    f"component definition {DefinitionValue.id} references missing mesh {MeshEntityId}"
                )
        if (
            DefinitionValue.document_id
            and DefinitionValue.document_id not in DocumentValues
        ):
            ErrorValues.append(
                f"component definition {DefinitionValue.id} references missing document"
            )
            continue
        TargetDocument = DocumentValues.get(DefinitionValue.document_id, DocumentValue)
        TargetBodyIds = {BodyValue.id for BodyValue in TargetDocument.bodies}
        for BodyId in DefinitionValue.body_ids:
            if BodyId not in TargetBodyIds:
                ErrorValues.append(
                    f"component definition {DefinitionValue.id} references missing body {BodyId}"
                )
    return tuple(ErrorValues)
