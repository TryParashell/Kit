# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from typing import Any as AnyValue
from typing import Mapping as TypeMap


# mate checks protect entity ownership and parameter references across component documents
def GetMateErrors(
    DocumentValue: AnyValue,
    AssemblyValue: AnyValue,
    Definitions: TypeMap[str, AnyValue],
    Entities: TypeMap[str, AnyValue],
    DocumentValues: TypeMap[str, AnyValue],
    IdentitySets: TypeMap[str, set[str]],
) -> tuple[str, ...]:
    from .document_model import CadDocument

    ErrorValues: list[str] = []
    for MateValue in AssemblyValue.Mates:
        if MateValue.OwnerDefinitionId not in Definitions:
            ErrorValues.append(
                f"mate {MateValue.EntityId} references missing owner definition"
            )
        if not MateValue.EntityIds:
            ErrorValues.append(f"mate {MateValue.EntityId} has no entities")
        for EntityId in MateValue.EntityIds:
            EntityValue = Entities.get(EntityId)
            if EntityValue is None:
                ErrorValues.append(
                    f"mate {MateValue.EntityId} references missing entity {EntityId}"
                )
            elif EntityValue.OwnerDefinitionId != MateValue.OwnerDefinitionId:
                ErrorValues.append(
                    f"mate {MateValue.EntityId} references entity from another assembly"
                )
        OwnerDef = Definitions.get(MateValue.OwnerDefinitionId)
        TargetDocument = DocumentValue
        if OwnerDef is not None and OwnerDef.DocumentId:
            TargetDocument = DocumentValues.get(OwnerDef.DocumentId)
        if isinstance(TargetDocument, CadDocument):
            TargetParamIds = (
                IdentitySets["Parameters"]
                if TargetDocument is DocumentValue
                else {ParamValue.EntityId for ParamValue in TargetDocument.Parameters}
            )
            for ParameterId in MateValue.ParameterIds:
                if ParameterId not in TargetParamIds:
                    ErrorValues.append(
                        f"mate {MateValue.EntityId} references missing parameter {ParameterId}"
                    )
    return tuple(ErrorValues)
