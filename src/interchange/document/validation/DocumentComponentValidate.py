# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from typing import Any as AnyValue
from typing import Mapping as TypeMap

from interchange.document.models.DocumentRoot import DocumentRoot


# embedded document checks prevent invalid recursive ownership and surface child failures
def GetDocLinkErrs(DocumentValue: AnyValue, AssemblyValue: AnyValue) -> tuple[str, ...]:
    ErrorValues: list[str] = []
    for ItemValue in AssemblyValue.Documents:
        if not isinstance(ItemValue.Document, DocumentRoot):
            ErrorValues.append(
                f"component document {ItemValue.EntityId} does not contain a CadDocument"
            )
        elif ItemValue.Document is DocumentValue:
            ErrorValues.append(
                f"component document {ItemValue.EntityId} contains its owner"
            )
        else:
            ErrorValues.extend(
                f"component document {ItemValue.EntityId}: {ErrorText}"
                for ErrorText in ItemValue.Document.GetErrors()
            )
    return tuple(ErrorValues)


# definition checks protect mesh document and body references across component boundaries
def GetDefLinkErrs(
    DocumentValue: AnyValue,
    AssemblyValue: AnyValue,
    DocumentValues: TypeMap[str, AnyValue],
) -> tuple[str, ...]:
    ErrorValues: list[str] = []
    MeshById = {ItemValue.EntityId: ItemValue for ItemValue in DocumentValue.Meshes}
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
        if isinstance(TargetDocument, DocumentRoot):
            TargetBodyIds = {BodyValue.EntityId for BodyValue in TargetDocument.Bodies}
            for BodyId in DefinitionValue.BodyIds:
                if BodyId not in TargetBodyIds:
                    ErrorValues.append(
                        f"component definition {DefinitionValue.EntityId} references missing body {BodyId}"
                    )
    return tuple(ErrorValues)
